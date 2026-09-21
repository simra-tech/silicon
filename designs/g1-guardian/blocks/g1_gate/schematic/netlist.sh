#!/usr/bin/env bash
# Netlist the G1_GATE schematics with xschem (headless) inside the pinned container.
# Usage (from repo root): G1_WORKDIR=designs/g1-guardian/blocks/g1_gate/schematic flow/run.sh bash netlist.sh
# Output: ../sim/netlist/<top>.spice with the top schematic as a .subckt.
set -uo pipefail
RC=/foss/pdks/ihp-sg13g2/libs.tech/xschem/xschemrc
OUT=../sim/netlist
mkdir -p "$OUT"
for top in g1_lvlup g1_lvldn g1_gate; do
  xschem -n -q -x --rcfile "$RC" -o "$OUT" "$top.sch" >/dev/null 2>&1 || true
  # xschem writes the top cell as a commented subckt; make it a real one
  sed -i -e 's/^\*+ /+ /' -e 's/^\*\*\.subckt/.subckt/' -e 's/^\*\*\.ends/.ends/' -e '/^\.end$/d' "$OUT/$top.spice"
done
ls -l "$OUT"
