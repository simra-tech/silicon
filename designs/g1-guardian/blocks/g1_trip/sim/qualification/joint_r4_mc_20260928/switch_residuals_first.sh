#!/usr/bin/env bash
# joint_r4_mc_20260928, 2026-09-27 ~23:40 CEST: the probes run ~1.5x slower than in r3 (the SMT siblings of CPUs 96-119
# are busy), so the full 28-probe sequence would end near the 06:00 deadline and the 125 C residual probes, which
# run last, would be the ones lost. For every seed still in calibration (leaf index <= 9) this script waits until a new
# probe has just started (< 45 s), stops that runner and its ngspice, and restarts the seed on the same CPU with
# runner_r4mc.py --resume --residuals-first. The resume re-analyses the finished leaves (identical decks) and re-simulates
# the interrupted one; the guard and residual probes are unchanged, only their order (residuals first).
# REPO = repository root, BULK_ROOT = bulk root.
set -u
cd ${REPO}
export BULK=${BULK_ROOT}
B=$BULK/r4-20260927/jointmc
switch() { # seed
  local s=$1 cpu=$((96 + $1 - 79001))
  while :; do
    [ -f $B/logs/s$s.log.rc ] && { echo "$(date -Is) $s runner already ended, not switched"; return; }
    local leaf=$(ls -d $B/s$s/p[0-9][0-9] 2>/dev/null | sort | tail -1)
    local idx=$((10#${leaf##*/p}))
    if [ $idx -gt 9 ]; then echo "$(date -Is) $s already past calibration (p$idx), not switched"; return; fi
    local age=$(( $(date +%s) - $(stat -c %Y $leaf/probe.cir 2>/dev/null || echo 0) ))
    if [ -f $leaf/probe.cir ] && [ $age -lt 45 ]; then
      local py=$(ps -eo pid,args | awk -v s="$s" '$2=="python3" && index($0,"runner_r4mc.py --seed " s " ") {print $1}')
      local ng=$(ps -eo pid,args | awk -v s="$s" '$2=="ngspice" && index($0,"/s" s "/p") {print $1}')
      echo "$(date -Is) $s stopping at ${leaf##*/} (age ${age} s): python $py ngspice $ng"
      kill $py $ng 2>/dev/null
      while [ ! -f $B/logs/s$s.log.rc ]; do sleep 2; done
      flow/launch_pinned.sh $cpu designs/g1-guardian/blocks/g1_trip/sim 40000 $B/logs/s$s.resfirst.log \
        python3 qualification/joint_r4_mc_20260928/runner_r4mc.py --seed $s --bulk $B --summary-dir $B/summaries --resume --residuals-first
      echo "$(date -Is) $s relaunched on cpu $cpu nice=$(nice)"
      return
    fi
    sleep 5
  done
}
for s in $(seq 79001 79024); do [ $s = 79021 ] && continue; switch $s & done
wait
echo "$(date -Is) switch done"
