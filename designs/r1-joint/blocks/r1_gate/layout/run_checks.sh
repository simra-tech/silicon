#!/bin/sh
# Generate one variant (hv or lv) of the gate layout, add the PDK fill, then run PDK DRC (main + maximal, density off),
# antenna and LVS on the filled GDS. Run from the repository root (POSIX sh):
#   G1_CPUSET=100-102; export G1_CPUSET; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; export G1_RESULTS_ROOT
#   sh designs/r1-joint/blocks/r1_gate/layout/run_checks.sh <hv|lv> <tag>
# Writes <G1_RESULTS_ROOT>/r1_gate/layout-{gen,drc,ant,lvs}-<variant>-<tag>/ and a run.json in each.
set -eu
V=$1
TAG=$V-$2
B=r1_gate
M=r1_gate_$V
R=$G1_RESULTS_ROOT/$B
L=designs/r1-joint/blocks/$B/layout
for k in gen drc ant lvs; do
  test ! -e "$R/layout-$k-$TAG" || { echo "run dir exists: $R/layout-$k-$TAG"; exit 1; }
  mkdir -p "$R/layout-$k-$TAG"
done
G1_WORKDIR=$L; export G1_WORKDIR
flow/run.sh klayout -b -r r1_gate_layout.py -rd variant=$V > "$R/layout-gen-$TAG/gen.log" 2>&1
flow/run.sh bash fill_r1_gate.sh $V > "$R/layout-gen-$TAG/fill.log" 2>&1
python3 $L/make_lvs_cdl.py $V >> "$R/layout-gen-$TAG/gen.log" 2>&1
unset G1_WORKDIR
cp $L/${M}.gds $L/${M}_filled.gds $L/${M}.lef $L/${M}_lvs.cdl "$R/layout-gen-$TAG/"
flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py --path=/work/$L/${M}_filled.gds \
  --run_mode=deep --no_density --run_dir="$R/layout-drc-$TAG" > "$R/layout-drc-$TAG/console.log" 2>&1 || true
flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py --path=/work/$L/${M}_filled.gds \
  --run_mode=deep --antenna_only --run_dir="$R/layout-ant-$TAG" > "$R/layout-ant-$TAG/console.log" 2>&1 || true
flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py --layout=/work/$L/${M}_filled.gds \
  --netlist=/work/$L/${M}_lvs.cdl --topcell=$M --run_mode=deep --no_series_res --run_dir="$R/layout-lvs-$TAG" \
  > "$R/layout-lvs-$TAG/console.log" 2>&1 || true
python3 $L/write_runjson.py $V "$2"
