"""Round 4 (Colab): three more QA systems, the ViEduReg pilot, and a KAG-style Verify operator.

  python s19_dot4.py systems   ->  outputs/dot4_systems.jsonl   (40 sampled questions x bm25 / dense / naive7b)
  python s19_dot4.py edu       ->  outputs/dot4_edu.jsonl       (30 ViEduReg questions, naive RAG over 4 education documents)
  python s19_dot4.py verify    ->  outputs/dot4_verify.jsonl    (the 80 sampled answers: Verify operator + revise,
                                                                 rescored by the 14B judge, which did not flag anything)

Each answer row holds the answer, its claims, the evidence pool, the 7B judge labels, RAGAS 7B, and the support
probabilities of the round-3 XLM-R verifier (xhard), so silver labels can be added later without rerunning models.
Every part resumes from its output file.

Verify operator (in the spirit of KAG's Verify step, not KAG itself): for each claim, the verifier decides when it is
sure; uncertain claims (support probability within MARGIN of the threshold) go to the 7B judge; a claim that names
a document number that no passage of the evidence belongs to is flagged. Flagged claims are revised once by the
generator; if every claim is flagged the operator refuses ("không tìm thấy thông tin").
"""

import json
import os
import re
import sys

os.environ.setdefault("VIKAG_CPU", "0")

from common import BIG_MODEL, GEN_MODEL, OUT, ROOT, append_jsonl, chat, chat_json, read_jsonl  # noqa: E402
from rules import overlap  # noqa: E402
from s1_answer import SYSTEM as GEN_SYSTEM, format_context  # noqa: E402
from s2_claims import FEWSHOT, SYSTEM as SPLIT_SYSTEM, clean  # noqa: E402
from s4_judges import evidence_text, judge, ragas  # noqa: E402
from s5_verifier import DOC_NO, MAX_LEN, head_ids, premises  # noqa: E402
from s8_revise import LABEL_VI, REVISE  # noqa: E402

MODEL_DIR = os.environ.get("VIKAG_XHARD", str(ROOT / "models" / "verifier_xhard"))
JUDGE14 = "qwen2.5:14b"
MARGIN = 0.15
BUDGET = 6000
_ver = {}


def verifier():
    if not _ver:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(MODEL_DIR)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR, torch_dtype=torch.float32).to("cuda").eval()
        _ver.update(tok=tok, model=model, ids=head_ids(model), torch=torch)
        d3 = json.load(open(OUT / "analysis" / "results_dot3.json", encoding="utf-8"))
        _ver["th"] = d3["thresholds"]["xhard_v1"]
    return _ver


def score(claim, pool):
    v = verifier()
    prem = premises(pool, False)
    probs = []
    with v["torch"].no_grad():
        for i in range(0, len(prem), 8):
            enc = v["tok"](prem[i:i + 8], [claim] * len(prem[i:i + 8]), truncation="longest_first", max_length=MAX_LEN,
                           padding=True, return_tensors="pt").to("cuda")
            probs += v["model"](**enc).logits.softmax(-1).tolist()
    relevant = sorted(range(len(prem)), key=lambda i: -overlap(claim, prem[i]))[:2]
    return {"entail": max(p[v["ids"]["supported"]] for p in probs), "contra": max(probs[i][v["ids"]["contradicted"]] for i in relevant)}


def decide(s, ts, tc):
    return "supported" if s["entail"] >= ts else "contradicted" if s["contra"] >= tc else "unsupported"


def split(question, answer):
    return clean(chat_json(f"{FEWSHOT}\nCÂU HỎI: {question}\nCÂU TRẢ LỜI: {answer}\nJSON:", SPLIT_SYSTEM, GEN_MODEL, num_predict=600).get("claims", []))


def take(passages, budget=BUDGET):
    out, used = [], 0
    for p in passages:
        if used + len(p["text"]) > budget and out:
            break
        out.append(p); used += len(p["text"])
    return out


def checked(row, pool, question):
    """Claims, 7B judge, RAGAS 7B and xhard scores for one answer."""
    cl = split(question, row["answer"])
    ev = evidence_text(pool)
    row["claims"] = cl
    row["pool"] = pool
    row["judge7"] = judge(cl, ev, BIG_MODEL) if cl else []
    row["ragas7"] = ragas(row["answer"], question, ev, BIG_MODEL)["score"]
    row["xhard"] = [score(c, pool) for c in cl]
    return row


# ---------- three more systems on the 40 sampled questions ----------
def systems():
    import csv
    from vihermes.graph import SQLiteGraph
    from vihermes.retrieval import HybridRetriever, NumpyDenseIndex, units
    from common import DATA, DENSE_INDEX, GRAPH_DB, OllamaEmbedder
    from s1_answer import passage
    from s3_pool import graph_facts

    graph = SQLiteGraph(GRAPH_DB)
    contexts = {r["context_id"]: r for r in csv.DictReader(open(DATA / "contexts.csv", encoding="utf-8"))}
    dense = NumpyDenseIndex(units(graph), OllamaEmbedder(), DENSE_INDEX)
    retr = {"bm25": HybridRetriever(graph, None, weight=0), "dense": HybridRetriever(graph, dense, weight=1),
            "naive7b": HybridRetriever(graph, dense, weight=0.5)}
    gen = {"bm25": GEN_MODEL, "dense": GEN_MODEL, "naive7b": BIG_MODEL}
    sample = [r["qid"] for r in read_jsonl(OUT / "sample.jsonl")]
    base = {a["qid"]: a for a in read_jsonl(OUT / "answers.jsonl") if a["system"] == "naive"}
    path = OUT / "dot4_systems.jsonl"
    done = {(r["qid"], r["system"]) for r in read_jsonl(path)} if path.exists() else set()
    for n, q in enumerate(sample, 1):
        a = base[q]
        for system in ("bm25", "dense", "naive7b"):
            if (q, system) in done:
                continue
            ret = [passage(e.node) for e in retr[system].seeds(a["question"], k=8)]
            ret = take(ret)
            answer = chat(f"NGỮ CẢNH:\n{format_context(ret)}\n\nCÂU HỎI: {a['question']}", GEN_SYSTEM, gen[system], num_predict=400, num_ctx=4096)
            ids = list(dict.fromkeys([p["id"] for p in ret] + a["gold_ids"]))
            pool = [{"id": i, "title": contexts[i]["title"], "text": contexts[i]["text"], "retrieved": i in {p["id"] for p in ret},
                     "gold": i in a["gold_ids"], "facts": graph_facts(graph, i)} for i in ids if i in contexts]
            row = {"qid": q, "system": system, "hop": a["hop"], "question": a["question"], "gold_answer": a["gold_answer"],
                   "gold_ids": a["gold_ids"], "answer": answer}
            append_jsonl(path, checked(row, pool, a["question"]))
        print(f"systems {n}/{len(sample)}", flush=True)


# ---------- ViEduReg pilot ----------
def edu():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel

    P = read_jsonl(OUT / "viedureg" / "passages.jsonl")
    byid = {p["id"]: p for p in P}
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    mat = vec.fit_transform([p["title"] + " " + p["text"] for p in P])
    path = OUT / "dot4_edu.jsonl"
    done = {r["qid"] for r in read_jsonl(path)} if path.exists() else set()
    Q = read_jsonl(OUT / "viedureg" / "questions.jsonl")
    for n, q in enumerate(Q, 1):
        if q["qid"] in done:
            continue
        sims = linear_kernel(vec.transform([q["question"]]), mat).ravel()
        ret = take([{"id": P[i]["id"], "title": P[i]["title"], "text": P[i]["text"]} for i in sims.argsort()[::-1][:8]])
        answer = chat(f"NGỮ CẢNH:\n{format_context(ret)}\n\nCÂU HỎI: {q['question']}", GEN_SYSTEM.replace("ngành y tế", "giáo dục đại học"),
                      GEN_MODEL, num_predict=400, num_ctx=4096)
        ids = list(dict.fromkeys([p["id"] for p in ret] + q["gold_ids"]))
        pool = [{"id": i, "title": byid[i]["title"], "text": byid[i]["text"], "retrieved": i in {p["id"] for p in ret},
                 "gold": i in q["gold_ids"], "facts": [f"Đoạn thuộc văn bản: {byid[i]['title']}"]} for i in ids]
        row = {"qid": q["qid"], "system": "edu_naive", "hop": q["hop"], "question": q["question"], "gold_answer": q["answer"],
               "gold_ids": q["gold_ids"], "answer": answer, "retrieved_gold": sum(p["gold"] and p["retrieved"] for p in pool)}
        append_jsonl(path, checked(row, pool, q["question"]))
        print(f"edu {n}/{len(Q)}", flush=True)


# ---------- KAG-style Verify operator on the 80 sampled answers ----------
def operator_labels(claims, pool):
    ts, tc = verifier()["th"]
    docs = {m for p in pool for m in DOC_NO.findall(p["title"] + " " + " ".join(p["facts"]) + " " + p["text"])}
    out, used_judge = [], 0
    ev = evidence_text(pool)
    for c in claims:
        s = score(c, pool)
        lab, how = decide(s, ts, tc), "verifier"
        if abs(s["entail"] - ts) < MARGIN:
            j = judge([c], ev, BIG_MODEL)[0]
            if j:
                lab, how, used_judge = j, "judge7b", used_judge + 1
        cited = set(DOC_NO.findall(c))
        if lab == "supported" and cited and not cited & docs:
            lab, how = "unsupported", "document check"
        out.append({"claim": c, "label": lab, "by": how, "entail": round(s["entail"], 4)})
    return out, used_judge


def verify():
    sample = {r["qid"] for r in read_jsonl(OUT / "sample.jsonl")}
    answers = {(a["qid"], a["system"]): a for a in read_jsonl(OUT / "answers.jsonl") if a["qid"] in sample}
    pools = {(p["qid"], p["system"]): p["pool"] for p in read_jsonl(OUT / "pools.jsonl")}
    claims = {}
    for c in read_jsonl(OUT / "claims.jsonl"):
        claims.setdefault((c["qid"], c["system"]), []).append(c["claim"])
    base = {(r["qid"], r["system"]): r["rounds"] for r in read_jsonl(OUT / "revise.jsonl")}
    path = OUT / "dot4_verify.jsonl"
    done = {(r["qid"], r["system"]) for r in read_jsonl(path)} if path.exists() else set()
    for n, key in enumerate(sorted(answers), 1):
        if key in done:
            continue
        a, pool = answers[key], pools[key]
        labels, n_judge = operator_labels(claims.get(key, []), pool)
        bad = [x for x in labels if x["label"] in LABEL_VI]
        answer, new_claims = a["answer"], None
        if bad and len(bad) == len(labels):
            answer, new_claims = "Không tìm thấy thông tin đủ tin cậy trong ngữ cảnh để trả lời câu hỏi này.", []
        elif bad:
            listing = "\n".join(f"- {x['claim']} ({LABEL_VI[x['label']]})" for x in bad)
            context = format_context(a["retrieved"], a["relations"])
            answer = chat(f"NGỮ CẢNH:\n{context}\n\nCÂU HỎI: {a['question']}\n\nCÂU TRẢ LỜI TRƯỚC:\n{answer}\n\nMỆNH ĐỀ CẦN SỬA:\n{listing}\n\n{REVISE}",
                          GEN_SYSTEM, GEN_MODEL, num_predict=400, num_ctx=4096)
            new_claims = split(a["question"], answer)
        ev = evidence_text(pool)
        row = {"qid": key[0], "system": key[1], "operator": labels, "judge_calls": n_judge, "changed": bool(bad),
               "answer_op": answer, "claims_op": new_claims}
        # independent rescoring by the 14B judge: the operator's answer and the earlier 7B-flagged revision
        row["j14_op"] = judge(new_claims, ev, JUDGE14) if new_claims else ([] if new_claims == [] else None)
        rounds = base.get(key) or []
        if rounds:
            last = rounds[-1]
            row["answer_base"], row["claims_base"] = last["answer"], last["claims"]
            row["j14_base"] = judge(last["claims"], ev, JUDGE14) if last["claims"] else []
        append_jsonl(path, row)
        print(f"verify {n}/{len(answers)} changed={bool(bad)} judge_calls={n_judge}", flush=True)


if __name__ == "__main__":
    {"systems": systems, "edu": edu, "verify": verify}[sys.argv[1]]()
