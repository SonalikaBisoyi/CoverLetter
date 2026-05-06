"""
PDF Export — generates beautifully formatted Resume and Cover Letter PDFs
using reportlab.
"""

import re
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ─── COLOUR PALETTE ───────────────────────────────────────────────────────────
ACCENT  = colors.HexColor("#2563EB")   # clean blue
DARK    = colors.HexColor("#0f172a")   # near-black
BODY    = colors.HexColor("#334155")   # body text
MUTED   = colors.HexColor("#64748b")   # muted
LIGHT   = colors.HexColor("#f1f5f9")   # background highlight
WHITE   = colors.white


def _base_styles():
    s = getSampleStyleSheet()

    def add(name, **kwargs):
        if name not in s:
            s.add(ParagraphStyle(name, **kwargs))
        return s[name]

    add("ResumeName",
        fontName="Helvetica-Bold", fontSize=22, textColor=DARK,
        spaceAfter=2, alignment=TA_LEFT, leading=26)

    add("ResumeContact",
        fontName="Helvetica", fontSize=9, textColor=MUTED,
        spaceAfter=10, alignment=TA_LEFT, leading=13)

    add("SectionHead",
        fontName="Helvetica-Bold", fontSize=9.5, textColor=ACCENT,
        spaceBefore=14, spaceAfter=2, letterSpacing=1.5,
        alignment=TA_LEFT)

    add("JobTitle",
        fontName="Helvetica-Bold", fontSize=10, textColor=DARK,
        spaceBefore=8, spaceAfter=0, leading=13)

    add("JobMeta",
        fontName="Helvetica-Oblique", fontSize=9, textColor=MUTED,
        spaceAfter=3, leading=12)

    add("BulletItem",
        fontName="Helvetica", fontSize=9.5, textColor=BODY,
        leftIndent=12, spaceAfter=2, leading=14, bulletIndent=0)

    add("SkillsText",
        fontName="Helvetica", fontSize=9.5, textColor=BODY,
        spaceAfter=4, leading=14)

    add("CLDate",
        fontName="Helvetica", fontSize=10, textColor=MUTED,
        spaceAfter=14, alignment=TA_RIGHT)

    add("CLSalutation",
        fontName="Helvetica-Bold", fontSize=10.5, textColor=DARK,
        spaceBefore=8, spaceAfter=10)

    add("CLBody",
        fontName="Helvetica", fontSize=10.5, textColor=BODY,
        spaceAfter=12, leading=17)

    add("CLClosing",
        fontName="Helvetica", fontSize=10.5, textColor=DARK,
        spaceBefore=14, spaceAfter=4, leading=16)

    return s


def _thin_rule(color=ACCENT, width=None, thickness=0.8):
    w = width or 6.5 * inch
    return HRFlowable(width=w, thickness=thickness, color=color,
                      spaceAfter=4, spaceBefore=2)


def _section_rule():
    return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"),
                      spaceAfter=4, spaceBefore=0)


def _parse_resume(text: str, styles) -> list:
    story = []
    lines = [l.rstrip() for l in text.splitlines()]

    SECTION_KEYWORDS = {
        "experience", "education", "skills", "projects", "certifications",
        "summary", "objective", "awards", "publications", "languages",
        "interests", "work history", "professional experience",
        "technical skills", "core competencies", "volunteering"
    }

    name_added = False
    contact_buffer = []
    i = 0

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        if not line:
            i += 1
            continue

        low = line.lower().rstrip(":")

        # ── Name ──────────────────────────────────────────────────────────────
        if not name_added:
            story.append(Paragraph(line, styles["ResumeName"]))
            name_added = True
            i += 1
            # Collect contact lines (next few non-section lines)
            while i < len(lines):
                cl = lines[i].strip()
                if not cl:
                    i += 1
                    break
                if any(kw in cl.lower() for kw in SECTION_KEYWORDS):
                    break
                contact_buffer.append(cl)
                i += 1
            if contact_buffer:
                contact_str = "  |  ".join(contact_buffer)
                story.append(Paragraph(contact_str, styles["ResumeContact"]))
            story.append(_thin_rule(thickness=2))
            continue

        # ── Section Heading ────────────────────────────────────────────────────
        is_heading = (
            (line.isupper() and 3 < len(line) < 50) or
            (low in SECTION_KEYWORDS) or
            (line.rstrip(":").lower() in SECTION_KEYWORDS)
        )
        if is_heading:
            story.append(Spacer(1, 4))
            story.append(Paragraph(line.upper().rstrip(":"), styles["SectionHead"]))
            story.append(_section_rule())
            i += 1
            continue

        # ── Bullet points ──────────────────────────────────────────────────────
        if line.startswith(("•", "-", "–", "*", "·")):
            text_val = line.lstrip("•-–*· ").strip()
            story.append(Paragraph(f"<bullet>•</bullet> {text_val}", styles["BulletItem"]))
            i += 1
            continue

        # ── Job entry (has | separator or date pattern) ────────────────────────
        has_pipe = "|" in line
        has_date = bool(re.search(r'(19|20)\d{2}', line))
        has_multi_space = "  " in line

        if has_pipe or (has_date and has_multi_space):
            parts = [p.strip() for p in re.split(r'\s{2,}|\|', line) if p.strip()]
            if len(parts) >= 2:
                story.append(Paragraph(parts[0], styles["JobTitle"]))
                story.append(Paragraph("  ·  ".join(parts[1:]), styles["JobMeta"]))
            else:
                story.append(Paragraph(line, styles["JobTitle"]))
            i += 1
            continue

        # ── Skills inline (comma-separated or colon-labeled) ───────────────────
        if ":" in line and len(line) < 120:
            label, _, rest = line.partition(":")
            if rest.strip():
                display = f"<b>{label.strip()}:</b> {rest.strip()}"
                story.append(Paragraph(display, styles["SkillsText"]))
                i += 1
                continue

        # ── Default body ──────────────────────────────────────────────────────
        story.append(Paragraph(line, styles["SkillsText"]))
        i += 1

    return story


def generate_resume_pdf(resume_text: str, output_path: str = None) -> str:
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix="tailored_resume_")
        output_path = tmp.name
        tmp.close()

    styles = _base_styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.8 * inch, rightMargin=0.8 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
    )
    story = _parse_resume(resume_text, styles)
    doc.build(story)
    return output_path


def generate_cover_letter_pdf(cover_letter_text: str, output_path: str = None) -> str:
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix="cover_letter_")
        output_path = tmp.name
        tmp.close()

    styles = _base_styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=1.1 * inch, rightMargin=1.1 * inch,
        topMargin=1.0 * inch, bottomMargin=1.0 * inch,
    )

    story = []
    story.append(_thin_rule(thickness=2, width=6.0 * inch))
    story.append(Spacer(1, 12))

    paragraphs = [p.strip() for p in cover_letter_text.split("\n\n") if p.strip()]

    for para in paragraphs:
        inner = [l.strip() for l in para.splitlines() if l.strip()]
        if not inner:
            continue

        first = inner[0]
        low_first = first.lower()

        if low_first.startswith(("dear", "to whom")):
            story.append(Paragraph(first, styles["CLSalutation"]))
            continue

        closing_words = ("sincerely", "regards", "best", "thank you", "yours", "warm")
        if any(low_first.startswith(c) for c in closing_words):
            story.append(Spacer(1, 20))
            for l in inner:
                story.append(Paragraph(l, styles["CLClosing"]))
            continue

        full = " ".join(inner)
        story.append(Paragraph(full, styles["CLBody"]))

    story.append(Spacer(1, 16))
    story.append(_thin_rule(thickness=0.5, color=colors.HexColor("#cbd5e1"), width=6.0 * inch))

    doc.build(story)
    return output_path