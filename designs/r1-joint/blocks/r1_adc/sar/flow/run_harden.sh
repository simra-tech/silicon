#!/bin/sh
# LibreLane hardening run of r1_adc_sar (T2j). Inside the container:
#   G1_CPUSET=116-117 G1_CPUS=2 G1_WORKDIR=designs/r1-joint/blocks/r1_adc/sar G1_RESULTS_ROOT=<bulk> \
#     flow/run.sh sh flow/run_harden.sh <run-id> <die height um> <core y0> <core y1> [timeout_s [cfg-append.yaml|- [librelane args]]]
# (flow/run.sh does not pass the caller environment into the container, so options are arguments.)
# Layout: $G1_RESULTS_ROOT/r1_adc_sar/<run-id>/{rtl,flow,librelane.log,run.json}. Core: x 2.88 .. 436.32 um,
# y <core y0> .. <core y1> (OpenROAD snaps the core bottom to a multiple of the 3.78 um row height from the die
# origin). Pins regenerated for the die (flow/gen_pins.py).
set -u
RID="$1"; H="$2"; CY0="$3"; CY1="$4"; TMO="${5:-7200}"; APP="${6:--}"; [ $# -ge 6 ] && shift 6 || shift $#; EXTRA="$*"
B="$G1_RESULTS_ROOT/r1_adc_sar/$RID"
if [ -e "$B" ]; then echo "run id $RID exists" >&2; exit 1; fi
mkdir -p "$B/flow" "$B/rtl"
cp rtl/r1_adc_sar.v "$B/rtl/"
cp flow/config.yaml flow/r1_adc_sar.sdc flow/r1_adc_sar_pnr.sdc flow/gen_pins.py flow/slice_pin_targets.json "$B/flow/"
python3 "$B/flow/gen_pins.py" 439 "$H" "$B/flow" > "$B/pins.txt" 2>&1 || { echo "pin generation failed" >&2; exit 1; }
python3 - "$B/flow/config.yaml" "$H" "$CY0" "$CY1" <<'EOP'
import sys, re
p, h, y0, y1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
s = open(p).read()
s = re.sub(r"^DIE_AREA:.*$", "DIE_AREA: [0, 0, 439, %g]" % h, s, flags=re.M)
s = re.sub(r"^CORE_AREA:.*$", "CORE_AREA: [2.88, %g, 436.32, %g]" % (y0, y1), s, flags=re.M)
open(p, "w").write(s)
EOP
if [ "$APP" != "-" ]; then
  python3 -c "
import sys, yaml
c = yaml.safe_load(open(sys.argv[1])); c.update(yaml.safe_load(open(sys.argv[2])))
yaml.safe_dump(c, open(sys.argv[1], 'w'), sort_keys=False)" "$B/flow/config.yaml" "$APP"
  cp "$APP" "$B/cfg_append.txt"
fi
(cd "$B" && sha256sum rtl/*.v flow/config.yaml flow/pins.cfg flow/r1_adc_sar.sdc flow/r1_adc_sar_pnr.sdc) > "$B/inputs.sha256"
T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cd "$B/flow"
timeout "$TMO" librelane config.yaml --pdk ihp-sg13g2 --pdk-root /foss/pdks --manual-pdk \
    --run-tag "$RID" $EXTRA > "$B/librelane.log" 2>&1
RC=$?
LLV=$(grep -ho '"librelane_version": "[^"]*"' "$B"/flow/runs/*/resolved.json 2>/dev/null | head -1 | sed 's/.*: //')
[ -z "$LLV" ] && LLV='"unknown"'
cat > "$B/run.json" <<EOJ
{"run_id": "$RID", "block": "r1_adc_sar", "track": "T2j", "start_utc": "$T0", "end_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
 "command": "flow/run.sh sh flow/run_harden.sh $RID $H $CY0 $CY1 $TMO $APP $EXTRA",
 "die_um": [439, $H], "core_y_um": [$CY0, $CY1],
 "tools": {"librelane": $LLV, "container": "tapeoutbench-eda:latest sha256:ddeb69576f28"},
 "pdk_commit": "$(cat /foss/pdks/ihp-sg13g2/COMMIT)",
 "rtl_sha256": "$(sha256sum "$B/rtl/r1_adc_sar.v" | cut -d' ' -f1)", "inputs": "inputs.sha256",
 "question": "Does r1_adc_sar harden in 439 x $H um at 42 MHz on sg13g2 with sign-off STA, DRC, LVS and antenna clean?",
 "exit_code": $RC, "timeout_s": $TMO}
EOJ
exit $RC
