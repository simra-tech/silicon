#!/usr/bin/env bash
# joint_r4_mc_20260928 launcher: seeds 79001-79024 (the r3 seeds) on CPUs 96-119, one seed per CPU, nice 0,
# detached via flow/launch_pinned.sh (wall bound 40000 s per seed, as r3). REPO = repository root, BULK_ROOT = bulk root.
set -eu
cd ${REPO}
export BULK=${BULK_ROOT}
B=$BULK/r4-20260927/jointmc
mkdir -p $B/logs
[ "$(nice)" = 0 ] || { echo "refusing to launch at nice $(nice)"; exit 1; }
i=0; for cpu in $(seq 96 119); do
  s=$((79001+i))
  flow/launch_pinned.sh $cpu designs/g1-guardian/blocks/g1_trip/sim 40000 $B/logs/s$s.log \
    python3 qualification/joint_r4_mc_20260928/runner_r4mc.py --seed $s --bulk $B --summary-dir $B/summaries
  i=$((i+1))
done
echo "launched $(date -Is) nice=$(nice)"
