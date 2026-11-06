"""Extra analyses for the IEEE paper, written to outputs/analysis/ieee_extra.json. results.json is not touched.

Everything here is post hoc: per-hop and per-system breakdowns, ROC curves, threshold sensitivity, thresholds tuned on
human labels with grouped cross-validation, agreement between checkers, and simple two-checker combinations.
"""

import json
from collections import Counter, defaultdict

import numpy as np
from sklearn.metrics import cohen_kappa_score, f1_score, roc_auc_score, roc_curve
from sklearn.model_selection import GroupKFold

from common import OUT, SEED, read_jsonl
from s10_dot2 import GRID, LABELS, decide, human_labels, macro_f1

RES = OUT / "analysis"
res = json.load(open(RES / "results.json", encoding="utf-8"))
d2 = json.load(open(RES / "results_dot2.json", encoding="utf-8"))
pre = json.load(open(OUT / "prelabels.json", encoding="utf-8"))
sample = {r["qid"]: r["split"] for r in read_jsonl(OUT / "sample.jsonl")}
claims = {c["cid"]: c for c in read_jsonl(OUT / "claims.jsonl") if c["qid"] in sample}
usable = [k for k in claims if k in pre and not pre[k]["bad"]]
gold = {k: pre[k]["label"] for k in usable}
test = [k for k in usable if sample[claims[k]["qid"]] == "test"]
dev = [k for k in usable if sample[claims[k]["qid"]] == "dev"]
human = {k: v for k, v in human_labels().items() if k in gold}
hk = [k for k in usable if k in human]
s1 = {r["cid"]: r for r in read_jsonl(OUT / "verifier_scores.jsonl")}
s2 = {r["cid"]: r for r in read_jsonl(OUT / "verifier_scores_dot2.jsonl")}


def score(name):
    return (s1 if name in s1[usable[0]] else s2)


TH = {**res["thresholds"], **d2["thresholds"]}
VERIF = ["zs_v1", "ft_v1", "ft20full_v1", "xzs_v1", "xft_v1", "xft_v3"]
pred = {n: {k: decide(score(n)[k][n]["entail"], score(n)[k][n]["contra"], *TH[n]) for k in usable} for n in VERIF}
for model, tag in (("qwen2.5:3b", "j3"), ("qwen2.5:7b", "j7")):
    pred[tag] = {k: v for j in read_jsonl(OUT / "judges.jsonl") if j["model"] == model for k, v in j["judge"].items() if v and k in gold}
pred["j14"] = {k: v for j in read_jsonl(OUT / "judges_dot2.jsonl") for k, v in j["judge"].items() if v and k in gold}
pred["silver"], pred["human"] = gold, human
out = {}


def catch(p, ks, ref):
    wrong = [k for k in ks if ref[k] != "supported" and k in p]
    right = [k for k in ks if ref[k] == "supported" and k in p]
    return {"caught": sum(p[k] != "supported" for k in wrong), "wrong": len(wrong), "false_alarm": sum(p[k] != "supported" for k in right), "right": len(right)}


def mf(p, ks, ref):
    ks = [k for k in ks if k in p]
    return macro_f1([ref[k] for k in ks], [p[k] for k in ks])


# ---- sample profile by hop and system
hop = defaultdict(lambda: {"claims": 0, "not_supported": 0, "human": 0, "agree": 0})
for k in usable:
    h = hop[str(claims[k]["hop"])]
    h["claims"] += 1
    h["not_supported"] += gold[k] != "supported"
    if k in human:
        h["human"] += 1; h["agree"] += human[k] == gold[k]
out["by_hop"] = {k: dict(v) for k, v in sorted(hop.items())}
sy = defaultdict(lambda: {"human": 0, "agree": 0})
for k in hk:
    s = sy[claims[k]["system"]]; s["human"] += 1; s["agree"] += human[k] == gold[k]
out["agree_by_system"] = {k: dict(v) for k, v in sy.items()}

# ---- detection by hop on all usable claims, silver labels
low, high = [k for k in usable if str(claims[k]["hop"]) in "123"], [k for k in usable if str(claims[k]["hop"]) in "45"]
out["detect_by_hop_group"] = {n: {"1-3": catch(pred[n], low, gold), "4-5": catch(pred[n], high, gold), "f1_1-3": mf(pred[n], low, gold), "f1_4-5": mf(pred[n], high, gold)}
                              for n in ("j7", "j14", "ft_v1", "xft_v1")}

# ---- per-label F1 on human labels
out["human_per_label"] = {}
for n in ("j7", "j14", "j3", "ft_v1", "ft20full_v1", "xft_v1", "zs_v1"):
    ks = [k for k in hk if k in pred[n]]
    v = f1_score([human[k] for k in ks], [pred[n][k] for k in ks], labels=LABELS, average=None, zero_division=0)
    out["human_per_label"][n] = dict(zip(LABELS, map(float, v)))
    out["human_per_label"][n]["catch"] = catch(pred[n], ks, human)

# ---- ROC curves
out["roc"] = {}
for n in ("zs_v1", "ft_v1", "ft20full_v1", "xft_v1", "xft_v3"):
    for tag, ks, ref in (("silver", test, gold), ("human", hk, human)):
        y = [int(ref[k] != "supported") for k in ks]
        sc = [1 - score(n)[k][n]["entail"] for k in ks]
        fpr, tpr, _ = roc_curve(y, sc)
        out["roc"][f"{n}|{tag}"] = {"auc": float(roc_auc_score(y, sc)), "fpr": [round(float(x), 4) for x in fpr], "tpr": [round(float(x), 4) for x in tpr]}
out["roc_points"] = {f"{n}|{tag}": catch(pred[n], ks, ref) for n in ("j7", "j14") for tag, ks, ref in (("silver", test, gold), ("human", hk, human))}

# ---- threshold sensitivity: best possible test score against the score reached with dev thresholds
out["threshold"] = {}
for n in ("ft_v1", "ft20full_v1", "xft_v1"):
    r = score(n)
    grid = {(a, b): macro_f1([gold[k] for k in test], [decide(r[k][n]["entail"], r[k][n]["contra"], a, b) for k in test]) for a in GRID for b in GRID}
    best = max(grid, key=grid.get)
    vals = np.array(list(grid.values()))
    curve = [{"ts": float(a), "silver": macro_f1([gold[k] for k in test], [decide(r[k][n]["entail"], r[k][n]["contra"], a, TH[n][1]) for k in test]),
              "human": macro_f1([human[k] for k in hk], [decide(r[k][n]["entail"], r[k][n]["contra"], a, TH[n][1]) for k in hk])} for a in GRID]
    out["threshold"][n] = {"dev_choice": TH[n], "dev_score": grid[tuple(TH[n])], "test_best": grid[best], "test_best_at": [float(x) for x in best],
                           "p05": float(np.percentile(vals, 5)), "p95": float(np.percentile(vals, 95)), "curve": curve}

# ---- thresholds tuned on human labels, grouped 5-fold cross-validation by question
out["human_tuned"] = {}
groups = np.array([claims[k]["qid"] for k in hk])
for n in ("zs_v1", "ft_v1", "ft20full_v1", "xzs_v1", "xft_v1"):
    r = score(n)
    held = {}
    chosen = []
    for tr, te in GroupKFold(n_splits=5).split(hk, groups=groups):
        ktr, kte = [hk[i] for i in tr], [hk[i] for i in te]
        y = [human[k] for k in ktr]
        t = max(((a, b) for a in GRID for b in GRID), key=lambda t: macro_f1(y, [decide(r[k][n]["entail"], r[k][n]["contra"], *t) for k in ktr]))
        chosen.append([float(x) for x in t])
        held.update({k: decide(r[k][n]["entail"], r[k][n]["contra"], *t) for k in kte})
    y = np.array([human[k] for k in hk]); pa = np.array([held[k] for k in hk]); pb = np.array([pred[n][k] for k in hk])
    rng = np.random.default_rng(SEED)
    d = [macro_f1(y[i], pa[i]) - macro_f1(y[i], pb[i]) for i in (rng.integers(0, len(hk), len(hk)) for _ in range(1000))]
    out["human_tuned"][n] = {"silver_tuned": macro_f1(y, pb), "human_tuned": macro_f1(y, pa), "diff": macro_f1(y, pa) - macro_f1(y, pb),
                             "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))], "catch": catch(held, hk, human), "folds": chosen}
out["human_tuned_ref"] = {"j7": mf(pred["j7"], hk, human), "j7_catch": catch(pred["j7"], hk, human)}

# ---- agreement between checkers on the human-labelled claims
names = ["human", "silver", "j7", "j14", "j3", "ft_v1", "ft20full_v1", "xft_v1"]
kap = {}
for a in names:
    for b in names:
        ks = [k for k in hk if k in pred[a] and k in pred[b]]
        kap[f"{a}|{b}"] = float(cohen_kappa_score([pred[a][k] for k in ks], [pred[b][k] for k in ks], labels=LABELS))
out["kappa"] = {"names": names, "values": kap}

# ---- two-checker combinations on the binary task: is this claim not supported?
out["combo"] = {}
J, X = pred["j7"], pred["xft_v1"]
both = [k for k in usable if k in J and k in X]
rules = {"7B only": lambda k: J[k] != "supported", "XLM-R only": lambda k: X[k] != "supported",
         "either flags": lambda k: J[k] != "supported" or X[k] != "supported", "both flag": lambda k: J[k] != "supported" and X[k] != "supported"}
for name, fn in rules.items():
    row = {}
    for tag, ks, ref in (("silver", [k for k in test if k in both], gold), ("human", [k for k in hk if k in both], human)):
        p = {k: "x" if fn(k) else "supported" for k in ks}
        c = catch(p, ks, ref)
        c["f1_flag"] = float(f1_score([ref[k] != "supported" for k in ks], [fn(k) for k in ks]))
        row[tag] = c
    out["combo"][name] = row
out["claims_per_answer"] = dict(Counter(str(claims[k]["hop"]) for k in usable))
json.dump(out, open(RES / "ieee_extra.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("by_hop", out["by_hop"]); print("system", out["agree_by_system"])
print("detect", json.dumps(out["detect_by_hop_group"])[:700])
print("human_per_label", {k: {a: round(b, 3) if isinstance(b, float) else b for a, b in v.items()} for k, v in out["human_per_label"].items()})
print("thr", {k: {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items() if a != "curve"} for k, v in out["threshold"].items()})
print("tuned", {k: {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items()} for k, v in out["human_tuned"].items()}, out["human_tuned_ref"])
print("kappa", {k: round(v, 2) for k, v in kap.items() if k.split("|")[0] in ("human", "silver", "j7") and k.split("|")[0] < k.split("|")[1]})
print("combo", out["combo"])
print("auc", {k: round(v["auc"], 3) for k, v in out["roc"].items()})
