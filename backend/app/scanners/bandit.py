"""
Bandit scanner wrapper (Python only).

Runs Bandit with JSON output and normalises findings.
"""

import json
import shutil
import subprocess
from typing import List, Dict, Any

from app.config import settings


SEVERITY_MAP = {
    "HIGH": "HIGH",
    "MEDIUM": "MEDIUM",
    "LOW": "LOW",
}

CONFIDENCE_TO_SEVERITY = {
    "HIGH": 0,
    "MEDIUM": 0,
    "LOW": 0,
}


def is_available() -> bool:
    return shutil.which("bandit") is not None


def run(project_path: str) -> Dict[str, Any]:
    """
    Run Bandit against project_path.
    Returns {"findings": [...], "error": None|str, "available": bool}
    """
    if not is_available():
        return {"findings": [], "error": "Scanner unavailable", "available": False}

    try:
        result = subprocess.run(
            [
                "bandit",
                "-r",
                "-f", "json",
                "--quiet",
                project_path,
            ],
            capture_output=True,
            text=True,
            timeout=settings.SCANNER_TIMEOUT_SECONDS,
        )
        # Bandit exits with 1 when issues found – normal
        output = result.stdout
        if not output.strip():
            return {"findings": [], "error": None, "available": True}

        data = json.loads(output)
        findings = _parse(data)
        return {"findings": findings, "error": None, "available": True}

    except subprocess.TimeoutExpired:
        return {"findings": [], "error": "Scanner timeout", "available": True}
    except json.JSONDecodeError as exc:
        return {"findings": [], "error": f"JSON parse error: {exc}", "available": True}
    except Exception as exc:
        return {"findings": [], "error": str(exc), "available": True}


def _parse(data: Dict) -> List[Dict]:
    findings = []
    for item in data.get("results", []):
        raw_sev = item.get("issue_severity", "MEDIUM").upper()
        severity = SEVERITY_MAP.get(raw_sev, "MEDIUM")

        findings.append({
            "tool": "Bandit",
            "rule_id": item.get("test_id", ""),
            "file": item.get("filename", ""),
            "line": item.get("line_number"),
            "column": item.get("col_offset"),
            "severity": severity,
            "category": item.get("test_name", "Security Issue"),
            "message": item.get("issue_text", ""),
            "verified": True,
        })
    return findings
