"""Shared paths, data loading, and Ollama helpers for the ViKAG-Faith pilot."""

import json
import os
import random
import re
import sys
import time
from pathlib import Path

import numpy as np
import ollama

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
DATASET = ROOT / "external" / "ViHERMES" / "dataset" / "dataset.jsonl"
GRAPH_DB = DATA / "graph.db"
DENSE_INDEX = DATA / "dense_bge-m3.npz"

GEN_MODEL = "qwen2.5:3b"
BIG_MODEL = "qwen2.5:7b"
EMBED_MODEL = "bge-m3"
SEED = 42
# The local GTX 1650 hangs the whole machine under sustained load (driver TDR -> hard freeze),
# so models run on the CPU unless VIKAG_CPU=0 (set on Colab, which has a T4).
USE_CPU = os.environ.get("VIKAG_CPU", "1") == "1"
CPU_ONLY = {"num_gpu": 0} if USE_CPU else {}

sys.stdout.reconfigure(encoding="utf-8")
OUT.mkdir(exist_ok=True)


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_jsonl(path, row):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_dataset():
    rows = read_jsonl(DATASET)
    for i, r in enumerate(rows):
        r["row"] = i
    return rows


def sample_questions(per_hop=20):
    """Stratified sample: `per_hop` questions for each hop level 1-5, fixed seed."""
    rows = load_dataset()
    rng = random.Random(SEED)
    picked = []
    for hop in range(1, 6):
        pool = [r for r in rows if r["hop_level"] == hop]
        picked += rng.sample(pool, per_hop)
    return picked


class OllamaEmbedder:
    """Implements the ViHERMES `Embedder` port with bge-m3 served by Ollama."""

    identity = "ollama:" + EMBED_MODEL

    def __init__(self):
        self.cache = {}

    def encode(self, texts, batch=8):
        if texts and all(t in self.cache for t in texts):
            return np.asarray([self.cache[t] for t in texts], dtype=np.float32)
        out = []
        for i in range(0, len(texts), batch):
            chunk = texts[i : i + batch]
            try:
                out += ollama.embed(model=EMBED_MODEL, input=chunk, options=CPU_ONLY)["embeddings"]
            except Exception as e:  # runner crashes on some batches: fall back to one at a time
                print("embed batch failed, retrying singly:", str(e)[:80])
                time.sleep(3)
                out += [ollama.embed(model=EMBED_MODEL, input=[t], options=CPU_ONLY)["embeddings"][0]
                        for t in chunk]
            if len(texts) > batch:
                print(f"embedded {len(out)}/{len(texts)}", flush=True)
        self.cache.update(zip(texts, out))
        return np.asarray(out, dtype=np.float32)

    def unload(self):
        """Free the 4GB GPU before an LLM is loaded: both together crash the GTX 1650."""
        ollama.embed(model=EMBED_MODEL, input=["."], keep_alive=0, options=CPU_ONLY)


def chat(prompt, system=None, model=GEN_MODEL, fmt=None, num_predict=512, num_ctx=6144, temperature=0, seed=SEED):
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    options = {"temperature": temperature, "seed": seed, "num_predict": num_predict, "num_ctx": num_ctx, **CPU_ONLY}
    for attempt in range(3):
        try:
            r = ollama.chat(model=model, messages=messages, format=fmt, options=options)
            return r["message"]["content"]
        except ollama.ResponseError as e:
            if "repeat" in str(e):
                # Newer Ollama aborts degenerate loops; retry less greedily, then give up on this call.
                if attempt == 2:
                    print("ollama gave up (repetition):", str(e)[:80])
                    return ""
                options = {**options, "temperature": 0.3, "repeat_penalty": 1.15 + 0.1 * attempt}
                continue
            if attempt == 2:
                raise
            print("ollama retry:", e)
            time.sleep(3)
        except Exception as e:  # transient server errors: retry, then surface
            if attempt == 2:
                raise
            print("ollama retry:", e)
            time.sleep(3)


def chat_json(prompt, system=None, model=GEN_MODEL, **kw):
    """Ask for JSON output; returns {} when the model's output cannot be parsed."""
    text = chat(prompt, system, model, fmt="json", **kw)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        try:
            return json.loads(m.group()) if m else {}
        except json.JSONDecodeError:
            return {}
