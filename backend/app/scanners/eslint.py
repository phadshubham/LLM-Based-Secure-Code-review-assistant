"""
ESLint scanner wrapper (JavaScript only).

Uses ESLint with JSON formatter.  Handles missing ESLint gracefully.
"""

import json
import shutil
import subprocess
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any

from app.config import settings


SEVERITY_MAP = {
    0: "INFO",
    1: "MEDIUM",
    2: "HIGH",
}

# Minimal .eslintrc.json with security-focused rules
ESLINT_CONFIG = {
    "env": {"browser": True, "es2021": True, "node": True},
    "parserOptions": {"ecmaVersion": 2021, "sourceType": "module"},
    "rules": {
        "no-eval": "error",
        "no-implied-eval": "error",
        "no-new-func": "error",
        "no-script-url": "error",
        "no-unsafe-innerhtml": "off",
        "no-unused-expressions": "warn",
    },
}


def is_available() -> bool:
    return shutil.which("eslint") is not None


def run(project_path: str) -> Dict[str, Any]:
    """
    Run ESLint against project_path.
    Returns {"findings": [...], "error": None|str, "available": bool}
    """
    if not is_available():
        return {"findings": [], "error": "Scanner unavailable", "available": False}

    # Write a temporary ESLint config so we don't depend on the project having one
    config_file = Path(project_path) / ".eslintrc_security_scan.json"
    try:
        config_file.write_text(json.dumps(ESLINT_CONFIG))

        result = subprocess.run(
            [
                "eslint",
                "--format", "json",
                "--no-eslintrc",
                "--config", str(config_file),
                "--ext", ".js,.jsx,.mjs",
                project_path,
            ],
            capture_output=True,
            text=True,
            timeout=settings.SCANNER_TIMEOUT_SECONDS,
        )

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
    finally:
        if config_file.exists():
            config_file.unlink()


def _parse(data: List) -> List[Dict]:
    findings = []
    for file_result in data:
        file_path = file_result.get("filePath", "")
        for msg in file_result.get("messages", []):
            raw_sev = msg.get("severity", 1)
            severity = SEVERITY_MAP.get(raw_sev, "MEDIUM")
            rule_id = msg.get("ruleId") or "eslint-rule"

            findings.append({
                "tool": "ESLint",
                "rule_id": rule_id,
                "file": file_path,
                "line": msg.get("line"),
                "column": msg.get("column"),
                "severity": severity,
                "category": _infer_category(rule_id),
                "message": msg.get("message", ""),
                "verified": True,
            })
    return findings


def _infer_category(rule_id: str) -> str:
    rule_lower = (rule_id or "").lower()
    if "eval" in rule_lower:
        return "Code Injection"
    if "sql" in rule_lower:
        return "SQL Injection"
    if "xss" in rule_lower or "innerhtml" in rule_lower:
        return "Cross-Site Scripting"
    if "prototype" in rule_lower:
        return "Prototype Pollution"
    return "Security Misconfiguration"
