#!/bin/sh
# Generate the r1_bias layout, then run the PDK DRC (main + maximal, deep, density off), the PDK antenna deck and the
# PDK LVS against the generated CDL, then the pin check. Run from the repository root (POSIX sh):
#   G1_CPUSET=116-119; export G1_CPUSET; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; export G1_RESULTS_ROOT
#   sh designs/r1-joint/blocks/r1_bias/layout/run_checks.sh <tag>
# Writes <G1_RESULTS_ROOT>/r1_bias/layout-{gen,drc,ant,lvs}-<tag>/ and a run.json in each (write_runjson.py).
# Method of blocks/r1_osc/layout/run_checks.sh. DRC and antenna run in parallel with LVS (KLayout only, 3 processes).
set -eu
TAG=$1
R=$G1_RESULTS_ROOT/r1_bias
L=designs/r1-joint/blocks/r1_bias/layout
for k in gen drc ant lvs; do
  test ! -e "$R/layout-$k-$TAG" || { echo "run dir exists: $R/layout-$k-$TAG"; exit 1; }
  mkdir -p "$R/layout-$k-$TAG"
done
G1_WORKDIR=$L; export G1_WORKDIR
flow/run.sh klayout -b -r r1_bias_layout.py > "$R/layout-gen-$TAG/gen.log" 2>&1 || { echo "generator failed"; tail -20 "$R/layout-gen-$TAG/gen.log"; exit 1; }
unset G1_WORKDIR
cp $L/r1_bias.gds $L/r1_bias_lvs.cdl $L/r1_bias_layout_meta.json "$R/layout-gen-$TAG/"
D=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
flow/run.sh python3 $D/drc/run_drc.py --path=/work/$L/r1_bias.gds --topcell=r1_bias \
  --run_mode=deep --no_density --run_dir="$R/layout-drc-$TAG" > "$R/layout-drc-$TAG/console.log" 2>&1 &
flow/run.sh python3 $D/drc/run_drc.py --path=/work/$L/r1_bias.gds --topcell=r1_bias \
  --run_mode=deep --antenna_only --run_dir="$R/layout-ant-$TAG" > "$R/layout-ant-$TAG/console.log" 2>&1 &
flow/run.sh python3 $D/lvs/run_lvs.py --layout=/work/$L/r1_bias.gds \
  --netlist=/work/$L/r1_bias_lvs.cdl --topcell=r1_bias --run_mode=deep --run_dir="$R/layout-lvs-$TAG" \
  > "$R/layout-lvs-$TAG/console.log" 2>&1 || true
wait
python3 $L/write_runjson.py "$TAG"
flow/run.sh python3 $L/check_pins.py $L/r1_bias.gds $L/r1_bias_lvs.cdl r1_bias > "$R/layout-gen-$TAG/pin_check.log" 2>&1 || true
cat "$R/layout-gen-$TAG/pin_check.log"
