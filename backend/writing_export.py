"""Offline TXT, DOCX and Vietnamese-safe PDF exports of saved drafts."""

from functools import lru_cache
from html import escape
from io import BytesIO
from pathlib import Path
import re


def _lines(content: str):
    """Read a minimal Markdown-like draft without interpreting arbitrary HTML."""
    for raw in content.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        if not line:
            yield "empty", ""
        elif re.match(r"^#{1,3}\s+", line):
            yield "heading", re.sub(r"^#{1,3}\s+", "", line)
        elif re.match(r"^[-*•]\s+", line):
            yield "bullet", re.sub(r"^[-*•]\s+", "", line)
        else:
            yield "body", line


def export_txt(title: str, content: str) -> bytes:
    return (title.strip() + "\n\n" + content.strip() + "\n").encode("utf-8-sig")


def export_docx(title: str, content: str) -> bytes:
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.left_margin = section.right_margin = Inches(0.9)
    section.top_margin = section.bottom_margin = Inches(0.85)

    normal = document.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(7)

    title_paragraph = document.add_paragraph(style="Title")
    title_paragraph.add_run(title.strip())
    title_paragraph.style.font.name = "Arial"
    title_paragraph.style.font.size = Pt(17)
    title_paragraph.style.font.color.rgb = RGBColor(0, 0, 0)
    title_paragraph.paragraph_format.space_after = Pt(17)
    # The built-in Word Title style may inherit a colored bottom border.
    # Explicitly disable it while keeping the semantic Title paragraph style.
    properties = title_paragraph._p.get_or_add_pPr()
    borders = properties.find(qn("w:pBdr"))
    if borders is None:
        borders = OxmlElement("w:pBdr")
        properties.append(borders)
    bottom = borders.find(qn("w:bottom"))
    if bottom is None:
        bottom = OxmlElement("w:bottom")
        borders.append(bottom)
    bottom.set(qn("w:val"), "nil")

    for kind, line in _lines(content):
        if kind == "empty":
            document.add_paragraph("")
        elif kind == "heading":
            paragraph = document.add_paragraph(line, style="Heading 2")
            paragraph.style.font.color.rgb = RGBColor(0, 0, 0)
        elif kind == "bullet":
            document.add_paragraph(line, style="List Bullet")
        else:
            document.add_paragraph(line)

    stream = BytesIO()
    document.save(stream)
    return stream.getvalue()


@lru_cache(maxsize=1)
def _pdf_font_name() -> str:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_candidates = (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/tahoma.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
    )
    for path in font_candidates:
        if path.is_file():
            pdfmetrics.registerFont(TTFont("TaskFlowUnicode", str(path)))
            return "TaskFlowUnicode"
    raise RuntimeError(
        "Không tìm thấy phông Unicode để xuất PDF tiếng Việt. "
        "Hãy cài DejaVu Sans hoặc sử dụng Arial/Tahoma."
    )


def export_pdf(title: str, content: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    font = _pdf_font_name()
    styles = {
        "title": ParagraphStyle("DraftTitle", fontName=font, fontSize=17, leading=25,
                                spaceAfter=17, alignment=TA_LEFT, textColor=colors.black),
        "body": ParagraphStyle("DraftBody", fontName=font, fontSize=10.5, leading=17,
                               spaceAfter=7, splitLongWords=True, wordWrap="CJK"),
        "heading": ParagraphStyle("DraftHeading", fontName=font, fontSize=12, leading=18,
                                  spaceBefore=11, spaceAfter=7, textColor=colors.black),
        "bullet": ParagraphStyle("DraftBullet", fontName=font, fontSize=10.5, leading=17,
                                 leftIndent=18, firstLineIndent=-12, spaceAfter=5),
    }
    story = [Paragraph(escape(title.strip()), styles["title"])]
    for kind, line in _lines(content):
        if kind == "empty":
            story.append(Spacer(1, 7))
        elif kind == "bullet":
            story.append(Paragraph("&#8226; " + escape(line), styles["bullet"]))
        else:
            story.append(Paragraph(escape(line), styles["heading" if kind == "heading" else "body"]))

    stream = BytesIO()
    document = SimpleDocTemplate(stream, pagesize=letter, leftMargin=64, rightMargin=64,
                                 topMargin=61, bottomMargin=61, title=title[:160], author="TaskFlow AI")
    document.build(story)
    return stream.getvalue()
