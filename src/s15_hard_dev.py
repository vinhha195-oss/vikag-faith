"""Accuracy on the held-out hard pairs, by error kind, for the zero-shot XLM-R and the model trained with them.

  python s15_hard_dev.py   ->  outputs/logs/dot3_hard_dev.json
"""

import json
import os
from collections import defaultdict

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from common import OUT, ROOT
from s5_verifier import MAX_LEN, head_ids

rows = json.load(open(OUT / "hardneg" / f"dev_hard_only{os.environ.get('VIKAG_HARD_TAG', '')}.json", encoding="utf-8"))
out = {}
# VIKAG_HARD_MODELS="name=path,..." overrides the Colab pair (zero-shot XLM-R and the model trained with hard pairs)
MODELS = [x.split("=", 1) for x in os.environ.get("VIKAG_HARD_MODELS", f"xzs=joeddav/xlm-roberta-large-xnli,xhard={ROOT / 'models' / 'verifier_xhard'}").split(",")]
for name, path in MODELS:
    tok = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSequenceClassification.from_pretrained(path, torch_dtype=torch.float32).to("cuda").eval()
    ids = head_ids(model); inv = {v: k for k, v in ids.items()}
    acc = defaultdict(lambda: [0, 0])
    with torch.no_grad():
        for i in range(0, len(rows), 8):
            b = rows[i:i + 8]
            enc = tok([x["premise"] for x in b], [x["hypothesis"] for x in b], truncation="longest_first", max_length=MAX_LEN, padding=True, return_tensors="pt").to("cuda")
            for x, p in zip(b, model(**enc).logits.argmax(-1).tolist()):
                for key in (x["kind"], f"{x['kind']}|{x['label']}"):
                    acc[key][0] += inv[p] == x["label"]; acc[key][1] += 1
    out[name] = {k: {"acc": c / n, "n": n} for k, (c, n) in sorted(acc.items())}
    del model; torch.cuda.empty_cache()
json.dump(out, open(OUT / "logs" / f"dot3_hard_dev{os.environ.get('VIKAG_HARD_TAG', '')}.json", "w", encoding="utf-8"), indent=1)
print(json.dumps(out, indent=1))
