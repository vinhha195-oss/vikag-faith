#!/usr/bin/env bash
# Second-round fine-tune on the local GTX 1650: mDeBERTa only, never Qwen.
# 450-character premises and 200 tokens instead of 900 and 320, because the card has 4 GB; same effective batch of 16.
cd /c/Users/Admin/vikag-faith/src || exit 1
export VIKAG_CPU=0 HF_HUB_OFFLINE=1 PYTHONIOENCODING=utf8 VIKAG_SCORE_FILE=verifier_scores_dot2.jsonl VIKAG_FT_TAG=ft20
LOG=../outputs/logs/dot2_gpu.log
say() { echo "$(date '+%m-%d %H:%M') $*" | tee -a "$LOG"; }
( while sleep 600; do say "gpu $(nvidia-smi --query-gpu=temperature.gpu,memory.used,power.draw --format=csv,noheader)"; done ) &
WATCH=$!

say "training ft20 on 30k pairs"
VIKAG_DATA_TAG=_20k450 VIKAG_TRAIN_MAX_LEN=200 VIKAG_EVAL_EVERY=600 VIKAG_DEV_MAX=1000 ../.venv/Scripts/python -u s5_verifier.py train > ../outputs/logs/dot2_train_ft20.log 2>&1
say "training exit $?: $(grep -E 'best dev|final dev' ../outputs/logs/dot2_train_ft20.log | tail -n 1)"
if [ -f ../models/verifier_ft20/config.json ]; then
  VIKAG_PRED_BS=4 VIKAG_VARIANTS=v1,v3 VIKAG_SKIP_ZS=1 ../.venv/Scripts/python -u s5_verifier.py predict > ../outputs/logs/dot2_local_ft20.log 2>&1
  say "scoring exit $?"
fi
../.venv/Scripts/python s10_dot2.py > ../outputs/logs/dot2_results.txt 2>&1
say "analysis exit $?"
kill $WATCH
