"""
Scanner Manager.

Orchestrates which scanners run for each detected language and
collects raw findings from all available tools.
"""

from typing import List, Dict, Any

from app.scanners import semgrep, bandit, eslint, spotbugs, trivy


# Language → list of scanner modules to use
LANGUAGE_SCANNERS: Dict[str, List] = {
    "Python": [semgrep, bandit, trivy],
    "JavaScript": [semgrep, eslint, trivy],
    "Java": [semgrep, spotbugs, trivy],
}


def run_scanners(project_path: str, languages: List[str]) -> Dict[str, Any]:
    """
    Run all relevant scanners for the given languages.

    Returns:
    {
        "all_findings": [...],
        "scanner_results": {
            "Semgrep": {"available": True, "findings_count": 3, "error": None},
            ...
        }
    }
    """
    all_findings: List[Dict] = []
    scanner_results: Dict[str, Dict] = {}
    ran_scanners: set = set()

    for lang in languages:
        scanner_list = LANGUAGE_SCANNERS.get(lang, [])
        for scanner_mod in scanner_list:
            scanner_name = scanner_mod.__name__.split(".")[-1].capitalize()
            if scanner_name in ran_scanners:
                continue
            ran_scanners.add(scanner_name)

            result = scanner_mod.run(project_path)
            findings = result.get("findings", [])
            all_findings.extend(findings)

            scanner_results[scanner_name] = {
                "available": result.get("available", True),
                "findings_count": len(findings),
                "error": result.get("error"),
            }

    # If no recognised language, run Semgrep + Trivy as a fallback
    if not ran_scanners:
        for scanner_mod in [semgrep, trivy]:
            scanner_name = scanner_mod.__name__.split(".")[-1].capitalize()
            result = scanner_mod.run(project_path)
            findings = result.get("findings", [])
            all_findings.extend(findings)
            scanner_results[scanner_name] = {
                "available": result.get("available", True),
                "findings_count": len(findings),
                "error": result.get("error"),
            }

    return {
        "all_findings": all_findings,
        "scanner_results": scanner_results,
    }


def get_scanner_availability() -> Dict[str, bool]:
    return {
        "semgrep": semgrep.is_available(),
        "bandit": bandit.is_available(),
        "eslint": eslint.is_available(),
        "spotbugs": spotbugs.is_available(),
        "trivy": trivy.is_available(),
    }
