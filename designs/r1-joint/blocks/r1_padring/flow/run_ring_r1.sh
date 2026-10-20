#!/usr/bin/env bash
# Reproduce the R1 ring reference (run ring-20261020-a): build from the G1 r4 ring cells, PDK fill, timestamp-free
# rewrite, CDL/projection references, physical checks, bond plan.  Every tool runs through flow/run.sh.
#   G1_CPUSET=116-119 G1_CPUS=4 G1_RESULTS_ROOT=<results root> designs/r1-joint/blocks/r1_padring/flow/run_ring_r1.sh <run-id>
# Status: the steps below were run one by one on 2026-10-20 with these commands.  This script, chained, was not run
# as one piece.  Large outputs (GDS, lvsdb) go to $G1_RESULTS_ROOT/r1_padring/<run-id>/; small reports to reports/<run-id>/.
set -euo pipefail
ID=${1:-ring-20261020-a}
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)
B=designs/r1-joint/blocks/r1_padring
R=$G1_RESULTS_ROOT/r1_padring/$ID; mkdir -p "$R"
cd "$REPO"
G1GDS=/work/designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r4.gds
test "$(sha256sum designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r4.gds | cut -d' ' -f1)" = 225d0b535321ed312594bb13d97b7271014f487162564a56c874572de715173a
run() { G1_WORKDIR=$B flow/run.sh "$@"; }
# 1 ring cells of G1 r4 re-assigned to the R1 pin map, core emptied
run klayout -b -r flow/build_ring.py -rd src=$G1GDS -rd out=$R/r1_padring_nofill.gds -rd report=$R/build_ring.json
# 2 PDK fill (Activ/GatPoly, Metal1-5, TopMetal1/2)
run bash -c "KLAYOUT_PATH=\$PDK_ROOT/\$PDK/libs.tech/klayout klayout -n sg13g2 -zz -r \$PDK_ROOT/\$PDK/libs.tech/klayout/tech/scripts/filler.py -rd output_file=$R/r1_padring_filled_raw.gds $R/r1_padring_nofill.gds" > "$R/fill.log" 2>&1
# 3 rewrite without timestamps (equal content -> equal bytes)
run klayout -b -r flow/rewrite_gds.py -rd i=$R/r1_padring_filled_raw.gds -rd o=$R/r1_padring_a.gds
# 4 references
python3 $B/flow/make_cdl.py designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl $B/netlist/r1_padring.cdl $B/netlist/r1_padring_projection_src.cdl $B/netlist/r1_padring_ringonly_projection_src.cdl
run klayout -b -r flow/flatten_reference.rb -rd source=/work/$B/netlist/r1_padring_projection_src.cdl -rd output=/work/$B/netlist/r1_padring_projected_ref.cdl -rd top=r1_padring
run klayout -b -r flow/flatten_reference.rb -rd source=/work/$B/netlist/r1_padring_ringonly_projection_src.cdl -rd output=/work/$B/netlist/r1_padring_ringonly_projected_ref.cdl -rd top=r1_padring
python3 $B/flow/make_lef.py $B/layout/r1_padring_ref.lef
# 5 checks: DRC main/maximal/density/antenna/precheck, LVS projected (G1 form), LVS canonical
$B/flow/run_signoff.sh "$R" "$R/r1_padring_a.gds" r1_padring /work/$B/netlist/r1_padring_projected_ref.cdl /work/$B/netlist/r1_padring.cdl
# 6 LVS, ring-only projected reference (substrate node separate from VSS, see README)
mkdir -p "$R/signoff/lvs_projected_ringonly"
run python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py --layout "$R/r1_padring_a.gds" --netlist /work/$B/netlist/r1_padring_ringonly_projected_ref.cdl --topcell r1_padring --run_mode deep --top_lvl_pins --spice_comments --run_dir "$R/signoff/lvs_projected_ringonly"
# 7 bond plan and its geometric check
SHA=$(sha256sum "$R/r1_padring_a.gds" | cut -d' ' -f1)
G1_WORKDIR=. flow/run.sh klayout -b -r designs/r1-joint/padframe/bondplan_r1.py -rd gds=$R/r1_padring_a.gds -rd src_csv=designs/r1-joint/padframe/bondmap_src_r1.csv -rd out_csv=designs/r1-joint/padframe/bondmap_r1_ring.csv -rd out_svg=designs/r1-joint/padframe/bondplan_r1.svg -rd out_json=designs/r1-joint/padframe/bondplan_r1.json -rd gds_sha=$SHA
G1_WORKDIR=. flow/run.sh klayout -b -r $B/flow/verify_bondmap.py -rd g=$R/r1_padring_a.gds -rd csvf=designs/r1-joint/padframe/bondmap_r1_ring.csv -rd out=$B/reports/bondmap/verify_bondmap_r1.json
