#!/bin/sh
# Layout E9 (track T3m): one layout iteration from a screened development build: copy the build (same generator, same
# flags, deterministic output) to the iteration run id, checks (DRC main + maximal, antenna, LVS, supply islands, pins),
# kpex 2.5D CC (one kpex at a time), RC and wiring-R netlists, pair loads, x1 pair R, top supply z.
# usage (host, repo root): G1_RESULTS_ROOT=<bulk>; export G1_RESULTS_ROOT; sh designs/r1-joint/blocks/r1_afe/pex/run_iter_e9.sh <screen build id> <layout run id> <pex run id>
set -u
SRC=$1; LR=$2; PR=$3
cd "$(dirname "$0")/../../../../.."
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"; G1_CPUSET=${G1_CPUSET:-106-108}; export G1_RESULTS_ROOT G1_CPUSET
B=$G1_RESULTS_ROOT/r1_afe; mkdir -p $B/$LR $B/$PR
cp $B/$SRC/r1_afe.gds $B/$SRC/r1_afe_layout.json $B/$SRC/r1_afe_ports.json $B/$SRC/gen.log $B/$LR/
echo "copied from screen build $SRC (same generator file and flags)" > $B/$LR/SOURCE.txt
sh designs/r1-joint/blocks/r1_afe/layout/run_checks_e6.sh $LR > $B/$LR/checks_e6.out 2>&1 &
CK=$!
sh designs/r1-joint/blocks/r1_afe/pex/run_pex.sh $B/$PR $B/$LR/r1_afe.gds > $B/$PR/run_pex.out 2>&1
echo "kpex rc $?" >> $B/$PR/iter.log
G1_WORKDIR=designs/r1-joint/blocks/r1_afe; export G1_WORKDIR
KCH=$B/$PR/kpex_ch/r1_afe_ch_flat__r1_afe_ch; KTOP=$B/$PR/kpex_top/r1_afe_top_flat__r1_afe
flow/run.sh klayout -b -r pex/pex_rc_build.py -rd kchdir=$KCH -rd ktopdir=$KTOP -rd ports=$B/$LR/r1_afe_ports.json -rd out=$B/pexrc-$LR > $B/$PR/pexrc_build.log 2>&1; echo "rc build $?" >> $B/$PR/iter.log
flow/run.sh klayout -b -r pex/pex_rc_build.py -rd kchdir=$KCH -rd ktopdir=$KTOP -rd ports=$B/$LR/r1_afe_ports.json -rd noc=1 -rd out=$B/pexr-$LR > $B/$PR/pexr_build.log 2>&1; echo "r build $?" >> $B/$PR/iter.log
P=designs/r1-joint/blocks/r1_afe/pex; REP=designs/r1-joint/blocks/r1_afe/reports/$PR; mkdir -p $REP
python3 $P/pair_loads.py e8d19=$B/pex-e8-dev19/kpex_ch/r1_afe_ch_flat__r1_afe_ch/r1_afe_ch_k25d_pex_netlist.spice,$B/pex-e8-dev19/kpex_top/r1_afe_top_flat__r1_afe/r1_afe_k25d_pex_netlist.spice e9=$KCH/r1_afe_ch_k25d_pex_netlist.spice,$KTOP/r1_afe_k25d_pex_netlist.spice > $REP/pair_loads.json
python3 $P/x1_pair_r.py $B/pexr-$LR/r1_afe_post_rc.spice $B/$LR/r1_afe_ports.json > $REP/x1_pair_r.json
python3 $P/top_supply_z.py $B/pexr-$LR/r1_afe_post_rc.spice > $REP/top_supply_z.json
python3 $P/vss_mutual.py $B/pexr-$LR/r1_afe_post_rc.spice > $REP/vss_mutual.json 2>/dev/null
python3 $P/path_balance.py $B/pexr-$LR/r1_afe_post_rc.spice > $REP/path_balance.json
wait $CK
echo done > $B/$PR/iter.done
