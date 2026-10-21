#!/bin/sh
# One gate-level job on the compiled model of an earlier run, with line-buffered output (partial results survive a stop).
# usage (repo root, via flow/run.sh): sh sim/signoff/run_gl_one.sh <src-run>/<mode> <new-run>/<mode> <test> <clk_ns> <SDF mode: MAXIMUM|TYPICAL>
set -u
export LD_LIBRARY_PATH=/foss/tools/iverilog/lib
R=$G1_RESULTS_ROOT/r1_ctrl
SRC=$R/$1; DST=$R/$2; T=$3; CK=$4; SM=$5
mkdir -p "$DST"; cp "$SRC"/tb_gl.vvp "$SRC"/delays.sdf "$SRC"/nl_sdf.v "$SRC"/tb_top_gl.v "$SRC"/compile.log "$SRC"/prep_sdf.log "$SRC"/versions.txt "$DST"/
cd "$DST"; s=$(date +%s)
stdbuf -oL vvp -n tb_gl.vvp +test=$T +clk_ns=$CK +sdf=$DST/delays.sdf +sdfmode=$SM > top_${T}_${CK}.log 2>&1
echo "rc=$? wall_s=$(( $(date +%s) - s ))" > top_${T}_${CK}.rc
