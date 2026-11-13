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

# ---------- three more systems (s19_dot4.py systems) on the same 40 questions, silver labels in dot4_silver.json
ps, pl = OUT / "dot4_systems.jsonl", OUT / "dot4_silver.json"
if ps.exists() and pl.exists():
    rows, lab = read_jsonl(ps), json.load(open(pl, encoding="utf-8"))["labels"]
    th = json.load(open(OUT / "analysis" / "results_dot3.json", encoding="utf-8"))["thresholds"]["xhard_v1"]
    rag7 = {(j["qid"], j["system"]): j["ragas"]["score"] for j in read_jsonl(OUT / "judges.jsonl") if j["model"] == "qwen2.5:7b"}
    per = defaultdict(lambda: {"silver": [], "judge7": [], "ragas7": [], "claims": 0, "dist": defaultdict(int), "empty": 0})
    for k in usable:  # the two round-1 systems, labels from prelabels.json
        q, sy, _ = k.split("|"); per[(q, sy)]
    for (q, sy) in list(per):
        ks = [k for k in usable if k.startswith(f"{q}|{sy}|")]
        a = per[(q, sy)]; a["sys"] = sy; a["n"] = len(ks)
        a["ggf"] = sum(gold[k] == "supported" for k in ks) / len(ks)
        a["ggf_j7"] = sum(pred["j7"].get(k) == "supported" for k in ks) / len(ks)
        a["ragas7"] = rag7.get((q, sy)); a["bad"] = any(gold[k] != "supported" for k in ks)
        for k in ks:
            a["dist"][gold[k]] += 1
    y, j7, xh, ent = [], [], [], []
    for r in rows:
        key = (r["qid"], r["system"]); a = per[key]; a["sys"] = r["system"]; a["ragas7"] = r["ragas7"]
        ls = [lab[f"{r['qid']}|{r['system']}|{i}"] for i in range(len(r["claims"]))]
        a["n"] = len(ls)
        if not ls:
            continue
        a["ggf"] = sum(x == "supported" for x in ls) / len(ls)
        a["ggf_j7"] = sum((x or "unsupported") == "supported" for x in r["judge7"]) / len(ls)
        a["bad"] = any(x != "supported" for x in ls)
        for i, l in enumerate(ls):
            a["dist"][l] += 1; y.append(l); j7.append(r["judge7"][i] or "unsupported")
            sc = r["xhard"][i]; ent.append(sc["entail"])
            xh.append("supported" if sc["entail"] >= th[0] else "contradicted" if sc["contra"] >= th[1] else "unsupported")
    table = {}
    for sy in ("graph", "naive", "bm25", "dense", "naive7b"):
        ans = [a for a in per.values() if a.get("sys") == sy]
        full = [a for a in ans if a.get("n")]
        rg = [a["ragas7"] for a in full if a["ragas7"] is not None]
        table[sy] = {"answers": len(ans), "no_claims": len(ans) - len(full), "claims": sum(a["n"] for a in full),
                     "dist": {l: sum(a["dist"][l] for a in full) for l in LABELS},
                     "ggf_silver": float(np.mean([a["ggf"] for a in full])), "ggf_judge7": float(np.mean([a["ggf_j7"] for a in full])),
                     "ragas7": float(np.mean(rg)), "answers_with_bad_claim": sum(a["bad"] for a in full)}
    names = list(table)
    rank = {m: float(spearmanr([table[n]["ggf_silver"] for n in names], [table[n][m] for n in names]).statistic) for m in ("ggf_judge7", "ragas7")}
    full = [a for a in per.values() if a.get("n") and a["ragas7"] is not None]
    rng = np.random.default_rng(42)

    def check(p):
        Y, P = np.array(y), np.array(p)
        b = [macro_f1(Y[i], P[i]) for i in (rng.integers(0, len(y), len(y)) for _ in range(1000))]
        wrong = [k for k, v in enumerate(y) if v != "supported"]; right = [k for k, v in enumerate(y) if v == "supported"]
        return {"macro_f1": macro_f1(y, p), "ci95": [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))],
                "caught": sum(p[k] != "supported" for k in wrong), "wrong": len(wrong), "false_alarm": sum(p[k] != "supported" for k in right), "right": len(right)}

    out["systems"] = {"table": table, "rank_spearman_vs_silver_ggf": rank,
                      "answer_spearman_ragas7_vs_silver_ggf": {"n": len(full), "rho": float(spearmanr([a["ggf"] for a in full], [a["ragas7"] for a in full]).statistic)},
                      "new_claims": {"n": len(y), "dist": {l: y.count(l) for l in LABELS}, "judge_7b": check(j7), "xhard": check(xh),
                                     "majority": {"macro_f1": macro_f1(y, ["supported"] * len(y))}}}

# ---------- KAG-style Verify operator (s19_dot4.py verify)
pv = OUT / "dot4_verify.jsonl"
if pv.exists():
    rows = read_jsonl(pv)
    order = defaultdict(list)
    for c in read_jsonl(OUT / "claims.jsonl"):
        order[(c["qid"], c["system"])].append(c["cid"])
    # 1. the operator's own labels on the original 284 claims, as a checker
    op = {}
    for r in rows:
        for cid, x in zip(order[(r["qid"], r["system"])], r["operator"]):
            if cid in gold:
                op[cid] = x["label"]
    res = {"checker": table_row(op, keys, gold, human), "judge_calls": sum(r["judge_calls"] for r in rows),
           "claims_checked": sum(len(r["operator"]) for r in rows),
           "decided_by": {b: sum(x["by"] == b for r in rows for x in r["operator"]) for b in ("verifier", "judge7b", "document check")},
           "human - judge_7b": paired(op, pred["j7"], keys, gold, human), "silver - judge_7b": paired(op, pred["j7"], keys, gold)}
    # 2. what happens to the answers, every version rescored by the same 14B judge
    j14 = {(j["qid"], j["system"]): j["judge"] for j in read_jsonl(OUT / "judges_dot2.jsonl")}
    revised = {(r["qid"], r["system"]): r["rounds"] for r in read_jsonl(OUT / "revise.jsonl")}

    def orig(key):
        return [j14[key].get(cid) or "unsupported" for cid in order[key]]

    def silver_ok(key):  # every usable claim of the original answer is supported (silver labels)
        ks = [cid for cid in order[key] if cid in gold]
        return bool(ks) and all(gold[cid] == "supported" for cid in ks)

    def summarise(version):
        refused = [k for k, v in version.items() if v is None]
        kept = {k: v for k, v in version.items() if v}
        return {"answers": len(version), "refused": len(refused),
                "refused_but_silver_correct": sum(silver_ok(k) for k in refused),
                "ggf14_mean": float(np.mean([sum(x == "supported" for x in v) / len(v) for v in kept.values()])),
                "with_bad_claim": sum(any(x != "supported" for x in v) for v in kept.values()),
                "claims": sum(len(v) for v in kept.values())}

    versions = {"original": {}, "baseline_revise": {}, "verify_operator": {}}
    for r in rows:
        key = (r["qid"], r["system"])
        versions["original"][key] = orig(key)
        versions["baseline_revise"][key] = r["j14_base"] if revised.get(key) else orig(key)
        versions["verify_operator"][key] = None if r["claims_op"] == [] else (r["j14_op"] if r["changed"] else orig(key))
    res["outcome"] = {k: summarise(v) for k, v in versions.items()}
    res["changed"] = sum(r["changed"] for r in rows)
    res["baseline_changed"] = sum(bool(revised.get((r["qid"], r["system"]))) for r in rows)
    res["silver_correct_answers"] = sum(silver_ok((r["qid"], r["system"])) for r in rows)
    out["verify"] = res

json.dump(out, open(RES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if "judge_32b" in out:
    r = out["judge_32b"]; m = r["method"]
    print(f"32B silver {m['macro_f1']:.3f} {m['ci95'][0]:.2f}-{m['ci95'][1]:.2f} auroc {m['auroc_not_supported']:.3f} caught {m['caught']}/{m['wrong']} fa {m['false_alarm']}/{m['right']} human {m['macro_f1_human']:.3f} cov {r['coverage']}")
    for k, v in r.items():
        if " - " in k:
            print(" ", k, round(v["diff"], 3), [round(a, 2) for a in v["ci95"]])
    print("  ragas32", r["corr_ragas_32b"], "judge32", r["corr_judge_32b"])
if "systems" in out:
    r = out["systems"]
    for k, v in r["table"].items():
        print(f"{k:8s} ans {v['answers']} empty {v['no_claims']} claims {v['claims']} silver {v['ggf_silver']:.3f} j7 {v['ggf_judge7']:.3f} ragas7 {v['ragas7']:.3f} bad {v['answers_with_bad_claim']} {v['dist']}")
    print("  rank rho", {k: round(v, 2) for k, v in r["rank_spearman_vs_silver_ggf"].items()}, "answer rho", r["answer_spearman_ragas7_vs_silver_ggf"])
    n = r["new_claims"]
    for k in ("judge_7b", "xhard"):
        m = n[k]; print(f"  {k} {m['macro_f1']:.3f} [{m['ci95'][0]:.2f}, {m['ci95'][1]:.2f}] caught {m['caught']}/{m['wrong']} fa {m['false_alarm']}/{m['right']}")
    print("  majority", round(n["majority"]["macro_f1"], 3), n["dist"])
if "verify" in out:
    r = out["verify"]; m = r["checker"]
    print(f"operator checker silver {m['macro_f1']:.3f} human {m['macro_f1_human']:.3f} caught {m['caught']}/{m['wrong']} fa {m['false_alarm']}/{m['right']}",
          "calls", r["judge_calls"], r["decided_by"], "changed", r["changed"], "base changed", r["baseline_changed"], "silver-correct", r["silver_correct_answers"])
    for k in ("human - judge_7b", "silver - judge_7b"):
        print(" ", k, round(r[k]["diff"], 3), [round(a, 2) for a in r[k]["ci95"]])
    for k, v in r["outcome"].items():
        print(" ", k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items()})
if "viedureg" in out:
    print("viedureg", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in out["viedureg"].items()})
