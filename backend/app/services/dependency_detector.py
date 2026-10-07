"""
Dependency detector – finds and reports dependency manifest files.
"""

import json
from pathlib import Path
from typing import Dict, List


DEPENDENCY_FILES: Dict[str, List[str]] = {
    "Python": ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"],
    "JavaScript": ["package.json", "package-lock.json", "yarn.lock"],
    "Java": ["pom.xml", "build.gradle", "build.gradle.kts"],
}


def detect_dependencies(project_path: str) -> Dict[str, List[str]]:
    """
    Scan project directory for dependency manifest files.
    Returns dict mapping language → list of found filenames.
    """
    root = Path(project_path)
    found: Dict[str, List[str]] = {}

    for lang, indicators in DEPENDENCY_FILES.items():
        for fname in indicators:
            matches = list(root.rglob(fname))
            # Ignore matches inside ignored dirs
            real_matches = [
                m for m in matches
                if not any(
                    part in {".git", "node_modules", "__pycache__", "venv", ".venv"}
                    for part in m.parts
                )
            ]
            if real_matches:
                found.setdefault(lang, []).append(fname)

    return found


def dependencies_to_json(deps: Dict) -> str:
    return json.dumps(deps)


def dependencies_from_json(deps_json: str) -> Dict:
    if not deps_json:
        return {}
    try:
        return json.loads(deps_json)
    except Exception:
        return {}
