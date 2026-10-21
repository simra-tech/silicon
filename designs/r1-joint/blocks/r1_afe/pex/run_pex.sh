#!/bin/sh
# kpex 2.5D CC of the channel cell and of the top cell without the channel instances (layout revision E2).
# usage (host): G1_RESULTS_ROOT=<bulk>; export G1_RESULTS_ROOT; sh designs/r1-joint/blocks/r1_afe/pex/run_pex.sh <abs run dir> <abs gds>
set -eu
D=$1; GDS=$2
cd "$(dirname "$0")/../../../../.."
G1_CPUSET=106-108; export G1_CPUSET; : "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"; export G1_RESULTS_ROOT
G1_WORKDIR=designs/r1-joint/blocks/r1_afe; export G1_WORKDIR; FAIL=0
flow/run.sh klayout -b -r pex/pex_prepare.py -rd gds=$GDS -rd out=$D/r1_afe_ch_flat.gds -rd cell=r1_afe_ch > $D/prep_ch.log 2>&1
flow/run.sh klayout -b -r pex/pex_prepare.py -rd gds=$GDS -rd out=$D/r1_afe_top_flat.gds -rd cell=top_only > $D/prep_top.log 2>&1
flow/run.sh kpex --pdk ihp-sg13g2 --threads 1 --gds $D/r1_afe_top_flat.gds --schematic layout/r1_afe_lvs.cdl --cell r1_afe --2.5D --mode CC --out_dir $D/kpex_top > $D/kpex_top_console.log 2>&1 || { echo "kpex top rc $?" >> $D/kpex_top_console.log; FAIL=1; }
flow/run.sh kpex --pdk ihp-sg13g2 --threads 2 --gds $D/r1_afe_ch_flat.gds --schematic layout/r1_afe_lvs.cdl --cell r1_afe_ch --2.5D --mode CC --out_dir $D/kpex_ch > $D/kpex_ch_console.log 2>&1 || { echo "kpex ch rc $?" >> $D/kpex_ch_console.log; FAIL=1; }
for f in $D/kpex_top/r1_afe_top_flat__r1_afe/r1_afe_k25d_pex_netlist.spice $D/kpex_ch/r1_afe_ch_flat__r1_afe_ch/r1_afe_ch_k25d_pex_netlist.spice; do
  [ -s "$f" ] || { echo "missing $f" >> $D/run_pex.log; FAIL=1; }
done
echo "done fail=$FAIL" > $D/pex.done
exit $FAIL
