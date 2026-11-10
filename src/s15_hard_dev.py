"""Accuracy on the held-out hard pairs, by error kind, for the zero-shot XLM-R and the model trained with them.

  python s15_hard_dev.py   ->  outputs/logs/dot3_hard_dev.json
"""

import json
from collections import defaultdict

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from common import OUT, ROOT
from s5_verifier import MAX_LEN, head_ids

rows = json.load(open(OUT / "hardneg" / "dev_hard_only.json", encoding="utf-8"))
out = {}
for name, path in (("xzs", "joeddav/xlm-roberta-large-xnli"), ("xhard", str(ROOT / "models" / "verifier_xhard"))):
    tok = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSequenceClassification.from_pretrained(path, torch_dtype=torch.float32).to("cuda").eval()
    ids = head_ids(model); inv = {v: k for k, v in ids.items()}
    acc = defaultdict(lambda: [0, 0])
    with torch.no_grad():
        for i in range(0, len(rows), 16):
            b = rows[i:i + 16]
            enc = tok([x["premise"] for x in b], [x["hypothesis"] for x in b], truncation="longest_first", max_length=MAX_LEN, padding=True, return_tensors="pt").to("cuda")
            for x, p in zip(b, model(**enc).logits.argmax(-1).tolist()):
                for key in (x["kind"], f"{x['kind']}|{x['label']}"):
                    acc[key][0] += inv[p] == x["label"]; acc[key][1] += 1
    out[name] = {k: {"acc": c / n, "n": n} for k, (c, n) in sorted(acc.items())}
    del model; torch.cuda.empty_cache()
json.dump(out, open(OUT / "logs" / "dot3_hard_dev.json", "w", encoding="utf-8"), indent=1)
print(json.dumps(out, indent=1))
