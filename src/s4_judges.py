"""Step 4: LLM-based automatic metrics on the annotation sample.

ragas  - RAGAS faithfulness re-implemented from the library's two prompts
         (statement generation, then NLI verdicts); score = supported / statements
judge  - claim-level LLM judge over OUR claims, 3 labels (same label set as the humans)
Run with qwen2.5:3b (7b optional: pass it as an argument). Every metric sees the same evidence pool.
"""

import sys

from common import BIG_MODEL, GEN_MODEL, OUT, append_jsonl, chat_json, read_jsonl

MAX_PASSAGE = 2500  # characters per passage inside LLM prompts

RAGAS_STATEMENTS = (
    "Given a question, an answer, and sentences from the answer analyze the complexity of each "
    "sentence given under 'sentences' and break down each sentence into one or more fully "
    "understandable statements while also ensuring no pronouns are used in each statement. "
    'Format the outputs in JSON: {"statements": ["...", "..."]}. Keep the statements in the '
    "language of the answer."
)
RAGAS_NLI = (
    "Your task is to judge the faithfulness of a series of statements based on a given context. "
    "For each statement you must return verdict as 1 if the statement can be directly inferred "
    "based on the context or 0 if the statement can not be directly inferred based on the context. "
    'Format the outputs in JSON: {"verdicts": [{"statement": "...", "reason": "...", "verdict": 1}]}'
)
JUDGE = (
    "Bạn là người kiểm chứng. Với mỗi mệnh đề (claim), so với BẰNG CHỨNG và gán đúng một nhãn:\n"
    "- supported: bằng chứng suy ra được mệnh đề.\n"
    "- contradicted: bằng chứng nói ngược lại mệnh đề (sai số liệu, ngày, tên văn bản, phủ định...).\n"
    "- unsupported: bằng chứng không đề cập, không đủ để kết luận.\n"
    'Trả về JSON: {"labels": [{"i": 1, "label": "supported"}, ...]} theo đúng thứ tự mệnh đề.'
)
LABELS = {"supported", "contradicted", "unsupported"}


def evidence_text(pool):
    parts = []
    for i, p in enumerate(pool, 1):
        facts = "; ".join(p["facts"])
        parts.append(f"[{i}] Văn bản: {p['title']}\n{p['text'][:MAX_PASSAGE]}\n(Thông tin đồ thị: {facts})")
    return "\n\n".join(parts)


def ragas(answer, question, context, model):
    sentences = [s.strip() for s in answer.replace("\n", " ").split(". ") if s.strip()]
    st = chat_json(
        f"question: {question}\nanswer: {answer}\nsentences: {sentences}",
        RAGAS_STATEMENTS, model, num_predict=700, num_ctx=4096,
    ).get("statements", [])
    st = [s for s in st if isinstance(s, str) and s.strip()]
    if not st:
        return {"statements": [], "verdicts": [], "score": None}
    listing = "\n".join(f"statement_{i}: {s}" for i, s in enumerate(st, 1))
    out = chat_json(f"context:\n{context}\n\nstatements:\n{listing}", RAGAS_NLI, model,
                    num_predict=1200, num_ctx=12288).get("verdicts", [])
    if not out:  # the call failed or returned nothing parseable: no score, not a zero
        return {"statements": st, "verdicts": [], "score": None}
    verdicts = [1 if str(v.get("verdict")).strip().lower() in {"1", "true", "yes"} else 0
                for v in out if isinstance(v, dict)][: len(st)]
    verdicts += [0] * (len(st) - len(verdicts))  # unparsed verdicts count as not inferred
    return {"statements": st, "verdicts": verdicts, "score": sum(verdicts) / len(st)}


def judge(claims, context, model):
    listing = "\n".join(f"{i}. {c}" for i, c in enumerate(claims, 1))
    out = chat_json(f"BẰNG CHỨNG:\n{context}\n\nMỆNH ĐỀ:\n{listing}", JUDGE, model,
                    num_predict=60 * len(claims) + 50, num_ctx=12288).get("labels", [])
    by_i = {}
    for x in out:
        if isinstance(x, dict) and str(x.get("label")).strip().lower() in LABELS:
            try:
                by_i[int(x.get("i"))] = str(x["label"]).strip().lower()
            except (TypeError, ValueError):
                pass
    # A claim the judge skipped gets None and is excluded from scoring, never a silent default.
    return [by_i.get(i) for i in range(1, len(claims) + 1)]


def main(models):
    sample = {r["qid"] for r in read_jsonl(OUT / "sample.jsonl")}
    answers = {(a["qid"], a["system"]): a for a in read_jsonl(OUT / "answers.jsonl")}
    pools = {(p["qid"], p["system"]): p["pool"] for p in read_jsonl(OUT / "pools.jsonl")}
    claims = {}
    for c in read_jsonl(OUT / "claims.jsonl"):
        claims.setdefault((c["qid"], c["system"]), []).append(c)
    path = OUT / "judges.jsonl"
    done = {(r["qid"], r["system"], r["model"]) for r in read_jsonl(path)} if path.exists() else set()
    keys = sorted(k for k in answers if k[0] in sample)
    for model in models:
        for n, key in enumerate(keys, 1):
            if (*key, model) in done:
                continue
            a, cl = answers[key], claims[key]
            context = evidence_text(pools[key])
            r = ragas(a["answer"], a["question"], context, model)
            labels = judge([c["claim"] for c in cl], context, model)
            append_jsonl(path, {"qid": key[0], "system": key[1], "model": model, "ragas": r,
                                "judge": {c["cid"]: l for c, l in zip(cl, labels)}})
            print(f"{model} {n}/{len(keys)}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or [GEN_MODEL])
