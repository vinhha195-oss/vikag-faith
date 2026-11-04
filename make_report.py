"""Build report/bao_cao_ViKAG-Faith.pdf from outputs/analysis/results.json (HTML -> PDF via Edge).

Re-run after `python src/s7_analysis.py` whenever the gold labels change; every number in the
report is read from results.json, and the label source (human / silver) is stated in the report.
"""

import base64
import html
import io
import json
import subprocess
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent
RES = json.load(open(ROOT / "outputs" / "analysis" / "results.json", encoding="utf-8"))
OUT_HTML = ROOT / "report" / "bao_cao_ViKAG-Faith.html"
OUT_PDF = ROOT / "report" / "bao_cao_ViKAG-Faith.pdf"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

NAMES = {
    "judge_7b": "LLM-judge (Qwen2.5-7B)", "judge_3b": "LLM-judge (Qwen2.5-3B)",
    "nli_zs_v1": "NLI zero-shot, V1 (chỉ đoạn văn)", "nli_zs_v2": "NLI zero-shot, V2 (+ thông tin graph)",
    "nli_zs_v1+rule": "NLI V1 + rule số/ngày", "nli_zs_v2+rule": "NLI V2 + rule số/ngày",
    "rule_only": "Chỉ rule số/ngày", "majority_supported": "Luôn đoán supported",
    "ragas_7b": "RAGAS faithfulness (7B)", "ragas_3b": "RAGAS faithfulness (3B)",
    "nli_ft_v1": "NLI fine-tune, V1", "nli_ft_v2": "NLI fine-tune, V2",
    "nli_ft_v1+rule": "NLI fine-tune V1 + rule", "nli_ft_v2+rule": "NLI fine-tune V2 + rule",
    "nli_nosynth_v1": "NLI fine-tune chỉ ViNLI, V1", "nli_nosynth_v2": "NLI fine-tune chỉ ViNLI, V2",
    "nli_nosynth_v1+rule": "NLI chỉ ViNLI V1 + rule", "nli_nosynth_v2+rule": "NLI chỉ ViNLI V2 + rule",
    "nli_selfcheck": "SelfCheckGPT-NLI (không dùng bằng chứng)",
}
# Methods drawn in the figures; the tables list every method.
FIG_KEYS = ["judge_7b", "judge_3b", "nli_ft_v1", "nli_ft_v2", "nli_nosynth_v1", "nli_zs_v1", "nli_zs_v2",
            "nli_zs_v1+rule", "nli_selfcheck", "rule_only", "majority_supported", "ragas_7b", "ragas_3b"]
INK, MUTED, ACC, ACC2, GRID = "#1f2328", "#6b6f76", "#2f6db5", "#c4741b", "#e3e3e0"
plt.rcParams.update({"font.family": "Segoe UI", "font.size": 9.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})


def fig_to_img(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return f'<img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}">'


def f(x, d=3):
    return "–" if x is None else f"{x:.{d}f}".replace(".", ",")


def pct(x):
    return f"{100 * x:.1f}%".replace(".", ",")


assert not RES["ft_identical_to_zs"], "fine-tuned verifier identical to zero-shot: training failed again?"
claim, corr = RES["claim_level"], RES["answer_level_correlation"]
CMP, REV = RES["comparisons"], RES["revise"]
sysr, qa = RES["systems"], RES["qa"]
gold_human = RES["gold"].startswith("human")
AUD = RES["agreement"].get("audit")
gold_txt = ("nhãn do người duyệt" if RES["gold"] == "human" else
            "nhãn silver do Claude gán; " + (f"một mẫu kiểm định mù {AUD['n']} claim do người gán cho κ = {f(AUD['kappa'], 2)}"
                                              if AUD else "chưa được người kiểm định"))

# ---------- figures ----------
order = sorted((k for k in claim if k in FIG_KEYS), key=lambda k: claim[k]["macro_f1"])
fig, ax = plt.subplots(figsize=(6.6, 3.9))
vals = [claim[k]["macro_f1"] for k in order]
lo = [claim[k]["macro_f1"] - claim[k]["ci95"][0] for k in order]
hi = [claim[k]["ci95"][1] - claim[k]["macro_f1"] for k in order]
colors = [ACC if k.startswith("judge") else (MUTED if k in ("majority_supported", "rule_only", "nli_selfcheck") else ACC2) for k in order]
ax.barh([NAMES[k] for k in order], vals, xerr=[lo, hi], color=colors, error_kw={"ecolor": INK, "lw": 0.8, "capsize": 2})
for i, k in enumerate(order):  # label sits past the CI whisker so the two never overlap
    ax.text(claim[k]["ci95"][1] + 0.01, i, f(claim[k]["macro_f1"]), va="center", fontsize=8.5, color=INK)
ax.set_xlabel("Macro-F1 trên tập test (3 nhãn), thanh lỗi = KTC 95% bootstrap")
ax.set_xlim(0, max(c[1] for c in (claim[k]["ci95"] for k in order)) + 0.1)
ax.grid(axis="x", color=GRID)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
FIG_CLAIM = fig_to_img(fig)

corder = sorted((k for k in corr if k in FIG_KEYS), key=lambda k: corr[k]["spearman"])
fig, ax = plt.subplots(figsize=(6.6, 3.6))
vals = [corr[k]["spearman"] for k in corder]
ax.barh([NAMES[k] for k in corder], vals,
        color=[ACC if k.startswith(("judge", "ragas")) else ACC2 for k in corder])
for i, v in enumerate(vals):
    ax.text(max(v, 0) + 0.012, i, f(v), va="center", fontsize=8.5)
ax.set_xlabel("Spearman ρ giữa điểm tự động và GGF của nhãn chuẩn (mức câu trả lời, tập test)")
ax.set_xlim(min(0, min(vals)) - 0.02, max(vals) + 0.12)
ax.grid(axis="x", color=GRID)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
FIG_CORR = fig_to_img(fig)

fig, ax = plt.subplots(figsize=(6.6, 2.6))
hops = sorted(sysr["by_hop"]["naive"], key=int)
for s, other, c, lab in (("naive", "graph", MUTED, "Naive RAG"), ("graph", "naive", ACC, "GraphRAG")):
    ax.plot([int(h) for h in hops], [sysr["by_hop"][s][h]["GGF"] for h in hops], marker="o", color=c, label=lab)
    for h in hops:  # the higher point of each pair is labelled above, the lower one below, so labels never overlap
        y, yo = sysr["by_hop"][s][h]["GGF"], sysr["by_hop"][other][h]["GGF"]
        up = y > yo or (y == yo and s == "naive")
        ax.text(int(h), y + (0.04 if up else -0.05), f(y, 2), ha="center", va="bottom" if up else "top", fontsize=8, color=c)
ax.set_xticks([int(h) for h in hops])
ax.set_xlabel("Số hop của câu hỏi")
ax.set_ylabel("GGF trung bình")
ax.set_ylim(0, 1.08)
ax.grid(axis="y", color=GRID)
ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 0.02))
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
FIG_HOP = fig_to_img(fig)

# ---------- tables ----------
claim_rows = "".join(
    f"<tr><td>{NAMES[k]}</td><td>{f(v['macro_f1'])}</td><td>{f(v['ci95'][0], 2)}–{f(v['ci95'][1], 2)}</td>"
    f"<td>{f(v['acc'])}</td><td>{f(v['f1_per_class']['supported'], 2)}</td><td>{f(v['f1_per_class']['contradicted'], 2)}</td>"
    f"<td>{f(v['f1_per_class']['unsupported'], 2)}</td><td>{f(v['auroc_not_supported'])}</td><td>{v['n']}</td></tr>"
    for k, v in sorted(claim.items(), key=lambda x: -x[1]["macro_f1"]))
corr_rows = "".join(
    f"<tr><td>{NAMES[k]}</td><td>{f(v['spearman'])}</td><td>{f(v['kendall'])}</td><td>{v['n']}</td></tr>"
    for k, v in sorted(corr.items(), key=lambda x: -x[1]["spearman"]))
best_claim = max(claim, key=lambda k: claim[k]["macro_f1"])
below = [NAMES[k] for k in claim if k != "majority_supported" and claim[k]["macro_f1"] <= claim["majority_supported"]["macro_f1"]]
beat_txt = ("mọi phương pháp còn lại đều vượt mốc này" if not below else
            "mọi phương pháp vượt mốc này, trừ " + ", ".join(below))
best_corr = max(corr, key=lambda k: corr[k]["spearman"])
gd = RES["gold_distribution"]
n_usable = sum(gd.values())
agr = RES["agreement"]
th = RES["thresholds"]

agree_html = ""
if AUD:
    LBL = ["supported", "contradicted", "unsupported"]
    cmr = "".join(f"<tr><td>Claude: {LBL[i]}</td>" + "".join(f"<td>{x}</td>" for x in row) + f"<td>{pct(AUD['agree_by_claude_label'][LBL[i]])}</td></tr>"
                  for i, row in enumerate(AUD["confusion_claude_rows_human_cols"]))
    sens = AUD["sensitivity"]
    sens_rows = "".join(f"<tr><td>{NAMES[k]}</td><td>{f(v['macro_f1_vs_human'])}</td><td>{f(v['macro_f1_vs_claude'])}</td><td>{v['n']}</td></tr>"
                        for k, v in sorted(sens.items(), key=lambda x: -x[1]["macro_f1_vs_human"]) if "+rule" not in k)
    s_ft, s_j7, s_zs = sens["nli_ft_v1"], sens["judge_7b"], sens["nli_zs_v1"]
    QG, QCG = agr.get("audit_G"), agr.get("audit_CG")
    quick_html = ""
    if QG and QCG:
        sg = QCG["sensitivity"]
        cg_rows = "".join(f"<tr><td>{NAMES[k]}</td><td>{f(sg[k]['macro_f1_vs_human'])}</td><td>{f(sg[k]['macro_f1_vs_claude'])}</td><td>{sg[k]['n']}</td></tr>"
                          for k in ("judge_7b", "nli_ft_v1", "nli_zs_v1", "nli_nosynth_v1", "judge_3b", "nli_selfcheck", "majority_supported"))
        n_skip = QG["n_input"] - QG["n"]
        qp = agr.get("quick_passes", ["G"])
        qname = "lượt " + ", ".join(qp)
        quick_html = f"""<p><b>Mẫu kiểm định bổ sung ({qname}).</b> Thêm {QG['n_input']} claim chọn <i>ngẫu nhiên</i> (không phân tầng, {len(qp)} lượt 30 claim), không trùng lượt trên,
được cùng người gán mù trên một trang rút gọn: mỗi màn hình một claim kèm 4 câu bằng chứng trùng từ nhiều nhất, có thể mở toàn bộ đoạn văn.
{n_skip} claim bị người gán đánh dấu khó hiểu hoặc là claim lỗi nên bị loại, còn {QG['n']} claim. Trên mẫu ngẫu nhiên này, Claude trùng với người
ở {pct(QG['acc'])} số claim (κ = {f(QG['kappa'])}). Đây là ước lượng ít thiên lệch hơn về độ chính xác chung của nhãn silver, nhưng với {QG['n']}
claim, khoảng tin cậy còn rộng. Gộp lượt C với {qname} ({QCG['n']} claim): trùng {pct(QCG['acc'])}, κ = {f(QCG['kappa'])}, tương quan thứ hạng metric
ρ = {f(QCG['rank_spearman'], 2)}. Theo nhãn người trên {QCG['n']} claim, LLM-judge 7B vẫn tốt nhất, còn verifier fine-tune V1 chỉ ngang zero-shot:
ưu thế của fine-tune ở mục 6.3 chỉ xuất hiện khi chấm theo nhãn Claude.</p>
<table><tr><th>Phương pháp (gộp lượt C và {', '.join(qp)})</th><th>Macro-F1 theo nhãn người</th><th>Macro-F1 theo nhãn Claude</th><th>n</th></tr>{cg_rows}</table>"""
    rank_txt = ("thứ hạng các metric gần như không đổi" if AUD["rank_spearman"] >= 0.8 else
                "thứ hạng các metric thay đổi đáng kể")
    pa = agr.get("pass_A_excluded", {})
    agree_html = f"""<h3>4.1 Độ tin cậy của nhãn silver: kiểm định mù</h3>
<p>Lượt duyệt đầu tiên (người duyệt xem nhãn gợi ý) xác nhận cả {pa.get('confirmed', 0)} claim mà không sửa nhãn nào
({pa.get('labels_changed', 0)} thay đổi) trong khoảng 10 phút; vì không có bằng chứng là đã đối chiếu thật, lượt này <b>không được dùng làm
nhãn người</b>. Thay vào đó, một <b>mẫu kiểm định mù</b> gồm {AUD['n']} claim (30 claim Claude gán supported, 15 contradicted,
15 unsupported, chọn ngẫu nhiên) được người gán lại từ đầu, không thấy nhãn hay lý do của Claude và không biết hệ sinh câu trả lời.</p>
<p>Kết quả: nhãn Claude trùng với người ở <b>{pct(AUD['acc'])}</b> số claim, <b>Cohen's κ = {f(AUD['kappa'])}</b> (đồng thuận thấp).
Lệch chủ yếu theo một hướng: người gán supported cho phần lớn claim mà Claude gán contradicted hoặc unsupported, tức Claude khắt khe hơn
người gán. Vì mẫu được chọn phân tầng theo nhãn Claude, tỉ lệ đồng ý được báo cáo riêng cho từng nhãn.</p>
<table><tr><th></th><th>Người: supported</th><th>Người: contradicted</th><th>Người: unsupported</th><th>Người đồng ý</th></tr>{cmr}</table>
<p><b>Kiểm tra độ nhạy.</b> Chấm lại các metric trên {AUD['n']} claim này theo hai bộ nhãn: {rank_txt}
(Spearman giữa hai bảng xếp hạng = {f(AUD['rank_spearman'], 2)}, tính trên mọi phương pháp kể cả biến thể + rule). Thay đổi lớn nhất là verifier
fine-tune V1: theo nhãn Claude nó đạt {f(s_ft['macro_f1_vs_claude'])}, gần judge-7B ({f(s_j7['macro_f1_vs_claude'])}), nhưng theo nhãn người
chỉ còn {f(s_ft['macro_f1_vs_human'])}, thấp hơn judge-7B ({f(s_j7['macro_f1_vs_human'])}) và cả verifier zero-shot ({f(s_zs['macro_f1_vs_human'])}).
Ngưỡng của verifier được chọn trên tập dev theo nhãn Claude, nên mô hình fine-tune có thể đã học cả cách gán nhãn khắt khe của Claude.
Các phương pháp không có tham số học từ nhãn (judge, NLI zero-shot) giữ thứ hạng ổn định hơn. Vì vậy các so sánh ở mục 6 chỉ nên đọc như kết quả
<i>theo nhãn silver</i>; với 60 claim, mẫu kiểm định đủ để cảnh báo nhưng chưa đủ để xếp hạng lại một cách chắc chắn.</p>
<table><tr><th>Phương pháp</th><th>Macro-F1 theo nhãn người</th><th>Macro-F1 theo nhãn Claude</th><th>n</th></tr>{sens_rows}</table>{quick_html}"""
elif agr.get("n"):
    changed = ", ".join(f"{k}: {v}" for k, v in agr["changed"].items()) or "không có"
    agree_html = (f"<p>Người duyệt đã xác nhận {agr['n']} claim. Nhãn của Claude trùng với nhãn cuối cùng ở "
                  f"{pct(agr['claude_vs_human_acc'])} số claim (Cohen's κ = {f(agr['claude_vs_human_kappa'])}). "
                  f"Các thay đổi: {html.escape(changed)}.</p>")
    if "A_vs_B_kappa" in agr:
        agree_html += f"<p>Hai người gán độc lập trên {agr['A_vs_B_n']} claim của tập dev đạt κ = {f(agr['A_vs_B_kappa'])}.</p>"
else:
    agree_html = ("<p class='warn'><b>Lưu ý:</b> tại thời điểm xuất báo cáo, chưa có nhãn của người duyệt. "
                  "Mọi số liệu dưới đây được tính trên nhãn silver do Claude (một LLM khác họ với các mô hình được "
                  "đánh giá) gán. Kết quả RQ1 vì vậy chỉ cho biết các metric khớp với một LLM mạnh hơn đến đâu, "
                  "chưa phải mức khớp với con người.</p>")

v1, v2 = claim["nli_zs_v1"]["macro_f1"], claim["nli_zs_v2"]["macro_f1"]
rq2_sentence = (f"Thêm thông tin graph (V2) {'làm giảm' if v2 < v1 else 'làm tăng'} macro-F1 của verifier NLI từ "
                f"{f(v1)} xuống {f(v2)}" if v2 < v1 else
                f"Thêm thông tin graph (V2) làm tăng macro-F1 của verifier NLI từ {f(v1)} lên {f(v2)}")
r1, r2 = claim["nli_zs_v1+rule"]["macro_f1"], claim["nli_zs_v2+rule"]["macro_f1"]
ft1, ft2, ns1 = (claim[k]["macro_f1"] for k in ("nli_ft_v1", "nli_ft_v2", "nli_nosynth_v1"))
sc = claim["nli_selfcheck"]["macro_f1"]


def cmp_txt(key):
    c = CMP[key]
    return f"chênh {f(c['diff'])}, KTC 95% [{f(c['ci95'][0], 2)}; {f(c['ci95'][1], 2)}]"


CMP_LABEL = {"nli_ft_v1 - judge_7b": "NLI fine-tune V1 − LLM-judge 7B", "nli_ft_v1 - nli_zs_v1": "NLI fine-tune V1 − NLI zero-shot V1",
             "nli_ft_v1 - nli_nosynth_v1": "NLI fine-tune V1 − fine-tune chỉ ViNLI V1", "nli_nosynth_v1 - nli_zs_v1": "Fine-tune chỉ ViNLI V1 − zero-shot V1",
             "nli_ft_v1 - nli_ft_v2": "NLI fine-tune V1 − fine-tune V2", "judge_7b - nli_selfcheck": "LLM-judge 7B − SelfCheckGPT-NLI"}
cmp_rows = "".join(f"<tr><td>{CMP_LABEL[k]}</td><td>{f(v['diff'])}</td><td>{f(v['ci95'][0], 2)}–{f(v['ci95'][1], 2)}</td>"
                   f"<td>{f(v['p_le_0'])}</td><td>{v['n']}</td></tr>" for k, v in CMP.items())
RA, RN, RG = REV["all"], REV["naive"], REV["graph"]
BR = REV["by_max_rounds"]
B1, B2, P2 = BR["1"], BR["2"], BR["round2_vs_round1"]
rounds_rows = "".join(
    f"<tr><td>{lab}</td><td>{f(r['GGF_after'])}</td><td>{f(r['CR_after'])}</td><td>{f(r['UR_after'])}</td>"
    f"<td>{f(r['answer_f1_after'])}</td><td>{f(r['answer_recall_after'])}</td><td>{f(r['answer_em_after'])}</td>"
    f"<td>{f(r['claims_after'], 2)}</td><td>{r['abstained_after']}</td></tr>"
    for lab, r in (("Không sửa", {**RA, "GGF_after": RA["GGF_before"], "CR_after": RA["CR_before"], "UR_after": RA["UR_before"],
                                  "answer_f1_after": RA["answer_f1_before"], "answer_recall_after": RA["answer_recall_before"],
                                  "answer_em_after": RA["answer_em_before"], "claims_after": RA["claims_before"], "abstained_after": 0}),
                   ("Tối đa 1 vòng", B1), ("Tối đa 2 vòng", B2)))
rev_rows = "".join(
    f"<tr><td>{lab}</td><td>{r['revised']}/{r['answers']}</td><td>{f(r['GGF_before'])} → {f(r['GGF_after'])}</td>"
    f"<td>{f(r['CR_before'])} → {f(r['CR_after'])}</td><td>{f(r['UR_before'])} → {f(r['UR_after'])}</td>"
    f"<td>{f(r['answer_f1_before'])} → {f(r['answer_f1_after'])}</td><td>{f(r['claims_before'], 2)} → {f(r['claims_after'], 2)}</td>"
    f"<td>{f(r['wilcoxon_GGF_p'])}</td><td>{f(r['wilcoxon_F1_p'])}</td></tr>"
    for lab, r in (("Cả hai hệ", RA), ("Naive RAG", RN), ("GraphRAG", RG)))

today = date.today().strftime("%d/%m/%Y")

# Appendix: every item of the Project 4 outline, with what this pilot actually did.
ST = {"ok": "Đạt", "part": "Một phần", "no": "Chưa làm"}
REQS = [
    ("Phương pháp", [
        ("Tách claim bằng LLM 7B, prompt tiếng Việt có ví dụ", "part", "Prompt tiếng Việt có ví dụ; dùng Qwen2.5-3B thay vì 7B"),
        ("Rule kiểm tra mỗi claim một vị từ chính", "part", "Quy tắc nằm trong prompt; rule chỉ đánh dấu claim chứa nhiều giá trị số"),
        ("Căn chỉnh claim với triple KG (entity linking), chunk gốc, top-k chunk", "part", "Bằng chứng = đoạn truy xuất ∪ đoạn vàng + thông tin graph mức văn bản; chưa có entity linking/triple riêng cho từng claim"),
        ("Verifier cross-encoder fine-tune ViNLI + dữ liệu tổng hợp", "ok", "mDeBERTa-v3-base (thay PhoBERT-large/XLM-R), 12.000 cặp ViNLI + 3.328 cặp tổng hợp"),
        ("Verifier Qwen 1.5–4B trả nhãn và span bằng chứng", "no", ""),
        ("Rule số/ngày", "ok", "So với văn bản bằng chứng, chưa so với thuộc tính KG"),
        ("Metric GGF, CR, UR", "ok", "Mục 3.2, 6.4, 6.5"),
        ("Verify-then-revise, tối đa 2 vòng", "ok", "Mục 3.4, 6.4"),
    ]),
    ("Câu hỏi nghiên cứu", [
        ("RQ1: RAGAS, LLM-judge tương quan với người", "part", f"Đo đầy đủ trên nhãn silver; nhãn người có {RES['agreement']['audit_CG']['n'] if RES['agreement'].get('audit_CG') else 60} claim (mục 4.1)"),
        ("RQ2: bằng chứng graph so với chỉ chunk", "part", "V1 so với V2; graph đưa vào dạng văn bản, chưa phải triple"),
        ("RQ3: revise giảm claim sai mà không giảm F1", "ok", "Giảm claim sai theo judge nhưng F1 giảm (mục 6.4)"),
    ]),
    ("Dữ liệu", [
        ("Câu hỏi ViHERMES", "ok", "100 câu, 20 câu mỗi mức hop"),
        ("ViEduReg (~500 câu quy chế đào tạo)", "no", ""),
        ("5 hệ thống × ~600 câu", "part", "2 hệ (Naive RAG, GraphRAG) × 100 câu"),
        ("~3.000 claim gán nhãn", "part", f"{RES['claims_total']} claim trong mẫu, nhãn silver"),
        ("3 nhãn + span bằng chứng", "part", "Đủ 3 nhãn; bằng chứng ở mức số đoạn, chưa có span"),
        ("2–3 người gán, báo cáo κ", "part", f"1 người, {RES['agreement']['audit_CG']['n'] if RES['agreement'].get('audit_CG') else AUD['n']} claim (2 lượt mù); chỉ có κ Claude–người"),
        ("~20% làm dev", "ok", f"{RES['claims_dev']} claim dev, {RES['claims_test']} claim test"),
        ("ViNLI >30K + ~20K cặp tổng hợp", "part", "12.000 + 3.328 cặp"),
    ]),
    ("Thiết lập thực nghiệm", [
        ("Baseline RAGAS với LLM mở", "ok", "Qwen2.5-3B/7B"),
        ("Baseline LLM-judge Qwen2.5-32B-AWQ (hoặc 14B)", "part", "Qwen2.5-3B/7B do phần cứng Colab T4"),
        ("Baseline SelfCheckGPT", "ok", "SelfCheckGPT-NLI, 3 mẫu"),
        ("Baseline NLI zero-shot đa ngôn ngữ", "ok", "mDeBERTa-v3-base-xnli"),
        ("Baseline hệ tốt nhất của ViHallu (nếu có mã nguồn)", "no", ""),
        ("Metric verifier: macro-F1, AUROC", "ok", "Mục 6.2, kèm KTC bootstrap và kiểm định ghép cặp"),
        ("Spearman/Kendall với người", "part", "Tính với nhãn silver; mẫu người không đủ cho mức câu trả lời"),
        ("Metric revise: thay đổi GGF và F1/EM", "ok", "GGF, token F1, EM (= 0, xem 6.4), thêm token recall"),
    ]),
    ("Ablation", [
        ("Bỏ triple", "ok", "V1 so với V2"),
        ("Bỏ rule số/ngày", "ok", "Biến thể + rule"),
        ("Encoder so với LLM nhỏ", "part", "mDeBERTa so với LLM-judge 3B/7B; chưa fine-tune LLM nhỏ"),
        ("Có/không dữ liệu tổng hợp", "ok", "Fine-tune chỉ ViNLI (mục 6.3)"),
        ("Số vòng revise", "ok", "1 vòng so với 2 vòng (mục 6.4)"),
    ]),
    ("Đóng góp và sản phẩm", [
        ("Bộ ViFaithKAG", "part", "Bản pilot: dataset/ViFaithKAG (claims, answers, passages JSONL)"),
        ("Verifier nhỏ", "ok", "mDeBERTa fine-tune"),
        ("Meta-evaluation metric tự động trên tiếng Việt", "ok", "Mục 6.2, 4.1"),
        ("Module cắm vào KAG solver như toán tử Verify", "no", ""),
        ("Paper và demo", "ok", "Báo cáo này và trang demo tương tác"),
        ("Chatbot quy chế cho trường", "no", "Phụ thuộc ViEduReg"),
        ("Rủi ro: báo cáo riêng kết quả trên claim thật", "ok", "Dữ liệu tổng hợp chỉ dùng để huấn luyện"),
    ]),
]
req_rows = "".join(f"<tr><th colspan='3'>{grp}</th></tr>" + "".join(
    f"<tr><td>{html.escape(item)}</td><td class='{st}'>{ST[st]}</td><td>{html.escape(note)}</td></tr>" for item, st, note in items)
    for grp, items in REQS)
req_count = {k: sum(st == k for _, items in REQS for _, st, _ in items) for k in ST}
CSS = """
@page{size:A4;margin:20mm 18mm}
body{font-family:'Times New Roman',serif;font-size:12.5pt;line-height:1.5;color:#1f2328}
h1{font-size:20pt;text-align:center;margin:0 0 4px}
h2{font-size:14.5pt;margin:22px 0 6px;border-bottom:1px solid #ccc;padding-bottom:3px}
h3{font-size:12.5pt;margin:14px 0 4px}
.sub{text-align:center;color:#555;margin-bottom:14px}
.abstract{border:1px solid #ddd;background:#f7f7f5;padding:10px 14px;margin:10px 0 16px}
table{border-collapse:collapse;width:100%;font-size:10.5pt;margin:8px 0}
th,td{border:1px solid #bbb;padding:4px 6px;text-align:left;vertical-align:top}
th{background:#eef1f5}
td:not(:first-child){text-align:right}
.tl td{text-align:left!important}
img{width:100%;margin:6px 0}
.cap{font-size:10pt;color:#555;text-align:center;margin-top:-2px}
.warn{border-left:4px solid #c4741b;background:#fdf4ea;padding:6px 10px}
code{font-size:10.5pt}
.small{font-size:10.5pt}
.ok{color:#1d6b3a;font-weight:bold}.part{color:#a3610f;font-weight:bold}.no{color:#a12b2b;font-weight:bold}
.req td:nth-child(2){text-align:center!important;white-space:nowrap}.req td{text-align:left!important}
"""

BODY = f"""
<h1>ViKAG-Faith: Đánh giá tính trung thực mức mệnh đề cho hệ hỏi đáp GraphRAG tiếng Việt</h1>
<div class="sub">Báo cáo thực nghiệm quy mô pilot · Dữ liệu ViHERMES (văn bản pháp quy y tế) · {today}</div>

<div class="abstract"><b>Tóm tắt.</b> Báo cáo đánh giá các metric faithfulness tự động cho hệ hỏi đáp tiếng Việt dùng truy xuất trên
đồ thị tri thức. Hai hệ (Naive RAG hybrid và GraphRAG dùng graph pháp quy của ViHERMES) cùng dùng Qwen2.5-3B trả lời 100 câu hỏi
ViHERMES (20 câu mỗi mức 1–5 hop). Câu trả lời được tách thành claim; {RES['claims_total']} claim của 80 câu trả lời được gán nhãn
supported / contradicted / unsupported ({gold_txt}). Trên tập test ({RES['claims_test']} claim, nhãn silver), verifier mDeBERTa
fine-tune trên ViNLI + cặp tổng hợp từ corpus đạt macro-F1 cao nhất ({f(ft1)}), ngang LLM-judge Qwen2.5-7B ({f(claim['judge_7b']['macro_f1'])};
{cmp_txt('nli_ft_v1 - judge_7b')}) và hơn rõ verifier zero-shot ({f(claim['nli_zs_v1']['macro_f1'])}). Ablation bỏ dữ liệu tổng hợp đưa
kết quả về mức zero-shot ({f(ns1)}). Tuy vậy, trên mẫu kiểm định mù do người gán, verifier fine-tune tụt xuống dưới judge-7B, nên ưu thế này
có thể đến từ việc học theo nhãn silver. Ở mức câu trả lời, <b>{NAMES[best_corr]}</b> tương quan cao nhất với nhãn chuẩn (Spearman ρ =
{f(corr[best_corr]['spearman'])}). SelfCheckGPT (không dùng bằng chứng) đạt {f(sc)}. Thêm thông tin graph dạng văn bản vào đầu vào NLI làm giảm
kết quả, và rule số/ngày không cải thiện thêm. Vòng <i>kiểm chứng rồi sửa</i> (judge 7B gắn cờ, bộ sinh viết lại) nâng GGF từ
{f(RA['GGF_before'])} lên {f(RA['GGF_after'])} (Wilcoxon p = {f(RA['wilcoxon_GGF_p'])}, đo bằng chính judge đó) nhưng giảm token F1 từ
{f(RA['answer_f1_before'])} xuống {f(RA['answer_f1_after'])}: câu trả lời trung thực hơn chủ yếu vì ngắn hơn. Naive RAG và GraphRAG
không khác nhau có ý nghĩa (GGF {f(sysr['naive']['GGF'])} và {f(sysr['graph']['GGF'])}, p = {f(sysr['wilcoxon_GGF_p'])}).</div>

<h2>1. Giới thiệu</h2>
<p>Hệ GraphRAG/KAG tiếng Việt hiện thường được chấm bằng F1 hoặc một điểm LLM-judge cho cả câu trả lời. Cách chấm này không chỉ ra
mệnh đề nào trong câu trả lời là bịa thêm hay mâu thuẫn với bằng chứng, trong khi với văn bản pháp quy, một con số hay một ngày hiệu
lực sai là đủ gây hậu quả. Đề tài là bản rút gọn của Project 4 trong đề cương ViKAG-Faith, theo đúng ba câu hỏi nghiên cứu của đề cương:</p>
<ul>
<li><b>RQ1.</b> Các metric faithfulness hiện có (RAGAS, LLM-judge, SelfCheckGPT) khớp với nhãn chuẩn đến mức nào trên tiếng Việt?</li>
<li><b>RQ2.</b> Verifier dùng bằng chứng graph (văn bản nguồn, số hiệu, quan hệ sửa đổi/dẫn chiếu), rule kiểm tra số/ngày và fine-tune trên
dữ liệu tổng hợp từ corpus có phát hiện claim sai tốt hơn verifier NLI chung không?</li>
<li><b>RQ3.</b> Vòng <i>kiểm chứng rồi sửa</i> (verify-then-revise) có giảm hallucination mà không làm giảm chất lượng trả lời không?</li>
</ul>
<p>Ngoài ra, mục 6.5 so sánh độ trung thực của Naive RAG và GraphRAG theo số hop.</p>

<h2>2. Công trình liên quan</h2>
<p class="small">RAGAS (Es và cs., EACL 2024 Demo) định nghĩa faithfulness là tỉ lệ statement suy ra được từ ngữ cảnh. SemEval-2024 SHROOM và
Mu-SHROOM nghiên cứu phát hiện hallucination; DSC2025 ViHallu đánh giá hallucination tiếng Việt nhưng không gắn với KG. ViHERMES
(Nguyen và cs., ACIIDS 2026) xây benchmark multi-hop về văn bản pháp quy y tế và graph cấu trúc pháp lý, cho thấy module Auditor kiểm
chứng nâng điểm LLM-judge từ 0,6823 lên 0,7554. Các hệ GraphRAG như LightRAG, HippoRAG 2 và KAG (Liang và cs., WWW 2025) chưa được
đánh giá faithfulness ở mức mệnh đề trên tiếng Việt. SelfCheckGPT (Manakul và cs., EMNLP 2023) phát hiện hallucination không cần bằng chứng,
dựa trên độ nhất quán giữa các câu trả lời lấy mẫu. Verifier dùng mDeBERTa-v3-base huấn luyện NLI đa ngôn ngữ (XNLI có tiếng Việt).</p>

<h2>3. Phương pháp</h2>
<h3>3.1 Hai hệ hỏi đáp được đánh giá</h3>
<p>Cả hai hệ dùng cùng corpus (998 đoạn văn bản của ViHERMES, 471 văn bản), cùng bộ truy xuất hybrid (BM25 + bge-m3, trọng số 0,5),
cùng ngân sách ngữ cảnh 6.000 ký tự và cùng bộ sinh Qwen2.5-3B-Instruct (nhiệt độ 0), nên khác biệt chỉ đến từ cách lấy ngữ cảnh:</p>
<ul>
<li><b>Naive RAG:</b> 8 đoạn có điểm cao nhất, cắt theo ngân sách.</li>
<li><b>GraphRAG:</b> 4 đoạn hạt giống, sau đó lan truyền trên graph cấu trúc pháp lý của ViHERMES (quan hệ AMENDS, REPLACES, REFERS_TO,
HAS_CLAUSE; 432 cạnh dẫn chiếu, 35 cạnh sửa đổi/thay thế), kèm danh sách quan hệ giữa các văn bản trong prompt.</li>
</ul>
<h3>3.2 Pipeline đánh giá</h3>
<ol>
<li><b>Tách claim:</b> Qwen2.5-3B, prompt tiếng Việt kèm ví dụ; mỗi claim một vị từ chính, tự hiểu được.</li>
<li><b>Tập bằng chứng</b> của mỗi câu trả lời = các đoạn hệ đã truy xuất ∪ các đoạn bằng chứng vàng của câu hỏi (ViHERMES cung cấp).
Mọi metric và người gán nhãn đều dùng đúng tập này, nên chênh lệch giữa các metric phản ánh chất lượng metric.</li>
<li><b>Nhãn:</b> supported (bằng chứng suy ra được), contradicted (bằng chứng nói ngược lại), unsupported (không đề cập / không đủ).
Claim tách hỏng được đánh dấu "claim lỗi" và loại khỏi phép đo.</li>
<li><b>Metric GGF</b> của một câu trả lời = tỉ lệ claim supported; CR, UR = tỉ lệ contradicted, unsupported.</li>
</ol>
<h3>3.3 Các metric tự động được so sánh</h3>
<ul>
<li><b>RAGAS faithfulness</b> tái hiện theo hai prompt gốc của thư viện (tách statement, rồi phán xét NLI), chạy với Qwen2.5-3B và 7B.</li>
<li><b>LLM-judge mức claim:</b> Qwen2.5-3B và 7B gán 3 nhãn cho các claim của đề tài.</li>
<li><b>Verifier NLI:</b> mDeBERTa-v3-base-xnli-multilingual, chạy trên cửa sổ 900 ký tự. Entailment lấy cửa sổ mạnh nhất; contradiction chỉ
xét 2 cửa sổ trùng từ nhiều nhất với claim (vì NLI hay gán "contradiction" cho văn bản không liên quan). Hai biến thể đầu vào:
<b>V1</b> chỉ đoạn văn; <b>V2</b> thêm tên văn bản, số hiệu và quan hệ lấy từ graph. Ngưỡng chọn trên tập dev
(V1: τ<sub>s</sub>={f(th['zs_v1'][0],2)}, τ<sub>c</sub>={f(th['zs_v1'][1],2)}; V2: τ<sub>s</sub>={f(th['zs_v2'][0],2)}, τ<sub>c</sub>={f(th['zs_v2'][1],2)}).</li>
<li><b>Verifier fine-tune:</b> mDeBERTa huấn luyện thêm trên 12.000 cặp ViNLI + 3.328 cặp tổng hợp từ các đoạn <i>không</i> thuộc mẫu đánh giá
(supported = câu gốc; contradicted = đổi con số/ngày hoặc thêm phủ định; unsupported = câu của đoạn khác cùng văn bản); 1 epoch, lr 5e-6,
giữ checkpoint tốt nhất trên dev, float32. <b>Ablation:</b> cùng cấu hình nhưng chỉ dùng ViNLI. Ngưỡng của mỗi biến thể chọn trên tập dev.</li>
<li><b>SelfCheckGPT-NLI</b> (Manakul và cs., EMNLP 2023): sinh thêm 3 câu trả lời (nhiệt độ 0,7) từ cùng prompt và ngữ cảnh; claim được coi là
đáng tin nếu các câu trả lời lấy mẫu kéo theo nó (trung bình xác suất entail/contradict của mDeBERTa). Phương pháp này không nhìn bằng chứng.</li>
<li><b>Rule số/ngày/số hiệu:</b> giá trị trong claim không có trong bằng chứng thì hạ nhãn supported thành unsupported; nếu câu bằng
chứng tương ứng có giá trị cùng loại khác thì gán contradicted.</li>
</ul>
<h3>3.4 Verify-then-revise (RQ3)</h3>
<p>Với mỗi câu trả lời trong mẫu, LLM-judge 7B (metric mức claim tốt nhất trong nhóm không cần huấn luyện) gắn cờ các claim unsupported hoặc
contradicted. Bộ sinh Qwen2.5-3B nhận lại <i>đúng ngữ cảnh đã truy xuất</i>, câu trả lời cũ và danh sách claim bị gắn cờ, rồi viết lại câu trả lời
(sửa hoặc bỏ các claim đó, chỉ dùng ngữ cảnh). Câu trả lời mới được tách claim và chấm lại bằng judge 7B trên cùng tập bằng chứng; tối đa 2 vòng.
Câu trả lời không có claim nào bị gắn cờ được giữ nguyên.</p>

<h2>4. Dữ liệu và gán nhãn</h2>
<p>100 câu hỏi được lấy ngẫu nhiên phân tầng từ 1.561 câu của ViHERMES (seed 42). Mẫu gán nhãn gồm 40 câu (8 câu mỗi mức hop) × 2 hệ
= 80 câu trả lời, {RES['claims_total']} claim; {RES['claims_bad']} claim lỗi bị loại, còn {n_usable} claim
(supported {gd.get('supported',0)}, contradicted {gd.get('contradicted',0)}, unsupported {gd.get('unsupported',0)}).
20% số câu hỏi ({RES['claims_dev']} claim) làm tập dev để chọn ngưỡng, phần còn lại ({RES['claims_test']} claim) làm tập test.</p>
<p>Quy trình gán nhãn: Claude gán toàn bộ claim kèm số đoạn bằng chứng và lý do (nhãn silver dùng cho mọi phép đo); người gán làm việc
trên trang HTML ngoại tuyến, <b>không biết câu trả lời thuộc hệ nào</b> (mã claim được ẩn danh hóa).</p>
{agree_html}

<h2>5. Thiết lập thực nghiệm</h2>
<table class="tl"><tr><th>Thành phần</th><th>Cấu hình</th></tr>
<tr><td>Bộ sinh câu trả lời, tách claim</td><td>Qwen2.5-3B-Instruct (Ollama, Q4_K_M), nhiệt độ 0</td></tr>
<tr><td>Embedding</td><td>bge-m3</td></tr>
<tr><td>LLM-judge, RAGAS</td><td>Qwen2.5-3B và Qwen2.5-7B (Ollama), num_ctx 12.288</td></tr>
<tr><td>Verifier</td><td>MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7; fine-tune float32, batch 4 × tích lũy 4, lr 5e-6, 1 epoch</td></tr>
<tr><td>SelfCheckGPT, verify-then-revise</td><td>3 mẫu, nhiệt độ 0,7 (seed 43–45); sửa tối đa 2 vòng, judge Qwen2.5-7B</td></tr>
<tr><td>Phần cứng</td><td>Google Colab T4 16GB cho mọi bước dùng mô hình; máy cá nhân cho dựng graph, phân tích, báo cáo</td></tr>
<tr><td>Thống kê</td><td>Macro-F1, AUROC (phát hiện claim không supported), Spearman/Kendall, KTC 95% bootstrap 1.000 lần (cả bootstrap ghép cặp cho hiệu số), Wilcoxon cặp</td></tr>
</table>

<h2>6. Kết quả</h2>
<h3>6.1 Chất lượng hỏi đáp của hai hệ (100 câu)</h3>
<table><tr><th>Hệ</th><th>Token F1 so với đáp án</th><th>Recall đoạn vàng trong ngữ cảnh</th><th>Tỉ lệ từ chối trả lời</th></tr>
<tr><td>Naive RAG</td><td>{f(qa['naive']['answer_f1'])}</td><td>{pct(qa['naive']['gold_passage_recall'])}</td><td>{pct(qa['naive']['abstain_rate'])}</td></tr>
<tr><td>GraphRAG</td><td>{f(qa['graph']['answer_f1'])}</td><td>{pct(qa['graph']['gold_passage_recall'])}</td><td>{pct(qa['graph']['abstain_rate'])}</td></tr></table>
<p>Hai hệ gần như ngang nhau. Với cùng ngân sách ngữ cảnh, graph của ViHERMES phát hành kèm dữ liệu khá thô (mỗi đoạn chỉ gắn với văn
bản gốc, ít cạnh sửa đổi), nên lan truyền trên graph thêm được ít đoạn vàng.</p>

<h3>6.2 RQ1: metric tự động so với nhãn chuẩn</h3>
<p><b>Mức claim.</b> {NAMES[best_claim]} đạt macro-F1 cao nhất ({f(claim[best_claim]['macro_f1'])}). Mốc "luôn đoán supported"
đạt {f(claim['majority_supported']['macro_f1'])}; {beat_txt}. Trong nhóm không cần huấn luyện, LLM-judge 7B tốt nhất
({f(claim['judge_7b']['macro_f1'])}), hơn judge 3B ({f(claim['judge_3b']['macro_f1'])}) và NLI zero-shot ({f(claim['nli_zs_v1']['macro_f1'])}).
SelfCheckGPT-NLI đạt {f(sc)}, tương đương NLI zero-shot dù không nhìn bằng chứng; nhưng độ chính xác của nó thấp
({f(claim['nli_selfcheck']['acc'])}) vì nó hay coi claim đúng là đáng ngờ khi các câu trả lời lấy mẫu diễn đạt khác nhau. Ngay cả phương pháp tốt
nhất vẫn còn xa mức thay được người: F1 cho nhãn contradicted và unsupported đều dưới 0,45.</p>
{FIG_CLAIM}
<div class="cap">Hình 1. Macro-F1 mức claim trên tập test (nhãn silver). Xanh: LLM-judge; cam: verifier NLI; xám: SelfCheckGPT, rule và mốc tham chiếu.</div>
<table><tr><th>Phương pháp</th><th>Macro-F1</th><th>KTC 95%</th><th>Acc</th><th>F1 sup.</th><th>F1 contra.</th><th>F1 unsup.</th><th>AUROC</th><th>n</th></tr>{claim_rows}</table>
<p class="small">AUROC: khả năng xếp hạng claim không supported cao hơn claim supported (NLI dùng 1 − P(entail); phương pháp khác dùng nhãn cứng).
LLM-judge thiếu nhãn ở vài claim do lỗi định dạng đầu ra nên n nhỏ hơn.</p>
<p><b>Mức câu trả lời.</b> {NAMES[best_corr]} tương quan cao nhất với GGF của nhãn chuẩn (ρ = {f(corr[best_corr]['spearman'])}).
Mô hình 7B tương quan cao hơn 3B ở cả RAGAS (ρ {f(corr['ragas_7b']['spearman'])} so với {f(corr['ragas_3b']['spearman'])}) và LLM-judge
(ρ {f(corr['judge_7b']['spearman'])} so với {f(corr['judge_3b']['spearman'])}); với cỡ mẫu {corr['ragas_7b']['n']} câu trả lời, chênh lệch
rõ nhất là ở RAGAS.</p>
{FIG_CORR}
<div class="cap">Hình 2. Tương quan Spearman giữa điểm tự động và GGF chuẩn trên các câu trả lời của tập test.</div>
<table><tr><th>Metric</th><th>Spearman ρ</th><th>Kendall τ</th><th>Số câu trả lời</th></tr>{corr_rows}</table>

<h3>6.3 RQ2: verifier dùng graph, rule số/ngày và fine-tune</h3>
<p>{rq2_sentence}. Ngưỡng tối ưu của V2 rất thấp (τ<sub>s</sub> = {f(th['zs_v2'][0],2)}): khi thêm tên văn bản vào đầu mỗi cửa sổ,
mô hình NLI gần như luôn cho xác suất entailment cao với claim nhắc tới văn bản đó, nên mất khả năng tách claim đúng và sai.
Rule số/ngày gần như không đổi kết quả (V1: {f(v1)} → {f(r1)}; V2: {f(v2)} → {f(r2)}); một nguyên nhân là nhiều lỗi trong dữ liệu
không nằm ở con số mà ở việc gán sai chủ thể (ví dụ nhiệm vụ của Văn phòng Bộ bị gán cho Viện Chiến lược và Chính sách y tế).</p>
<p><b>Fine-tune và ablation.</b> Trên dev của verifier, fine-tune với ViNLI + cặp tổng hợp nâng độ chính xác từ 0,758 lên 0,793 (ViNLI) và
từ 0,545 lên 0,875 (cặp tổng hợp); bản chỉ dùng ViNLI đạt 0,798 và 0,588. Trên tập test của đề tài, fine-tune V1 đạt {f(ft1)}, hơn zero-shot
({cmp_txt('nli_ft_v1 - nli_zs_v1')}), trong khi bản chỉ ViNLI đạt {f(ns1)}, ngang zero-shot ({cmp_txt('nli_nosynth_v1 - nli_zs_v1')}).
Vậy phần cải thiện đến từ <b>dữ liệu tổng hợp trong miền</b> (đổi số/ngày, phủ định, câu cùng văn bản), không phải từ thêm dữ liệu NLI tiếng Việt
chung. Fine-tune cũng giảm thiệt hại của V2 ({f(ft2)} so với {f(v2)} ở zero-shot) nhưng V2 vẫn kém V1. So với judge 7B, fine-tune V1 cao hơn
nhưng chưa có ý nghĩa ({cmp_txt('nli_ft_v1 - judge_7b')}); và như mục 4.1 cho thấy, ưu thế này không giữ được trên mẫu nhãn người.</p>
<table><tr><th>So sánh (macro-F1, tập test)</th><th>Hiệu số</th><th>KTC 95% bootstrap ghép cặp</th><th>Tỉ lệ mẫu bootstrap ≤ 0</th><th>n</th></tr>{cmp_rows}</table>
<p class="small"><b>Ghi chú tái lập.</b> Checkpoint mDeBERTa được lưu ở float16. Các lần fine-tune đầu tiên trên Colab (transformers 5.x giữ nguyên
dtype của checkpoint) huấn luyện ở fp16 thuần nên loss = NaN ngay từ đầu; checkpoint "tốt nhất" khi đó chính là mô hình gốc. Bản báo cáo trước
vì vậy đã kết luận nhầm rằng fine-tune không giúp ích. Mã hiện tại ép float32, dừng khi loss không hữu hạn, và mọi điểm verifier (kể cả zero-shot)
được chấm lại bằng float32.</p>

<h3>6.4 RQ3: verify-then-revise</h3>
<table><tr><th></th><th>Được sửa</th><th>GGF</th><th>CR</th><th>UR</th><th>Token F1</th><th>Số claim/câu</th><th>p (GGF)</th><th>p (F1)</th></tr>{rev_rows}</table>
<p class="small">GGF/CR/UR do judge 7B chấm, trên các câu trả lời còn claim sau khi sửa ({RA['scored']}/{RA['answers']}); p: Wilcoxon cặp trên các câu trả lời được sửa.
Token F1 so với đáp án chuẩn của ViHERMES, trên cả {RA['answers']} câu trả lời.</p>
<p>{RA['revised']}/{RA['answers']} câu trả lời có claim bị gắn cờ và được viết lại, trung bình {f(RA['mean_rounds_revised'], 1)} vòng. GGF tăng từ
{f(RA['GGF_before'])} lên {f(RA['GGF_after'])} và tỉ lệ claim mâu thuẫn giảm từ {f(RA['CR_before'])} xuống {f(RA['CR_after'])}. Nhưng chất lượng trả lời
giảm: token F1 từ {f(RA['answer_f1_before'])} xuống {f(RA['answer_f1_after'])} (p = {f(RA['wilcoxon_F1_p'])}), số claim mỗi câu từ
{f(RA['claims_before'], 2)} xuống {f(RA['claims_after'], 2)}, và {RA['abstained_after']} câu trả lời chuyển thành "không tìm thấy thông tin". Bộ sinh 3B
chủ yếu <b>xóa</b> claim bị gắn cờ thay vì sửa đúng theo bằng chứng. Mức tăng GGF là <b>giới hạn trên</b>: chính judge 7B vừa gắn cờ vừa chấm lại,
nên câu trả lời mới được tối ưu theo đúng thước đo đó. Câu trả lời đã sửa chưa được người gán nhãn. Hiệu quả rõ hơn ở Naive RAG
(GGF {f(RN['GGF_before'])} → {f(RN['GGF_after'])}, p = {f(RN['wilcoxon_GGF_p'])}) so với GraphRAG ({f(RG['GGF_before'])} → {f(RG['GGF_after'])},
p = {f(RG['wilcoxon_GGF_p'])}), vì GraphRAG ban đầu ít claim sai hơn theo judge.</p>
<p><b>Ablation số vòng sửa.</b> Cùng dữ liệu, dừng vòng lặp sau vòng 1 hoặc cho phép vòng 2:</p>
<table><tr><th>Cấu hình</th><th>GGF</th><th>CR</th><th>UR</th><th>Token F1</th><th>Token recall</th><th>EM</th><th>Số claim/câu</th><th>Từ chối</th></tr>{rounds_rows}</table>
<p class="small">"Không sửa" tính GGF trên các câu trả lời được chấm ở cấu hình 2 vòng. Token recall = tỉ lệ từ của đáp án chuẩn có trong câu trả lời.</p>
<p>Vòng 1 mang lại phần lớn mức tăng GGF ({f(RA['GGF_before'])} → {f(B1['GGF_after'])}). {BR['needed_round_2']['2']['answers']} câu trả lời vẫn còn claim bị gắn cờ
sau vòng 1 và đi tiếp vòng 2; trên {P2['n']} câu còn chấm được ở cả hai vòng, vòng 2 nâng GGF từ {f(P2['GGF_r1'])} lên {f(P2['GGF_r2'])} và giảm CR từ {f(P2['CR_r1'])} xuống
{f(P2['CR_r2'])}, nhưng chưa có ý nghĩa thống kê (Wilcoxon p = {f(P2['wilcoxon_GGF_p'])}); token F1 giảm tiếp {f(P2['F1_r1'])} → {f(P2['F1_r2'])}
(p = {f(P2['wilcoxon_F1_p'])}). Mỗi vòng thêm vừa bớt claim sai vừa bớt nội dung. <b>EM bằng {f(RA['answer_em_before'])} ở mọi cấu hình</b>, vì đáp án
của ViHERMES là đoạn văn dài (trung bình khoảng 115 từ) nên không câu trả lời nào trùng khớp hoàn toàn. Vì vậy EM không dùng được cho bộ dữ liệu này;
token recall cho thấy rõ hơn mức mất nội dung ({f(RA['answer_recall_before'])} → {f(B1['answer_recall_after'])} → {f(B2['answer_recall_after'])}).</p>

<h3>6.5 So sánh hai hệ và theo số hop</h3>
<table><tr><th>Hệ</th><th>Số câu trả lời</th><th>GGF</th><th>CR (contradicted)</th><th>UR (unsupported)</th></tr>
<tr><td>Naive RAG</td><td>{sysr['naive']['answers']}</td><td>{f(sysr['naive']['GGF'])}</td><td>{f(sysr['naive']['CR'])}</td><td>{f(sysr['naive']['UR'])}</td></tr>
<tr><td>GraphRAG</td><td>{sysr['graph']['answers']}</td><td>{f(sysr['graph']['GGF'])}</td><td>{f(sysr['graph']['CR'])}</td><td>{f(sysr['graph']['UR'])}</td></tr></table>
<p>Khác biệt GGF giữa hai hệ không có ý nghĩa thống kê (Wilcoxon cặp, p = {f(sysr['wilcoxon_GGF_p'])}). Độ trung thực giảm rõ ở câu
hỏi 4–5 hop:</p>
{FIG_HOP}
<div class="cap">Hình 3. GGF trung bình theo số hop (8 câu hỏi mỗi mức, mỗi hệ).</div>

<h2>7. Phân tích lỗi</h2>
<table class="tl"><tr><th>Loại lỗi</th><th>Ví dụ (claim → bằng chứng)</th></tr>
<tr><td>Sai mốc thời gian</td><td>"Luật sửa đổi Luật Dược trình Quốc hội tháng 10/2025" → tờ trình ghi "trình Quốc hội vào tháng 10 năm 2022"; mốc 10/2025 là của Luật An toàn thực phẩm.</td></tr>
<tr><td>Gán sai chủ thể</td><td>Nhiệm vụ truyền thông CCHC, quản lý Cổng TTĐT của Văn phòng Bộ bị gán cho Viện Chiến lược và Chính sách y tế.</td></tr>
<tr><td>Sai phép so sánh, tổng hợp</td><td>"Tổng mức phạt của nhóm phòng khám là 8 triệu" trong khi riêng một phòng khám đã bị phạt 30 triệu.</td></tr>
<tr><td>Từ chối sai</td><td>"Không có thông tin về thông tư phân nhóm thiết bị y tế" trong khi bằng chứng ghi rõ hiệu lực 01/01/2026.</td></tr>
<tr><td>Lỗi do bước tách claim</td><td>Claim đảo nghĩa ("cử tri kiến nghị phải tham gia BHYT tại trường học"), chèn tên người không có trong câu trả lời, câu dẫn không có nội dung ({RES['claims_bad']} claim lỗi).</td></tr>
</table>

<h2>8. Hạn chế</h2>
<ul>
<li><b>Nguồn nhãn:</b> {gold_txt}. {f'Đồng thuận Claude–người thấp, nên số tuyệt đối của RQ1 chỉ là ước lượng; mẫu kiểm định chỉ có {AUD["n"]} claim (thêm {agr["audit_G"]["n"]} claim ở các lượt nhanh) và một người gán (không phải chuyên gia pháp lý), nên chính nhãn người cũng có thể sai, nhất là với claim về sự vắng mặt thông tin.' if AUD else 'Kết quả RQ1 cần được kiểm chứng lại khi có nhãn người.'}
{'' if 'A_vs_B_kappa' in agr else 'Chưa có người gán thứ hai nên chưa đo được độ đồng thuận giữa người với người.'}</li>
<li><b>Quy mô nhỏ:</b> {RES['claims_test']} claim test và 63 câu trả lời test; khoảng tin cậy rộng, nhiều khác biệt giữa các metric chưa có ý nghĩa thống kê.</li>
<li><b>Mô hình nhỏ:</b> bộ sinh và bộ tách claim là Qwen2.5-3B do giới hạn phần cứng (GPU cá nhân 4GB không ổn định, phải dùng Colab miễn phí); judge lớn nhất là 7B.</li>
<li><b>RAGAS tái hiện:</b> dùng lại hai prompt gốc nhưng không dùng thư viện ragas, và chạy trên tập bằng chứng chung thay vì chỉ ngữ cảnh truy xuất.</li>
<li><b>Graph thô:</b> graph phát hành của ViHERMES chỉ gắn đoạn với văn bản và một ít quan hệ trích bằng regex, nên RQ2 chỉ kiểm tra loại thông tin graph này.</li>
<li><b>Fine-tune học theo nhãn silver:</b> ngưỡng được chọn theo nhãn Claude, và trên mẫu nhãn người verifier fine-tune kém judge 7B; cần
chọn ngưỡng và đánh giá lại trên nhãn người trước khi kết luận verifier fine-tune tốt hơn. Dữ liệu tổng hợp lấy từ cùng corpus (trừ các đoạn của
mẫu đánh giá), nên có thể quá khớp với văn phong của ViHERMES.</li>
<li><b>Verify-then-revise tự chấm:</b> câu trả lời đã sửa chỉ được chấm bằng judge đã gắn cờ, chưa có nhãn người hay metric độc lập ngoài token F1.</li>
<li><b>Một miền:</b> chỉ văn bản pháp quy y tế (ViHERMES).</li>
<li><b>Phần đề cương chưa làm</b> (thu hẹp theo quy mô pilot): bộ quy chế đào tạo ViEduReg; 5 hệ được đánh giá (mới có 2: Naive RAG và GraphRAG,
chưa có LightRAG/HippoRAG/KAG); verifier dựa trên Qwen fine-tune; tích hợp như một toán tử Verify trong pipeline KAG; hai người gán độc lập
và κ giữa người với người.</li>
</ul>

<h2>9. Kết luận</h2>
<p>Trên dữ liệu pháp quy y tế tiếng Việt, các metric faithfulness tự động chạy bằng LLM mở cỡ nhỏ chỉ khớp ở mức thấp đến trung bình với nhãn chuẩn.
<b>RQ1:</b> trong các metric có sẵn, LLM-judge 7B tốt nhất ở mức claim và RAGAS 7B tốt nhất ở mức câu trả lời; mô hình 7B tốt hơn 3B; SelfCheckGPT
không thay được metric có bằng chứng. <b>RQ2:</b> fine-tune verifier với dữ liệu tổng hợp trong miền là thay đổi duy nhất có ích rõ (ablation chỉ ViNLI
không cải thiện), còn thông tin graph dạng văn bản và rule số/ngày không giúp. Tuy nhiên, kiểm định mù cho thấy ưu thế của verifier fine-tune phụ
thuộc vào nhãn silver{(' (κ Claude–người = ' + f(AUD['kappa'], 2) + ', thứ hạng metric ρ = ' + f(AUD['rank_spearman'], 2) + ')') if AUD else ''}.
<b>RQ3:</b> vòng kiểm chứng rồi sửa giảm claim sai theo judge nhưng làm câu trả lời ngắn và kém đầy đủ hơn; với bộ sinh 3B, đó là đánh đổi chứ chưa
phải cải thiện thuần. Hướng tiếp theo: gán nhãn người đầy đủ với hai người (có chuyên môn pháp lý) và bước thống nhất bất đồng, chọn ngưỡng verifier trên
nhãn người, dùng judge ≥14B và bộ sinh lớn hơn cho bước sửa, chấm câu trả lời đã sửa bằng người hoặc một metric độc lập, và thử verifier đọc triple có
cấu trúc thay vì chuỗi văn bản.</p>

<h2>Tài liệu tham khảo</h2>
<ol class="small">
<li>Es, S. và cs. RAGAS: Automated Evaluation of Retrieval Augmented Generation. EACL 2024 Demo. arXiv:2309.15217.</li>
<li>Nguyen, L. S. T. và cs. ViHERMES: A Graph-Grounded Multihop QA Benchmark and System for Vietnamese Healthcare Regulations. ACIIDS 2026. arXiv:2602.07361. github.com/ura-hcmut/ViHERMES.</li>
<li>Liang, L. và cs. KAG: Boosting LLMs in Professional Domains via Knowledge Augmented Generation. WWW 2025. arXiv:2409.13731.</li>
<li>Guo, Z. và cs. LightRAG. arXiv:2410.05779. · Gutiérrez, B. J. và cs. HippoRAG 2. arXiv:2502.14802.</li>
<li>Mickus, T. và cs. SemEval-2024 Task 6: SHROOM. arXiv:2403.07726.</li>
<li>DSC2025 ViHallu. arXiv:2601.04711. · VLUE (gồm ViNLI). arXiv:2403.15882.</li>
<li>Laurer, M. và cs. mDeBERTa-v3-base-xnli-multilingual-nli-2mil7. Hugging Face.</li>
<li>Manakul, P., Liusie, A., Gales, M. SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models. EMNLP 2023. arXiv:2303.08896.</li>
</ol>

<h2>Phụ lục A: đối chiếu với đề cương Project 4</h2>
<p class="small">Mỗi hạng mục của đề cương ViKAG-Faith và phần đề tài pilot đã thực hiện: {req_count['ok']} hạng mục đạt,
{req_count['part']} hạng mục làm một phần hoặc thu nhỏ quy mô, {req_count['no']} hạng mục chưa làm. Các phần thu nhỏ chủ yếu liên quan đến
quy mô dữ liệu, số hệ thống, số người gán nhãn và kích thước mô hình (giới hạn phần cứng Colab T4), như đã nêu ở mục 8.</p>
<table class="req small"><tr><th>Hạng mục đề cương</th><th>Trạng thái</th><th>Thực hiện trong đề tài</th></tr>{req_rows}</table>

<h2>Phụ lục B: tái lập</h2>
<p class="small">Mã nguồn: <code>vikag-faith/src</code> (s1_answer → s2_claims → s3_pool → s4_judges → s5_verifier → s8_revise, s9_selfcheck → s6_annotation → s7_analysis),
notebook Colab sinh bởi <code>make_colab.py</code>, báo cáo sinh bởi <code>make_report.py</code>, trang demo bởi <code>make_demo.py</code>
(https://claude.ai/artifact/WpaWPBgdzeQgxe9jmwVeQ4), bộ dữ liệu <code>dataset/ViFaithKAG</code> bởi <code>make_dataset.py</code>. Seed 42. Mọi số liệu trong báo cáo đọc từ
<code>outputs/analysis/results.json</code>.</p>
"""

OUT_HTML.parent.mkdir(exist_ok=True)
OUT_HTML.write_text(f"<!doctype html><html lang='vi'><head><meta charset='utf-8'><title>ViKAG-Faith</title>"
                    f"<style>{CSS}</style></head><body>{BODY}</body></html>", encoding="utf-8")
subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={OUT_PDF}",
                OUT_HTML.as_uri()], check=True, capture_output=True)
print(OUT_PDF, f"gold={RES['gold']}")
