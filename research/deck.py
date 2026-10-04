"""
Step 3: Deck generation.

Turns a structured outline (from structure.py) into a polished PowerPoint:
light background, minimal color, real bullet points, native (editable)
charts built from real data, and a source citation on every slide.
"""

import json
import os
import sys
from urllib.parse import urlparse

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.oxml.ns import qn

# ---------- Palette: light background, minimal color ----------
BG      = RGBColor(0xFF, 0xFF, 0xFF)
INK     = RGBColor(0x1F, 0x27, 0x33)   # near-black charcoal, headings
BODY    = RGBColor(0x3F, 0x46, 0x52)   # dark gray, bullet text
MUTED   = RGBColor(0x8C, 0x94, 0x9E)   # light gray, footer/source text
ACCENT  = RGBColor(0x35, 0x5C, 0x7D)   # single muted slate-blue accent
LINE    = RGBColor(0xE3, 0xE6, 0xEA)   # hairline dividers

FONT = "Calibri"

SLIDE_W_IN = 13.333
SLIDE_H_IN = 7.5


def titleize(text):
    """Title-case a string while preserving common acronyms like AI."""
    small_words = {"a", "an", "the", "and", "or", "but", "for", "on", "in", "of", "to", "with"}
    acronyms = {"ai", "ml", "ai's"}
    words = text.split()
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        if lw in acronyms:
            out.append(w.upper())
        elif i != 0 and lw in small_words:
            out.append(lw)
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)


def domain(url):
    try:
        d = urlparse(url).netloc
        return d.replace("www.", "")
    except Exception:
        return url


def source_line(sources):
    if not sources:
        return ""
    domains = sorted(set(domain(u) for u in sources if u))
    return "Source: " + ", ".join(domains)


def set_background(slide, color=BG):
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = color


def add_textbox(slide, x, y, w, h, text, size, color, bold=False, italic=False,
                 align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=FONT, spacing=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    r.font.name = font
    if spacing:
        rPr = r._r.get_or_add_rPr()
        rPr.set("spc", str(spacing))
    return tb


def add_footer(slide, page_num, sources):
    add_textbox(slide, 0.7, 7.05, 8.5, 0.3, source_line(sources), 9, MUTED, italic=True)
    add_textbox(slide, 12.0, 7.05, 0.65, 0.3, str(page_num), 10, MUTED, align=PP_ALIGN.RIGHT)


def add_header(slide, eyebrow, title):
    add_textbox(slide, 0.7, 0.5, 11.9, 0.3, eyebrow.upper(), 11, ACCENT, bold=True, spacing=150)
    add_textbox(slide, 0.7, 0.82, 11.9, 0.7, title, 26, INK, bold=True)
    # thin accent underline
    line = slide.shapes.add_connector(1, Inches(0.7), Inches(1.55), Inches(1.6), Inches(1.55))
    line.line.color.rgb = ACCENT
    line.line.width = Pt(2.25)


def add_bullets(slide, x, y, w, h, bullets):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(16)
        p.line_spacing = 1.15
        r = p.add_run()
        r.text = "\u2022  " + b
        r.font.size = Pt(17)
        r.font.color.rgb = BODY
        r.font.name = FONT


def add_chart(slide, x, y, w, h, chart_spec):
    chart_data = CategoryChartData()
    chart_data.categories = chart_spec["labels"]
    chart_data.add_series(chart_spec.get("unit", "Value"), chart_spec["values"])

    chart_type = XL_CHART_TYPE.PIE if chart_spec.get("chart_type") == "pie" else XL_CHART_TYPE.COLUMN_CLUSTERED
    gframe = slide.shapes.add_chart(chart_type, Inches(x), Inches(y), Inches(w), Inches(h), chart_data)
    chart = gframe.chart
    chart.has_legend = chart_spec.get("chart_type") == "pie"
    if chart.has_legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(11)
        chart.legend.font.color.rgb = BODY

    plot = chart.plots[0]
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.font.size = Pt(12)
    dl.font.color.rgb = INK
    dl.font.bold = True
    if chart_spec.get("chart_type") != "pie":
        dl.number_format = '0"' + "" + '"'
        dl.number_format_is_linked = False

    series = plot.series[0]
    fill = series.format.fill
    fill.solid()
    fill.fore_color.rgb = ACCENT

    if chart_spec.get("chart_type") != "pie":
        cat_ax = chart.category_axis
        cat_ax.tick_labels.font.size = Pt(11)
        cat_ax.tick_labels.font.color.rgb = BODY
        cat_ax.format.line.color.rgb = LINE
        val_ax = chart.value_axis
        val_ax.tick_labels.font.size = Pt(10)
        val_ax.tick_labels.font.color.rgb = MUTED
        val_ax.has_major_gridlines = True
        val_ax.major_gridlines.format.line.color.rgb = LINE
        val_ax.format.line.color.rgb = LINE

    chart.has_title = False
    return gframe


# ============================================================
# Slide builders
# ============================================================

def build_title_slide(prs, topic):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide)
    add_textbox(slide, 0.9, 2.55, 11.5, 0.35, "RESEARCH OVERVIEW", 13, ACCENT,
                bold=True, spacing=200)
    add_textbox(slide, 0.9, 2.95, 11.5, 1.6, titleize(topic), 40, INK, bold=True)
    add_textbox(slide, 0.9, 4.15, 11.0, 0.5,
                "How generative AI is transforming business and the workplace",
                16, BODY, italic=True)
    line = slide.shapes.add_connector(1, Inches(0.9), Inches(2.48), Inches(2.0), Inches(2.48))
    line.line.color.rgb = ACCENT
    line.line.width = Pt(2.5)
    add_textbox(slide, 0.9, 6.7, 8, 0.3, "Compiled from public research and industry reports",
                10.5, MUTED)
    return slide


def build_bullets_slide(prs, page_num, slide_data, eyebrow):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide)
    add_header(slide, eyebrow, slide_data["title"])
    add_bullets(slide, 0.85, 2.15, 10.8, 4.3, slide_data["bullets"])
    add_footer(slide, page_num, slide_data.get("sources", []))
    return slide


def build_chart_slide(prs, page_num, slide_data, eyebrow):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide)
    add_header(slide, eyebrow, slide_data["title"])

    chart_spec = slide_data["chart"]
    unit = chart_spec.get("unit", "")
    if unit:
        add_textbox(slide, 0.85, 1.95, 11.6, 0.3, unit, 12, MUTED, italic=True)

    add_chart(slide, 0.85, 2.35, 11.6, 3.9, chart_spec)

    bullets = slide_data.get("bullets", [])
    if bullets:
        add_bullets(slide, 0.85, 6.25, 11.6, 0.6, [bullets[0]])

    add_footer(slide, page_num, slide_data.get("sources", []))
    return slide


def build_closing_slide(prs, topic):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide)
    add_textbox(slide, 0, 3.0, SLIDE_W_IN, 0.3, "SUMMARY", 12, ACCENT,
                bold=True, align=PP_ALIGN.CENTER, spacing=200)
    add_textbox(slide, 1.5, 3.35, 10.33, 0.9, "Thank You", 36, INK, bold=True,
                align=PP_ALIGN.CENTER)
    add_textbox(slide, 2.17, 4.35, 9.0, 0.6,
                "How generative AI is transforming business and the workplace.",
                14, BODY, italic=True, align=PP_ALIGN.CENTER)
    return slide


# ============================================================
# Main build
# ============================================================

def build_deck(outline, out_path):
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W_IN)
    prs.slide_height = Inches(SLIDE_H_IN)

    topic = outline["topic"]
    slides = outline["slides"]

    build_title_slide(prs, topic)

    page = 2
    for s in slides:
        eyebrow = "Generative AI \u00B7 Business Impact"
        if s.get("type") == "chart" and s.get("chart"):
            build_chart_slide(prs, page, s, eyebrow)
        else:
            build_bullets_slide(prs, page, s, eyebrow)
        page += 1

    build_closing_slide(prs, topic)

    prs.save(out_path)
    print(f"Saved deck to {out_path} ({len(slides) + 2} slides)")


if __name__ == "__main__":
    outline_path = sys.argv[1] if len(sys.argv) > 1 else "output/outline_generative_ai_impact_on_business.json"
    with open(outline_path, "r", encoding="utf-8") as f:
        outline = json.load(f)

    out_name = os.path.splitext(os.path.basename(outline_path))[0].replace("outline_", "deck_") + ".pptx"
    out_path = os.path.join("output", out_name)
    build_deck(outline, out_path)
