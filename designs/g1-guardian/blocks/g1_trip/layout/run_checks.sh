#!/usr/bin/env bash
# Regenerate the G1_TRIP layout (generator, then the PDK metal/active fill by fill_macro.sh), run the PDK
# DRC (full rule set, deep, no density), LVS and the antenna deck.
# Usage (repo root): G1_WORKDIR=designs/g1-guardian/blocks/g1_trip/layout flow/run.sh bash run_checks.sh [gen|drc|lvs|ant|all]
set -u
what=${1:-all}
PM="isense:ISENSE,vref:VREF,cmp_clk:clk,vdd:VDD,vdda:IOVDD,vss:VSS"
for b in 0 1 2 3 4 5 6 7; do PM="$PM,soft$b:dac_soft[$b],hard$b:dac_hard[$b]"; done
if [ "$what" = gen ] || [ "$what" = all ]; then
  mkdir -p /work/build/g1_trip/lay ../reports/fill
  klayout -b -r gen_trip_layout.py -rd what=top -rd out=/work/build/g1_trip/lay/g1_trip_nofill.gds 2>&1 | grep -v "^GRID\|^EPSILON\|^Success\|^Technology" || true
  cp /work/build/g1_trip/lay/g1_trip_nofill.lef g1_trip.lef
  bash fill_macro.sh /work/build/g1_trip/lay/g1_trip_nofill.gds g1_trip.gds 3.0
  cp /work/build/g1_trip/fill/filler.log ../reports/fill/filler.log
  ls -la *.gds
  python3 lvs_netlist.py ../sim/netlist/g1_trip.spice g1_trip_lvs.cdl top=g1_trip "portmap=$PM"
fi
if [ "$what" = drc ] || [ "$what" = all ]; then
  rm -rf ../reports/drc
  python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/drc/run_drc.py --path=g1_trip.gds --topcell=g1_trip --run_mode=deep --no_density --run_dir=../reports/drc 2>&1 | tail -3
fi
if [ "$what" = lvs ] || [ "$what" = all ]; then
  rm -rf ../reports/lvs
  python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/lvs/run_lvs.py --layout=g1_trip.gds --netlist=g1_trip_lvs.cdl --topcell=g1_trip --run_mode=deep --run_dir=../reports/lvs 2>&1 | grep -E "Status|Outcome|Errors|Warnings"
  # the DAC cell alone without the series-resistor combiner: every tap node of the 530-unit string is
  # compared (the combiner would merge resistors through nodes that only reach switches)
  rm -rf ../reports/lvs_dac_noseries
  python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/lvs/run_lvs.py --layout=g1_trip.gds --netlist=g1_trip_lvs.cdl --topcell=g1_dac8 --run_mode=deep --no_series_res --run_dir=../reports/lvs_dac_noseries 2>&1 | grep -E "Status|Outcome|Errors|Warnings"
  echo "g1_dac8 extracted devices: $(grep -c '^R' ../reports/lvs_dac_noseries/g1_trip_extracted.cir) resistors, $(grep -c '^M' ../reports/lvs_dac_noseries/g1_trip_extracted.cir) MOS"
fi
if [ "$what" = ant ] || [ "$what" = all ]; then
  rm -rf ../reports/antenna
  python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/drc/run_drc.py --path=g1_trip.gds --topcell=g1_trip --run_mode=deep --antenna_only --run_dir=../reports/antenna 2>&1 | tail -3
fi
