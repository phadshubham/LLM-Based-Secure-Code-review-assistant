"""
System status API router.

GET /api/system/status – backend, database, Ollama, scanner availability
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.config import settings
from app.services.llm_service import check_ollama_status
from app.services.scanner_manager import get_scanner_availability

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
async def system_status(db: Session = Depends(get_db)):
    # Database check
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
        db_error = None
    except Exception as exc:
        db_ok = False
        db_error = str(exc)

    # Ollama / LLM check
    ollama_info = await check_ollama_status()

    # Scanner availability
    scanners = get_scanner_availability()

    return {
        "backend": {"available": True},
        "database": {"available": db_ok, "error": db_error},
        "ollama": {
            "available": ollama_info["available"],
            "model": ollama_info["model"],
            "model_available": ollama_info.get("model_available", False),
            "available_models": ollama_info.get("available_models", []),
            "error": ollama_info.get("error"),
        },
        "scanners": {
            name: {"available": avail}
            for name, avail in scanners.items()
        },
        "config": {
            "ollama_model": settings.OLLAMA_MODEL,
            "max_upload_mb": settings.MAX_UPLOAD_SIZE_MB,
            "context_lines_before": settings.CONTEXT_LINES_BEFORE,
            "context_lines_after": settings.CONTEXT_LINES_AFTER,
            "llm_timeout_seconds": settings.LLM_TIMEOUT_SECONDS,
        },
    }
