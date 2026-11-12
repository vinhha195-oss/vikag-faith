"""ViEduReg pilot: a small set of Vietnamese higher-education regulations for testing the checkers outside health.

  python s20_viedureg.py build <folder>   ->  outputs/viedureg/passages.jsonl

Sources (public guidance documents of the Ministry of Education and Training, quality assurance of higher
education): Công văn 768 and 769 (2018), and the guidance tables attached to Công văn 1668 and 1669 (2019).
Thông tư 20/2026 is a scanned PDF without text and Thông tư 04/2025 lost its diacritics in OCR, so both are left out.
Passages are cut on paragraph boundaries at about 900 characters, like the ViHERMES windows.
"""

import glob
import json
import os
import re
import sys

from common import OUT

SOURCES = [("CV 768", "Công văn 768/QLCL-KĐCLGD hướng dẫn đánh giá theo bộ tiêu chuẩn chất lượng cơ sở giáo dục đại học", "CV 768*.docx"),
           ("CV 769", "Công văn 769/QLCL-KĐCLGD hướng dẫn đánh giá chương trình đào tạo", "CV 769*.docx"),
           ("CV 1668", "Hướng dẫn đánh giá kèm Công văn 1668/QLCL-KĐCLGD (thay thế Công văn 768)", "*1668*.pdf"),
           ("CV 1669", "Hướng dẫn đánh giá kèm Công văn 1669/QLCL-KĐCLGD (thay thế Công văn 769)", "*1669*.pdf")]
SIZE = 900


def text_of(path):
    if path.endswith(".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(path).paragraphs)
    import pypdfium2 as P
    d = P.PdfDocument(path)
    return "\n".join(d[i].get_textpage().get_text_range() for i in range(len(d)))


def chunks(text):
    paras = [" ".join(p.split()) for p in re.split(r"\r?\n", text)]
    paras = [p for p in paras if len(p) > 1 and not re.fullmatch(r"\d+", p)]
    out, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) > SIZE:
            out.append(cur); cur = ""
        cur = (cur + " " + p).strip()
    if cur:
        out.append(cur)
    return [c for c in out if len(c) >= 200]


def build(folder):
    rows = []
    for doc_id, title, pattern in SOURCES:
        path = glob.glob(os.path.join(folder, pattern))[0]
        for i, c in enumerate(chunks(text_of(path))):
            rows.append({"id": f"{doc_id.replace(' ', '')}-{i:03d}", "doc": doc_id, "title": title, "text": c})
    (OUT / "viedureg").mkdir(exist_ok=True)
    with open(OUT / "viedureg" / "passages.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(len(rows), "passages", {d: sum(r["doc"] == d for r in rows) for d, _, _ in SOURCES})


if __name__ == "__main__":
    {"build": lambda: build(sys.argv[2])}[sys.argv[1]]()
