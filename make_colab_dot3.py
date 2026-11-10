"""Build colab/ViKAG_Faith_Dot3.ipynb: third round on a free Colab T4.

Part A trains XLM-R on pairs that include the error-shaped hard negatives (src/s14_hardneg.py) and scores the
284 claims; Part B starts the live demo (src/s16_live.py) with a public Gradio link. Results go to
MyDrive/vikag-faith/dot3/ and never overwrite earlier result files.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": text.strip("\n").splitlines(keepends=True)}


cells = [
    md("""
# ViKAG-Faith, đợt 3: verifier học lỗi thật và chatbot kiểm chứng trực tiếp

| Phần | Việc | Thời gian (đo ở đợt 2 với cấu hình tương tự) |
|---|---|---|
| Cài đặt | Mã nguồn, thư viện, Ollama, đồ thị ViHERMES | khoảng 10 phút |
| A | Luyện XLM-R với dữ liệu lỗi sát thực tế, chấm 284 ý | khoảng 70 phút |
| B | Chatbot kiểm chứng trực tiếp, có link công khai | chạy đến khi dừng |

1. **Runtime → Change runtime type → T4 GPU**, rồi **Runtime → Run all**. Cho phép kết nối Google Drive.
2. Xong phần A, file `MyDrive/vikag-faith/dot3/vikag_dot3.zip` xuất hiện trên Drive. Nhắn "check" để Claude lấy kết quả.
3. Phần B in ra một link dạng `https://....gradio.live`. Mở link đó để demo; link sống đến khi tắt Colab.
4. Nếu phiên bị ngắt, chạy lại **Run all**: phần A đã xong sẽ tự bỏ qua nhờ mô hình lưu trên Drive.
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
    md("## Cài đặt"),
    code("""
%%bash
set -eo pipefail
DRIVE=/content/drive/MyDrive/vikag-faith/dot3
mkdir -p $DRIVE/logs /content/vikag-faith/data /content/vikag-faith/models
rm -rf /content/repo && git clone -q --depth 1 https://github.com/vinhha195-oss/vikag-faith.git /content/repo
cd /content/vikag-faith
rm -rf src && cp -r /content/repo/src src
mkdir -p outputs/logs && cp -r /content/repo/outputs/* outputs/
pip install -q ollama "transformers==4.46.3" "tokenizers==0.20.3" "datasets==5.0.1" sentencepiece scikit-learn protobuf "gradio<6"
python - <<'EOS'
import gzip, shutil
for a, b in (("train_hard", "verifier_train_hard"), ("dev_hard", "verifier_dev_hard")):
    with gzip.open(f"outputs/hardneg/{a}.jsonl.gz", "rb") as s, open(f"data/{b}.jsonl", "wb") as d:
        shutil.copyfileobj(s, d)
EOS
wc -l data/verifier_train_hard.jsonl data/verifier_dev_hard.jsonl
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
cd /content/vikag-faith
[ -d external/ViHERMES ] || git clone -q --depth 1 https://github.com/ura-hcmut/ViHERMES.git external/ViHERMES
pip install -q -e external/ViHERMES
cd external/ViHERMES
[ -f ../../data/graph.db ] || (vihermes extract-contexts --qa dataset/dataset.jsonl --output ../../data/contexts.csv \\
  && vihermes ingest --input ../../data/contexts.csv --db ../../data/graph.db)
ls -la ../../data
"""),
    code("""
import os
os.environ["VIKAG_CPU"] = "0"
os.chdir("/content/vikag-faith/src")
"""),
    md("## Phần A. Luyện XLM-R với dữ liệu lỗi sát thực tế"),
    code("""
%%bash
set -eo pipefail
DRIVE=/content/drive/MyDrive/vikag-faith/dot3
export VIKAG_BASE=joeddav/xlm-roberta-large-xnli VIKAG_ZS_NAME=xzs VIKAG_FT_TAG=xhard
if [ -f $DRIVE/models/verifier_xhard/config.json ]; then
  echo "đã có mô hình trên Drive, bỏ qua bước luyện"; cp -r $DRIVE/models/verifier_xhard ../models/
else
  VIKAG_BS=8 VIKAG_ACCUM=2 VIKAG_EVAL_EVERY=400 VIKAG_DATA_TAG=_hard python s5_verifier.py train 2>&1 \\
    | grep -E 'transformers|train rows|dev acc|step|best|final|Error' | tee $DRIVE/logs/dot3_train_xhard.log | tail -n 4
  mkdir -p $DRIVE/models && cp -r ../models/verifier_xhard $DRIVE/models/ || echo "Drive không đủ chỗ, mô hình chỉ ở phiên này"
fi
VIKAG_SCORE_FILE=verifier_scores_dot3.jsonl VIKAG_PRED_BS=16 VIKAG_VARIANTS=v1,v3 VIKAG_SKIP_ZS=1 python s5_verifier.py predict 2>&1 | tail -n 3
python s15_hard_dev.py | tail -n 30
cp ../outputs/verifier_scores_dot3.jsonl ../outputs/logs/dot3_hard_dev.json $DRIVE/
cd $DRIVE && rm -f vikag_dot3.zip && zip -qr vikag_dot3.zip verifier_scores_dot3.jsonl dot3_hard_dev.json logs && ls -la vikag_dot3.zip
"""),
    md("## Phần B. Chatbot kiểm chứng trực tiếp\nChạy ô dưới, chờ dòng `Running on public URL: https://....gradio.live`, rồi mở link đó. Ô này chạy liên tục cho tới khi bấm dừng."),
    code("""
!cd /content/vikag-faith/src && VIKAG_CPU=0 python s16_live.py
"""),
]

nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": [], "gpuType": "T4"},
      "kernelspec": {"name": "python3", "display_name": "Python 3"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
out = ROOT / "colab" / "ViKAG_Faith_Dot3.ipynb"
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(out, len(cells), "cells")
