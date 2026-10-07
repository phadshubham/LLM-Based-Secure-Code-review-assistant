"""
SpotBugs scanner wrapper (Java only).

SpotBugs requires a compiled project (class files).  This wrapper
attempts to compile the project with javac first, then runs SpotBugs.
If SpotBugs is not installed, returns "Scanner unavailable".
"""

import glob
import json
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any

from app.config import settings


SEVERITY_MAP = {
    "1": "HIGH",
    "2": "MEDIUM",
    "3": "LOW",
}


def is_available() -> bool:
    return shutil.which("spotbugs") is not None or shutil.which("findbugs") is not None


def _spotbugs_cmd() -> str:
    return "spotbugs" if shutil.which("spotbugs") else "findbugs"


def run(project_path: str) -> Dict[str, Any]:
    if not is_available():
        return {"findings": [], "error": "Scanner unavailable", "available": False}

    # Find Java source files
    java_files = list(Path(project_path).rglob("*.java"))
    if not java_files:
        return {"findings": [], "error": "No Java files found", "available": True}

    with tempfile.TemporaryDirectory() as tmpdir:
        class_dir = os.path.join(tmpdir, "classes")
        os.makedirs(class_dir, exist_ok=True)
        output_xml = os.path.join(tmpdir, "spotbugs.xml")

        # Attempt to compile
        try:
            subprocess.run(
                ["javac", "-d", class_dir]
                + [str(f) for f in java_files],
                capture_output=True,
                timeout=60,
            )
        except Exception:
            pass  # Compilation failure is not fatal; SpotBugs may still work

        # Run SpotBugs
        try:
            result = subprocess.run(
                [
                    _spotbugs_cmd(),
                    "-textui",
                    "-xml:withMessages",
                    f"-output={output_xml}",
                    class_dir,
                ],
                capture_output=True,
                text=True,
                timeout=settings.SCANNER_TIMEOUT_SECONDS,
            )

            if not os.path.exists(output_xml):
                return {
                    "findings": [],
                    "error": "SpotBugs produced no output",
                    "available": True,
                }

            findings = _parse_xml(output_xml)
            return {"findings": findings, "error": None, "available": True}

        except subprocess.TimeoutExpired:
            return {"findings": [], "error": "Scanner timeout", "available": True}
        except Exception as exc:
            return {"findings": [], "error": str(exc), "available": True}


def _parse_xml(xml_path: str) -> List[Dict]:
    findings = []
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for bug in root.findall("BugInstance"):
            rank = bug.get("rank", "2")
            severity = SEVERITY_MAP.get(rank, "MEDIUM")

            # Get source line
            src_line = bug.find("SourceLine")
            file_name = ""
            line_no = None
            if src_line is not None:
                file_name = src_line.get("sourcepath", "")
                start = src_line.get("start")
                line_no = int(start) if start else None

            long_msg = bug.find("LongMessage")
            message = long_msg.text if long_msg is not None else bug.get("type", "")

            findings.append({
                "tool": "SpotBugs",
                "rule_id": bug.get("type", ""),
                "file": file_name,
                "line": line_no,
                "column": None,
                "severity": severity,
                "category": bug.get("category", "Security"),
                "message": message,
                "verified": True,
            })
    except ET.ParseError:
        pass
    return findings
