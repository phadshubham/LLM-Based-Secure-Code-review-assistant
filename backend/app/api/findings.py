"""
Findings API router.

GET /api/findings/{finding_id}         – finding detail with code snippet
GET /api/findings/{finding_id}/review  – AI review for a finding
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.finding import Finding
from app.models.ai_review import AIReview

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/findings", tags=["findings"])


def _finding_full(f: Finding, ai: AIReview = None) -> dict:
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
            "created_at": ai.created_at.isoformat() if ai.created_at else None,
        }
    else:
        d["ai_review"] = None
    return d


@router.get("/{finding_id}")
def get_finding(finding_id: str, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.finding_id == finding_id).first()
    if not finding:
        raise HTTPException(404, "Finding not found.")
    ai = db.query(AIReview).filter(AIReview.finding_id == finding_id).first()
    return {"finding": _finding_full(finding, ai)}


@router.get("/{finding_id}/review")
def get_ai_review(finding_id: str, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.finding_id == finding_id).first()
    if not finding:
        raise HTTPException(404, "Finding not found.")
    ai = db.query(AIReview).filter(AIReview.finding_id == finding_id).first()
    if not ai:
        raise HTTPException(404, "AI review not yet available for this finding.")
    return {
        "review_id": ai.review_id,
        "finding_id": ai.finding_id,
        "explanation": ai.explanation,
        "impact": ai.impact,
        "recommendation": ai.recommendation,
        "suggested_patch": ai.suggested_patch,
        "confidence": ai.confidence,
        "classification": ai.classification,
        "source": ai.source,
        "created_at": ai.created_at.isoformat() if ai.created_at else None,
    }
