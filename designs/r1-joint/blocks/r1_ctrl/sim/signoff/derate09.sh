#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Revision 0.9: ctrl IR-drop derate at the try-h1 losses, method of ../r1_top/irderate/run_derate.sh (tracks T11b, T8g).
# The cell characterisation and the derate factors are not rerun: they depend on the supply losses and the cells, not on
# the netlist, so the factor cases of run <G1_RESULTS_ROOT>/r1_top/r1ctrl_irderate_h1dev1 (cases.txt) are reused. Only the
# OpenSTA step (../r1_top/irderate/sta_derate.tcl, read-only) and the parser (sta_parse.py, read-only) run, on the 0.9
# netlist, the sign-off SDC and the nominal SPEF of the given hardening run.
# Inside the container, G1_WORKDIR = this block directory:
#   flow/run.sh sh sim/signoff/derate09.sh <ll-run> <out-run-id>
set -u
LL=$1; O=$G1_RESULTS_ROOT/r1_ctrl/$2
I=../r1_top/irderate
H1=$G1_RESULTS_ROOT/r1_top/r1ctrl_irderate_h1dev1
[ -e "$O" ] && { echo "$O exists"; exit 1; }
mkdir -p "$O/sta"
F=${DERATE_FINAL:-$G1_RESULTS_ROOT/r1_ctrl/$LL/flow/runs/$LL/final}   # DERATE_FINAL=<dir with nl/, spef/nom/> before the flow end
[ -f "$F/nl/r1_ctrl_top.nl.v" ] && [ -f "$F/spef/nom/r1_ctrl_top.nom.spef" ] || { echo "no netlist or SPEF in $F" > "$O/FAILED"; exit 1; }
cp "$H1/cases.txt" "$H1/loss_V.json" "$H1/factors.json" "$H1/factors_ff.json" "$O/"
CASES=$(sed -n 's/^slow //p' "$O/cases.txt"); CASESF=$(sed -n 's/^fast //p' "$O/cases.txt")
sha256sum "$F/nl/r1_ctrl_top.nl.v" flow/r1_ctrl.sdc "$F/spef/nom/r1_ctrl_top.nom.spef" "$I/sta_derate.tcl" "$I/sta_parse.py" "$O/cases.txt" > "$O/inputs.sha256"
export NETLIST="$F/nl/r1_ctrl_top.nl.v" SDC=flow/r1_ctrl.sdc SPEF="$F/spef/nom/r1_ctrl_top.nom.spef"
LIBNAME=slow_1p08V_125C CASES="$CASES" sta -no_splash -exit "$I/sta_derate.tcl" > "$O/sta/derate_slow_1p08V_125C.rpt" 2>&1
LIBNAME=fast_1p32V_m40C CASES="$CASESF" sta -no_splash -exit "$I/sta_derate.tcl" > "$O/sta/derate_fast_1p32V_m40C.rpt" 2>&1
python3 "$I/sta_parse.py" "$O/sta/derate_slow_1p08V_125C.rpt" > "$O/sta/derate_summary.json"
python3 "$I/sta_parse.py" "$O/sta/derate_fast_1p32V_m40C.rpt" > "$O/sta/derate_fast_summary.json"
echo "pdk_commit $(cat /foss/pdks/ihp-sg13g2/COMMIT)" > "$O/versions.txt"
echo done > "$O/DONE"
