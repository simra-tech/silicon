#!/bin/sh
# usage (container, G1_WORKDIR = r1_ctrl block dir): sta_adcmin.sh <ll-run> <out-run-id> <adc min input delay ns>
set -u
RUN=$G1_RESULTS_ROOT/r1_ctrl/$1/flow/runs/$1; export RUN; O=$G1_RESULTS_ROOT/r1_ctrl/$2
[ -e "$O" ] && { echo "$O exists"; exit 1; }
mkdir -p "$O"; ADCMIN=$3; export ADCMIN
sha256sum $RUN/final/nl/r1_ctrl_top.nl.v $RUN/final/spef/nom/r1_ctrl_top.nom.spef flow/r1_ctrl.sdc sim/signoff/sta_adcmin.tcl > "$O/inputs.sha256"
for c in typ_1p20V_25C fast_1p32V_m40C slow_1p08V_125C; do
  CORNER=nom_$c; export CORNER; LIBNAME=$c; export LIBNAME
  sta -no_splash -exit sim/signoff/sta_adcmin.tcl > "$O/hold_adcmin_$c.rpt" 2>&1
done
echo done > "$O/DONE"
