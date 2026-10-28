#!/bin/sh
# B10 PEX of record on CPU 104 (repo root): kpex 2.5D CC (pex/run_pex.sh) + pex_build.py RC netlist, copies into pex/,
# merge into sim/post/r1_adc_post_rc_mb10<tag>.spice. Usage: sh chain_pex104.sh <dev tag>
cd "$(dirname "$0")/../../../../../../../.."
: "${G1_RESULTS_ROOT:?}"; export G1_RESULTS_ROOT
T=$1; X=$G1_RESULTS_ROOT/r1_adc/pex-b10-${T}${PEXSUF:-}; G=$G1_RESULTS_ROOT/r1_adc/layout-b10-$T/r1_adc.gds
G1_CPUSET=104; export G1_CPUSET
date > /dev/null
sh designs/r1-joint/blocks/r1_adc/pex/run_pex.sh $X $G $G1_RESULTS_ROOT/r1_adc/layout-b10-$T/r1_adc_layout.json || { echo "run_pex failed"; exit 1; }
G1_WORKDIR=designs/r1-joint/blocks/r1_adc; export G1_WORKDIR
flow/run.sh klayout -b -r pex/pex_build.py -rd kdir=$X -rd out=$X/build -rd lj=$G1_RESULTS_ROOT/r1_adc/layout-b10-$T/r1_adc_layout.json > $X/build.console 2>&1 || { echo "pex_build failed"; exit 1; }
B=designs/r1-joint/blocks/r1_adc
cp $X/build/r1_adc_post_rc.spice $B/pex/r1_adc_post_rc_b10${MBSUF:-}.spice
cp $X/build/r1_adc_post_c.spice $B/pex/r1_adc_post_c_b10${MBSUF:-}.spice
cp $X/build/pex_report.json $B/pex/pex_report_b10${MBSUF:-}.json
sed "s#$G1_RESULTS_ROOT#<G1_RESULTS_ROOT>#g" $X/build/pex_build.log > $B/pex/pex_build_b10${MBSUF:-}.log
flow/run.sh python3 sim/post/merge_parallel.py pex/r1_adc_post_rc_b10${MBSUF:-}.spice sim/post/r1_adc_post_rc_mb10${MBSUF:-}.spice || { echo "merge failed"; exit 1; }
echo "pex chain done"
