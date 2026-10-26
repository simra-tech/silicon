#!/bin/sh
# Chip fill of r1_top (track T8). POSIX sh, repository root as cwd, G1_CPUSET, G1_RESULTS_ROOT and G1_WORKDIR exported.
#   sh designs/r1-joint/blocks/r1_top/flow/fill_top.sh <source run dir> <fill run dir> [ring_depth_um=0] [thru=] [metal2_distance_um=1.0] [gatpoly_gap_um=1.6] [metal345_distance_um=2.0]
# <source run dir> holds r1_top.gds (e.g. $G1_RESULTS_ROOT/r1_top/asm-20261021-e4); <fill run dir> is new
# (e.g. $G1_RESULTS_ROOT/r1_top/asm-20261021-e4-fill) and receives r1_top.gds (filled), fill_exclusions.json,
# fill_counts.json, filler.log and the pre-fill GDS. The unmodified PDK filler (libs.tech/klayout/tech/scripts/filler.py,
# three macros ActGatP, Metal, TopMetal, default distances) fills the interior of the real sealring (EdgeSeal 39/0 holes).
# Steps: fill_top_pre.py (temporary no-fill cell: macros, ADC placeholder, pad ring band, bond openings) -> stock filler
# -> fill_top_post.py (remove temporary cell, geometry gate: only datatype-22 fill layers differ, count fill).
# The macros are not edited: their cells are the same cells as before.
set -eu
SRC=$1; DST=$2; RD=${3:-0}; THRU=${4:-}; M2D=${5:-1.0}; GPH=${6:-1.6}; M345D=${7:-2.0}
T=designs/r1-joint/blocks/r1_top/flow
[ -f "$SRC/r1_top.gds" ] || { echo "no $SRC/r1_top.gds"; exit 1; }
[ ! -e "$DST/r1_top.gds" ] || { echo "$DST/r1_top.gds exists; use a new run directory"; exit 1; }
mkdir -p "$DST"
sha256sum "$SRC/r1_top.gds" > "$DST/input_gds.sha256"
flow/run.sh klayout -b -r $T/fill_top_pre.py -rd src="$SRC/r1_top.gds" -rd dst="$DST/r1_top_prefill.gds" \
  -rd out="$DST/fill_exclusions.json" -rd ring_depth=$RD -rd thru="$THRU" > "$DST/pre.log" 2>&1
# Run-time copy of the PDK filler scripts (like the LVS deck copy of run_lvs_top.sh). Two numbers differ from the PDK
# default, both inside the rule limits; nothing else changes:
#   Metal2 filler distance 1.5 um -> $M2D um (the macro's own parameter; minimum 0.42 um by rule M2Fil.b). The default
#     gives 49 % coverage of free area, too little for the global Metal2 minimum of 35 % (M2.j).
#   Metal3-5 filler distance 2.0 um -> $M345D um (same parameter, minimum 0.42 um by rules M3Fil.b, M4Fil.b, M5Fil.b). Tried
#     when the 800 um window minimum of 25 % (M3Fil.h, M4Fil.h, M5Fil.h) is not reached at 2.0 um.
#   GatPoly filler horizontal gap 5.0 um -> $GPH um (gp_spacing_h = width + gap; minimum 0.8 um by rule GFil.c). The
#     default gives 28 % coverage, too little for the global GatPoly minimum of 15 % (GFil.g).
PD=$DST/pdkcopy/ihp-sg13g2/libs.tech/klayout/tech
mkdir -p "$PD"
flow/run.sh sh -c "cp -r /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/macros /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/scripts $PD/"
sed -i "s/'distance_m2' => 1.5,/'distance_m2' => $M2D,/" "$PD/macros/sg13g2_filler_Metal.lym"
for k in 3 4 5; do sed -i "s/'distance_m$k' => 2.0,/'distance_m$k' => $M345D,/" "$PD/macros/sg13g2_filler_Metal.lym"; done
sed -i "s/gp_spacing_h = gp_width + 5\$/gp_spacing_h = gp_width + $GPH/" "$PD/macros/sg13g2_filler_ActGatP.lym"
for m in Metal ActGatP; do
  flow/run.sh diff /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/macros/sg13g2_filler_$m.lym "$PD/macros/sg13g2_filler_$m.lym" 2>/dev/null | grep -v "^time=\|^Resource" >> "$DST/filler_macro_diff.txt" || true
done
flow/run.sh env PDK_ROOT="$DST/pdkcopy" PDK=ihp-sg13g2 klayout -n sg13g2 -zz -r "$PD/scripts/filler.py" \
  -rd output_file="$DST/r1_top_filler_out.gds" "$DST/r1_top_prefill.gds" > "$DST/filler.log" 2>&1
# Step 2b: drop the GatPoly filler rectangles that break maximal-deck rule GFil.j (see fill_top_fixj.py).
flow/run.sh klayout -b -r $T/fill_top_fixj.py -rd src="$DST/r1_top_filler_out.gds" -rd dst="$DST/r1_top_filler_fixj.gds" \
  -rd out="$DST/fill_fixj.json" > "$DST/fixj.log" 2>&1
flow/run.sh klayout -b -r $T/fill_top_post.py -rd orig="$SRC/r1_top.gds" -rd filled="$DST/r1_top_filler_fixj.gds" \
  -rd dst="$DST/r1_top.gds" -rd out="$DST/fill_counts.json" > "$DST/post.log" 2>&1
sha256sum "$DST/r1_top.gds" > "$DST/r1_top.gds.sha256"
cat "$DST/pre.log" | tail -1; tail -3 "$DST/post.log"
