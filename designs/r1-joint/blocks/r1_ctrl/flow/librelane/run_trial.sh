#!/bin/sh
# First LibreLane hardening trial of r1_ctrl (revision 0.2). Inside the container:
#   G1_CPUSET=112-115 G1_CPUS=4 G1_WORKDIR=designs/r1-joint/blocks/r1_ctrl \
#   G1_RESULTS_ROOT=/opt/sim/<user>/r1-traces/sims flow/run.sh sh flow/librelane/run_trial.sh <run-id>
# Layout of the bulk run: $G1_RESULTS_ROOT/r1_ctrl/<run-id>/{flow,rtl -> repository rtl}
# Wall-clock limit 2 h (brief); a run that hits it is recorded as "not run (time limit)".
set -u
RID="$1"
B="$G1_RESULTS_ROOT/r1_ctrl/$RID"
if [ -e "$B" ]; then echo "run id $RID exists" >&2; exit 1; fi
mkdir -p "$B/flow"
ln -s "$(pwd)/rtl" "$B/rtl"
cp flow/librelane/config.yaml flow/r1_ctrl.sdc "$B/flow/"
sha256sum rtl/*.v flow/librelane/config.yaml flow/r1_ctrl.sdc > "$B/inputs.sha256"
{ echo "date_utc $(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "librelane $(librelane --version 2>&1 | tail -1)";
  echo "pdk_commit $(cat /foss/pdks/ihp-sg13g2/COMMIT)"; } > "$B/versions.txt"
cd "$B/flow"
timeout 7200 librelane config.yaml --pdk ihp-sg13g2 --pdk-root /foss/pdks --manual-pdk \
    --run-tag "$RID" > "$B/librelane.log" 2>&1
echo "exit $?" >> "$B/versions.txt"
# the version banner of "librelane --version" is not one line; take it from the run
grep -ho '"librelane_version": "[^"]*"' "$B"/flow/runs/*/resolved.json | head -1 >> "$B/versions.txt"
