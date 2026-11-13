"""Live demo (Colab): ask a question, get an answer, see every claim checked against the retrieved text.

Tier 1 is the fine-tuned XLM-R verifier (models/verifier_xhard). Claims whose support probability lies within
MARGIN of the threshold are uncertain; with the box ticked they go to tier 2, the Qwen2.5-7B judge.
Thresholds are tuned on the dev split from outputs/verifier_scores_dot3.jsonl, as in s10.

  python s16_live.py    ->  prints a public Gradio link
"""

import html
import json
import os

os.environ.setdefault("VIKAG_CPU", "0")

import gradio as gr  # noqa: E402
import torch  # noqa: E402
from transformers import AutoModelForSequenceClassification, AutoTokenizer  # noqa: E402
from vihermes.graph import SQLiteGraph  # noqa: E402
from vihermes.retrieval import HybridRetriever, NumpyDenseIndex, units  # noqa: E402

from common import BIG_MODEL, DENSE_INDEX, GEN_MODEL, GRAPH_DB, OUT, ROOT, OllamaEmbedder, chat, chat_json, read_jsonl  # noqa: E402
from rules import overlap  # noqa: E402
from s1_answer import SYSTEM, format_context, passage, take_budget  # noqa: E402
from s2_claims import FEWSHOT, SYSTEM as SPLIT_SYSTEM, clean  # noqa: E402
from s4_judges import JUDGE  # noqa: E402
from s5_verifier import MAX_LEN, head_ids, premises  # noqa: E402
from s10_dot2 import GRID, decide, macro_f1  # noqa: E402

MODEL_DIR = os.environ.get("VIKAG_LIVE_MODEL", str(ROOT / "models" / "verifier_xhard"))
NAME = os.environ.get("VIKAG_LIVE_NAME", "xhard_v1")
MARGIN = 0.15
VI = {"supported": ("Có căn cứ", "#22744f", "#e1f1e8"), "contradicted": ("Mâu thuẫn", "#b4432f", "#f8e4df"),
      "unsupported": ("Không có căn cứ", "#9a6a08", "#f8eed2")}


def thresholds():
    pre = json.load(open(OUT / "prelabels.json", encoding="utf-8"))
    split = {r["qid"]: r["split"] for r in read_jsonl(OUT / "sample.jsonl")}
    rows = {r["cid"]: r for r in read_jsonl(OUT / "verifier_scores_dot3.jsonl")}
    dev = [k for k in rows if k in pre and not pre[k]["bad"] and split.get(rows[k]["cid"].split("|")[0]) == "dev" and NAME in rows[k]]
    y = [pre[k]["label"] for k in dev]
    return max(((a, b) for a in GRID for b in GRID),
               key=lambda t: macro_f1(y, [decide(rows[k][NAME]["entail"], rows[k][NAME]["contra"], *t) for k in dev]))


graph = SQLiteGraph(GRAPH_DB)
embedder = OllamaEmbedder()
retriever = HybridRetriever(graph, NumpyDenseIndex(units(graph), embedder, DENSE_INDEX), weight=0.5)
tok = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR, torch_dtype=torch.float32).to("cuda").eval()
IDS = head_ids(model)
TS, TC = thresholds()
print("thresholds", TS, TC, flush=True)


def verify(claim, pool):
    prem = premises(pool, False)
    probs = []
    with torch.no_grad():
        for i in range(0, len(prem), 8):
            enc = tok(prem[i:i + 8], [claim] * len(prem[i:i + 8]), truncation="longest_first", max_length=MAX_LEN, padding=True, return_tensors="pt").to("cuda")
            probs += model(**enc).logits.softmax(-1).tolist()
    best = max(range(len(prem)), key=lambda i: probs[i][IDS["supported"]])
    relevant = sorted(range(len(prem)), key=lambda i: -overlap(claim, prem[i]))[:2]
    entail, contra = probs[best][IDS["supported"]], max(probs[i][IDS["contradicted"]] for i in relevant)
    return entail, contra, prem[max(relevant[:1] + [best], key=lambda i: overlap(claim, prem[i]))]


def judge(claim, pool):
    context = "\n\n".join(f"[{i}] Văn bản: {p['title']}\n{p['text'][:2500]}" for i, p in enumerate(pool, 1))
    out = chat_json(f"BẰNG CHỨNG:\n{context}\n\nMỆNH ĐỀ:\n1. {claim}", JUDGE, BIG_MODEL, num_predict=120, num_ctx=8192).get("labels", [])
    lab = str(out[0].get("label", "")).lower() if out and isinstance(out[0], dict) else ""
    return lab if lab in VI else None


def analyse(question, use_judge=True):
    """The whole live pipeline, as data: used by the Gradio page and by s22_record.py."""
    pool = [passage(n) for n in take_budget([e.node for e in retriever.seeds(question, k=8)])]  # same budget as Naive RAG
    answer = chat(f"NGỮ CẢNH:\n{format_context(pool)}\n\nCÂU HỎI: {question}", SYSTEM, GEN_MODEL, num_predict=400, num_ctx=4096)
    claims = clean(chat_json(f"{FEWSHOT}\nCÂU HỎI: {question}\nCÂU TRẢ LỜI: {answer}\nJSON:", SPLIT_SYSTEM, GEN_MODEL, num_predict=600).get("claims", []))
    rows = []
    for c in claims:
        e, k, window = verify(c, pool)
        label, tier = decide(e, k, TS, TC), "Máy so khớp"
        if use_judge and abs(e - TS) < MARGIN:
            j = judge(c, pool)
            if j:
                label, tier = j, "Giám khảo 7B (máy so khớp chưa chắc)"
        rows.append({"claim": c, "label": label, "by": tier, "p": round(e, 3), "evidence": window[:900]})
    return {"question": question, "answer": answer, "claims": rows, "sources": [p["title"][:160] for p in pool]}


def run(question, use_judge):
    if not question.strip():
        return "<p>Nhập một câu hỏi.</p>"
    a = analyse(question, use_judge)
    answer, claims, pool = a["answer"], a["claims"], a["sources"]
    rows, n_judge = [], sum(x["by"] != "Máy so khớp" for x in a["claims"])
    for x in claims:
        c, label, tier, e, window = x["claim"], x["label"], x["by"], x["p"], x["evidence"]
        name, fg, bg = VI[label]
        rows.append(f"""<div style="border:1px solid #d7e0e1;border-radius:10px;padding:10px 12px;margin:8px 0">
<div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap"><b>{html.escape(c)}</b>
<span style="background:{bg};color:{fg};border-radius:999px;padding:2px 10px;font-weight:600;white-space:nowrap">{name}</span></div>
<div style="font-size:13px;color:#56656c">Quyết định bởi: {tier} · P(có căn cứ) = {e:.2f}</div>
<details><summary style="cursor:pointer;color:#0e5e6f;font-size:13px">Đoạn văn bản gần nhất</summary>
<div style="font-size:13px;white-space:pre-wrap;background:#f6f8f8;padding:8px;border-radius:6px">{html.escape(window[:900])}</div></details></div>""")
    counts = {k: sum(VI[k][0] in r for r in rows) for k in VI}
    head = (f"<h3>Câu trả lời</h3><p style='background:#edf2f2;padding:10px 12px;border-radius:8px'>{html.escape(answer)}</p>"
            f"<h3>{len(claims)} ý: {counts['supported']} có căn cứ · {counts['contradicted']} mâu thuẫn · {counts['unsupported']} không có căn cứ</h3>"
            f"<p style='font-size:13px;color:#56656c'>{n_judge} ý được chuyển sang giám khảo 7B. Kết quả của máy chỉ để tham khảo.</p>")
    sources = "".join(f"<li>{html.escape(t[:140])}</li>" for t in pool)
    return head + "".join(rows) + f"<h3>Văn bản đã truy xuất</h3><ol style='font-size:13px'>{sources}</ol>"


EXAMPLES = [["Công ty TNHH Fine Việt Nam được phép quảng cáo trên những nền tảng mạng xã hội và thương mại điện tử nào?", True],
            ["Thông tư hướng dẫn phương pháp chế biến dược liệu và vị thuốc cổ truyền có hiệu lực từ ngày nào?", True],
            ["Phòng ban nào thuộc Cục Dân số có chức năng liên quan đến thanh tra, xử lý vi phạm pháp luật?", False]]
if __name__ == "__main__":
  demo = gr.Interface(fn=run, inputs=[gr.Textbox(label="Câu hỏi về văn bản pháp quy y tế", lines=2), gr.Checkbox(value=True, label="Gửi ý chưa chắc sang giám khảo 7B (máy chấm hai tầng)")],
                    outputs=gr.HTML(), examples=EXAMPLES, title="ViKAG-Faith: kiểm chứng từng ý của câu trả lời",
                    description="Chatbot trả lời từ văn bản ViHERMES; mỗi ý được máy so khớp XLM-R kiểm tra, ý chưa chắc chuyển sang Qwen2.5-7B.")
  demo.launch(share=True)
