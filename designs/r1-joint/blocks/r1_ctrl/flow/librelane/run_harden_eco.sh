#!/bin/sh
# LibreLane hardening of r1_ctrl continued after a one-pin post-CTS repair (revision 0.9, track T5i). Inside the container:
#   G1_CPUSET=112-115 G1_CPUS=4 G1_WORKDIR=designs/r1-joint/blocks/r1_ctrl G1_RESULTS_ROOT=<G1_RESULTS_ROOT> \
#   flow/run.sh sh flow/librelane/run_harden_eco.sh <src-run> <new-run> <instance> <clock net> [cfg-append]
# <src-run>: a run_harden.sh run whose step 35-openroad-cts lost a clock-gate pin (Checker.DisconnectedPins).
# The script (1) copies the source run inputs and RTL, (2) applies flow/librelane/eco_cts_pin.tcl to the step-35
# odb (input A of <instance> to <clock net>), (3) runs LibreLane from OpenROAD.ResizerTimingPostCTS to the end with
# the repaired state. The repair uses the OpenROAD build of LibreLane (/foss/tools/openroad-librelane, odb schema
# 0.126); the openroad on the container PATH is newer (schema 0.136) and its odb cannot be read by the flow.
# Steps 1-35 (synthesis to CTS) are those of <src-run>, unchanged; every later step, all
# checkers and the sign-off reports run on the repaired design.
set -u
SRC="$1"; RID="$2"; INST="$3"; NET="$4"; APP="${5:-}"
S="$G1_RESULTS_ROOT/r1_ctrl/$SRC"; B="$G1_RESULTS_ROOT/r1_ctrl/$RID"
SR="$S/flow/runs/$SRC"
if [ -e "$B" ]; then echo "run id $RID exists" >&2; exit 1; fi
mkdir -p "$B/flow" "$B/rtl" "$B/eco"
cp "$S"/rtl/*.v "$B/rtl/"
cp "$S"/flow/*.yaml "$S"/flow/*.cfg "$S"/flow/*.sdc "$B/flow/"
if [ -n "$APP" ]; then
  python3 -c "
import sys, yaml
c = yaml.safe_load(open(sys.argv[1])); c.update(yaml.safe_load(open(sys.argv[2])))
yaml.safe_dump(c, open(sys.argv[1], 'w'), sort_keys=False)" "$B/flow/config.yaml" "$APP"
  cp "$APP" "$B/cfg_append.txt"
fi
ECO_IN="$SR/35-openroad-cts/r1_ctrl_top.odb" ECO_OUT_DIR="$B/eco" ECO_INST="$INST" ECO_PIN=A ECO_NET="$NET" \
  ECO_TOP=r1_ctrl_top /foss/tools/openroad-librelane/bin/openroad -exit -no_splash flow/librelane/eco_cts_pin.tcl > "$B/eco/eco.log" 2>&1 || { cat "$B/eco/eco.log"; exit 1; }
python3 - "$SR/35-openroad-cts/state_out.json" "$B/eco" "$B/eco/state_in.json" <<'EOP'
import json, sys
st = json.load(open(sys.argv[1]))
for k, ext in (("odb", "odb"), ("def", "def"), ("nl", "nl.v"), ("pnl", "pnl.v")):
    st[k] = "%s/r1_ctrl_top.%s" % (sys.argv[2], ext)
json.dump(st, open(sys.argv[3], "w"), indent=2)
EOP
(cd "$B" && sha256sum rtl/*.v flow/config.yaml flow/*.sdc eco/r1_ctrl_top.odb) > "$B/inputs.sha256"
T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cd "$B/flow"
timeout 14400 librelane config.yaml --pdk ihp-sg13g2 --pdk-root /foss/pdks --manual-pdk --run-tag "$RID" \
    --from OpenROAD.ResizerTimingPostCTS --with-initial-state "$B/eco/state_in.json" > "$B/librelane.log" 2>&1
RC=$?
LLV=$(grep -ho '"librelane_version": "[^"]*"' "$B"/flow/runs/*/resolved.json | head -1 | sed 's/.*: //')
RTLSHA=$(cat "$B"/rtl/*.v | sha256sum | cut -d' ' -f1)
cat > "$B/run.json" <<EOJ
{"run_id": "$RID", "block": "r1_ctrl", "start_utc": "$T0", "end_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
 "command": "flow/run.sh sh flow/librelane/run_harden_eco.sh $SRC $RID $INST $NET $APP",
 "source_run_steps_1_35": "$SRC", "eco": "$INST/A -> $NET (eco/eco.log)",
 "tools": {"librelane": $LLV, "container": "tapeoutbench-eda:latest sha256:ddeb69576f28"},
 "pdk_commit": "$(cat /foss/pdks/ihp-sg13g2/COMMIT)",
 "rtl_concat_sha256": "$RTLSHA", "inputs": "inputs.sha256",
 "question": "Does r1_ctrl 0.9 harden at 42 MHz on sg13g2 with sign-off STA, DRC and LVS clean?",
 "exit_code": $RC, "timeout_s": 14400}
EOJ
