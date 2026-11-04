"""Step 9: SelfCheckGPT-NLI baseline (reference-free: it never sees the evidence).

  python s9_selfcheck.py gen  # N_SAMPLES extra answers per sampled question, temperature 0.7,
                              # same generator, prompt and context as s1 -> selfcheck_samples.jsonl
  python s9_selfcheck.py nli  # per claim: mean P(entail) / P(contradiction) of the claim given each
                              # sample (mDeBERTa zero-shot) -> selfcheck_scores.jsonl
A claim the stochastic samples do not repeat is treated as likely hallucinated; s7 tunes the
thresholds on dev exactly as for the evidence-based NLI verifier.
"""

import sys

from common import GEN_MODEL, OUT, SEED, USE_CPU, append_jsonl, chat, read_jsonl, write_jsonl

N_SAMPLES = 3
TEMPERATURE = 0.7


def gen():
    from s1_answer import SYSTEM, format_context

    sample = {r["qid"] for r in read_jsonl(OUT / "sample.jsonl")}
    path = OUT / "selfcheck_samples.jsonl"
    done = {(r["qid"], r["system"]) for r in read_jsonl(path)} if path.exists() else set()
    todo = [a for a in read_jsonl(OUT / "answers.jsonl")
            if a["qid"] in sample and (a["qid"], a["system"]) not in done]
    for n, a in enumerate(todo, 1):
        prompt = f"NGỮ CẢNH:\n{format_context(a['retrieved'], a['relations'])}\n\nCÂU HỎI: {a['question']}"
        samples = [chat(prompt, SYSTEM, GEN_MODEL, num_predict=400, num_ctx=4096,
                        temperature=TEMPERATURE, seed=SEED + k) for k in range(1, N_SAMPLES + 1)]
        append_jsonl(path, {"qid": a["qid"], "system": a["system"], "samples": samples})
        print(f"selfcheck gen {n}/{len(todo)}", flush=True)


def nli():
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    from s5_verifier import BASE, MAX_LEN

    dev_ = "cpu" if USE_CPU or not torch.cuda.is_available() else "cuda"
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForSequenceClassification.from_pretrained(BASE, torch_dtype=torch.float32).to(dev_).eval()
    samples = {(r["qid"], r["system"]): [s for s in r["samples"] if s.strip()]
               for r in read_jsonl(OUT / "selfcheck_samples.jsonl")}
    rows = []
    claims = [c for c in read_jsonl(OUT / "claims.jsonl") if (c["qid"], c["system"]) in samples]
    for n, c in enumerate(claims, 1):
        prem = samples[(c["qid"], c["system"])]
        if not prem:
            continue
        with torch.no_grad():
            enc = tok(prem, [c["claim"]] * len(prem), truncation="longest_first", max_length=MAX_LEN,
                      padding=True, return_tensors="pt").to(dev_)
            probs = model(**enc).logits.softmax(-1).tolist()
        rows.append({"cid": c["cid"], "entail": sum(p[0] for p in probs) / len(probs),
                     "contra": sum(p[2] for p in probs) / len(probs)})
        if n % 50 == 0:
            print(f"selfcheck nli {n}/{len(claims)}", flush=True)
    write_jsonl(OUT / "selfcheck_scores.jsonl", rows)
    print("selfcheck scores:", len(rows))


if __name__ == "__main__":
    {"gen": gen, "nli": nli}[sys.argv[1]]()
