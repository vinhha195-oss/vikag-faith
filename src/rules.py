"""Deterministic number / date / document-code check for claims against evidence."""

import re
import unicodedata

DOC_CODE = re.compile(r"\b\d{1,4}/\d{4}/[A-ZĐ][A-ZĐ0-9-]*", re.I)
DATE_WORDS = re.compile(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", re.I)
DATE_NUM = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b")
NUMBER = re.compile(r"\b\d+(?:[.,]\d+)*\s*%?")
WORD = re.compile(r"\w+")


def norm(text):
    return unicodedata.normalize("NFC", text)


def values(text):
    """Typed values in a text: ('code', ...), ('date', d/m/y), ('num', ...)."""
    text = norm(text)
    out = set()
    for m in DOC_CODE.finditer(text):
        out.add(("code", m.group().upper()))
    text = DOC_CODE.sub(" ", text)
    for rx in (DATE_WORDS, DATE_NUM):
        for d, mth, y in rx.findall(text):
            out.add(("date", f"{int(d)}/{int(mth)}/{y}"))
        text = rx.sub(" ", text)
    for m in NUMBER.finditer(text):
        v = m.group().replace(" ", "").replace(",", ".").rstrip(".")
        if v:
            out.add(("num", v.lstrip("0") or "0"))
    return out


def sentences(text):
    return [s for s in re.split(r"(?<=[.;:!?])\s+|\n+", norm(text)) if s.strip()]


def overlap(a, b):
    wa = {w for w in WORD.findall(a.lower()) if not w.isdigit()}
    wb = {w for w in WORD.findall(b.lower()) if not w.isdigit()}
    return len(wa & wb) / max(1, len(wa))


def check(claim, evidence_texts):
    """None if every value in the claim occurs in the evidence; otherwise 'contradicted' when a
    closely matching evidence sentence carries a competing value of the same type (one the claim
    does not mention), else 'unsupported'."""
    claimed = values(claim)
    if not claimed:
        return None
    pool = set()
    for t in evidence_texts:
        pool |= values(t)
    missing = claimed - pool
    if not missing:
        return None
    kinds = {k for k, _ in missing}
    for t in evidence_texts:
        for s in sentences(t):
            competing = {k for k, v in values(s) - claimed}
            if overlap(claim, s) >= 0.5 and kinds & competing:
                return "contradicted"
    return "unsupported"
