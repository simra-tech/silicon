#!/bin/sh
# usage (repo root): flow/run.sh sh sim/signoff/run_equiv.sh <run-id>
set -u
RID="$1"
T7=$G1_RESULTS_ROOT/r1_ctrl/r1ctrl_ll_20261021_t7/flow/runs/r1ctrl_ll_20261021_t7
OUT="$G1_RESULTS_ROOT/r1_ctrl/$RID"
mkdir -p "$OUT"
sed -e "s|@RTL@|$G1_RESULTS_ROOT/r1_ctrl/r1ctrl_ll_20261021_t7/rtl|g" \
    -e "s|@NL@|$T7/06-yosys-synthesis/r1_ctrl_top.nl.v|" \
    -e "s|@LIB@|/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib|" \
    sim/signoff/equiv.ys.in > "$OUT/equiv.ys"
{ yosys -V; sha256sum "$T7/06-yosys-synthesis/r1_ctrl_top.nl.v"; cat "$G1_RESULTS_ROOT"/r1_ctrl/r1ctrl_ll_20261021_t7/rtl/*.v | sha256sum; } > "$OUT/versions.txt"
cd "$OUT" && timeout 3000 yosys -l equiv.log equiv.ys > equiv.stdout 2>&1; echo "yosys rc=$?" >> equiv.log
