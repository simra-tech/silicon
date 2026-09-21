#!/usr/bin/env bash
# Netlist the g1_ls schematics with xschem (headless) inside the pinned container.
# Usage (repo root): G1_WORKDIR=designs/g1-guardian/blocks/g1_ctrl/ls/xschem flow/run.sh bash netlist.sh
# Output: ../sim/netlist/g1_ls_up.spice with the cell as a .subckt (in out vdd vdda vss) for ngspice,
#         ../sim/netlist/g1_ls_up.cdl (same netlist, MOS as M elements) for the KLayout LVS deck.
set -uo pipefail
RC=/foss/pdks/ihp-sg13g2/libs.tech/xschem/xschemrc
OUT=../sim/netlist
mkdir -p "$OUT"
for top in g1_ls_up; do
  xschem -n -q -x --rcfile "$RC" -o "$OUT" "$top.sch" >/dev/null 2>&1 || true
  # xschem writes the top cell as a commented subckt; make it a real one
  sed -i -e 's/^\*+ /+ /' -e 's/^\*\*\.subckt/.subckt/' -e 's/^\*\*\.ends/.ends/' -e '/^\.end$/d' "$OUT/$top.spice"
  # CDL for the KLayout LVS deck (run_lvs.py): the deck's reader takes MOS devices as M elements
  # (M<name> d g s b <model> w= l=), while xschem emits the PDK MOS symbols as X subcircuit calls;
  # the conversion is mechanical (XM -> M, drop the ngspice-only mm_ok flag), nothing else changes.
  sed -e 's/^XM/M/' -e 's/ mm_ok=1//' "$OUT/$top.spice" > "$OUT/$top.cdl"
done
ls -l "$OUT"; cat "$OUT/g1_ls_up.spice" "$OUT/g1_ls_up.cdl"
