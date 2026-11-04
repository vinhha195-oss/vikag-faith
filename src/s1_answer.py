"""Step 1: answer the sampled ViHERMES questions with two systems sharing one LLM.

naive  - hybrid BM25 + bge-m3 seeds, cut at a character budget
graph  - same seeds, then ViHERMES typed propagation over the regulatory graph
Both get the same generator, prompt and context budget, so differences come from retrieval.
"""

from vihermes.graph import SQLiteGraph
from vihermes.retrieval import GraphPropagator, HybridRetriever, NumpyDenseIndex, units

from common import (
    DENSE_INDEX, GEN_MODEL, GRAPH_DB, OUT, OllamaEmbedder, append_jsonl, chat, read_jsonl,
    sample_questions,
)

BUDGET = 6000  # characters of passage text per question, both systems
OUTFILE = OUT / "answers.jsonl"

SYSTEM = (
    "Bạn là trợ lý hỏi đáp về văn bản quy phạm pháp luật ngành y tế Việt Nam. "
    "Chỉ dùng thông tin trong NGỮ CẢNH. Trả lời bằng tiếng Việt, 2-5 câu, nêu tên văn bản khi có. "
    "Nếu ngữ cảnh không đủ, nói rõ là không tìm thấy thông tin."
)


def passage(node):
    return {"id": node.id, "title": node.title, "text": node.text}


def take_budget(nodes):
    out, used = [], 0
    for n in nodes:
        if used + len(n.text) > BUDGET and out:
            break
        out.append(n)
        used += len(n.text)
    return out


def format_context(passages, relations=()):
    parts = [f"[{i}] Văn bản: {p['title']}\n{p['text']}" for i, p in enumerate(passages, 1)]
    if relations:
        parts.append("Quan hệ giữa các văn bản:\n" + "\n".join(relations))
    return "\n\n".join(parts)


def describe(edge, graph):
    names = {"AMENDS": "được sửa đổi bởi", "REPLACES": "được thay thế bởi",
             "SUPPLEMENTS": "được bổ sung bởi", "REFERS_TO": "dẫn chiếu tới"}
    if edge.relation not in names:
        return None
    s, t = graph.get(edge.source), graph.get(edge.target)
    label = lambda n, key: (n.title if n and n.title else key)  # noqa: E731
    return f"- {label(s, edge.source)} {names[edge.relation]} {label(t, edge.target)}"


def main():
    graph = SQLiteGraph(GRAPH_DB)
    corpus = units(graph)
    embedder = OllamaEmbedder()
    dense = NumpyDenseIndex(corpus, embedder, DENSE_INDEX)
    retriever = HybridRetriever(graph, dense, weight=0.5)
    propagator = GraphPropagator(graph, max_depth=4, max_nodes=8, max_chars=BUDGET)

    done = {(r["qid"], r["system"]) for r in read_jsonl(OUTFILE)} if OUTFILE.exists() else set()
    questions = sample_questions()
    embedder.encode([q["question"] for q in questions])  # cache, then free the GPU for the LLM
    embedder.unload()
    for qi, q in enumerate(questions):
        seeds = retriever.seeds(q["question"], k=8)
        runs = {"naive": (take_budget([e.node for e in seeds]), [])}
        expanded = propagator.expand(seeds[:4])
        gnodes = [e.node for e in expanded.evidence if e.node.kind != "Document" and e.node.text]
        rels = [d for d in (describe(e, graph) for e in expanded.edges) if d]
        runs["graph"] = (take_budget(gnodes), rels[:12])
        for system, (nodes, relations) in runs.items():
            if (q["id"] + f"#{q['row']}", system) in done:
                continue
            passages = [passage(n) for n in nodes]
            prompt = f"NGỮ CẢNH:\n{format_context(passages, relations)}\n\nCÂU HỎI: {q['question']}"
            answer = chat(prompt, SYSTEM, GEN_MODEL, num_predict=400, num_ctx=4096)
            append_jsonl(OUTFILE, {
                "qid": q["id"] + f"#{q['row']}", "system": system, "hop": q["hop_level"],
                "question": q["question"], "gold_answer": q["answer"],
                "gold_ids": q["used_context_ids"], "answer": answer,
                "retrieved": passages, "relations": relations,
            })
        print(f"{qi + 1}/{len(questions)} hop={q['hop_level']}", flush=True)


if __name__ == "__main__":
    main()
