"""
Language detection service.

Walks the project directory, counts source files by extension,
and identifies which languages are present.
"""

import json
from pathlib import Path
from typing import List, Dict
from app.config import settings


# Extension → language mapping
EXTENSION_MAP: Dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".java": "Java",
}

# Dependency file indicators per language
DEPENDENCY_INDICATORS: Dict[str, List[str]] = {
    "Python": ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"],
    "JavaScript": ["package.json", "package-lock.json", "yarn.lock"],
    "Java": ["pom.xml", "build.gradle", "build.gradle.kts"],
}


def detect_languages(project_path: str) -> List[Dict]:
    """
    Returns a list like:
    [{"name": "Python", "file_count": 10}, ...]
    sorted by file_count descending.
    """
    root = Path(project_path)
    counts: Dict[str, int] = {}

    for file in root.rglob("*"):
        # Skip ignored directories
        if any(part in settings.IGNORE_DIRS for part in file.parts):
            continue
        if file.is_file():
            lang = EXTENSION_MAP.get(file.suffix.lower())
            if lang:
                counts[lang] = counts.get(lang, 0) + 1

    result = [
        {"name": lang, "file_count": count}
        for lang, count in counts.items()
    ]
    result.sort(key=lambda x: x["file_count"], reverse=True)
    return result


def detect_dependencies(project_path: str) -> Dict[str, List[str]]:
    """
    Returns which dependency files are found per language.
    Example: {"Python": ["requirements.txt"], "JavaScript": ["package.json"]}
    """
    root = Path(project_path)
    found: Dict[str, List[str]] = {}

    for lang, indicators in DEPENDENCY_INDICATORS.items():
        for fname in indicators:
            matches = list(root.rglob(fname))
            if matches:
                found.setdefault(lang, []).append(fname)

    return found


def primary_language(languages: List[Dict]) -> str | None:
    """Return the primary language name or None."""
    if not languages:
        return None
    return languages[0]["name"]


def languages_to_json(languages: List[Dict]) -> str:
    return json.dumps(languages)


def languages_from_json(languages_json: str) -> List[Dict]:
    if not languages_json:
        return []
    try:
        return json.loads(languages_json)
    except Exception:
        return []
