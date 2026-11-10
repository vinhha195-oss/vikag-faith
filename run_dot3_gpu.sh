#!/usr/bin/env bash
# Third-round fine-tune on the local GTX 1650: same recipe as run_dot2_gpu.sh (mDeBERTa, 450 characters, 200 tokens),
# but about 3,200 base pairs are replaced by error-shaped hard pairs (src/s14_hardneg.py with VIKAG_HARD_TAG=450).
cd /c/Users/Admin/vikag-faith/src || exit 1
export VIKAG_CPU=0 HF_HUB_OFFLINE=1 PYTHONIOENCODING=utf8 VIKAG_SCORE_FILE=verifier_scores_dot3.jsonl VIKAG_FT_TAG=fthard
LOG=../outputs/logs/dot3_gpu.log
say() { echo "$(date '+%m-%d %H:%M') $*" | tee -a "$LOG"; }
( while sleep 600; do say "gpu $(nvidia-smi --query-gpu=temperature.gpu,memory.used,power.draw --format=csv,noheader)"; done ) &
WATCH=$!

say "training fthard on 30k pairs"
VIKAG_DATA_TAG=_hard450 VIKAG_TRAIN_MAX_LEN=200 VIKAG_EVAL_EVERY=600 VIKAG_DEV_MAX=1000 ../.venv/Scripts/python -u s5_verifier.py train > ../outputs/logs/dot3_train_fthard.log 2>&1
say "training exit $?: $(grep -E 'best dev|final dev' ../outputs/logs/dot3_train_fthard.log | tail -n 1)"
if [ -f ../models/verifier_fthard/config.json ]; then
  VIKAG_PRED_BS=4 VIKAG_VARIANTS=v1,v3 VIKAG_SKIP_ZS=1 ../.venv/Scripts/python -u s5_verifier.py predict > ../outputs/logs/dot3_predict.log 2>&1
  say "scoring exit $?"
  VIKAG_HARD_TAG=450 VIKAG_HARD_MODELS="zs=MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7,ft20=../models/verifier_ft20,fthard=../models/verifier_fthard" \
    ../.venv/Scripts/python -u s15_hard_dev.py > ../outputs/logs/dot3_hard_dev.txt 2>&1
  say "hard dev exit $?"
fi
kill $WATCH
say "done"
