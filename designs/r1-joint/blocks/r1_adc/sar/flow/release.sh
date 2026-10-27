#!/bin/sh
# T2j: copy the deliverables of a finished r1_adc_sar hardening run to <G1_RESULTS_ROOT>/r1_adc_sar/release-<tag>/
# with SHA256SUMS.   G1_WORKDIR=designs/r1-joint/blocks/r1_adc/sar flow/run.sh sh flow/release.sh <run-id> <tag>
set -eu
HR="$1"; TAG="$2"
F="$G1_RESULTS_ROOT/r1_adc_sar/$HR/flow/runs/$HR/final"
O="$G1_RESULTS_ROOT/r1_adc_sar/release-$TAG"
if [ -e "$O" ]; then echo "release $TAG exists" >&2; exit 1; fi
mkdir -p "$O/sdf"
cp "$F/gds/r1_adc_sar.gds" "$F/lef/r1_adc_sar.lef" "$F/nl/r1_adc_sar.nl.v" "$F/pnl/r1_adc_sar.pnl.v" \
   "$F/spef/nom/r1_adc_sar.nom.spef" "$O/"
cp "$F"/spice/*.spice "$O/r1_adc_sar.lvs.spice" 2>/dev/null || true
for c in nom_fast_1p32V_m40C nom_typ_1p20V_25C nom_slow_1p08V_125C; do cp "$F/sdf/$c/r1_adc_sar__$c.sdf" "$O/sdf/"; done
cp "$F/metrics.json" "$O/"
python3 tools/v2spice.py "$F/pnl/r1_adc_sar.pnl.v" /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/spice/sg13g2_stdcell.spice \
    "$O/r1_adc_sar_gl_sim.spice" > "$O/v2spice.log"
cp rtl/r1_adc_sar.v flow/r1_adc_sar.sdc flow/pins.md "$O/"
(cd "$O" && find . -type f ! -name SHA256SUMS | sort | xargs sha256sum > SHA256SUMS)
cat "$O/SHA256SUMS"
