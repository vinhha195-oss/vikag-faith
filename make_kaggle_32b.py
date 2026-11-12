"""Build kaggle/ViKAG_Judge32B.ipynb: LLM-judge and RAGAS with Qwen2.5-32B on Kaggle's two T4 GPUs.

Qwen2.5-32B (Q4_K_M, about 20 GB) does not fit one 16 GB T4, but Ollama splits it across the two T4s that Kaggle
offers. Run it as a background commit ("Save Version" -> "Save & Run All"), which needs no open browser; the result
is /kaggle/working/judges_32b.jsonl in the notebook output. s4_judges.py resumes from that file if rerun.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t.strip("\n").splitlines(keepends=True)}


cells = [
    md("""
# ViKAG-Faith: LLM-judge và RAGAS với Qwen2.5-32B (Kaggle, 2 × T4)

1. Bên phải: **Settings → Accelerator → GPU T4 x2**, và **Internet → On** (cần tài khoản đã xác minh số điện thoại).
2. Bấm **Save Version → Save & Run All (Commit)**. Notebook chạy nền, đóng trình duyệt cũng được; tối đa 12 giờ.
3. Chạy xong, mở phiên bản đó → **Output** → tải `judges_32b.jsonl`, chép vào `vikag-faith/outputs/`, nhắn Claude.
"""),
    code("!nvidia-smi --query-gpu=name,memory.total --format=csv"),
    code("""
%%bash
set -eo pipefail
cd /kaggle/working
echo "1. kiểm tra Internet"; curl -sI -m 10 https://github.com > /dev/null || { echo "KHÔNG CÓ INTERNET: Settings -> Internet -> On (cần xác minh số điện thoại)"; exit 1; }
echo "2. tải mã nguồn"; [ -d vikag-faith ] || git clone -q --depth 1 https://github.com/vinhha195-oss/vikag-faith.git
echo "3. cài thư viện"; pip install -q ollama
echo "4. cài Ollama"; (apt-get -qq update && apt-get -qq install -y zstd) > /dev/null 2>&1 || true
command -v ollama > /dev/null || curl -fsSL https://ollama.com/install.sh | sh 2>&1 | tail -n 3
echo "5. chạy Ollama"; (nohup ollama serve > /kaggle/working/ollama.log 2>&1 &); sleep 10
echo "6. tải Qwen2.5-32B (khoảng 20 GB)"; ollama pull qwen2.5:32b 2>&1 | tail -n 2
ollama list
"""),
    code("""
%%bash
cd /kaggle/working/vikag-faith/src
export VIKAG_CPU=0 VIKAG_JUDGE_FILE=judges_32b.jsonl PYTHONIOENCODING=utf8
python s4_judges.py qwen2.5:32b 2>&1 | tail -n 5
cp ../outputs/judges_32b.jsonl /kaggle/working/judges_32b.jsonl
wc -l /kaggle/working/judges_32b.jsonl
nvidia-smi --query-gpu=memory.used --format=csv
"""),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
      "language_info": {"name": "python"}, "kaggle": {"accelerator": "nvidiaTeslaT4", "isInternetEnabled": True, "isGpuEnabled": True}},
      "nbformat": 4, "nbformat_minor": 4}
out = ROOT / "kaggle" / "ViKAG_Judge32B.ipynb"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(out)
