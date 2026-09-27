#!/usr/bin/env bash
# Red-team 2026-09-27 trip_path: one G1_GATE brown-out run. Usage (inside the container via flow/run.sh, workdir
# designs/g1-guardian/blocks/g1_gate/sim): bash <this> <BV|BA> <tripd 1|0> <mos> <temp> <outdir>
set -eu
SUF=""; if [ "${NODCN:-0}" = 1 ]; then SUF=_nodcn; fi
CASE=$1; TD=$2; MOS=$3; TEMP=$4; OUT=$5
D=$(dirname "$0")
if [ "$CASE" = BV ]; then PD="0 0 1u 1.2 5u 1.2 25u 0 30u 0 35u 1.2 40u 1.2"; PA="0 0 1u 0 2u 3.3 40u 3.3"
else PD="0 0 1u 1.2 40u 1.2"; PA="0 0 1u 0 2u 3.3 5u 3.3 25u 0 30u 0 35u 3.3 40u 3.3"; fi
name="bo_${CASE}_td${TD}_${MOS}_${TEMP}C${SUF}"
sed -e "s/@@CASE@@/$CASE/g" -e "s/@@TRIPD@@/$TD/g" -e "s/@@MOS@@/$MOS/g" -e "s/@@TEMP@@/$TEMP/g" \
    -e "s/@@PWLA@@/$PA/" -e "s/@@PWLD@@/$PD/" -e "s#@@OUT@@#$OUT/$name.dat#" "$D/tb_gate_brownout.cir.tmpl" > "$OUT/$name.cir"
if [ "${NODCN:-0}" = 1 ]; then sed -i -e "s#^.include /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/spice/sg13g2_io.spi#.include ${G1_RESULTS_ROOT}/redteam-20260927/trip_path/net/sg13g2_io_nodcn.spi#" -e "s/ sg13g2_IOPad/ g1nd_sg13g2_IOPad/" "$OUT/$name.cir"; fi
ngspice -b "$OUT/$name.cir" > "$OUT/$name.log" 2>&1 || true
grep -E "^BROWNOUT|Timestep too small|rror" "$OUT/$name.log" | head -5
