#!/bin/sh
# Generate the layout (no fill: single cell), then run PDK DRC (main + maximal, density off), antenna and LVS.
# Run from the repository root (POSIX sh):
#   G1_CPUSET=100-102; export G1_CPUSET; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; export G1_RESULTS_ROOT
#   sh designs/r1-joint/blocks/r1_ls/layout/run_checks.sh <tag>
# Writes <G1_RESULTS_ROOT>/r1_ls/layout-{gen,drc,ant,lvs}-<tag>/ and a run.json in each.
set -eu
TAG=$1
B=r1_ls
R=$G1_RESULTS_ROOT/$B
L=designs/r1-joint/blocks/$B/layout
for k in gen drc ant lvs; do
  test ! -e "$R/layout-$k-$TAG" || { echo "run dir exists: $R/layout-$k-$TAG"; exit 1; }
  mkdir -p "$R/layout-$k-$TAG"
done
G1_WORKDIR=$L; export G1_WORKDIR
flow/run.sh klayout -b -r r1_ls_layout.py > "$R/layout-gen-$TAG/gen.log" 2>&1
python3 $L/make_lvs_cdl.py >> "$R/layout-gen-$TAG/gen.log" 2>&1
unset G1_WORKDIR
cp $L/r1_ls.gds $L/r1_ls.lef $L/r1_ls.vh $L/r1_ls_lvs.cdl "$R/layout-gen-$TAG/"
flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py --path=/work/$L/r1_ls.gds \
  --run_mode=deep --no_density --run_dir="$R/layout-drc-$TAG" > "$R/layout-drc-$TAG/console.log" 2>&1 || true
flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py --path=/work/$L/r1_ls.gds \
  --run_mode=deep --antenna_only --run_dir="$R/layout-ant-$TAG" > "$R/layout-ant-$TAG/console.log" 2>&1 || true
flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py --layout=/work/$L/r1_ls.gds \
  --netlist=/work/$L/r1_ls_lvs.cdl --topcell=r1_ls --run_mode=deep --run_dir="$R/layout-lvs-$TAG" \
  > "$R/layout-lvs-$TAG/console.log" 2>&1 || true
python3 $L/write_runjson.py "$TAG"
