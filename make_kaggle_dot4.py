"""Build kaggle/ViKAG_Dot4.ipynb: parts B, C and D of round four (src/s19_dot4.py, src/s22_record.py) on Kaggle.

Used when the free Colab GPU quota is spent. Kaggle runs the notebook as a background commit, so no browser has to
stay open. The round-3 XLM-R verifier (verifier_xhard) is read from a Kaggle dataset if one is attached, otherwise
downloaded from the Drive folder below, which must be shared as "anyone with the link". Results land in
/kaggle/working/ as dot4_systems.jsonl, dot4_verify.jsonl and dot4_live.jsonl.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
XHARD_FOLDER = "1cc-0nsBzL2P9J-la7QaIgnMlPABH1RYt"  # MyDrive/vikag-faith/dot3/models/verifier_xhard


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t.strip("\n").splitlines(keepends=True)}


def part(script, arg, tag):
    # no "set -e": a failing part must not stop the later ones in a background commit
    return code(f"""
%%bash
cd /kaggle/working/vikag-faith/src
export VIKAG_CPU=0 PYTHONIOENCODING=utf8
python {script} {arg} 2>&1 | grep --line-buffered -E "{tag} [0-9]+/|Error|Traceback|error" | awk 'NR % 5 == 1 || /Error|Traceback|error/'
cp ../outputs/dot4_*.jsonl /kaggle/working/ 2>/dev/null; wc -l /kaggle/working/dot4_*.jsonl
""")


cells = [
    md("""
# ViKAG-Faith, đợt 4 trên Kaggle: ba hệ mới, toán tử Verify, chạy sẵn 8 câu cho demo

1. Bên phải: **Settings → Accelerator → GPU T4 x2**, **Internet → On**.
2. Bấm **Save Version → Save & Run All (Commit)**. Chạy nền khoảng 4–5 giờ, đóng trình duyệt cũng được.
3. Xong: mở phiên bản đó → **Output** → tải `dot4_systems.jsonl`, `dot4_verify.jsonl`, `dot4_live.jsonl`, nhắn Claude.
"""),
    code("!nvidia-smi --query-gpu=name,memory.total --format=csv"),
    code(f"""
%%bash
set -eo pipefail
cd /kaggle/working
echo "1. kiểm tra Internet"; curl -sI -m 10 https://github.com > /dev/null || {{ echo "KHÔNG CÓ INTERNET: Settings -> Internet -> On"; exit 1; }}
echo "2. tải mã nguồn"; [ -d vikag-faith ] || git clone -q --depth 1 https://github.com/vinhha195-oss/vikag-faith.git
cd vikag-faith; mkdir -p data models outputs/logs
echo "3. cài thư viện"; pip install -q ollama gdown "transformers==4.46.3" "tokenizers==0.20.3" sentencepiece scikit-learn protobuf "gradio<6" 2>&1 | tail -n 2
echo "4. mô hình XLM-R đợt 3"
SRC=$(dirname "$(find /kaggle/input -name model.safetensors -path '*xhard*' 2>/dev/null | head -n 1)" 2>/dev/null || true)
if [ -n "$SRC" ] && [ "$SRC" != "." ]; then cp -r "$SRC" models/verifier_xhard
else gdown -q --folder "https://drive.google.com/drive/folders/{XHARD_FOLDER}" -O models/verifier_xhard \\
  || {{ echo "KHÔNG TẢI ĐƯỢC MÔ HÌNH: chia sẻ thư mục verifier_xhard trên Drive ở chế độ 'Bất kỳ ai có đường liên kết'"; exit 1; }}
fi
[ -f models/verifier_xhard/model.safetensors ] || mv models/verifier_xhard/*/* models/verifier_xhard/ 2>/dev/null || true
ls -la models/verifier_xhard
echo "5. cài và chạy Ollama"; (apt-get -qq update && apt-get -qq install -y zstd) > /dev/null 2>&1 || true
command -v ollama > /dev/null || curl -fsSL https://ollama.com/install.sh | sh 2>&1 | tail -n 2
(nohup ollama serve > /kaggle/working/ollama.log 2>&1 &); sleep 10
echo "6. tải mô hình Qwen và bge-m3"; for m in qwen2.5:3b qwen2.5:7b qwen2.5:14b bge-m3; do ollama pull $m > /dev/null 2>&1; done
ollama list
echo "7. đồ thị ViHERMES"
[ -d external/ViHERMES ] || git clone -q --depth 1 https://github.com/ura-hcmut/ViHERMES.git external/ViHERMES
pip install -q -e external/ViHERMES 2>&1 | tail -n 1
cd external/ViHERMES
[ -f ../../data/graph.db ] || (vihermes extract-contexts --qa dataset/dataset.jsonl --output ../../data/contexts.csv \\
  && vihermes ingest --input ../../data/contexts.csv --db ../../data/graph.db)
ls -la ../../data
"""),
    md("## Phần B. Ba hệ mới (BM25, vector, Qwen 7B) cho 40 câu hỏi"),
    part("s19_dot4.py", "systems", "systems"),
    md("## Phần C. Toán tử Verify kiểu KAG, chấm lại bằng judge 14B"),
    part("s19_dot4.py", "verify", "verify"),
    md("## Phần D. Chạy sẵn 8 câu hỏi qua chatbot, cho tab \"Thử trực tiếp\" của demo"),
    part("s22_record.py", "", "live"),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
      "language_info": {"name": "python"}, "kaggle": {"accelerator": "nvidiaTeslaT4", "isInternetEnabled": True, "isGpuEnabled": True}},
      "nbformat": 4, "nbformat_minor": 4}
out = ROOT / "kaggle" / "ViKAG_Dot4.ipynb"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(out, len(cells), "cells")
