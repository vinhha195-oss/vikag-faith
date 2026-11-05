"""Build nop_bai/ViKAG-Faith_BaiBao.docx: the project written as a 12-14 page paper in the course template
(title, author line, Tên đề tài / English, Abstract + key findings, 1. Introduction ... 8. Kết luận, Caveats, References).

Layout: A4, 2.5 cm margins, Times New Roman 13 pt, native Office equations, section headings with a rule above.
Every number is read from outputs/analysis/results.json. Run after s7_analysis.py.
"""

import io
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT  # noqa: E402
from docx.oxml import OxmlElement, parse_xml  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402

AUTHOR = "Hà Văn Vinh"   # điền họ tên tác giả
COURSE = "Xử lý ngôn ngữ tự nhiên nâng cao"     # điền tên môn học

ROOT = Path(__file__).resolve().parent
R = json.load(open(ROOT / "outputs" / "analysis" / "results.json", encoding="utf-8"))
OUT = ROOT / "nop_bai" / "ViKAG-Faith_BaiBao.docx"
FIG = ROOT / "report" / "paper_figs"
FIG.mkdir(parents=True, exist_ok=True)
FONT = "Times New Roman"
BODY_PT = 13
TEAL, ORANGE, GREY, RED, LIGHT = "#1F3A5F", "#B0763A", "#6B7280", "#A23B3B", "#B8C4D3"
plt.rcParams.update({"font.family": FONT, "font.size": 9, "axes.edgecolor": "#888888"})

CL, CO, CMP, REV, SY, QA = R["claim_level"], R["answer_level_correlation"], R["comparisons"], R["revise"], R["systems"], R["qa"]
AG = R["agreement"]
AC, AQ, ACG = AG["audit"], AG["audit_G"], AG["audit_CG"]
SENS = ACG["sensitivity"]
TH = R["thresholds"]
N_CLAIMS_ALL = sum(1 for _ in open(ROOT / "outputs" / "claims.jsonl", encoding="utf-8"))
_story = (ROOT / "demo" / "vikag_faith_demo.html").read_text(encoding="utf-8")  # catch counts come from make_demo.py
_at = _story.index("const DATA = ") + 13
D2 = json.load(open(ROOT / "outputs" / "analysis" / "results_dot2.json", encoding="utf-8"))  # second round, separate file
V3 = D2["methods"]["nli_zs_v3"]
CATCH = json.loads(_story[_at:_story.index(chr(10), _at)].strip().rstrip(";"))["summary"]["catch"]


def f(x, d=3):
    return "–" if x is None else f"{x:.{d}f}".replace(".", ",").replace("-", "−")


def pct(x, d=0):
    return f"{100 * x:.{d}f}%".replace(".", ",")


NAMES = {
    "judge_7b": "LLM-judge Qwen2.5-7B", "judge_3b": "LLM-judge Qwen2.5-3B",
    "nli_zs_v1": "NLI zero-shot, V1", "nli_zs_v2": "NLI zero-shot, V2 (+graph)",
    "nli_ft_v1": "NLI fine-tune, V1", "nli_ft_v2": "NLI fine-tune, V2 (+graph)",
    "nli_nosynth_v1": "NLI fine-tune chỉ ViNLI, V1", "nli_zs_v1+rule": "NLI zero-shot V1 + rule",
    "nli_ft_v1+rule": "NLI fine-tune V1 + rule", "nli_selfcheck": "SelfCheckGPT-NLI",
    "rule_only": "Chỉ rule số/ngày", "majority_supported": "Luôn đoán supported",
    "ragas_7b": "RAGAS (Qwen2.5-7B)", "ragas_3b": "RAGAS (Qwen2.5-3B)",
}


# ---------------------------------------------------------------- figures
def save(fig, name):
    path = FIG / name
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_architecture():
    # Coordinates are in inches on a 9 x 4.6 canvas, so box sizes and font sizes stay in proportion.
    W, H = 9.0, 4.6
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    def box(x, y, w, h, title, body="", fc="#F3F7F8", ec="#5B6670"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", fc=fc, ec=ec, lw=0.9))
        ax.text(x + w / 2, y + h - 0.13, title, ha="center", va="top", fontsize=7.6, fontweight="bold")
        if body:
            ax.text(x + w / 2, y + h - 0.36, body, ha="center", va="top", fontsize=6.8, linespacing=1.35)

    def arrow(x1, y1, x2, y2, color="#5B6670", dashed=False):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9, color=color, lw=0.9,
                                     linestyle="--" if dashed else "-", shrinkA=0, shrinkB=0))

    ax.text(0.05, 4.48, "Sinh câu trả lời", fontsize=8.5, fontweight="bold", color=TEAL)
    box(0.05, 3.15, 1.5, 1.05, "ViHERMES", "100 câu hỏi\n20 câu mỗi mức 1–5 hop")
    box(1.95, 3.72, 1.9, 0.62, "Naive RAG", "BM25 + bge-m3, 8 đoạn")
    box(1.95, 3.0, 1.9, 0.62, "GraphRAG", "4 hạt giống + lan truyền")
    box(4.25, 3.15, 1.75, 1.05, "Qwen2.5-3B", "cùng prompt\nngân sách 6.000 ký tự")
    box(6.4, 3.15, 1.6, 1.05, "Câu trả lời", "200 câu trả lời\nmẫu đánh giá: 80")
    arrow(1.55, 3.67, 1.95, 4.03); arrow(1.55, 3.67, 1.95, 3.31)
    arrow(3.85, 4.03, 4.25, 3.85); arrow(3.85, 3.31, 4.25, 3.5); arrow(6.0, 3.67, 6.4, 3.67)

    ax.text(0.05, 2.62, "Đánh giá faithfulness mức claim", fontsize=8.5, fontweight="bold", color=TEAL)
    box(0.05, 1.35, 1.5, 1.05, "Tách claim", "Qwen2.5-3B\nprompt có ví dụ")
    box(1.95, 1.35, 1.9, 1.05, "Tập bằng chứng", "đoạn truy xuất\n+ đoạn vàng\n+ thông tin graph")
    box(4.25, 1.2, 1.75, 1.35, "Metric tự động", "RAGAS · LLM-judge\nNLI V1/V2 (ZS, FT)\nrule · SelfCheckGPT")
    box(6.4, 1.35, 1.15, 1.05, "Nhãn chuẩn", "silver (Claude)\n+ người (mù)")
    box(7.85, 1.35, 1.1, 1.05, "Meta-eval.", "macro-F1\nAUROC\nSpearman", fc="#FDF1E4", ec=ORANGE)
    arrow(7.2, 3.15, 0.8, 2.4, dashed=True)
    arrow(1.55, 1.87, 1.95, 1.87); arrow(3.85, 1.87, 4.25, 1.87); arrow(6.0, 1.87, 6.4, 1.87); arrow(7.55, 1.87, 7.85, 1.87)

    box(4.25, 0.05, 1.75, 0.85, "Verify-then-revise", "judge 7B gắn cờ → 3B viết lại\ntối đa 2 vòng", fc="#E8F2F3", ec=TEAL)
    arrow(5.12, 1.2, 5.12, 0.9, color=TEAL)
    ax.text(6.15, 0.47, "chấm lại bằng judge 7B,\nso token F1 với đáp án", fontsize=6.8, color=TEAL, style="italic", va="center")
    return save(fig, "fig1_architecture.png")


def fig_claim_level():
    keys = ["majority_supported", "rule_only", "nli_zs_v2", "nli_selfcheck", "nli_zs_v1", "nli_nosynth_v1",
            "judge_3b", "nli_ft_v2", "judge_7b", "nli_ft_v1"]
    keys = [k for k in keys if k in CL]
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    vals = [CL[k]["macro_f1"] for k in keys]
    lo = [CL[k]["macro_f1"] - CL[k]["ci95"][0] for k in keys]
    hi = [CL[k]["ci95"][1] - CL[k]["macro_f1"] for k in keys]
    col = [TEAL if k.startswith("judge") else GREY if k in ("majority_supported", "rule_only", "nli_selfcheck") else ORANGE for k in keys]
    ax.barh([NAMES[k] for k in keys], vals, xerr=[lo, hi], color=col, error_kw={"ecolor": "#333", "lw": 0.7, "capsize": 2})
    for i, k in enumerate(keys):
        ax.text(CL[k]["ci95"][1] + 0.01, i, f(CL[k]["macro_f1"]), va="center", fontsize=7.5)
    ax.set_xlim(0, 0.75)
    ax.set_xlabel(f"Macro-F1 trên {R['claims_test']} claim test (nhãn silver), thanh lỗi = KTC 95% bootstrap")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color="#e5e5e5")
    ax.set_axisbelow(True)
    return save(fig, "fig2_claim_level.png")


def fig_human_vs_silver():
    keys = ["judge_7b", "nli_zs_v1", "nli_nosynth_v1", "nli_ft_v1", "judge_3b", "nli_selfcheck"]
    fig, ax = plt.subplots(figsize=(7.0, 2.9))
    y = range(len(keys))
    h = [SENS[k]["macro_f1_vs_human"] for k in keys]
    c = [SENS[k]["macro_f1_vs_claude"] for k in keys]
    ax.barh([i + 0.2 for i in y], h, height=0.38, color=RED, label="theo nhãn người")
    ax.barh([i - 0.2 for i in y], c, height=0.38, color=LIGHT, label="theo nhãn Claude")
    for i, (a, b) in enumerate(zip(h, c)):
        ax.text(a + 0.006, i + 0.2, f(a), va="center", fontsize=7.3)
        ax.text(b + 0.006, i - 0.2, f(b), va="center", fontsize=7.3)
    ax.set_yticks(list(y))
    ax.set_yticklabels([NAMES[k] for k in keys])
    ax.invert_yaxis()
    ax.set_xlim(0, 0.7)
    ax.set_xlabel(f"Macro-F1 trên {ACG['n']} claim có nhãn người")
    ax.legend(frameon=False, loc="lower right", fontsize=7.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return save(fig, "fig3_human_vs_silver.png")


def fig_hop():
    hops = ["1", "2", "3", "4", "5"]
    fig, ax = plt.subplots(figsize=(6.4, 2.5))
    for s, col, lab in (("naive", GREY, "Naive RAG"), ("graph", TEAL, "GraphRAG")):
        ax.plot([int(h) for h in hops], [SY["by_hop"][s][h]["GGF"] for h in hops], marker="o", color=col, label=lab)
    for h in hops:
        a, b = SY["by_hop"]["naive"][h]["GGF"], SY["by_hop"]["graph"][h]["GGF"]
        for v, col, up in ((a, GREY, a >= b), (b, TEAL, b > a)):
            ax.text(int(h), v + (0.045 if up else -0.06), f(v), ha="center", va="bottom" if up else "top", fontsize=7, color=col)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xlabel("Số hop của câu hỏi")
    ax.set_ylabel("GGF trung bình")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", color="#e5e5e5")
    ax.legend(frameon=False, loc="lower left", fontsize=7.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return save(fig, "fig4_hop.png")


# ---------------------------------------------------------------- docx helpers
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, side, Cm(2.5))
TEXT_W = Cm(21.0 - 2 * 2.5)

normal = doc.styles["Normal"]
normal.font.name, normal.font.size = FONT, Pt(BODY_PT)
normal.font.color.rgb = RGBColor(0, 0, 0)
normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
normal.paragraph_format.space_after = Pt(5)
normal.paragraph_format.line_spacing = 1.15
for name, size, before, after in (("Heading 1", 24, 0, 10), ("Heading 2", 18, 18, 8), ("Heading 3", 14, 12, 6)):
    s = doc.styles[name]
    s.font.name, s.font.size, s.font.bold = FONT, Pt(size), True
    s.font.color.rgb = RGBColor(0, 0, 0)
    s.font.italic = False
    rf = s._element.rPr.rFonts
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), FONT)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]
    s.paragraph_format.space_before, s.paragraph_format.space_after = Pt(before), Pt(after)
for name in ("List Bullet", "List Paragraph"):
    doc.styles[name].font.name = FONT
    doc.styles[name].font.size = Pt(BODY_PT)

TOKEN = re.compile(r"(\*\*.+?\*\*|\*.+?\*|`.+?`|P_sup|P_con|τ_s|τ_c|κ|ρ|∪|(?<![\w/.-])p(?= = )|(?<=tập claim )C(?=:)|(?<=Với claim )c(?= và)|(?<=cửa sổ )w(?=:))")
INLINE_MATH = {"P_sup", "P_con", "τ_s", "τ_c", "κ", "ρ", "∪", "p", "C", "c", "w"}
M_NS = ('xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"')


def mr(t, plain=False, size=None):
    """One OMML run: italic maths by default, upright for names and words, always Cambria Math."""
    sty = '<m:rPr><m:sty m:val="p"/></m:rPr>' if plain else ""
    sz = f'<w:sz w:val="{int(size * 2)}"/>' if size else ""
    return (f'<m:r>{sty}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>{sz}</w:rPr>'
            f'<m:t xml:space="preserve">{t}</m:t></m:r>')


def msub(base, sub):
    return f"<m:sSub><m:e>{base}</m:e><m:sub>{sub}</m:sub></m:sSub>"


def mfrac(num, den):
    return f"<m:f><m:num>{num}</m:num><m:den>{den}</m:den></m:f>"


def mmax(under, arg):
    return (f'<m:func><m:fName><m:limLow><m:e>{mr("max", True)}</m:e><m:lim>{under}</m:lim></m:limLow></m:fName>'
            f"<m:e>{arg}</m:e></m:func>")


def omath(body):
    return parse_xml(f"<m:oMath {M_NS}>{body}</m:oMath>")


def inline_math(tok, size=None):
    if "_" in tok:
        a, b = tok.split("_")
        return msub(mr(a, size=size), mr(b, len(b) > 1, size))
    return mr(tok, size=size)


def rich(p, text, size=None, bold=False, italic=False):
    """Add runs to p; **bold**, *italic* and `code` spans are honoured."""
    for part in TOKEN.split(text):
        if not part:
            continue
        if part in INLINE_MATH:
            p._p.append(omath(inline_math(part, size)))
            continue
        b, i, code = bold, italic, False
        if part.startswith("**"):
            part, b = part[2:-2], True
        elif part.startswith("`"):
            part, code = part[1:-1], True
        elif part.startswith("*"):
            part, i = part[1:-1], True
        r = p.add_run(part)
        r.bold, r.italic = b or None, i or None
        if code:
            r.font.name = FONT
            r.font.size = Pt(size or BODY_PT)
        elif size:
            r.font.size = Pt(size)
    return p


def para(text, size=None, align=WD_ALIGN_PARAGRAPH.LEFT, after=5, italic=False):
    p = doc.add_paragraph()
    rich(p, text, size=size, italic=italic)
    p.alignment = align
    p.paragraph_format.space_after = Pt(after)
    return p


def rule_above(p):
    ppr = p._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    top = OxmlElement("w:top")
    for k, v in (("w:val", "single"), ("w:sz", "4"), ("w:space", "8"), ("w:color", "BFBFBF")):
        top.set(qn(k), v)
    bdr.append(top)
    ppr.append(bdr)


def h2(text):
    p = doc.add_heading(text, level=2)
    rule_above(p)
    return p


def h3(text):
    return doc.add_heading(text, level=3)


def bullets(items, size=None):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        rich(p, it, size=size)
        p.paragraph_format.space_after = Pt(4)


def numbered(items, start=1):
    for n, it in enumerate(items, start):
        p = doc.add_paragraph()
        p.add_run(f"{n}.\t")
        rich(p, it)
        p.paragraph_format.left_indent = Cm(0.75)
        p.paragraph_format.first_line_indent = Cm(-0.75)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(0.75))
        p.paragraph_format.space_after = Pt(4)


def equation(body, n):
    """Numbered display equation: native OMML centred in a borderless table, number flush right."""
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for c, width in zip(t.rows[0].cells, (TEXT_W - Cm(1.2), Cm(1.2))):
        c.width = width
    left, right = t.rows[0].cells
    p = left.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p._p.append(parse_xml(f"<m:oMathPara {M_NS}><m:oMath>{body}</m:oMath></m:oMathPara>"))
    q = right.paragraphs[0]
    q.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    q.add_run(f"({n})")
    right.vertical_alignment = 1  # centre
    after = doc.add_paragraph()
    after.paragraph_format.space_after = Pt(0)
    after.paragraph_format.line_spacing = Pt(4)


FIGN, TABN = [0], [0]


def figure(path, caption, width=Cm(16.5)):
    FIGN[0] += 1
    doc.add_picture(str(path), width=min(width, TEXT_W))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.keep_with_next = True
    p = doc.add_paragraph()
    r = p.add_run(f"Hình {FIGN[0]}. ")
    r.bold, r.font.size = True, Pt(10)
    rich(p, caption, size=10, italic=True)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    return FIGN[0]


def shade(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    for k, v in (("w:val", "clear"), ("w:color", "auto"), ("w:fill", fill)):
        shd.set(qn(k), v)
    tcpr.append(shd)


def table(caption, header, rows, widths, align=None, size=10.5, bold_rows=()):
    """Caption above the table, header bold on a light fill; align: 'l'/'c'/'r' per column."""
    TABN[0] += 1
    p = doc.add_paragraph()
    r = p.add_run(f"Bảng {TABN[0]}. {caption}")
    r.bold, r.font.size = True, Pt(10)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_after = Pt(3)
    t = doc.add_table(rows=0, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    align = align or ["l"] + ["c"] * (len(header) - 1)
    al = {"l": WD_ALIGN_PARAGRAPH.LEFT, "c": WD_ALIGN_PARAGRAPH.CENTER, "r": WD_ALIGN_PARAGRAPH.RIGHT}
    total = sum(widths)
    for ri, row in enumerate([header] + rows):
        new_row = t.add_row()
        new_row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        cells = new_row.cells
        for ci, val in enumerate(row):
            c = cells[ci]
            c.width = int(TEXT_W * widths[ci] / total)
            c.paragraphs[0].text = ""
            rich(c.paragraphs[0], str(val), size=size, bold=ri == 0 or (ri - 1) in bold_rows)
            c.paragraphs[0].paragraph_format.keep_with_next = ri < len(rows)  # keep the table on one page
            c.paragraphs[0].alignment = al["c" if ri == 0 and ci > 0 else align[ci]]
            c.paragraphs[0].paragraph_format.space_after = Pt(1)
            if ri == 0:
                shade(c, "F2F2F2")
                c.paragraphs[0].paragraph_format.keep_with_next = True
    trpr = t.rows[0]._tr.get_or_add_trPr()
    trpr.append(OxmlElement("w:tblHeader"))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return TABN[0]


def page_number_footer():
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for kind, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), kind)
        else:
            e = OxmlElement("w:instrText")
            e.set(qn("xml:space"), "preserve")
            e.text = text
        run._r.append(e)
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)


# ---------------------------------------------------------------- content
page_number_footer()
F1, F2, F3, F4 = fig_architecture(), fig_claim_level(), fig_human_vs_silver(), fig_hop()
j7, ft, zs, ns = CL["judge_7b"], CL["nli_ft_v1"], CL["nli_zs_v1"], CL["nli_nosynth_v1"]
c_ft_j7, c_ft_zs, c_ns_zs = CMP["nli_ft_v1 - judge_7b"], CMP["nli_ft_v1 - nli_zs_v1"], CMP["nli_nosynth_v1 - nli_zs_v1"]
RA, R1, R2 = REV["all"], REV["by_max_rounds"]["1"], REV["by_max_rounds"]["2"]
P2 = REV["by_max_rounds"]["round2_vs_round1"]
hj7, hft, hzs = SENS["judge_7b"]["macro_f1_vs_human"], SENS["nli_ft_v1"]["macro_f1_vs_human"], SENS["nli_zs_v1"]["macro_f1_vs_human"]
qp = AG.get("quick_passes", [])

doc.add_heading("Đánh giá tính trung thực mức mệnh đề cho hệ hỏi đáp GraphRAG tiếng Việt trên văn bản pháp quy y tế", level=1)
p = doc.add_paragraph()
rich(p, f"{AUTHOR} · *Học viên cao học – {COURSE}*", size=10)
p = doc.add_paragraph()
rich(p, "**Tên đề tài:** Đánh giá và kiểm chứng tính trung thực (faithfulness) mức mệnh đề cho KAG/GraphRAG tiếng Việt dựa trên đồ thị tri thức "
        "**English:** *ViKAG-Faith: Graph-Grounded Claim-Level Faithfulness Evaluation and Verification for Vietnamese Knowledge-Augmented Generation*", size=10.5)

p = doc.add_paragraph()
rich(p, f"**Abstract.** Hệ hỏi đáp RAG/GraphRAG tiếng Việt thường được chấm bằng F1 hoặc một điểm LLM-judge cho cả câu trả lời; không điểm nào "
        f"cho biết mệnh đề nào được bằng chứng hỗ trợ, mệnh đề nào bịa thêm hay mâu thuẫn. Với văn bản pháp quy, một ngày hiệu lực hay một mức "
        f"phạt sai là đủ gây hậu quả. Chúng tôi xây dựng ViKAG-Faith, một quy trình đánh giá faithfulness mức mệnh đề (claim) trên ViHERMES [1]: hai hệ "
        f"(Naive RAG và GraphRAG dùng đồ thị pháp lý của ViHERMES) cùng dùng Qwen2.5-3B trả lời 100 câu hỏi (1–5 hop); câu trả lời được tách thành "
        f"{N_CLAIMS_ALL} claim, trong đó {R['claims_total']} claim của 80 câu trả lời được gán nhãn supported / contradicted / unsupported trên một tập "
        f"bằng chứng chung. Chúng tôi so sánh RAGAS [2], LLM-judge, SelfCheckGPT [8], verifier NLI đa ngôn ngữ có và không có thông tin đồ thị, rule "
        f"số/ngày, verifier fine-tune bằng dữ liệu tổng hợp trong miền, và vòng kiểm chứng rồi sửa (verify-then-revise). Nhãn chính do Claude gán "
        f"(silver); {ACG['n']} claim được người gán mù qua {1 + len(qp)} lượt.")
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
bullets([
    f"**LLM-judge 7B là metric đáng tin nhất khi so với người.** Trên {ACG['n']} claim có nhãn người, judge Qwen2.5-7B đạt macro-F1 {f(hj7)}, "
    f"cao hơn các verifier NLI ({f(hzs)}–{f(hft)}); ở mức câu trả lời, RAGAS 7B tương quan cao nhất với GGF chuẩn (ρ = {f(CO['ragas_7b']['spearman'])}).",
    f"**Fine-tune với dữ liệu tổng hợp chỉ tốt hơn theo nhãn silver.** Verifier fine-tune đạt {f(ft['macro_f1'])} so với {f(zs['macro_f1'])} của "
    f"zero-shot trên nhãn Claude, nhưng theo nhãn người hai bản ngang nhau ({f(hft)} và {f(hzs)}); thông tin đồ thị dạng văn bản làm verifier kém đi.",
    f"**Verify-then-revise đổi độ đầy đủ lấy độ trung thực.** Tỉ lệ claim mâu thuẫn giảm {pct(RA['CR_before'], 1)} → {pct(RA['CR_after'], 1)} nhưng "
    f"token F1 giảm {f(RA['answer_f1_before'])} → {f(RA['answer_f1_after'])}: bộ sinh 3B chủ yếu xóa claim bị gắn cờ.",
    f"**Nhãn silver chỉ là ước lượng.** Claude trùng người ở {pct(ACG['acc'])} số claim (κ = {f(ACG['kappa'], 2)}) và khắt khe hơn người; "
    f"thứ hạng metric thay đổi khi đổi bộ nhãn (mục 6.2 và Caveats).",
])

# 1 ------------------------------------------------------------------
para("**Keywords:** GraphRAG, faithfulness, claim-level verification, tiếng Việt, ViHERMES.", after=8)
h2("1. Introduction")
bullets([
    "*Bối cảnh:* GraphRAG và KAG [3]–[6] đưa đồ thị tri thức vào bước truy xuất để trả lời câu hỏi nhiều bước. ViHERMES [1] xây benchmark "
    "multi-hop cho văn bản pháp quy y tế Việt Nam cùng đồ thị cấu trúc pháp lý, và cho thấy bỏ module Auditor (kiểm chứng) làm điểm LLM-judge "
    "giảm từ 0,7554 xuống 0,6823. Kiểm chứng là thành phần quan trọng, nhưng chính cách đo độ trung thực trên tiếng Việt chưa được đánh giá.",
    "*Vấn đề:* điểm F1 hoặc một điểm judge cho cả câu trả lời không chỉ ra mệnh đề nào sai. Các metric faithfulness phổ biến (RAGAS [2], "
    "LLM-as-a-judge [17], SelfCheckGPT [8]) được kiểm định chủ yếu trên tiếng Anh; DSC2025 ViHallu [11] đánh giá hallucination tiếng Việt nhưng "
    "không gắn với đồ thị tri thức hay bằng chứng truy xuất.",
    "*Hướng tiếp cận:* tách câu trả lời thành claim nguyên tử (như FActScore [18]), đối chiếu từng claim với một tập bằng chứng chung "
    "(đoạn truy xuất, đoạn vàng và thông tin đồ thị), rồi đo mức khớp của từng metric tự động với nhãn chuẩn (meta-evaluation).",
    "*RQ1:* các metric faithfulness hiện có (RAGAS, LLM-judge, SelfCheckGPT, NLI zero-shot) khớp với nhãn chuẩn đến mức nào trên tiếng Việt?",
    "*RQ2:* verifier dùng thông tin đồ thị, rule số/ngày và fine-tune bằng dữ liệu tổng hợp trong miền có phát hiện claim sai tốt hơn verifier NLI chung không?",
    "*RQ3:* vòng verify-then-revise giảm tỉ lệ claim không được hỗ trợ bao nhiêu, và có làm giảm chất lượng trả lời không?",
    f"*Contributions:* (C1) quy trình đánh giá mức claim tái lập được trên ViHERMES (7 bước, chạy trên Colab T4); (C2) bộ dữ liệu ViFaithKAG bản "
    f"pilot: {R['claims_total']} claim có nhãn silver, {ACG['n']} claim có nhãn người, kèm điểm của mọi metric; (C3) meta-evaluation 12 biến thể metric "
    f"kèm ablation đồ thị, rule, dữ liệu tổng hợp và số vòng sửa; (C4) phân tích độ tin cậy của nhãn LLM so với người, cho thấy thứ hạng metric "
    f"phụ thuộc vào nguồn nhãn.",
])

# 2 ------------------------------------------------------------------
h2("2. Related Work")
bullets([
    "*Đo faithfulness của RAG:* RAGAS [2] định nghĩa faithfulness là tỉ lệ statement suy ra được từ ngữ cảnh, dùng LLM để tách statement và phán xét. "
    "FActScore [18] chấm độ chính xác của từng atomic fact so với nguồn tri thức. LLM-as-a-judge [17] dùng LLM mạnh làm giám khảo; độ khớp với người "
    "phụ thuộc kích thước và miền.",
    "*Phát hiện hallucination:* SelfCheckGPT [8] không cần bằng chứng, dựa vào độ nhất quán giữa các câu trả lời lấy mẫu. SemEval-2024 SHROOM [9] "
    "và SemEval-2025 Mu-SHROOM [10] chuẩn hóa bài toán phát hiện đoạn bịa; DSC2025 ViHallu [11] là cuộc thi tiếng Việt đầu tiên về chủ đề này.",
    "*NLI tiếng Việt và đa ngôn ngữ:* XNLI [19] có tiếng Việt; ViNLI [20] là kho NLI tiếng Việt (nằm trong VLUE [12]). mDeBERTa-v3 [13] huấn luyện "
    "trên NLI đa ngôn ngữ [14] là verifier encoder phổ biến.",
    "*Graph RAG, KAG và văn bản pháp quy:* RAG [7], GraphRAG [4], LightRAG [5], HippoRAG 2 [6] và KAG [3] dùng đồ thị để truy xuất hoặc suy luận. "
    "ViHERMES [1] dựng đồ thị Văn bản–Điều–Khoản với quan hệ sửa đổi, thay thế, dẫn chiếu cho văn bản y tế.",
    "*Vị trí của đề tài:* không đề xuất hệ hỏi đáp mới mà đánh giá các metric kiểm chứng trên tiếng Việt, ở mức claim, có so với nhãn người; "
    "dùng nguyên dữ liệu và đồ thị của ViHERMES, chỉ thêm tầng đánh giá.",
])

# 3 ------------------------------------------------------------------
h2("3. Proposed Method")
para(f"Hình 1 tóm tắt quy trình: phần trên sinh câu trả lời bằng hai hệ, phần dưới đánh giá từng claim; nhánh verify-then-revise dùng "
     f"kết quả kiểm chứng để viết lại câu trả lời.")
figure(F1, "Quy trình ViKAG-Faith. Đường nét đứt: các câu trả lời của mẫu 80 được đưa sang bước tách claim.")
numbered([
    "**Hai hệ hỏi đáp:** cùng corpus ViHERMES (998 đoạn, 471 văn bản), cùng bộ truy xuất hybrid BM25 [15] + bge-m3 [16] (trọng số 0,5), cùng "
    "ngân sách 6.000 ký tự và bộ sinh Qwen2.5-3B-Instruct [21] (nhiệt độ 0). *Naive RAG* lấy 8 đoạn tốt nhất; *GraphRAG* lấy 4 đoạn hạt giống "
    "rồi lan truyền trên đồ thị của ViHERMES (`GraphPropagator`, độ sâu ≤ 4, tối đa 8 nút) và thêm danh sách quan hệ giữa văn bản vào prompt. "
    "Khác biệt giữa hai hệ vì vậy chỉ đến từ cách lấy ngữ cảnh.",
    "**Tách claim:** Qwen2.5-3B, prompt tiếng Việt có hai ví dụ, yêu cầu mỗi claim một vị từ chính, tự hiểu được (thay đại từ bằng tên cụ "
    "thể), giữ nguyên số, ngày, số hiệu văn bản. Claim chứa từ ba giá trị số trở lên được đánh dấu để người gán kiểm tra.",
    "**Tập bằng chứng chung:** với mỗi câu trả lời, bằng chứng = các đoạn hệ đã truy xuất ∪ các đoạn vàng của câu hỏi (ViHERMES cung cấp), kèm "
    "thông tin đồ thị của từng đoạn (tên văn bản, số hiệu, quan hệ). Mọi metric và người gán đều dùng đúng tập này, nên chênh lệch giữa các metric "
    "phản ánh chất lượng metric chứ không phải chất lượng truy xuất.",
    "**Nhãn và metric câu trả lời:** mỗi claim mang một nhãn supported / contradicted / unsupported. Với câu trả lời có tập claim C:",
])
CARD = mr("|C|")
equation(mr("GGF", True) + mr(" = ", True) + mfrac(mr("|{c ∈ C : c") + mr(" supported", True) + mr("}|"), CARD), 1)
equation(mr("CR", True) + mr(" = ", True) + mfrac(mr("|{c ∈ C : c") + mr(" contradicted", True) + mr("}|"), CARD) + mr(" ,     ", True)
         + mr("UR", True) + mr(" = ", True) + mfrac(mr("|{c ∈ C : c") + mr(" unsupported", True) + mr("}|"), CARD), 2)
numbered([
    "**Metric dựa trên LLM:** RAGAS faithfulness tái hiện theo hai prompt gốc của thư viện (tách statement, rồi phán xét NLI theo lô) và LLM-judge "
    "mức claim gán 3 nhãn cho các claim của đề tài; cả hai chạy với Qwen2.5-3B và 7B qua Ollama. Đầu ra không đọc được được loại khỏi phép đo, "
    "không mặc định thành một nhãn.",
    f"**Verifier NLI:** mDeBERTa-v3-base-xnli-multilingual [13], [14] chạy trên cửa sổ 900 ký tự (bước 700). Với claim c và các cửa sổ w:",
], start=5)
equation(msub(mr("P"), mr("sup", True)) + mr("(c) = ") + mmax(mr("w"), mr("P(") + mr("entail", True) + mr(" | w, c)")), 3)
equation(msub(mr("P"), mr("con", True)) + mr("(c) = ") + mmax(mr("w ∈ ") + mr("top-2 overlap", True), mr("P(") + mr("contra", True) + mr(" | w, c)")), 4)
para(f"Contradiction chỉ xét hai cửa sổ trùng từ nhiều nhất với claim, vì NLI hay gán “contradiction” cho văn bản không liên quan. Nhãn: supported "
     f"nếu P_sup ≥ τ_s, ngược lại contradicted nếu P_con ≥ τ_c, còn lại unsupported; (τ_s, τ_c) chọn trên tập dev (V1 zero-shot: {f(TH['zs_v1'][0], 2)}, "
     f"{f(TH['zs_v1'][1], 2)}). Hai biến thể đầu vào: **V1** chỉ đoạn văn; **V2** thêm tên văn bản, số hiệu và quan hệ lấy từ đồ thị vào đầu mỗi cửa sổ; "
     f"**V3** chỉ thêm tối đa 3 triple có chung từ khóa với claim (từ 467 triple của đồ thị) và, qua mutual index, đoạn gốc của văn bản mà claim nêu số hiệu.")
numbered([
    "**Fine-tune verifier bằng dữ liệu tổng hợp:** 12.000 cặp ViNLI [20] + 3.328 cặp tạo từ các đoạn *không* thuộc mẫu đánh giá: supported = câu "
    "gốc; contradicted = đổi một con số, ngày hoặc thêm phủ định (“không”); unsupported = câu của đoạn khác cùng văn bản. Huấn luyện 1 epoch, "
    "lr 5e-6, batch 4 × tích lũy 4, float32, giữ checkpoint tốt nhất trên dev. Ablation: cùng cấu hình nhưng chỉ dùng ViNLI.",
    "**Rule số/ngày/số hiệu:** giá trị trong claim không có trong bằng chứng thì hạ supported thành unsupported; nếu câu bằng chứng tương ứng có "
    "giá trị cùng loại khác thì gán contradicted.",
    "**SelfCheckGPT-NLI** [8]: sinh thêm 3 câu trả lời (nhiệt độ 0,7) từ cùng prompt và ngữ cảnh; điểm của claim là trung bình xác suất entail/contradict "
    "của mDeBERTa với mỗi câu trả lời lấy mẫu làm premise. Phương pháp không nhìn bằng chứng.",
    "**Verify-then-revise (RQ3):** judge 7B gắn cờ claim unsupported hoặc contradicted; Qwen2.5-3B nhận lại đúng ngữ cảnh đã truy xuất, câu trả lời "
    "cũ và danh sách claim bị gắn cờ, rồi viết lại (sửa hoặc bỏ các claim đó). Câu trả lời mới được tách claim và chấm lại bằng judge 7B; tối đa 2 vòng.",
], start=7)
para("*Điểm khác so với ViHERMES gốc:* đề tài giữ nguyên dữ liệu, đồ thị và bộ truy xuất của ViHERMES, chỉ thêm tầng tách claim, tập bằng chứng "
     "chung, các metric kiểm chứng và quy trình meta-evaluation.", italic=False)

# 4 ------------------------------------------------------------------
h2("4. Dataset")
gd = R["gold_distribution"]
bullets([
    f"*Câu hỏi và câu trả lời:* 100 câu lấy ngẫu nhiên phân tầng từ 1.561 câu của ViHERMES (20 câu mỗi mức hop, seed 42); 2 hệ × 100 = 200 câu trả lời, "
    f"tách được {N_CLAIMS_ALL} claim. Mẫu gán nhãn: 40 câu (8 mỗi mức hop) × 2 hệ = 80 câu trả lời, {R['claims_total']} claim (Bảng 1).",
])
table("Thống kê dữ liệu", ["Thành phần", "Giá trị"], [
    ["Câu hỏi ViHERMES / mức hop", "100 / 20 câu mỗi mức 1–5"],
    ["Câu trả lời (2 hệ)", f"200, tách {N_CLAIMS_ALL} claim"],
    ["Mẫu gán nhãn", f"80 câu trả lời, {R['claims_total']} claim ({R['claims_bad']} claim lỗi bị loại)"],
    ["Phân bố nhãn silver (claim dùng được)", f"supported {gd['supported']} · contradicted {gd['contradicted']} · unsupported {gd['unsupported']}"],
    ["Tập dev / test (theo câu hỏi, 20% dev)", f"{R['claims_dev']} / {R['claims_test']} claim"],
    ["Dữ liệu huấn luyện verifier", "12.000 cặp ViNLI + 3.328 cặp tổng hợp (ngoài mẫu đánh giá)"],
], [4, 8], align=["l", "l"])
bullets([
    "*Dữ liệu huấn luyện verifier:* cặp tổng hợp lấy từ các đoạn không thuộc mẫu đánh giá, nên không rò rỉ sang tập test; dev gồm 1.000 cặp ViNLI "
    "và 10% cặp tổng hợp. Bảng 2 cho thấy fine-tune với dữ liệu tổng hợp tăng mạnh độ chính xác trên cặp tổng hợp, còn bản chỉ dùng ViNLI hầu như "
    "không học được dạng lỗi trong miền.",
])
table("Độ chính xác của verifier trên tập dev (3 nhãn)", ["Verifier", "Dev ViNLI", "Dev cặp tổng hợp"], [
    ["mDeBERTa zero-shot", "0,758", "0,545"],
    ["Fine-tune ViNLI + tổng hợp (15.328 cặp)", "0,793", "0,875"],
    ["Fine-tune chỉ ViNLI (12.000 cặp)", "0,798", "0,588"],
], [7, 3, 3])
quick_txt = ", ".join(qp)
bullets([
    "*Nhãn silver:* Claude gán toàn bộ claim kèm số đoạn bằng chứng và lý do; đây là nhãn chuẩn của mọi phép đo trên tập test.",
    f"*Nhãn người (kiểm định mù):* một người gán trên trang HTML ngoại tuyến, không thấy nhãn hay lý do của Claude và không biết câu trả lời "
    f"thuộc hệ nào (mã claim được ẩn danh). Lượt C: 60 claim chọn phân tầng theo nhãn Claude (30/15/15), xem toàn bộ đoạn văn. Lượt {quick_txt}: "
    f"mỗi lượt 30 claim ngẫu nhiên không trùng lượt trước, mỗi màn hình một claim kèm 4 câu bằng chứng trùng từ nhiều nhất (có thể mở toàn đoạn). "
    f"Lượt duyệt có gợi ý (284 claim xác nhận trong ~10 phút, 0 thay đổi) và hai lượt có file xuất không tạo qua trang gán nhãn bị loại (Bảng 3).",
])
table("Các lượt gán nhãn người", ["Lượt", "Cách chọn / hiển thị", "Claim dùng được", "Trùng Claude", "κ"], [
    ["C", "Phân tầng 30/15/15 · toàn đoạn văn", AC["n"], pct(AC["acc"]), f(AC["kappa"], 2)],
    [quick_txt, f"Ngẫu nhiên · 4 câu bằng chứng ({AQ['n_input'] - AQ['n']} claim bị bỏ qua)", AQ["n"], pct(AQ["acc"]), f(AQ["kappa"], 2)],
    ["Gộp", "", ACG["n"], pct(ACG["acc"]), f(ACG["kappa"], 2)],
    ["Bị loại", "Duyệt có gợi ý (A); file không tạo qua trang (D, E)", "–", "–", "–"],
], [2, 7, 3, 3, 2], bold_rows=(2,))
bullets([
    "*Ví dụ claim:* Bảng 4 trích ba claim có nhãn người trùng nhãn Claude, đại diện ba loại lỗi thường gặp.",
])
table("Ví dụ claim và bằng chứng", ["Claim", "Bằng chứng (trích)", "Nhãn"], [
    ["“Tổng mức phạt của nhóm ba phòng khám là 8 triệu đồng.”", "Medic – Chi Lăng: 4.000.000 đ; Thu Cúc: 8.000.000 đ; phòng khám YHCT: 30.000.000 đ", "contradicted"],
    ["“Cục Dân số không liên quan đến thanh tra, xử lý vi phạm pháp luật.”", "Cục có nhiệm vụ “kiểm tra, thanh tra chuyên ngành … xử lý vi phạm pháp luật trong lĩnh vực dân số”", "contradicted"],
    ["“Thông tư 30/2017/TT-BYT có hiệu lực từ ngày 01/01/2018.”", "Thông tư mới có hiệu lực từ 28/10/2024; TT 30/2017 hết hiệu lực từ ngày đó (không nêu ngày 01/01/2018)", "unsupported"],
], [6, 7, 2.4], align=["l", "l", "c"], size=10)

# 5 ------------------------------------------------------------------
h2("5. Experimental Setup")
bullets([
    "*Cấu hình so sánh:* LLM-judge 3B/7B; RAGAS 3B/7B; NLI zero-shot V1/V2; NLI fine-tune V1/V2; NLI fine-tune chỉ ViNLI (ablation dữ liệu tổng hợp); "
    "mỗi biến thể NLI có và không có rule (ablation rule); SelfCheckGPT-NLI; rule đơn lẻ; mốc “luôn đoán supported”.",
    "*Metrics:* mức claim: macro-F1 3 nhãn, F1 từng nhãn, AUROC phát hiện claim không supported (NLI dùng 1 − P_sup); mức câu trả lời: Spearman và "
    "Kendall giữa điểm tự động và GGF chuẩn trên 61–63 câu trả lời test (tùy số câu có đầu ra hợp lệ); revise: thay đổi GGF, CR, UR, token F1, EM và token recall so với đáp án ViHERMES.",
    "*Thống kê:* KTC 95% bootstrap 1.000 lần; bootstrap ghép cặp cho hiệu số macro-F1; Wilcoxon cặp cho so sánh hai hệ và trước/sau khi sửa; "
    "Cohen's κ cho độ đồng thuận Claude–người.",
    "*Phần cứng:* Google Colab T4 16GB cho mọi bước dùng mô hình (Ollama, Q4_K_M; PyTorch float32); máy cá nhân chỉ cho phân tích và báo cáo, "
    "vì GPU cá nhân (4GB) treo máy khi chạy mô hình.",
])

# 6 ------------------------------------------------------------------
h2("6. Results & Ablation")
keys = ["judge_7b", "judge_3b", "nli_ft_v1", "nli_ft_v2", "nli_nosynth_v1", "nli_zs_v1", "nli_zs_v1+rule", "nli_zs_v2",
        "nli_selfcheck", "rule_only", "majority_supported"]
rows = []
for k in keys:
    c = CL[k]
    rows.append([NAMES[k], f(c["macro_f1"]), f"{f(c['ci95'][0], 2)}–{f(c['ci95'][1], 2)}", f(c["auroc_not_supported"]),
                 f(SENS[k]["macro_f1_vs_human"]) if k in SENS else "–", f(CO[k]["spearman"]) if k in CO else "–"])
rows.append([NAMES["ragas_7b"], "–", "–", "–", "–", f(CO["ragas_7b"]["spearman"])])
rows.append([NAMES["ragas_3b"], "–", "–", "–", "–", f(CO["ragas_3b"]["spearman"])])
table(f"Kết quả tổng hợp. Macro-F1, KTC và AUROC trên {R['claims_test']} claim test (nhãn silver); cột “người” trên {ACG['n']} claim có nhãn người; "
      f"Spearman giữa điểm câu trả lời và GGF chuẩn", ["Phương pháp", "Macro-F1", "KTC 95%", "AUROC", "Macro-F1 (người)", "Spearman ρ"],
      rows, [6, 2.2, 2.4, 2, 2.6, 2.4])
figure(F2, "Macro-F1 mức claim trên tập test. Xanh: LLM-judge; cam: verifier NLI; xám: SelfCheckGPT, rule và mốc tham chiếu.", width=Cm(15.5))

h3("6.1 RQ1 – Các metric có sẵn")
para(f"Trong nhóm không cần huấn luyện, LLM-judge 7B tốt nhất ở mức claim (macro-F1 {f(j7['macro_f1'])}, AUROC {f(j7['auroc_not_supported'])}), "
     f"hơn judge 3B ({f(CL['judge_3b']['macro_f1'])}) và NLI zero-shot ({f(zs['macro_f1'])}). Judge 7B bắt được {CATCH['j7']['caught']}/{CATCH['j7']['wrong']} claim sai và báo nhầm {CATCH['j7']['false_alarm']}/{CATCH['j7']['right']} claim đúng. Mọi phương pháp đều yếu ở hai nhãn lỗi: F1 của judge 7B cho "
     f"contradicted và unsupported chỉ {f(j7['f1_per_class']['contradicted'])} và {f(j7['f1_per_class']['unsupported'])}. SelfCheckGPT-NLI đạt "
     f"{f(CL['nli_selfcheck']['macro_f1'])}, ngang NLI zero-shot dù không nhìn bằng chứng, nhưng độ chính xác thấp ({f(CL['nli_selfcheck']['acc'])}) vì nó coi "
     f"claim đúng là đáng ngờ khi các câu trả lời lấy mẫu diễn đạt khác nhau. Ở mức câu trả lời, RAGAS 7B tương quan cao nhất với GGF chuẩn "
     f"(ρ = {f(CO['ragas_7b']['spearman'])}), trong khi RAGAS 3B chỉ đạt {f(CO['ragas_3b']['spearman'])}: kích thước judge quyết định nhiều hơn công thức metric.")
pc_keys = ["judge_7b", "judge_3b", "nli_ft_v1", "nli_zs_v1", "nli_selfcheck", "rule_only"]
table("F1 theo từng nhãn trên tập test (nhãn silver)", ["Phương pháp", "supported", "contradicted", "unsupported", "Accuracy"],
      [[NAMES[k], f(CL[k]["f1_per_class"]["supported"]), f(CL[k]["f1_per_class"]["contradicted"]), f(CL[k]["f1_per_class"]["unsupported"]), f(CL[k]["acc"])]
       for k in pc_keys], [6, 2.4, 2.4, 2.4, 2.2])
para("Accuracy cao không đồng nghĩa với metric tốt: “luôn đoán supported” đạt accuracy "
     f"{f(CL['majority_supported']['acc'])} vì {pct(CL['majority_supported']['acc'])} claim test là supported, nên bài dùng macro-F1 làm chỉ số chính.")

h3("6.2 RQ2 – Đồ thị, rule và fine-tune")
para(f"**Đồ thị:** thêm thông tin đồ thị vào đầu cửa sổ (V2) làm macro-F1 của NLI zero-shot giảm {f(zs['macro_f1'])} → {f(CL['nli_zs_v2']['macro_f1'])}. "
     f"Ngưỡng tối ưu của V2 rất thấp (τ_s = {f(TH['zs_v2'][0], 2)}): khi tên văn bản đứng đầu mỗi cửa sổ, mô hình cho xác suất entail cao với mọi claim nhắc "
     f"tới văn bản đó. Khi chỉ nối các triple liên quan tới từng claim (V3), macro-F1 zero-shot tăng lên {f(V3['macro_f1'])}, cao hơn V2 nhưng không khác V1 có ý nghĩa (chênh {f(D2['paired_silver']['nli_zs_v3 - nli_zs_v1']['diff'])}, KTC [{f(D2['paired_silver']['nli_zs_v3 - nli_zs_v1']['ci95'][0], 2)}; {f(D2['paired_silver']['nli_zs_v3 - nli_zs_v1']['ci95'][1], 2)}]); theo nhãn người V3 lại thấp hơn V1 ({f(V3['macro_f1_human'])} so với {f(SENS['nli_zs_v1']['macro_f1_vs_human'])}). "
     f"**Rule số/ngày** gần như không đổi kết quả ({f(zs['macro_f1'])} → {f(CL['nli_zs_v1+rule']['macro_f1'])}); nhiều lỗi nằm ở việc gán "
     f"sai chủ thể chứ không ở con số. **Fine-tune:** theo nhãn silver, fine-tune V1 hơn zero-shot (chênh {f(c_ft_zs['diff'])}, KTC 95% "
     f"[{f(c_ft_zs['ci95'][0], 2)}; {f(c_ft_zs['ci95'][1], 2)}]) và nhỉnh hơn judge 7B nhưng không có ý nghĩa (chênh {f(c_ft_j7['diff'])}, KTC "
     f"[{f(c_ft_j7['ci95'][0], 2)}; {f(c_ft_j7['ci95'][1], 2)}]). Ablation chỉ dùng ViNLI không cải thiện (chênh {f(c_ns_zs['diff'])}): phần tăng đến từ "
     f"dữ liệu tổng hợp trong miền.")
cmp_label = {"nli_ft_v1 - judge_7b": "Fine-tune V1 − judge 7B", "nli_ft_v1 - nli_zs_v1": "Fine-tune V1 − zero-shot V1",
             "nli_ft_v1 - nli_nosynth_v1": "Fine-tune V1 − fine-tune chỉ ViNLI", "nli_nosynth_v1 - nli_zs_v1": "Fine-tune chỉ ViNLI − zero-shot V1",
             "nli_ft_v1 - nli_ft_v2": "Fine-tune V1 − fine-tune V2", "judge_7b - nli_selfcheck": "Judge 7B − SelfCheckGPT"}
table("So sánh ghép cặp macro-F1 trên tập test (bootstrap 1.000 lần, nhãn silver)", ["So sánh", "Hiệu số", "KTC 95%", "Tỉ lệ ≤ 0"],
      [[cmp_label[k], f(v["diff"]), f"{f(v['ci95'][0], 2)}; {f(v['ci95'][1], 2)}", f(v["p_le_0"])] for k, v in CMP.items()], [7, 2.2, 3, 2.2])
para(f"**Kiểm định với nhãn người** (Hình 3) đảo kết luận về fine-tune: trên {ACG['n']} claim, fine-tune V1 đạt {f(hft)}, ngang zero-shot ({f(hzs)}) và thấp "
     f"hơn rõ judge 7B ({f(hj7)}); tương quan thứ hạng các metric giữa hai bộ nhãn chỉ ρ = {f(ACG['rank_spearman'], 2)}. Ngưỡng của verifier được chọn "
     f"theo nhãn Claude, nên mô hình fine-tune có thể đã học cách gán nhãn khắt khe của Claude: ma trận nhầm lẫn cho thấy người gán supported cho gần "
     f"một nửa số claim mà Claude gán contradicted hoặc unsupported.")
figure(F3, f"Macro-F1 của các metric trên {ACG['n']} claim có nhãn người, chấm theo nhãn người và theo nhãn Claude.", width=Cm(15.5))
cm = ACG["confusion_claude_rows_human_cols"]
LB = ["supported", "contradicted", "unsupported"]
table(f"Ma trận nhầm lẫn giữa nhãn Claude (hàng) và nhãn người (cột) trên {ACG['n']} claim",
      ["Claude \\ Người", "supported", "contradicted", "unsupported", "Người đồng ý"],
      [[LB[i]] + [str(x) for x in row] + [pct(row[i] / sum(row)) if sum(row) else "–"] for i, row in enumerate(cm)], [4, 2.5, 2.5, 2.5, 2.8])
para(f"Claude gán contradicted hoặc unsupported cho {sum(cm[1]) + sum(cm[2])} claim, người chỉ đồng ý ở {cm[1][1] + cm[2][2]} claim và gán supported cho "
     f"{cm[1][0] + cm[2][0]} claim trong số đó. Ngược lại, khi Claude gán supported, người đồng ý {pct(cm[0][0] / sum(cm[0]))}. Độ lệch có hướng này giải "
     f"thích vì sao metric được tối ưu theo nhãn Claude (verifier fine-tune với ngưỡng chọn trên dev silver) bị đánh giá thấp hơn khi đổi sang nhãn người.")

h3("6.3 RQ3 – Verify-then-revise")
table("Verify-then-revise trên 80 câu trả lời (GGF, CR, UR do judge 7B chấm; token F1, recall, EM so với đáp án ViHERMES)",
      ["Cấu hình", "GGF", "CR", "UR", "Token F1", "Token recall", "EM", "Claim/câu"], [
          ["Không sửa", f(RA["GGF_before"]), f(RA["CR_before"]), f(RA["UR_before"]), f(RA["answer_f1_before"]), f(RA["answer_recall_before"]), f(RA["answer_em_before"]), f(RA["claims_before"], 2)],
          ["Tối đa 1 vòng", f(R1["GGF_after"]), f(R1["CR_after"]), f(R1["UR_after"]), f(R1["answer_f1_after"]), f(R1["answer_recall_after"]), f(R1["answer_em_after"]), f(R1["claims_after"], 2)],
          ["Tối đa 2 vòng", f(R2["GGF_after"]), f(R2["CR_after"]), f(R2["UR_after"]), f(R2["answer_f1_after"]), f(R2["answer_recall_after"]), f(R2["answer_em_after"]), f(R2["claims_after"], 2)],
      ], [3.4, 1.6, 1.6, 1.6, 1.8, 2.1, 1.4, 2.0])
para(f"{RA['revised']}/{RA['answers']} câu trả lời có claim bị gắn cờ. GGF tăng {f(RA['GGF_before'])} → {f(RA['GGF_after'])} (Wilcoxon p = {f(RA['wilcoxon_GGF_p'])}) "
     f"và CR giảm một nửa, nhưng token F1 giảm {f(RA['answer_f1_before'])} → {f(RA['answer_f1_after'])} (p = {f(RA['wilcoxon_F1_p'])}), số claim mỗi câu giảm "
     f"{f(RA['claims_before'], 2)} → {f(RA['claims_after'], 2)} và {RA['abstained_after']} câu chuyển thành “không tìm thấy thông tin”. Vòng 1 cho phần lớn mức "
     f"tăng; trên {P2['n']} câu cần vòng 2, GGF tăng {f(P2['GGF_r1'])} → {f(P2['GGF_r2'])} nhưng chưa có ý nghĩa (p = {f(P2['wilcoxon_GGF_p'])}). EM bằng 0 ở mọi "
     f"cấu hình vì đáp án ViHERMES dài (khoảng 115 từ), nên token recall được dùng để đo mức mất nội dung. Mức tăng GGF là giới hạn trên, vì chính judge "
     f"7B vừa gắn cờ vừa chấm lại.")
table("Ví dụ verify-then-revise (câu hỏi 3 hop, Naive RAG; trích nguyên văn)", ["Trước khi sửa", "Sau 1 vòng sửa"], [[
    "Dự kiến Luật sửa đổi Luật Dược sẽ được trình Quốc hội vào **tháng 10/2025**. Nghị định 124/2021/NĐ-CP về xử phạt vi phạm hành chính trong "
    "lĩnh vực y tế được ban hành vào tháng 12/2021. Thời điểm các bệnh viện tự chủ được tự quyết định mua sắm thuốc theo Luật số 90/2025/QH15 "
    "là từ ngày 01/7/2025.",
    "Không tìm thấy thông tin về thời điểm dự kiến trình Quốc hội Luật sửa đổi Luật Dược. Thời điểm ban hành Nghị định 124/2021/NĐ-CP và thời "
    "điểm các bệnh viện tự chủ được tự quyết định mua sắm thuốc theo Luật số 90/2025/QH15 *được nêu rõ trong ngữ cảnh*."]], [1, 1], align=["l", "l"], size=10)
para("Judge 7B gắn cờ hai claim đầu (văn bản ghi Luật Dược trình Quốc hội tháng 10/2022). Câu trả lời mới đạt GGF = 1 theo judge nhưng đã bỏ cả ba "
     "mốc thời gian, kể cả mốc 01/7/2025 mà judge và Claude đều gán supported, và thay bằng câu chung chung “được nêu rõ trong ngữ cảnh”. Đây là dạng "
     "điển hình khiến GGF tăng trong khi token recall giảm.")

h3("6.4 Hai hệ và độ khó theo hop")
table("Chất lượng hỏi đáp và độ trung thực của hai hệ", ["Hệ", "Token F1 (100 câu)", "Recall đoạn vàng", "GGF", "CR", "UR"], [
    ["Naive RAG", f(QA["naive"]["answer_f1"]), pct(QA["naive"]["gold_passage_recall"], 1), f(SY["naive"]["GGF"]), f(SY["naive"]["CR"]), f(SY["naive"]["UR"])],
    ["GraphRAG", f(QA["graph"]["answer_f1"]), pct(QA["graph"]["gold_passage_recall"], 1), f(SY["graph"]["GGF"]), f(SY["graph"]["CR"]), f(SY["graph"]["UR"])],
], [3, 3, 3, 2, 2, 2])
para(f"Hai hệ không khác nhau có ý nghĩa (Wilcoxon cặp trên GGF, p = {f(SY['wilcoxon_GGF_p'])}). Đồ thị phát hành của ViHERMES khá thô (mỗi đoạn chủ yếu gắn "
     f"với văn bản gốc, ít cạnh sửa đổi), nên lan truyền thêm được ít đoạn vàng. Độ trung thực giảm rõ ở câu 4–5 hop (Hình 4).")
figure(F4, "GGF trung bình theo số hop (8 câu hỏi mỗi mức; GraphRAG mức 5 hop có 7 câu trả lời có claim; nhãn silver).", width=Cm(13))

h3("6.5 Phân tích lỗi")
bullets([
    "**Sai mốc thời gian:** “Luật sửa đổi Luật Dược trình Quốc hội tháng 10/2025” trong khi tờ trình ghi tháng 10/2022; mốc 10/2025 thuộc Luật An toàn thực phẩm.",
    "**Gán sai chủ thể:** nhiệm vụ truyền thông cải cách hành chính của Văn phòng Bộ bị gán cho Viện Chiến lược và Chính sách y tế. Rule số/ngày không bắt được loại lỗi này.",
    "**Sai phép tổng hợp:** cộng tiền phạt của nhiều quyết định (Bảng 4). Cả hai LLM-judge bỏ sót vì phải tự cộng số từ nhiều văn bản; NLI lại bắt được.",
    "**Bịa thêm danh sách:** liệt kê Instagram, TikTok, YouTube trong khi giấy xác nhận quảng cáo chỉ ghi facebook, zalo; NLI zero-shot bị lừa vì một văn bản khác trong ngữ cảnh có chữ “instagram”.",
    f"**Từ chối sai và lỗi tách claim:** “không có thông tin” dù bằng chứng ghi rõ ngày hiệu lực; {R['claims_bad']} claim bị tách hỏng (đảo nghĩa, chèn tên không có trong câu trả lời).",
])

# 7 ------------------------------------------------------------------
h2("7. Rủi ro & hạn chế")
bullets([
    f"**Nhãn chuẩn là silver:** Claude trùng người {pct(ACG['acc'])} (κ = {f(ACG['kappa'], 2)}). Giảm thiểu: báo cáo song song theo nhãn người; mở rộng nhãn người, hai người gán và bước thống nhất.",
    "**Một người gán, không phải chuyên gia pháp lý;** các lượt nhanh chỉ hiển thị 4 câu bằng chứng nên có thể bỏ sót bằng chứng ở xa. Giảm thiểu: lượt C dùng toàn đoạn văn và được báo cáo riêng.",
    "**Quy mô nhỏ:** 2 hệ thay vì 5, 284 claim thay vì khoảng 3.000, judge lớn nhất 7B (giới hạn Colab T4). Giảm thiểu: KTC bootstrap và kiểm định ghép cặp cho mọi so sánh chính.",
    "**Ngưỡng verifier chọn theo nhãn silver:** làm verifier fine-tune nghiêng theo Claude. Giảm thiểu: chọn ngưỡng trên nhãn người khi đủ dữ liệu.",
    "**Verify-then-revise tự chấm:** câu trả lời đã sửa chỉ được chấm bằng judge đã gắn cờ. Giảm thiểu: chấm lại bằng người hoặc metric độc lập.",
    "**Đồ thị dạng văn bản:** triple được nối vào đầu vào dưới dạng văn bản và mới thử với NLI zero-shot; chưa fine-tune với 20.000 cặp tổng hợp; chưa có ViEduReg, verifier Qwen trả span, toán tử Verify trong KAG.",
])

# 8 ------------------------------------------------------------------
h2("8. Kết luận & hướng phát triển")
para(f"Trên văn bản pháp quy y tế tiếng Việt, các metric faithfulness tự động chạy bằng LLM mở cỡ nhỏ chỉ khớp ở mức thấp đến trung bình với nhãn chuẩn. "
     f"LLM-judge 7B là metric ổn định nhất ở cả hai bộ nhãn; RAGAS 7B tốt nhất ở mức câu trả lời. Fine-tune verifier bằng dữ liệu tổng hợp trong miền tăng "
     f"điểm theo nhãn silver nhưng không theo nhãn người, cho thấy meta-evaluation dùng nhãn LLM có thể đổi thứ hạng metric. Vòng verify-then-revise với bộ "
     f"sinh 3B giảm claim sai bằng cách xóa nội dung, là đánh đổi chứ chưa phải cải thiện thuần. Hướng phát triển:")
numbered([
    "Gán nhãn người cho toàn bộ mẫu với hai người có chuyên môn pháp lý, báo cáo κ giữa người với người; chọn ngưỡng verifier trên nhãn người.",
    "Thay judge 7B bằng 14–32B; thêm verifier Qwen 1,5–4B fine-tune trả nhãn và span bằng chứng.",
    "Đưa thông tin đồ thị vào verifier dưới dạng triple có cấu trúc; mở rộng sang LightRAG, HippoRAG 2, KAG và bộ quy chế đào tạo ViEduReg.",
    "Chấm câu trả lời đã sửa bằng người hoặc metric độc lập; dùng bộ sinh lớn hơn cho bước sửa.",
])

h2("Caveats")
bullets([
    f"Mọi số liệu trên tập test dùng nhãn silver do Claude gán; số liệu theo nhãn người tính trên {ACG['n']} claim do một người gán.",
    "Các lần fine-tune đầu tiên trên Colab bị loss NaN do checkpoint mDeBERTa lưu ở float16 và thư viện mới giữ nguyên dtype; kết quả trong bài là sau khi sửa (huấn luyện và chấm lại toàn bộ bằng float32).",
    "Môi trường Colab dùng transformers 5.x, máy cá nhân dùng 4.46; Ollama chạy mô hình lượng tử hóa Q4_K_M.",
    "Ba lượt gán nhãn bị loại (một lượt duyệt có gợi ý và hai lượt có file xuất không tạo qua trang gán nhãn) không được dùng ở bất kỳ phép đo nào.",
    "Một số tài liệu tham khảo là preprint arXiv và có thể thay đổi sau phản biện.",
])

h2("References")
REFS = [
    "Nguyen, L.S.T., Bui, Q.M., Ngo, T.T., Vo, Q.T.N., Le, D.N.H., Quan, T.T.: ViHERMES: A Graph-Grounded Multihop Question Answering Benchmark and System for Vietnamese Healthcare Regulations. ACIIDS 2026. arXiv:2602.07361 — https://github.com/ura-hcmut/ViHERMES",
    "Es, S., James, J., Espinosa-Anke, L., Schockaert, S.: RAGAs: Automated Evaluation of Retrieval Augmented Generation. EACL 2024 System Demonstrations — https://aclanthology.org/2024.eacl-demo.16/",
    "Liang, L., et al.: KAG: Boosting LLMs in Professional Domains via Knowledge Augmented Generation. arXiv:2409.13731 (2024) — https://arxiv.org/abs/2409.13731",
    "Edge, D., Trinh, H., Cheng, N., et al.: From Local to Global: A Graph RAG Approach to Query-Focused Summarization. arXiv:2404.16130 (2024)",
    "Guo, Z., Xia, L., Yu, Y., Ao, T., Huang, C.: LightRAG: Simple and Fast Retrieval-Augmented Generation. arXiv:2410.05779 (2024)",
    "Gutiérrez, B.J., Shu, Y., Qi, W., Zhou, S., Su, Y.: From RAG to Memory: Non-Parametric Continual Learning for Large Language Models (HippoRAG 2). arXiv:2502.14802 (2025)",
    "Lewis, P., Perez, E., Piktus, A., et al.: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS 33 (2020)",
    "Manakul, P., Liusie, A., Gales, M.J.F.: SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models. EMNLP 2023. arXiv:2303.08896",
    "Mickus, T., Zosa, E., Vázquez, R., et al.: SemEval-2024 Task 6: SHROOM, a Shared-task on Hallucinations and Related Observable Overgeneration Mistakes. SemEval 2024. arXiv:2403.07726",
    "Vázquez, R., Mickus, T., et al.: SemEval-2025 Task 3: Mu-SHROOM, the Multilingual Shared Task on Hallucinations and Related Observable Overgeneration Mistakes. SemEval 2025",
    "DSC2025 ViHallu: Vietnamese hallucination detection challenge. arXiv:2601.04711 (2026)",
    "VLUE: Vietnamese Language Understanding Evaluation benchmark (gồm ViNLI). arXiv:2403.15882 (2024)",
    "He, P., Gao, J., Chen, W.: DeBERTaV3: Improving DeBERTa using ELECTRA-Style Pre-Training with Gradient-Disentangled Embedding Sharing. ICLR 2023. arXiv:2111.09543",
    "Laurer, M., et al.: mDeBERTa-v3-base-xnli-multilingual-nli-2mil7. Hugging Face model card — https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7",
    "Robertson, S., Zaragoza, H.: The Probabilistic Relevance Framework: BM25 and Beyond. Foundations and Trends in Information Retrieval 3(4), 333–389 (2009)",
    "Chen, J., Xiao, S., Zhang, P., et al.: BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation. arXiv:2402.03216 (2024)",
    "Zheng, L., Chiang, W.-L., Sheng, Y., et al.: Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS 36 (2023). arXiv:2306.05685",
    "Min, S., Krishna, K., Lyu, X., et al.: FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation. EMNLP 2023. arXiv:2305.14251",
    "Conneau, A., Rinott, R., Lample, G., et al.: XNLI: Evaluating Cross-lingual Sentence Representations. EMNLP 2018",
    "Huynh, T.V., Nguyen, K.V., Nguyen, N.L.-T.: ViNLI: A Vietnamese Corpus for Studies on Open-Domain Natural Language Inference. COLING 2022",
    "Qwen Team: Qwen2.5 Technical Report. arXiv:2412.15115 (2024)",
]
for i, ref in enumerate(REFS, 1):
    p = doc.add_paragraph()
    r = p.add_run(f"[{i}]\t")
    r.font.size = Pt(10)
    rich(p, ref, size=10)
    p.paragraph_format.left_indent = Cm(0.9)
    p.paragraph_format.first_line_indent = Cm(-0.9)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(0.9))
    p.paragraph_format.space_after = Pt(2)

doc.save(OUT)
print(OUT, "figures", FIGN[0], "tables", TABN[0], "refs", len(REFS))
