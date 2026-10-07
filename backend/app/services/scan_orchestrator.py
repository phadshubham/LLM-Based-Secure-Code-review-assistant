"""
Scan Orchestrator.

This module drives the full scan pipeline:
  1. Detect languages
  2. Run scanners
  3. Normalize findings
  4. Calculate score
  5. Extract code context
  6. Get AI explanations
  7. Persist everything to the database

It runs in a FastAPI background task.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.scan import Scan
from app.models.finding import Finding
from app.models.ai_review import AIReview
from app.config import settings
from app.services import (
    scanner_manager,
    finding_normalizer,
    scoring_service,
    context_builder,
    llm_service,
    report_service,
)

logger = logging.getLogger(__name__)

STEPS = [
    "Uploading",
    "Processing",
    "Detecting Languages",
    "Running Security Scanners",
    "Normalizing Findings",
    "Calculating Security Score",
    "Generating AI Explanations",
    "Saving Results",
    "Completed",
]


def _update_scan(db: Session, scan_id: str, **kwargs) -> None:
    db.query(Scan).filter(Scan.scan_id == scan_id).update(kwargs)
    db.commit()


def run_scan_background(
    scan_id: str,
    project_id: str,
    project_path: str,
    languages: List[Dict],
) -> None:
    """
    Full scan pipeline executed as a background task.
    All database writes use a fresh session.
    """
    db: Session = SessionLocal()
    try:
        _run(db, scan_id, project_id, project_path, languages)
    except Exception as exc:
        logger.exception("Scan %s failed with unhandled error", scan_id)
        try:
            _update_scan(
                db,
                scan_id,
                status="failed",
                error_message=str(exc)[:500],
                completed_at=datetime.utcnow(),
            )
        except Exception:
            pass
    finally:
        db.close()


def _run(
    db: Session,
    scan_id: str,
    project_id: str,
    project_path: str,
    languages: List[Dict],
) -> None:

    # ── Step: Running ────────────────────────────────────
    _update_scan(db, scan_id, status="running", progress_step="Running Security Scanners")

    lang_names = [l["name"] for l in languages]
    logger.info("Scan %s: detected languages %s", scan_id, lang_names)

    # ── Step: Run Scanners ───────────────────────────────
    scanner_output = scanner_manager.run_scanners(project_path, lang_names)
    raw_findings = scanner_output["all_findings"]
    scanner_results = scanner_output["scanner_results"]
    scanners_used = list(scanner_results.keys())

    logger.info(
        "Scan %s: scanners=%s raw_findings=%d",
        scan_id, scanners_used, len(raw_findings),
    )

    # ── Step: Normalize ──────────────────────────────────
    _update_scan(db, scan_id, progress_step="Normalizing Findings")
    normalised = finding_normalizer.normalize_findings(raw_findings)

    # ── Step: Score ──────────────────────────────────────
    _update_scan(db, scan_id, progress_step="Calculating Security Score")
    score = scoring_service.calculate_score(normalised)
    counts = scoring_service.count_by_severity(normalised)

    # ── Step: AI Explanations ────────────────────────────
    _update_scan(db, scan_id, progress_step="Generating AI Explanations")

    # Determine primary language for context
    primary_lang = lang_names[0] if lang_names else "Unknown"

    # Persist findings first so we have IDs, then fetch AI
    finding_records: List[Finding] = []
    for nf in normalised:
        # Extract code context
        snippet = context_builder.extract_context(
            project_path,
            nf.get("file", ""),
            nf.get("line"),
        )

        finding = Finding(
            finding_id=str(uuid.uuid4()),
            scan_id=scan_id,
            tool=nf["tool"],
            rule_id=nf.get("rule_id", ""),
            file=nf.get("file", ""),
            line=nf.get("line"),
            column=nf.get("column"),
            severity=nf["severity"],
            category=nf.get("category", ""),
            message=nf.get("message", ""),
            code_snippet=snippet,
            verified=nf.get("verified", True),
            status="open",
        )
        db.add(finding)
        finding_records.append((finding, snippet, nf))

    db.commit()

    # ── AI Explanations (async inside sync context using asyncio.run) ────────
    import asyncio

    async def _get_all_reviews():
        tasks = []
        for finding, snippet, nf in finding_records:
            enriched = {**nf, "language": primary_lang}
            tasks.append(
                llm_service.get_ai_review(enriched, snippet)
            )
        results = []
        # Run one at a time to avoid overwhelming a small model
        for finding, snippet, nf in finding_records:
            enriched = {**nf, "language": primary_lang}
            result = await llm_service.get_ai_review(enriched, snippet)
            results.append((finding, result))
        return results

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ai_results = loop.run_until_complete(_get_all_reviews())
    except Exception as exc:
        logger.warning("AI review phase failed: %s", exc)
        ai_results = [(f, None) for f, _, _ in finding_records]
    finally:
        try:
            loop.close()
        except Exception:
            pass

    # Persist AI reviews
    for finding, ai_data in ai_results:
        if not ai_data:
            continue
        review = AIReview(
            review_id=str(uuid.uuid4()),
            finding_id=finding.finding_id,
            explanation=ai_data.get("explanation", ""),
            impact=ai_data.get("impact", ""),
            recommendation=ai_data.get("recommendation", ""),
            suggested_patch=ai_data.get("patch", ""),
            confidence=ai_data.get("confidence", "medium"),
            classification=ai_data.get("classification", "VERIFIED_FINDING"),
            source=settings.OLLAMA_MODEL,
            raw_response=json.dumps(ai_data),
        )
        db.add(review)

    db.commit()

    # ── Step: Saving ─────────────────────────────────────
    _update_scan(db, scan_id, progress_step="Saving Results")

    # Generate reports
    try:
        from app.models.project import Project
        from app.models.ai_review import AIReview as AIReviewModel

        project = db.query(Project).filter(Project.project_id == project_id).first()
        findings_for_report = db.query(Finding).filter(Finding.scan_id == scan_id).all()
        ai_map = {
            r.finding_id: r
            for r in db.query(AIReviewModel)
            .filter(AIReviewModel.finding_id.in_([f.finding_id for f in findings_for_report]))
            .all()
        }

        def _f(f, ai):
            d = {
                "finding_id": f.finding_id,
                "tool": f.tool,
                "rule_id": f.rule_id,
                "file": f.file,
                "line": f.line,
                "severity": f.severity,
                "category": f.category,
                "message": f.message,
                "code_snippet": f.code_snippet,
                "verified": f.verified,
                "status": f.status,
            }
            if ai:
                d["ai_review"] = {
                    "explanation": ai.explanation,
                    "impact": ai.impact,
                    "recommendation": ai.recommendation,
                    "patch": ai.suggested_patch,
                    "confidence": ai.confidence,
                    "classification": ai.classification,
                }
            else:
                d["ai_review"] = None
            return d

        scan_obj = db.query(Scan).filter(Scan.scan_id == scan_id).first()
        scan_data = {
            "project": {
                "project_id": project.project_id if project else "",
                "name": project.name if project else "Unknown",
                "source_type": project.source_type if project else "",
                "repository_url": project.repository_url if project else None,
                "language": project.language if project else "[]",
            },
            "scan": {
                "scan_id": scan_obj.scan_id,
                "status": "completed",
                "security_score": score,
                "total_findings": len(normalised),
                "critical_count": counts.get("CRITICAL", 0),
                "high_count": counts.get("HIGH", 0),
                "medium_count": counts.get("MEDIUM", 0),
                "low_count": counts.get("LOW", 0),
                "info_count": counts.get("INFO", 0),
                "started_at": scan_obj.started_at.isoformat() if scan_obj.started_at else None,
                "completed_at": datetime.utcnow().isoformat(),
            },
            "findings": [_f(f, ai_map.get(f.finding_id)) for f in findings_for_report],
        }
        report_service.generate_pdf(scan_data)
        report_service.generate_json(scan_data)
    except Exception as exc:
        logger.warning("Report pre-generation failed: %s", exc)

    # ── Step: Completed ──────────────────────────────────
    _update_scan(
        db,
        scan_id,
        status="completed",
        progress_step="Completed",
        security_score=score,
        total_findings=len(normalised),
        critical_count=counts.get("CRITICAL", 0),
        high_count=counts.get("HIGH", 0),
        medium_count=counts.get("MEDIUM", 0),
        low_count=counts.get("LOW", 0),
        info_count=counts.get("INFO", 0),
        scanners_used=json.dumps(scanners_used),
        completed_at=datetime.utcnow(),
    )
    logger.info(
        "Scan %s completed: score=%.1f findings=%d",
        scan_id, score, len(normalised),
    )
