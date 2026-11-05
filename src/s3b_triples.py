"""Step 3b: triple store and mutual index between triples and source passages (proposal, evidence alignment).

triple        = (document or clause; legal relation; document) taken from the ViHERMES graph
chunk_triples = passage id -> triples of its document and of the passage itself
doc_chunks    = document number -> its passages, so a document named in a claim leads back to its source text

Writes outputs/triple_index.json. Uses no model.
"""

import csv
import json
import re
import sqlite3

from common import DATA, GRAPH_DB, OUT

DOC_NO = re.compile(r"\d+/(?:\d{4}/)?[A-Za-zĐđ]+(?:-[A-Za-zĐđ]+)*")
NAMES = {"AMENDS": "sửa đổi", "REPLACES": "thay thế", "SUPPLEMENTS": "bổ sung", "REFERS_TO": "dẫn chiếu tới"}
csv.field_size_limit(10 ** 8)


def main():
    db = sqlite3.connect(GRAPH_DB)
    nodes = {i: json.loads(p) for i, p in db.execute("select id, payload from nodes")}

    def name(key):
        n = nodes.get(key) or {}
        if n.get("title"):
            return n["title"]
        return n.get("document_id") or key

    def doc_of(key):
        return (nodes.get(key) or {}).get("document_id") or key

    by_doc, by_node, total = {}, {}, 0
    for src, tgt, rel in db.execute("select source, target, relation from edges"):
        if rel not in NAMES:
            continue
        t = f"({name(src)}; {NAMES[rel]}; {name(tgt)})."
        total += 1
        for key in (src, tgt):
            by_node.setdefault(key, []).append(t)
            by_doc.setdefault(doc_of(key), []).append(t)

    chunk_triples, doc_chunks = {}, {}
    for r in csv.DictReader(open(DATA / "contexts.csv", encoding="utf-8")):
        pid, doc = r["context_id"], doc_of(r["context_id"])
        chunk_triples[pid] = list(dict.fromkeys(by_node.get(pid, []) + by_doc.get(doc, [])))
        item = {"id": pid, "title": r["title"], "text": r["text"]}
        doc_chunks.setdefault(doc, []).append(item)
        # Mutual index by document number: the number in a title or heading, or the graph's own node id.
        keys = set(DOC_NO.findall(r["title"] + " " + r["text"][:300]))
        if not doc.startswith("doc-"):
            keys.add(doc)
        for key in keys:
            doc_chunks.setdefault(key, []).append(item)

    path = OUT / "triple_index.json"
    json.dump({"chunk_triples": chunk_triples, "doc_chunks": doc_chunks}, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    with_t = sum(bool(v) for v in chunk_triples.values())
    print(f"triples {total}  passages {len(chunk_triples)}  passages with triples {with_t}  index keys {len(doc_chunks)}")


if __name__ == "__main__":
    main()
