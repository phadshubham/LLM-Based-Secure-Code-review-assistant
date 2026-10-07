"""
Pytest test suite for the Secure Code Review Assistant backend.

Tests cover:
  - Language detection
  - Dependency detection
  - ZIP extraction security
  - Finding normalization
  - Severity mapping
  - Security scoring
  - Context extraction
  - Database models
  - API endpoints
  - LLM service (mocked)
"""

import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# ─────────────────────────────────────────────────────────────────────────────
# Language Detection
# ─────────────────────────────────────────────────────────────────────────────

def test_language_detection_python(tmp_path):
    from app.services.language_detector import detect_languages
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "util.py").write_text("pass")
    langs = detect_languages(str(tmp_path))
    assert len(langs) == 1
    assert langs[0]["name"] == "Python"
    assert langs[0]["file_count"] == 2


def test_language_detection_javascript(tmp_path):
    from app.services.language_detector import detect_languages
    (tmp_path / "app.js").write_text("console.log('hi')")
    (tmp_path / "index.jsx").write_text("export default () => <div/>;")
    langs = detect_languages(str(tmp_path))
    assert langs[0]["name"] == "JavaScript"
    assert langs[0]["file_count"] == 2


def test_language_detection_java(tmp_path):
    from app.services.language_detector import detect_languages
    (tmp_path / "Main.java").write_text("public class Main {}")
    langs = detect_languages(str(tmp_path))
    assert langs[0]["name"] == "Java"


def test_language_detection_ignores_node_modules(tmp_path):
    from app.services.language_detector import detect_languages
    node_mod = tmp_path / "node_modules"
    node_mod.mkdir()
    (node_mod / "ignored.py").write_text("print('ignored')")
    (tmp_path / "app.py").write_text("print('real')")
    langs = detect_languages(str(tmp_path))
    assert langs[0]["file_count"] == 1


def test_language_detection_empty(tmp_path):
    from app.services.language_detector import detect_languages
    langs = detect_languages(str(tmp_path))
    assert langs == []


def test_primary_language():
    from app.services.language_detector import primary_language
    langs = [{"name": "Python", "file_count": 5}, {"name": "JavaScript", "file_count": 2}]
    assert primary_language(langs) == "Python"
    assert primary_language([]) is None


# ─────────────────────────────────────────────────────────────────────────────
# Dependency Detection
# ─────────────────────────────────────────────────────────────────────────────

def test_dependency_detection_python(tmp_path):
    from app.services.dependency_detector import detect_dependencies
    (tmp_path / "requirements.txt").write_text("flask==2.0.0")
    deps = detect_dependencies(str(tmp_path))
    assert "Python" in deps
    assert "requirements.txt" in deps["Python"]


def test_dependency_detection_javascript(tmp_path):
    from app.services.dependency_detector import detect_dependencies
    (tmp_path / "package.json").write_text('{"name": "test"}')
    deps = detect_dependencies(str(tmp_path))
    assert "JavaScript" in deps


def test_dependency_detection_java(tmp_path):
    from app.services.dependency_detector import detect_dependencies
    (tmp_path / "pom.xml").write_text("<project/>")
    deps = detect_dependencies(str(tmp_path))
    assert "Java" in deps


def test_dependency_detection_none(tmp_path):
    from app.services.dependency_detector import detect_dependencies
    deps = detect_dependencies(str(tmp_path))
    assert deps == {}


# ─────────────────────────────────────────────────────────────────────────────
# ZIP Security
# ─────────────────────────────────────────────────────────────────────────────

def test_zip_safe_extraction(tmp_path):
    from app.services.project_manager import extract_zip
    # Create a safe ZIP
    zip_path = tmp_path / "safe.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("app.py", "print('hello')")
        zf.writestr("subdir/util.py", "pass")
    project_dir = extract_zip(zip_path)
    assert project_dir.exists()


def test_zip_path_traversal_blocked(tmp_path):
    from app.services.project_manager import extract_zip
    zip_path = tmp_path / "evil.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../../evil.sh", "rm -rf /")
    with pytest.raises((ValueError, Exception)):
        extract_zip(zip_path)


def test_github_url_validation():
    from app.services.project_manager import validate_github_url
    assert validate_github_url("https://github.com/user/repo") is True
    assert validate_github_url("https://github.com/user/repo.git") is True
    assert validate_github_url("https://notgithub.com/user/repo") is False
    assert validate_github_url("http://evil.com/") is False
    assert validate_github_url("") is False


# ─────────────────────────────────────────────────────────────────────────────
# Finding Normalization
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_FINDINGS = [
    {
        "tool": "Semgrep",
        "rule_id": "sql-injection",
        "file": "login.py",
        "line": 52,
        "column": 5,
        "severity": "HIGH",
        "category": "SQL Injection",
        "message": "Possible SQL injection via string concatenation",
        "verified": True,
    },
    {
        "tool": "Bandit",
        "rule_id": "B303",
        "file": "crypto.py",
        "line": 10,
        "column": 1,
        "severity": "MEDIUM",
        "category": "Weak Cryptography",
        "message": "Use of MD5 is insecure",
        "verified": True,
    },
    # Duplicate – should be deduped
    {
        "tool": "Semgrep",
        "rule_id": "sql-injection",
        "file": "login.py",
        "line": 52,
        "column": 5,
        "severity": "HIGH",
        "category": "SQL Injection",
        "message": "Possible SQL injection via string concatenation",
        "verified": True,
    },
]


def test_normalization_deduplication():
    from app.services.finding_normalizer import normalize_findings
    normalised = normalize_findings(SAMPLE_FINDINGS)
    assert len(normalised) == 2  # duplicate removed


def test_normalization_severity_mapping():
    from app.services.finding_normalizer import normalize_severity
    assert normalize_severity("ERROR") == "HIGH"
    assert normalize_severity("WARNING") == "MEDIUM"
    assert normalize_severity("HIGH") == "HIGH"
    assert normalize_severity("CRITICAL") == "CRITICAL"
    assert normalize_severity("INFO") == "INFO"
    assert normalize_severity("UNKNOWN_SEV") == "INFO"


def test_normalization_sort_order():
    from app.services.finding_normalizer import normalize_findings
    findings = [
        {"tool": "T", "rule_id": "1", "file": "a.py", "line": 1, "severity": "LOW", "message": "m"},
        {"tool": "T", "rule_id": "2", "file": "a.py", "line": 2, "severity": "CRITICAL", "message": "m"},
        {"tool": "T", "rule_id": "3", "file": "a.py", "line": 3, "severity": "HIGH", "message": "m"},
    ]
    normalised = normalize_findings(findings)
    assert normalised[0]["severity"] == "CRITICAL"
    assert normalised[1]["severity"] == "HIGH"
    assert normalised[2]["severity"] == "LOW"


# ─────────────────────────────────────────────────────────────────────────────
# Security Scoring
# ─────────────────────────────────────────────────────────────────────────────

def test_security_score_perfect():
    from app.services.scoring_service import calculate_score
    assert calculate_score([]) == 100.0


def test_security_score_deductions():
    from app.services.scoring_service import calculate_score
    findings = [
        {"severity": "CRITICAL"},
        {"severity": "HIGH"},
        {"severity": "MEDIUM"},
        {"severity": "LOW"},
    ]
    score = calculate_score(findings)
    assert score == 100 - 20 - 10 - 5 - 2  # = 63


def test_security_score_floor_at_zero():
    from app.services.scoring_service import calculate_score
    # 10 CRITICAL findings
    findings = [{"severity": "CRITICAL"}] * 10
    assert calculate_score(findings) == 0.0


def test_security_score_info_no_deduction():
    from app.services.scoring_service import calculate_score
    findings = [{"severity": "INFO"}] * 100
    assert calculate_score(findings) == 100.0


def test_severity_counts():
    from app.services.scoring_service import count_by_severity
    findings = [
        {"severity": "CRITICAL"},
        {"severity": "HIGH"},
        {"severity": "HIGH"},
        {"severity": "MEDIUM"},
        {"severity": "LOW"},
        {"severity": "INFO"},
    ]
    counts = count_by_severity(findings)
    assert counts["CRITICAL"] == 1
    assert counts["HIGH"] == 2
    assert counts["MEDIUM"] == 1
    assert counts["LOW"] == 1
    assert counts["INFO"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Context Builder
# ─────────────────────────────────────────────────────────────────────────────

def test_context_extraction(tmp_path):
    from app.services.context_builder import extract_context
    code = "\n".join([f"# line {i}" for i in range(1, 101)])
    src_file = tmp_path / "main.py"
    src_file.write_text(code)

    snippet = extract_context(str(tmp_path), "main.py", 50, lines_before=5, lines_after=5)
    assert snippet is not None
    assert "line 45" in snippet or "line 50" in snippet


def test_context_extraction_missing_file(tmp_path):
    from app.services.context_builder import extract_context
    snippet = extract_context(str(tmp_path), "nonexistent.py", 10)
    assert snippet is None


def test_context_extraction_no_line_number(tmp_path):
    from app.services.context_builder import extract_context
    code = "# line 1\n# line 2\n# line 3\n"
    (tmp_path / "main.py").write_text(code)
    snippet = extract_context(str(tmp_path), "main.py", None)
    assert snippet is not None


# ─────────────────────────────────────────────────────────────────────────────
# LLM Service (mocked)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_llm_review_success():
    from app.services.llm_service import get_ai_review

    mock_response = {
        "explanation": "SQL injection allows attackers to modify database queries.",
        "impact": "Attacker could read, modify or delete database data.",
        "recommendation": "Use parameterised queries.",
        "patch": "cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))",
        "confidence": "high",
        "classification": "VERIFIED_FINDING",
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "message": {"content": json.dumps(mock_response)}
        }
        mock_resp.raise_for_status = MagicMock()
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_resp
        )

        finding = {
            "tool": "Semgrep",
            "rule_id": "sql-injection",
            "file": "login.py",
            "line": 52,
            "severity": "HIGH",
            "category": "SQL Injection",
            "message": "SQL injection",
            "language": "Python",
        }
        result = await get_ai_review(finding, "cursor.execute('SELECT * FROM users WHERE id=' + uid)")
        assert result is not None
        assert result["classification"] == "VERIFIED_FINDING"
        assert "explanation" in result


@pytest.mark.asyncio
async def test_llm_review_ollama_unavailable():
    from app.services.llm_service import get_ai_review
    import httpx

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        finding = {"tool": "Bandit", "rule_id": "B303", "severity": "MEDIUM", "message": "test"}
        result = await get_ai_review(finding, None)
        assert result is None


@pytest.mark.asyncio
async def test_ollama_status_unavailable():
    from app.services.llm_service import check_ollama_status
    import httpx

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        status = await check_ollama_status()
        assert status["available"] is False
        assert "error" in status


# ─────────────────────────────────────────────────────────────────────────────
# Database Models
# ─────────────────────────────────────────────────────────────────────────────

def test_database_models(tmp_path):
    """Test creating project, scan, finding and AI review in SQLite."""
    import uuid
    from datetime import datetime

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Base
    from app.models.project import Project
    from app.models.scan import Scan
    from app.models.finding import Finding
    from app.models.ai_review import AIReview

    # Use a temp database
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    project = Project(
        project_id=str(uuid.uuid4()),
        name="Test Project",
        source_type="zip",
    )
    db.add(project)
    db.commit()

    scan = Scan(
        scan_id=str(uuid.uuid4()),
        project_id=project.project_id,
        status="completed",
        security_score=75.0,
    )
    db.add(scan)
    db.commit()

    finding = Finding(
        finding_id=str(uuid.uuid4()),
        scan_id=scan.scan_id,
        tool="Semgrep",
        rule_id="sql-injection",
        file="app.py",
        line=10,
        severity="HIGH",
        category="SQL Injection",
        message="SQL injection found",
        verified=True,
    )
    db.add(finding)
    db.commit()

    review = AIReview(
        review_id=str(uuid.uuid4()),
        finding_id=finding.finding_id,
        explanation="SQL injection explanation",
        classification="VERIFIED_FINDING",
        confidence="high",
    )
    db.add(review)
    db.commit()

    # Verify retrieval
    assert db.query(Project).count() == 1
    assert db.query(Scan).count() == 1
    assert db.query(Finding).count() == 1
    assert db.query(AIReview).count() == 1

    db.close()


# ─────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def test_client(tmp_path, monkeypatch):
    """Create a FastAPI test client with an isolated SQLite database."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from fastapi.testclient import TestClient

    db_path = tmp_path / "test_api.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    from app.database import Base, get_db
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Set storage dirs to tmp_path
    monkeypatch.setattr("app.config.settings.UPLOADS_DIR", tmp_path / "uploads")
    monkeypatch.setattr("app.config.settings.PROJECTS_DIR", tmp_path / "projects")
    monkeypatch.setattr("app.config.settings.REPORTS_DIR", tmp_path / "reports")
    (tmp_path / "uploads").mkdir()
    (tmp_path / "projects").mkdir()
    (tmp_path / "reports").mkdir()

    from app.main import app
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


def test_root_endpoint(test_client):
    resp = test_client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"


def test_list_projects_empty(test_client):
    resp = test_client.get("/api/projects")
    assert resp.status_code == 200
    assert resp.json()["projects"] == []


def test_upload_invalid_extension(test_client):
    resp = test_client.post(
        "/api/projects/upload",
        files={"file": ("evil.exe", b"fake content", "application/octet-stream")},
        data={"project_name": "Evil"},
    )
    assert resp.status_code == 400


def test_upload_valid_zip(test_client, tmp_path):
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("main.py", "print('hello')")
    buf.seek(0)

    resp = test_client.post(
        "/api/projects/upload",
        files={"file": ("project.zip", buf.read(), "application/zip")},
        data={"project_name": "Test Project"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "project" in data
    assert data["project"]["name"] == "Test Project"


def test_system_status(test_client):
    resp = test_client.get("/api/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "backend" in data
    assert "database" in data
    assert "ollama" in data
    assert "scanners" in data


def test_scan_not_found(test_client):
    resp = test_client.get("/api/scans/nonexistent-id")
    assert resp.status_code == 404


def test_finding_not_found(test_client):
    resp = test_client.get("/api/findings/nonexistent-id")
    assert resp.status_code == 404


def test_github_invalid_url(test_client):
    resp = test_client.post(
        "/api/projects/github",
        json={"url": "https://notgithub.com/user/repo"},
    )
    assert resp.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# End-to-End Workflow (mocked scanners + LLM)
# ─────────────────────────────────────────────────────────────────────────────

def test_end_to_end_scan_workflow(tmp_path):
    """
    Full pipeline: project dir → scanners → normalization → score → context → AI review → DB
    Uses mocked scanners and mocked LLM.
    """
    import uuid
    import asyncio
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Base

    # Create an isolated project directory
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "app.py").write_text(
        "import sqlite3\n"
        "def get_user(name):\n"
        "    conn = sqlite3.connect('db')\n"
        "    cursor = conn.cursor()\n"
        "    q = \"SELECT * FROM users WHERE name='\" + name + \"'\"\n"
        "    cursor.execute(q)\n"
    )

    # Language detection
    from app.services.language_detector import detect_languages
    langs = detect_languages(str(project_dir))
    assert langs[0]["name"] == "Python"

    # Normalise mock findings
    from app.services.finding_normalizer import normalize_findings
    raw = [
        {
            "tool": "Semgrep",
            "rule_id": "sql-injection",
            "file": str(project_dir / "app.py"),
            "line": 5,
            "severity": "HIGH",
            "category": "SQL Injection",
            "message": "SQL injection",
            "verified": True,
        }
    ]
    normalised = normalize_findings(raw)
    assert len(normalised) == 1

    # Score
    from app.services.scoring_service import calculate_score
    score = calculate_score(normalised)
    assert score == 90.0  # 100 - 10 (HIGH)

    # Context
    from app.services.context_builder import extract_context
    snippet = extract_context(str(project_dir), str(project_dir / "app.py"), 5)
    assert snippet is not None
    assert "name" in snippet

    # Mock LLM
    async def mock_review():
        from app.services.llm_service import _parse_llm_response
        return _parse_llm_response(json.dumps({
            "explanation": "SQL injection found",
            "impact": "Data breach",
            "recommendation": "Use parameterised queries",
            "patch": "cursor.execute('SELECT * FROM users WHERE name=?', (name,))",
            "confidence": "high",
            "classification": "VERIFIED_FINDING",
        }))

    review = asyncio.run(mock_review())
    assert review["classification"] == "VERIFIED_FINDING"

    # Database
    db_path = tmp_path / "e2e.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    from app.models.project import Project
    from app.models.scan import Scan
    from app.models.finding import Finding
    from app.models.ai_review import AIReview

    project = Project(project_id=str(uuid.uuid4()), name="E2E", source_type="zip")
    db.add(project)
    db.commit()

    scan = Scan(
        scan_id=str(uuid.uuid4()),
        project_id=project.project_id,
        status="completed",
        security_score=score,
        total_findings=len(normalised),
    )
    db.add(scan)
    db.commit()

    for nf in normalised:
        f = Finding(
            finding_id=str(uuid.uuid4()),
            scan_id=scan.scan_id,
            tool=nf["tool"],
            rule_id=nf.get("rule_id", ""),
            file=nf.get("file", ""),
            line=nf.get("line"),
            severity=nf["severity"],
            category=nf.get("category", ""),
            message=nf.get("message", ""),
            verified=nf.get("verified", True),
        )
        db.add(f)
        db.commit()

        if review:
            r = AIReview(
                review_id=str(uuid.uuid4()),
                finding_id=f.finding_id,
                explanation=review.get("explanation", ""),
                impact=review.get("impact", ""),
                recommendation=review.get("recommendation", ""),
                suggested_patch=review.get("patch", ""),
                confidence=review.get("confidence", "high"),
                classification=review.get("classification", "VERIFIED_FINDING"),
                source="test-model",
            )
            db.add(r)
            db.commit()

    # Verify
    assert db.query(Finding).count() == 1
    assert db.query(AIReview).count() == 1
    assert db.query(Scan).filter(Scan.security_score == 90.0).count() == 1

    db.close()
