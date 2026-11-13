"""Record real runs of the live chatbot (s16_live.analyse) for the demo's offline "Thử trực tiếp" tab.

  python s22_record.py   ->  outputs/dot4_live.jsonl   (one row per question, resumable)
The questions are eight ViHERMES questions of the sampled set, shown in the demo as recorded runs, not live ones.
"""

import json

from common import OUT, append_jsonl, read_jsonl
import s16_live

QIDS = ["q3#140", "q3#620", "q1#1134", "q2#1081", "q1#255", "q1#114", "q1#111", "q3#119"]
questions = {a["qid"]: a["question"] for a in read_jsonl(OUT / "answers.jsonl")}
path = OUT / "dot4_live.jsonl"
done = {r["qid"] for r in read_jsonl(path)} if path.exists() else set()
for n, q in enumerate(QIDS, 1):
    if q in done:
        continue
    row = s16_live.analyse(questions[q], True)
    append_jsonl(path, {"qid": q, **row})
    print(f"live {n}/{len(QIDS)} claims={len(row['claims'])}", flush=True)
