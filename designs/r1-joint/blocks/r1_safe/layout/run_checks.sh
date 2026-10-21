#!/bin/sh
# Generate the r1_safe layout, then run the PDK DRC (main + maximal, density off), the PDK antenna check, the PDK LVS
# (stock deck) and the PDK LVS with comparer search limits (diagnostic copy, see below), the pin check and run.json.
# Run from the repository root (POSIX sh):
#   G1_CPUSET=116-117; export G1_CPUSET; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; export G1_RESULTS_ROOT
#   sh designs/r1-joint/blocks/r1_safe/layout/run_checks.sh <tag>
# Writes <G1_RESULTS_ROOT>/r1_safe/layout-{gen,drc,ant,lvs,lvsx}-<tag>/ with a run.json in each.
#
# Diagnostic LVS (lvsx): KLayout 0.30.9 with the stock deck crashes (signal 11 in NetlistCrossReference::sort_circuit)
# or leaves the symmetric multiplexer nets unresolved. The lvsx run uses a copy of the PDK LVS directory with exactly
# two added lines after "align": max_depth(8) and max_branch_complexity(100). These are comparer search limits; no
# layer derivation, device extraction or rule is changed. The copy is made in the run directory at run time.
set -eu
TAG=$1
PDKD=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
R=$G1_RESULTS_ROOT/r1_safe
L=designs/r1-joint/blocks/r1_safe/layout
for k in gen drc ant lvs lvsx; do
  test ! -e "$R/layout-$k-$TAG" || { echo "run dir exists: $R/layout-$k-$TAG"; exit 1; }
  mkdir -p "$R/layout-$k-$TAG"
done
G=$R/layout-gen-$TAG
G1_WORKDIR=$L; export G1_WORKDIR
flow/run.sh klayout -b -r r1_safe_layout.py -rd out="$G" -rd cmp=1 > "$G/gen.log" 2>&1
unset G1_WORKDIR
python3 $L/make_cdl.py "$G/r1_safe_lvs.cdl" >> "$G/gen.log" 2>&1
python3 $L/check_pins.py "$G/r1_safe.lef" "$G/r1_safe_lvs.cdl" r1_safe > "$G/pin_check.log" 2>&1 || true
flow/run.sh python3 $PDKD/drc/run_drc.py --path="$G/r1_safe.gds" --run_mode=deep --no_density \
  --run_dir="$R/layout-drc-$TAG" > "$R/layout-drc-$TAG/console.log" 2>&1 || true
flow/run.sh python3 $PDKD/drc/run_drc.py --path="$G/r1_safe.gds" --run_mode=deep --antenna_only \
  --run_dir="$R/layout-ant-$TAG" > "$R/layout-ant-$TAG/console.log" 2>&1 || true
flow/run.sh python3 $PDKD/lvs/run_lvs.py --layout="$G/r1_safe.gds" --netlist="$G/r1_safe_lvs.cdl" --topcell=r1_safe \
  --run_mode=deep --run_dir="$R/layout-lvs-$TAG" > "$R/layout-lvs-$TAG/console.log" 2>&1 || true
# diagnostic deck copy (run_lvs.py reads <copy root>/versions.txt five levels up, so keep the PDK depth)
X=$R/layout-lvsx-$TAG
mkdir -p "$X/deck/p/libs.tech/klayout/tech"
flow/run.sh sh -c "cp -r $PDKD/lvs $X/deck/p/libs.tech/klayout/tech/ && cp /foss/pdks/versions.txt $X/deck/"
sed -i 's/^  align$/  align\n  max_depth(8)\n  max_branch_complexity(100)/' "$X/deck/p/libs.tech/klayout/tech/lvs/sg13g2.lvs"
flow/run.sh python3 "$X/deck/p/libs.tech/klayout/tech/lvs/run_lvs.py" --layout="$G/r1_safe.gds" \
  --netlist="$G/r1_safe_lvs.cdl" --topcell=r1_safe --run_mode=deep --run_dir="$X/out" > "$X/console.log" 2>&1 || true
python3 $L/write_runjson.py "$TAG"
