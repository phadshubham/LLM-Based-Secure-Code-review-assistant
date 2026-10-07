"""
Security Scoring Service.

Calculates a project security score from 0–100 based on finding severities.
"""

from typing import List, Dict


DEDUCTIONS = {
    "CRITICAL": 20,
    "HIGH": 10,
    "MEDIUM": 5,
    "LOW": 2,
    "INFO": 0,
}


def calculate_score(findings: List[Dict]) -> float:
    """
    Start at 100, subtract points per finding severity.
    Floor at 0.
    """
    score = 100.0
    for finding in findings:
        sev = (finding.get("severity") or "INFO").upper()
        score -= DEDUCTIONS.get(sev, 0)
    return max(0.0, score)


def count_by_severity(findings: List[Dict]) -> Dict[str, int]:
    counts = {s: 0 for s in DEDUCTIONS}
    for f in findings:
        sev = (f.get("severity") or "INFO").upper()
        if sev in counts:
            counts[sev] += 1
    return counts


SCORE_DISCLAIMER = (
    "This security score is an educational/project-defined metric "
    "and is not an industry security certification."
)
