"""Build report/bao_cao_ViKAG-Faith.docx from the HTML report that make_report.py writes.

Converting the generated HTML (instead of re-typing the report) keeps every sentence and number identical
to the PDF. Run after `python make_report.py`.
"""

import base64
import io
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "report" / "bao_cao_ViKAG-Faith.html"
OUT = ROOT / "report" / "bao_cao_ViKAG-Faith.docx"
FONT = "Times New Roman"
INK, MUTED, HEAD_BG = RGBColor(0x1F, 0x23, 0x28), RGBColor(0x55, 0x55, 0x55), "EEF1F5"
STATUS = {"ok": RGBColor(0x1D, 0x6B, 0x3A), "part": RGBColor(0xA3, 0x61, 0x0F), "no": RGBColor(0xA1, 0x2B, 0x2B)}


def shade(el, fill):
    """Background fill for a paragraph (w:pPr) or a table cell (w:tcPr)."""
    pr = el.get_or_add_pPr() if hasattr(el, "get_or_add_pPr") else el.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pr.append(shd)


def border_box(p, color="DDDDDD"):
    ppr = p._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    for side in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:space"), "6")
        e.set(qn("w:color"), color)
        bdr.append(e)
    ppr.append(bdr)


def field(paragraph, code):
    """Insert a Word field (PAGE, TOC ...); Word computes it when fields are updated."""
    run = paragraph.add_run()
    for kind, text in (("begin", None), (None, code), ("separate", None), (None, ""), ("end", None)):
        if kind:
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), kind)
        else:
            e = OxmlElement("w:instrText" if text else "w:t")
            e.set(qn("xml:space"), "preserve")
            e.text = text
        run._r.append(e)


def inline(paragraph, node, size=None, bold=False, italic=False, color=None):
    """Copy inline HTML (text, b, i, sub, code) into runs of a docx paragraph."""
    for child in node.children:
        if isinstance(child, NavigableString):
            text = " ".join(str(child).split()) if str(child).strip() else (" " if str(child) else "")
            if not text:
                continue
            # keep single spaces between inline elements, drop leading space at paragraph start
            if not paragraph.text and text.startswith(" "):
                text = text.lstrip()
            if str(child)[:1].isspace() and paragraph.text and not paragraph.text.endswith(" ") and not text.startswith(" "):
                text = " " + text
            if str(child)[-1:].isspace() and not text.endswith(" "):
                text += " "
            r = paragraph.add_run(text)
            r.bold, r.italic = bold or None, italic or None
            if size:
                r.font.size = Pt(size)
            if color:
                r.font.color.rgb = color
        elif child.name in ("b", "strong"):
            inline(paragraph, child, size, True, italic, color)
        elif child.name in ("i", "em"):
            inline(paragraph, child, size, bold, True, color)
        elif child.name == "sub":
            before = len(paragraph.runs)
            inline(paragraph, child, size, bold, italic, color)
            for r in paragraph.runs[before:]:
                r.font.subscript = True
        elif child.name == "code":
            before = len(paragraph.runs)
            inline(paragraph, child, (size or 12) - 1, bold, italic, color)
            for r in paragraph.runs[before:]:
                r.font.name = "Consolas"
        elif child.name == "br":
            paragraph.add_run().add_break()
        else:
            inline(paragraph, child, size, bold, italic, color)


def para(doc, node, style=None, size=None, align=None, italic=False, color=None, space_after=6):
    p = doc.add_paragraph(style=style)
    inline(p, node, size=size, italic=italic, color=color)
    p.paragraph_format.space_after = Pt(space_after)
    if align is not None:
        p.alignment = align
    return p


def table(doc, node, small):
    rows = node.find_all("tr")
    ncol = max(sum(int(c.get("colspan", 1)) for c in r.find_all(["td", "th"])) for r in rows)
    t = doc.add_table(rows=0, cols=ncol)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    left_all = "tl" in (node.get("class") or []) or "req" in (node.get("class") or [])
    size = 9 if small or ncol >= 7 else 10
    for r in rows:
        cells = r.find_all(["td", "th"])
        row = t.add_row()
        i = 0
        for c in cells:
            span = int(c.get("colspan", 1))
            cell = row.cells[i]
            if span > 1:
                cell = cell.merge(row.cells[i + span - 1])
            cell.paragraphs[0].text = ""
            p = cell.paragraphs[0]
            cls = (c.get("class") or [""])[0]
            inline(p, c, size=size, bold=c.name == "th" or cls in STATUS, color=STATUS.get(cls))
            p.paragraph_format.space_after = Pt(0)
            numeric = c.name == "td" and i > 0 and not left_all
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if numeric else WD_ALIGN_PARAGRAPH.LEFT
            if "req" in (node.get("class") or []) and i == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if c.name == "th":
                shade(cell._tc, HEAD_BG)
            i += span
    # Column widths follow the longest text in each column (Word's equal split wraps the method names).
    width = Cm(16.6)
    longest = [4] * ncol
    for r in rows:
        i = 0
        for c in r.find_all(["td", "th"]):
            span = int(c.get("colspan", 1))
            if span == 1:
                longest[i] = max(longest[i], min(len(c.get_text(" ", strip=True)), 45))
            i += span
    # Floor keeps short numeric columns ("218", "0,521") on one line; the cap stops long method names
    # in the first column from squeezing everything else.
    longest = [min(max(longest[0], 12), 30)] + [max(x, 7) for x in longest[1:]]
    # A header row repeats on every page and never stays alone at the bottom of one.
    first = t.rows[0]
    if all(c.name == "th" for c in rows[0].find_all(["td", "th"])):
        trpr = first._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:tblHeader"))
        for cell in first.cells:
            cell.paragraphs[0].paragraph_format.keep_with_next = True
    total = sum(longest)
    t.autofit = False
    for row in t.rows:
        for i, cell in enumerate(row.cells):
            cell.width = int(width * longest[i] / total)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def main():
    soup = BeautifulSoup(SRC.read_text(encoding="utf-8"), "html.parser")
    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    sec.left_margin = sec.right_margin = Cm(2.2)
    sec.top_margin = sec.bottom_margin = Cm(2.0)

    st = doc.styles
    st["Normal"].font.name = FONT
    st["Normal"].font.size = Pt(12)
    st["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    st["Normal"].paragraph_format.line_spacing = 1.2
    for name, size in (("Title", 18), ("Heading 1", 14), ("Heading 2", 12.5)):
        s = st[name]
        s.font.name, s.font.size, s.font.bold, s.font.color.rgb = FONT, Pt(size), True, INK
        rf = s._element.rPr.rFonts  # heading styles use theme fonts by default; pin them to Times New Roman
        for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rf.set(qn(a), FONT)
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rf.get(qn(a)) is not None:
                del rf.attrib[qn(a)]
    st["Heading 1"].paragraph_format.space_before = Pt(16)
    st["Heading 2"].paragraph_format.space_before = Pt(10)
    for name in ("List Bullet", "List Number"):
        st[name].font.name = FONT
        st[name].font.size = Pt(12)

    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field(footer, "PAGE")

    body = soup.body
    toc_done = False
    for node in body.children:
        if not getattr(node, "name", None):
            continue
        cls = node.get("class") or []
        if node.name == "h1":
            p = doc.add_paragraph(style="Title")
            inline(p, node)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif node.name == "div" and "sub" in cls:
            para(doc, node, align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, color=MUTED, space_after=12)
        elif node.name == "div" and "abstract" in cls:
            p = para(doc, node, size=11.5, space_after=12)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            shade(p._p, "F7F7F5")
            border_box(p)
        elif node.name == "h2":
            if not toc_done:  # table of contents before the first section
                p = doc.add_paragraph()
                r = p.add_run("Mục lục")
                r.bold, r.font.size = True, Pt(14)
                field(doc.add_paragraph(), 'TOC \\o "1-2" \\h \\z \\u')
                doc.add_page_break()
                toc_done = True
            doc.add_heading(node.get_text(" ", strip=True), level=1)
        elif node.name == "h3":
            doc.add_heading(node.get_text(" ", strip=True), level=2)
        elif node.name == "p":
            small = "small" in cls
            p = para(doc, node, size=10.5 if small else None)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            if "warn" in cls:
                shade(p._p, "FDF4EA")
        elif node.name in ("ul", "ol"):
            small = "small" in cls
            for n, li in enumerate(node.find_all("li", recursive=False), 1):
                if node.name == "ul":
                    p = para(doc, li, style="List Bullet", size=10.5 if small else None, space_after=3)
                else:  # numbered by hand: Word's List Number would continue across lists (refs started at 5)
                    p = doc.add_paragraph()
                    r = p.add_run(f"{n}.\t")
                    if small:
                        r.font.size = Pt(10.5)
                    inline(p, li, size=10.5 if small else None)
                    p.paragraph_format.left_indent = Cm(0.75)
                    p.paragraph_format.first_line_indent = Cm(-0.75)
                    p.paragraph_format.tab_stops.add_tab_stop(Cm(0.75))
                    p.paragraph_format.space_after = Pt(3)
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif node.name == "table":
            table(doc, node, "small" in cls)
        elif node.name == "img":
            data = base64.b64decode(node["src"].split(",", 1)[1])
            doc.add_picture(io.BytesIO(data), width=Cm(15.5))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif node.name == "div" and "cap" in cls:
            para(doc, node, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, color=MUTED, space_after=10)
        else:
            raise ValueError(f"unhandled element <{node.name} class={cls}>")

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
