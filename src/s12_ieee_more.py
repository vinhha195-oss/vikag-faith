"""More post hoc numbers for the IEEE paper, added to outputs/analysis/ieee_extra.json under the key "more"."""

import json
from collections import Counter, defaultdict
from statistics import mean

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import confusion_matrix

from common import OUT, read_jsonl
from s11_ieee_extra import LABELS, claims, gold, hk, human, macro_f1, out, pre, pred, test, usable

P = OUT / "analysis" / "ieee_extra.json"
more = {}

# ---- per-system scores
more["by_system"] = {}
for n in ("j7", "j14", "ft_v1", "ft20full_v1", "xft_v1"):
    row = {}
    for sy in ("naive", "graph"):
        ks = [k for k in test if claims[k]["system"] == sy and k in pred[n]]
        hs = [k for k in hk if claims[k]["system"] == sy and k in pred[n]]
        row[sy] = {"silver": macro_f1([gold[k] for k in ks], [pred[n][k] for k in ks]), "n": len(ks), "human": macro_f1([human[k] for k in hs], [pred[n][k] for k in hs]), "n_human": len(hs)}
    more["by_system"][n] = row

# ---- confusion of checkers against human labels
more["confusion_human"] = {}
for n in ("j7", "xft_v1"):
    ks = [k for k in hk if k in pred[n]]
    more["confusion_human"][n] = confusion_matrix([human[k] for k in ks], [pred[n][k] for k in ks], labels=LABELS).tolist()

# ---- answer-level scatter
ggf = defaultdict(list)
for k in test:
    ggf[(claims[k]["qid"], claims[k]["system"])].append(gold[k] == "supported")
ggf = {a: sum(v) / len(v) for a, v in ggf.items()}
r7 = {(j["qid"], j["system"]): j["ragas"]["score"] for j in read_jsonl(OUT / "judges.jsonl") if j["model"] == "qwen2.5:7b"}
r14 = {(j["qid"], j["system"]): j["ragas"]["score"] for j in read_jsonl(OUT / "judges_dot2.jsonl")}
more["scatter"] = {t: [[ggf[a], r[a]] for a in ggf if r.get(a) is not None] for t, r in (("7b", r7), ("14b", r14))}
common = [a for a in ggf if r7.get(a) is not None and r14.get(a) is not None]
more["ragas_vs_ragas"] = {"n": len(common), "rho": float(spearmanr([r7[a] for a in common], [r14[a] for a in common]).statistic)}

# ---- claim extraction quality
rows = list(claims.values())
per = Counter((c["qid"], c["system"]) for c in rows)
hop = defaultdict(list)
for (q, s), v in per.items():
    hop[str(next(c["hop"] for c in rows if c["qid"] == q))].append(v)
more["extraction"] = {"answers": len(per), "mean_claims": mean(per.values()), "max_claims": max(per.values()), "by_hop": {h: mean(v) for h, v in sorted(hop.items())},
                      "bad": sum(1 for c in rows if pre.get(c["cid"], {}).get("bad")), "multi_value": sum(1 for c in rows if str(c.get("multi_value")) == "True"),
                      "bad_notes": [pre[c["cid"]].get("note", "") for c in rows if pre.get(c["cid"], {}).get("bad")]}

# ---- disagreement between Claude and the human
dis = [k for k in hk if human[k] != gold[k]]
more["disagree"] = {"n": len(dis), "pairs": {f"{a}>{b}": v for (a, b), v in Counter((gold[k], human[k]) for k in dis).items()},
                    "j7_with_human": sum(pred["j7"].get(k) == human[k] for k in dis), "j7_with_silver": sum(pred["j7"].get(k) == gold[k] for k in dis)}
json.dump({**json.load(open(P, encoding="utf-8")), "more": more}, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: v for k, v in more.items() if k not in ("scatter", "extraction")})
print({k: v for k, v in more["extraction"].items() if k != "bad_notes"}, more["extraction"]["bad_notes"][:8])
print("rev", list(read_jsonl(OUT / "revise.jsonl")[0].keys()))
for k in sorted(dis, key=lambda k: (gold[k], human[k])):
    note = pre[k].get("note", "") or pre[k].get("reason", "")
    if note and len(claims[k]["claim"]) < 130:
        print(gold[k][:4], human[k][:4], str(pred["j7"].get(k))[:4], "|", claims[k]["claim"], "|", note[:150])
