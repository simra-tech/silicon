#!/usr/bin/env bash
# Re-run of the final-GDS chip STA of 2026-09-28 with the corrected SDC (float derate 0.05).
# Repository root; BULK = this re-run's results root, pre-populated with copies of inputs/, rc_r4/, eco_views/
# from the 2026-09-28 timing root. Reuses the scripts of sta_final_gds_20260928 unchanged. CPUs 90 and 91, one run each.
set -uo pipefail
B=${BULK:?}/final; mkdir -p $B
H=designs/g1-guardian/blocks/g1_ctrl/reports/sta_final_gds_20260928
export MACRO_NL=$BULK/eco_views/g1_digital.nl.v MACRO_SPEF=$BULK/eco_views/g1_digital.nom.spef INPUTS=$BULK/inputs PIN_SLEWS=1
declare -A OT=([fast]=0.620,0.659 [typ]=0.940,0.948 [slow]=1.426,1.560)
declare -A OL=([fast]=0.485,0.528 [typ]=0.723,0.767 [slow]=1.086,1.235)
jobs_=()
for corner in fast typ slow; do
  jobs_+=("chip $corner chip_p2p $BULK/rc_r4/top_p2p.spef - - - ")
  jobs_+=("chip $corner chip_ub $BULK/rc_r4/top_ub.spef - - - ")
  jobs_+=("chip $corner chip_p2p_oscedge $BULK/rc_r4/top_p2p.spef - ${OT[$corner]} ${OL[$corner]} ")
  jobs_+=("chip $corner chip_p2p_sclkport $BULK/rc_r4/top_p2p.spef SCLK - - ")
  jobs_+=("chip $corner chip_p2p_board10pF $BULK/rc_r4/top_p2p.spef - - - 10")
  jobs_+=("chip $corner chip_p2p_board15pF $BULK/rc_r4/top_p2p.spef - - - 15")
done
cpus=(90 91); i=0
for j in "${jobs_[@]}"; do
  read -r case_ corner tag spef clk ot ol bl <<<"$j"
  cpu=${cpus[$((i % 2))]}
  ( export TOP_SPEF=$spef; [ "$clk" != - ] && export CLOCK_NET=$clk
    [ "$ot" != - ] && export OSC_TRANS=$ot; [ "$ol" != - ] && export OSC_LAT=$ol; [ -n "${bl:-}" ] && export BOARD_LOAD_PF=$bl
    $H/run_sta_final.sh $case_ $corner $cpu $BULK $B/$tag-$corner; echo "$tag $corner rc=$?" >> $B/done.txt ) &
  i=$((i+1)); if (( i % 2 == 0 )); then wait; fi
done
wait
echo ALL_DONE >> $B/done.txt
