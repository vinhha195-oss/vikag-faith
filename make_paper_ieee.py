"""Build ieee/main.tex and its figures: the project as an IEEE conference paper in English (IEEEtran).

Every result is read from outputs/analysis/results.json and results_dot2.json through <<expr>> slots, so the paper
cannot drift from the Word version. Compile on Overleaf: upload ieee/ViKAG-Faith_IEEE_Overleaf.zip.
"""

import json
import re
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).parent
IEEE = ROOT / "ieee"
(IEEE / "figures").mkdir(parents=True, exist_ok=True)
R = json.load(open(ROOT / "outputs" / "analysis" / "results.json", encoding="utf-8"))
D2 = json.load(open(ROOT / "outputs" / "analysis" / "results_dot2.json", encoding="utf-8"))
_s = (ROOT / "demo" / "vikag_faith_demo.html").read_text(encoding="utf-8")
_a = _s.index("const DATA = ") + 13
E = json.load(open(ROOT / "outputs" / "analysis" / "ieee_extra.json", encoding="utf-8"))
CATCH = json.loads(_s[_a:_s.index("\n", _a)].strip().rstrip(";"))["summary"]["catch"]

CL, CO, CMP, REV, SY, QA = R["claim_level"], R["answer_level_correlation"], R["comparisons"], R["revise"], R["systems"], R["qa"]
AG = R["agreement"]
AC, AQ, ACG = AG["audit"], AG["audit_G"], AG["audit_CG"]
SENS, TH = ACG["sensitivity"], R["thresholds"]
RA, R1, R2 = REV["all"], REV["by_max_rounds"]["1"], REV["by_max_rounds"]["2"]
P2 = REV["by_max_rounds"]["round2_vs_round1"]
M, PS, PH, AP = D2["methods"], D2["paired_silver"], D2["paired_human"], D2["auroc_paired"]
J14, XZ1, XF1, XF3, QSP = M["judge_14b"], M["nli_xzs_v1"], M["nli_xft_v1"], M["nli_xft_v3"], M["qwen3b_span"]
FT1, FF1, FF3, V3 = M["nli_ft20_v1"], M["nli_ft20full_v1"], M["nli_ft20full_v3"], M["nli_zs_v3"]
R14, JC14, SPN = D2["corr_ragas_14b"], D2["corr_judge_14b"], D2["span"]
CM = ACG["confusion_claude_rows_human_cols"]
NOT_SUP = sum(CM[1]) + sum(CM[2])
HUMAN_SUP = CM[1][0] + CM[2][0]
HUMAN_AGREE = CM[1][1] + CM[2][2]


def n(x, d=3):
    if x is None:
        return "--"
    t = f"{abs(x):.{d}f}"
    return ("$-$" + t) if x < 0 and float(t) != 0 else t


def ci(v, d=2):
    return f"[{n(v['ci95'][0], d)}, {n(v['ci95'][1], d)}]"


def pc(x, d=0):
    return f"{100 * x:.{d}f}\\%"


def frac(a, b):
    return f"{a}/{b}"


# ---------- figures ----------
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"], "font.size": 8, "axes.edgecolor": "#666666", "pdf.fonttype": 42})
INK, ACC, ALT, MUTE = "#222222", "#1f3a5f", "#b5651d", "#9a9a9a"


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(7.1, 2.35))
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.3); ax.axis("off")

    def box(x, y, w, h, title, body, fc="#f2f4f6"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.05", fc=fc, ec="#777777", lw=0.7))
        ax.text(x + w / 2, y + h - 0.13, title, ha="center", va="top", fontsize=7.6, fontweight="bold", color=INK)
        ax.text(x + w / 2, y + h - 0.38, body, ha="center", va="top", fontsize=6.6, color=INK, linespacing=1.25)

    def arrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=0.8, color="#555555"))

    box(0.05, 2.15, 1.75, 1.05, "100 questions", "ViHERMES\n20 per hop level, 1\u20135")
    box(2.2, 2.15, 1.85, 1.05, "Two QA systems", "Naive RAG, GraphRAG\nsame corpus and generator")
    box(4.45, 2.15, 1.75, 1.05, "200 answers", "80 sampled\nfor labelling")
    box(6.6, 2.15, 1.65, 1.05, "Claim extraction", "Qwen2.5-3B\n284 claims in sample")
    box(0.05, 0.3, 1.75, 1.15, "Common evidence", "retrieved + gold passages\n+ graph information")
    box(2.2, 0.3, 1.85, 1.15, "Checkers", "RAGAS, LLM-judge,\nNLI, rule, SelfCheckGPT")
    box(4.45, 0.3, 1.75, 1.15, "Meta-evaluation", "against silver labels and\nblind human labels")
    box(6.6, 0.3, 1.65, 1.15, "Verify-then-revise", "judge flags claims,\ngenerator rewrites", fc="#e6edf5")
    box(8.55, 0.3, 1.4, 1.15, "Rescoring", "GGF, token F1,\nrecall", fc="#e6edf5")
    arrow(1.85, 2.67, 2.17, 2.67); arrow(4.1, 2.67, 4.42, 2.67); arrow(6.25, 2.67, 6.57, 2.67)
    arrow(0.92, 2.12, 0.92, 1.48); arrow(1.85, 0.87, 2.17, 0.87); arrow(4.1, 0.87, 4.42, 0.87)
    arrow(6.25, 0.87, 6.57, 0.87); arrow(8.3, 0.87, 8.52, 0.87); arrow(7.42, 2.12, 3.2, 1.48)
    fig.savefig(IEEE / "figures" / "pipeline.pdf", bbox_inches="tight", pad_inches=0.02); plt.close(fig)


NAMES = [("nli_ft_v1", "NLI fine-tuned V1", ALT), ("judge_7b", "LLM-judge 7B", ACC), ("nli_ft_v2", "NLI fine-tuned V2", ALT), ("judge_3b", "LLM-judge 3B", ACC),
         ("nli_selfcheck", "SelfCheckGPT-NLI", MUTE), ("nli_nosynth_v1", "NLI ViNLI-only V1", ALT), ("nli_zs_v1", "NLI zero-shot V1", ALT),
         ("nli_zs_v2", "NLI zero-shot V2", ALT), ("majority_supported", "Always supported", MUTE), ("rule_only", "Rule only", MUTE)]


def fig_scores():
    fig, ax = plt.subplots(figsize=(3.45, 2.5))
    for i, (k, lab, c) in enumerate(reversed(NAMES)):
        v = CL[k]
        ax.errorbar(v["macro_f1"], i, xerr=[[v["macro_f1"] - v["ci95"][0]], [v["ci95"][1] - v["macro_f1"]]], fmt="o", ms=3, color=c, elinewidth=1, capsize=1.5)
    ax.set_yticks(range(len(NAMES))); ax.set_yticklabels([x[1] for x in reversed(NAMES)])
    ax.set_xlabel("Macro-F1, silver labels, 95% CI"); ax.grid(axis="x", lw=0.3); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.savefig(IEEE / "figures" / "scores.pdf", bbox_inches="tight", pad_inches=0.02); plt.close(fig)


def fig_labels():
    keys = [k for k in ("judge_7b", "judge_3b", "nli_ft_v1", "nli_ft_v2", "nli_zs_v1", "nli_selfcheck") if k in SENS]
    lab = {"judge_7b": "Judge 7B", "judge_3b": "Judge 3B", "nli_ft_v1": "Fine-tuned V1", "nli_ft_v2": "Fine-tuned V2", "nli_zs_v1": "Zero-shot V1", "nli_selfcheck": "SelfCheckGPT"}
    fig, ax = plt.subplots(figsize=(3.45, 2.2))
    ys = range(len(keys))
    ax.barh([y + 0.19 for y in ys], [SENS[k]["macro_f1_vs_claude"] for k in keys], 0.36, color=MUTE, label="Scored against silver labels")
    ax.barh([y - 0.19 for y in ys], [SENS[k]["macro_f1_vs_human"] for k in keys], 0.36, color=ACC, label="Scored against human labels")
    ax.set_yticks(list(ys)); ax.set_yticklabels([lab[k] for k in keys]); ax.invert_yaxis()
    ax.set_xlabel(f"Macro-F1 on the {ACG['n']} human-labelled claims"); ax.legend(frameon=False, fontsize=7, loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.savefig(IEEE / "figures" / "labels.pdf", bbox_inches="tight", pad_inches=0.02); plt.close(fig)


def fig_hops():
    hops = ["1", "2", "3", "4", "5"]
    fig, ax = plt.subplots(figsize=(3.45, 1.9))
    ax.plot(hops, [SY["by_hop"]["naive"][h]["GGF"] for h in hops], marker="s", ms=3.5, color=MUTE, label="Naive RAG")
    ax.plot(hops, [SY["by_hop"]["graph"][h]["GGF"] for h in hops], marker="o", ms=3.5, color=ACC, label="GraphRAG")
    ax.set_ylim(0, 1); ax.set_xlabel("Hops"); ax.set_ylabel("Mean GGF (silver)"); ax.legend(frameon=False, fontsize=7); ax.grid(axis="y", lw=0.3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.savefig(IEEE / "figures" / "hops.pdf", bbox_inches="tight", pad_inches=0.02); plt.close(fig)


def fig_roc():
    fig, axes = plt.subplots(1, 2, figsize=(3.45, 1.85), sharey=True)
    series = [("zs_v1", "mDeBERTa zero-shot", MUTE), ("ft_v1", "Fine-tuned V1", ALT), ("ft20full_v1", "Fine-tuned 20k", "#7a3e9d"), ("xft_v1", "XLM-R fine-tuned", ACC)]
    for ax, tag, title in zip(axes, ("silver", "human"), ("Silver labels, test", "Human labels")):
        for k, lab, c in series:
            r = E["roc"][f"{k}|{tag}"]
            ax.plot(r["fpr"], r["tpr"], color=c, lw=1, label=f"{lab}")
        for j, mark in (("j7", "o"), ("j14", "s")):
            q = E["roc_points"][f"{j}|{tag}"]
            ax.plot(q["false_alarm"] / q["right"], q["caught"] / q["wrong"], mark, color="black", ms=3.5, label=f"Judge {j[1:]}B")
        ax.plot([0, 1], [0, 1], color="#cccccc", lw=0.6)
        ax.set_title(title, fontsize=8); ax.set_xlabel("False alarm rate")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("Detection rate")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=6.3, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.17))
    fig.savefig(IEEE / "figures" / "roc.pdf", bbox_inches="tight", pad_inches=0.02); plt.close(fig)


def fig_threshold():
    fig, ax = plt.subplots(figsize=(3.45, 1.85))
    for k, lab, c in (("ft_v1", "Fine-tuned V1", ALT), ("ft20full_v1", "Fine-tuned 20k", "#7a3e9d"), ("xft_v1", "XLM-R fine-tuned", ACC)):
        cu = E["threshold"][k]["curve"]
        ax.plot([x["ts"] for x in cu], [x["silver"] for x in cu], color=c, lw=1, label=f"{lab}, silver")
        ax.plot([x["ts"] for x in cu], [x["human"] for x in cu], color=c, lw=1, ls="--", label=f"{lab}, human")
    ax.set_xlabel(r"Support threshold $\tau_s$ ($\tau_c$ fixed at the dev choice)"); ax.set_ylabel("Macro-F1")
    ax.legend(frameon=False, fontsize=6, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.28)); ax.grid(axis="y", lw=0.3)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.savefig(IEEE / "figures" / "threshold.pdf", bbox_inches="tight", pad_inches=0.02); plt.close(fig)


def fig_kappa():
    names, vals = E["kappa"]["names"], E["kappa"]["values"]
    lab = {"human": "Human", "silver": "Silver", "j7": "Judge 7B", "j14": "Judge 14B", "j3": "Judge 3B", "ft_v1": "Fine-tuned V1", "ft20full_v1": "Fine-tuned 20k", "xft_v1": "XLM-R fine-t."}
    fig, ax = plt.subplots(figsize=(3.45, 2.75))
    m = [[vals[f"{a}|{b}"] for b in names] for a in names]
    ax.imshow(m, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(names))); ax.set_yticks(range(len(names)))
    ax.set_xticklabels([lab[x] for x in names], rotation=45, ha="right"); ax.set_yticklabels([lab[x] for x in names])
    for i, row in enumerate(m):
        for j, v in enumerate(row):
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.3, color="white" if v > 0.6 else INK)
    fig.savefig(IEEE / "figures" / "kappa.pdf", bbox_inches="tight", pad_inches=0.02); plt.close(fig)


def fig_scatter():
    fig, axes = plt.subplots(1, 2, figsize=(3.45, 1.7), sharey=True)
    for ax, t, lab, rho in zip(axes, ("7b", "14b"), ("RAGAS 7B", "RAGAS 14B"), (CO["ragas_7b"]["spearman"], R14["spearman"])):
        pts = E["more"]["scatter"][t]
        ax.scatter([x[1] for x in pts], [x[0] for x in pts], s=7, color=ACC, alpha=0.6, lw=0)
        ax.plot([0, 1], [0, 1], color="#cccccc", lw=0.6)
        ax.set_title(f"{lab}, rho = {rho:.3f}", fontsize=8); ax.set_xlabel("RAGAS score")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("Reference GGF")
    fig.savefig(IEEE / "figures" / "scatter.pdf", bbox_inches="tight", pad_inches=0.02); plt.close(fig)


def fig_gap():
    rows = [("Judge 7B", CL["judge_7b"]["macro_f1"], SENS["judge_7b"]["macro_f1_vs_human"]), ("Judge 14B", J14["macro_f1"], J14["macro_f1_human"]),
            ("Fine-tuned V1, round 1", CL["nli_ft_v1"]["macro_f1"], SENS["nli_ft_v1"]["macro_f1_vs_human"]), ("Fine-tuned V1, 20k", FF1["macro_f1"], FF1["macro_f1_human"]),
            ("Zero-shot V1", CL["nli_zs_v1"]["macro_f1"], SENS["nli_zs_v1"]["macro_f1_vs_human"]), ("XLM-R zero-shot V1", XZ1["macro_f1"], XZ1["macro_f1_human"]),
            ("XLM-R fine-tuned V1", XF1["macro_f1"], XF1["macro_f1_human"]), ("Qwen 3B with spans", QSP["macro_f1"], QSP["macro_f1_human"])]
    fig, ax = plt.subplots(figsize=(3.45, 2.1))
    for i, (lab, a, b) in enumerate(reversed(rows)):
        ax.plot([a, b], [i, i], color="#bbbbbb", lw=1.2, zorder=1)
        ax.scatter(a, i, s=14, color=MUTE, zorder=2, label="Silver" if i == 0 else None)
        ax.scatter(b, i, s=14, color=ACC, zorder=2, label="Human" if i == 0 else None)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in reversed(rows)]); ax.set_xlabel("Macro-F1"); ax.grid(axis="x", lw=0.3); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=2)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.savefig(IEEE / "figures" / "gap.pdf", bbox_inches="tight", pad_inches=0.02); plt.close(fig)


# ---------- table rows ----------
def row_main(name, k, ragas=False):
    if ragas:
        return f"{name} & -- & -- & -- & -- & {n(CO[k]['spearman'])} \\\\"
    v, s = CL[k], SENS.get(k)
    return f"{name} & {n(v['macro_f1'])} & {ci(v)} & {n(v['auroc_not_supported'])} & {n(s['macro_f1_vs_human']) if s else '--'} & {n(CO[k]['spearman']) if k in CO else '--'} \\\\"


MAIN_ROWS = "\n".join([
    row_main("LLM-judge Qwen2.5-7B", "judge_7b"), row_main("LLM-judge Qwen2.5-3B", "judge_3b"), row_main("NLI fine-tuned, V1", "nli_ft_v1"),
    row_main("NLI fine-tuned, V2 (+graph)", "nli_ft_v2"), row_main("NLI fine-tuned ViNLI only, V1", "nli_nosynth_v1"), row_main("NLI zero-shot, V1", "nli_zs_v1"),
    row_main("NLI zero-shot V1 + rule", "nli_zs_v1+rule"), row_main("NLI zero-shot, V2 (+graph)", "nli_zs_v2"), row_main("SelfCheckGPT-NLI", "nli_selfcheck"),
    row_main("Rule only", "rule_only"), row_main("Always supported", "majority_supported"), row_main("RAGAS (Qwen2.5-7B)", "ragas_7b", True), row_main("RAGAS (Qwen2.5-3B)", "ragas_3b", True)])


def row_cls(name, k):
    v = CL[k]; c = v["f1_per_class"]
    return f"{name} & {n(c['supported'])} & {n(c['contradicted'])} & {n(c['unsupported'])} & {n(v['acc'])} \\\\"


CLS_ROWS = "\n".join(row_cls(a, b) for a, b in (("Judge 7B", "judge_7b"), ("Judge 3B", "judge_3b"), ("Fine-tuned V1", "nli_ft_v1"), ("Zero-shot V1", "nli_zs_v1"),
                                               ("SelfCheckGPT", "nli_selfcheck"), ("Rule only", "rule_only")))
CMP_LABEL = {"nli_ft_v1 - judge_7b": "Fine-tuned V1 $-$ judge 7B", "nli_ft_v1 - nli_zs_v1": "Fine-tuned V1 $-$ zero-shot V1", "nli_ft_v1 - nli_nosynth_v1": "Fine-tuned V1 $-$ ViNLI only",
             "nli_nosynth_v1 - nli_zs_v1": "ViNLI only $-$ zero-shot V1", "nli_ft_v1 - nli_ft_v2": "Fine-tuned V1 $-$ fine-tuned V2", "judge_7b - nli_selfcheck": "Judge 7B $-$ SelfCheckGPT"}
CMP_ROWS = "\n".join(f"{CMP_LABEL[k]} & {n(v['diff'])} & {ci(v)} & {n(v['p_le_0'])} \\\\" for k, v in CMP.items())
LB = ["supported", "contradicted", "unsupported"]
CM_ROWS = "\n".join(f"{LB[i]} & {r[0]} & {r[1]} & {r[2]} & {pc(r[i] / sum(r))} \\\\" for i, r in enumerate(CM))


def row2(name, r, b=None):
    return f"{name} & {n(r['macro_f1'])} & {ci(r)} & {n(r['auroc_not_supported'])} & {r['caught']}/{r['wrong']} & {r['false_alarm']}/{r['right']} & {n(r['macro_f1_human'])} \\\\"


def base_row(name, k, c, auroc):
    v = CL[k]; h = SENS[k]["macro_f1_vs_human"]
    return f"{name} & {n(v['macro_f1'])} & {ci(v)} & {n(auroc)} & {c['caught']}/{c['wrong']} & {c['false_alarm']}/{c['right']} & {n(h)} \\\\"


R2_ROWS = "\n".join([
    base_row("Judge 7B", "judge_7b", CATCH["j7"], CL["judge_7b"]["auroc_not_supported"]), row2("Judge 14B", J14),
    base_row("Fine-tuned V1, round 1", "nli_ft_v1", CATCH["ft"], AP["ft20_v1 - ft_v1 silver"]["b"]),
    row2("Fine-tuned V1, 450 chars", FT1), row2("Fine-tuned V3, 450 chars", M["nli_ft20_v3"]), row2("Fine-tuned V1, 900 chars", FF1), row2("Fine-tuned V3, 900 chars", FF3), row2("Zero-shot V3", V3),
    row2("XLM-R zero-shot V1", XZ1), row2("XLM-R zero-shot V3", M["nli_xzs_v3"]), row2("XLM-R fine-tuned V1", XF1), row2("XLM-R fine-tuned V3", XF3), row2("Qwen 3B with spans", QSP)])
REV_ROWS = "\n".join(f"{name} & {n(g)} & {n(c)} & {n(u)} & {n(f1)} & {n(rc)} & {n(em)} & {n(cl, 2)} \\\\" for name, g, c, u, f1, rc, em, cl in (
    ("No revision", RA["GGF_before"], RA["CR_before"], RA["UR_before"], RA["answer_f1_before"], RA["answer_recall_before"], RA["answer_em_before"], RA["claims_before"]),
    ("At most 1 round", R1["GGF_after"], R1["CR_after"], R1["UR_after"], R1["answer_f1_after"], R1["answer_recall_after"], R1["answer_em_after"], R1["claims_after"]),
    ("At most 2 rounds", R2["GGF_after"], R2["CR_after"], R2["UR_after"], R2["answer_f1_after"], R2["answer_recall_after"], R2["answer_em_after"], R2["claims_after"])))
FULL_NAMES = {"judge_7b": "LLM-judge 7B", "judge_3b": "LLM-judge 3B", "nli_ft_v1": "Fine-tuned V1", "nli_ft_v1+rule": "Fine-tuned V1 + rule", "nli_ft_v2": "Fine-tuned V2",
              "nli_ft_v2+rule": "Fine-tuned V2 + rule", "nli_nosynth_v1": "ViNLI only V1", "nli_nosynth_v1+rule": "ViNLI only V1 + rule", "nli_nosynth_v2": "ViNLI only V2",
              "nli_nosynth_v2+rule": "ViNLI only V2 + rule", "nli_zs_v1": "Zero-shot V1", "nli_zs_v1+rule": "Zero-shot V1 + rule", "nli_zs_v2": "Zero-shot V2", "nli_zs_v2+rule": "Zero-shot V2 + rule",
              "nli_selfcheck": "SelfCheckGPT-NLI", "rule_only": "Rule only", "majority_supported": "Always supported"}


def row_full(k):
    v = CL[k]; c = v.get("f1_per_class", {}); h = SENS.get(k, {}).get("macro_f1_vs_human")
    return f"{FULL_NAMES[k]} & {n(v['macro_f1'])} & {ci(v)} & {n(v['acc'])} & {n(v['auroc_not_supported'])} & {n(c.get('supported'))} & {n(c.get('contradicted'))} & {n(c.get('unsupported'))} & {n(h)} \\\\"


FULL_ROWS = "\n".join(row_full(k) for k in FULL_NAMES)
CORR_NAMES = {**FULL_NAMES, "ragas_7b": "RAGAS 7B", "ragas_3b": "RAGAS 3B"}
_corr = [(CORR_NAMES[k], v) for k, v in CO.items() if "+rule" not in k and k in CORR_NAMES] + [("RAGAS 14B", R14), ("LLM-judge 14B", JC14)]
CORR_ROWS = "\n".join(f"{a} & {n(v['spearman'])} & {n(v['kendall'])} & {v['n']} \\\\" for a, v in sorted(_corr, key=lambda x: -x[1]["spearman"]))
TH_NAMES = {"zs_v1": "Zero-shot V1", "zs_v2": "Zero-shot V2", "zs_v3": "Zero-shot V3", "ft_v1": "Fine-tuned V1", "ft_v2": "Fine-tuned V2", "nosynth_v1": "ViNLI only V1", "nosynth_v2": "ViNLI only V2",
            "selfcheck": "SelfCheckGPT", "ft20_v1": "20k, 450 chars V1", "ft20_v3": "20k, 450 chars V3", "ft20full_v1": "20k, 900 chars V1", "ft20full_v3": "20k, 900 chars V3",
            "xzs_v1": "XLM-R zero-shot V1", "xzs_v3": "XLM-R zero-shot V3", "xft_v1": "XLM-R fine-tuned V1", "xft_v3": "XLM-R fine-tuned V3"}
_th = {**TH, **D2["thresholds"]}
TH_ROWS = "\n".join(f"{TH_NAMES[k]} & {n(_th[k][0], 2)} & {n(_th[k][1], 2)} \\\\" for k in TH_NAMES)
PAIR_NAMES = {"judge_14b": "Judge 14B", "nli_zs_v3": "Zero-shot V3", "nli_ft20_v1": "20k, 450 chars V1", "nli_ft20_v3": "20k, 450 chars V3", "nli_ft20full_v1": "20k, 900 chars V1", "nli_ft20full_v3": "20k, 900 chars V3",
              "nli_xzs_v1": "XLM-R zero-shot V1", "nli_xzs_v3": "XLM-R zero-shot V3", "nli_xft_v1": "XLM-R fine-tuned V1", "nli_xft_v3": "XLM-R fine-tuned V3", "qwen3b_span": "Qwen 3B with spans"}


def _pc(d, a, b):
    v = d[f"{a} - {b}"]
    return f"{n(v['diff'])} {ci(v)}"


PAIR_ROWS = "\n".join(f"{v} & {_pc(PS, k, 'nli_ft_v1')} & {_pc(PS, k, 'judge_7b')} & {_pc(PH, k, 'nli_ft_v1')} & {_pc(PH, k, 'judge_7b')} \\\\" for k, v in PAIR_NAMES.items())
HOP_ROWS = "\n".join(
    f"{h} & {b['claims']} & {pc(b['not_supported'] / b['claims'])} & {b['human']} & {pc(b['agree'] / b['human'])} & {n(SY['by_hop']['naive'][h]['GGF'], 2)} & {n(SY['by_hop']['graph'][h]['GGF'], 2)} & {n(SY['by_hop']['naive'][h]['CR'], 2)} & {n(SY['by_hop']['graph'][h]['CR'], 2)} \\\\"
    for h, b in E["by_hop"].items())
REV_SYS = "\n".join(f"{name} & {v['revised']}/{v['answers']} & {n(v['GGF_before'])} & {n(v['GGF_after'])} & {n(v['answer_f1_before'])} & {n(v['answer_f1_after'])} & {v['abstained_after']} \\\\"
                    for name, v in (("Naive RAG", REV["naive"]), ("GraphRAG", REV["graph"])))
_hl = {"j7": "Judge 7B", "j14": "Judge 14B", "j3": "Judge 3B", "ft_v1": "Fine-tuned V1", "ft20full_v1": "Fine-tuned 20k", "xft_v1": "XLM-R fine-tuned", "zs_v1": "Zero-shot V1"}
HL_ROWS = "\n".join(f"{_hl[k]} & {n(v['supported'])} & {n(v['contradicted'])} & {n(v['unsupported'])} & {v['catch']['caught']}/{v['catch']['wrong']} & {v['catch']['false_alarm']}/{v['catch']['right']} \\\\"
                    for k, v in E["human_per_label"].items())
_ht = {"zs_v1": "mDeBERTa zero-shot", "ft_v1": "Fine-tuned V1", "ft20full_v1": "Fine-tuned 20k", "xzs_v1": "XLM-R zero-shot", "xft_v1": "XLM-R fine-tuned"}
HT_ROWS = "\n".join(f"{_ht[k]} & {n(v['silver_tuned'])} & {n(v['human_tuned'])} & {n(v['diff'])} & {ci(v)} \\\\" for k, v in E["human_tuned"].items())
DH_ROWS = "\n".join(
    f"{_hl[k]} & {v['1-3']['caught']}/{v['1-3']['wrong']} & {v['1-3']['false_alarm']}/{v['1-3']['right']} & {v['4-5']['caught']}/{v['4-5']['wrong']} & {v['4-5']['false_alarm']}/{v['4-5']['right']} \\\\"
    for k, v in E["detect_by_hop_group"].items())
CB_ROWS = "\n".join(f"{k} & {v['silver']['caught']}/{v['silver']['wrong']} & {v['silver']['false_alarm']}/{v['silver']['right']} & {n(v['silver']['f1_flag'])} & {v['human']['caught']}/{v['human']['wrong']} & {v['human']['false_alarm']}/{v['human']['right']} & {n(v['human']['f1_flag'])} \\\\"
                    for k, v in E["combo"].items())
_pn = {"judge_7b": "Judge 7B", "nli_ft_v1": "Fine-tuned V1", "nli_zs_v1": "Zero-shot V1", "judge_3b": "Judge 3B"}
PASS_ROWS = "\n".join(f"{v} & {n(AC['sensitivity'][k]['macro_f1_vs_human'])} & {n(AQ['sensitivity'][k]['macro_f1_vs_human'])} & {n(SENS[k]['macro_f1_vs_human'])} \\\\" for k, v in _pn.items())
TH_GAP = E["threshold"]
EITHER, BOTH = E["combo"]["either flags"], E["combo"]["both flag"]
HTF = E["human_tuned"]["ft_v1"]
MORE = E["more"]
_bs = {"j7": "Judge 7B", "j14": "Judge 14B", "ft_v1": "Fine-tuned V1", "ft20full_v1": "Fine-tuned 20k", "xft_v1": "XLM-R fine-tuned"}
BS_ROWS = "\n".join(f"{_bs[k]} & {n(v['naive']['silver'])} & {n(v['graph']['silver'])} & {n(v['naive']['human'])} & {n(v['graph']['human'])} \\\\" for k, v in MORE["by_system"].items())


def _cf(k):
    return "\n".join(f"{LB[i]} & " + " & ".join(str(x) for x in r) + " \\\\" for i, r in enumerate(MORE["confusion_human"][k]))


CF7, CFX = _cf("j7"), _cf("xft_v1")


def _power(name, v):
    se = (v["ci95"][1] - v["ci95"][0]) / 3.92
    need = v["n"] * (2.8 * se / 0.05) ** 2
    return f"{name} & {v['n']} & {n(se)} & {int(round(need, -2)):,} \\\\"


POWER_ROWS = "\n".join([_power("Fine-tuned V1 $-$ judge 7B, silver", CMP["nli_ft_v1 - judge_7b"]), _power("Judge 14B $-$ judge 7B, silver", PS["judge_14b - judge_7b"]),
                        _power("Judge 14B $-$ judge 7B, human", PH["judge_14b - judge_7b"]), _power("XLM-R fine-tuned $-$ judge 7B, human", PH["nli_xft_v1 - judge_7b"])])
DIS = MORE["disagree"]
_dp = DIS["pairs"]
BIB = {
    "vihermes": r"L. S. T. Nguyen, Q. M. Bui, T. T. Ngo, Q. T. N. Vo, D. N. H. Le, and T. T. Quan, ``ViHERMES: A graph-grounded multihop question answering benchmark and system for Vietnamese healthcare regulations,'' in \emph{Proc. ACIIDS}, 2026, arXiv:2602.07361.",
    "ragas": r"S. Es, J. James, L. Espinosa-Anke, and S. Schockaert, ``RAGAs: Automated evaluation of retrieval augmented generation,'' in \emph{Proc. EACL System Demonstrations}, 2024.",
    "kag": r"L. Liang \emph{et al.}, ``KAG: Boosting LLMs in professional domains via knowledge augmented generation,'' 2024, arXiv:2409.13731.",
    "graphrag": r"D. Edge, H. Trinh, N. Cheng \emph{et al.}, ``From local to global: A graph RAG approach to query-focused summarization,'' 2024, arXiv:2404.16130.",
    "lightrag": r"Z. Guo, L. Xia, Y. Yu, T. Ao, and C. Huang, ``LightRAG: Simple and fast retrieval-augmented generation,'' 2024, arXiv:2410.05779.",
    "hipporag": r"B. J. Guti\'errez, Y. Shu, W. Qi, S. Zhou, and Y. Su, ``From RAG to memory: Non-parametric continual learning for large language models,'' 2025, arXiv:2502.14802.",
    "rag": r"P. Lewis, E. Perez, A. Piktus \emph{et al.}, ``Retrieval-augmented generation for knowledge-intensive NLP tasks,'' in \emph{Proc. NeurIPS}, vol. 33, 2020.",
    "selfcheck": r"P. Manakul, A. Liusie, and M. J. F. Gales, ``SelfCheckGPT: Zero-resource black-box hallucination detection for generative large language models,'' in \emph{Proc. EMNLP}, 2023, arXiv:2303.08896.",
    "shroom": r"T. Mickus, E. Zosa, R. V\'azquez \emph{et al.}, ``SemEval-2024 Task 6: SHROOM, a shared-task on hallucinations and related observable overgeneration mistakes,'' in \emph{Proc. SemEval}, 2024, arXiv:2403.07726.",
    "mushroom": r"R. V\'azquez, T. Mickus \emph{et al.}, ``SemEval-2025 Task 3: Mu-SHROOM, the multilingual shared task on hallucinations and related observable overgeneration mistakes,'' in \emph{Proc. SemEval}, 2025.",
    "vihallu": r"``DSC2025 ViHallu: Vietnamese hallucination detection challenge,'' 2026, arXiv:2601.04711.",
    "vlue": r"``VLUE: Vietnamese language understanding evaluation benchmark,'' 2024, arXiv:2403.15882.",
    "deberta": r"P. He, J. Gao, and W. Chen, ``DeBERTaV3: Improving DeBERTa using ELECTRA-style pre-training with gradient-disentangled embedding sharing,'' in \emph{Proc. ICLR}, 2023, arXiv:2111.09543.",
    "mdeberta": r"M. Laurer \emph{et al.}, ``mDeBERTa-v3-base-xnli-multilingual-nli-2mil7,'' Hugging Face model card. [Online]. Available: \url{https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7}",
    "bm25": r"S. Robertson and H. Zaragoza, ``The probabilistic relevance framework: BM25 and beyond,'' \emph{Found. Trends Inf. Retr.}, vol. 3, no. 4, pp. 333--389, 2009.",
    "bge": r"J. Chen, S. Xiao, P. Zhang \emph{et al.}, ``BGE M3-embedding: Multi-lingual, multi-functionality, multi-granularity text embeddings through self-knowledge distillation,'' 2024, arXiv:2402.03216.",
    "judge": r"L. Zheng, W.-L. Chiang, Y. Sheng \emph{et al.}, ``Judging LLM-as-a-judge with MT-Bench and Chatbot Arena,'' in \emph{Proc. NeurIPS}, vol. 36, 2023, arXiv:2306.05685.",
    "factscore": r"S. Min, K. Krishna, X. Lyu \emph{et al.}, ``FActScore: Fine-grained atomic evaluation of factual precision in long form text generation,'' in \emph{Proc. EMNLP}, 2023, arXiv:2305.14251.",
    "xnli": r"A. Conneau, R. Rinott, G. Lample \emph{et al.}, ``XNLI: Evaluating cross-lingual sentence representations,'' in \emph{Proc. EMNLP}, 2018.",
    "vinli": r"T. V. Huynh, K. V. Nguyen, and N. L.-T. Nguyen, ``ViNLI: A Vietnamese corpus for studies on open-domain natural language inference,'' in \emph{Proc. COLING}, 2022.",
    "qwen": r"Qwen Team, ``Qwen2.5 technical report,'' 2024, arXiv:2412.15115.",
}

TEMPLATE = r"""\documentclass[conference]{IEEEtran}
\usepackage[T1]{fontenc}
\usepackage{cite}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{array}
\usepackage{url}
\usepackage[hidelinks]{hyperref}
\graphicspath{{figures/}}
\begin{document}

\title{ViKAG-Faith: Graph-Grounded Claim-Level Faithfulness Evaluation and Verification for Vietnamese Knowledge-Augmented Generation}

\author{\IEEEauthorblockN{H\`a V\u{a}n Vinh}
\IEEEauthorblockA{Graduate student, Advanced Natural Language Processing\\
Vietnam}}

\maketitle

\begin{abstract}
Vietnamese RAG and GraphRAG question answering systems are usually scored with F1 or a single LLM-judge score for the whole answer. Neither shows which statements are backed by evidence and which are invented or contradicted. For legal regulations, one wrong effective date or fine is enough to cause harm. We build ViKAG-Faith, a claim-level faithfulness evaluation pipeline on ViHERMES. Two systems, Naive RAG and GraphRAG, answer 100 questions of 1--5 hops with Qwen2.5-3B. Answers are split into <<sum(1 for _ in open(ROOT / 'outputs' / 'claims.jsonl', encoding='utf-8'))>> claims, of which <<R['claims_total']>> claims from 80 answers are labelled supported, contradicted or unsupported against a common evidence set. We compare RAGAS, LLM-judges, SelfCheckGPT, multilingual NLI verifiers with and without graph information, number and date rules, verifiers fine-tuned on synthetic in-domain data, and a verify-then-revise loop. The primary labels are silver labels assigned by an LLM (Claude); <<ACG['n']>> claims were also labelled blindly by one human annotator. On those claims, the 7B judge reaches the highest macro-F1 (<<n(SENS['judge_7b']['macro_f1_vs_human'])>>), above every NLI verifier (best <<n(XF1['macro_f1_human'])>>). Fine-tuning with synthetic data raises the mDeBERTa verifier from <<n(CL['nli_zs_v1']['macro_f1'])>> to <<n(CL['nli_ft_v1']['macro_f1'])>> on silver labels, yet the gain disappears on human labels (<<n(SENS['nli_ft_v1']['macro_f1_vs_human'])>> versus <<n(SENS['nli_zs_v1']['macro_f1_vs_human'])>>). Silver labels agree with the human on <<pc(ACG['acc'])>> of claims ($\kappa=<<n(ACG['kappa'], 2)>>$), and metric rankings change with the label source. Verify-then-revise halves the contradiction rate but lowers token F1, because the small generator mostly deletes flagged claims.
\end{abstract}

\begin{IEEEkeywords}
GraphRAG, faithfulness, claim-level verification, Vietnamese, ViHERMES, meta-evaluation
\end{IEEEkeywords}

\section{Introduction}
GraphRAG and knowledge-augmented generation (KAG) bring knowledge graphs into retrieval to answer multi-step questions \cite{kag,graphrag,lightrag,hipporag}. ViHERMES \cite{vihermes} provides a multi-hop benchmark for Vietnamese healthcare regulations together with a legal structure graph, and shows that removing its Auditor (verification) module lowers the LLM-judge score from 0.7554 to 0.6823. Verification clearly matters, but the way faithfulness itself is measured on Vietnamese has not been evaluated.

An F1 or a single judge score for a whole answer does not reveal which statement is wrong. Common faithfulness metrics such as RAGAS \cite{ragas}, LLM-as-a-judge \cite{judge} and SelfCheckGPT \cite{selfcheck} have been validated mainly on English. DSC2025 ViHallu \cite{vihallu} evaluates Vietnamese hallucination, but not in connection with a knowledge graph or retrieved evidence.

Our approach splits answers into atomic claims, as FActScore \cite{factscore} does, checks each claim against a common evidence set of retrieved passages, gold passages and graph information, and measures how well each automatic metric matches reference labels. This is a meta-evaluation: the object under test is the checker, not the chatbot. We ask three questions.

\begin{itemize}
\item \textbf{RQ1:} How well do existing faithfulness metrics (RAGAS, LLM-judge, SelfCheckGPT, zero-shot NLI) match reference labels on Vietnamese?
\item \textbf{RQ2:} Do graph information, number and date rules, and fine-tuning on synthetic in-domain data help a verifier detect wrong claims better than a generic NLI verifier?
\item \textbf{RQ3:} How much does a verify-then-revise loop reduce unsupported claims, and does it hurt answer quality?
\end{itemize}

Our contributions are: (C1) a reproducible claim-level evaluation pipeline on ViHERMES; (C2) the pilot ViFaithKAG dataset with <<R['claims_total']>> silver-labelled claims, <<ACG['n']>> human-labelled claims and the scores of every metric; (C3) a meta-evaluation of 24 metric variants, 12 in each of two rounds, with ablations of graph input, rules, synthetic data and revision rounds; and (C4) an analysis of LLM label reliability against a human annotator, showing that metric rankings depend on the label source.

\section{Related Work}
\textbf{Measuring RAG faithfulness.} RAGAS \cite{ragas} defines faithfulness as the share of statements that can be inferred from the context, using an LLM to extract and judge statements. FActScore \cite{factscore} scores each atomic fact against a knowledge source. LLM-as-a-judge \cite{judge} uses a strong LLM as the grader; agreement with humans depends on model size and domain.

\textbf{Hallucination detection.} SelfCheckGPT \cite{selfcheck} needs no evidence and relies on consistency between sampled answers. SemEval-2024 SHROOM \cite{shroom} and SemEval-2025 Mu-SHROOM \cite{mushroom} standardise the detection of invented spans, and DSC2025 ViHallu \cite{vihallu} is a Vietnamese challenge on this topic.

\textbf{Vietnamese and multilingual NLI.} XNLI \cite{xnli} includes Vietnamese, and ViNLI \cite{vinli} is a Vietnamese NLI corpus that is part of VLUE \cite{vlue}. mDeBERTa-v3 \cite{deberta}, trained on multilingual NLI \cite{mdeberta}, is a widely used encoder verifier.

\textbf{Graph RAG, KAG and regulations.} RAG \cite{rag}, GraphRAG \cite{graphrag}, LightRAG \cite{lightrag}, HippoRAG 2 \cite{hipporag} and KAG \cite{kag} use graphs for retrieval or reasoning. ViHERMES \cite{vihermes} builds a Document--Article--Clause graph with amendment, replacement and citation relations for healthcare documents.

Table~\ref{tab:related} compares these lines of work with ours.

\begin{table*}[t]
\caption{Related work compared by evaluation unit, evidence, language and use of a graph}
\label{tab:related}
\centering
\footnotesize
\begin{tabular}{lllll}
\toprule
Work & Unit & Evidence & Language & Graph \\
\midrule
RAGAS \cite{ragas} & Statement & Retrieved context & Mainly English & No \\
FActScore \cite{factscore} & Atomic fact & Knowledge source & English & No \\
SelfCheckGPT \cite{selfcheck} & Sentence & None, sampled answers & English & No \\
SHROOM, Mu-SHROOM \cite{shroom,mushroom} & Span & None required & English, multilingual & No \\
ViHallu \cite{vihallu} & -- & Not tied to retrieval & Vietnamese & No \\
ViHERMES \cite{vihermes} & Whole answer & Retrieved context & Vietnamese & Legal graph \\
This work & Claim & Common evidence set & Vietnamese & Legal graph, triples \\
\bottomrule
\end{tabular}
\end{table*}

\textbf{Positioning.} We do not propose a new QA system. We evaluate verification metrics on Vietnamese at claim level against human labels, keeping the ViHERMES data and graph unchanged and adding only an evaluation layer.

\section{Proposed Method}
Fig.~\ref{fig:pipeline} summarises the pipeline. The upper row generates answers with two systems, the lower row evaluates each claim, and the revise branch uses verification results to rewrite answers.

\begin{figure*}[t]
\centering
\includegraphics[width=\textwidth]{pipeline.pdf}
\caption{The ViKAG-Faith pipeline. Answers in the labelled sample go to claim extraction, then to the checkers and to meta-evaluation.}
\label{fig:pipeline}
\end{figure*}

\subsection{Question answering systems}
Both systems share the ViHERMES corpus (998 passages from 471 documents), a hybrid BM25 \cite{bm25} and bge-m3 \cite{bge} retriever (weight 0.5), a budget of 6,000 characters and the Qwen2.5-3B-Instruct generator \cite{qwen} at temperature 0. Naive RAG takes the 8 best passages. GraphRAG takes 4 seed passages, propagates over the ViHERMES graph (depth up to 4, at most 8 nodes) and adds a list of document relations to the prompt. Any difference between the systems therefore comes only from how context is obtained.

\subsection{Claim extraction and common evidence}
Qwen2.5-3B extracts claims with a Vietnamese prompt containing two examples. Each claim must have one main predicate and stand alone, with pronouns replaced by names and numbers, dates and document identifiers kept intact. For each answer, the evidence is the union of the retrieved passages and the gold passages of the question, with the graph information of each passage (document title, identifier and relations). Every metric and the annotator use exactly this set, so differences between metrics reflect metric quality and not retrieval quality.

\subsection{Labels and answer-level metrics}
Each claim receives one label from supported, contradicted and unsupported. For an answer with claim set $C$, the faithfulness score GGF is the share of supported claims, and CR and UR are the contradicted and unsupported rates:
\begin{equation}
\mathrm{GGF}=\frac{|\{c\in C: c\ \text{supported}\}|}{|C|},
\end{equation}
\begin{equation}
\mathrm{CR}=\frac{|\{c\in C: c\ \text{contradicted}\}|}{|C|},\quad
\mathrm{UR}=\frac{|\{c\in C: c\ \text{unsupported}\}|}{|C|}.
\end{equation}

\subsection{Checkers}
\textbf{LLM-based metrics.} RAGAS faithfulness is reimplemented from the two original prompts of the library, and a claim-level LLM-judge assigns the three labels to our claims. Both run with Qwen2.5-3B and 7B through Ollama; round 2 adds 14B and a Qwen 3B verifier that returns a label with an evidence span. Unreadable outputs are excluded from measurement and never defaulted to a label.

\textbf{NLI verifier.} mDeBERTa-v3-base-xnli-multilingual \cite{deberta,mdeberta} runs on windows of 900 characters with a stride of 700; round 2 adds XLM-R large xnli, zero-shot and fine-tuned on 16,000 pairs. For claim $c$ and windows $w$,
\begin{equation}
P_{\mathrm{sup}}(c)=\max_{w}\,P(\mathrm{entail}\mid w,c),
\end{equation}
\begin{equation}
P_{\mathrm{con}}(c)=\max_{w\in W_2(c)}\,P(\mathrm{contradiction}\mid w,c),
\end{equation}
where $W_2(c)$ holds the two windows with the highest word overlap with the claim, because NLI models tend to return contradiction for unrelated text. A claim is supported if $P_{\mathrm{sup}}\ge\tau_s$, otherwise contradicted if $P_{\mathrm{con}}\ge\tau_c$, and otherwise unsupported. The thresholds are chosen on the dev split (V1 zero-shot: $\tau_s=<<n(TH['zs_v1'][0], 2)>>$, $\tau_c=<<n(TH['zs_v1'][1], 2)>>$). V1 uses passages only. V2 adds the document title, identifier and relations to the start of every window. V3 adds at most 3 triples sharing keywords with the claim, from 467 graph triples, and, through a mutual index, the source passage of any document the claim cites.

\textbf{Fine-tuning on synthetic data.} We combine 12,000 ViNLI \cite{vinli} pairs with 3,328 pairs built from passages outside the evaluation sample: supported is the original sentence; contradicted changes a number or date or adds a negation; unsupported is a sentence from another passage of the same document. Training runs one epoch at learning rate $5\times10^{-6}$, batch size 4 with 4 accumulation steps, in float32, keeping the best dev checkpoint. An ablation uses ViNLI only. Round 2 repeats this with 12,000 ViNLI pairs and 17,993 synthetic pairs. A first run on a 4 GB GPU had to shorten training premises to 450 characters and 200 tokens; it was then repeated with the round 1 input of 900 characters and 320 tokens.

\textbf{Rules and SelfCheckGPT.} A number, date or identifier in a claim that is missing from the evidence demotes supported to unsupported; if the matching evidence sentence holds a different value of the same kind, the claim becomes contradicted. SelfCheckGPT-NLI \cite{selfcheck} samples 3 extra answers at temperature 0.7 from the same prompt and context, and averages the mDeBERTa entailment and contradiction probabilities using each sample as premise. It does not see the evidence.

\subsection{Verify-then-revise}
For RQ3, the 7B judge flags unsupported or contradicted claims. Qwen2.5-3B receives the same retrieved context, the old answer and the flagged claims, and rewrites the answer by fixing or dropping them. The new answer is split into claims and rescored by the 7B judge, for at most 2 rounds.

\section{Dataset}
We draw 100 of the 1,561 ViHERMES questions by stratified sampling (20 per hop level, seed 42), so two systems give 200 answers. The labelled sample has 40 questions (8 per hop level) for 80 answers and <<R['claims_total']>> claims (Table~\ref{tab:data}).

\begin{table}[t]
\caption{Dataset statistics}
\label{tab:data}
\centering
\footnotesize
\begin{tabular}{p{0.46\columnwidth}p{0.44\columnwidth}}
\toprule
Item & Value \\
\midrule
Questions / hop levels & 100 / 20 per level, 1--5 \\
Answers (two systems) & 200 \\
Labelled sample & 80 answers, <<R['claims_total']>> claims (<<R['claims_bad']>> malformed claims excluded) \\
Silver label distribution & supported <<R['gold_distribution']['supported']>>, contradicted <<R['gold_distribution']['contradicted']>>, unsupported <<R['gold_distribution']['unsupported']>> \\
Dev / test split by question & <<R['claims_dev']>> / <<R['claims_test']>> claims \\
\bottomrule
\end{tabular}
\end{table}

\textbf{Claim extraction quality.} In the labelled sample, an answer has <<n(MORE['extraction']['mean_claims'], 2)>> claims on average and at most <<MORE['extraction']['max_claims']>>, with little change across hop levels (<<n(min(MORE['extraction']['by_hop'].values()), 2)>> to <<n(max(MORE['extraction']['by_hop'].values()), 2)>>). <<R['claims_bad']>> of <<R['claims_total']>> claims (<<pc(R['claims_bad'] / R['claims_total'], 1)>>) were excluded as malformed: repeated questions, lead-in phrases without content, vague statements, or placeholders such as ``[?]''. A further <<MORE['extraction']['multi_value']>> claims hold three or more numeric values and were marked for the annotator, because such claims can be partly right. Extraction by the same small model thus adds a source of error before any checker runs.

Synthetic pairs come from passages outside the evaluation sample, so they do not leak into the test split. The dev set holds 1,000 ViNLI pairs and 10\% of the synthetic pairs. Table~\ref{tab:dev} shows that synthetic data strongly raises accuracy on synthetic pairs, while the ViNLI-only model barely learns the in-domain error types.

\begin{table}[t]
\caption{Verifier accuracy on the dev set (three labels)}
\label{tab:dev}
\centering
\footnotesize
\begin{tabular}{lcc}
\toprule
Verifier & ViNLI dev & Synthetic dev \\
\midrule
mDeBERTa zero-shot & 0.758 & 0.545 \\
Fine-tuned, ViNLI + synthetic & 0.793 & 0.875 \\
Fine-tuned, ViNLI only & 0.798 & 0.588 \\
\bottomrule
\end{tabular}
\end{table}

\textbf{Silver labels.} Claude labelled all claims with evidence passage numbers and reasons. These labels are the reference for every test-set measurement, but they are not human labels.

\textbf{Human labels (blind audit).} One annotator worked on an offline HTML page without seeing Claude's labels or reasons, and without knowing which system produced an answer. Pass C covers 60 claims stratified by Claude's label (30/15/15) with full passages. Passes G, H, I and J each cover 30 random claims not used before, one claim per screen with the 4 most overlapping evidence sentences and the option to open the full passage. A pre-filled review pass (A) and two passes with exports not created through the labelling page (D, E) were excluded (Table~\ref{tab:audit}).

\begin{table}[t]
\caption{Human labelling passes}
\label{tab:audit}
\centering
\footnotesize
\begin{tabular}{p{0.2\columnwidth}p{0.3\columnwidth}ccc}
\toprule
Pass & Selection and display & Claims & Agree & $\kappa$ \\
\midrule
C & Stratified, full passage & <<AC['n']>> & <<pc(AC['acc'])>> & <<n(AC['kappa'], 2)>> \\
G, H, I, J & Random, 4 sentences & <<AQ['n']>> & <<pc(AQ['acc'])>> & <<n(AQ['kappa'], 2)>> \\
All & & <<ACG['n']>> & <<pc(ACG['acc'])>> & <<n(ACG['kappa'], 2)>> \\
Excluded & A, D, E & -- & -- & -- \\
\bottomrule
\end{tabular}
\end{table}

Table~\ref{tab:examples} shows three claims where the human label equals Claude's label, translated from Vietnamese.

\begin{table}[t]
\caption{Example claims and evidence (translated)}
\label{tab:examples}
\centering
\footnotesize
\begin{tabular}{p{0.36\columnwidth}p{0.36\columnwidth}p{0.16\columnwidth}}
\toprule
Claim & Evidence & Label \\
\midrule
The total fine of the three clinics is 8 million VND. & One clinic alone was fined 30,000,000 VND. & contra. \\
The Population Department has no role in inspection or handling violations. & Its duties include specialised inspection and handling violations in the population field. & contra. \\
Circular 30/2017/TT-BYT takes effect on 01/01/2018. & The evidence gives no such date. & unsup. \\
\bottomrule
\end{tabular}
\end{table}

\section{Experimental Setup}
\textbf{Configurations.} Round 1 compares 12 variants: LLM-judge and RAGAS with 3B and 7B; NLI zero-shot, fine-tuned and ViNLI-only, each with V1 and V2; SelfCheckGPT-NLI; and rule only. Each NLI variant is also tested with and without rules, and an always-supported baseline is included. Round 2 adds 12 variants: judge and RAGAS 14B, zero-shot V3, fine-tuned V1 and V3 at 450 and 900 characters, XLM-R zero-shot and fine-tuned V1 and V3, and Qwen 3B with spans.

\textbf{Metrics.} At claim level we report three-label macro-F1, per-label F1 and AUROC for detecting non-supported claims. At answer level we report Spearman and Kendall correlation between automatic scores and reference GGF on 61--63 test answers, depending on valid outputs. For revision we report changes in GGF, CR, UR, token F1, exact match and token recall against ViHERMES answers.

\textbf{Statistics.} We use 95\% bootstrap confidence intervals with 1,000 resamples, paired bootstrap for macro-F1 differences, paired Wilcoxon tests for system and before/after comparisons, and Cohen's $\kappa$ for agreement. Intervals are not corrected for multiple comparisons.

\textbf{Hardware.} Models run on a Google Colab T4 GPU (Ollama with Q4\_K\_M quantisation; PyTorch in float32), except zero-shot V3 on CPU and the short-premise fine-tune on a local GTX 1650.

\section{Results}
Table~\ref{tab:main} and Fig.~\ref{fig:scores} give the main results of round 1.

\begin{table*}[t]
\caption{Main results of round 1. Macro-F1, CI and AUROC on <<R['claims_test']>> test claims (silver labels); human column on <<ACG['n']>> human-labelled claims; Spearman $\rho$ between answer scores and reference GGF}
\label{tab:main}
\centering
\footnotesize
\begin{tabular}{lccccc}
\toprule
Method & Macro-F1 & 95\% CI & AUROC & Macro-F1 (human) & Spearman $\rho$ \\
\midrule
<<MAIN_ROWS>>
\bottomrule
\end{tabular}
\end{table*}

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{scores.pdf}
\caption{Claim-level macro-F1 on the test split. Blue: LLM-judges; orange: NLI verifiers; grey: SelfCheckGPT, rule and baseline.}
\label{fig:scores}
\end{figure}

\subsection{RQ1: Existing metrics}
In round 1, among methods that need no training, the 7B judge is best at claim level (macro-F1 <<n(CL['judge_7b']['macro_f1'])>>, AUROC <<n(CL['judge_7b']['auroc_not_supported'])>>), ahead of the 3B judge (<<n(CL['judge_3b']['macro_f1'])>>) and zero-shot NLI (<<n(CL['nli_zs_v1']['macro_f1'])>>). It catches <<CATCH['j7']['caught']>>/<<CATCH['j7']['wrong']>> wrong claims and raises <<CATCH['j7']['false_alarm']>>/<<CATCH['j7']['right']>> false alarms. All methods are weak on the two error labels (Table~\ref{tab:class}). SelfCheckGPT-NLI reaches <<n(CL['nli_selfcheck']['macro_f1'])>>, level with zero-shot NLI without seeing the evidence, but its accuracy is low (<<n(CL['nli_selfcheck']['acc'])>>) because it treats correct claims as doubtful when samples are worded differently. At answer level, RAGAS 7B has the highest correlation with reference GGF ($\rho=<<n(CO['ragas_7b']['spearman'])>>$) while RAGAS 3B reaches only <<n(CO['ragas_3b']['spearman'])>>, so judge size matters more than the metric formula. High accuracy does not imply a good metric: always predicting supported gives accuracy <<n(CL['majority_supported']['acc'])>>, which is why macro-F1 is our main measure.

\begin{table}[t]
\caption{F1 per label on the test split (silver labels)}
\label{tab:class}
\centering
\footnotesize
\begin{tabular}{lcccc}
\toprule
Method & Supp. & Contra. & Unsup. & Acc. \\
\midrule
<<CLS_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\subsection{RQ2: Graph, rules and fine-tuning}
Adding graph information to every window (V2) lowers zero-shot macro-F1 from <<n(CL['nli_zs_v1']['macro_f1'])>> to <<n(CL['nli_zs_v2']['macro_f1'])>>. Its best threshold is very low ($\tau_s=<<n(TH['zs_v2'][0], 2)>>$): with a document title at the start of each window, the model gives high entailment to any claim naming that document. Adding only triples related to each claim (V3) raises zero-shot macro-F1 to <<n(V3['macro_f1'])>>, above V2, but on human labels V3 falls below V1 (<<n(V3['macro_f1_human'])>> versus <<n(SENS['nli_zs_v1']['macro_f1_vs_human'])>>). Rules barely change results (<<n(CL['nli_zs_v1']['macro_f1'])>> to <<n(CL['nli_zs_v1+rule']['macro_f1'])>>), since many errors concern the wrong subject and not a number. On silver labels, fine-tuned V1 beats zero-shot (difference <<n(CMP['nli_ft_v1 - nli_zs_v1']['diff'])>>, 95\% CI <<ci(CMP['nli_ft_v1 - nli_zs_v1'])>>) and is not significantly above the 7B judge. The ViNLI-only ablation shows no gain (<<n(CMP['nli_nosynth_v1 - nli_zs_v1']['diff'])>>), so the improvement comes from the synthetic in-domain data (Table~\ref{tab:paired}).

\begin{table}[t]
\caption{Paired comparison of macro-F1 on the test split (silver labels, 1,000 bootstrap resamples)}
\label{tab:paired}
\centering
\footnotesize
\begin{tabular}{p{0.46\columnwidth}ccc}
\toprule
Comparison & Diff. & 95\% CI & Share $\le 0$ \\
\midrule
<<CMP_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\textbf{Human labels.} Fig.~\ref{fig:labels} reverses the conclusion on fine-tuning. On <<ACG['n']>> claims, fine-tuned V1 reaches <<n(SENS['nli_ft_v1']['macro_f1_vs_human'])>>, level with zero-shot (<<n(SENS['nli_zs_v1']['macro_f1_vs_human'])>>) and clearly below the 7B judge (<<n(SENS['judge_7b']['macro_f1_vs_human'])>>). The rank correlation of metrics between the two label sets is only $\rho=<<n(ACG['rank_spearman'], 2)>>$. Verifier thresholds are chosen on Claude's labels, so one explanation is that the fine-tuned model learnt Claude's strict labelling; Section~\ref{sec:posthoc} tests this. Table~\ref{tab:confusion} supports this: Claude labels <<NOT_SUP>> claims contradicted or unsupported, and the human agrees on only <<HUMAN_AGREE>> and labels <<HUMAN_SUP>> of them supported, whereas <<pc(CM[0][0] / sum(CM[0]))>> of Claude's supported labels are confirmed.

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{labels.pdf}
\caption{Macro-F1 of metrics on the human-labelled claims, scored against each label set.}
\label{fig:labels}
\end{figure}

\begin{table}[t]
\caption{Confusion between Claude labels (rows) and human labels (columns) on <<ACG['n']>> claims}
\label{tab:confusion}
\centering
\footnotesize
\begin{tabular}{lcccc}
\toprule
Claude & Supp. & Contra. & Unsup. & Agree \\
\midrule
<<CM_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\textbf{Round 2: larger models.} The 14B judge reaches <<n(J14['macro_f1'])>> on silver labels, not significantly different from the 7B judge (<<n(PS['judge_14b - judge_7b']['diff'])>>, CI <<ci(PS['judge_14b - judge_7b'])>>). On human labels it is lower (<<n(J14['macro_f1_human'])>> versus <<n(SENS['judge_7b']['macro_f1_vs_human'])>>, CI of the difference <<ci(PH['judge_14b - judge_7b'])>>). At answer level, RAGAS 14B reaches $\rho=<<n(R14['spearman'])>>$ and the 14B judge <<n(JC14['spearman'])>>, above the 7B versions (<<n(CO['ragas_7b']['spearman'])>> and <<n(CO['judge_7b']['spearman'])>>), but on <<R14['n']>> answers and without a test of the difference. XLM-R zero-shot V1 reaches <<n(XZ1['macro_f1'])>> on silver labels, clearly above mDeBERTa zero-shot (<<n(PS['nli_xzs_v1 - nli_zs_v1']['diff'])>>, CI <<ci(PS['nli_xzs_v1 - nli_zs_v1'])>>), but only <<n(XZ1['macro_f1_human'])>> on human labels. XLM-R fine-tuned V1 reaches <<n(XF1['macro_f1_human'])>> on human labels, significantly above XLM-R zero-shot (<<n(PH['nli_xft_v1 - nli_xzs_v1']['diff'])>>, CI <<ci(PH['nli_xft_v1 - nli_xzs_v1'])>>) and not significantly different from the 7B judge (CI <<ci(PH['nli_xft_v1 - judge_7b'])>>), at the cost of <<XF1['false_alarm']>>/<<XF1['right']>> false alarms. XLM-R fine-tuned V3 has the highest AUROC (<<n(XF3['auroc_not_supported'])>>), above round 1 on silver labels (CI <<ci(AP['xft_v3 - ft_v1 silver'])>>) but not on human labels. Qwen 3B with spans reaches <<n(QSP['macro_f1'])>> on silver and <<n(QSP['macro_f1_human'])>> on human labels, clearly below the 7B judge; only <<SPN['verbatim']>>/<<SPN['labelled']>> labels carry a span copied from the evidence, ignoring case and punctuation.

\textbf{Round 2: about 20,000 synthetic pairs.} Accuracy on synthetic dev pairs rises from 0.594 to 0.897. With short premises (450 characters, 200 tokens), fine-tuned V1 reaches only <<n(FT1['macro_f1'])>>, below round 1 (<<n(PS['nli_ft20_v1 - nli_ft_v1']['diff'])>>, CI <<ci(PS['nli_ft20_v1 - nli_ft_v1'])>>). Retraining with the round 1 input (900 characters, 320 tokens) gives <<n(FF1['macro_f1'])>>, the highest silver score, significantly above the short-premise model (<<n(PS['nli_ft20full_v1 - nli_ft20_v1']['diff'])>>, CI <<ci(PS['nli_ft20full_v1 - nli_ft20_v1'])>>) but not above round 1 (<<n(PS['nli_ft20full_v1 - nli_ft_v1']['diff'])>>, CI <<ci(PS['nli_ft20full_v1 - nli_ft_v1'])>>). AUROC barely moves (<<n(AP['ft20full_v1 - ft_v1 silver']['b'])>> to <<n(AP['ft20full_v1 - ft_v1 silver']['a'])>>, CI <<ci(AP['ft20full_v1 - ft_v1 silver'])>>). The first drop thus came from short premises, and more data did not improve discrimination. On human labels this model reaches only <<n(FF1['macro_f1_human'])>>, clearly below the 7B judge (CI <<ci(PH['nli_ft20full_v1 - judge_7b'])>>). Table~\ref{tab:round2} lists these results.

\begin{table*}[t]
\caption{Round 2 on the test split compared with round 1 and the 7B judge. Thresholds are chosen on dev with the round 1 grid. ``Caught'' counts wrong claims detected; ``False alarms'' counts correct claims flagged}
\label{tab:round2}
\centering
\footnotesize
\begin{tabular}{lcccccc}
\toprule
Method & Silver & 95\% CI & AUROC & Caught & False alarms & Human \\
\midrule
<<R2_ROWS>>
\bottomrule
\end{tabular}
\end{table*}

\subsection{RQ3: Verify-then-revise}
Of 80 answers, <<RA['revised']>> have flagged claims (Table~\ref{tab:revise}). GGF rises from <<n(RA['GGF_before'])>> to <<n(RA['GGF_after'])>> (Wilcoxon $p=<<n(RA['wilcoxon_GGF_p'])>>$) and CR halves, but token F1 falls from <<n(RA['answer_f1_before'])>> to <<n(RA['answer_f1_after'])>> ($p=<<n(RA['wilcoxon_F1_p'])>>$), claims per answer fall from <<n(RA['claims_before'], 2)>> to <<n(RA['claims_after'], 2)>>, and <<RA['abstained_after']>> answers become ``no information found''. The first revision round gives most of the gain: on the <<P2['n']>> answers that needed a second round, GGF moves from <<n(P2['GGF_r1'])>> to <<n(P2['GGF_r2'])>> without significance ($p=<<n(P2['wilcoxon_GGF_p'])>>$). Exact match is 0 in every configuration because ViHERMES answers are long (about 115 words), so token recall measures content loss. The GGF gain is an upper bound, since the 7B judge both flags and rescores.

\begin{table}[t]
\caption{Verify-then-revise on 80 answers. GGF, CR and UR from the 7B judge; F1, recall and EM against ViHERMES answers}
\label{tab:revise}
\centering
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{lccccccc}
\toprule
Setting & GGF & CR & UR & F1 & Recall & EM & Claims \\
\midrule
<<REV_ROWS>>
\bottomrule
\end{tabular}
\end{table}

Table~\ref{tab:revsys} splits the loop by system. Both systems gain GGF and lose token F1, so the trade-off does not depend on the retrieval method.

\begin{table}[t]
\caption{Verify-then-revise by system, at most 2 rounds}
\label{tab:revsys}
\centering
\footnotesize
\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{lcccccc}
\toprule
System & Revised & GGF before & After & F1 before & After & Refused \\
\midrule
<<REV_SYS>>
\bottomrule
\end{tabular}
\end{table}

Table~\ref{tab:revex} gives one 3-hop example. The 7B judge flagged the claim that the amended Pharmacy Law would go to the National Assembly in 10/2025, while the document says 10/2022. The new answer reached GGF of 1 by the judge but dropped all three dates, including the correct 01/07/2025 date that both the judge and Claude labelled supported, and replaced them with a generic sentence saying the dates are stated in the context. This pattern explains how GGF rises while token recall falls.

\begin{table}[t]
\caption{Verify-then-revise example (3 hops, Naive RAG, translated)}
\label{tab:revex}
\centering
\footnotesize
\begin{tabular}{p{0.45\columnwidth}p{0.45\columnwidth}}
\toprule
Before revision & After one round \\
\midrule
The amended Pharmacy Law is expected to go to the National Assembly in 10/2025. Decree 124/2021/ND-CP on administrative penalties in health was issued in 12/2021. Autonomous hospitals may decide drug procurement under Law 90/2025/QH15 from 01/07/2025. & No information was found on when the amended Pharmacy Law is expected to go to the National Assembly. The issuing date of Decree 124/2021/ND-CP and the date autonomous hospitals may decide drug procurement under Law 90/2025/QH15 are stated clearly in the context. \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Systems and hop difficulty}
The two systems do not differ significantly (paired Wilcoxon on GGF, $p=<<n(SY['wilcoxon_GGF_p'])>>$; Table~\ref{tab:systems}). The released ViHERMES graph is coarse, with few amendment edges, so propagation adds few gold passages. Faithfulness falls clearly at 4 and 5 hops (Fig.~\ref{fig:hops}).

\begin{table}[t]
\caption{Answer quality and faithfulness of the two systems}
\label{tab:systems}
\centering
\footnotesize
\begin{tabular}{lccccc}
\toprule
System & Token F1 & Gold recall & GGF & CR & UR \\
\midrule
Naive RAG & <<n(QA['naive']['answer_f1'])>> & <<pc(QA['naive']['gold_passage_recall'], 1)>> & <<n(SY['naive']['GGF'])>> & <<n(SY['naive']['CR'])>> & <<n(SY['naive']['UR'])>> \\
GraphRAG & <<n(QA['graph']['answer_f1'])>> & <<pc(QA['graph']['gold_passage_recall'], 1)>> & <<n(SY['graph']['GGF'])>> & <<n(SY['graph']['CR'])>> & <<n(SY['graph']['UR'])>> \\
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{hops.pdf}
\caption{Mean GGF by hop count, with 8 questions per level. GraphRAG has 7 answers with claims at 5 hops.}
\label{fig:hops}
\end{figure}

\subsection{Error analysis}
\begin{itemize}
\item \textbf{Wrong dates:} an answer places the amended Pharmacy Law in 10/2025, while the document says 10/2022; 10/2025 belongs to the Food Safety Law.
\item \textbf{Wrong subject:} a task of the Ministry Office is assigned to the Institute of Strategy and Policy. Number and date rules cannot catch this type.
\item \textbf{Wrong aggregation:} fines from several decisions are added incorrectly. Both LLM-judges miss this because they must add numbers across documents; NLI catches it.
\item \textbf{Invented lists:} an answer lists Instagram, TikTok and YouTube although the advertising certificate names others; zero-shot NLI is misled because another document in the context mentions Instagram.
\item \textbf{False refusals and extraction errors:} answers claim there is no information when the evidence is explicit, and <<R['claims_bad']>> claims were malformed by extraction.
\end{itemize}

Table~\ref{tab:cases} shows four of these errors with the verdict of each checker. The fine-tuned verifier matches the silver label on all four, the 7B judge on two and the 3B judge on one. The 7B judge misses the wrong sum and flags the invented item under another label.

\begin{table*}[t]
\caption{Four claims and the verdict of each checker (S supported, C contradicted, U unsupported; translated)}
\label{tab:cases}
\centering
\footnotesize
\begin{tabular}{p{0.11\textwidth}p{0.3\textwidth}p{0.3\textwidth}ccccc}
\toprule
Error type & Claim & Evidence & Silver & 7B & 3B & Zero-shot & Fine-tuned \\
\midrule
Wrong sum & The total fine of the three clinics is 8 million VND. & One clinic alone was fined 30 million VND. & C & S & S & C & C \\
False denial & The Population Department has no role in inspection or handling violations. & Its duties include specialised inspection and handling violations in the population field. & C & C & S & C & C \\
Invented item & Fine Vietnam Co. may advertise on Instagram. & Instagram appears only in the certificate of another company in the context. & U & C & U & S & U \\
Invented date & Circular 30/2017/TT-BYT takes effect on 01/01/2018. & The evidence gives no such date. & U & U & C & U & U \\
\bottomrule
\end{tabular}
\end{table*}

\subsection{Post hoc analyses}
\label{sec:posthoc}
The analyses in this subsection were designed after the main results, on the same data, so they suggest explanations and do not confirm them.

\textbf{Difficulty by hop.} Table~\ref{tab:hop} shows that the share of non-supported silver labels grows from <<pc(E['by_hop']['1']['not_supported'] / E['by_hop']['1']['claims'])>> at 1 hop to <<pc(E['by_hop']['4']['not_supported'] / E['by_hop']['4']['claims'])>> at 4 hops. Claude and the human also agree less at 3 and 4 hops (<<pc(E['by_hop']['3']['agree'] / E['by_hop']['3']['human'])>> and <<pc(E['by_hop']['4']['agree'] / E['by_hop']['4']['human'])>>) than at 1 and 2 hops (<<pc(E['by_hop']['1']['agree'] / E['by_hop']['1']['human'])>> and <<pc(E['by_hop']['2']['agree'] / E['by_hop']['2']['human'])>>), so hard questions are also hard to label. Table~\ref{tab:dethop} shows that the 7B judge detects <<E['detect_by_hop_group']['j7']['1-3']['caught']>>/<<E['detect_by_hop_group']['j7']['1-3']['wrong']>> wrong claims at 1--3 hops but only <<E['detect_by_hop_group']['j7']['4-5']['caught']>>/<<E['detect_by_hop_group']['j7']['4-5']['wrong']>> at 4--5 hops. A faithfulness score is therefore least reliable on the questions where wrong claims are most frequent.

\begin{table}[t]
\caption{Profile by hop on usable claims: silver error share, Claude--human agreement, mean GGF and CR for Naive RAG (N) and GraphRAG (G)}
\label{tab:hop}
\centering
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{ccccccccc}
\toprule
Hop & Claims & Wrong & Human & Agree & GGF N & GGF G & CR N & CR G \\
\midrule
<<HOP_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\begin{table}[t]
\caption{Detection of non-supported claims by hop group, all usable claims, silver labels}
\label{tab:dethop}
\centering
\footnotesize
\begin{tabular}{lcccc}
\toprule
 & \multicolumn{2}{c}{1--3 hops} & \multicolumn{2}{c}{4--5 hops} \\
Checker & Caught & False al. & Caught & False al. \\
\midrule
<<DH_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\textbf{The silver--human gap.} Fig.~\ref{fig:gap} places both scores side by side. The gap has no single direction: LLM-judge 7B scores higher on human labels, while the verifiers tuned on silver labels fall. Table~\ref{tab:hl} gives per-label results on human labels, using all <<ACG['n']>> claims. The human labelled <<ACG['human_distribution']['supported']>> claims supported, <<ACG['human_distribution']['unsupported']>> unsupported and <<ACG['human_distribution']['contradicted']>> contradicted, so the contradicted F1 rests on few examples. XLM-R fine-tuned has the best contradicted F1, and the 7B judge the best supported and unsupported F1.

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{gap.pdf}
\caption{Macro-F1 on silver labels (test split) and human labels for selected checkers.}
\label{fig:gap}
\end{figure}

\begin{table}[t]
\caption{Per-label F1 and detection on human labels}
\label{tab:hl}
\centering
\footnotesize
\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{lccccc}
\toprule
Checker & Supp. & Contra. & Unsup. & Caught & False al. \\
\midrule
<<HL_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\textbf{Disagreement in detail.} Claude and the human differ on <<DIS['n']>> claims. Of these, <<_dp.get('contradicted>supported', 0) + _dp.get('unsupported>supported', 0)>> are claims Claude rejects and the human accepts, <<_dp.get('supported>contradicted', 0) + _dp.get('supported>unsupported', 0)>> go the other way, and <<_dp.get('contradicted>unsupported', 0) + _dp.get('unsupported>contradicted', 0)>> differ only between contradicted and unsupported, so both sides call the claim wrong. On the disputed claims the 7B judge sides with the human <<DIS['j7_with_human']>> times and with Claude <<DIS['j7_with_silver']>> times. Table~\ref{tab:dis} shows examples. In several, Claude's reason points to a precise detail, such as a shortened name or a change from a subsidy to a contribution, which suggests that the human may accept near matches. In others, Claude asks for an explicit statement where a reader might accept a reasonable inference.

\begin{table*}[t]
\caption{Examples of disagreement between Claude and the human (translated; S supported, C contradicted, U unsupported)}
\label{tab:dis}
\centering
\footnotesize
\begin{tabular}{p{0.4\textwidth}p{0.38\textwidth}ccc}
\toprule
Claim & Claude's reason & Claude & Human & 7B \\
\midrule
The representative of Thai Ha General Clinic is Mr. Le Son. & The correct name is Mr. Le Quang Son. & C & S & S \\
Policy sets the insurance contribution of students at 50\% of the minimum contribution. & Students receive a subsidy of at least 50\%; they do not contribute 50\%. & C & S & S \\
The Institute of Strategy and Policy manages the Hai Thuong Lan Ong award golden book. & The golden book is managed by the Department of Traditional Medicine. & C & S & C \\
Fine Vietnam Co. may advertise on Pinterest. & Pinterest is not mentioned. & U & C & C \\
Health staff at the CDC centre must propose the GSP certification of vaccine stores. & No rule says that health staff propose it. & U & S & S \\
GSP principles are taken from the World Health Organization. & Issued on the basis of WHO guidance. & S & C & S \\
\bottomrule
\end{tabular}
\end{table*}

Table~\ref{tab:cfh} shows how two checkers err against the human. The 7B judge tends to accept claims, while XLM-R fine-tuned rejects many supported claims.

\begin{table}[t]
\caption{Human labels (rows) against predictions (columns) on the human-labelled claims}
\label{tab:cfh}
\centering
\footnotesize
\begin{tabular}{lccc}
\toprule
Judge 7B & Supp. & Contra. & Unsup. \\
\midrule
<<CF7>>
\midrule
XLM-R fine-tuned & Supp. & Contra. & Unsup. \\
\midrule
<<CFX>>
\bottomrule
\end{tabular}
\end{table}

\textbf{Discrimination without thresholds.} Fig.~\ref{fig:roc} shows ROC curves for detecting non-supported claims. On silver labels, fine-tuned verifiers separate from zero-shot, with AUROC <<n(E['roc']['ft_v1|silver']['auc'])>> against <<n(E['roc']['zs_v1|silver']['auc'])>>. On human labels the gap narrows but remains (<<n(E['roc']['ft_v1|human']['auc'])>> against <<n(E['roc']['zs_v1|human']['auc'])>>), and XLM-R fine-tuned reaches <<n(E['roc']['xft_v1|human']['auc'])>>. So fine-tuning keeps some ranking signal under human labels even though macro-F1 at the chosen threshold does not improve. At their fixed operating points, both judges lie above the verifier curves on both label sets, so at the same false alarm rate they detect more wrong claims.

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{roc.pdf}
\caption{ROC curves for detecting non-supported claims. Dots mark the fixed operating points of the 7B and 14B judges.}
\label{fig:roc}
\end{figure}

\textbf{Threshold sensitivity.} Fig.~\ref{fig:threshold} varies the support threshold. For fine-tuned V1, the dev thresholds give <<n(TH_GAP['ft_v1']['dev_score'])>>, while the best grid point on test gives <<n(TH_GAP['ft_v1']['test_best'])>>; for XLM-R fine-tuned the figures are <<n(TH_GAP['xft_v1']['dev_score'])>> and <<n(TH_GAP['xft_v1']['test_best'])>>. Those best points are oracle values, not results, but they show that <<R['claims_dev']>> dev claims select thresholds with an error of up to about 0.1 in macro-F1. Differences of this size between verifiers should not be over-interpreted, and AUROC is the safer comparison.

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{threshold.pdf}
\caption{Macro-F1 against the support threshold. Solid: silver labels on test; dashed: human labels.}
\label{fig:threshold}
\end{figure}

\textbf{Tuning thresholds on human labels.} If thresholds tuned on silver labels caused the drop, tuning on human labels should recover it. We ran grouped five-fold cross-validation over the <<ACG['n']>> human-labelled claims, keeping claims of one question in one fold, and pooled the held-out predictions (Table~\ref{tab:ht}). Fine-tuned V1 does not improve (<<n(HTF['silver_tuned'])>> to <<n(HTF['human_tuned'])>>, CI of the difference <<ci(HTF)>>), and no verifier improves significantly. Thresholds alone therefore do not explain the gap on this sample, although each fold trains on only about 130 claims and the chosen thresholds vary between folds.

\begin{table}[t]
\caption{Macro-F1 on human labels: thresholds from silver dev against grouped five-fold thresholds from human labels}
\label{tab:ht}
\centering
\footnotesize
\begin{tabular}{lcccc}
\toprule
Verifier & Silver & Human & Diff. & 95\% CI \\
\midrule
<<HT_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\textbf{Agreement between checkers.} Fig.~\ref{fig:kappa} gives pairwise Cohen's $\kappa$ on the human-labelled claims. The human agrees more with the 7B judge ($\kappa=<<n(E['kappa']['values']['human|j7'], 2)>>$) than with the silver labels ($\kappa=<<n(E['kappa']['values']['human|silver'], 2)>>$) or the 14B judge ($\kappa=<<n(E['kappa']['values']['human|j14'], 2)>>$). Agreement with the human is low for every checker, and the 7B judge and the verifiers also agree little with one another, which suggests that they make different errors.

\begin{figure}[t]
\centering
\includegraphics[width=0.92\columnwidth]{kappa.pdf}
\caption{Pairwise Cohen's $\kappa$ on the human-labelled claims.}
\label{fig:kappa}
\end{figure}

\textbf{Combining two checkers.} Because the 7B judge and XLM-R fine-tuned disagree often ($\kappa=<<n(E['kappa']['values']['j7|xft_v1'], 2)>>$), we tested two simple rules on the binary task of flagging a claim (Table~\ref{tab:combo}). Flagging when either checker objects catches <<EITHER['silver']['caught']>>/<<EITHER['silver']['wrong']>> wrong claims on silver labels at the cost of <<EITHER['silver']['false_alarm']>>/<<EITHER['silver']['right']>> false alarms. Flagging only when both object cuts false alarms to <<BOTH['silver']['false_alarm']>>/<<BOTH['silver']['right']>> and still catches <<BOTH['silver']['caught']>>. Neither rule beats the 7B judge alone on flag F1, but they offer two useful operating points.

\begin{table}[t]
\caption{Flagging rules from the 7B judge and XLM-R fine-tuned V1; ``F1'' is for the flag class}
\label{tab:combo}
\centering
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{lcccccc}
\toprule
 & \multicolumn{3}{c}{Silver, test} & \multicolumn{3}{c}{Human} \\
Rule & Caught & False al. & F1 & Caught & False al. & F1 \\
\midrule
<<CB_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\textbf{Answer-level agreement.} Fig.~\ref{fig:scatter} plots RAGAS against reference GGF. Scores spread widely at every GGF level, so even the best correlation does not make a single answer's score dependable. Two RAGAS versions also differ: their rank correlation with each other is $\rho=<<n(MORE['ragas_vs_ragas']['rho'], 2)>>$ on <<MORE['ragas_vs_ragas']['n']>> answers.

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{scatter.pdf}
\caption{RAGAS score against reference GGF for test answers. Each dot is one answer; the grey line marks equality.}
\label{fig:scatter}
\end{figure}

\textbf{Results by system.} Table~\ref{tab:bysys} splits checker scores by the system that produced the answer. Differences between systems are smaller than differences between label sets, so the checker comparison does not depend on one system.

\begin{table}[t]
\caption{Macro-F1 by answer system}
\label{tab:bysys}
\centering
\footnotesize
\begin{tabular}{lcccc}
\toprule
 & \multicolumn{2}{c}{Silver, test} & \multicolumn{2}{c}{Human} \\
Checker & Naive & Graph & Naive & Graph \\
\midrule
<<BS_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\textbf{Sample size.} Many intervals in this paper include zero. Table~\ref{tab:power} estimates the claims needed to detect a macro-F1 difference of 0.05 with 80\% power, taking the standard error from the bootstrap interval and assuming that it shrinks with the square root of the sample. The estimates are optimistic because claims from one answer are not independent. They still show that the target of about 3,000 claims in our proposal is of the right order, and that the present sample cannot settle differences of this size.

\begin{table}[t]
\caption{Estimated claims needed to detect a difference of 0.05 in macro-F1 with 80\% power}
\label{tab:power}
\centering
\footnotesize
\begin{tabular}{p{0.52\columnwidth}ccc}
\toprule
Comparison & $n$ & SE & Needed \\
\midrule
<<POWER_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\textbf{Effect of the audit pass.} Table~\ref{tab:pass} compares pass C, stratified with full passages, against the random quick passes. The 7B judge leads in both, so the main finding does not depend on the display condition. Pass C oversamples errors, so scores between the two columns are not directly comparable.

\begin{table}[t]
\caption{Macro-F1 on human labels by audit pass}
\label{tab:pass}
\centering
\footnotesize
\begin{tabular}{lccc}
\toprule
Checker & Pass C (<<AC['n']>>) & G--J (<<AQ['n']>>) & All (<<ACG['n']>>) \\
\midrule
<<PASS_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\textbf{Cost.} Table~\ref{tab:cost} lists wall-clock times of round 2. They come from file timestamps of a single run, so they are indicative only. The 14B judge with RAGAS took about 2.8 hours for 80 answers, roughly 30 times the 3B span run, without a significant claim-level gain.

\begin{table}[t]
\caption{Wall-clock time of round 2 jobs (single run)}
\label{tab:cost}
\centering
\footnotesize
\begin{tabular}{p{0.6\columnwidth}cc}
\toprule
Job & GPU & Time \\
\midrule
Judge and RAGAS 14B, 80 answers & T4 & about 2.8 h \\
Qwen 3B with spans, 80 answers & T4 & 5 min \\
XLM-R zero-shot, <<R['claims_total']>> claims, V1 and V3 & T4 & 6.5 min \\
XLM-R fine-tune, 16,000 pairs, with scoring & T4 & 69 min \\
mDeBERTa fine-tune, 29,993 pairs, 900 chars, with scoring & T4 & 53 min \\
mDeBERTa fine-tune, 29,993 pairs, 450 chars & GTX 1650 & about 2 h \\
\bottomrule
\end{tabular}
\end{table}

\section{Discussion}
\textbf{Which checker should a practitioner use?} On this data, the 7B judge is the most defensible default. It leads on human labels, is not significantly below the best verifier on silver labels, and needs no training. Moving to 14B brings a clear gain only at answer level, where RAGAS reaches $\rho=<<n(R14['spearman'])>>$, and even that gain is untested. A team that wants one faithfulness number per answer can use RAGAS 14B, while a team that needs to locate wrong claims should stay with a claim-level judge. For regulations, where missing a wrong claim costs more than reviewing a correct one, the either-flags rule is a reasonable triage step: it passes few wrong claims but sends close to half of the correct claims to a human reader. It supports human review and does not replace it.

\textbf{Why do silver and human labels disagree?} We can see the size of the disagreement but not who is right. Claude labels <<NOT_SUP>> claims as non-supported and the human confirms <<HUMAN_AGREE>> of them. Three explanations are plausible. Claude may be stricter about implicit inferences. The annotator, who is not a legal expert, may accept claims that a lawyer would reject. The quick passes may also hide distant evidence, although Table~\ref{tab:pass} shows the same leading checker in both conditions. Adjudication by two legal experts is the only way to separate these. Until then, both label sets should be reported, because a ranking from one source does not transfer to the other.

\textbf{What does fine-tuning learn?} Accuracy on synthetic dev pairs reaches about 0.9, far above any score on real claims. Synthetic errors change a number, a date or a negation, or borrow a sentence from elsewhere. Real errors in our sample also include wrong subjects, wrong aggregation across documents and invented list items, which these perturbations do not produce. A verifier can thus master the synthetic task without learning the real one. This fits the flat AUROC from 15,000 to 30,000 pairs: adding more pairs of the same kind does not help. Future synthetic data should reproduce the observed error types, for example by swapping the responsible agency between passages of one document.

\textbf{Why did graph input not help?} Prepending metadata to each window makes every claim that names a document look entailed. Selective triples avoid part of this, but the released graph is coarse and is passed as plain text. Our result concerns this form of graph input on this graph, and it does not show that graphs cannot help verification.

\textbf{What does revision really do?} A faithfulness score alone rewards deletion. An answer that says less contains fewer wrong claims, so GGF improves as content disappears. Any revision loop should therefore be scored by faithfulness and completeness together, with an independent scorer. With a 3B generator the loop mostly removes content, and a larger generator may behave differently.

\textbf{Recommendations for meta-evaluation.} Our results suggest four practices for future work on Vietnamese faithfulness evaluation. First, report the label source and keep human labels for at least part of the sample, because a ranking on LLM labels may not hold. Second, compare checkers with threshold-free measures as well as macro-F1, since small dev sets make thresholds unstable. Third, report detection and false alarms separately, because a high macro-F1 can hide a verifier that rejects a third or more of correct claims. Fourth, split results by hop, since a mean score hides the weakest questions, where errors are most common.

\section{Threats to Validity}
\textbf{Silver reference.} Claude agrees with the human on <<pc(ACG['acc'])>> of claims ($\kappa=<<n(ACG['kappa'], 2)>>$). We therefore report both label sets; more human labels and a second annotator with adjudication are needed.

\textbf{One annotator.} The annotator is not a legal expert, and quick passes show 4 evidence sentences, so distant evidence may be missed. Pass C uses full passages and is reported separately.

\textbf{Small scale.} We evaluate 2 systems, <<R['claims_total']>> claims and judges up to 14B. Bootstrap intervals and paired tests accompany the main comparisons, without multiple-comparison correction.

\textbf{Thresholds tuned on silver labels.} Only <<R['claims_dev']>> dev claims are available, and thresholds tuned on silver labels may lean toward Claude. Tuning on human labels did not improve scores in our cross-validation (Table~\ref{tab:ht}), but that sample is small.

\textbf{Self-scored revision.} Revised answers are scored only by the judge that flagged them. Rescoring by humans or an independent metric is needed.

\textbf{Graph as text.} Triples are appended as text, so verifiers do not read graph structure. ViEduReg and the KAG Verify operator are not covered.

\textbf{Post hoc and multiple comparisons.} Many comparisons were run without correction, and the analyses in Section~\ref{sec:posthoc} were chosen after seeing the main results. Intervals that barely exclude zero should be read as hints.

\textbf{Implementation.} Early fine-tuning runs produced NaN loss because the mDeBERTa checkpoint is stored in float16; all reported runs use float32. Round 1 on Colab used transformers 5.x, and round 2 used 4.46. Ollama runs Q4\_K\_M quantised models, so results may differ from full-precision weights.

\section{Conclusion}
On Vietnamese healthcare regulations, automatic faithfulness metrics running on small open LLMs match reference labels only at a low to moderate level. The 7B judge is the most stable metric across both label sets, and the 14B judge is not significantly better at claim level. RAGAS is best at answer level and improves with model size. Fine-tuning mDeBERTa on synthetic in-domain data raises silver scores but not human-label scores, and about 20,000 pairs bring no significant gain; XLM-R fine-tuning improves on human labels but raises many false alarms. Tuning thresholds on human labels did not close the gap. Meta-evaluation with LLM labels can therefore change metric rankings, and reports should state their label source. Verify-then-revise with a 3B generator reduces wrong claims by deleting content, which is a trade-off and not a pure improvement.

Future work includes full human labelling by two annotators with legal expertise and threshold selection on human labels; a 32B judge and a fine-tuned small Qwen verifier whose spans are copied from the evidence; structured triple input for verifiers and extension to LightRAG, HippoRAG 2, KAG and ViEduReg; and independent scoring of revised answers with a larger generator. Code and data are available at \url{https://github.com/vinhha195-oss/vikag-faith}.

\appendices

\section{Prompts}
The RAGAS prompts follow the library. The statement prompt reads: ``Given a question, an answer, and sentences from the answer analyze the complexity of each sentence given under `sentences' and break down each sentence into one or more fully understandable statements while also ensuring no pronouns are used in each statement.'' The verdict prompt reads: ``Your task is to judge the faithfulness of a series of statements based on a given context. For each statement you must return verdict as 1 if the statement can be directly inferred based on the context or 0 if the statement can not be directly inferred based on the context.'' Both ask for JSON output, and the first keeps the language of the answer.

The remaining prompts are in Vietnamese; these are English translations.

\textbf{Generator.} ``You are an assistant answering questions about Vietnamese healthcare legal documents. Use only information in the CONTEXT. Answer in Vietnamese in 2--5 sentences, naming documents when available. If the context is insufficient, say clearly that no information was found.''

\textbf{Claim extraction.} ``Split the answer into atomic claims. Each claim states ONE fact with one main predicate. Each claim must be self-contained: replace pronouns with specific names. Keep numbers, dates and document identifiers as in the answer. Add nothing beyond the answer, and drop sentences that only say no information was found.'' Two worked examples follow.

\textbf{LLM-judge.} ``You are a fact checker. For each claim, compare with the EVIDENCE and assign exactly one label. supported: the evidence implies the claim. contradicted: the evidence says the opposite (wrong figure, date, document name, negation, and so on). unsupported: the evidence does not mention it or is not enough to conclude.'' The span verifier adds: ``For each claim, copy verbatim one short sentence from the EVIDENCE as the basis in the span field; if there is none, leave the string empty.''

\section{Annotation Protocol}
The annotator received a single offline HTML page holding the claim, the question and the evidence; labels were saved locally and exported as a file. Claim identifiers were anonymised, so the annotator could not tell which system produced a claim, and neither Claude's labels nor its reasons were shown. An earlier pre-filled review pass confirmed all <<AG['pass_A_excluded']['confirmed']>> labels with <<AG['pass_A_excluded']['labels_changed']>> changes in about 10 minutes. Such a result says little about label quality, so we discarded it and moved to blind passes. Passes D and E were excluded because their exports were not created through the labelling page. In the quick passes, the annotator could skip a claim; <<AQ['n_input'] - AQ['n']>> claims were skipped and are not counted.

\section{Full Results}
Table~\ref{tab:full} lists every round 1 configuration. Table~\ref{tab:corr} lists answer-level correlations, Table~\ref{tab:th} the dev thresholds, and Table~\ref{tab:pairfull} the paired comparisons of round 2.

\begin{table*}[t]
\caption{All round 1 configurations on <<R['claims_test']>> test claims (silver labels), with macro-F1 on human labels}
\label{tab:full}
\centering
\footnotesize
\begin{tabular}{lcccccccc}
\toprule
Method & Macro-F1 & 95\% CI & Acc. & AUROC & F1 supp. & F1 contra. & F1 unsup. & Human \\
\midrule
<<FULL_ROWS>>
\bottomrule
\end{tabular}
\end{table*}

\begin{table*}[t]
\caption{Paired macro-F1 differences of round 2 methods with 95\% CI (1,000 bootstrap resamples, not corrected for multiple comparisons)}
\label{tab:pairfull}
\centering
\footnotesize
\begin{tabular}{lcccc}
\toprule
Method & Silver, $-$ fine-tuned V1 & Silver, $-$ judge 7B & Human, $-$ fine-tuned V1 & Human, $-$ judge 7B \\
\midrule
<<PAIR_ROWS>>
\bottomrule
\end{tabular}
\end{table*}

\begin{table}[t]
\caption{Answer-level correlation with reference GGF on the test split, sorted by Spearman $\rho$; $n$ is the number of answers with valid output}
\label{tab:corr}
\centering
\footnotesize
\begin{tabular}{lccc}
\toprule
Metric & Spearman & Kendall & $n$ \\
\midrule
<<CORR_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\begin{table}[t]
\caption{Thresholds chosen on the dev split}
\label{tab:th}
\centering
\footnotesize
\begin{tabular}{lcc}
\toprule
Verifier & $\tau_s$ & $\tau_c$ \\
\midrule
<<TH_ROWS>>
\bottomrule
\end{tabular}
\end{table}

\section{Reproducibility}
The repository holds the pipeline as numbered scripts. \texttt{s1\_answer} generates answers, \texttt{s2\_claims} extracts claims, \texttt{s3\_pool} builds the evidence sets, \texttt{s3b\_triples} builds triples and the mutual index, \texttt{s4\_judges} runs RAGAS and the LLM-judges, \texttt{s5\_verifier} prepares data and trains and scores verifiers, \texttt{s6\_annotation} and \texttt{s6\_quick} build the labelling pages, \texttt{s7\_analysis} computes the round 1 results, \texttt{s8\_revise} runs verify-then-revise, \texttt{s9\_selfcheck} runs SelfCheckGPT, \texttt{s10\_dot2} analyses round 2, and \texttt{s11\_ieee\_extra} and \texttt{s12\_ieee\_more} compute the post hoc analyses of this paper. All sampling uses seed 42, and every number in this paper is generated from the stored result files.

\begin{thebibliography}{99}
<<BIBITEMS>>
\end{thebibliography}

\end{document}
"""


def build():
    fig_pipeline(); fig_scores(); fig_labels(); fig_hops(); fig_roc(); fig_threshold(); fig_kappa(); fig_gap(); fig_scatter()
    order = []
    for m in re.finditer(r"\\cite\{([^}]+)\}", TEMPLATE):
        for k in m.group(1).split(","):
            if k not in order:
                order.append(k)
    missing = set(BIB) - set(order)
    assert not missing, missing
    ns = dict(globals())
    ns["BIBITEMS"] = "\n".join(f"\\bibitem{{{k}}} {BIB[k]}" for k in order)
    tex = re.sub(r"<<(.+?)>>", lambda m: str(eval(m.group(1), ns)), TEMPLATE, flags=re.S)
    (IEEE / "main.tex").write_text(tex, encoding="utf-8")
    z = IEEE / "ViKAG-Faith_IEEE_Overleaf.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as a:
        a.write(IEEE / "main.tex", "main.tex")
        for p in sorted((IEEE / "figures").glob("*.pdf")):
            a.write(p, f"figures/{p.name}")
    print(IEEE / "main.tex", len(tex), z.stat().st_size)


if __name__ == "__main__":
    build()
