#!/bin/sh
# T2j: sign-off STA and window analysis of a finished r1_adc_sar hardening run, all three corners.
#   G1_CPUSET=116 G1_WORKDIR=designs/r1-joint/blocks/r1_adc/sar G1_RESULTS_ROOT=<bulk> flow/run.sh sh flow/sta/run_sta.sh <hardening run-id> <out run-id>
# Writes <bulk>/r1_adc_sar/<out run-id>/{signoff_<corner>.log, windows_<corner>.log, inputs.sha256} and copies the
# summaries to flow/sta/results/<out run-id>/ (windows.json, windows.md, signoff.json).
set -u
HR="$1"; OR="$2"
F="$G1_RESULTS_ROOT/r1_adc_sar/$HR/flow/runs/$HR/final"
B="$G1_RESULTS_ROOT/r1_adc_sar/$OR"
if [ -e "$B" ]; then echo "run id $OR exists" >&2; exit 1; fi
mkdir -p "$B" "flow/sta/results/$OR"
cp flow/r1_adc_sar.sdc "$B/"
L=/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib
(sha256sum "$F/nl/r1_adc_sar.nl.v" "$F/spef/nom/r1_adc_sar.nom.spef" "$B/r1_adc_sar.sdc" flow/sta/sta_windows.sdc) > "$B/inputs.sha256"
for c in fast:fast_1p32V_m40C:0.95 typ:typ_1p20V_25C:1.42 slow:slow_1p08V_125C:2.31; do
  t=${c%%:*}; r=${c#*:}; lib=$L/sg13g2_stdcell_${r%%:*}.lib; mr=${c##*:}
  env SAR_NL="$F/nl/r1_adc_sar.nl.v" SAR_SPEF="$F/spef/nom/r1_adc_sar.nom.spef" SAR_LIB="$lib" SAR_TAG=$t \
      SAR_SDC="$B/r1_adc_sar.sdc" SAR_MCLK_RISE=$mr sta -no_splash -exit flow/sta/signoff_sta.tcl > "$B/signoff_$t.log" 2>&1
  env SAR_NL="$F/nl/r1_adc_sar.nl.v" SAR_SPEF="$F/spef/nom/r1_adc_sar.nom.spef" SAR_LIB="$lib" SAR_TAG=$t \
      sta -no_splash -exit flow/sta/sta_windows.tcl > "$B/windows_$t.log" 2>&1
done
python3 flow/sta/sta_windows.py "flow/sta/results/$OR/windows.json" "flow/sta/results/$OR/windows.md" \
    fast="$B/windows_fast.log" typ="$B/windows_typ.log" slow="$B/windows_slow.log" \
    fast_so="$B/signoff_fast.log" typ_so="$B/signoff_typ.log" slow_so="$B/signoff_slow.log"
python3 - "$B" "flow/sta/results/$OR/signoff.json" "$HR" <<'EOP'
import json, re, sys
b, out, hr = sys.argv[1:4]
r = {"hardening_run": hr, "sdc": "flow/r1_adc_sar.sdc (copy in the run dir)", "rc": "final/spef/nom", "corners": {}}
for c in ("fast", "typ", "slow"):
    d = {"groups": {}}
    for l in open("%s/signoff_%s.log" % (b, c)):
        m = re.match(r"(worst slack|tns) (max|min) (-?[\d.]+)", l)
        if m: d["%s_%s" % ("ws" if m.group(1) == "worst slack" else "tns", "setup" if m.group(2) == "max" else "hold")] = float(m.group(3))
        m = re.match(r"GROUP (\S+) (max|min) (\S+) (\S+)", l)
        if m: d["groups"]["%s_%s" % (m.group(1), m.group(2))] = {"slack_ns": float(m.group(3)), "endpoint": m.group(4)}
    d["drv_violators"] = sum(1 for l in open("%s/signoff_%s.log" % (b, c)) if "(VIOLATED)" in l and "slack" not in l)
    r["corners"][c] = d
json.dump(r, open(out, "w"), indent=1)
print(json.dumps(r, indent=1))
EOP
