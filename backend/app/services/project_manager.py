"""
Project Manager service.

Handles:
  - Safe ZIP extraction with path-traversal protection
  - Public GitHub repository cloning
  - Project directory lifecycle
"""

import os
import re
import shutil
import subprocess
import zipfile
import uuid
from pathlib import Path
from typing import Tuple

from app.config import settings


# ─── ZIP helpers ─────────────────────────────────────────────────────────────

def _safe_zip_extract(zip_path: Path, dest_dir: Path) -> None:
    """
    Extract ZIP while preventing path-traversal attacks.
    Raises ValueError if any member would escape dest_dir.
    """
    dest_dir = dest_dir.resolve()
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            # Resolve the target path
            member_path = (dest_dir / member).resolve()
            if not str(member_path).startswith(str(dest_dir)):
                raise ValueError(
                    f"Unsafe ZIP path detected: {member!r} would escape {dest_dir}"
                )
        zf.extractall(dest_dir)


def extract_zip(zip_path: Path) -> Path:
    """
    Safely extract a ZIP file into an isolated project directory.
    Returns the path to the extracted project root.
    """
    project_id = str(uuid.uuid4())
    project_dir = settings.PROJECTS_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    try:
        _safe_zip_extract(zip_path, project_dir)
    except Exception:
        shutil.rmtree(project_dir, ignore_errors=True)
        raise

    # If the ZIP contains exactly one top-level directory, descend into it
    contents = list(project_dir.iterdir())
    if len(contents) == 1 and contents[0].is_dir():
        return contents[0]

    return project_dir


# ─── GitHub helpers ───────────────────────────────────────────────────────────

_GITHUB_RE = re.compile(
    r"^https?://github\.com/[\w.\-]+/[\w.\-]+(\.git)?/?$",
    re.IGNORECASE,
)


def validate_github_url(url: str) -> bool:
    """Return True if the URL looks like a valid public GitHub repository URL."""
    return bool(_GITHUB_RE.match(url.strip()))


def clone_github_repo(url: str) -> Tuple[str, Path]:
    """
    Clone a public GitHub repository into an isolated directory.
    Returns (project_name, project_dir).
    Raises subprocess.CalledProcessError on clone failure.
    """
    url = url.strip().rstrip("/")
    # Derive a project name from the URL
    repo_name = url.split("/")[-1].replace(".git", "")

    project_id = str(uuid.uuid4())
    project_dir = settings.PROJECTS_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            [
                "git", "clone",
                "--depth", "1",     # shallow clone – faster
                "--single-branch",
                url,
                str(project_dir),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
    except Exception:
        shutil.rmtree(project_dir, ignore_errors=True)
        raise

    return repo_name, project_dir


# ─── Cleanup ──────────────────────────────────────────────────────────────────

def delete_project_directory(project_path: str) -> None:
    """Remove a project directory from the filesystem."""
    p = Path(project_path)
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)
