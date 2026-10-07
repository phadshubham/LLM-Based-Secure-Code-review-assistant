"""
Semgrep scanner wrapper.

Runs Semgrep with the auto ruleset and returns normalised findings.
Handles missing Semgrep gracefully.
"""

import json
import shutil
import subprocess
from typing import List, Dict, Any

from app.config import settings


SEVERITY_MAP = {
    "ERROR": "HIGH",
    "WARNING": "MEDIUM",
    "INFO": "INFO",
    "CRITICAL": "CRITICAL",
    "HIGH": "HIGH",
    "MEDIUM": "MEDIUM",
    "LOW": "LOW",
}


def is_available() -> bool:
    return shutil.which("semgrep") is not None


def run(project_path: str) -> Dict[str, Any]:
    """
    Run Semgrep against project_path.
    Returns {"findings": [...], "error": None|str, "available": bool}
    """
    if not is_available():
        return {"findings": [], "error": "Scanner unavailable", "available": False}

    try:
        result = subprocess.run(
            [
                "semgrep",
                "--config", "auto",
                "--json",
                "--quiet",
                "--no-rewrite-rule-ids",
                "--timeout", "60",
                project_path,
            ],
            capture_output=True,
            text=True,
            timeout=settings.SCANNER_TIMEOUT_SECONDS,
        )
        # Semgrep exits with code 1 when findings are present – that is normal
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
        meta = item.get("extra", {})
        raw_sev = (
            meta.get("severity", "")
            or item.get("severity", "")
        ).upper()
        severity = SEVERITY_MAP.get(raw_sev, "INFO")

        findings.append({
            "tool": "Semgrep",
            "rule_id": item.get("check_id", "unknown"),
            "file": item.get("path", ""),
            "line": item.get("start", {}).get("line"),
            "column": item.get("start", {}).get("col"),
            "severity": severity,
            "category": _infer_category(item.get("check_id", "")),
            "message": meta.get("message", ""),
            "verified": True,
        })
    return findings


def _infer_category(rule_id: str) -> str:
    """Guess a human-readable category from the rule ID."""
    rule_lower = rule_id.lower()
    keywords = {
        "sql": "SQL Injection",
        "xss": "Cross-Site Scripting",
        "injection": "Injection",
        "command": "Command Injection",
        "path": "Path Traversal",
        "crypto": "Weak Cryptography",
        "hardcode": "Hardcoded Secret",
        "secret": "Hardcoded Secret",
        "password": "Hardcoded Secret",
        "ssrf": "SSRF",
        "xxe": "XXE",
        "deseria": "Deserialization",
        "exec": "Code Execution",
        "eval": "Code Execution",
        "open-redirect": "Open Redirect",
        "ldap": "LDAP Injection",
        "csrf": "CSRF",
        "auth": "Authentication Issue",
        "taint": "Taint",
    }
    for kw, cat in keywords.items():
        if kw in rule_lower:
            return cat
    return "Security Misconfiguration"
