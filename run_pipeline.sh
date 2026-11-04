#!/usr/bin/env bash
# Steps 1-4 on CPU; each step resumes or is cheap to rerun.
set -e
cd "$(dirname "$0")"
source .venv/Scripts/activate
cd src
python s1_answer.py >> ../outputs/s1.log 2>&1
python s2_claims.py  > ../outputs/s2.log 2>&1
python s3_pool.py    > ../outputs/s3.log 2>&1
python s4_judges.py >> ../outputs/s4.log 2>&1
echo PIPELINE_DONE >> ../outputs/s4.log
