#!/usr/bin/env bash
# Netlist the R1_OSC xschem sheets (headless, pinned container) into xschem_netlist/r1_osc.spice.
# Usage (repo root): G1_CPUSET=100-102 G1_WORKDIR=designs/r1-joint/blocks/r1_osc/schematic flow/run.sh bash netlist_xschem.sh
set -uo pipefail
RC=/foss/pdks/ihp-sg13g2/libs.tech/xschem/xschemrc
OUT=xschem_netlist
mkdir -p "$OUT"
xschem -n -q -x --rcfile "$RC" -o "$OUT" r1_osc.sch >/dev/null 2>&1 || true
sed -i -e 's/^\*\*\.subckt/.subckt/' -e 's/^\*\*\.ends/.ends/' -e '/^\.end$/d' "$OUT/r1_osc.spice"
xschem --version 2>/dev/null | head -1 > "$OUT/xschem_version.txt" || true
ls -l "$OUT"
