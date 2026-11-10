"""Local checking demo that runs on this PC without any LLM.

Paste a question and an answer (or pick one of the 80 sampled answers). The app retrieves passages from the
ViHERMES corpus with TF-IDF, splits the answer into sentences, and checks each sentence with the fine-tuned
mDeBERTa verifier. For a sampled answer it uses that answer's evidence pool and extracted claims instead, and
also shows Claude's silver label for comparison.

  python s17_check_app.py      ->  open http://127.0.0.1:8765
Uses only the standard library server; VIKAG_CPU=0 runs the verifier on the GPU.
"""

import csv
import html
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from common import DATA, OUT, ROOT, USE_CPU, read_jsonl
from rules import overlap
from s5_verifier import MAX_LEN, head_ids, premises
from s10_dot2 import GRID, decide, macro_f1

TAG = os.environ.get("VIKAG_APP_MODEL", "fthard" if (ROOT / "models" / "verifier_fthard" / "config.json").exists() else "ft20")
MODEL_DIR = ROOT / "models" / f"verifier_{TAG}"
SCORES = {"fthard": "verifier_scores_dot3.jsonl", "ft20": "verifier_scores_dot2.jsonl"}[TAG]
DEV = "cpu" if USE_CPU or not torch.cuda.is_available() else "cuda"
torch.set_num_threads(2)
VI = {"supported": ("Có căn cứ", "ok"), "contradicted": ("Mâu thuẫn", "bad"), "unsupported": ("Không có căn cứ", "warn")}


def thresholds(name):
    pre = json.load(open(OUT / "prelabels.json", encoding="utf-8"))
    split = {r["qid"]: r["split"] for r in read_jsonl(OUT / "sample.jsonl")}
    rows = {r["cid"]: r for r in read_jsonl(OUT / SCORES) if name in r}
    dev = [k for k in rows if k in pre and not pre[k]["bad"] and split.get(k.split("|")[0]) == "dev"]
    y = [pre[k]["label"] for k in dev]
    return max(((a, b) for a in GRID for b in GRID), key=lambda t: macro_f1(y, [decide(rows[k][name]["entail"], rows[k][name]["contra"], *t) for k in dev]))


ctx = list(csv.DictReader(open(DATA / "contexts.csv", encoding="utf-8")))
vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)
mat = vec.fit_transform([r["title"] + " " + r["text"] for r in ctx])
tok = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR, torch_dtype=torch.float32).to(DEV).eval()
IDS = head_ids(model)
TS, TC = thresholds(f"{TAG}_v1")
pre = json.load(open(OUT / "prelabels.json", encoding="utf-8"))
pools = {(p["qid"], p["system"]): p["pool"] for p in read_jsonl(OUT / "pools.jsonl")}
in_sample = {r["qid"] for r in read_jsonl(OUT / "sample.jsonl")}
answers = {(a["qid"], a["system"]): a for a in read_jsonl(OUT / "answers.jsonl") if (a["qid"], a["system"]) in pools and a["qid"] in in_sample}
claims_by = {}
for c in read_jsonl(OUT / "claims.jsonl"):
    claims_by.setdefault((c["qid"], c["system"]), []).append(c)
SAMPLES = sorted([k for k in answers if k in claims_by], key=lambda k: (int(answers[k]["hop"]), k))
print(f"model {TAG} on {DEV}, thresholds {TS} {TC}, {len(SAMPLES)} sampled answers", flush=True)


def retrieve(text, k=5):
    sims = linear_kernel(vec.transform([text]), mat).ravel()
    return [{"id": ctx[i]["context_id"], "title": ctx[i]["title"], "text": ctx[i]["text"], "facts": []} for i in sims.argsort()[::-1][:k]]


def sentences(answer):
    parts = re.split(r"(?<=[.;!?])\s+|\n+", answer)
    return [p.strip() for p in parts if len(p.strip()) >= 15]


def check(claim, pool):
    prem = premises(pool, False)
    probs = []
    with torch.no_grad():
        for i in range(0, len(prem), 8):
            enc = tok(prem[i:i + 8], [claim] * len(prem[i:i + 8]), truncation="longest_first", max_length=MAX_LEN, padding=True, return_tensors="pt").to(DEV)
            probs += model(**enc).logits.softmax(-1).tolist()
    relevant = sorted(range(len(prem)), key=lambda i: -overlap(claim, prem[i]))[:2]
    e, c = max(p[IDS["supported"]] for p in probs), max(probs[i][IDS["contradicted"]] for i in relevant)
    best = max(range(len(prem)), key=lambda i: probs[i][IDS["supported"]] if e >= TS else -overlap(claim, prem[i]))
    return decide(e, c, TS, TC), e, prem[best]


def run(req):
    if req.get("sample") not in (None, ""):
        key = SAMPLES[int(req["sample"])]
        pool, question, answer = pools[key], answers[key]["question"], answers[key]["answer"]
        items = [(c["claim"], pre.get(c["cid"], {})) for c in claims_by[key]]
        items = [(t, p.get("label") if not p.get("bad") else None) for t, p in items]
    else:
        question, answer = req.get("question", ""), req.get("answer", "")
        pool = retrieve(question + " " + answer)
        items = [(s, None) for s in sentences(answer)]
    rows = []
    for text, silver in items:
        label, e, window = check(text, pool)
        rows.append({"claim": text, "label": label, "p": round(e, 3), "silver": silver, "evidence": window[:900]})
    return {"question": question, "answer": answer, "rows": rows, "sources": [p["title"][:160] for p in pool], "model": TAG}


PAGE = r"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kiểm chứng câu trả lời</title><style>
:root{--bg:#f6f8f8;--card:#fff;--ink:#16232a;--muted:#56656c;--line:#d7e0e1;--acc:#0e5e6f;--ok:#22744f;--okb:#e1f1e8;--bad:#b4432f;--badb:#f8e4df;--warn:#9a6a08;--warnb:#f8eed2}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,"Segoe UI",sans-serif}.wrap{max-width:860px;margin:0 auto;padding:24px 16px 48px;display:flex;flex-direction:column;gap:14px}
h1{font-size:26px;margin:0}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
textarea,select{width:100%;box-sizing:border-box;font:15px system-ui;border:1px solid var(--line);border-radius:8px;padding:8px}
button{font:600 15px system-ui;background:var(--acc);color:#fff;border:0;border-radius:8px;padding:9px 16px;cursor:pointer}
.row{border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:8px 0}.top{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
.chip{border-radius:999px;padding:2px 10px;font-weight:600;font-size:13px;white-space:nowrap}.ok{background:var(--okb);color:var(--ok)}.bad{background:var(--badb);color:var(--bad)}.warn{background:var(--warnb);color:var(--warn)}
.small{font-size:13px;color:var(--muted)}pre{white-space:pre-wrap;font:13px system-ui;background:var(--bg);padding:8px;border-radius:6px}
</style></head><body><div class="wrap"><h1>Kiểm chứng từng ý của câu trả lời</h1>
<p class="small">Máy so khớp mDeBERTa (đã luyện với dữ liệu lỗi sát thực tế) chạy trên máy này. Kết quả chỉ để tham khảo.</p>
<div class="card"><b>Cách 1. Chọn một câu trả lời trong mẫu 80</b><select id="sample"><option value="">— chọn —</option>__OPTIONS__</select>
<p class="small">Dùng đúng bằng chứng và các ý đã tách của mẫu; hiện thêm nhãn của Claude để so.</p><button onclick="go(true)">Kiểm chứng</button></div>
<div class="card"><b>Cách 2. Dán câu hỏi và câu trả lời bất kỳ</b><textarea id="q" rows="2" placeholder="Câu hỏi"></textarea><textarea id="a" rows="4" placeholder="Câu trả lời cần kiểm chứng" style="margin-top:8px"></textarea>
<p class="small">Máy tự tìm 5 đoạn văn bản liên quan nhất trong kho ViHERMES và tách câu trả lời theo câu.</p><button onclick="go(false)">Kiểm chứng</button></div>
<div id="out"></div></div><script>
const VI={supported:["Có căn cứ","ok"],contradicted:["Mâu thuẫn","bad"],unsupported:["Không có căn cứ","warn"]};
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
async function go(fromSample){const out=document.getElementById("out");out.innerHTML='<div class="card">Đang kiểm chứng…</div>';
 const body=fromSample?{sample:document.getElementById("sample").value}:{question:document.getElementById("q").value,answer:document.getElementById("a").value};
 if(fromSample&&body.sample===""){out.innerHTML='<div class="card">Hãy chọn một câu trả lời.</div>';return}
 const r=await (await fetch("/api/check",{method:"POST",body:JSON.stringify(body)})).json();
 const n=k=>r.rows.filter(x=>x.label===k).length;
 out.innerHTML=`<div class="card"><p class="small">Câu hỏi</p><p>${esc(r.question)}</p><p class="small">Câu trả lời</p><p>${esc(r.answer)}</p>
 <b>${r.rows.length} ý: ${n("supported")} có căn cứ · ${n("contradicted")} mâu thuẫn · ${n("unsupported")} không có căn cứ</b>
 ${r.rows.map(x=>`<div class="row"><div class="top"><span>${esc(x.claim)}</span><span class="chip ${VI[x.label][1]}">${VI[x.label][0]}</span></div>
 <div class="small">P(có căn cứ) = ${x.p}${x.silver?` · nhãn Claude: ${VI[x.silver][0]}`:""}</div>
 <details><summary class="small">Đoạn văn bản dùng để so</summary><pre>${esc(x.evidence)}</pre></details></div>`).join("")}
 <p class="small">Văn bản dùng làm bằng chứng:</p><ol class="small">${r.sources.map(s=>`<li>${esc(s)}</li>`).join("")}</ol></div>`;}
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        data = body.encode("utf-8")
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        opts = "".join(f'<option value="{i}">[{answers[k]["hop"]} hop · {"Naive" if k[1] == "naive" else "Graph"}] {html.escape(answers[k]["question"][:100])}</option>' for i, k in enumerate(SAMPLES))
        self._send(200, PAGE.replace("__OPTIONS__", opts), "text/html; charset=utf-8")

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        try:
            self._send(200, json.dumps(run(req), ensure_ascii=False), "application/json")
        except Exception as e:  # show the error in the page rather than dropping the connection
            self._send(500, json.dumps({"question": "", "answer": f"Lỗi: {e}", "rows": [], "sources": []}, ensure_ascii=False), "application/json")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("open http://127.0.0.1:8765", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
