#!/usr/bin/env bash
# Dispatcher r2: pending seeds one per free, uncontended CPU (no other process >20 % CPU pinned there);
# at most 16 concurrent before 21:00 Europe/Berlin, 24 after; CPUs 100-115 (except 104, 106) first, then 80-87.
set -eu
cd ${REPO}
export BULK=${BULK_ROOT}
B=$BULK/joint_r3_mc_20260926
declare -A busy
while read c s; do busy[$c]=$s; done < $B/busy_initial.txt
pending=(79005 79007 79017 79018 79019 79020 79021 79022 79023 79024)
t21=$(TZ=Europe/Berlin date -d '21:00' +%s)
contended() { ps -eo psr,pcpu,args | awk -v c=$1 '$1==c && $2>20 && $0 !~ /joint_r3_mc/' | grep -q . ; }
while [ ${#pending[@]} -gt 0 ]; do
  running=0
  for c in "${!busy[@]}"; do if [ -f $B/logs/s${busy[$c]}.log.rc ]; then unset busy[$c]; else running=$((running+1)); fi; done
  cap=16; [ $(date +%s) -ge $t21 ] && cap=24
  for c in 100 101 102 103 105 107 108 109 110 111 112 113 114 115 80 81 82 83 84 85 86 87; do
    [ ${#pending[@]} -gt 0 ] && [ $running -lt $cap ] || break
    [ -n "${busy[$c]:-}" ] && continue
    contended $c && { echo "$(date -Is) cpu $c contended, skipped"; continue; }
    s=${pending[0]}; pending=("${pending[@]:1}")
    flow/launch_pinned.sh $c designs/g1-guardian/blocks/g1_trip/sim 40000 $B/logs/s$s.log \
      python3 qualification/joint_r3_mc_20260926/runner_r3mc.py --seed $s --bulk $B
    busy[$c]=$s; running=$((running+1)); echo "$(date -Is) seed $s on cpu $c nice=$(nice) running=$running"
  done
  sleep 60
done
echo "$(date -Is) all seeds launched"
