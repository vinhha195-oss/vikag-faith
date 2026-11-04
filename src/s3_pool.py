"""Step 3: build each answer's evidence pool and the graph facts attached to it,
then draw the paired annotation sample (40 questions x 2 systems).

pool        = passages the system retrieved + the question's gold supporting passages
graph facts = provenance (passage -> document title) + legal relations from the ViHERMES graph
"""

import csv
import random

from vihermes.graph import SQLiteGraph

from common import DATA, GRAPH_DB, OUT, SEED, read_jsonl, write_jsonl

NAMES = {"AMENDS": "được sửa đổi bởi", "REPLACES": "được thay thế bởi",
         "SUPPLEMENTS": "được bổ sung bởi", "REFERS_TO": "dẫn chiếu tới"}


def label(graph, key):
    n = graph.get(key)
    if n is None:
        return key
    if n.title:
        return n.title
    return f"{n.document_id} (chưa có văn bản trong corpus)" if n.placeholder else key


def graph_facts(graph, pid):
    """Facts about one passage that come from the graph, not from its body text."""
    node = graph.get(pid)
    facts = []
    if node is not None:
        doc = graph.get(node.document_id)
        facts.append(f"Đoạn thuộc văn bản: {doc.title if doc and doc.title else node.title}")
        if not node.document_id.startswith("doc-"):
            facts.append(f"Số hiệu văn bản: {node.document_id}")
    for e in graph.edges(pid) + graph.edges(pid, incoming=True):
        if e.relation in NAMES:
            facts.append(f"{label(graph, e.source)} {NAMES[e.relation]} {label(graph, e.target)}")
    return list(dict.fromkeys(facts))


def main():
    graph = SQLiteGraph(GRAPH_DB)
    contexts = {r["context_id"]: r for r in csv.DictReader(open(DATA / "contexts.csv", encoding="utf-8"))}
    answers = read_jsonl(OUT / "answers.jsonl")
    claims = read_jsonl(OUT / "claims.jsonl")
    with_claims = {(c["qid"], c["system"]) for c in claims}

    pools = []
    for a in answers:
        ids = list(dict.fromkeys([p["id"] for p in a["retrieved"]] + a["gold_ids"]))
        pool = []
        for pid in ids:
            ctx = contexts.get(pid)
            if ctx is None:  # retrieved non-context nodes do not occur for context imports
                continue
            pool.append({
                "id": pid, "title": ctx["title"], "text": ctx["text"],
                "retrieved": pid in {p["id"] for p in a["retrieved"]},
                "gold": pid in a["gold_ids"], "facts": graph_facts(graph, pid),
            })
        pools.append({"qid": a["qid"], "system": a["system"], "hop": a["hop"], "pool": pool})
    write_jsonl(OUT / "pools.jsonl", pools)

    # Paired sample: questions where both systems produced claims, 8 per hop.
    rng = random.Random(SEED)
    sample = []
    for hop in range(1, 6):
        qids = sorted({a["qid"] for a in answers if a["hop"] == hop
                       and (a["qid"], "naive") in with_claims and (a["qid"], "graph") in with_claims})
        sample += rng.sample(qids, min(8, len(qids)))
    rng.shuffle(sample)
    # 20% of questions -> dev (threshold tuning), rest -> test.
    split = {q: ("dev" if i < len(sample) // 5 else "test") for i, q in enumerate(sample)}
    write_jsonl(OUT / "sample.jsonl", [{"qid": q, "split": split[q]} for q in sample])
    n = sum(1 for c in claims if c["qid"] in split)
    print(f"pools: {len(pools)}  sampled questions: {len(sample)}  sampled claims: {n}")


if __name__ == "__main__":
    main()
