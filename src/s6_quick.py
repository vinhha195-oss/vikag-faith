"""Quick blind check (pass G): 30 random claims, one per screen, with only the evidence sentences that share
the most words with the claim (the full passages stay one click away). No suggestions, no system names.

  python s6_quick.py        ->  outputs/annotation/annotate_G.html  (export: vifaith_labels_G.json)
  python s6_quick.py H      ->  pass H: 30 further random claims, none already labelled in passes C, G

Made because the full page (pass F) was too hard to use; s7 reports these labels as an extra audit sample,
separately from pass C, since the annotator saw short excerpts instead of whole passages.
"""

import json
import random
import re
import sys

from common import OUT, SEED, read_jsonl
from s6_annotation import audit_sample, opaque

N_CLAIMS, N_SENTENCES = 30, 4

PAGE = r"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kiểm tra nhanh 30 ý (lượt __PASS__)</title>
<style>
:root{--bg:#f6f8f8;--card:#fff;--ink:#16232a;--muted:#56656c;--line:#d7e0e1;--acc:#0e5e6f;--ok:#22744f;--bad:#b4432f;--warn:#9a6a08;--hl:#fff0a8}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 system-ui,"Segoe UI",sans-serif}
.wrap{max-width:760px;margin:0 auto;padding:20px 16px 40px;display:flex;flex-direction:column;gap:14px}
.bar{height:8px;background:var(--line);border-radius:4px;overflow:hidden}.bar i{display:block;height:100%;background:var(--acc)}
.top{display:flex;justify-content:space-between;align-items:center;font-size:14px;color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.lab{font-size:13px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.claim{font-size:21px;font-weight:600;line-height:1.45}
.q{font-size:14px;color:var(--muted)}
.sent{border-left:3px solid var(--line);padding:6px 12px;margin:8px 0;font-size:16px}
.sent .t{display:block;font-size:12.5px;color:var(--muted)}
mark{background:var(--hl);border-radius:2px;padding:0 1px}
details summary{cursor:pointer;color:var(--acc);font-size:14.5px;margin-top:6px}
.full{white-space:pre-wrap;font-size:14px;max-height:300px;overflow:auto;background:var(--bg);border-radius:6px;padding:8px 10px;margin-top:6px}
.btns{display:grid;gap:10px}
.btns button{font:600 17px system-ui,sans-serif;border-radius:10px;padding:14px 16px;cursor:pointer;text-align:left;border:2px solid var(--line);background:var(--card);color:var(--ink)}
.btns button small{display:block;font-weight:400;font-size:13.5px;color:var(--muted)}
.btns button.sel{border-color:var(--acc);background:#dcebee}
.b1{border-left:8px solid var(--ok)!important}.b2{border-left:8px solid var(--bad)!important}.b3{border-left:8px solid var(--warn)!important}
.row{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center}
.link{background:none;border:none;color:var(--muted);font-size:14px;cursor:pointer;text-decoration:underline;padding:0}
.nav button{font:600 15px system-ui;border:1px solid var(--line);background:var(--card);border-radius:8px;padding:8px 14px;cursor:pointer}
.done{text-align:center}.done button{font:700 18px system-ui;background:var(--acc);color:#fff;border:none;border-radius:10px;padding:14px 22px;cursor:pointer}
button:focus-visible{outline:3px solid var(--acc);outline-offset:2px}
</style></head><body><div class="wrap" id="app"></div>
<script>
const DATA = __DATA__;
const KEY = "vifaith-__PASS__";
let st = {};
try { st = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
let i = Math.min(st._i || 0, DATA.length);
const save = () => { st._i = i; try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {} };
const esc = (s) => s.replace(/[&<>]/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;"}[c]));
const words = (s) => new Set((s.toLowerCase().match(/[\p{L}\p{N}]+/gu) || []).filter((w) => w.length > 2 || /\d/.test(w)));
const hl = (text, claim) => { const w = words(claim); return esc(text).replace(/[\p{L}\p{N}]+/gu, (t) => w.has(t.toLowerCase()) ? `<mark>${t}</mark>` : t); };
const OPTS = [["supported", "Văn bản nói đúng như vậy", "có câu cùng ý, kể cả khi khác chữ", "b1"],
              ["contradicted", "Văn bản nói khác", "số, ngày, tên cơ quan khác, hoặc nói ngược lại", "b2"],
              ["unsupported", "Văn bản không nhắc tới", "tìm không thấy trong các câu bên trên", "b3"]];
const nDone = () => DATA.filter((d) => st[d.cid] && (st[d.cid].label || st[d.cid].bad)).length;
function pick(label, bad) {
  const d = DATA[i]; const r = st[d.cid] || {};
  st[d.cid] = {...r, label: bad ? "" : label, bad: !!bad, confirmed: true, t: Date.now()};
  i++; save(); render(); window.scrollTo(0, 0);
}
function render() {
  const app = document.getElementById("app"), n = nDone();
  const head = `<div class="top"><span>Đã làm ${n}/${DATA.length}</span><span>${n > 0 && i < DATA.length ? `<button class="link" onclick="exportJson()">Lưu tạm (làm dở)</button> · ` : ""}${i > 0 ? `<button class="link" onclick="i--;save();render()">← Ý trước</button>` : ""}</span></div>
    <div class="bar"><i style="width:${100 * n / DATA.length}%"></i></div>`;
  if (i >= DATA.length) {
    app.innerHTML = head + `<div class="card done"><p style="font-size:20px;font-weight:600">Xong ${n}/${DATA.length} ý. Cảm ơn bạn!</p>
      <p>Bấm nút dưới để lưu kết quả (file <b>vifaith_labels___PASS__.json</b> vào thư mục Downloads).</p>
      <button id="exp">Lưu kết quả</button><p style="font-size:14px;color:var(--muted)">Muốn sửa ý nào thì bấm “← Ý trước”.</p></div>`;
    document.getElementById("exp").onclick = exportJson; return;
  }
  const d = DATA[i], r = st[d.cid] || {};
  const sents = d.sents.map((s) => `<div class="sent"><span class="t">${esc(s.title)}</span>${hl(s.text, d.claim)}</div>`).join("");
  const full = d.full.map((p) => `<p style="font-weight:600;font-size:13.5px;margin:8px 0 0">${esc(p.title)}</p><div class="full">${hl(p.text, d.claim)}</div>`).join("");
  app.innerHTML = head + `
   <div class="card"><div class="lab">Ý ${i + 1} cần kiểm tra</div><div class="claim">${esc(d.claim)}</div>
     <p class="q">Trích từ câu trả lời cho câu hỏi: ${esc(d.question)}</p></div>
   <div class="card"><div class="lab">Văn bản gốc (các câu liên quan nhất, từ trùng được tô vàng)</div>${sents}
     <details id="more"><summary>Không thấy? Xem toàn bộ văn bản</summary>${full}</details></div>
   <div class="btns">${OPTS.map(([v, t, s, c], k) => `<button class="${c}${r.label === v ? " sel" : ""}" onclick="pick('${v}')">${k + 1}. ${t}<small>${s}</small></button>`).join("")}</div>
   <div class="row"><button class="link" onclick="pick('',true)">Ý này khó hiểu, không đọc ra nghĩa (bỏ qua)</button></div>`;
  document.getElementById("more").ontoggle = (e) => { st[d.cid] = {...(st[d.cid] || {}), expanded: true}; save(); };
}
function exportJson() {
  const out = {mode: "__PASS__", exported: new Date().toISOString(), labels: {}};
  DATA.forEach((d) => { const r = st[d.cid]; if (r) out.labels[d.cid] = {label: r.label || "", bad: !!r.bad, confirmed: !!r.confirmed, t: r.t || null, expanded: !!r.expanded, evidence: "", note: ""}; });
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(out, null, 1)], {type: "application/json"}));
  a.download = "vifaith_labels___PASS__.json"; a.click();
}
document.addEventListener("keydown", (e) => { const k = {"1": "supported", "2": "contradicted", "3": "unsupported"}[e.key]; if (k && i < DATA.length) pick(k); });
render();
</script></body></html>"""


def words(s):
    return {w for w in re.findall(r"\w+", s.lower()) if len(w) > 2 or any(ch.isdigit() for ch in w)}


def best_sentences(claim, pool):
    cw = words(claim)
    cands = []
    for p in pool:
        for s in re.split(r"(?<=[.;:])\s+|\n+", p["text"]):
            s = " ".join(s.split())
            if 25 <= len(s):
                cands.append((len(cw & words(s)), -len(s), p["title"], s[:420]))
    cands.sort(reverse=True)
    return [{"title": t, "text": s} for _, _, t, s in cands[:N_SENTENCES]]


QUICK_PASSES = "GHIJ"  # each later pass skips every claim labelled in an earlier one


def labelled(passes):
    ids = json.load(open(OUT / "annotation" / "id_map.json", encoding="utf-8"))
    done = set()
    for name in passes:
        path = OUT / "annotation" / f"vifaith_labels_{name}.json"
        if path.exists():
            done |= {ids[k] for k in json.load(open(path, encoding="utf-8"))["labels"] if k in ids}
    return done


def main(name="G"):
    assert name in QUICK_PASSES, f"pass must be one of {QUICK_PASSES}"
    pre = json.load(open(OUT / "prelabels.json", encoding="utf-8"))
    sample = {r["qid"] for r in read_jsonl(OUT / "sample.jsonl")}
    answers = {(a["qid"], a["system"]): a for a in read_jsonl(OUT / "answers.jsonl")}
    pools = {(p["qid"], p["system"]): p["pool"] for p in read_jsonl(OUT / "pools.jsonl")}
    taken = audit_sample(pre) | labelled("C" + QUICK_PASSES[:QUICK_PASSES.index(name)])
    claims = [c for c in read_jsonl(OUT / "claims.jsonl") if c["qid"] in sample and c["cid"] not in taken]
    # Pass G keeps its original draw (seed + 3); later passes draw from what is left.
    chosen = random.Random(SEED + 3 + QUICK_PASSES.index(name)).sample(claims, min(N_CLAIMS, len(claims)))
    items = []
    for c in chosen:
        key = (c["qid"], c["system"])
        items.append({"cid": opaque(c["cid"]), "claim": c["claim"], "question": answers[key]["question"],
                      "sents": best_sentences(c["claim"], pools[key]),
                      "full": [{"title": p["title"], "text": p["text"]} for p in pools[key]]})
    out = OUT / "annotation" / f"annotate_{name}.html"
    out.write_text(PAGE.replace("__DATA__", json.dumps(items, ensure_ascii=False)).replace("__PASS__", name), encoding="utf-8")
    print(out, len(items), "claims")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "G")
