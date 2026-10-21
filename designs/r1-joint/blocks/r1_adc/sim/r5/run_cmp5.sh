#!/bin/sh
# run_cmp5.sh <suffix> [set]: (set b: tb_cmp5n_*.cir, other sets tb_cmp5n_*_<set>.cir) decision-0 comparator r1_cmp5n decks of revision 5 at tt, ss/125 C/1.08 V, ff/-40 C/1.32 V,
# one CPU per corner (103, 104, 105). Stops a corner on the first failed job (run_ngspice5.py exits 1); the script
# exits 1 if any corner failed.
X=$1; S=${2:-b}; D=""; [ "$S" != "b" ] && D="_$S"
cd "$(dirname "$0")/../.."
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the results root}"; export G1_RESULTS_ROOT
NV=n8; [ "$S" = "c" ] && NV=n16r
run() { C=$1; T=$2; V=$3; TAG=$4; CPU=$5
  python3 sim/r5/run_ngspice5.py --deck sim/r5/tb_cmp5n_mem$D.cir --run-id r5-cmpn-mem-$TAG$X --cpuset $CPU --sub CORNER=$C \
    --sub TEMP=$T --sub VDD=$V --sub ASM=0.0002 --timeout 3600 --expect mem.raw \
    --question "R5 item 2: NMOS-input decision-0 comparator variants, decision time and memory at CM 0.7/0.6/0.5 V, $TAG" \
    --disposition "comparator sizing run (post_cmp5.py)" || return 1
  python3 sim/r5/run_ngspice5.py --deck sim/r5/tb_cmp5n_noise$D.cir --run-id r5-cmpn-noise-$TAG$X --cpuset $CPU --sub CORNER=$C \
    --sub TEMP=$T --sub VDD=$V --sub VCM=0.6 --sub VX=0.8 --timeout 3600 --expect noise_$NV.txt \
    --question "R5 item 2: NMOS-input comparator first-stage noise PSD at CM 0.6 V, $TAG" \
    --disposition "comparator noise run (post_cmp5.py)" || return 1
}
rc=0
run mos_tt 27 1.2 tt27 103 & p1=$!
run mos_ss 125 1.08 ss125 104 & p2=$!
run mos_ff -40 1.32 ffm40 105 & p3=$!
wait $p1 || rc=1; wait $p2 || rc=1; wait $p3 || rc=1
exit $rc
