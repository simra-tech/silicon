#!/bin/sh
# Sign-off of a revision-0.8 hardening run (inside the container, G1_WORKDIR = r1_ctrl block dir).
# usage: signoff08.sh <ll-run> <sta-run-id>
# Same steps as the 0.7 sign-off (<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_dev07/signoff07.sh): true setup/hold at typ/fast/slow
# with the sign-off SDC flow/r1_ctrl.sdc, fanout 8 / slew / cap per corner, the 128 pins against pins_v07.json, LibreLane report.
set -u
LL=$1; S=$G1_RESULTS_ROOT/r1_ctrl/$2
mkdir -p $S/tmpfo
LLRUN=$LL SDC=flow/r1_ctrl.sdc sh sim/signoff/sta_all.sh $S
for c in typ_1p20V_25C fast_1p32V_m40C slow_1p08V_125C; do
  LLRUN=$LL SDC=flow/r1_ctrl.sdc LIBNAME=$c TMPDIR_FO=$S/tmpfo FANOUT_TCL=sim/signoff/sta_fanout06.tcl sh sim/signoff/sta_fanout.sh $S/fanout_$c.rpt
done
F=$G1_RESULTS_ROOT/r1_ctrl/$LL/flow/runs/$LL/final
python3 flow/librelane/check_pins_v06.py $F/def/r1_ctrl_top.def flow/librelane/pins_v07.json > $S/pins_check.txt 2>&1
python3 flow/librelane/ll_report.py $G1_RESULTS_ROOT/r1_ctrl/$LL $LL $S/ll_report.md > /dev/null 2>&1
python3 flow/check_sdc_ports.py rtl/r1_ctrl_top.v flow/r1_ctrl.sdc $S/sdc_ports_signoff.json > $S/sdc_ports.log 2>&1
python3 flow/check_sdc_ports.py rtl/r1_ctrl_top.v flow/r1_ctrl_pnr6h.sdc $S/sdc_ports_pnr6h.json >> $S/sdc_ports.log 2>&1
echo done > $S/DONE
