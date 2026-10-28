#!/bin/sh
# kpex 2.5D CC of the slice cell and of the top cell without the slice instances (r1_adc layout A).
# usage (host, repo root or anywhere): G1_RESULTS_ROOT=<bulk>; export G1_RESULTS_ROOT; sh designs/r1-joint/blocks/r1_adc/pex/run_pex.sh <abs run dir> <abs gds>
# Exits non-zero if a step fails; it does not resubmit.
set -eu
D=$1; GDS=$2
# T2p (layout B10): optional 3rd argument, the layout JSON of a development layout (default: the tracked record)
LJ=${3:-}; LJA=""; [ -n "$LJ" ] && LJA="-rd lj=$LJ"
cd "$(dirname "$0")/../../../../.."
G1_CPUSET=${G1_CPUSET:-103}; export G1_CPUSET; : "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"; export G1_RESULTS_ROOT
G1_WORKDIR=designs/r1-joint/blocks/r1_adc; export G1_WORKDIR; FAIL=0
mkdir -p "$D"
flow/run.sh klayout -b -r pex/pex_prepare.py -rd gds=$GDS -rd out=$D/r1_adc_slice_flat.gds -rd cell=slice $LJA > $D/prep_slice.log 2>&1 || FAIL=1
flow/run.sh klayout -b -r pex/pex_prepare.py -rd gds=$GDS -rd out=$D/r1_adc_top_flat.gds -rd cell=top_only $LJA > $D/prep_top.log 2>&1 || FAIL=1
[ $FAIL = 0 ] || { echo "prepare failed" > $D/pex.done; exit 1; }
flow/run.sh kpex --pdk ihp-sg13g2 --threads 1 --gds $D/r1_adc_top_flat.gds --schematic layout/r1_adc_lvs.cdl --cell r1_adc --2.5D --mode CC --out_dir $D/kpex_top > $D/kpex_top_console.log 2>&1 || { echo "kpex top rc $?" >> $D/kpex_top_console.log; FAIL=1; }
flow/run.sh kpex --pdk ihp-sg13g2 --threads 1 --gds $D/r1_adc_slice_flat.gds --schematic layout/r1_adc_lvs.cdl --cell r1_adc_slice --2.5D --mode CC --out_dir $D/kpex_slice > $D/kpex_slice_console.log 2>&1 || { echo "kpex slice rc $?" >> $D/kpex_slice_console.log; FAIL=1; }
for f in $D/kpex_top/r1_adc_top_flat__r1_adc/r1_adc_k25d_pex_netlist.spice $D/kpex_slice/r1_adc_slice_flat__r1_adc_slice/r1_adc_slice_k25d_pex_netlist.spice; do
  [ -s "$f" ] || { echo "missing $f" >> $D/run_pex.log; FAIL=1; }
done
echo "done fail=$FAIL" > $D/pex.done
exit $FAIL
