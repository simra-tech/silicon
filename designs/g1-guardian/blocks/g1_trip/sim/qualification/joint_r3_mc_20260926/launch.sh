#!/usr/bin/env bash
# joint_r3_mc_20260926 launcher: 16 seeds now on CPUs 100-115, 8 seeds at 21:00 Europe/Berlin on CPUs 80-87.
# One seed per CPU, nice 0, detached via flow/launch_pinned.sh (wall bound 40000 s per seed).
set -eu
cd ${REPO}
export BULK=${BULK_ROOT}
B=$BULK/joint_r3_mc_20260926
go() { # cpu seed
  flow/launch_pinned.sh $1 designs/g1-guardian/blocks/g1_trip/sim 40000 $B/logs/s$2.log \
    python3 qualification/joint_r3_mc_20260926/runner_r3mc.py --seed $2 --bulk $B
}
mkdir -p $B/logs
i=0; for cpu in $(seq 100 115); do go $cpu $((79001+i)); i=$((i+1)); done
echo "batch1 launched $(date -Is) nice=$(nice)"
target=$(TZ=Europe/Berlin date -d '21:00' +%s); now=$(date +%s)
[ $target -gt $now ] && sleep $((target-now))
i=0; for cpu in $(seq 80 87); do go $cpu $((79017+i)); i=$((i+1)); done
echo "batch2 launched $(date -Is) nice=$(nice)"
