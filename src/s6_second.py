"""Second annotator, pass K: the claims where Claude and the first annotator disagree, mixed with as many claims
where they agree, so the annotator cannot tell which claims are disputed. Full passages are open by default.

  python s6_second.py   ->  outputs/annotation/annotate_K.html  (export: vifaith_labels_K.json)

The page shows no label from Claude or from the first annotator and no system name.
"""

import json
import random

from common import OUT, SEED, read_jsonl
from s6_annotation import opaque
from s6_quick import PAGE, best_sentences
from s10_dot2 import human_labels

N_FILLER = 23


def main():
    pre = json.load(open(OUT / "prelabels.json", encoding="utf-8"))
    human = human_labels()
    claims = {c["cid"]: c for c in read_jsonl(OUT / "claims.jsonl")}
    answers = {(a["qid"], a["system"]): a for a in read_jsonl(OUT / "answers.jsonl")}
    pools = {(p["qid"], p["system"]): p["pool"] for p in read_jsonl(OUT / "pools.jsonl")}
    usable = [k for k in human if k in pre and not pre[k]["bad"]]
    disputed = sorted(k for k in usable if human[k] != pre[k]["label"])
    agreed = sorted(k for k in usable if human[k] == pre[k]["label"])
    rng = random.Random(SEED + 11)
    chosen = disputed + rng.sample(agreed, N_FILLER)
    rng.shuffle(chosen)
    items = []
    for k in chosen:
        c = claims[k]; key = (c["qid"], c["system"])
        items.append({"cid": opaque(k), "claim": c["claim"], "question": answers[key]["question"],
                      "sents": best_sentences(c["claim"], pools[key]),
                      "full": [{"title": p["title"], "text": p["text"]} for p in pools[key]]})
    page = (PAGE.replace("Kiểm tra nhanh 30 ý (lượt __PASS__)", f"Kiểm tra {len(items)} ý (lượt __PASS__)")
            .replace('<details id="more">', '<details id="more" open>')
            .replace("Không thấy? Xem toàn bộ văn bản", "Toàn bộ văn bản (đọc kỹ khi chưa chắc)"))
    assert '<details id="more" open>' in page
    out = OUT / "annotation" / "annotate_K.html"
    out.write_text(page.replace("__DATA__", json.dumps(items, ensure_ascii=False)).replace("__PASS__", "K"), encoding="utf-8")
    json.dump({"disputed": disputed, "filler": [k for k in chosen if k not in disputed]}, open(OUT / "annotation" / "pass_K_design.json", "w", encoding="utf-8"), indent=1)
    print(out, len(items), "claims,", len(disputed), "disputed")


if __name__ == "__main__":
    main()
