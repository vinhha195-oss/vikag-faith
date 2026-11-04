"""Step 8 (RQ3): verify-then-revise.

For every sampled answer the claim judge (qwen2.5:7b, from s4) flags unsupported/contradicted
claims. The generator (qwen2.5:3b) then rewrites the answer from the SAME retrieved context,
told which claims were not backed by it. The new answer is split (s2 prompt) and judged again
(s4 judge, same evidence pool); at most ROUNDS rounds. Output: outputs/revise.jsonl, one row per
answer with every round, so s7 can compare GGF / contradiction rate / token F1 before and after.
Answers with no flagged claim are kept unchanged (round list empty).
"""

from common import BIG_MODEL, GEN_MODEL, OUT, append_jsonl, chat, chat_json, read_jsonl
from s1_answer import SYSTEM as GEN_SYSTEM, format_context
from s2_claims import FEWSHOT, SYSTEM as SPLIT_SYSTEM, clean
from s4_judges import evidence_text, judge

ROUNDS = 2
REVISE = (
    "Dưới đây là câu trả lời trước của bạn và các mệnh đề trong đó mà người kiểm chứng thấy "
    "KHÔNG được NGỮ CẢNH hỗ trợ hoặc MÂU THUẪN với NGỮ CẢNH. Viết lại câu trả lời: sửa hoặc bỏ "
    "các mệnh đề đó, giữ các ý đúng, chỉ dùng thông tin trong NGỮ CẢNH, 2-5 câu. "
    "Nếu ngữ cảnh không đủ, nói rõ là không tìm thấy thông tin."
)
LABEL_VI = {"unsupported": "không có căn cứ", "contradicted": "mâu thuẫn với ngữ cảnh"}


def split(question, answer):
    prompt = f"{FEWSHOT}\nCÂU HỎI: {question}\nCÂU TRẢ LỜI: {answer}\nJSON:"
    return clean(chat_json(prompt, SPLIT_SYSTEM, GEN_MODEL, num_predict=600).get("claims", []))


def main():
    sample = {r["qid"] for r in read_jsonl(OUT / "sample.jsonl")}
    answers = {(a["qid"], a["system"]): a for a in read_jsonl(OUT / "answers.jsonl")}
    pools = {(p["qid"], p["system"]): p["pool"] for p in read_jsonl(OUT / "pools.jsonl")}
    j7 = {(j["qid"], j["system"]): j["judge"] for j in read_jsonl(OUT / "judges.jsonl")
          if j["model"] == BIG_MODEL}
    claims = {}
    for c in read_jsonl(OUT / "claims.jsonl"):
        claims.setdefault((c["qid"], c["system"]), []).append(c["claim"])
    path = OUT / "revise.jsonl"
    done = {(r["qid"], r["system"]) for r in read_jsonl(path)} if path.exists() else set()
    keys = sorted(k for k in answers if k[0] in sample and k not in done)
    for n, key in enumerate(keys, 1):
        a = answers[key]
        cl = claims.get(key, [])
        labels = [j7[key].get(f"{key[0]}|{key[1]}|{i}") for i in range(len(cl))]
        evidence = evidence_text(pools[key])
        context = format_context(a["retrieved"], a["relations"])
        answer, rounds = a["answer"], []
        for _ in range(ROUNDS):
            bad = [(c, l) for c, l in zip(cl, labels) if l in LABEL_VI]
            if not bad:
                break
            listing = "\n".join(f"- {c} ({LABEL_VI[l]})" for c, l in bad)
            prompt = (f"NGỮ CẢNH:\n{context}\n\nCÂU HỎI: {a['question']}\n\n"
                      f"CÂU TRẢ LỜI TRƯỚC:\n{answer}\n\nMỆNH ĐỀ CẦN SỬA:\n{listing}\n\n{REVISE}")
            answer = chat(prompt, GEN_SYSTEM, GEN_MODEL, num_predict=400, num_ctx=4096)
            cl = split(a["question"], answer)
            labels = judge(cl, evidence, BIG_MODEL) if cl else []
            rounds.append({"answer": answer, "claims": cl, "labels": labels})
        append_jsonl(path, {"qid": key[0], "system": key[1], "rounds": rounds})
        print(f"revise {n}/{len(keys)} rounds={len(rounds)}", flush=True)


if __name__ == "__main__":
    main()
