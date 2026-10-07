"""
Trivy scanner wrapper.

Runs `trivy fs` on the project directory for dependency and filesystem
vulnerability scanning.  Handles missing Trivy gracefully.
"""

import json
import shutil
import subprocess
from typing import List, Dict, Any

from app.config import settings


SEVERITY_MAP = {
    "CRITICAL": "CRITICAL",
    "HIGH": "HIGH",
    "MEDIUM": "MEDIUM",
    "LOW": "LOW",
    "UNKNOWN": "INFO",
}


def is_available() -> bool:
    return shutil.which("trivy") is not None


def run(project_path: str) -> Dict[str, Any]:
    """
    Run Trivy filesystem scan.
    Returns {"findings": [...], "error": None|str, "available": bool}
    """
    if not is_available():
        return {"findings": [], "error": "Scanner unavailable", "available": False}

    try:
        result = subprocess.run(
            [
                "trivy",
                "fs",
                "--format", "json",
                "--quiet",
                "--exit-code", "0",
                "--scanners", "vuln,secret,misconfig",
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


def _parse(data: Dict) -> List[Dict]:
    findings = []

    results = data.get("Results", [])
    for result in results:
        target = result.get("Target", "")

        # Vulnerabilities (dependency CVEs)
        for vuln in result.get("Vulnerabilities") or []:
            raw_sev = vuln.get("Severity", "UNKNOWN").upper()
            severity = SEVERITY_MAP.get(raw_sev, "INFO")
            vid = vuln.get("VulnerabilityID", "")
            pkg = vuln.get("PkgName", "")
            installed = vuln.get("InstalledVersion", "")
            fixed = vuln.get("FixedVersion", "")
            title = vuln.get("Title") or vuln.get("Description", "Vulnerability found")

            message = (
                f"{vid}: {title}. "
                f"Package: {pkg} {installed}"
                + (f" (fix available: {fixed})" if fixed else "")
            )

            findings.append({
                "tool": "Trivy",
                "rule_id": vid,
                "file": target,
                "line": None,
                "column": None,
                "severity": severity,
                "category": "Vulnerable Dependency",
                "message": message,
                "verified": True,
            })

        # Secrets
        for secret in result.get("Secrets") or []:
            raw_sev = secret.get("Severity", "HIGH").upper()
            severity = SEVERITY_MAP.get(raw_sev, "HIGH")
            findings.append({
                "tool": "Trivy",
                "rule_id": secret.get("RuleID", "secret"),
                "file": target,
                "line": secret.get("StartLine"),
                "column": None,
                "severity": severity,
                "category": "Exposed Secret",
                "message": secret.get("Title", "Secret detected"),
                "verified": True,
            })

        # Misconfigurations
        for misconf in result.get("Misconfigurations") or []:
            raw_sev = misconf.get("Severity", "MEDIUM").upper()
            severity = SEVERITY_MAP.get(raw_sev, "MEDIUM")
            findings.append({
                "tool": "Trivy",
                "rule_id": misconf.get("ID", "misconfig"),
                "file": target,
                "line": None,
                "column": None,
                "severity": severity,
                "category": "Misconfiguration",
                "message": misconf.get("Title", "Misconfiguration detected"),
                "verified": True,
            })

    return findings
