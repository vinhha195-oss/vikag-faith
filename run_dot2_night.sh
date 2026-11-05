#!/usr/bin/env bash
# Unattended overnight run on this PC: mDeBERTa only, CPU, 3 threads, idle priority, never Qwen.
# Waits for the running V3 scoring, trains on the 20k set, rescores, analyses, then shuts the PC down.
# Training stops at TRAIN_STOP and the best checkpoint saved so far is used, so a result always exists.
cd /c/Users/Admin/vikag-faith/src || exit 1
export VIKAG_CPU=1 OMP_NUM_THREADS=3 MKL_NUM_THREADS=3 CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 PYTHONIOENCODING=utf8
export VIKAG_SCORE_FILE=verifier_scores_dot2.jsonl
LOG=../outputs/logs/dot2_night.log
TRAIN_STOP=05:00
say() { echo "$(date '+%m-%d %H:%M') $*" | tee -a "$LOG"; }
low() { powershell -NoProfile -Command "Get-Process python -ErrorAction SilentlyContinue | Where-Object { \$_.StartTime -gt (Get-Date).AddMinutes(-3) } | ForEach-Object { \$_.PriorityClass='Idle' }" > /dev/null 2>&1; }
worker() { powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | Where-Object { \$_.CommandLine -like '*s5_verifier.py $1*' } | Select-Object -ExpandProperty ProcessId"; }

say "start; waiting for V3 scoring"
while [ -n "$(worker predict)" ]; do sleep 60; done
say "V3 scoring finished: $(tail -n 1 ../outputs/logs/dot2_local_zs_v3.log)"

say "training ft20"
VIKAG_DATA_TAG=_20k VIKAG_FT_TAG=ft20 VIKAG_EVAL_EVERY=500 ../.venv/Scripts/python -u s5_verifier.py train > ../outputs/logs/dot2_train_ft20.log 2>&1 &
sleep 45; low
stopped=no
while [ -n "$(worker train)" ]; do
  now=$(date +%H:%M)
  if [[ "$now" > "$TRAIN_STOP" && "$now" < "12:00" ]]; then
    for p in $(worker train); do taskkill //F //PID "$p" > /dev/null 2>&1; done
    stopped=yes
    say "training stopped at the time limit; using the best checkpoint saved so far"
    break
  fi
  sleep 60
done
say "training ended (stopped=$stopped): $(grep -E 'best dev|step ' ../outputs/logs/dot2_train_ft20.log | tail -n 1)"

if [ -f ../models/verifier_ft20/config.json ]; then
  say "scoring ft20"
  VIKAG_VARIANTS=v1,v3 VIKAG_SKIP_ZS=1 VIKAG_FT_TAG=ft20 ../.venv/Scripts/python -u s5_verifier.py predict > ../outputs/logs/dot2_local_ft20.log 2>&1 &
  sleep 45; low
  wait $!
  say "ft20 scoring exit $?"
fi

../.venv/Scripts/python s10_dot2.py > ../outputs/logs/dot2_results.txt 2>&1
say "analysis exit $?"
say "shutting down in 10 minutes; cancel with: shutdown /a"
shutdown //s //t 600 //c "ViKAG-Faith: dot 2 xong. Huy bang lenh: shutdown /a"
