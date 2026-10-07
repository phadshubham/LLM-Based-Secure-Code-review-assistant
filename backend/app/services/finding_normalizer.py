"""
Finding Normalizer.

Converts raw scanner outputs into a common internal Finding schema,
deduplicates near-identical findings, and assigns normalised severities.
"""

import hashlib
from typing import List, Dict


SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]

SEVERITY_ALIASES: Dict[str, str] = {
    "CRITICAL": "CRITICAL",
    "ERROR": "HIGH",
    "HIGH": "HIGH",
    "WARNING": "MEDIUM",
    "MEDIUM": "MEDIUM",
    "LOW": "LOW",
    "INFO": "INFO",
    "NOTE": "INFO",
    "INFORMATIONAL": "INFO",
    "UNKNOWN": "INFO",
}


def normalize_severity(raw: str) -> str:
    return SEVERITY_ALIASES.get((raw or "INFO").upper(), "INFO")


def _dedup_key(finding: Dict) -> str:
    """Create a stable deduplication key for a finding."""
    return hashlib.md5(
        f"{finding.get('tool')}|{finding.get('file')}|{finding.get('line')}|{finding.get('rule_id')}".encode()
    ).hexdigest()


def normalize_findings(raw_findings: List[Dict]) -> List[Dict]:
    """
    Normalise and deduplicate raw scanner findings.
    Returns a list of normalised finding dicts.
    """
    seen: set = set()
    normalised: List[Dict] = []

    for raw in raw_findings:
        severity = normalize_severity(raw.get("severity", "INFO"))

        finding = {
            "tool": raw.get("tool", "Unknown"),
            "rule_id": raw.get("rule_id") or "",
            "file": raw.get("file") or "",
            "line": raw.get("line"),
            "column": raw.get("column"),
            "severity": severity,
            "category": raw.get("category") or "Security Issue",
            "message": raw.get("message") or "",
            "code_snippet": raw.get("code_snippet"),
            "verified": raw.get("verified", True),
            "status": "open",
        }

        key = _dedup_key(finding)
        if key not in seen:
            seen.add(key)
            normalised.append(finding)

    # Sort: CRITICAL first, then by file/line
    normalised.sort(
        key=lambda f: (
            SEVERITY_ORDER.index(f["severity"]) if f["severity"] in SEVERITY_ORDER else 99,
            f.get("file") or "",
            f.get("line") or 0,
        )
    )
    return normalised
