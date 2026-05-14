from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.enums import TA_LEFT

from bot.utils.logger import logger


def export_pdf(
    text: str,
    output_path: Path,
    title: str = "Documento Acessível",
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        title=title,
        language="pt-BR",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "AccessibleTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=12,
        leading=22,
    )

    heading1 = ParagraphStyle(
        "AccessibleH1",
        parent=styles["Heading1"],
        fontSize=16,
        spaceBefore=12,
        spaceAfter=6,
        leading=20,
    )

    heading2 = ParagraphStyle(
        "AccessibleH2",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=10,
        spaceAfter=4,
        leading=18,
    )

    body = ParagraphStyle(
        "AccessibleBody",
        parent=styles["Normal"],
        fontSize=11,
        leading=15,
        spaceAfter=6,
        alignment=TA_LEFT,
    )

    elements: list = []
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 6 * mm))

    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue

        lines = para.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("### "):
                elements.append(Paragraph(line[4:], heading2))
            elif line.startswith("## "):
                elements.append(Paragraph(line[3:], heading1))
            elif line.startswith("# "):
                elements.append(Paragraph(line[2:], heading1))
            else:
                elements.append(Paragraph(line, body))

    doc.build(elements)
    logger.debug("PDF exportado: {}", output_path)
    return output_path
