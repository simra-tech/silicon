#!/usr/bin/env bash
# Netlist a schematic in this directory with xschem (headless) and expose the top level as a
# .subckt. Run from the repository root inside the pinned container:
#   G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/xschem flow/run.sh bash netlist.sh g1_bgr
set -euo pipefail
cell="$1"
xschem --rcfile xschemrc -n -q -x "${cell}.sch" 2>&1 | grep -v "^$" | grep -v "MODELS_" || true
sed -i -e 's/^\*\*\.subckt/.subckt/' -e 's/^\*\*\.ends/.ends/' -e '/^\.end$/d' "${cell}.spice"
if grep -q "IS MISSING" "${cell}.spice"; then echo "unresolved symbols in ${cell}.sch"; exit 1; fi
echo "wrote ${cell}.spice"
