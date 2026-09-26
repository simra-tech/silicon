#!/usr/bin/env bash
# Resume watcher (home quota full at 16:44): when a seed's runner has exited without a final summary,
# restart it with runner_r3mc_r2.py --resume on the same CPU; summaries go to $B/summaries.
set -u
cd ${REPO}
export BULK=${BULK_ROOT}
B=$BULK/joint_r3_mc_20260926
Q=designs/g1-guardian/blocks/g1_trip/sim/qualification/joint_r3_mc_20260926
declare -A cpu=([79018]=80 [79019]=82 [79021]=110 [79022]=112 [79023]=109 [79024]=100)
declare -A tries
final() { python3 - "$1" <<'PY'
import json,sys
for p in [sys.argv[1]]:
    try:
        d=json.load(open(p)); sys.exit(0 if d['status']!='running' else 1)
    except Exception: sys.exit(1)
PY
}
while :; do
  left=0
  for s in "${!cpu[@]}"; do
    if final $B/summaries/s$s/summary.json || final $Q/s$s/summary.json; then continue; fi
    left=$((left+1))
    pgrep -f "runner_r3mc(_r2)?\.py --seed $s" >/dev/null && continue
    t=${tries[$s]:-0}; [ $t -ge 500 ] && continue
    tries[$s]=$((t+1))
    flow/launch_pinned.sh ${cpu[$s]} designs/g1-guardian/blocks/g1_trip/sim 40000 $B/logs/s$s.resume$t.log \
      python3 ${BULK_ROOT}/joint_r3_mc_20260926/runner_r3mc_r2.py --seed $s --bulk $B --summary-dir $B/summaries --resume
    echo "$(date -Is) resumed seed $s on cpu ${cpu[$s]} attempt $t nice=$(nice)"
  done
  [ $left -eq 0 ] && break
  sleep 60
done
echo "$(date -Is) all done"
