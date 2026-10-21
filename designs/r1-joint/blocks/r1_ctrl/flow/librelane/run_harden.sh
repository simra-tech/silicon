#!/bin/sh
# LibreLane hardening run of r1_ctrl (revision 0.3). Inside the container:
#   G1_CPUSET=112-115 G1_CPUS=4 G1_WORKDIR=designs/r1-joint/blocks/r1_ctrl \
#   G1_RESULTS_ROOT=/opt/sim/<user>/r1-traces/sims flow/run.sh sh flow/librelane/run_harden.sh <run-id> [timeout_s]
# Differs from run_trial.sh (revision 0.2): the RTL is copied, not linked, so later
# edits in the tree do not change a running or finished run; run.json is written.
# Layout: $G1_RESULTS_ROOT/r1_ctrl/<run-id>/{rtl,flow,librelane.log,run.json}
set -u
RID="$1"; TMO="${2:-14400}"
B="$G1_RESULTS_ROOT/r1_ctrl/$RID"
if [ -e "$B" ]; then echo "run id $RID exists" >&2; exit 1; fi
mkdir -p "$B/flow" "$B/rtl"
cp rtl/*.v "$B/rtl/"
cp flow/librelane/config.yaml flow/librelane/pins.cfg flow/r1_ctrl.sdc "$B/flow/"
# optional comparison variant: R1_LIB_VARIANT=<file> replaces rtl/r1_lib.v in the run
# copy and adds the define R1_CFG_FLOPS (flip-flop register file; area/timing study)
if [ -n "${R1_LIB_VARIANT:-}" ]; then
  cp "$R1_LIB_VARIANT" "$B/rtl/r1_lib.v"
  sed -i 's/^  - SYNTHESIS$/  - SYNTHESIS\n  - R1_CFG_FLOPS/' "$B/flow/config.yaml"
  echo "variant $R1_LIB_VARIANT (R1_CFG_FLOPS)" > "$B/variant.txt"
fi
# optional (revision 0.4 studies): R1_CFG_APPEND=<file> adds lines to the run copy of config.yaml,
# R1_LL_EXTRA='--to OpenROAD.CTS' stops the flow early (area-only study, not a hardening result)
if [ -n "${R1_CFG_APPEND:-}" ]; then   # keys in the file replace the same keys of config.yaml
  python3 -c "
import sys, yaml
c = yaml.safe_load(open(sys.argv[1])); c.update(yaml.safe_load(open(sys.argv[2])))
yaml.safe_dump(c, open(sys.argv[1], 'w'), sort_keys=False)" "$B/flow/config.yaml" "$R1_CFG_APPEND"
  cp "$R1_CFG_APPEND" "$B/cfg_append.txt"
fi
(cd "$B" && sha256sum rtl/*.v flow/config.yaml flow/pins.cfg flow/r1_ctrl.sdc) > "$B/inputs.sha256"
T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cd "$B/flow"
timeout "$TMO" librelane config.yaml --pdk ihp-sg13g2 --pdk-root /foss/pdks --manual-pdk \
    --run-tag "$RID" ${R1_LL_EXTRA:-} > "$B/librelane.log" 2>&1
RC=$?
LLV=$(grep -ho '"librelane_version": "[^"]*"' "$B"/flow/runs/*/resolved.json | head -1 | sed 's/.*: //')
RTLSHA=$(cat "$B"/rtl/*.v | sha256sum | cut -d' ' -f1)
cat > "$B/run.json" <<EOJ
{"run_id": "$RID", "block": "r1_ctrl", "start_utc": "$T0", "end_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
 "command": "flow/run.sh sh flow/librelane/run_harden.sh $RID $TMO",
 "tools": {"librelane": $LLV, "container": "tapeoutbench-eda:latest sha256:ddeb69576f28"},
 "pdk_commit": "$(cat /foss/pdks/ihp-sg13g2/COMMIT)",
 "rtl_concat_sha256": "$RTLSHA", "inputs": "inputs.sha256",
 "question": "Does r1_ctrl harden at 42 MHz on sg13g2 with sign-off STA, DRC and LVS clean?",
 "exit_code": $RC, "timeout_s": $TMO}
EOJ
