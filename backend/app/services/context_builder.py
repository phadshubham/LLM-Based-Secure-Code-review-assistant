"""
Context Builder.

Extracts the relevant source-code snippet for a finding.
Only the lines around the finding are sent to the LLM –
never the entire file or project.
"""

from pathlib import Path
from typing import Optional

from app.config import settings


def extract_context(
    project_path: str,
    file_path: str,
    line_number: Optional[int],
    lines_before: int = settings.CONTEXT_LINES_BEFORE,
    lines_after: int = settings.CONTEXT_LINES_AFTER,
) -> Optional[str]:
    """
    Extract lines_before..lines_after around line_number from file_path.

    file_path may be absolute or relative to project_path.
    Returns the code snippet as a string, or None if the file cannot be read.
    """
    if not file_path:
        return None

    # Resolve path
    candidate = Path(file_path)
    if not candidate.is_absolute():
        candidate = Path(project_path) / file_path

    if not candidate.exists():
        return None

    try:
        lines = candidate.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return None

    if not lines:
        return None

    if line_number is None:
        # Return the first max (lines_before + lines_after) lines as context
        snippet_lines = lines[: lines_before + lines_after]
    else:
        # Convert to 0-indexed
        idx = line_number - 1
        start = max(0, idx - lines_before)
        end = min(len(lines), idx + lines_after + 1)
        snippet_lines = lines[start:end]

    # Add line numbers for readability
    line_start = (
        max(1, line_number - lines_before) if line_number else 1
    )
    numbered = [
        f"{line_start + i:4d} | {l}"
        for i, l in enumerate(snippet_lines)
    ]
    return "\n".join(numbered)
