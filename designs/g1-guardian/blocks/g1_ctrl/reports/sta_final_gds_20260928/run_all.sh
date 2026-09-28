#!/usr/bin/env bash
# All final-GDS STA runs of 2026-09-28 (repository root; BULK = results root; CPUs 97-100, one run per CPU).
set -uo pipefail
B=${BULK:?}/final
H=designs/g1-guardian/blocks/g1_ctrl/reports/sta_final_gds_20260928
export MACRO_NL=$BULK/eco_views/g1_digital.nl.v MACRO_SPEF=$BULK/eco_views/g1_digital.nom.spef INPUTS=$BULK/inputs PIN_SLEWS=1
# from osc_clk_stage.json (ngspice, *_route): 20-80 % transition at clkbuf_0_osc_clk/A (tr,tf) and latch output q -> that pin (dq_r,dq_f)
declare -A OT=([fast]=0.620,0.659 [typ]=0.940,0.948 [slow]=1.426,1.560)
declare -A OL=([fast]=0.485,0.528 [typ]=0.723,0.767 [slow]=1.086,1.235)
jobs_=()
for corner in fast typ slow; do
  jobs_+=("macro $corner macro - - - - ")
  jobs_+=("chip $corner chip_p2p $BULK/rc_r4/top_p2p.spef - - -")
  jobs_+=("chip $corner chip_ub $BULK/rc_r4/top_ub.spef - - -")
  jobs_+=("chip $corner chip_p2p_oscedge $BULK/rc_r4/top_p2p.spef - ${OT[$corner]} ${OL[$corner]}")
  jobs_+=("chip $corner chip_p2p_sclkport $BULK/rc_r4/top_p2p.spef SCLK - -")
  jobs_+=("chip $corner chip_p2p_board15pF $BULK/rc_r4/top_p2p.spef - - - 15")
done
cpus=(97 98 99 100); i=0; pids=()
for j in "${jobs_[@]}"; do
  read -r case_ corner tag spef clk ot ol bl <<<"$j"
  cpu=${cpus[$((i % 4))]}
  ( [ "$spef" != - ] && export TOP_SPEF=$spef; [ "$clk" != - ] && export CLOCK_NET=$clk
    [ "$ot" != - ] && export OSC_TRANS=$ot; [ "$ol" != - ] && export OSC_LAT=$ol; [ -n "${bl:-}" ] && export BOARD_LOAD_PF=$bl
    $H/run_sta_final.sh $case_ $corner $cpu $BULK $B/$tag-$corner; echo "$tag $corner rc=$?" >> $B/done.txt ) &
  pids[$cpu]=$!; i=$((i+1))
  if (( i % 4 == 0 )); then wait; fi
done
wait
echo ALL_DONE >> $B/done.txt
