"""Refresh demo/vikag_faith_demo.html, the single demo page: the data line of the page is rewritten in place
from outputs/ (same numbers as the paper). There is no separate template."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
R = lambda f: [json.loads(l) for l in open(OUT / f, encoding="utf-8")]  # noqa: E731

res = json.load(open(OUT / "analysis" / "results.json", encoding="utf-8"))
sample = {r["qid"]: r["split"] for r in R("sample.jsonl")}
answers = {(a["qid"], a["system"]): a for a in R("answers.jsonl")}
pools = {(p["qid"], p["system"]): p["pool"] for p in R("pools.jsonl")}
pre = json.load(open(OUT / "prelabels.json", encoding="utf-8"))
scores = {r["cid"]: r for r in R("verifier_scores.jsonl")}
ids = json.load(open(OUT / "annotation" / "id_map.json", encoding="utf-8"))
audit = {}  # human labels from the two blind passes (C: full passages, G: quick excerpts)
for name in ("C", "G", "H", "I", "J"):
    path = OUT / "annotation" / f"vifaith_labels_{name}.json"
    if path.exists():
        audit.update({ids[k]: v["label"] for k, v in json.load(open(path, encoding="utf-8"))["labels"].items() if v.get("label")})
revise = {(r["qid"], r["system"]): r["rounds"] for r in R("revise.jsonl")}
judges = {}
for j in R("judges.jsonl"):
    judges.setdefault((j["qid"], j["system"]), {})[j["model"]] = j


def decide(s, ts, tc):
    return "supported" if s["entail"] >= ts else "contradicted" if s["contra"] >= tc else "unsupported"


th = res["thresholds"]
claims = {}
for c in R("claims.jsonl"):
    if c["qid"] in sample:
        claims.setdefault((c["qid"], c["system"]), []).append(c)

passages, items = {}, {}
for (q, s), cl in claims.items():
    a = answers[(q, s)]
    for p in pools[(q, s)]:
        passages[p["id"]] = {"t": p["title"], "x": p["text"], "f": p["facts"][1:]}
    jg = judges.get((q, s), {})
    rows = []
    for c in cl:
        k = c["cid"]
        rows.append({
            "c": c["claim"], "bad": pre[k]["bad"], "note": pre[k]["note"],
            "L": {"claude": pre[k]["label"],
                  "j7": jg.get("qwen2.5:7b", {}).get("judge", {}).get(k),
                  "j3": jg.get("qwen2.5:3b", {}).get("judge", {}).get(k),
                  "v1": decide(scores[k]["zs_v1"], *th["zs_v1"]),
                  "ft": decide(scores[k]["ft_v1"], *th["ft_v1"]),
                  "v2": decide(scores[k]["zs_v2"], *th["zs_v2"]),
                  "human": audit.get(k)},
        })
    item = items.setdefault(q, {"q": q, "hop": a["hop"], "split": sample[q], "question": a["question"],
                                "gold": a["gold_answer"], "gold_ids": a["gold_ids"], "sys": {}})
    item["sys"][s] = {"answer": a["answer"], "pool": [p["id"] for p in pools[(q, s)]],
                      "ragas7": jg.get("qwen2.5:7b", {}).get("ragas", {}).get("score"),
                      "ragas3": jg.get("qwen2.5:3b", {}).get("ragas", {}).get("score"),
                      "claims": rows, "rev": None}
    rounds = revise.get((q, s))
    if rounds:
        last = rounds[-1]
        ls = [x for x in last["labels"] if x]
        item["sys"][s]["rev"] = {"rounds": len(rounds), "answer": last["answer"], "claims": last["claims"],
                                 "labels": last["labels"], "ggf": sum(x == "supported" for x in ls) / len(ls) if ls else None}

summary = {
    "claim": {k: {"f1": v["macro_f1"], "ci": v["ci95"], "acc": v["acc"]} for k, v in res["claim_level"].items()},
    "corr": {k: v["spearman"] for k, v in res["answer_level_correlation"].items()},
    "revise": res["revise"]["all"],
    "systems": {s: res["systems"][s] for s in ("naive", "graph")}, "p": res["systems"]["wilcoxon_GGF_p"],
    "audit": {k: res["agreement"].get("audit_CG", res["agreement"]["audit"])[k] for k in ("n", "acc", "kappa", "confusion_claude_rows_human_cols", "rank_spearman")},
    "qa": res["qa"], "n_claims": res["claims_total"], "n_test": res["claims_test"],
}
# Plain-language numbers for the story page: how many wrong claims (Claude label not "supported") each
# checker flags on the test split, and how many correct claims it flags by mistake.
test_rows = [r for it in items.values() if it["split"] == "test" for s in it["sys"].values() for r in s["claims"] if not r["bad"]]
catch = {}
for m in ("j7", "j3", "v1", "ft"):
    rs = [r for r in test_rows if r["L"][m]]
    wrong = [r for r in rs if r["L"]["claude"] != "supported"]
    right = [r for r in rs if r["L"]["claude"] == "supported"]
    catch[m] = {"caught": sum(r["L"][m] != "supported" for r in wrong), "wrong": len(wrong),
                "false_alarm": sum(r["L"][m] != "supported" for r in right), "right": len(right)}
summary["catch"] = catch
summary["rounds"] = {k: res["revise"]["by_max_rounds"][k] for k in ("1", "2")}
summary["by_hop"] = res["systems"]["by_hop"]
summary["comparisons"] = res["comparisons"]
summary["sensitivity"] = res["agreement"].get("audit_CG", res["agreement"]["audit"])["sensitivity"]

data = {"items": sorted(items.values(), key=lambda x: (x["hop"], x["q"])), "passages": passages, "summary": summary}
page = ROOT / "demo" / "vikag_faith_demo.html"
lines = page.read_text(encoding="utf-8").split("\n")
at = next(i for i, line in enumerate(lines) if line.startswith("const DATA = "))
lines[at] = "const DATA = " + json.dumps(data, ensure_ascii=False) + ";"
page.write_text("\n".join(lines), encoding="utf-8")
print(page, f"{page.stat().st_size / 1e6:.2f} MB", len(items), "questions")
