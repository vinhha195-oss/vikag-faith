"""Step 7: meta-evaluation of faithfulness metrics against the gold claim labels.

Gold = HUMAN labels from the two blind passes (C: 60-claim audit, F: ~100 more claims) once
vifaith_labels_F.json exists; Claude's labels then become one more method ("claude_silver"). Without D,
gold = Claude's labels, reported as SILVER. VIKAG_GOLD=silver forces the silver setting.
Writes outputs/analysis/results.json.
"""

import json
import os
import random
from collections import Counter, defaultdict

import numpy as np
from scipy.stats import kendalltau, spearmanr, wilcoxon
from sklearn.metrics import accuracy_score, cohen_kappa_score, confusion_matrix, f1_score, roc_auc_score
from vihermes.evaluation import token_f1
from vihermes.retrieval import tokens

from common import OUT, SEED, read_jsonl
from rules import check

LABELS = ["supported", "contradicted", "unsupported"]
ANN = OUT / "annotation"
RES = OUT / "analysis"
RES.mkdir(exist_ok=True)


def load_human(name):
    path = ANN / f"vifaith_labels_{name}.json"
    if not path.exists():
        return None
    ids = json.load(open(ANN / "id_map.json", encoding="utf-8"))
    raw = json.load(open(path, encoding="utf-8"))["labels"]
    # A claim marked malformed may carry no label; keep it so it is excluded rather than missing.
    return {ids[k]: v for k, v in raw.items() if (v.get("label") or v.get("bad")) and ids.get(k)}


def gold_labels():
    """Human gold = blind passes C + F (never pass A: suggestions confirmed without a single change in
    ~10 minutes). Falls back to Claude's silver labels while pass F is missing."""
    pre = json.load(open(OUT / "prelabels.json", encoding="utf-8"))
    # Pass D is excluded (its export was not produced through the annotation page) and so is pass E,
    # which re-typed D. Pass F is the blind relabel of ~100 claims.
    d = load_human("F")
    if d and os.environ.get("VIKAG_GOLD", "human") == "human":
        human = {**(load_human("C") or {}), **d}
        return {k: {"label": v["label"], "bad": bool(v.get("bad"))} for k, v in human.items()}, "human", pre, None
    return {k: {"label": v["label"], "bad": v["bad"]} for k, v in pre.items()}, "silver", pre, None


def decide(entail, contra, ts, tc):
    if entail >= ts:
        return "supported"
    if contra >= tc:
        return "contradicted"
    return "unsupported"


def apply_rule(label, claim, evidence):
    r = check(claim, evidence)
    if r == "contradicted":
        return "contradicted"
    if r == "unsupported" and label == "supported":
        return "unsupported"
    return label


def macro_f1(y, p):
    return f1_score(y, p, labels=LABELS, average="macro", zero_division=0)


def bootstrap(y, p, n=1000):
    rng = np.random.default_rng(SEED)
    y, p = np.array(y), np.array(p)
    vals = [macro_f1(y[i], p[i]) for i in (rng.integers(0, len(y), len(y)) for _ in range(n))]
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def main():
    sample = {r["qid"]: r["split"] for r in read_jsonl(OUT / "sample.jsonl")}
    claims = {c["cid"]: c for c in read_jsonl(OUT / "claims.jsonl") if c["qid"] in sample}
    pools = {(p["qid"], p["system"]): p["pool"] for p in read_jsonl(OUT / "pools.jsonl")}
    answers = read_jsonl(OUT / "answers.jsonl")
    judges = read_jsonl(OUT / "judges.jsonl")
    scores = {r["cid"]: r for r in read_jsonl(OUT / "verifier_scores.jsonl")}
    # SelfCheckGPT (s9) scores sit beside the verifier's, under the variant name "selfcheck".
    if (OUT / "selfcheck_scores.jsonl").exists():
        for r in read_jsonl(OUT / "selfcheck_scores.jsonl"):
            if r["cid"] in scores:
                scores[r["cid"]]["selfcheck"] = {"entail": r["entail"], "contra": r["contra"]}
    gold, gold_kind, pre, reviewed = gold_labels()

    def evidence(c):
        return [f"{p['title']} {' '.join(p['facts'])} {p['text']}" for p in pools[(c["qid"], c["system"])]]

    unlabeled = [k for k in claims if k not in gold]
    usable = [k for k in claims if k in gold and not gold[k]["bad"]]
    split = {k: sample[claims[k]["qid"]] for k in usable}
    dev = [k for k in usable if split[k] == "dev"]
    test = [k for k in usable if split[k] == "test"]

    # ---- claim-level predictions per method ----
    preds = {}
    for model in ("qwen2.5:3b", "qwen2.5:7b"):
        tag = "judge_" + model.split(":")[1]
        preds[tag] = {}
        for j in judges:
            if j["model"] == model:
                preds[tag].update({k: v for k, v in j["judge"].items() if v})
    thresholds = {}
    grid = np.round(np.arange(0.1, 0.95, 0.05), 2)
    for variant in ("zs_v1", "zs_v2", "ft_v1", "ft_v2", "nosynth_v1", "nosynth_v2", "selfcheck"):
        if not all(variant in scores[k] for k in usable):
            if any(variant in scores[k] for k in usable):
                print("skipping", variant, "- scores missing for some claims")
            continue
        best = max(((ts, tc) for ts in grid for tc in grid),
                   key=lambda t: macro_f1([gold[k]["label"] for k in dev],
                                          [decide(scores[k][variant]["entail"], scores[k][variant]["contra"], *t) for k in dev]))
        thresholds[variant] = [float(x) for x in best]
        base = {k: decide(scores[k][variant]["entail"], scores[k][variant]["contra"], *best) for k in usable}
        preds["nli_" + variant] = base
        if variant != "selfcheck":  # SelfCheckGPT is reference-free; the rule needs the evidence
            preds["nli_" + variant + "+rule"] = {k: apply_rule(v, claims[k]["claim"], evidence(claims[k])) for k, v in base.items()}
    if gold_kind == "human":  # Claude's labels are now one more automatic method
        preds["claude_silver"] = {k: pre[k]["label"] for k in usable if not pre[k]["bad"]}
    preds["rule_only"] = {k: (check(claims[k]["claim"], evidence(claims[k])) or "supported") for k in usable}
    preds["majority_supported"] = {k: "supported" for k in usable}

    same_ft = all(scores[k].get("ft_v1") == scores[k].get("zs_v1") for k in usable)
    same_nosynth = all(scores[k].get("nosynth_v1") == scores[k].get("zs_v1") for k in usable) \
        if "nli_nosynth_v1" in preds else None

    claim_table = {}
    for name, p in preds.items():
        ks = [k for k in test if k in p]
        y = [gold[k]["label"] for k in ks]
        yp = [p[k] for k in ks]
        row = {"n": len(ks), "coverage": len(ks) / len(test), "acc": accuracy_score(y, yp),
               "macro_f1": macro_f1(y, yp), "ci95": bootstrap(y, yp),
               "f1_per_class": dict(zip(LABELS, f1_score(y, yp, labels=LABELS, average=None, zero_division=0).tolist()))}
        # Detecting "not supported" claims: NLI uses 1 - entail as a score, others their hard label.
        yb = [int(v != "supported") for v in y]
        if name.startswith("nli_") and "+rule" not in name:
            sb = [1 - scores[k][name[4:]]["entail"] for k in ks]
        else:
            sb = [int(v != "supported") for v in yp]
        row["auroc_not_supported"] = roc_auc_score(yb, sb) if 0 < sum(yb) < len(yb) else None
        claim_table[name] = row

    # Paired bootstrap of macro-F1 differences on the claims both methods labelled.
    def paired(a, b, n=1000):
        ks = [k for k in test if k in preds[a] and k in preds[b]]
        y = np.array([gold[k]["label"] for k in ks])
        pa, pb = np.array([preds[a][k] for k in ks]), np.array([preds[b][k] for k in ks])
        rng = np.random.default_rng(SEED)
        d = [macro_f1(y[i], pa[i]) - macro_f1(y[i], pb[i]) for i in (rng.integers(0, len(ks), len(ks)) for _ in range(n))]
        return {"n": len(ks), "diff": macro_f1(y, pa) - macro_f1(y, pb),
                "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))], "p_le_0": float(np.mean(np.array(d) <= 0))}

    comparisons = {f"{a} - {b}": paired(a, b) for a, b in (
        ("nli_ft_v1", "judge_7b"), ("nli_ft_v1", "nli_zs_v1"), ("nli_ft_v1", "nli_nosynth_v1"),
        ("nli_nosynth_v1", "nli_zs_v1"), ("nli_ft_v1", "nli_ft_v2"), ("judge_7b", "nli_selfcheck"))
        if a in preds and b in preds}

    # ---- answer-level: GGF / CR / UR ----
    by_answer = defaultdict(list)
    for k in usable:
        by_answer[(claims[k]["qid"], claims[k]["system"])].append(k)

    def rates(ks, lab):
        c = Counter(lab[k] for k in ks)
        n = len(ks)
        return c["supported"] / n, c["contradicted"] / n, c["unsupported"] / n

    human = {a: rates(ks, {k: gold[k]["label"] for k in ks}) for a, ks in by_answer.items()}
    test_answers = [a for a in by_answer if sample[a[0]] == "test"]
    corr = {}
    for name, p in preds.items():
        if name == "majority_supported":
            continue
        xs, ys = [], []
        for a in test_answers:
            ks = [k for k in by_answer[a] if k in p]
            if ks:
                xs.append(rates(ks, p)[0])
                ys.append(human[a][0])
        corr[name] = {"n": len(xs), "spearman": spearmanr(xs, ys).statistic, "kendall": kendalltau(xs, ys).statistic}
    for j_model in ("qwen2.5:3b", "qwen2.5:7b"):
        xs, ys = [], []
        for j in judges:
            a = (j["qid"], j["system"])
            if j["model"] == j_model and a in test_answers and j["ragas"]["score"] is not None:
                xs.append(j["ragas"]["score"])
                ys.append(human[a][0])
        corr["ragas_" + j_model.split(":")[1]] = {"n": len(xs), "spearman": spearmanr(xs, ys).statistic,
                                                   "kendall": kendalltau(xs, ys).statistic}

    # ---- system comparison (all 80 sampled answers, human/silver gold) ----
    systems = {}
    for s in ("naive", "graph"):
        rs = [human[a] for a in human if a[1] == s]
        systems[s] = {"answers": len(rs), "GGF": float(np.mean([r[0] for r in rs])),
                      "CR": float(np.mean([r[1] for r in rs])), "UR": float(np.mean([r[2] for r in rs]))}
    paired = [(human[(q, "naive")][0], human[(q, "graph")][0]) for q in sample
              if (q, "naive") in human and (q, "graph") in human]
    systems["wilcoxon_GGF_p"] = float(wilcoxon([x for x, _ in paired], [y for _, y in paired]).pvalue) \
        if any(x != y for x, y in paired) else None
    hop = defaultdict(lambda: defaultdict(list))
    for (q, s), r in human.items():
        hop[s][claims[by_answer[(q, s)][0]]["hop"]].append(r)
    systems["by_hop"] = {s: {h: {"n": len(v), "GGF": float(np.mean([x[0] for x in v])),
                                 "CR": float(np.mean([x[1] for x in v]))} for h, v in sorted(d.items())}
                         for s, d in hop.items()}

    # ---- RQ3: verify-then-revise (s8). Before/after are both scored by the 7B claim judge, the
    # same judge that flagged the claims, so the gain is an upper bound; token F1 is independent. ----
    revise = None
    if (OUT / "revise.jsonl").exists():
        ans = {(a["qid"], a["system"]): a for a in answers}
        j7 = {(j["qid"], j["system"]): j["judge"] for j in judges if j["model"] == "qwen2.5:7b"}

        def judged(labels):
            ls = [x for x in labels if x]
            if not ls:
                return None
            c = Counter(ls)
            return c["supported"] / len(ls), c["contradicted"] / len(ls), c["unsupported"] / len(ls)

        def em(pred, ref):
            return float(tokens(pred) == tokens(ref))

        def recall(pred, ref):  # share of the reference's tokens the answer keeps
            p, r = Counter(tokens(pred)), Counter(tokens(ref))
            return sum((p & r).values()) / max(sum(r.values()), 1)

        rev_rows = read_jsonl(OUT / "revise.jsonl")

        def build(max_rounds):
            """One row per answer, stopping the revise loop after `max_rounds` rounds (ablation on rounds)."""
            rows = []
            for r in rev_rows:
                a, rounds = (r["qid"], r["system"]), r["rounds"][:max_rounds]
                before = judged(list(j7.get(a, {}).values()))
                last = rounds[-1] if rounds else None
                after = judged(last["labels"]) if last else before
                text, ref = (last["answer"] if last else ans[a]["answer"]), ans[a]["gold_answer"]
                rows.append({"a": a, "revised": bool(rounds), "rounds": len(rounds), "before": before, "after": after,
                             "f1_before": token_f1(ans[a]["answer"], ref), "f1_after": token_f1(text, ref),
                             "em_before": em(ans[a]["answer"], ref), "em_after": em(text, ref),
                             "recall_before": recall(ans[a]["answer"], ref), "recall_after": recall(text, ref),
                             "abstain_after": not (last["claims"] if last else True),
                             "claims_before": len(j7.get(a, {})), "claims_after": len(last["claims"]) if last else len(j7.get(a, {}))})
            return rows

        rows = build(2)

        def summary(rs):
            ok = [x for x in rs if x["before"] and x["after"]]
            out = {"answers": len(rs), "revised": sum(x["revised"] for x in rs),
                   "mean_rounds_revised": float(np.mean([x["rounds"] for x in rs if x["revised"]])) if any(x["revised"] for x in rs) else 0.0,
                   "abstained_after": sum(x["abstain_after"] for x in rs), "scored": len(ok)}
            for i, m in enumerate(("GGF", "CR", "UR")):
                out[m + "_before"] = float(np.mean([x["before"][i] for x in ok]))
                out[m + "_after"] = float(np.mean([x["after"][i] for x in ok]))
            for m in ("f1", "em", "recall"):
                out[f"answer_{m}_before"] = float(np.mean([x[m + "_before"] for x in rs]))
                out[f"answer_{m}_after"] = float(np.mean([x[m + "_after"] for x in rs]))
            out["claims_before"] = float(np.mean([x["claims_before"] for x in rs]))
            out["claims_after"] = float(np.mean([x["claims_after"] for x in rs]))
            diff = [(x["before"][0], x["after"][0]) for x in ok if x["revised"]]
            out["wilcoxon_GGF_p"] = float(wilcoxon([b for b, _ in diff], [c for _, c in diff]).pvalue) \
                if any(b != c for b, c in diff) else None
            fd = [(x["f1_before"], x["f1_after"]) for x in rs if x["revised"]]
            out["wilcoxon_F1_p"] = float(wilcoxon([b for b, _ in fd], [c for _, c in fd]).pvalue) \
                if any(b != c for b, c in fd) else None
            return out

        revise = {"all": summary(rows), **{s: summary([x for x in rows if x["a"][1] == s]) for s in ("naive", "graph")}}
        # Ablation on the number of rounds: stop after round 1 vs. allow round 2, all answers, and the
        # answers that actually needed a second round (still flagged after round 1).
        one = build(1)
        two_ids = sorted({r2["a"] for r2 in rows if r2["rounds"] == 2})
        revise["by_max_rounds"] = {"1": summary(one), "2": revise["all"],
                                   "needed_round_2": {"1": summary([x for x in one if x["a"] in two_ids]),
                                                      "2": summary([x for x in rows if x["a"] in two_ids])}}
        r1, r2 = {x["a"]: x for x in one if x["a"] in two_ids}, {x["a"]: x for x in rows if x["a"] in two_ids}
        both = [a for a in two_ids if r1[a]["after"] and r2[a]["after"]]
        pair = lambda xs, ys: float(wilcoxon(xs, ys).pvalue) if any(p != q for p, q in zip(xs, ys)) else None  # noqa: E731
        revise["by_max_rounds"]["round2_vs_round1"] = {
            "n": len(both),
            "GGF_r1": float(np.mean([r1[a]["after"][0] for a in both])), "GGF_r2": float(np.mean([r2[a]["after"][0] for a in both])),
            "CR_r1": float(np.mean([r1[a]["after"][1] for a in both])), "CR_r2": float(np.mean([r2[a]["after"][1] for a in both])),
            "F1_r1": float(np.mean([r1[a]["f1_after"] for a in two_ids])), "F1_r2": float(np.mean([r2[a]["f1_after"] for a in two_ids])),
            "recall_r1": float(np.mean([r1[a]["recall_after"] for a in two_ids])), "recall_r2": float(np.mean([r2[a]["recall_after"] for a in two_ids])),
            "wilcoxon_GGF_p": pair([r1[a]["after"][0] for a in both], [r2[a]["after"][0] for a in both]),
            "wilcoxon_F1_p": pair([r1[a]["f1_after"] for a in two_ids], [r2[a]["f1_after"] for a in two_ids])}

    # ---- QA quality on all 100 questions (context for the faithfulness numbers) ----
    qa = {}
    for s in ("naive", "graph"):
        xs = [a for a in answers if a["system"] == s]
        qa[s] = {"questions": len(xs),
                 "answer_f1": float(np.mean([token_f1(a["answer"], a["gold_answer"]) for a in xs])),
                 "gold_passage_recall": float(np.mean([len({p["id"] for p in a["retrieved"]} & set(a["gold_ids"])) / len(a["gold_ids"]) for a in xs])),
                 "abstain_rate": float(np.mean(["không tìm thấy" in a["answer"].lower() or "không có thông tin" in a["answer"].lower() for a in xs]))}

    # ---- agreement ----
    agreement = {}
    if reviewed:
        ks = sorted(reviewed)
        agreement["claude_vs_human_kappa"] = cohen_kappa_score([pre[k]["label"] for k in ks], [gold[k]["label"] for k in ks])
        agreement["claude_vs_human_acc"] = float(np.mean([pre[k]["label"] == gold[k]["label"] for k in ks]))
        agreement["n"] = len(ks)
        agreement["changed"] = Counter(f"{pre[k]['label']}->{gold[k]['label']}" for k in ks if pre[k]["label"] != gold[k]["label"])
    def audit_stats(audit):
        """Claude vs human on one blind sample, and metric ranks against both label sets."""
        ks = sorted(k for k, v in audit.items() if not v.get("bad") and not gold[k]["bad"])
        yc, yh = [pre[k]["label"] for k in ks], [audit[k]["label"] for k in ks]
        cm = confusion_matrix(yc, yh, labels=LABELS)
        res = {
            "n": len(ks), "n_input": len(audit), "acc": float(np.mean([a == b for a, b in zip(yc, yh)])),
            "kappa": float(cohen_kappa_score(yc, yh)),
            "confusion_claude_rows_human_cols": cm.tolist(),
            "human_distribution": Counter(yh), "claude_distribution": Counter(yc),
            # Per Claude label: share the human agreed with (the sample is stratified by Claude label).
            "agree_by_claude_label": {lab: float(cm[i, i] / cm[i].sum()) for i, lab in enumerate(LABELS) if cm[i].sum()},
        }
        # Sensitivity: does the ranking of metrics change when the audited claims are scored
        # against the human labels instead of Claude's?
        sens = {}
        for name, p in preds.items():
            kk = [k for k in ks if k in p]
            sens[name] = {"n": len(kk),
                          "macro_f1_vs_human": macro_f1([audit[k]["label"] for k in kk], [p[k] for k in kk]),
                          "macro_f1_vs_claude": macro_f1([pre[k]["label"] for k in kk], [p[k] for k in kk]),
                          "acc_vs_human": accuracy_score([audit[k]["label"] for k in kk], [p[k] for k in kk])}
        names = [n for n in sens if not (n.startswith("nli_ft") and same_ft)]
        res["sensitivity"] = sens
        res["rank_spearman"] = float(spearmanr([sens[n]["macro_f1_vs_human"] for n in names],
                                                              [sens[n]["macro_f1_vs_claude"] for n in names]).statistic)
        # Human-label GGF per system on the audited claims only.
        res["by_system"] = {
            s: {"n": sum(1 for k in ks if claims[k]["system"] == s),
                "human_supported": float(np.mean([audit[k]["label"] == "supported" for k in ks if claims[k]["system"] == s])),
                "claude_supported": float(np.mean([pre[k]["label"] == "supported" for k in ks if claims[k]["system"] == s]))}
            for s in ("naive", "graph")}
        return res

    audit = load_human("C")
    if audit:
        agreement["audit"] = audit_stats(audit)
    # Quick passes G, H, ...: 30 random claims each, labelled from short excerpts (s6_quick.py). Reported
    # together and pooled with C; pass C alone stays the main audit (its protocol, full passages, is the reference).
    quick, quick_passes = {}, []
    for name in "GHIJ":
        lab = load_human(name)
        if lab:
            quick.update(lab)
            quick_passes.append(name)
    agreement["quick_passes"] = quick_passes
    if quick:
        agreement["audit_G"] = audit_stats(quick)
        if audit:
            agreement["audit_CG"] = audit_stats({**audit, **quick})
    pass_a = load_human("A")
    if pass_a:
        changed = sum(1 for k, v in pass_a.items() if v["label"] != pre[k]["label"])
        agreement["pass_A_excluded"] = {"confirmed": len(pass_a), "labels_changed": changed}
    b = load_human("B")
    if b:
        ks = [k for k in b if k in gold]
        agreement["A_vs_B_kappa"] = cohen_kappa_score([gold[k]["label"] for k in ks], [b[k]["label"] for k in ks])
        agreement["A_vs_B_n"] = len(ks)

    results = {
        "gold": gold_kind, "claims_total": len(claims), "claims_unlabeled": len(unlabeled),
        "claims_bad": len(claims) - len(unlabeled) - len(usable),
        "claims_dev": len(dev), "claims_test": len(test),
        "gold_distribution": Counter(gold[k]["label"] for k in usable),
        "thresholds": thresholds, "ft_identical_to_zs": same_ft, "nosynth_identical_to_zs": same_nosynth,
        "revise": revise,
        "claim_level": claim_table, "comparisons": comparisons, "answer_level_correlation": corr,
        "systems": systems, "qa": qa, "agreement": agreement,
        "judge_coverage": {m: sum(1 for j in judges if j["model"] == m for v in j["judge"].values() if v) for m in ("qwen2.5:3b", "qwen2.5:7b")},
    }
    json.dump(results, open(RES / "results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: results[k] for k in ("gold", "claims_test", "gold_distribution", "thresholds", "ft_identical_to_zs")}, ensure_ascii=False, default=float))
    for n, r in sorted(claim_table.items(), key=lambda x: -x[1]["macro_f1"]):
        print(f"{n:22s} macroF1={r['macro_f1']:.3f} [{r['ci95'][0]:.2f},{r['ci95'][1]:.2f}] acc={r['acc']:.3f} n={r['n']}")
    for n, r in corr.items():
        print(f"{n:22s} spearman={r['spearman']:.3f} kendall={r['kendall']:.3f} n={r['n']}")
    print(json.dumps(systems, ensure_ascii=False, default=float)[:600])
    print(json.dumps(qa, ensure_ascii=False))
    print(json.dumps(agreement, ensure_ascii=False, default=str))


if __name__ == "__main__":
    random.seed(SEED)
    main()
