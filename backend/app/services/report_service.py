"""
Report Service.

Generates PDF and JSON reports for completed scans.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from app.config import settings


AI_DISCLAIMER = (
    "AI-generated recommendations should be reviewed by a developer "
    "before implementation. Scanner findings are verified by deterministic "
    "static analysis tools."
)

SCORE_DISCLAIMER = (
    "This security score is an educational/project-defined metric "
    "and is not an industry security certification."
)


# ─── PDF ─────────────────────────────────────────────────────────────────────

def generate_pdf(scan_data: Dict[str, Any]) -> Path:
    """
    Generate a PDF report for a scan.
    Returns the Path to the generated file.
    """
    scan_id = scan_data["scan"]["scan_id"]
    output_path = settings.REPORTS_DIR / f"report_{scan_id}.pdf"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Header ──────────────────────────────────────────
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )
    story.append(Paragraph("Security Code Review Report", title_style))
    story.append(
        Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#64748b")))
    story.append(Spacer(1, 0.4 * cm))

    # ── Project Info ─────────────────────────────────────
    project = scan_data.get("project", {})
    scan = scan_data.get("scan", {})

    story.append(Paragraph("Project Information", styles["Heading2"]))
    info_rows = [
        ["Project Name", project.get("name", "N/A")],
        ["Source Type", project.get("source_type", "N/A").upper()],
        ["Languages", ", ".join(
            l["name"] for l in json.loads(project.get("language") or "[]")
        ) or "N/A"],
        ["Scan Date", (scan.get("completed_at") or scan.get("started_at") or "")[:19]],
        ["Scan ID", scan.get("scan_id", "")],
    ]
    if project.get("repository_url"):
        info_rows.insert(2, ["Repository", project["repository_url"]])

    info_table = Table(info_rows, colWidths=[4 * cm, 12 * cm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Security Score ────────────────────────────────────
    score = scan.get("security_score", 0) or 0
    score_color = (
        colors.HexColor("#22c55e") if score >= 80
        else colors.HexColor("#f59e0b") if score >= 60
        else colors.HexColor("#ef4444")
    )
    story.append(Paragraph("Security Score", styles["Heading2"]))
    score_style = ParagraphStyle(
        "Score",
        parent=styles["Normal"],
        fontSize=32,
        textColor=score_color,
        fontName="Helvetica-Bold",
    )
    story.append(Paragraph(f"{score:.0f} / 100", score_style))
    story.append(Paragraph(SCORE_DISCLAIMER, ParagraphStyle(
        "Disclaimer",
        parent=styles["Italic"],
        fontSize=8,
        textColor=colors.HexColor("#64748b"),
    )))
    story.append(Spacer(1, 0.5 * cm))

    # ── Severity Summary ──────────────────────────────────
    story.append(Paragraph("Severity Summary", styles["Heading2"]))
    sev_data = [
        ["Severity", "Count"],
        ["Critical", str(scan.get("critical_count", 0))],
        ["High", str(scan.get("high_count", 0))],
        ["Medium", str(scan.get("medium_count", 0))],
        ["Low", str(scan.get("low_count", 0))],
        ["Info", str(scan.get("info_count", 0))],
    ]
    sev_colors_map = {
        "Critical": colors.HexColor("#7f1d1d"),
        "High": colors.HexColor("#9b1c1c"),
        "Medium": colors.HexColor("#92400e"),
        "Low": colors.HexColor("#1e3a5f"),
        "Info": colors.HexColor("#1e3a5f"),
    }
    sev_table = Table(sev_data, colWidths=[8 * cm, 8 * cm])
    sev_table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
    ]
    for i, (sev, _) in enumerate(sev_data[1:], start=1):
        if sev in sev_colors_map:
            sev_table_style.append(
                ("TEXTCOLOR", (0, i), (0, i), sev_colors_map[sev])
            )
    sev_table.setStyle(TableStyle(sev_table_style))
    story.append(sev_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Findings ─────────────────────────────────────────
    findings = scan_data.get("findings", [])
    story.append(Paragraph(f"Security Findings ({len(findings)})", styles["Heading2"]))

    sev_bg = {
        "CRITICAL": colors.HexColor("#fee2e2"),
        "HIGH": colors.HexColor("#fef3c7"),
        "MEDIUM": colors.HexColor("#fef9c3"),
        "LOW": colors.HexColor("#dbeafe"),
        "INFO": colors.HexColor("#f1f5f9"),
    }
    sev_fg = {
        "CRITICAL": colors.HexColor("#7f1d1d"),
        "HIGH": colors.HexColor("#78350f"),
        "MEDIUM": colors.HexColor("#713f12"),
        "LOW": colors.HexColor("#1e3a8a"),
        "INFO": colors.HexColor("#334155"),
    }

    for i, finding in enumerate(findings, start=1):
        sev = finding.get("severity", "INFO").upper()
        bg = sev_bg.get(sev, colors.HexColor("#f1f5f9"))
        fg = sev_fg.get(sev, colors.HexColor("#334155"))

        block = []

        # Finding header
        header_style = ParagraphStyle(
            f"FH{i}", parent=styles["Normal"],
            fontSize=10, fontName="Helvetica-Bold",
            textColor=fg, backColor=bg,
        )
        verified_label = "VERIFIED FINDING" if finding.get("verified") else "AI OBSERVATION"
        block.append(Paragraph(
            f"#{i}  [{sev}]  {finding.get('category', 'Security Issue')}  —  {verified_label}",
            header_style,
        ))

        detail_rows = [
            ["File", finding.get("file", "")],
            ["Line", str(finding.get("line") or "N/A")],
            ["Scanner", finding.get("tool", "")],
            ["Rule", finding.get("rule_id", "")],
            ["Message", finding.get("message", "")],
        ]
        detail_table = Table(detail_rows, colWidths=[3 * cm, 13 * cm])
        detail_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 3),
        ]))
        block.append(detail_table)

        # AI Review if present
        ai = finding.get("ai_review")
        if ai:
            ai_style = ParagraphStyle(
                f"AI{i}", parent=styles["Normal"],
                fontSize=8, textColor=colors.HexColor("#334155"),
                leftIndent=8,
            )
            block.append(Spacer(1, 0.2 * cm))
            block.append(Paragraph("AI EXPLANATION", ParagraphStyle(
                f"AIH{i}", parent=styles["Normal"],
                fontSize=9, fontName="Helvetica-Bold",
                textColor=colors.HexColor("#7c3aed"),
            )))
            if ai.get("explanation"):
                block.append(Paragraph(ai["explanation"], ai_style))
            if ai.get("impact"):
                block.append(Paragraph(f"Impact: {ai['impact']}", ai_style))
            if ai.get("recommendation"):
                block.append(Paragraph(f"Recommendation: {ai['recommendation']}", ai_style))
            if ai.get("patch") and ai["patch"].strip():
                block.append(Paragraph("AI-GENERATED PATCH — Review before applying.", ParagraphStyle(
                    f"PH{i}", parent=styles["Normal"],
                    fontSize=8, fontName="Helvetica-Bold",
                    textColor=colors.HexColor("#d97706"),
                )))
                code_style = ParagraphStyle(
                    f"Code{i}", parent=styles["Normal"],
                    fontSize=7, fontName="Courier",
                    backColor=colors.HexColor("#f8fafc"),
                )
                block.append(Paragraph(
                    ai["patch"].replace("\n", "<br/>").replace(" ", "&nbsp;"),
                    code_style,
                ))

        block.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
        block.append(Spacer(1, 0.3 * cm))

        story.append(KeepTogether(block))

    # ── Disclaimer ───────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#64748b")))
    story.append(Paragraph(AI_DISCLAIMER, ParagraphStyle(
        "FooterDisclaimer",
        parent=styles["Italic"],
        fontSize=8,
        textColor=colors.HexColor("#64748b"),
    )))

    doc.build(story)
    return output_path


# ─── JSON ─────────────────────────────────────────────────────────────────────

def generate_json(scan_data: Dict[str, Any]) -> Path:
    """
    Generate a JSON export for a scan.
    Returns the Path to the generated file.
    """
    scan_id = scan_data["scan"]["scan_id"]
    output_path = settings.REPORTS_DIR / f"report_{scan_id}.json"

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "disclaimer": AI_DISCLAIMER,
        "score_disclaimer": SCORE_DISCLAIMER,
        "project": scan_data.get("project", {}),
        "scan": scan_data.get("scan", {}),
        "findings": scan_data.get("findings", []),
    }

    output_path.write_text(
        json.dumps(report, indent=2, default=str),
        encoding="utf-8",
    )
    return output_path
