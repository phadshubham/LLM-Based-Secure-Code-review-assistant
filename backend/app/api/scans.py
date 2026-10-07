"""
Scans API router.

GET /api/scans/{scan_id}          – scan status and summary
GET /api/scans/{scan_id}/findings – paginated findings for a scan
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.scan import Scan
from app.models.finding import Finding
from app.models.ai_review import AIReview

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scans", tags=["scans"])


def _scan_to_dict(s: Scan) -> dict:
    return {
        "scan_id": s.scan_id,
        "project_id": s.project_id,
        "status": s.status,
        "progress_step": s.progress_step,
        "security_score": s.security_score,
        "total_findings": s.total_findings,
        "critical_count": s.critical_count,
        "high_count": s.high_count,
        "medium_count": s.medium_count,
        "low_count": s.low_count,
        "info_count": s.info_count,
        "scanners_used": json.loads(s.scanners_used) if s.scanners_used else [],
        "error_message": s.error_message,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
    }


def _finding_to_dict(f: Finding, ai: AIReview = None) -> dict:
    d = {
        "finding_id": f.finding_id,
        "scan_id": f.scan_id,
        "tool": f.tool,
        "rule_id": f.rule_id,
        "file": f.file,
        "line": f.line,
        "column": f.column,
        "severity": f.severity,
        "category": f.category,
        "message": f.message,
        "code_snippet": f.code_snippet,
        "verified": f.verified,
        "status": f.status,
        "ai_review": None,
    }
    if ai:
        d["ai_review"] = {
            "review_id": ai.review_id,
            "explanation": ai.explanation,
            "impact": ai.impact,
            "recommendation": ai.recommendation,
            "suggested_patch": ai.suggested_patch,
            "confidence": ai.confidence,
            "classification": ai.classification,
            "source": ai.source,
        }
    return d


@router.get("/{scan_id}")
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
    if not scan:
        raise HTTPException(404, "Scan not found.")
    return {"scan": _scan_to_dict(scan)}


@router.get("/{scan_id}/findings")
def get_findings(
    scan_id: str,
    severity: str = Query(None),
    tool: str = Query(None),
    category: str = Query(None),
    verified: bool = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
    if not scan:
        raise HTTPException(404, "Scan not found.")

    q = db.query(Finding).filter(Finding.scan_id == scan_id)

    if severity:
        q = q.filter(Finding.severity == severity.upper())
    if tool:
        q = q.filter(Finding.tool == tool)
    if category:
        q = q.filter(Finding.category.ilike(f"%{category}%"))
    if verified is not None:
        q = q.filter(Finding.verified == verified)

    total = q.count()
    findings = q.offset((page - 1) * page_size).limit(page_size).all()

    # Fetch AI reviews
    finding_ids = [f.finding_id for f in findings]
    ai_reviews = (
        db.query(AIReview)
        .filter(AIReview.finding_id.in_(finding_ids))
        .all()
    )
    ai_map = {r.finding_id: r for r in ai_reviews}

    return {
        "scan": _scan_to_dict(scan),
        "findings": [_finding_to_dict(f, ai_map.get(f.finding_id)) for f in findings],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
