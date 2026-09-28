#!/usr/bin/env bash
# joint_r4_mc_20260928, 2026-09-27 ~23:40 CEST: repair of the switch. switch_residuals_first.sh was started as a background
# job of the interactive shell and therefore ran at nice 5, and runner --resume treats a leaf whose ngspice was killed
# (run.json terminal, returncode -15) as finished, so every switched seed ended at once with a numerical calibration
# failure on the killed leaf. Those killed leaves (wall < 60 s, rc -15) were renamed pNN.killed; this script relaunches
# the 23 seeds at nice 0 with --resume --residuals-first (finished leaves re-analysed, the killed one re-simulated).
set -eu
cd ${REPO}
export BULK=${BULK_ROOT}
B=$BULK/r4-20260927/jointmc
[ "$(nice)" = 0 ] || { echo "refusing to launch at nice $(nice)"; exit 1; }
for s in $(seq 79001 79024); do
  [ $s = 79021 ] && continue
  flow/launch_pinned.sh $((96 + s - 79001)) designs/g1-guardian/blocks/g1_trip/sim 40000 $B/logs/s$s.relaunch.log \
    python3 qualification/joint_r4_mc_20260928/runner_r4mc.py --seed $s --bulk $B --summary-dir $B/summaries --resume --residuals-first
done
echo "relaunched $(date -Is) nice=$(nice)"
