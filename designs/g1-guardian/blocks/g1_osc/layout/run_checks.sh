#!/usr/bin/env bash
# Regenerate the G1_OSC layout (generator, then the PDK metal/active fill by fill_macro.sh), run the PDK
# DRC (full rule set, deep, no density), LVS and the antenna deck.
# Usage (repo root): G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh bash run_checks.sh [gen|drc|lvs|ant|all]
set -u
what=${1:-all}
PM="vdd:VDD,vss:VSS,trim0:trim[0],trim1:trim[1],trim2:trim[2],trim3:trim[3]"
if [ "$what" = gen ] || [ "$what" = all ]; then
  mkdir -p /work/build/g1_osc/lay
  klayout -b -r gen_osc_layout.py -rd out=/work/build/g1_osc/lay/g1_osc_nofill.gds 2>&1 | grep -v "^GRID\|^EPSILON\|^Success\|^Technology" || true
  cp /work/build/g1_osc/lay/g1_osc_nofill.lef g1_osc.lef
  cp /work/build/g1_osc/lay/g1_osc_nofill_pexlabels.txt g1_osc_pexlabels.txt
  bash fill_macro.sh /work/build/g1_osc/lay/g1_osc_nofill.gds g1_osc.gds 3.0
  cp /work/build/g1_osc/fill/filler.log ../reports/fill/filler.log 2>/dev/null || { mkdir -p ../reports/fill; cp /work/build/g1_osc/fill/filler.log ../reports/fill/filler.log; }
  ls -la *.gds
  python3 lvs_netlist.py ../sim/netlist/g1_osc.spice g1_osc_lvs.cdl top=g1_osc "portmap=$PM"
fi
if [ "$what" = drc ] || [ "$what" = all ]; then
  rm -rf ../reports/drc
  python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/drc/run_drc.py --path=g1_osc.gds --topcell=g1_osc --run_mode=deep --no_density --run_dir=../reports/drc 2>&1 | tail -3
fi
if [ "$what" = lvs ] || [ "$what" = all ]; then
  rm -rf ../reports/lvs
  python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/lvs/run_lvs.py --layout=g1_osc.gds --netlist=g1_osc_lvs.cdl --topcell=g1_osc --run_mode=deep --run_dir=../reports/lvs 2>&1 | grep -E "Status|Outcome|Errors|Warnings"
fi
if [ "$what" = ant ] || [ "$what" = all ]; then
  rm -rf ../reports/antenna
  python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/drc/run_drc.py --path=g1_osc.gds --topcell=g1_osc --run_mode=deep --antenna_only --run_dir=../reports/antenna 2>&1 | tail -3
fi
