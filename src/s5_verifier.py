"""Step 5: claim verifier.

  python s5_verifier.py data     # synthetic regulatory pairs + ViNLI -> data/verifier_*.jsonl
  python s5_verifier.py train    # fine-tune mDeBERTa-v3-base-xnli -> models/verifier
  python s5_verifier.py predict  # entail/contra probabilities per claim, zero-shot and fine-tuned,
                                 # with evidence V1 (passage text), V2 (+ graph facts), V3 (+ claim-linked triples)
Thresholds that turn probabilities into labels are tuned later on the dev split (s7).
"""

import csv
import random
import re
import sys

import os

from common import DATA, OUT, ROOT, SEED, USE_CPU, read_jsonl, write_jsonl
from rules import overlap

BASE = os.environ.get("VIKAG_BASE", "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7")
# Second round: extra pairs and variants go to separate files, so the first round's results never change.
DATA_TAG = os.environ.get("VIKAG_DATA_TAG", "")
ZS_NAME = os.environ.get("VIKAG_ZS_NAME", "zs")
SCORE_FILE = os.environ.get("VIKAG_SCORE_FILE", "verifier_scores.jsonl")
SYNTH_TARGET = int(os.environ.get("VIKAG_SYNTH_TARGET", "0"))  # 0 = first-round sampling
# VIKAG_FT_TAG names a fine-tuned variant ("ft" = main run); VIKAG_NO_SYNTH=1 trains on ViNLI only (ablation).
FT_TAG = os.environ.get("VIKAG_FT_TAG", "ft")
FT_DIR = ROOT / "models" / ("verifier" if FT_TAG == "ft" else f"verifier_{FT_TAG}")
MAX_LEN = 320
WINDOW, STRIDE = 900, 700  # characters per evidence window
# Output order differs between checkpoints (mDeBERTa: E/N/C, XLM-R: C/N/E), so it is read from the config.
NLI_NAMES = {"supported": "entailment", "unsupported": "neutral", "contradicted": "contradiction"}


def head_ids(model):
    ids = {k.lower(): v for k, v in model.config.label2id.items()}
    if not all(v in ids for v in NLI_NAMES.values()):
        ids = {"entailment": 0, "neutral": 1, "contradiction": 2}
    return {k: ids[v] for k, v in NLI_NAMES.items()}


# ---------- data ----------

NEGATIONS = [("phải", "không phải"), ("được", "không được"), ("có", "không có"),
             ("bắt buộc", "không bắt buộc")]


def split_sentences(text):
    parts = re.split(r"(?<=[.;:])\s+|\n+", text)
    return [p.strip() for p in parts if 40 <= len(p.strip()) <= 300]


def corrupt(sentence, rng):
    """Make a contradiction by changing a number/date or inserting a negation."""
    nums = list(re.finditer(r"\d+", sentence))
    if nums and rng.random() < 0.7:
        m = rng.choice(nums)
        old = int(m.group())
        new = old + rng.choice([1, 2, 3, 5, 10]) * rng.choice([-1, 1])
        if new < 0 or new == old:
            new = old + 7
        return sentence[: m.start()] + str(new) + sentence[m.end():]
    for a, b in rng.sample(NEGATIONS, len(NEGATIONS)):
        hit = re.search(rf"\b{a}\b", sentence)
        if hit and not sentence[max(0, hit.start() - 6):hit.start()].strip().endswith("không"):
            return sentence[: hit.start()] + b + sentence[hit.end():]
    return None


def window_of(text, sentence):
    i = text.find(sentence)
    start = max(0, min(i - WINDOW // 3, len(text) - WINDOW))
    return text[start:start + WINDOW]


def build_data():
    from datasets import load_dataset

    rng = random.Random(SEED)
    sample = {r["qid"] for r in read_jsonl(OUT / "sample.jsonl")}
    held = {p["id"] for x in read_jsonl(OUT / "pools.jsonl") if x["qid"] in sample for p in x["pool"]}
    ctx = [r for r in csv.DictReader(open(DATA / "contexts.csv", encoding="utf-8"))
           if r["context_id"] not in held]
    by_doc = {}
    for r in ctx:
        by_doc.setdefault(r["title"], []).append(r)
    # First round: 2 sentences per passage, one pair of each kind. Second round: every sentence,
    # up to 2 corrupted and 2 unrelated hypotheses each, then cut to SYNTH_TARGET.
    per_passage, per_kind = (10 ** 6, 2) if SYNTH_TARGET else (2, 1)
    synth = []
    for r in ctx:
        sents = split_sentences(r["text"])
        rng.shuffle(sents)
        for s in sents[:per_passage]:
            premise = window_of(r["text"], s)
            if s not in premise:
                continue
            synth.append({"premise": premise, "hypothesis": s, "label": "supported", "src": "synth"})
            seen = {s}
            for _ in range(per_kind):
                bad = corrupt(s, rng)
                if bad and bad not in seen:
                    seen.add(bad)
                    synth.append({"premise": premise, "hypothesis": bad, "label": "contradicted", "src": "synth"})
            # Unsupported: a sentence from another passage (prefer the same document).
            for _ in range(per_kind):
                others = [o for o in by_doc[r["title"]] if o is not r] or rng.sample(ctx, 3)
                cand = split_sentences(rng.choice(others)["text"])
                if cand:
                    h = rng.choice(cand)
                    if h not in r["text"] and h not in seen:
                        seen.add(h)
                        synth.append({"premise": premise, "hypothesis": h, "label": "unsupported", "src": "synth"})
    names = {"entailment": "supported", "neutral": "unsupported", "contradiction": "contradicted"}
    vinli = load_dataset("presencesw/vinli_4_label")
    rows = {}
    for split in ("train", "dev"):
        rows[split] = [{"premise": x["sentence1"], "hypothesis": x["sentence2"],
                        "label": names[x["gold_label"]], "src": "vinli"}
                       for x in vinli[split] if x["gold_label"] in names]
    rng.shuffle(synth)
    if SYNTH_TARGET:
        synth = synth[:SYNTH_TARGET]
    n_dev = len(synth) // 10
    train = rng.sample(rows["train"], min(int(os.environ.get("VIKAG_VINLI", "4000")), len(rows["train"]))) + synth[n_dev:]
    dev = rng.sample(rows["dev"], 1000) + synth[:n_dev]
    rng.shuffle(train)
    train = train[: int(os.environ.get("VIKAG_MAX_TRAIN", len(train)))]  # smoke tests only
    write_jsonl(DATA / f"verifier_train{DATA_TAG}.jsonl", train)
    write_jsonl(DATA / f"verifier_dev{DATA_TAG}.jsonl", dev)
    count = lambda xs, k: {v: sum(x[k] == v for x in xs) for v in sorted({x[k] for x in xs})}  # noqa: E731
    print("train", len(train), count(train, "label"), count(train, "src"))
    print("dev", len(dev), count(dev, "label"), count(dev, "src"))


# ---------- train ----------

def train():
    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

    torch.manual_seed(SEED)
    dev_ = "cpu" if USE_CPU or not torch.cuda.is_available() else "cuda"
    tok = AutoTokenizer.from_pretrained(BASE)
    # The checkpoint is stored in float16; newer transformers keep that dtype, and pure fp16
    # training gave NaN loss on Colab from the first steps. Always train in float32.
    model = AutoModelForSequenceClassification.from_pretrained(BASE, torch_dtype=torch.float32).to(dev_)
    import transformers
    print("transformers", transformers.__version__, "torch", torch.__version__,
          "dtype", next(model.parameters()).dtype, flush=True)
    tr, dv = read_jsonl(DATA / f"verifier_train{DATA_TAG}.jsonl"), read_jsonl(DATA / f"verifier_dev{DATA_TAG}.jsonl")
    label_id = head_ids(model)
    if os.environ.get("VIKAG_NO_SYNTH") == "1":
        tr = [r for r in tr if r["src"] != "synth"]
    tr = tr[: int(os.environ.get("VIKAG_MAX_RUN", len(tr)))]  # XLM-R is slower on a free T4
    print("train rows", len(tr), "->", FT_DIR, flush=True)

    def collate(batch):
        enc = tok([b["premise"] for b in batch], [b["hypothesis"] for b in batch],
                  truncation="longest_first", max_length=MAX_LEN, padding=True, return_tensors="pt")
        enc["labels"] = torch.tensor([label_id[b["label"]] for b in batch])
        return enc

    bs, accum, epochs = int(os.environ.get("VIKAG_BS", "4")), int(os.environ.get("VIKAG_ACCUM", "4")), 1
    loader = DataLoader(tr, batch_size=bs, shuffle=True, collate_fn=collate)
    opt = torch.optim.AdamW(model.parameters(), lr=5e-6, weight_decay=0.01)
    steps = len(loader) * epochs // accum
    sched = get_linear_schedule_with_warmup(opt, int(0.06 * steps), steps)

    def evaluate():
        model.eval()
        correct = {"vinli": [0, 0], "synth": [0, 0]}
        with torch.no_grad():
            for i in range(0, len(dv), 16):
                batch = dv[i:i + 16]
                enc = collate(batch).to(dev_)
                pred = model(**{k: v for k, v in enc.items() if k != "labels"}).logits.argmax(-1)
                for b, p, y in zip(batch, pred.tolist(), enc["labels"].tolist()):
                    correct[b["src"]][0] += p == y
                    correct[b["src"]][1] += 1
        model.train()
        return {k: round(c / max(n, 1), 4) for k, (c, n) in correct.items()}

    # A first Colab run collapsed to one class (dev 0.76 -> 0.34), so training keeps the best
    # dev checkpoint, starting from the base model itself: the result is never worse than zero-shot.
    FT_DIR.mkdir(parents=True, exist_ok=True)
    acc = evaluate()
    best = (acc["vinli"] + acc["synth"]) / 2
    print("dev acc before:", acc, flush=True)
    model.save_pretrained(FT_DIR); tok.save_pretrained(FT_DIR)
    model.train()
    nonfinite = 0
    for epoch in range(epochs):
        for i, enc in enumerate(loader):
            enc = enc.to(dev_)
            loss = model(**enc).loss / accum
            if not torch.isfinite(loss):
                nonfinite += 1
                if nonfinite > 20:
                    raise RuntimeError("loss is not finite; training aborted")
                continue
            loss.backward()
            if (i + 1) % accum == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step(); sched.step(); opt.zero_grad()
                if ((i + 1) // accum) % int(os.environ.get("VIKAG_EVAL_EVERY", "150")) == 0:
                    acc = evaluate()
                    score = (acc["vinli"] + acc["synth"]) / 2
                    kept = score > best
                    if kept:
                        best = score
                        model.save_pretrained(FT_DIR); tok.save_pretrained(FT_DIR)
                    print(f"step {(i + 1) // accum}/{steps} loss {loss.item() * accum:.4f} dev {acc}"
                          f"{' -> saved' if kept else ''}", flush=True)
    print("best dev mean acc:", round(best, 4), "non-finite batches skipped:", nonfinite, flush=True)


# ---------- predict ----------

def windows(text):
    if len(text) <= WINDOW:
        return [text]
    return [text[i:i + WINDOW] for i in range(0, len(text) - WINDOW // 3, STRIDE)]


def premises(pool, with_graph):
    out = []
    for p in pool:
        head = ""
        if with_graph:
            head = f"Văn bản: {p['title']}. " + " ".join(f + "." for f in p["facts"][:6]) + "\n"
        out += [head + w for w in windows(p["text"])]
    return out


MIN_LINK = 0.3  # share of the claim's words a triple must contain to count as linked
DOC_NO = re.compile(r"\d+/(?:\d{4}/)?[A-Za-zĐđ]+(?:-[A-Za-zĐđ]+)*")


def premises_v3(pool, claim, index):
    """V3: only the triples that share an entity with this claim, not every fact of every passage,
    plus source passages reached through the mutual index when the claim names another document."""
    cited = {m for m in DOC_NO.findall(claim) if m in index["doc_chunks"]}
    pool_ids = {p["id"] for p in pool}
    extra = []
    for doc in cited:
        extra += [c for c in index["doc_chunks"][doc] if c["id"] not in pool_ids]
    extra = sorted(extra, key=lambda c: -overlap(claim, c["text"]))[:2]
    out = []
    for p in pool + extra:
        triples = index["chunk_triples"].get(p["id"], [])
        ranked = sorted(triples, key=lambda t: -overlap(claim, t))
        picked = [t for t in ranked if overlap(claim, t) >= MIN_LINK][:3]
        head = ("Tri thức: " + " ".join(picked) + "\n") if picked else ""
        out += [head + w for w in windows(p["text"])]
    return out


def predict():
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    dev_ = "cpu" if USE_CPU or not torch.cuda.is_available() else "cuda"
    sample = {r["qid"] for r in read_jsonl(OUT / "sample.jsonl")}
    pools = {(p["qid"], p["system"]): p["pool"] for p in read_jsonl(OUT / "pools.jsonl")}
    claims = [c for c in read_jsonl(OUT / "claims.jsonl") if c["qid"] in sample]
    result = {c["cid"]: {} for c in claims}
    path_out = OUT / SCORE_FILE
    variants = os.environ.get("VIKAG_VARIANTS", "v1,v2").split(",")
    index = None
    if "v3" in variants:
        import json
        index = json.load(open(OUT / "triple_index.json", encoding="utf-8"))
    old = {r["cid"]: r for r in read_jsonl(path_out)} if path_out.exists() else {}
    # Variants already scored are skipped; VIKAG_FORCE=1 rescores both (zero-shot and FT_TAG).
    force = os.environ.get("VIKAG_FORCE") == "1"
    wanted = [(ZS_NAME, BASE), (FT_TAG, str(FT_DIR))]
    if os.environ.get("VIKAG_SKIP_ZS") == "1":
        wanted = wanted[1:]
    if os.environ.get("VIKAG_SKIP_FT") == "1":
        wanted = wanted[:1]
    runs = [(n, p) for n, p in wanted
            if force or not all(f"{n}_{v}" in old.get(c["cid"], {}) for c in claims for v in variants)]
    for name, path in runs:
        if name != ZS_NAME and not (FT_DIR / "config.json").exists():
            print("no fine-tuned model; zero-shot scores only")
            continue
        tok = AutoTokenizer.from_pretrained(path)
        model = AutoModelForSequenceClassification.from_pretrained(path, torch_dtype=torch.float32).to(dev_).eval()
        ids = head_ids(model)
        for variant in variants:
            for n, c in enumerate(claims):
                pool = pools[(c["qid"], c["system"])]
                prem = premises_v3(pool, c["claim"], index) if variant == "v3" else premises(pool, variant == "v2")
                probs = []
                with torch.no_grad():
                    size = int(os.environ.get("VIKAG_PRED_BS", "8"))
                    for i in range(0, len(prem), size):
                        enc = tok(prem[i:i + size], [c["claim"]] * len(prem[i:i + size]), truncation="longest_first",
                                  max_length=MAX_LEN, padding=True, return_tensors="pt").to(dev_)
                        probs += model(**enc).logits.softmax(-1).tolist()
                # Entailment: strongest window. Contradiction: only the 2 windows that share the
                # most words with the claim, since NLI calls unrelated text "contradiction" too.
                relevant = sorted(range(len(prem)), key=lambda i: -overlap(c["claim"], prem[i]))[:2]
                result[c["cid"]][f"{name}_{variant}"] = {
                    "entail": max(p[ids["supported"]] for p in probs),
                    "contra": max(probs[i][ids["contradicted"]] for i in relevant),
                    "contra_any": max(p[ids["contradicted"]] for p in probs)}
            print(name, variant, "done", flush=True)
        del model
        torch.cuda.empty_cache()
    merged = [{**{kk: vv for kk, vv in old.get(k, {}).items() if kk != "cid"}, **v} for k, v in result.items()]
    write_jsonl(path_out, [{"cid": k, **m} for k, m in zip(result, merged)])


if __name__ == "__main__":
    {"data": build_data, "train": train, "predict": predict}[sys.argv[1]]()
