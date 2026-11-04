"""Build colab/ViKAG_Faith_Colab.ipynb: the whole model-heavy pipeline (steps 1-5, 8, 9 and the verifier
ablation) for a Colab T4.

The notebook embeds the current src/*.py files, so it always runs the same code as this repo.
Outputs persist in Google Drive (MyDrive/vikag-faith/outputs), so a dropped session resumes.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = sorted((ROOT / "src").glob("*.py"))


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


cells = [
    md("""
# ViKAG-Faith — chạy pipeline trên Colab GPU

1. **Runtime → Change runtime type → T4 GPU**, rồi **Runtime → Run all**.
2. Khi được hỏi, cho phép kết nối Google Drive (kết quả lưu ở `MyDrive/vikag-faith/outputs`).
3. Bước 1–5 đã chạy xong trước đây sẽ tự bỏ qua; phần bổ sung (s9, s8, ablation) mất khoảng 1–1,5 giờ.
   Nếu phiên bị ngắt, chỉ cần **Run all** lại: các bước đã xong sẽ được bỏ qua.
4. Cuối cùng tải `MyDrive/vikag-faith/vikag_outputs.zip` về máy và giải nén vào `C:\\Users\\Admin\\vikag-faith\\`.
"""),
    code("""
!nvidia-smi --query-gpu=name,memory.total --format=csv
import torch
assert torch.cuda.is_available(), "Chưa bật GPU: Runtime → Change runtime type → T4 GPU"
"""),
    code("""
from google.colab import drive
drive.mount('/content/drive')
"""),
    md("## Mã nguồn dự án (sinh tự động từ `src/`)"),
    code("!mkdir -p /content/vikag-faith/src"),
]
for f in SRC:
    cells.append(code(f"%%writefile /content/vikag-faith/src/{f.name}\n" + f.read_text(encoding="utf-8")))

cells += [
    md("## Cài đặt: ViHERMES, thư viện Python, Ollama + mô hình"),
    code("""
%%bash
set -eo pipefail
DRIVE=/content/drive/MyDrive/vikag-faith
mkdir -p $DRIVE/outputs/logs
cd /content/vikag-faith
[ -L outputs ] || ln -s $DRIVE/outputs outputs
mkdir -p data models
[ -d external/ViHERMES ] || git clone -q --depth 1 https://github.com/ura-hcmut/ViHERMES.git external/ViHERMES
pip install -q -e external/ViHERMES ollama datasets sentencepiece scikit-learn
echo ok
"""),
    code("""
%%bash
set -eo pipefail
apt-get -qq install -y zstd > /dev/null
command -v ollama > /dev/null || (curl -fsSL https://ollama.com/install.sh | sh > /dev/null)
pgrep -x ollama > /dev/null || (nohup ollama serve > /content/ollama.log 2>&1 &)
sleep 5
for m in qwen2.5:3b qwen2.5:7b bge-m3; do ollama pull $m > /dev/null 2>&1; done
ollama list
"""),
    code("""
%%bash
set -eo pipefail
cd /content/vikag-faith/external/ViHERMES
[ -f ../../data/graph.db ] || (vihermes extract-contexts --qa dataset/dataset.jsonl --output ../../data/contexts.csv \\
  && vihermes ingest --input ../../data/contexts.csv --db ../../data/graph.db)
"""),
    md("## Chạy pipeline (GPU)"),
    code("""
import os
os.environ["VIKAG_CPU"] = "0"      # dùng GPU T4
os.environ["VIKAG_VINLI"] = "12000"  # số cặp ViNLI để fine-tune verifier
os.chdir("/content/vikag-faith/src")
"""),
    code("# Bước 1: 2 hệ trả lời 100 câu hỏi (tự bỏ qua câu đã xong)\n!python s1_answer.py"),
    code("# Bước 2: tách claim\n!test -f ../outputs/claims.jsonl || python s2_claims.py 2>&1 | tail -n 3"),
    code("# Bước 3: tập bằng chứng + chọn mẫu gán nhãn\n!test -f ../outputs/sample.jsonl || python s3_pool.py"),
    code("# Bước 4: RAGAS + LLM-judge với qwen2.5:3b và qwen2.5:7b (bỏ qua câu đã chấm)\n!python s4_judges.py qwen2.5:3b qwen2.5:7b"),
    md("## Bổ sung: baseline SelfCheckGPT (s9) và verify-then-revise (s8, RQ3)"),
    code("# Bước 9a: 3 câu trả lời lấy mẫu (temperature 0,7) cho mỗi câu hỏi trong mẫu\n"
         "!python s9_selfcheck.py gen 2>&1 | tee ../outputs/logs/s9_gen.log | tail -n 3"),
    code("# Bước 8: judge 7B gắn cờ claim sai -> 3B viết lại -> tách claim + chấm lại (tối đa 2 vòng)\n"
         "!python s8_revise.py 2>&1 | tee ../outputs/logs/s8_revise.log | tail -n 5"),
    code("# Giải phóng VRAM của Ollama trước khi dùng mDeBERTa\n!for m in qwen2.5:3b qwen2.5:7b bge-m3; do ollama stop $m; done"),
    code("""
%%bash
# Bước 5 + ablation: verifier huấn luyện bằng float32 (checkpoint lưu fp16; các lần trước train
# fp16 nên loss = nan). Train bản chính (ViNLI + tổng hợp) và bản "nosynth" (chỉ ViNLI), rồi chấm
# lại toàn bộ bằng fp32. Xong thì ghi dấu logs/fp32_done để lần Run all sau bỏ qua.
set -eo pipefail
[ -f ../outputs/logs/fp32_done ] && { echo "verifier fp32: đã xong, bỏ qua"; exit 0; }
python s5_verifier.py data 2>&1 | tail -n 2
python s5_verifier.py train 2>&1 | grep -E 'transformers|train rows|dev acc|step|best|Error' | tee ../outputs/logs/s5_train_ft_fp32.log
VIKAG_NO_SYNTH=1 VIKAG_FT_TAG=nosynth python s5_verifier.py train 2>&1 \\
  | grep -E 'transformers|train rows|dev acc|step|best|Error' | tee ../outputs/logs/s5_train_nosynth_fp32.log
VIKAG_FORCE=1 python s5_verifier.py predict 2>&1 | tail -n 3
VIKAG_FORCE=1 VIKAG_FT_TAG=nosynth python s5_verifier.py predict 2>&1 | tail -n 3
python s9_selfcheck.py nli 2>&1 | tail -n 2
touch ../outputs/logs/fp32_done
"""),
    md("## Đóng gói kết quả"),
    code("""
%%bash
cd /content/drive/MyDrive/vikag-faith
rm -f vikag_outputs.zip
zip -qr vikag_outputs.zip outputs
ls -la outputs vikag_outputs.zip
"""),
]

nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": [], "gpuType": "T4"},
      "kernelspec": {"name": "python3", "display_name": "Python 3"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
out = ROOT / "colab" / "ViKAG_Faith_Colab.ipynb"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(out, len(cells), "cells")
