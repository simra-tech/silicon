#!/usr/bin/env bash
# Replaces the batch-2 part of launch.sh (batch 1 = seeds 79001-79016 on CPUs 100-115 already running):
# start seeds 79017-79024 one per free CPU, at most 16 concurrent before 21:00 Europe/Berlin and 24 after,
# CPUs 100-115 first, then 80-87. A CPU is free when its last seed's launch_pinned .rc file exists.
set -eu
cd ${REPO}
export BULK=${BULK_ROOT}
B=$BULK/joint_r3_mc_20260926
declare -A busy   # cpu -> seed
for i in $(seq 0 15); do busy[$((100+i))]=$((79001+i)); done
pending=($(seq 79017 79024))
t21=$(TZ=Europe/Berlin date -d '21:00' +%s)
while [ ${#pending[@]} -gt 0 ]; do
  running=0
  for c in "${!busy[@]}"; do [ -f $B/logs/s${busy[$c]}.log.rc ] && unset busy[$c] || running=$((running+1)); done
  cap=16; [ $(date +%s) -ge $t21 ] && cap=24
  for c in $(seq 100 115) $(seq 80 87); do
    [ ${#pending[@]} -gt 0 ] && [ $running -lt $cap ] || break
    [ -n "${busy[$c]:-}" ] && continue
    s=${pending[0]}; pending=("${pending[@]:1}")
    flow/launch_pinned.sh $c designs/g1-guardian/blocks/g1_trip/sim 40000 $B/logs/s$s.log \
      python3 qualification/joint_r3_mc_20260926/runner_r3mc.py --seed $s --bulk $B
    busy[$c]=$s; running=$((running+1)); echo "$(date -Is) seed $s on cpu $c nice=$(nice) running=$running"
  done
  sleep 60
done
echo "$(date -Is) all seeds launched"
