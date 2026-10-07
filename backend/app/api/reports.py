"""
Reports API router.

GET /api/reports/{scan_id}/pdf   – download PDF report
GET /api/reports/{scan_id}/json  – download JSON report
"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.project import Project
from app.models.scan import Scan
from app.models.finding import Finding
from app.models.ai_review import AIReview
from app.services import report_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["reports"])


def _build_scan_data(scan_id: str, db: Session) -> dict:
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
    if not scan:
        raise HTTPException(404, "Scan not found.")
    if scan.status != "completed":
        raise HTTPException(400, "Scan is not yet completed.")

    project = db.query(Project).filter(Project.project_id == scan.project_id).first()

    findings = db.query(Finding).filter(Finding.scan_id == scan_id).all()
    finding_ids = [f.finding_id for f in findings]
    ai_reviews = db.query(AIReview).filter(AIReview.finding_id.in_(finding_ids)).all()
    ai_map = {r.finding_id: r for r in ai_reviews}

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

    return {
        "project": {
            "project_id": project.project_id if project else "",
            "name": project.name if project else "Unknown",
            "source_type": project.source_type if project else "",
            "repository_url": project.repository_url if project else None,
            "language": project.language if project else "[]",
        },
        "scan": {
            "scan_id": scan.scan_id,
            "status": scan.status,
            "security_score": scan.security_score,
            "total_findings": scan.total_findings,
            "critical_count": scan.critical_count,
            "high_count": scan.high_count,
            "medium_count": scan.medium_count,
            "low_count": scan.low_count,
            "info_count": scan.info_count,
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        },
        "findings": [_f(f, ai_map.get(f.finding_id)) for f in findings],
    }


@router.get("/{scan_id}/pdf")
def download_pdf(scan_id: str, db: Session = Depends(get_db)):
    scan_data = _build_scan_data(scan_id, db)
    pdf_path = settings.REPORTS_DIR / f"report_{scan_id}.pdf"

    # Re-generate if not present or stale
    if not pdf_path.exists():
        try:
            pdf_path = report_service.generate_pdf(scan_data)
        except Exception as exc:
            logger.error("PDF generation failed: %s", exc)
            raise HTTPException(500, f"PDF generation failed: {exc}")

    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=f"security_report_{scan_id[:8]}.pdf",
    )


@router.get("/{scan_id}/json")
def download_json(scan_id: str, db: Session = Depends(get_db)):
    scan_data = _build_scan_data(scan_id, db)
    json_path = settings.REPORTS_DIR / f"report_{scan_id}.json"

    if not json_path.exists():
        try:
            json_path = report_service.generate_json(scan_data)
        except Exception as exc:
            raise HTTPException(500, f"JSON report generation failed: {exc}")

    return FileResponse(
        str(json_path),
        media_type="application/json",
        filename=f"security_report_{scan_id[:8]}.json",
    )
