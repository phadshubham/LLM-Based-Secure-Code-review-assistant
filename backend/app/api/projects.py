"""
Projects API router.

POST /api/projects/upload     – upload a ZIP file
POST /api/projects/github     – submit a public GitHub URL
GET  /api/projects            – list all projects
GET  /api/projects/{id}       – project detail
POST /api/projects/{id}/scan  – trigger a new scan
GET  /api/projects/{id}/history – scan history for a project
"""

import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.project import Project
from app.models.scan import Scan
from app.services import project_manager, language_detector, dependency_detector
from app.services.scan_orchestrator import run_scan_background

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects", tags=["projects"])


# ─── Helper ──────────────────────────────────────────────────────────────────

def _project_to_dict(p: Project) -> dict:
    return {
        "project_id": p.project_id,
        "name": p.name,
        "source_type": p.source_type,
        "repository_url": p.repository_url,
        "language": language_detector.languages_from_json(p.language),
        "dependencies": dependency_detector.dependencies_from_json(p.dependencies),
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


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


# ─── Upload ZIP ──────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_project(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_name: str = Form(None),
    db: Session = Depends(get_db),
):
    # Validate content type
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(400, "Only .zip files are accepted.")

    # Read file and check size
    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            413,
            f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    # Save ZIP to uploads/
    upload_id = str(uuid.uuid4())
    upload_path = settings.UPLOADS_DIR / f"{upload_id}.zip"
    upload_path.write_bytes(data)

    # Extract safely
    try:
        project_dir = project_manager.extract_zip(upload_path)
    except ValueError as exc:
        upload_path.unlink(missing_ok=True)
        raise HTTPException(400, f"Unsafe ZIP archive: {exc}")
    except Exception as exc:
        upload_path.unlink(missing_ok=True)
        raise HTTPException(400, f"Could not extract ZIP: {exc}")
    finally:
        upload_path.unlink(missing_ok=True)

    # Detect languages & dependencies
    languages = language_detector.detect_languages(str(project_dir))
    deps = dependency_detector.detect_dependencies(str(project_dir))

    name = project_name or (file.filename.replace(".zip", "") or "Uploaded Project")

    project = Project(
        project_id=str(uuid.uuid4()),
        name=name,
        source_type="zip",
        language=json.dumps(languages),
        dependencies=json.dumps(deps),
        project_path=str(project_dir),
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return {"project": _project_to_dict(project)}


# ─── GitHub URL ──────────────────────────────────────────────────────────────

@router.post("/github")
async def add_github_project(
    background_tasks: BackgroundTasks,
    payload: dict,
    db: Session = Depends(get_db),
):
    url = (payload.get("url") or "").strip()
    if not project_manager.validate_github_url(url):
        raise HTTPException(400, "Invalid or unsupported GitHub repository URL.")

    try:
        repo_name, project_dir = project_manager.clone_github_repo(url)
    except Exception as exc:
        raise HTTPException(400, f"Failed to clone repository: {exc}")

    languages = language_detector.detect_languages(str(project_dir))
    deps = dependency_detector.detect_dependencies(str(project_dir))

    name = payload.get("project_name") or repo_name or "GitHub Project"

    project = Project(
        project_id=str(uuid.uuid4()),
        name=name,
        source_type="github",
        repository_url=url,
        language=json.dumps(languages),
        dependencies=json.dumps(deps),
        project_path=str(project_dir),
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return {"project": _project_to_dict(project)}


# ─── List Projects ───────────────────────────────────────────────────────────

@router.get("")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return {"projects": [_project_to_dict(p) for p in projects]}


# ─── Project Detail ──────────────────────────────────────────────────────────

@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found.")
    return {"project": _project_to_dict(project)}


# ─── Trigger Scan ────────────────────────────────────────────────────────────

@router.post("/{project_id}/scan")
def trigger_scan(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found.")
    if not project.project_path or not Path(project.project_path).exists():
        raise HTTPException(400, "Project directory not found on server.")

    # Create a scan record
    scan = Scan(
        scan_id=str(uuid.uuid4()),
        project_id=project_id,
        status="pending",
        progress_step="Queued",
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Run scan in background
    background_tasks.add_task(
        run_scan_background,
        scan_id=scan.scan_id,
        project_id=project_id,
        project_path=project.project_path,
        languages=language_detector.languages_from_json(project.language),
    )

    return {"scan": _scan_to_dict(scan)}


# ─── Scan History ────────────────────────────────────────────────────────────

@router.get("/{project_id}/history")
def get_scan_history(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found.")

    scans = (
        db.query(Scan)
        .filter(Scan.project_id == project_id)
        .order_by(Scan.started_at.asc())
        .all()
    )
    return {
        "project": _project_to_dict(project),
        "scans": [_scan_to_dict(s) for s in scans],
    }
