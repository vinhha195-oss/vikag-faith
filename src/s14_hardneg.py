"""Hard negatives shaped like the errors found in the error analysis, for a third verifier run.

The first synthetic set only changed numbers, dates or added a negation. Real wrong claims more often
  - name the wrong agency            -> agency swapped with another one in the corpus        (contradicted)
  - add items to a list              -> an item from another list inserted                   (unsupported)
  - deny something the text says     -> "no information about X" while X is in the passage  (contradicted)
Each kind gets a supported counterpart so the model cannot learn the template alone: the original sentence for
swaps, a list with one item removed, and "the passage mentions X".

Passages of the evaluation sample are excluded, as in s5. Output (gzipped jsonl, committed so Colab can read it):
  outputs/hardneg/train_hard.jsonl.gz  : hard pairs + base pairs from data/verifier_train_20k.jsonl, 16,000 rows
  outputs/hardneg/dev_hard.jsonl.gz    : data/verifier_dev_20k.jsonl + held-out hard pairs (src "synth")
"""

import csv
import os
import gzip
import json
import random
import re
from collections import Counter

from common import DATA, OUT, SEED, read_jsonl
from s5_verifier import split_sentences, window_of

N_PER_KIND = 2000
# Colab run: 16,000 rows from the 900-character base set. Local run (VIKAG_HARD_BASE=_20k450, VIKAG_TRAIN_WINDOW=450):
# same size as the base set, so the only change from the second-round model is that hard pairs replace base pairs.
BASE_TAG = os.environ.get("VIKAG_HARD_BASE", "_20k")
OUT_TAG = os.environ.get("VIKAG_HARD_TAG", "")
N_TOTAL = int(os.environ.get("VIKAG_HARD_TOTAL", "16000"))
AGENCIES = ["Bộ Y tế", "Sở Y tế", "Thanh tra Bộ Y tế", "Văn phòng Bộ Y tế", "Cục Quản lý Dược", "Cục Quản lý Y, Dược cổ truyền",
            "Cục Quản lý Khám, chữa bệnh", "Cục An toàn thực phẩm", "Cục Y tế dự phòng", "Cục Dân số", "Tổng cục Dân số", "Cục Khoa học công nghệ và Đào tạo",
            "Cục Quản lý Môi trường y tế", "Cục Phòng, chống HIV/AIDS", "Cục Công nghệ thông tin", "Cục Hạ tầng và Thiết bị y tế", "Vụ Pháp chế",
            "Vụ Kế hoạch - Tài chính", "Vụ Tổ chức cán bộ", "Vụ Bảo hiểm y tế", "Vụ Sức khỏe Bà mẹ - Trẻ em", "Viện Chiến lược và Chính sách y tế",
            "Bảo hiểm xã hội Việt Nam", "Bộ Tài chính", "Bộ Công Thương", "Ủy ban nhân dân tỉnh", "Trung tâm Kiểm soát bệnh tật", "Bệnh viện Bạch Mai"]
ORG_OLD = re.compile(r"\b(?:Bộ|Cục|Sở|Viện|Văn phòng|Thanh tra|Vụ|Tổng cục|Ủy ban nhân dân|Trung tâm|Bệnh viện|Ban|Hội đồng)"
                 r"(?: (?:[A-ZĐÂĂÊÔƠƯÁÀẢÃẠÉÈẺẼẸÍÌỈĨỊÓÒỎÕỌÚÙỦŨỤÝỲỶỸỴ][\w\-]*|và|y|tế|dược|thực|phẩm|dân|số|tỉnh|thành|phố)){1,7}")
ENT = re.compile(r"\b\d{1,4}/\d{4}/[A-ZĐ][A-ZĐ\-]+|\bngày \d{1,2}/\d{1,2}/\d{4}|\b\d{1,3}(?:\.\d{3})+ đồng")
VN = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ")


def clean(s):
    w = s.split()
    return len(w) >= 8 and sum(any(ch in VN for ch in x.lower()) for x in w) / len(w) >= 0.25 and sum(x.isupper() and len(x) > 2 for x in w) / len(w) < 0.15


LIST = re.compile(r"((?:[^,.;:]{2,40}, ){2,}[^,.;:]{2,40}(?: và [^,.;:]{2,40})?)")


def main():
    rng = random.Random(SEED + 21)
    sample = {r["qid"] for r in read_jsonl(OUT / "sample.jsonl")}
    held = {p["id"] for x in read_jsonl(OUT / "pools.jsonl") if x["qid"] in sample for p in x["pool"]}
    ctx = [r for r in csv.DictReader(open(DATA / "contexts.csv", encoding="utf-8")) if r["context_id"] not in held]
    sents = [(r, s) for r in ctx for s in split_sentences(r["text"]) if clean(s)]
    rng.shuffle(sents)
    corpus = " ".join(r["text"] for r in ctx)
    orgs = sorted((a for a in AGENCIES if corpus.count(a) >= 2), key=len, reverse=True)  # longest first, so "Bộ Y tế" does not cut "Thanh tra Bộ Y tế"
    items = sorted({x.strip() for _, s in sents for m in LIST.finditer(s) for x in re.split(r", | và ", m.group(1))
                    if 2 <= len(x.split()) <= 5 and x.strip()[:1].islower() and clean(" ".join([x] * 4))})
    hard = {"swap": [], "list": [], "deny": []}

    def add(kind, r, s, h, label):
        premise = window_of(r["text"], s)
        if s in premise and (h != s or label == "supported"):
            hard[kind].append({"premise": premise, "hypothesis": h, "label": label, "src": "synth", "kind": kind})

    for r, s in sents:
        if len(hard["swap"]) < 2 * N_PER_KIND:
            m = [a for a in orgs if a in s]
            if m:
                o = m[0]
                alt = rng.choice(orgs)
                if alt != o and alt not in o and o not in alt and alt not in r["text"]:
                    add("swap", r, s, s.replace(o, alt, 1), "contradicted")
                    add("swap", r, s, s, "supported")
        if len(hard["list"]) < 2 * N_PER_KIND:
            m = LIST.search(s)
            if m:
                parts = re.split(r", | và ", m.group(1))
                if len(parts) >= 3 and all(1 <= len(x.split()) <= 6 for x in parts):
                    extra = rng.choice(items)
                    if extra.lower() not in r["text"].lower():
                        add("list", r, s, s.replace(m.group(1), ", ".join(parts[:-1] + [extra]) + " và " + parts[-1], 1), "unsupported")
                        keep = parts[:]; keep.pop(rng.randrange(len(keep) - 1))
                        add("list", r, s, s.replace(m.group(1), ", ".join(keep[:-1]) + " và " + keep[-1], 1), "supported")
        if len(hard["deny"]) < 2 * N_PER_KIND:
            ents = [m.group(0) for m in ENT.finditer(s)] or [o for o in orgs if o in s and o != "Bộ Y tế"]  # ids, dates and amounts first; "Bộ Y tế" is everywhere
            if ents:
                e = rng.choice(ents)
                neg, pos = rng.choice([("Văn bản không nêu {e}.", "Văn bản có nêu {e}."), ("Không tìm thấy thông tin về {e} trong văn bản.", "Văn bản có thông tin về {e}.")])
                add("deny", r, s, neg.format(e=e), "contradicted")
                add("deny", r, s, pos.format(e=e), "supported")
    for k in hard:
        rng.shuffle(hard[k])
        hard[k] = hard[k][:N_PER_KIND]
    dev_hard = [x for k in hard for x in hard[k][:200]]
    train_hard = [x for k in hard for x in hard[k][200:]]
    base = read_jsonl(DATA / f"verifier_train{BASE_TAG}.jsonl")
    rng.shuffle(base)
    train = train_hard + base[:N_TOTAL - len(train_hard)]
    rng.shuffle(train)
    dev = read_jsonl(DATA / f"verifier_dev{BASE_TAG}.jsonl") + dev_hard
    (OUT / "hardneg").mkdir(exist_ok=True)
    for name, rows in (("train_hard", train), ("dev_hard", dev)):
        with gzip.open(OUT / "hardneg" / f"{name}{OUT_TAG}.jsonl.gz", "wt", encoding="utf-8") as f:
            for x in rows:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
    json.dump(dev_hard, open(OUT / "hardneg" / f"dev_hard_only{OUT_TAG}.json", "w", encoding="utf-8"), ensure_ascii=False)
    if OUT_TAG:  # local run: write the training files directly
        from common import write_jsonl
        write_jsonl(DATA / f"verifier_train_hard{OUT_TAG}.jsonl", train)
        write_jsonl(DATA / f"verifier_dev_hard{OUT_TAG}.jsonl", dev)
    print("orgs", len(orgs), "list items", len(items))
    print({k: (len(v), Counter(x["label"] for x in v)) for k, v in hard.items()})
    print("train", len(train), Counter(x.get("kind", x["src"]) for x in train), "dev", len(dev))
    for k in hard:
        for x in hard[k][:3]:
            print(k, x["label"], "|", x["hypothesis"][:200])


if __name__ == "__main__":
    main()
