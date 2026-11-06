"""Second-round analysis: new verifier variants, the 14B judge and the small Qwen verifier with spans.

Same test split, thresholds tuned on the same dev split with the same grid as s7. Writes
outputs/analysis/results_dot2.json and leaves results.json untouched, so first-round numbers do not move.
Silver labels stay the reference on the test split; the human column uses the same 165 blind labels.
"""

import json
import os
import re
from collections import defaultdict

import numpy as np
from scipy.stats import kendalltau, spearmanr
from sklearn.metrics import f1_score, roc_auc_score

from common import OUT, SEED, read_jsonl

ANN = OUT / "annotation"
RES = OUT / "analysis"
LABELS = ["supported", "contradicted", "unsupported"]
GRID = np.round(np.arange(0.1, 0.95, 0.05), 2)
SCORE_FILE = os.environ.get("VIKAG_DOT2_SCORES", "verifier_scores_dot2.jsonl")
JUDGE_FILE = os.environ.get("VIKAG_DOT2_JUDGES", "judges_dot2.jsonl")
SPAN_FILE = os.environ.get("VIKAG_DOT2_SPAN", "judges_span.jsonl")


def macro_f1(y, p):
    return float(f1_score(y, p, labels=LABELS, average="macro", zero_division=0))


def decide(entail, contra, ts, tc):
    return "supported" if entail >= ts else "contradicted" if contra >= tc else "unsupported"


def human_labels():
    ids = json.load(open(ANN / "id_map.json", encoding="utf-8"))
    out = {}
    for name in ("C", "G", "H", "I", "J"):
        raw = json.load(open(ANN / f"vifaith_labels_{name}.json", encoding="utf-8"))["labels"]
        out.update({ids[k]: v["label"] for k, v in raw.items() if v.get("label") and ids.get(k)})
    return out


def table_row(p, keys, gold, human, score=None):
    ks = [k for k in keys["test"] if k in p]
    y, yp = [gold[k] for k in ks], [p[k] for k in ks]
    rng = np.random.default_rng(SEED)
    boots = [macro_f1([y[i] for i in idx], [yp[i] for i in idx]) for idx in (rng.integers(0, len(ks), len(ks)) for _ in range(1000))]
    wrong = [k for k in ks if gold[k] != "supported"]
    right = [k for k in ks if gold[k] == "supported"]
    hs = [k for k in keys["usable"] if k in human and k in p]
    yb = [int(v != "supported") for v in y]
    sb = [1 - score[k] for k in ks] if score else [int(v != "supported") for v in yp]
    return {"n": len(ks), "macro_f1": macro_f1(y, yp), "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
            "auroc_not_supported": float(roc_auc_score(yb, sb)), "caught": sum(p[k] != "supported" for k in wrong), "wrong": len(wrong),
            "false_alarm": sum(p[k] != "supported" for k in right), "right": len(right),
            "n_human": len(hs), "macro_f1_human": macro_f1([human[k] for k in hs], [p[k] for k in hs])}


def paired(a, b, keys, gold, labels=None):
    ref = labels or gold
    pool = keys["usable"] if labels else keys["test"]
    ks = [k for k in pool if k in a and k in b and k in ref]
    y, pa, pb = np.array([ref[k] for k in ks]), np.array([a[k] for k in ks]), np.array([b[k] for k in ks])
    rng = np.random.default_rng(SEED)
    d = [macro_f1(y[i], pa[i]) - macro_f1(y[i], pb[i]) for i in (rng.integers(0, len(ks), len(ks)) for _ in range(1000))]
    return {"n": len(ks), "diff": macro_f1(y, pa) - macro_f1(y, pb), "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
            "p_le_0": float(np.mean(np.array(d) <= 0))}


def main():
    res = json.load(open(RES / "results.json", encoding="utf-8"))
    pre = json.load(open(OUT / "prelabels.json", encoding="utf-8"))
    sample = {r["qid"]: r["split"] for r in read_jsonl(OUT / "sample.jsonl")}
    claims = {c["cid"]: c for c in read_jsonl(OUT / "claims.jsonl") if c["qid"] in sample}
    usable = [k for k in claims if k in pre and not pre[k]["bad"]]
    gold = {k: pre[k]["label"] for k in usable}
    keys = {"usable": usable, "dev": [k for k in usable if sample[claims[k]["qid"]] == "dev"],
            "test": [k for k in usable if sample[claims[k]["qid"]] == "test"]}
    human = human_labels()

    def tune(rows, name):
        y = [gold[k] for k in keys["dev"]]
        best = max(((a, b) for a in GRID for b in GRID),
                   key=lambda t: macro_f1(y, [decide(rows[k][name]["entail"], rows[k][name]["contra"], *t) for k in keys["dev"]]))
        return [float(x) for x in best]

    first = {r["cid"]: r for r in read_jsonl(OUT / "verifier_scores.jsonl")}
    th = res["thresholds"]
    base = {n: {k: decide(first[k][n]["entail"], first[k][n]["contra"], *th[n]) for k in usable} for n in ("zs_v1", "ft_v1")}
    judges7 = {}
    judges = read_jsonl(OUT / "judges.jsonl")
    for j in judges:
        if j["model"] == "qwen2.5:7b":
            judges7.update({k: v for k, v in j["judge"].items() if v and k in gold})

    out = {"methods": {}, "thresholds": {}, "paired_silver": {}, "paired_human": {}}
    new = {}
    path = OUT / SCORE_FILE
    if path.exists():
        rows = {r["cid"]: r for r in read_jsonl(path)}
        names = sorted({n for r in rows.values() for n in r if n != "cid"})
        for n in names:
            if not all(n in rows.get(k, {}) for k in usable):
                print("skipping", n, "- scores missing")
                continue
            t = tune(rows, n)
            out["thresholds"][n] = t
            new["nli_" + n] = {k: decide(rows[k][n]["entail"], rows[k][n]["contra"], *t) for k in usable}
            out["methods"]["nli_" + n] = table_row(new["nli_" + n], keys, gold, human, {k: rows[k][n]["entail"] for k in usable})

    # answer-level reference: silver GGF per answer on the test split, as in s7
    by_answer = defaultdict(list)
    for k in keys["test"]:
        by_answer[(claims[k]["qid"], claims[k]["system"])].append(k)
    ggf = {a: sum(gold[k] == "supported" for k in ks) / len(ks) for a, ks in by_answer.items()}

    def corr(score):
        ks = [a for a in ggf if score.get(a) is not None]
        rho = spearmanr([ggf[a] for a in ks], [score[a] for a in ks]).statistic
        tau = kendalltau([ggf[a] for a in ks], [score[a] for a in ks]).statistic
        return {"n": len(ks), "spearman": float(rho), "kendall": float(tau)}

    path = OUT / JUDGE_FILE
    if path.exists():
        rows = read_jsonl(path)
        p = {k: v for j in rows for k, v in j["judge"].items() if v and k in gold}
        new["judge_14b"] = p
        out["methods"]["judge_14b"] = table_row(p, keys, gold, human)
        out["judge_coverage_14b"] = len(p)
        ragas = {(j["qid"], j["system"]): j["ragas"]["score"] for j in rows}
        out["corr_ragas_14b"] = corr(ragas)
        pa = {(j["qid"], j["system"]): [v == "supported" for k, v in j["judge"].items() if v and k in gold] for j in rows}
        out["corr_judge_14b"] = corr({a: sum(v) / len(v) for a, v in pa.items() if v})

    path = OUT / SPAN_FILE
    if path.exists():
        # same evidence the model saw; case, punctuation and "..." do not count against a copied span
        norm = lambda t: " ".join(re.sub(r"[\W_]+", " ", t.lower()).split())
        pools = {(p["qid"], p["system"]): norm(" ".join(x["text"][:2500] + " " + x["title"] + " " + " ".join(x["facts"]) for x in p["pool"]))
                 for p in read_jsonl(OUT / "pools.jsonl")}
        rows = read_jsonl(path)
        p, found, given = {}, 0, 0
        for j in rows:
            text = pools[(j["qid"], j["system"])]
            for k, v in j["judge"].items():
                if not v or k not in gold:
                    continue
                p[k] = v["label"]
                span = norm(v.get("span", ""))
                if span:
                    given += 1
                    found += f" {span} " in f" {text} "
        new["qwen3b_span"] = p
        out["methods"]["qwen3b_span"] = table_row(p, keys, gold, human)
        out["span"] = {"labelled": len(p), "given": given, "verbatim": found, "rate": found / max(1, len(p))}

    for name, pred in new.items():
        for ref_name, ref in (("nli_ft_v1", base["ft_v1"]), ("nli_zs_v1", base["zs_v1"]), ("judge_7b", judges7)):
            out["paired_silver"][f"{name} - {ref_name}"] = paired(pred, ref, keys, gold)
            out["paired_human"][f"{name} - {ref_name}"] = paired(pred, ref, keys, gold, human)
    if {"nli_ft20_v1", "nli_ft20_v3"} <= new.keys():
        out["paired_silver"]["nli_ft20_v3 - nli_ft20_v1"] = paired(new["nli_ft20_v3"], new["nli_ft20_v1"], keys, gold)
        out["paired_human"]["nli_ft20_v3 - nli_ft20_v1"] = paired(new["nli_ft20_v3"], new["nli_ft20_v1"], keys, gold, human)

    if {"nli_xft_v1", "nli_xzs_v1"} <= new.keys():
        out["paired_silver"]["nli_xft_v1 - nli_xzs_v1"] = paired(new["nli_xft_v1"], new["nli_xzs_v1"], keys, gold)
        out["paired_human"]["nli_xft_v1 - nli_xzs_v1"] = paired(new["nli_xft_v1"], new["nli_xzs_v1"], keys, gold, human)

    # threshold-free check, and how far the choice of grid matters; the wide grid is a sensitivity run on dev, not the headline
    if (OUT / SCORE_FILE).exists():
        def auroc_gap(n, r, ks, ref):
            ks = [k for k in ks if k in ref]
            yb = np.array([int(ref[k] != "supported") for k in ks])
            sa = np.array([1 - rows2[k][n]["entail"] for k in ks])
            sb = np.array([1 - first[k][r]["entail"] for k in ks])
            rng = np.random.default_rng(SEED)
            d = [roc_auc_score(yb[i], sa[i]) - roc_auc_score(yb[i], sb[i]) for i in (rng.integers(0, len(ks), len(ks)) for _ in range(1000)) if 0 < yb[i].sum() < len(i)]
            return {"n": len(ks), "a": float(roc_auc_score(yb, sa)), "b": float(roc_auc_score(yb, sb)), "diff": float(roc_auc_score(yb, sa) - roc_auc_score(yb, sb)),
                    "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]}

        rows2 = {r["cid"]: r for r in read_jsonl(OUT / SCORE_FILE)}
        wide = np.round(np.concatenate([np.arange(0.01, 0.1, 0.01), np.arange(0.1, 0.96, 0.05)]), 2)
        out["auroc_paired"], out["wide_grid"] = {}, {}
        for n in ("ft20_v1", "ft20_v3", "xft_v1", "xft_v3"):
            if n not in out["thresholds"]:
                continue
            out["auroc_paired"][f"{n} - ft_v1 silver"] = auroc_gap(n, "ft_v1", keys["test"], gold)
            out["auroc_paired"][f"{n} - ft_v1 human"] = auroc_gap(n, "ft_v1", keys["usable"], human)
            y = [gold[k] for k in keys["dev"]]
            t = max(((a, b) for a in wide for b in wide), key=lambda t: macro_f1(y, [decide(rows2[k][n]["entail"], rows2[k][n]["contra"], *t) for k in keys["dev"]]))
            p = {k: decide(rows2[k][n]["entail"], rows2[k][n]["contra"], *t) for k in usable}
            hs = [k for k in usable if k in human]
            out["wide_grid"][n] = {"thresholds": [float(x) for x in t], "macro_f1": macro_f1([gold[k] for k in keys["test"]], [p[k] for k in keys["test"]]),
                                   "macro_f1_human": macro_f1([human[k] for k in hs], [p[k] for k in hs])}
    json.dump(out, open(RES / "results_dot2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("method                 macroF1   CI95            AUROC  caught  falseAl  human")
    for n, r in out["methods"].items():
        print(f"{n:22s} {r['macro_f1']:.3f}  {r['ci95'][0]:.2f}-{r['ci95'][1]:.2f}  {r['auroc_not_supported']:.3f}  "
              f"{r['caught']}/{r['wrong']}  {r['false_alarm']}/{r['right']}  {r['macro_f1_human']:.3f} ({r['n_human']})")
    for k in ("corr_ragas_14b", "corr_judge_14b", "span", "judge_coverage_14b", "auroc_paired", "wide_grid"):
        if k in out:
            print(k, out[k])
    print("baseline: judge_7b", round(res["claim_level"]["judge_7b"]["macro_f1"], 3), "ft_v1", round(res["claim_level"]["nli_ft_v1"]["macro_f1"], 3))


if __name__ == "__main__":
    main()
