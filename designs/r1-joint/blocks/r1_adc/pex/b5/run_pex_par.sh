#!/bin/sh
# layout B5 (T2k): same as pex/b4/run_pex_par.sh; pex_prepare.py and pex_build.py detect B5 from layout/r1_adc_layout.json (slice north pins, SAR macro removed from the top-only extraction, macro-pin and macro-supply ports).
# layout B4: pex/run_pex.sh with the two kpex runs in parallel (slice on the first CPU of G1_CPUSET_A, top on G1_CPUSET_B),
# then pex/pex_build.py (method B.1). usage (host, any cwd):
#   G1_RESULTS_ROOT=<bulk>; export G1_RESULTS_ROOT; sh designs/r1-joint/blocks/r1_adc/pex/b5/run_pex_par.sh <abs run dir> <abs gds> <cpu a> <cpu b>
set -u
D=$1; GDS=$2; CA=$3; CB=$4
cd "$(dirname "$0")/../../../../../.."
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"; export G1_RESULTS_ROOT
G1_WORKDIR=designs/r1-joint/blocks/r1_adc; export G1_WORKDIR
mkdir -p "$D"; FAIL=0
G1_CPUSET=$CA; export G1_CPUSET
flow/run.sh klayout -b -r pex/pex_prepare.py -rd gds=$GDS -rd out=$D/r1_adc_slice_flat.gds -rd cell=slice > $D/prep_slice.log 2>&1 || FAIL=1
flow/run.sh klayout -b -r pex/pex_prepare.py -rd gds=$GDS -rd out=$D/r1_adc_top_flat.gds -rd cell=top_only > $D/prep_top.log 2>&1 || FAIL=1
[ $FAIL = 0 ] || { echo "prepare failed" > $D/pex.done; exit 1; }
( G1_CPUSET=$CB; export G1_CPUSET; flow/run.sh kpex --pdk ihp-sg13g2 --threads 1 --gds $D/r1_adc_top_flat.gds --schematic layout/r1_adc_lvs.cdl --cell r1_adc --2.5D --mode CC --out_dir $D/kpex_top > $D/kpex_top_console.log 2>&1 || echo "kpex top rc $?" >> $D/kpex_top_console.log ) &
flow/run.sh kpex --pdk ihp-sg13g2 --threads 1 --gds $D/r1_adc_slice_flat.gds --schematic layout/r1_adc_lvs.cdl --cell r1_adc_slice --2.5D --mode CC --out_dir $D/kpex_slice > $D/kpex_slice_console.log 2>&1 || echo "kpex slice rc $?" >> $D/kpex_slice_console.log
wait
for f in $D/kpex_top/r1_adc_top_flat__r1_adc/r1_adc_k25d_pex_netlist.spice $D/kpex_slice/r1_adc_slice_flat__r1_adc_slice/r1_adc_slice_k25d_pex_netlist.spice; do
  [ -s "$f" ] || { echo "missing $f" >> $D/run_pex.log; FAIL=1; }
done
[ $FAIL = 0 ] && flow/run.sh klayout -b -r pex/pex_build.py -rd kdir=$D -rd out=$D/build > $D/build.console 2>&1 || FAIL=1
echo "done fail=$FAIL" > $D/pex.done
exit $FAIL
