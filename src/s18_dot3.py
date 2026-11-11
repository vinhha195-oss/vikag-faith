"""Third-round analysis: XLM-R fine-tuned with error-shaped hard negatives (xhard), against XLM-R fine-tuned on the
second-round data (xft), the round 1 fine-tuned mDeBERTa (ft_v1) and the 7B judge. Same dev-tuned thresholds and
statistics as s10. Writes outputs/analysis/results_dot3.json; earlier result files are not touched.
"""

import json

import numpy as np
from sklearn.metrics import roc_auc_score

from common import OUT, SEED, read_jsonl
from s10_dot2 import GRID, decide, macro_f1, paired, table_row
from s11_ieee_extra import TH, dev, gold, hk, human, pred, score, test, usable

S3 = {r["cid"]: r for r in read_jsonl(OUT / "verifier_scores_dot3.jsonl")}
keys = {"usable": usable, "dev": dev, "test": test}
out = {"methods": {}, "thresholds": {}, "paired_silver": {}, "paired_human": {}, "auroc_paired": {}}
new = {}
for n in ("xhard_v1", "xhard_v3"):
    y = [gold[k] for k in dev]
    t = max(((a, b) for a in GRID for b in GRID), key=lambda t: macro_f1(y, [decide(S3[k][n]["entail"], S3[k][n]["contra"], *t) for k in dev]))
    out["thresholds"][n] = [float(x) for x in t]
    new[n] = {k: decide(S3[k][n]["entail"], S3[k][n]["contra"], *t) for k in usable}
    out["methods"][n] = table_row(new[n], keys, gold, human, {k: S3[k][n]["entail"] for k in usable})
refs = {"xft_v1": pred["xft_v1"], "ft_v1": pred["ft_v1"], "judge_7b": pred["j7"]}
for n, p in new.items():
    for r, q in refs.items():
        out["paired_silver"][f"{n} - {r}"] = paired(p, q, keys, gold)
        out["paired_human"][f"{n} - {r}"] = paired(p, q, keys, gold, human)


def auroc_gap(a, b, ks, ref):
    yb = np.array([int(ref[k] != "supported") for k in ks])
    sa = np.array([1 - S3[k][a]["entail"] for k in ks]); sb = np.array([1 - score(b)[k][b]["entail"] for k in ks])
    rng = np.random.default_rng(SEED)
    d = [roc_auc_score(yb[i], sa[i]) - roc_auc_score(yb[i], sb[i]) for i in (rng.integers(0, len(ks), len(ks)) for _ in range(1000)) if 0 < yb[i].sum() < len(i)]
    return {"a": float(roc_auc_score(yb, sa)), "b": float(roc_auc_score(yb, sb)), "diff": float(roc_auc_score(yb, sa) - roc_auc_score(yb, sb)),
            "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]}


for a, b in (("xhard_v1", "xft_v1"), ("xhard_v3", "xft_v3")):
    out["auroc_paired"][f"{a} - {b} silver"] = auroc_gap(a, b, test, gold)
    out["auroc_paired"][f"{a} - {b} human"] = auroc_gap(a, b, hk, human)
out["hard_dev"] = json.load(open(OUT / "logs" / "dot3_hard_dev.json", encoding="utf-8"))
json.dump(out, open(OUT / "analysis" / "results_dot3.json", "w", encoding="utf-8"), indent=1)

for n, r in out["methods"].items():
    print(f"{n} silver {r['macro_f1']:.3f} {r['ci95'][0]:.2f}-{r['ci95'][1]:.2f} auroc {r['auroc_not_supported']:.3f} caught {r['caught']}/{r['wrong']} fa {r['false_alarm']}/{r['right']} human {r['macro_f1_human']:.3f}  th {out['thresholds'][n]}")
for g in ("paired_silver", "paired_human"):
    for k, v in out[g].items():
        print(g[7:], k, round(v["diff"], 3), [round(x, 2) for x in v["ci95"]])
for k, v in out["auroc_paired"].items():
    print(k, round(v["a"], 3), round(v["b"], 3), [round(x, 3) for x in v["ci95"]])
