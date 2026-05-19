from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    ListFlowable, ListItem,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

from bot.utils.logger import logger


class _OutlineDocTemplate(SimpleDocTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._outline_data = []
        self._outline_counter = 0
        self._prev_level = 0

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            name = flowable.style.name
            level = {"AccessibleH1": 1, "AccessibleH2": 2, "AccessibleH3": 3}.get(name)
            if level is not None:
                text = flowable.getPlainText()
                adj_level = level - 1
                if adj_level > self._prev_level + 1:
                    adj_level = self._prev_level + 1
                key = f"bm{self._outline_counter}"
                self._outline_counter += 1
                self.canv.bookmarkPage(key)
                self._outline_data.append((adj_level, text, key))
                self._prev_level = adj_level
        super().afterFlowable(flowable)

    def handle_pageEnd(self):
        for level, text, key in self._outline_data:
            self.canv.addOutlineEntry(text, key, level, closed=False)
        super().handle_pageEnd()


def export_pdf(
    text: str,
    output_path: Path,
    title: str = "Documento Acessível",
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    headings = []
    for para in text.split("\n\n"):
        for line in para.strip().split("\n"):
            line = line.strip()
            if line.startswith("### "):
                headings.append((3, line[4:]))
            elif line.startswith("## "):
                headings.append((2, line[3:]))
            elif line.startswith("# "):
                headings.append((1, line[2:]))

    def add_page_number(canvas_obj: canvas.Canvas, doc):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 9)
        page_num = canvas_obj.getPageNumber()
        canvas_obj.drawCentredString(
            A4[0] / 2, 12 * mm, f"- {page_num} -"
        )
        canvas_obj.restoreState()

    doc = _OutlineDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=25 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        title=title,
        language="pt-BR",
        author="Bot Acess",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "AccessibleTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=12,
        leading=22,
        alignment=TA_CENTER,
    )

    heading1 = ParagraphStyle(
        "AccessibleH1",
        parent=styles["Heading1"],
        fontSize=16,
        spaceBefore=12,
        spaceAfter=6,
        leading=20,
        textColor=HexColor("#1a1a2e"),
    )

    heading2 = ParagraphStyle(
        "AccessibleH2",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=10,
        spaceAfter=4,
        leading=18,
        textColor=HexColor("#16213e"),
    )

    heading3 = ParagraphStyle(
        "AccessibleH3",
        parent=styles["Heading3"],
        fontSize=12,
        spaceBefore=8,
        spaceAfter=4,
        leading=15,
        textColor=HexColor("#0f3460"),
    )

    body = ParagraphStyle(
        "AccessibleBody",
        parent=styles["Normal"],
        fontSize=11,
        leading=15,
        spaceAfter=6,
        alignment=TA_LEFT,
    )

    toc_style = ParagraphStyle(
        "AccessibleTOC",
        parent=styles["Normal"],
        fontSize=11,
        leading=18,
        leftIndent=10,
    )

    toc_title_style = ParagraphStyle(
        "TOCHeading",
        parent=styles["Heading1"],
        fontSize=16,
        spaceBefore=6,
        spaceAfter=12,
        leading=20,
    )

    elements = []

    elements.append(Spacer(1, 30 * mm))
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 10 * mm))

    if headings:
        elements.append(Paragraph("Índice", toc_title_style))
        for level, heading_text in headings:
            indent = 10 + (level - 1) * 15
            prefix = {1: "", 2: "  ", 3: "    "}[level]
            style = ParagraphStyle(
                f"TOCLevel{level}",
                parent=toc_style,
                leftIndent=indent,
                fontSize={1: 12, 2: 11, 3: 10}[level],
            )
            elements.append(Paragraph(f"{prefix}{heading_text}", style))
        elements.append(Spacer(1, 10 * mm))
        elements.append(PageBreak())

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
                elements.append(Paragraph(line[4:], heading3))
            elif line.startswith("## "):
                elements.append(Paragraph(line[3:], heading2))
            elif line.startswith("# "):
                elements.append(Paragraph(line[2:], heading1))
            else:
                elements.append(Paragraph(line, body))

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    logger.debug("PDF exportado com bookmarks e numeracao: {}", output_path)
    return output_path
