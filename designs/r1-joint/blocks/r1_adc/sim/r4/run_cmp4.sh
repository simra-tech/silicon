#!/bin/sh
# run_cmp4.sh <set> <suffix>: comparator memory/decision-time and noise decks of revision 4 at tt, ss/125 C/1.08 V,
# ff/-40 C/1.32 V, one CPU per corner (103, 104, 105). Revision-4 campaign helper.
S=$1; X=$2; D=""; [ "$S" != "a" ] && D="_$S"
cd "$(dirname "$0")/../.."
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the results root}"; export G1_RESULTS_ROOT
run() { C=$1; T=$2; V=$3; TAG=$4; CPU=$5
  python3 sim/run_ngspice.py --deck sim/r4/tb_cmp4_mem$D.cir --run-id r4-cmp-mem-$TAG-$S$X --cpuset $CPU --sub CORNER=$C \
    --sub TEMP=$T --sub VDD=$V --sub ASM=0.0002 --timeout 3600 \
    --question "R2-3 rev 4: comparator variants set $S, decision time and memory, one decision per tick, clkgen clock, $TAG"
  python3 sim/run_ngspice.py --deck sim/r4/tb_cmp4_noise$D.cir --run-id r4-cmp-noise-$TAG-$S$X --cpuset $CPU --sub CORNER=$C \
    --sub TEMP=$T --sub VDD=$V --sub VCM=0.1 --sub VX=0.3 --timeout 3600 \
    --question "R2-3 rev 4: comparator variants set $S, first-stage noise PSD at CM 0.1 V, $TAG"
}
run mos_tt 27 1.2 tt27 103 &
run mos_ss 125 1.08 ss125 104 &
run mos_ff -40 1.32 ffm40 105 &
wait
