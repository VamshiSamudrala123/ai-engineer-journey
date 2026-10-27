"""Create evidence-backed account investigation PDFs from approved tool results."""

from collections.abc import Mapping
from datetime import datetime, timezone
from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


METRIC_FIELDS = (
    ("Total transactions", "total_transactions"),
    ("Outgoing transactions", "outgoing_transactions"),
    ("Incoming transactions", "incoming_transactions"),
    ("Self-transfers", "self_transfers"),
    ("Synthetic labeled transactions", "labeled_transactions"),
)


def _count(record, name):
    value = record.get(name)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def build_account_report_pdf(investigation: Mapping) -> bytes:
    """Return PDF bytes using *only* validated account-investigation results.

    This function doesn't call Gemini, load private data, or write files.
    Its caller is responsible for obtaining a fresh approved tool result.
    """
    if not isinstance(investigation, Mapping):
        raise ValueError("Investigation result must be a mapping")

    bank_id = _count(investigation, "bank_id")
    account_number = investigation.get("account_number")
    if (
        not isinstance(account_number, str)
        or not account_number.strip()
        or len(account_number) > 64
    ):
        raise ValueError("account_number must be a nonempty string up to 64 characters")

    values = {name: _count(investigation, name) for _, name in METRIC_FIELDS}
    total = values["total_transactions"]
    if (
        values["outgoing_transactions"]
        + values["incoming_transactions"]
        + values["self_transfers"]
        != total
    ):
        raise ValueError("Transaction counts do not reconcile")
    if values["labeled_transactions"] > total:
        raise ValueError("Labeled transactions exceed total")

    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=21 * mm,
        bottomMargin=21 * mm,
        title="InsightForge AI - Account Investigation",
        author="InsightForge AI",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportHeading",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=24,
        textColor=colors.HexColor("#263457"),
        spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="ReportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        alignment=TA_LEFT,
        spaceAfter=9,
    ))

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story = [
        Paragraph("InsightForge AI | Account Investigation", styles["ReportHeading"]),
        Paragraph("SYNTHETIC BANKING DATA - NOT REAL FINANCIAL ACTIVITY", styles["ReportBody"]),
        Paragraph(f"Report generated: {generated}", styles["ReportBody"]),
        Spacer(1, 5 * mm),
        Paragraph("Account identity", styles["Heading2"]),
        Paragraph(f"Bank ID: <b>{bank_id}</b>", styles["ReportBody"]),
        Paragraph(
            f"Account number: <b>{escape(account_number.strip())}</b>",
            styles["ReportBody"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Verified transaction counts", styles["Heading2"]),
    ]

    table_data = [["Measure", "Count"]] + [
        [label, f"{values[name]:,}"] for label, name in METRIC_FIELDS
    ]
    table = Table(table_data, colWidths=[117 * mm, 52 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEFFA")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#263457")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#DCE2ED")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    story += [table, Spacer(1, 8 * mm), Paragraph("Findings and limitations", styles["Heading2"])]

    if total == 0:
        finding = "No matching transactions were found in the available dataset."
    else:
        finding = (
            f"The dataset contains {total:,} matching transactions: "
            f"{values['outgoing_transactions']:,} outgoing, "
            f"{values['incoming_transactions']:,} incoming, and "
            f"{values['self_transfers']:,} self-transfers."
        )
    story.extend([
        Paragraph(escape(finding), styles["ReportBody"]),
        Paragraph(
            "Source: approved InsightForge account investigation tool using DuckDB. "
            "Counts reflect the available synthetic dataset, not external bank records.",
            styles["ReportBody"],
        ),
        Paragraph(
            "Synthetic laundering labels are generated dataset annotations, "
            "not evidence of real-world criminal activity. A zero label count "
            "does not establish that an account is safe.",
            styles["ReportBody"],
        ),
        Paragraph(
            "This report contains deterministic summaries of tool results; "
            "it does not include AI-generated conclusions or risk scores.",
            styles["ReportBody"],
        ),
    ])

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#68738A"))
        canvas.drawString(20 * mm, 13 * mm, "InsightForge AI | Synthetic data only")
        canvas.drawRightString(190 * mm, 13 * mm, f"Page {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
