"""
Application configuration management.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent


class Settings:
    # ─── Database ────────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'storage' / 'secure_code_review.db'}"
    )

    # ─── Storage ─────────────────────────────────────────────────────────────
    UPLOADS_DIR: Path = BASE_DIR / "storage" / "uploads"
    PROJECTS_DIR: Path = BASE_DIR / "storage" / "projects"
    REPORTS_DIR: Path = BASE_DIR / "storage" / "reports"

    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
    MAX_UPLOAD_SIZE_BYTES: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # ─── Ollama / LLM ────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b")
    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))

    # ─── Context builder ─────────────────────────────────────────────────────
    CONTEXT_LINES_BEFORE: int = int(os.getenv("CONTEXT_LINES_BEFORE", "20"))
    CONTEXT_LINES_AFTER: int = int(os.getenv("CONTEXT_LINES_AFTER", "20"))

    # ─── CORS ────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # ─── Scanning ─────────────────────────────────────────────────────────────
    SCANNER_TIMEOUT_SECONDS: int = int(os.getenv("SCANNER_TIMEOUT_SECONDS", "120"))

    # Directories to ignore when scanning
    IGNORE_DIRS: set = {
        ".git", "node_modules", "__pycache__", "venv", ".venv",
        "dist", "build", "target", ".idea", ".vscode", ".env",
        "env", ".tox", "coverage", ".mypy_cache", ".pytest_cache",
    }


settings = Settings()

# Ensure storage directories exist
for _dir in (settings.UPLOADS_DIR, settings.PROJECTS_DIR, settings.REPORTS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
