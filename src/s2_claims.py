"""Step 2: split every system answer into atomic, self-contained claims (Vietnamese prompt)."""

import re

from common import GEN_MODEL, OUT, append_jsonl, chat_json, read_jsonl, write_jsonl

SYSTEM = (
    "Bạn tách câu trả lời thành các mệnh đề nguyên tử (claim). Quy tắc:\n"
    "1. Mỗi claim chỉ nêu MỘT sự kiện, có một vị từ chính.\n"
    "2. Mỗi claim phải tự hiểu được: thay đại từ ('văn bản này', 'nó') bằng tên cụ thể.\n"
    "3. Giữ nguyên con số, ngày tháng, số hiệu văn bản như trong câu trả lời.\n"
    "4. Không thêm thông tin ngoài câu trả lời. Bỏ các câu chỉ nói 'không tìm thấy thông tin'.\n"
    'Trả về JSON: {"claims": ["...", "..."]}'
)

FEWSHOT = """Ví dụ:
CÂU HỎI: Thông tư 01/2020/TT-BYT có hiệu lực khi nào và quy định gì?
CÂU TRẢ LỜI: Thông tư 01/2020/TT-BYT có hiệu lực từ ngày 01/3/2020. Văn bản này quy định hồ sơ đăng ký lưu hành thuốc gồm đơn đăng ký và giấy chứng nhận GMP.
JSON: {"claims": ["Thông tư 01/2020/TT-BYT có hiệu lực từ ngày 01/3/2020.", "Thông tư 01/2020/TT-BYT quy định hồ sơ đăng ký lưu hành thuốc gồm đơn đăng ký.", "Thông tư 01/2020/TT-BYT quy định hồ sơ đăng ký lưu hành thuốc gồm giấy chứng nhận GMP."]}

CÂU HỎI: Ai chịu trách nhiệm tổ chức thực hiện chương trình?
CÂU TRẢ LỜI: Ngữ cảnh không nêu rõ. Tuy nhiên, Bộ Y tế chủ trì và phối hợp với các bộ, ngành liên quan.
JSON: {"claims": ["Bộ Y tế chủ trì tổ chức thực hiện chương trình.", "Bộ Y tế phối hợp với các bộ, ngành liên quan để thực hiện chương trình."]}
"""

ABSTAIN = re.compile(r"không (tìm thấy|có|đủ) thông tin|không được (nêu|đề cập)", re.I)
NUMBER = re.compile(r"\d+(?:[.,/]\d+)*")


def clean(claims):
    seen, out = set(), []
    for c in claims:
        if not isinstance(c, str):
            continue
        c = " ".join(c.split())
        if len(c) < 8 or c.lower() in seen or ABSTAIN.search(c):
            continue
        seen.add(c.lower())
        out.append(c)
    return out


def main():
    answers = read_jsonl(OUT / "answers.jsonl")
    # Raw splits are cached per answer so an interrupted run resumes.
    raw_path = OUT / "claims_raw.jsonl"
    raw = {(r["qid"], r["system"]): r["claims"] for r in read_jsonl(raw_path)} if raw_path.exists() else {}
    rows = []
    for i, a in enumerate(answers):
        key = (a["qid"], a["system"])
        if key not in raw:
            prompt = f"{FEWSHOT}\nCÂU HỎI: {a['question']}\nCÂU TRẢ LỜI: {a['answer']}\nJSON:"
            raw[key] = chat_json(prompt, SYSTEM, GEN_MODEL, num_predict=600).get("claims", [])
            append_jsonl(raw_path, {"qid": a["qid"], "system": a["system"], "claims": raw[key]})
        claims = clean(raw[key])
        for j, c in enumerate(claims):
            rows.append({
                "cid": f"{a['qid']}|{a['system']}|{j}", "qid": a["qid"], "system": a["system"],
                "hop": a["hop"], "claim": c,
                # Rule post-check: claims carrying several values are flagged for annotators.
                "multi_value": len(NUMBER.findall(c)) >= 3,
            })
        if not claims:
            print("no claims:", a["qid"], a["system"])
        print(f"{i + 1}/{len(answers)}", flush=True)
    write_jsonl(OUT / "claims.jsonl", rows)
    print("claims:", len(rows))


if __name__ == "__main__":
    main()
