"""Build colab/ViKAG_Faith_Dot2.ipynb: the second round closing proposal gaps on a free Colab T4.

Inputs come from the public repository. Every result goes to its own file (verifier_scores_dot2.jsonl,
judges_dot2.jsonl, judges_span.jsonl), so results.json from the first round never changes. Each step leaves a marker, so Run all resumes after a drop.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


cells = [
    md("""
# ViKAG-Faith, đợt 2: phần cần GPU của Colab

Fine-tune 20.000 cặp đã chạy xong trên máy, notebook này chỉ làm phần còn lại:

| Phần | Việc | Ước tính |
|---|---|---|
| 1 | Judge và RAGAS Qwen2.5-14B | 45 phút |
| 2 | Verifier Qwen nhỏ trả nhãn và span | 20 phút |
| 3 | XLM-R zero-shot | 15 phút |
| 4 | Chuẩn bị 20.000 cặp với cửa sổ 900 ký tự | 5 phút |
| 5 | XLM-R fine-tune | 30 phút |
| 6 | mDeBERTa fine-tune với 900 ký tự, 320 token | 40 phút |

Thời gian chỉ là ước tính, chưa đo trên T4.

1. **Runtime → Change runtime type → T4 GPU**, rồi **Runtime → Run all**. Cho phép kết nối Google Drive.
2. Dữ liệu tự tải từ GitHub, không cần chuẩn bị gì trên Drive.
3. Nếu phiên bị ngắt, chỉ cần **Run all** lại: phần đã xong sẽ tự bỏ qua. Nếu hết thời gian, phần đã xong vẫn dùng được.
4. Sau mỗi phần, file `MyDrive/vikag-faith/vikag_dot2.zip` được cập nhật. Gửi file này lại khi xong, kể cả khi chỉ xong phần 1.
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
    md("## Mã nguồn (sinh tự động từ `src/`)"),
    code("!mkdir -p /content/vikag-faith/src"),
]
for f in sorted((ROOT / "src").glob("*.py")):
    cells.append(code(f"%%writefile /content/vikag-faith/src/{f.name}\n" + f.read_text(encoding="utf-8")))

PACK = "bash /content/pack.sh"
cells += [
    md("## Cài đặt: dữ liệu từ GitHub, thư viện, Ollama"),
    code("""
%%bash
set -eo pipefail
DRIVE=/content/drive/MyDrive/vikag-faith
mkdir -p $DRIVE/outputs/logs
cd /content/vikag-faith
[ -L outputs ] || ln -s $DRIVE/outputs outputs
mkdir -p data models
[ -d /content/repo ] || git clone -q --depth 1 https://github.com/vinhha195-oss/vikag-faith.git /content/repo
cp -n /content/repo/outputs/*.jsonl /content/repo/outputs/*.json outputs/ || true
pip install -q ollama "transformers==4.46.3" "tokenizers==0.20.3" "datasets==5.0.1" sentencepiece scikit-learn protobuf
for f in sample.jsonl pools.jsonl claims.jsonl answers.jsonl triple_index.json verifier_scores_dot2.jsonl; do test -s outputs/$f || { echo "THIẾU outputs/$f"; exit 1; }; done
cat > /content/pack.sh <<'EOS'
cd /content/drive/MyDrive/vikag-faith
rm -f vikag_dot2.zip
zip -qr vikag_dot2.zip outputs/verifier_scores_dot2.jsonl outputs/judges_dot2.jsonl outputs/judges_span.jsonl outputs/logs
ls -la vikag_dot2.zip
EOS
echo ok
"""),
    code("""
%%bash
set -eo pipefail
apt-get -qq install -y zstd > /dev/null
command -v ollama > /dev/null || (curl -fsSL https://ollama.com/install.sh | sh > /dev/null)
pgrep -x ollama > /dev/null || (nohup ollama serve > /content/ollama.log 2>&1 &)
sleep 5
ollama --version
"""),
    code("""
import os
os.environ["VIKAG_CPU"] = "0"
os.environ["VIKAG_VINLI"] = "12000"
os.environ["VIKAG_SCORE_FILE"] = "verifier_scores_dot2.jsonl"
os.chdir("/content/vikag-faith/src")
"""),
    md("## Phần 1. LLM-judge và RAGAS với Qwen2.5-14B"),
    code("""
%%bash
set -eo pipefail
M=../outputs/logs/dot2_judge14_done
[ -f $M ] && { echo "đã xong, bỏ qua"; exit 0; }
ollama pull qwen2.5:14b > /dev/null 2>&1
VIKAG_JUDGE_FILE=judges_dot2.jsonl python s4_judges.py qwen2.5:14b 2>&1 | tail -n 2
ollama stop qwen2.5:14b || true
touch $M
""" + PACK),
    md("## Phần 2. Verifier Qwen nhỏ trả nhãn và span"),
    code("""
%%bash
set -eo pipefail
M=../outputs/logs/dot2_span_done
[ -f $M ] && { echo "đã xong, bỏ qua"; exit 0; }
ollama pull qwen2.5:3b > /dev/null 2>&1
VIKAG_SPAN=1 python s4_judges.py qwen2.5:3b 2>&1 | tail -n 2
ollama stop qwen2.5:3b || true
touch $M
""" + PACK),
    md("## Phần 3. XLM-R zero-shot"),
    code("""
%%bash
set -eo pipefail
M=../outputs/logs/dot2_xzs_done
[ -f $M ] && { echo "đã xong, bỏ qua"; exit 0; }
VIKAG_BASE=joeddav/xlm-roberta-large-xnli VIKAG_ZS_NAME=xzs VIKAG_FT_TAG=xft VIKAG_PRED_BS=16 VIKAG_VARIANTS=v1,v3 VIKAG_SKIP_FT=1 python s5_verifier.py predict 2>&1 | tail -n 2
touch $M
""" + PACK),
    md("## Phần 4. Chuẩn bị 20.000 cặp với cửa sổ 900 ký tự"),
    code("""
%%bash
set -eo pipefail
[ -d ../external/ViHERMES ] || git clone -q --depth 1 https://github.com/ura-hcmut/ViHERMES.git ../external/ViHERMES
pip install -q -e ../external/ViHERMES
cd ../external/ViHERMES
[ -f ../../data/contexts.csv ] || vihermes extract-contexts --qa dataset/dataset.jsonl --output ../../data/contexts.csv
cd ../../src
[ -f ../data/verifier_train_20k.jsonl ] || VIKAG_DATA_TAG=_20k VIKAG_SYNTH_TARGET=20000 python s5_verifier.py data 2>&1 | tail -n 2 | tee ../outputs/logs/dot2_data.log
"""),
    md("## Phần 5. XLM-R fine-tune"),
    code("""
%%bash
set -eo pipefail
M=../outputs/logs/dot2_xft_done
[ -f $M ] && { echo "đã xong, bỏ qua"; exit 0; }
export VIKAG_BASE=joeddav/xlm-roberta-large-xnli VIKAG_ZS_NAME=xzs VIKAG_FT_TAG=xft
VIKAG_BS=8 VIKAG_ACCUM=2 VIKAG_EVAL_EVERY=400 VIKAG_DATA_TAG=_20k VIKAG_MAX_RUN=16000 python s5_verifier.py train 2>&1 \\
  | grep -E 'transformers|train rows|dev acc|step|best|final|Error' | tee ../outputs/logs/dot2_train_xft.log | tail -n 4
VIKAG_PRED_BS=16 VIKAG_VARIANTS=v1,v3 VIKAG_SKIP_ZS=1 python s5_verifier.py predict 2>&1 | tail -n 3
touch $M
""" + PACK),
    md("## Phần 6. mDeBERTa fine-tune với 900 ký tự, 320 token, cùng đầu vào với đợt 1"),
    code("""
%%bash
set -eo pipefail
M=../outputs/logs/dot2_ft20full_done
[ -f $M ] && { echo "đã xong, bỏ qua"; exit 0; }
VIKAG_BS=16 VIKAG_ACCUM=1 VIKAG_EVAL_EVERY=400 VIKAG_DATA_TAG=_20k VIKAG_FT_TAG=ft20full python s5_verifier.py train 2>&1 \\
  | grep -E 'transformers|train rows|dev acc|step|best|final|Error' | tee ../outputs/logs/dot2_train_ft20full.log | tail -n 4
VIKAG_PRED_BS=32 VIKAG_VARIANTS=v1,v3 VIKAG_SKIP_ZS=1 VIKAG_FT_TAG=ft20full python s5_verifier.py predict 2>&1 | tail -n 3
touch $M
""" + PACK),
]

nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": [], "gpuType": "T4"},
      "kernelspec": {"name": "python3", "display_name": "Python 3"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
out = ROOT / "colab" / "ViKAG_Faith_Dot2.ipynb"
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(out, len(cells), "cells")
