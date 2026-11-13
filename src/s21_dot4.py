"""Round-4 analysis: the 32B judge (Kaggle), the ViEduReg pilot, and later the extra systems and the Verify operator.
Writes outputs/analysis/results_dot4.json; earlier result files are not touched. Parts whose input file is missing
are skipped, so this can run as results arrive.
"""

import json
from collections import defaultdict

import numpy as np
from scipy.stats import kendalltau, spearmanr

from common import OUT, read_jsonl
from s10_dot2 import LABELS, macro_f1, paired, table_row
from s11_ieee_extra import dev, gold, hk, human, pred, test, usable

RES = OUT / "analysis" / "results_dot4.json"
out = json.load(open(RES, encoding="utf-8")) if RES.exists() else {}
keys = {"usable": usable, "dev": dev, "test": test}

# ---------- judge 32B
p32 = OUT / "judges_32b.jsonl"
if p32.exists():
    rows = read_jsonl(p32)
    j32 = {k: v for r in rows for k, v in r["judge"].items() if v and k in gold}
    res = {"method": table_row(j32, keys, gold, human), "coverage": len(j32)}
    for name, ref in (("judge_7b", pred["j7"]), ("judge_14b", pred["j14"]), ("nli_ft_v1", pred["ft_v1"])):
        res[f"silver - {name}"] = paired(j32, ref, keys, gold)
        res[f"human - {name}"] = paired(j32, ref, keys, gold, human)
    by_answer = defaultdict(list)
    for k in test:
        c = k.split("|")
        by_answer[(c[0], c[1])].append(gold[k] == "supported")
    ggf = {a: sum(v) / len(v) for a, v in by_answer.items()}

    def corr(score):
        ks = [a for a in ggf if score.get(a) is not None]
        return {"n": len(ks), "spearman": float(spearmanr([ggf[a] for a in ks], [score[a] for a in ks]).statistic),
                "kendall": float(kendalltau([ggf[a] for a in ks], [score[a] for a in ks]).statistic)}

    res["corr_ragas_32b"] = corr({(r["qid"], r["system"]): r["ragas"]["score"] for r in rows})
    per = defaultdict(list)
    for k, v in j32.items():
        c = k.split("|"); per[(c[0], c[1])].append(v == "supported")
    res["corr_judge_32b"] = corr({a: sum(v) / len(v) for a, v in per.items() if v})
    out["judge_32b"] = res

# ---------- ViEduReg pilot
pe, pl = OUT / "dot4_edu.jsonl", OUT / "viedureg" / "silver_labels.json"
if pe.exists() and pl.exists():
    rows, lab = read_jsonl(pe), json.load(open(pl, encoding="utf-8"))["labels"]
    th = json.load(open(OUT / "analysis" / "results_dot3.json", encoding="utf-8"))["thresholds"]["xhard_v1"]
    y, j, x, ent = [], [], [], []
    for r in rows:
        for i, c in enumerate(r["claims"]):
            y.append(lab[f"{r['qid']}|{i}"]["label"]); j.append(r["judge7"][i] or "unsupported")
            s = r["xhard"][i]; ent.append(s["entail"])
            x.append("supported" if s["entail"] >= th[0] else "contradicted" if s["contra"] >= th[1] else "unsupported")

    def catch(p):
        wrong = [k for k, v in enumerate(y) if v != "supported"]; right = [k for k, v in enumerate(y) if v == "supported"]
        return {"caught": sum(p[k] != "supported" for k in wrong), "wrong": len(wrong), "false_alarm": sum(p[k] != "supported" for k in right), "right": len(right)}

    rng = np.random.default_rng(42)

    def ci(p):
        Y, P = np.array(y), np.array(p)
        b = [macro_f1(Y[i], P[i]) for i in (rng.integers(0, len(y), len(y)) for _ in range(1000))]
        return [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]

    ggf = [sum(lab[f"{r['qid']}|{i}"]["label"] == "supported" for i in range(len(r["claims"]))) / len(r["claims"]) for r in rows if r["claims"]]
    rag = [r["ragas7"] for r in rows if r["claims"]]
    ok = [(a, b) for a, b in zip(ggf, rag) if b is not None]
    out["viedureg"] = {"questions": len(rows), "claims": len(y), "dist": {l: y.count(l) for l in LABELS},
                       "gold_retrieved": sum(r["retrieved_gold"] > 0 for r in rows), "ggf_mean": float(np.mean(ggf)),
                       "judge_7b": {"macro_f1": macro_f1(y, j), "ci95": ci(j), **catch(j)},
                       "xhard": {"macro_f1": macro_f1(y, x), "ci95": ci(x), **catch(x)},
                       "majority": {"macro_f1": macro_f1(y, ["supported"] * len(y))},
                       "ragas7_spearman": float(spearmanr([a for a, _ in ok], [b for _, b in ok]).statistic), "ragas_n": len(ok)}

json.dump(out, open(RES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if "judge_32b" in out:
    r = out["judge_32b"]; m = r["method"]
    print(f"32B silver {m['macro_f1']:.3f} {m['ci95'][0]:.2f}-{m['ci95'][1]:.2f} auroc {m['auroc_not_supported']:.3f} caught {m['caught']}/{m['wrong']} fa {m['false_alarm']}/{m['right']} human {m['macro_f1_human']:.3f} cov {r['coverage']}")
    for k, v in r.items():
        if " - " in k:
            print(" ", k, round(v["diff"], 3), [round(a, 2) for a in v["ci95"]])
    print("  ragas32", r["corr_ragas_32b"], "judge32", r["corr_judge_32b"])
if "viedureg" in out:
    print("viedureg", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in out["viedureg"].items()})
