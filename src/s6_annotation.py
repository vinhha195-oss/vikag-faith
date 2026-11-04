"""Step 6: build the offline annotation page (outputs/annotation/annotate.html).

Annotators are blind to the system. Claude's pre-labels (outputs/prelabels.json) are pre-selected
and marked as suggestions; every change is saved in the browser and exported as JSON.
  python s6_annotation.py            # annotator A (corrects Claude's pre-labels)
  python s6_annotation.py --blank    # annotator B for the double-annotated subset, no pre-labels
  python s6_annotation.py --audit    # blind audit: 60 claims stratified by Claude label, no suggestions
  python s6_annotation.py --rest     # blind pass E: every sampled claim not in the audit, no suggestions
                                     # (pass D, same claims, was excluded: its export was not made through the page)
  python s6_annotation.py --rest100  # blind pass F: whole answers drawn at random until ~100 claims, no suggestions
"""

import hashlib
import json
import random
import sys

from common import OUT, SEED, read_jsonl

PAGE = r"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gán nhãn ViFaithKAG</title>
<style>
:root{--bg:#fafaf8;--card:#fff;--ink:#1d1d1b;--muted:#6b6b66;--line:#e2e1dc;--acc:#2b6cb0;--ok:#2f855a;--bad:#c53030;--warn:#b7791f}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,"Segoe UI",sans-serif}
header{position:sticky;top:0;background:var(--card);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;z-index:2}
header b{font-size:16px}.prog{color:var(--muted)}button{font:inherit;padding:6px 12px;border:1px solid var(--line);border-radius:6px;background:var(--card);cursor:pointer}
button.primary{background:var(--acc);color:#fff;border-color:var(--acc)}
main{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px;padding:16px;max-width:1400px;margin:auto}
@media(max-width:900px){main{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin-bottom:12px}
h3{margin:0 0 6px;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
.claim{border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:10px 0}
.claim.cur{border-color:var(--acc);box-shadow:0 0 0 2px #2b6cb033}
.claim .txt{font-weight:600;margin-bottom:6px}.opts{display:flex;gap:6px;flex-wrap:wrap}
.opts label{border:1px solid var(--line);border-radius:6px;padding:3px 10px;cursor:pointer}
.opts input{margin-right:4px}.sup{color:var(--ok)}.con{color:var(--bad)}.uns{color:var(--warn)}
.sugg{font-size:12px;color:var(--muted);margin-top:4px}.ev{margin-top:6px;font-size:13px;color:var(--muted)}
.ev input{width:5em}textarea{width:100%;font:inherit;font-size:13px;margin-top:6px;border:1px solid var(--line);border-radius:6px}
.pass{border-top:1px solid var(--line);padding:10px 0}.pass:first-child{border-top:0}
.ptitle{font-weight:600}.facts{font-size:12px;color:var(--muted);margin:2px 0 6px}.ptext{white-space:pre-wrap;font-size:14px}
.tag{font-size:11px;border-radius:4px;padding:1px 6px;margin-left:6px;background:#eef2f7;color:var(--muted)}
.guide{font-size:13px;color:var(--muted)}mark{background:#fff3b0}
</style></head><body>
<header><b>ViFaithKAG</b><span class="prog" id="prog"></span>
<button id="prev">← Trước</button><button id="next" class="primary">Tiếp →</button>
<select id="jump"></select><button id="export">Xuất kết quả (.json)</button>
<label class="guide"><input type="checkbox" id="hl" checked> tô sáng từ trùng</label></header>
<main><section><div class="card"><h3>Câu hỏi</h3><div id="q"></div></div>
<div class="card"><h3>Câu trả lời của hệ thống</h3><div id="a"></div></div>
<div class="card"><h3>Claim cần gán nhãn</h3><div class="guide">
<b class="sup">supported</b>: bằng chứng suy ra được claim ·
<b class="con">contradicted</b>: bằng chứng nói ngược lại (sai số, ngày, tên văn bản, phủ định) ·
<b class="uns">unsupported</b>: bằng chứng không đề cập / không đủ. Chỉ so với BẰNG CHỨNG bên phải, không dùng hiểu biết riêng.
Claim tách lỗi (không đứng độc lập, gộp nhiều ý) → đánh dấu "claim lỗi".</div><div id="claims"></div></div></section>
<section><div class="card"><h3>Bằng chứng (đánh số để ghi vào ô "đoạn")</h3><div id="pool"></div></div></section></main>
<script>
const DATA = __DATA__;
const MODE = "__MODE__";
const KEY = "vifaith-" + MODE;
let st = {};
try { st = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { st = {}; }
let idx = Math.min(+(st._idx || 0), DATA.length - 1), cur = 0;
const save = () => { st._idx = idx; try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {} };
const esc = s => s.replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
function words(s){ return new Set((s.toLowerCase().match(/[\p{L}\p{N}]+/gu)||[]).filter(w=>w.length>2)); }
function highlight(text, claim){
  if(!document.getElementById("hl").checked||!claim) return esc(text);
  const w = words(claim);
  return esc(text).replace(/[\p{L}\p{N}]+/gu, t => w.has(t.toLowerCase()) ? "<mark>"+t+"</mark>" : t);
}
function rec(cid, c){ if(!st[cid]) st[cid] = {label: MODE==="A" ? (c.pre||"") : "", evidence: MODE==="A" ? (c.pre_ev||"") : "", bad: MODE==="A" && !!c.pre_bad, note:"", touched:false}; return st[cid]; }
function done(){ let n=0,t=0; DATA.forEach(d=>d.claims.forEach(c=>{t++; const r=st[c.cid]; if(r&&r.label&&r.touched) n++;})); return [n,t]; }
function render(){
  const d = DATA[idx]; const [n,t] = done();
  document.getElementById("prog").textContent = `Câu ${idx+1}/${DATA.length} · đã xác nhận ${n}/${t} claim`;
  document.getElementById("q").textContent = d.question;
  document.getElementById("a").textContent = d.answer;
  const claimText = d.claims[cur] ? d.claims[cur].claim : "";
  document.getElementById("pool").innerHTML = d.pool.map((p,i)=>`<div class="pass"><div class="ptitle">[${i+1}] ${esc(p.title)}</div>
    <div class="facts">${p.facts.map(esc).join(" · ")}</div><div class="ptext">${highlight(p.text, claimText)}</div></div>`).join("");
  document.getElementById("claims").innerHTML = d.claims.map((c,i)=>{ const r = rec(c.cid,c);
    const opt = (v,cls)=>`<label class="${cls}"><input type="radio" name="l${i}" value="${v}" ${r.label===v?"checked":""}>${v}</label>`;
    return `<div class="claim ${i===cur?"cur":""}" data-i="${i}"><div class="txt">${i+1}. ${esc(c.claim)}</div>
      <div class="opts">${opt("supported","sup")}${opt("contradicted","con")}${opt("unsupported","uns")}
      <label><input type="checkbox" data-bad ${r.bad?"checked":""}>claim lỗi</label></div>
      ${MODE==="A"&&c.pre?`<div class="sugg">Gợi ý của Claude: <b>${c.pre}</b>${c.pre_note?" — "+esc(c.pre_note):""} ${r.touched?"· <b>đã xác nhận</b>":"· chưa xác nhận"}</div>`:""}
      <div class="ev">Đoạn bằng chứng (vd: 1,3): <input data-ev value="${esc(r.evidence||"")}"></div>
      <textarea rows="1" placeholder="Ghi chú (tuỳ chọn)" data-note>${esc(r.note||"")}</textarea></div>`; }).join("");
  document.querySelectorAll(".claim").forEach(el=>{ const i=+el.dataset.i, c=DATA[idx].claims[i], r=rec(c.cid,c);
    el.addEventListener("click",()=>{ if(cur!==i){cur=i; render();} });
    el.querySelectorAll("input[type=radio]").forEach(x=>x.addEventListener("change",()=>{r.label=x.value;r.touched=true;r.t=Date.now();save();render();}));
    el.querySelector("[data-bad]").addEventListener("change",e=>{r.bad=e.target.checked;r.touched=true;save();});
    el.querySelector("[data-ev]").addEventListener("change",e=>{r.evidence=e.target.value;r.touched=true;save();});
    el.querySelector("[data-note]").addEventListener("change",e=>{r.note=e.target.value;save();});
  });
  document.getElementById("jump").value = idx; save();
}
function go(k){ if(MODE!=="A" && k>0 && DATA[idx].claims.some(c=>!rec(c.cid,c).label) && !confirm("Trang này còn claim chưa chọn nhãn. Vẫn chuyển trang?")) return;
  if(MODE==="A") DATA[idx].claims.forEach(c=>{const r=rec(c.cid,c); if(r.label) r.touched=true;});
  idx=Math.max(0,Math.min(DATA.length-1,idx+k)); cur=0; render(); window.scrollTo(0,0); }
document.getElementById("next").onclick=()=>go(1); document.getElementById("prev").onclick=()=>go(-1);
document.getElementById("hl").onchange=render;
const j=document.getElementById("jump"); DATA.forEach((d,i)=>{const o=document.createElement("option");o.value=i;o.textContent="Câu "+(i+1);j.appendChild(o);});
j.onchange=()=>{idx=+j.value;cur=0;render();};
document.getElementById("export").onclick=()=>{ const out={mode:MODE,exported:new Date().toISOString(),labels:{}};
  DATA.forEach(d=>d.claims.forEach(c=>{const r=st[c.cid]; if(r) out.labels[c.cid]={label:r.label,evidence:r.evidence,bad:r.bad,note:r.note,confirmed:r.touched,t:r.t||null};}));
  const a=document.createElement("a"); a.href=URL.createObjectURL(new Blob([JSON.stringify(out,null,1)],{type:"application/json"}));
  a.download=`vifaith_labels_${MODE}.json`; a.click(); };
document.addEventListener("keydown",e=>{ if(e.target.tagName==="TEXTAREA"||e.target.tagName==="INPUT"&&e.target.type==="text") return;
  const c=DATA[idx].claims[cur]; if(!c) return; const r=rec(c.cid,c);
  const k={"1":"supported","2":"contradicted","3":"unsupported"}[e.key];
  if(k){r.label=k;r.touched=true;r.t=Date.now();save();render();}
  if(e.key==="j"){cur=Math.min(cur+1,DATA[idx].claims.length-1);render();}
  if(e.key==="k"){cur=Math.max(cur-1,0);render();}
  if(e.key==="ArrowRight")go(1); if(e.key==="ArrowLeft")go(-1); });
render();
</script></body></html>"""


def opaque(cid):
    """Claim IDs carry the system name; the page only sees an opaque ID (mapping kept aside)."""
    return hashlib.sha1(cid.encode()).hexdigest()[:12]


def audit_sample(pre, per_label={"supported": 30, "contradicted": 15, "unsupported": 15}):
    """Blind audit set: claims drawn per Claude label so agreement can be measured for every class."""
    rng = random.Random(SEED + 1)
    chosen = set()
    for label, n in per_label.items():
        pool = sorted(k for k, v in pre.items() if v["label"] == label and not v["bad"])
        chosen |= set(rng.sample(pool, min(n, len(pool))))
    return chosen


def main():
    blank = "--blank" in sys.argv
    audit = "--audit" in sys.argv
    rest = "--rest" in sys.argv
    rest100 = "--rest100" in sys.argv
    sample = read_jsonl(OUT / "sample.jsonl")
    keep = {r["qid"] for r in sample}
    if blank:  # annotator B: the dev questions only (double-annotated subset for kappa)
        keep = {r["qid"] for r in sample if r["split"] == "dev"}
    answers = {(a["qid"], a["system"]): a for a in read_jsonl(OUT / "answers.jsonl")}
    pools = {(p["qid"], p["system"]): p["pool"] for p in read_jsonl(OUT / "pools.jsonl")}
    pre = json.load(open(OUT / "prelabels.json", encoding="utf-8"))
    only = audit_sample(pre) if audit else None
    if rest:  # same blind protocol as the audit, on all claims the audit did not cover
        only = {c["cid"] for c in read_jsonl(OUT / "claims.jsonl") if c["qid"] in keep} - audit_sample(pre)
    if rest100:  # whole answers in random order until ~100 claims, so answer-level scores can use them too
        audited, by_answer = audit_sample(pre), {}
        for c in read_jsonl(OUT / "claims.jsonl"):
            if c["qid"] in keep and c["cid"] not in audited:
                by_answer.setdefault((c["qid"], c["system"]), []).append(c["cid"])
        keys = sorted(by_answer)
        random.Random(SEED + 2).shuffle(keys)
        only = set()
        for k in keys:
            if len(only) >= 100:
                break
            only |= set(by_answer[k])
    if blank or audit or rest or rest100:  # no suggestions: the annotator labels from scratch
        pre = {}
    claims = {}
    for c in read_jsonl(OUT / "claims.jsonl"):
        claims.setdefault((c["qid"], c["system"]), []).append(c)
    items = []
    for key in sorted(k for k in answers if k[0] in keep):
        a = answers[key]
        shown = [c for c in claims.get(key, []) if only is None or c["cid"] in only]
        if not shown:
            continue
        items.append({
            "question": a["question"], "answer": a["answer"],
            "pool": [{"title": p["title"], "facts": p["facts"], "text": p["text"]} for p in pools[key]],
            "claims": [{"cid": opaque(c["cid"]), "claim": c["claim"],
                        "pre": pre.get(c["cid"], {}).get("label", ""),
                        "pre_ev": pre.get(c["cid"], {}).get("evidence", ""),
                        "pre_note": pre.get(c["cid"], {}).get("note", ""),
                        "pre_bad": pre.get(c["cid"], {}).get("bad", False)} for c in shown],
        })
    random.Random(SEED).shuffle(items)  # interleave systems; annotators never see the system name
    mode = "F" if rest100 else "E" if rest else "C" if audit else "B" if blank else "A"
    html = PAGE.replace("__DATA__", json.dumps(items, ensure_ascii=False)).replace("__MODE__", mode)
    out = OUT / "annotation" / f"annotate_{mode}.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    ids = {opaque(c["cid"]): c["cid"] for cl in claims.values() for c in cl}
    (out.parent / "id_map.json").write_text(json.dumps(ids, ensure_ascii=False, indent=1), encoding="utf-8")
    print(out, len(items), "answers", sum(len(i["claims"]) for i in items), "claims")


if __name__ == "__main__":
    main()
