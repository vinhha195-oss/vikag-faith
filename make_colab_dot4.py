"""Build colab/ViKAG_Faith_Dot4.ipynb: fourth round on a free Colab T4 (src/s19_dot4.py).

Part A trains XLM-R on pairs that include the error-shaped hard negatives (src/s14_hardneg.py) and scores the
284 claims; Part B starts the live demo (src/s16_live.py) with a public Gradio link. Results go to
MyDrive/vikag-faith/dot4/ and never overwrite earlier result files.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": text.strip("\n").splitlines(keepends=True)}


RUN = """
%%bash
DRIVE=/content/drive/MyDrive/vikag-faith/dot4
cd /content/vikag-faith/src
VIKAG_CPU=0 PYTHONIOENCODING=utf8 python s19_dot4.py PART 2>&1 | grep --line-buffered -E "PART [0-9]+/|Error|Traceback" | awk 'NR % 5 == 1 || /Error|Traceback/'
cd $DRIVE && rm -f vikag_dot4.zip && zip -q vikag_dot4.zip dot4_*.jsonl && ls -la vikag_dot4.zip
"""

cells = [
    md("""
# ViKAG-Faith, đợt 4: ViEduReg, ba hệ mới, toán tử Verify

| Phần | Việc | Ước tính (chưa đo) |
|---|---|---|
| Cài đặt | Mã nguồn, thư viện, Ollama, đồ thị ViHERMES, mô hình XLM-R đợt 3 từ Drive | 15 phút |
| A | ViEduReg: 30 câu hỏi về văn bản kiểm định chất lượng giáo dục | 30 phút |
| B | Ba hệ mới (BM25, vector, Qwen 7B) cho 40 câu hỏi | 1,5–2 giờ |
| C | Toán tử Verify kiểu KAG trên 80 câu trả lời, chấm lại bằng judge 14B | 1,5 giờ |

1. **Runtime → Change runtime type → T4 GPU**, rồi **Runtime → Run all**. Cho phép Google Drive.
2. Sau mỗi phần, `MyDrive/vikag-faith/dot4/vikag_dot4.zip` được cập nhật. Nhắn "check" để Claude lấy kết quả.
3. Phiên bị ngắt thì **Run all** lại: phần đã xong được giữ trên Drive và tự chạy tiếp từ chỗ dừng.
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
DRIVE=/content/drive/MyDrive/vikag-faith/dot4
mkdir -p $DRIVE/logs /content/vikag-faith/data /content/vikag-faith/models
rm -rf /content/repo && git clone -q --depth 1 https://github.com/vinhha195-oss/vikag-faith.git /content/repo
cd /content/vikag-faith
rm -rf src && cp -r /content/repo/src src
mkdir -p outputs/logs && cp -r /content/repo/outputs/* outputs/
# results are written straight to Drive, so a dropped session keeps every finished answer
for f in dot4_edu.jsonl dot4_systems.jsonl dot4_verify.jsonl; do ln -sf $DRIVE/$f outputs/$f; done
[ -d models/verifier_xhard ] || cp -r /content/drive/MyDrive/vikag-faith/dot3/models/verifier_xhard models/
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
for m in qwen2.5:3b qwen2.5:7b qwen2.5:14b bge-m3; do ollama pull $m > /dev/null 2>&1; done
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
    md("## Phần A. ViEduReg"),
    code(RUN.replace("PART", "edu")),
    md("## Phần B. Ba hệ mới"),
    code(RUN.replace("PART", "systems")),
    md("## Phần C. Toán tử Verify kiểu KAG"),
    code(RUN.replace("PART", "verify")),
]

nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": [], "gpuType": "T4"},
      "kernelspec": {"name": "python3", "display_name": "Python 3"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
out = ROOT / "colab" / "ViKAG_Faith_Dot4.ipynb"
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(out, len(cells), "cells")
