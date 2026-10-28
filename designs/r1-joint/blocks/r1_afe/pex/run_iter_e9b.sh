#!/bin/sh
# Layout E9b (track T3n, decision D29): E9 generator and flags with the x1p C trim at 23/23 edges, netlist F3 passed
# explicitly to every step (generator, wiring-R view, RC build; ledger F-20261030-T3m-08). Steps: generator; checks
# (DRC main + maximal, antenna, LVS, supply islands, pins) in parallel with the wiring-R view (KLayout LVS deck of kpex
# + RNetExtractor R, for the early op/drift screen); kpex 2.5D CC of top and channel in parallel; RC and wiring-R
# netlists from kpex; pair loads (E9 against E9b), x1 pair R, top supply z, vss mutual, path balance.
# usage (host, repo root): G1_RESULTS_ROOT=<bulk>; export G1_RESULTS_ROOT; sh designs/r1-joint/blocks/r1_afe/pex/run_iter_e9b.sh <layout run id> <pex run id>
set -u
LR=$1; PR=$2; SCH=r1_afe_revF3.spice
cd "$(dirname "$0")/../../../../.."
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"; G1_CPUSET=106-108; export G1_RESULTS_ROOT G1_CPUSET
B=$G1_RESULTS_ROOT/r1_afe; L=$B/$LR; D=$B/$PR; mkdir -p $L $D
G1_WORKDIR=designs/r1-joint/blocks/r1_afe; export G1_WORKDIR
echo "gen start $(date -u +%FT%TZ)" > $L/iter.log
flow/run.sh klayout -b -r layout/r1_afe_layout.py -rd out=$L/r1_afe.gds -rd adjpairs=2 -rd fwide=1 -rd x1bus=1 -rd x1w2=1 \
  -rd x1vfill=1 -rd x1vcl=1 -rd x1headarr=1 -rd x1railv=1 -rd x1feed=40 -rd x1wmode=none -rd o1first=1 \
  -rd dumpnets=x1p,x1n,xa1_o1n,xa1_o1p,inp,inn,xa1_fn,xa1_fp -rd ctrim=x1p:1:23,x1p:2:23 -rd fnshift=0 -rd devx=1 \
  -rd sch=$SCH > $L/gen.log 2>&1
echo "gen rc $? $(date -u +%FT%TZ)" >> $L/iter.log
[ -s $L/r1_afe.gds ] || { echo "no gds" >> $L/iter.log; exit 1; }
sh designs/r1-joint/blocks/r1_afe/layout/run_checks_e6.sh $LR > $L/checks_e6.out 2>&1 &
CK=$!
# wiring-R view from the LVS deck of kpex (as pex/run_pexr.sh, with the F3 devices)
V=$B/pexr-$LR-lvs; mkdir -p $V/lvs_ch/r1_afe_ch_flat__r1_afe_ch $V/lvs_top/r1_afe_top_flat__r1_afe
K=/usr/local/lib/python3.12/dist-packages/klayout_pex/pdk/ihp-sg13g2/libs.tech/kpex/sg13g2.lvs
O="-rd thr=1 -rd run_mode=deep -rd spice_net_names=true -rd spice_comments=false -rd scale=false -rd verbose=false -rd schematic_simplify=false -rd net_only=false -rd top_lvl_pins=true -rd combine=false -rd combine_devices=false -rd purge=false -rd purge_nets=false -rd no_simplify=true"
flow/run.sh klayout -b -r pex/pex_prepare.py -rd gds=$L/r1_afe.gds -rd out=$D/r1_afe_ch_flat.gds -rd cell=r1_afe_ch > $D/prep_ch.log 2>&1
flow/run.sh klayout -b -r pex/pex_prepare.py -rd gds=$L/r1_afe.gds -rd out=$D/r1_afe_top_flat.gds -rd cell=top_only > $D/prep_top.log 2>&1
flow/run.sh klayout -b -r $K -rd input=$D/r1_afe_ch_flat.gds -rd report=$V/lvs_ch/r1_afe_ch_flat__r1_afe_ch/r1_afe_ch.lvsdb.gz -rd schematic=/work/designs/r1-joint/blocks/r1_afe/layout/r1_afe_lvs.cdl $O > $V/lvs_ch_console.log 2>&1; echo "kpex-deck lvs ch rc $?" >> $L/iter.log
flow/run.sh klayout -b -r $K -rd input=$D/r1_afe_top_flat.gds -rd report=$V/lvs_top/r1_afe_top_flat__r1_afe/r1_afe.lvsdb.gz -rd schematic=/work/designs/r1-joint/blocks/r1_afe/layout/r1_afe_lvs.cdl $O > $V/lvs_top_console.log 2>&1; echo "kpex-deck lvs top rc $?" >> $L/iter.log
flow/run.sh klayout -b -r pex/pex_rc_build.py -rd kchdir=$V/lvs_ch/r1_afe_ch_flat__r1_afe_ch -rd ktopdir=$V/lvs_top/r1_afe_top_flat__r1_afe -rd ports=$L/r1_afe_ports.json -rd noc=1 -rd sch=$SCH -rd out=$V/pexr > $V/pexr_build.log 2>&1; echo "lvs-view R build rc $? $(date -u +%FT%TZ)" >> $L/iter.log
# kpex 2.5D CC, top (1 thread) and channel (2 threads) in parallel
flow/run.sh kpex --pdk ihp-sg13g2 --threads 1 --gds $D/r1_afe_top_flat.gds --schematic layout/r1_afe_lvs.cdl --cell r1_afe --2.5D --mode CC --out_dir $D/kpex_top > $D/kpex_top_console.log 2>&1 &
KT=$!
flow/run.sh kpex --pdk ihp-sg13g2 --threads 2 --gds $D/r1_afe_ch_flat.gds --schematic layout/r1_afe_lvs.cdl --cell r1_afe_ch --2.5D --mode CC --out_dir $D/kpex_ch > $D/kpex_ch_console.log 2>&1
echo "kpex ch rc $? $(date -u +%FT%TZ)" >> $L/iter.log
wait $KT; echo "kpex top rc $?" >> $L/iter.log
KCH=$D/kpex_ch/r1_afe_ch_flat__r1_afe_ch; KTOP=$D/kpex_top/r1_afe_top_flat__r1_afe
for f in $KCH/r1_afe_ch_k25d_pex_netlist.spice $KTOP/r1_afe_k25d_pex_netlist.spice; do [ -s $f ] || { echo "missing $f" >> $L/iter.log; exit 1; }; done
flow/run.sh klayout -b -r pex/pex_rc_build.py -rd kchdir=$KCH -rd ktopdir=$KTOP -rd ports=$L/r1_afe_ports.json -rd sch=$SCH -rd out=$B/pexrc-$LR > $D/pexrc_build.log 2>&1; echo "rc build rc $?" >> $L/iter.log
flow/run.sh klayout -b -r pex/pex_rc_build.py -rd kchdir=$KCH -rd ktopdir=$KTOP -rd ports=$L/r1_afe_ports.json -rd noc=1 -rd sch=$SCH -rd out=$B/pexr-$LR > $D/pexr_build.log 2>&1; echo "r build rc $?" >> $L/iter.log
P=designs/r1-joint/blocks/r1_afe/pex; REP=designs/r1-joint/blocks/r1_afe/reports/$PR; mkdir -p $REP
python3 $P/pair_loads.py e9=$B/pex-e9-dev21/kpex_ch/r1_afe_ch_flat__r1_afe_ch/r1_afe_ch_k25d_pex_netlist.spice,$B/pex-e9-dev21/kpex_top/r1_afe_top_flat__r1_afe/r1_afe_k25d_pex_netlist.spice e9b=$KCH/r1_afe_ch_k25d_pex_netlist.spice,$KTOP/r1_afe_k25d_pex_netlist.spice > $REP/pair_loads.json
python3 $P/x1_pair_r.py $B/pexr-$LR/r1_afe_post_rc.spice $L/r1_afe_ports.json > $REP/x1_pair_r.json
python3 $P/top_supply_z.py $B/pexr-$LR/r1_afe_post_rc.spice > $REP/top_supply_z.json
python3 $P/vss_mutual.py $B/pexr-$LR/r1_afe_post_rc.spice > $REP/vss_mutual.json 2>/dev/null
python3 $P/path_balance.py $B/pexr-$LR/r1_afe_post_rc.spice > $REP/path_balance.json
wait $CK
echo "done $(date -u +%FT%TZ)" >> $L/iter.log; echo done > $D/iter.done
