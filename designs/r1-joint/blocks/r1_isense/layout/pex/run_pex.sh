#!/bin/sh
# PEX of r1_isense (channel r1_isense_ch). Run from the repo root on the host:
#   G1_CPUSET=...; export G1_CPUSET; G1_RESULTS_ROOT=...; export G1_RESULTS_ROOT
#   sh designs/r1-joint/blocks/r1_isense/layout/pex/run_pex.sh <run id>
# Steps: flatten + strip MIM (pex_prepare.py), kpex 2.5D CC, R network + MIM (pex_build.py), port-to-main-node
# wiring resistance (pex_paths.py), post-layout netlists and decks (make_post.py, views RC, _c, _r).
set -e
RID=$1
B=designs/r1-joint/blocks/r1_isense/layout
P=$G1_RESULTS_ROOT/r1_isense/$RID
mkdir -p $P
flow/run.sh klayout -b -r $B/pex/pex_prepare.py -rd gds=/work/$B/r1_isense.gds -rd out=$P/ch_nomim.gds > $P/prepare.log 2>&1
flow/run.sh kpex --version > $P/kpex_version.log 2>&1 || true
flow/run.sh kpex --pdk ihp_sg13g2 --threads 3 --gds $P/ch_nomim.gds --cell r1_isense_ch \
  --schematic /work/$B/r1_isense_lvs.cdl --2.5D --mode CC --out_dir $P/kpex > $P/kpex.console.log 2>&1
flow/run.sh klayout -b -r $B/pex/pex_build.py -rd kpexdir=$P/kpex/ch_nomim__r1_isense_ch -rd gds=$P/ch_nomim.gds \
  -rd out=$P/rc -rd cdl=/work/$B/r1_isense_lvs.cdl > $P/pex_build.console.log 2>&1
flow/run.sh python3 $B/pex/pex_paths.py $P/rc > $P/pex_paths.log 2>&1
python3 $B/pex/make_post.py $P/rc $P/decks
python3 $B/pex/make_post.py $P/rc $P/decks_c _c
python3 $B/pex/make_post.py $P/rc $P/decks_r _r
sha256sum $B/r1_isense.gds $B/r1_isense_lvs.cdl designs/r1-joint/blocks/r1_isense/schematic/r1_isense.spice | sed "s#  $B/#  layout/#; s#  designs/r1-joint/blocks/r1_isense/#  #" > $P/inputs.sha256
flow/run.sh python3 $B/tools/write_pex_runjson.py $RID
echo "run_pex: done $RID"
