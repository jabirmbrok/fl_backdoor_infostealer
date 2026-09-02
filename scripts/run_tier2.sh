#!/usr/bin/env bash
# Run every Tier 2 job in order, one GPU job at a time.
# Skips any run whose output directory already exists, so it is safe to re-run.
#
#   bash scripts/run_tier2.sh
set -u

PY="${PY:-$HOME/anaconda3/envs/malware/python.exe}"
ORDER="configs/camera_ready/tier2/run_order.txt"
LOGDIR="results/logs"
mkdir -p "$LOGDIR"

declare -A SCRIPT=(
  [clean]="scripts/train_fl_clean.py"
  [backdoor]="scripts/train_fl_backdoor.py"
  [defense]="scripts/train_fl_backdoor_defense.py"
  [control]="scripts/evaluate_trigger_control.py"
)

total=$(wc -l < "$ORDER")
i=0
failed=0
start_all=$SECONDS

while IFS=$'\t' read -r kind cfg exp; do
  i=$((i + 1))
  if [ "$kind" = "control" ]; then
    out="results/trigger_control/${exp}.json"
  else
    out="results/${exp}/history.json"
  fi
  if [ -e "$out" ]; then
    echo "[$i/$total] skip (already present): $exp"
    continue
  fi

  echo "[$i/$total] $kind: $exp"
  t0=$SECONDS
  PYTHONIOENCODING=utf-8 "$PY" "${SCRIPT[$kind]}" --config "$cfg" > "$LOGDIR/${exp}.log" 2>&1
  rc=$?
  dt=$((SECONDS - t0))
  if [ $rc -ne 0 ]; then
    echo "    FAILED (exit $rc) after ${dt}s -- see $LOGDIR/${exp}.log"
    tail -3 "$LOGDIR/${exp}.log" | sed 's/^/    /'
    failed=$((failed + 1))
  else
    echo "    done in ${dt}s"
  fi
done < "$ORDER"

echo "Tier 2 finished in $((SECONDS - start_all))s; $failed job(s) failed."
exit $failed
