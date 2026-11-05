"""Package the ViFaithKAG pilot dataset into dataset/ViFaithKAG: claims with labels, answers, evidence passages.

Everything comes from outputs/. Labels keep their provenance: `silver_label` is Claude's, `human_label` exists only
for the 60 claims of the blind audit. Passage texts are from ViHERMES (MIT), credited in the README.
"""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
DST = ROOT / "dataset" / "ViFaithKAG"
R = lambda f: [json.loads(l) for l in open(OUT / f, encoding="utf-8")]  # noqa: E731
W = lambda f, rows: open(DST / f, "w", encoding="utf-8").writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)  # noqa: E731

res = json.load(open(OUT / "analysis" / "results.json", encoding="utf-8"))
sample = {r["qid"]: r["split"] for r in R("sample.jsonl")}
answers = {(a["qid"], a["system"]): a for a in R("answers.jsonl") if a["qid"] in sample}
pools = {(p["qid"], p["system"]): p["pool"] for p in R("pools.jsonl")}
pre = json.load(open(OUT / "prelabels.json", encoding="utf-8"))
ids = json.load(open(OUT / "annotation" / "id_map.json", encoding="utf-8"))
audit, audit_pass = {}, {}  # blind human labels: pass C (full passages) and pass G (quick excerpts)
for name in ("C", "G", "H", "I", "J"):
    path = OUT / "annotation" / f"vifaith_labels_{name}.json"
    if path.exists():
        for k, v in json.load(open(path, encoding="utf-8"))["labels"].items():
            if v.get("label"):
                audit[ids[k]], audit_pass[ids[k]] = v["label"], name
scores = {r["cid"]: r for r in R("verifier_scores.jsonl")}
selfcheck = {r["cid"]: r for r in R("selfcheck_scores.jsonl")}
revise = {(r["qid"], r["system"]): r["rounds"] for r in R("revise.jsonl")}
judges = {}
for j in R("judges.jsonl"):
    judges.setdefault((j["qid"], j["system"]), {})[j["model"]] = j

licence = (DST / "LICENSE_ViHERMES").read_bytes() if (DST / "LICENSE_ViHERMES").exists() else (ROOT / "external" / "ViHERMES" / "LICENSE").read_bytes()
if DST.exists():
    shutil.rmtree(DST)
DST.mkdir(parents=True)
(DST / "LICENSE_ViHERMES").write_bytes(licence)

claims = []
for c in R("claims.jsonl"):
    if c["qid"] not in sample:
        continue
    k, key = c["cid"], (c["qid"], c["system"])
    jg = judges.get(key, {})
    claims.append({
        "cid": k, "qid": c["qid"], "system": c["system"], "hop": c["hop"], "split": sample[c["qid"]],
        "claim": c["claim"], "malformed": pre[k]["bad"], "silver_label": pre[k]["label"], "silver_note": pre[k]["note"],
        "human_label": audit.get(k), "human_pass": audit_pass.get(k),
        "judge_7b": jg.get("qwen2.5:7b", {}).get("judge", {}).get(k), "judge_3b": jg.get("qwen2.5:3b", {}).get("judge", {}).get(k),
        "nli": {v: {"entail": round(s["entail"], 4), "contra": round(s["contra"], 4)}
                for v, s in scores[k].items() if v != "cid"},
        "selfcheck": {x: round(selfcheck[k][x], 4) for x in ("entail", "contra")} if k in selfcheck else None,
    })
W("claims.jsonl", claims)

rows, passages = [], {}
for key, a in sorted(answers.items()):
    for p in pools[key]:
        passages[p["id"]] = {"id": p["id"], "title": p["title"], "text": p["text"], "graph_facts": p["facts"]}
    jg = judges.get(key, {})
    rounds = revise.get(key) or []
    rows.append({
        "qid": a["qid"], "system": a["system"], "hop": a["hop"], "split": sample[a["qid"]], "question": a["question"],
        "gold_answer": a["gold_answer"], "gold_passage_ids": a["gold_ids"], "answer": a["answer"],
        "retrieved_ids": [p["id"] for p in a["retrieved"]], "relations": a["relations"],
        "evidence_ids": [p["id"] for p in pools[key]],
        "ragas_7b": jg.get("qwen2.5:7b", {}).get("ragas", {}).get("score"), "ragas_3b": jg.get("qwen2.5:3b", {}).get("ragas", {}).get("score"),
        "revised": rounds,
    })
W("answers.jsonl", rows)
W("passages.jsonl", sorted(passages.values(), key=lambda p: p["id"]))
json.dump({"thresholds_tuned_on_dev_silver": res["thresholds"]}, open(DST / "thresholds.json", "w", encoding="utf-8"), indent=1)

n_h = sum(c["human_label"] is not None and not c["malformed"] for c in claims)
n_h_bad = sum(c["human_label"] is not None and c["malformed"] for c in claims)
cg = res["agreement"].get("audit_CG", res["agreement"]["audit"])
pct_h, kappa_h = f"{100 * cg['acc']:.0f}%", f"{cg['kappa']:.2f}".replace(".", ",")
(DST / "README.md").write_text(f"""# ViFaithKAG (pilot)

Bộ dữ liệu đánh giá tính trung thực mức mệnh đề (claim) cho hỏi đáp RAG/GraphRAG tiếng Việt trên văn bản pháp quy
y tế, xây trong đề tài ViKAG-Faith. Quy mô pilot: 40 câu hỏi ViHERMES (8 câu mỗi mức 1–5 hop) × 2 hệ
(Naive RAG, GraphRAG) = {len(rows)} câu trả lời, {len(claims)} claim, {len(passages)} đoạn bằng chứng.

## Nguồn nhãn (đọc trước khi dùng)

- `silver_label`: do **Claude (Anthropic) gán** cho mọi claim, kèm lý do `silver_note`. Đây **không phải nhãn người**.
- `human_label`: có ở **{n_h} claim** hợp lệ (thêm {n_h_bad} claim tách hỏng cũng có nhãn nhưng không tính) của các lượt kiểm định mù do 1 người gán, không thấy nhãn Claude, không biết hệ
  (`human_pass`: `C` = 60 claim phân tầng, xem toàn đoạn văn; `G`, `H`, `I`, `J` = mỗi lượt 30 claim ngẫu nhiên, xem câu trích, một số bị bỏ qua).
  Gộp các lượt, Claude trùng với người {pct_h}, Cohen's κ = {kappa_h}: Claude khắt khe hơn người.
- `malformed = true`: claim bị tách hỏng, đã loại khỏi mọi phép đo.

## Tệp

| Tệp | Nội dung |
|---|---|
| `claims.jsonl` | Một dòng mỗi claim: nhãn silver/người, nhãn LLM-judge Qwen2.5-7B/3B, xác suất NLI (`zs_*` zero-shot, `ft_*` fine-tune, `nosynth_*` fine-tune chỉ ViNLI; `v1` đoạn văn, `v2` + thông tin graph), điểm SelfCheckGPT |
| `answers.jsonl` | Câu hỏi, đáp án ViHERMES, câu trả lời của hệ, id đoạn truy xuất / bằng chứng, điểm RAGAS, các vòng verify-then-revise |
| `passages.jsonl` | Đoạn bằng chứng (văn bản ViHERMES) kèm thông tin lấy từ graph |
| `thresholds.json` | Ngưỡng entail/contra của từng biến thể NLI, chọn trên tập dev theo nhãn silver |

`split`: 20% câu hỏi là `dev` (chọn ngưỡng), còn lại là `test`. Nhãn: `supported`, `contradicted`, `unsupported`.

## Giấy phép và ghi nguồn

- Câu hỏi, đáp án, đoạn văn bản và graph lấy từ **ViHERMES** (Nguyen và cs., ACIIDS 2026; github.com/ura-hcmut/ViHERMES),
  giấy phép **MIT**. Bản quyền của phần đó thuộc các tác giả ViHERMES; văn bản quy phạm pháp luật gốc thuộc phạm vi công cộng.
- Câu trả lời do Qwen2.5-3B-Instruct sinh; nhãn silver do Claude gán; các điểm tự động do Qwen2.5 và mDeBERTa-v3-base-xnli tính.
- Phần do đề tài tạo ra (claim, nhãn, điểm) phát hành theo MIT, giữ nguyên thông báo bản quyền của ViHERMES.

Chi tiết phương pháp và kết quả: `nop_bai/ViKAG-Faith_BaiBao.docx`.
""", encoding="utf-8")
print(DST, len(claims), "claims", len(rows), "answers", len(passages), "passages", n_h, "human labels")
