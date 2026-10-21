#!/bin/sh
# DRC (PDK sg13g2 deck, main + maximal rule tables, deep, density off: block level), antenna (PDK deck) and LVS
# (PDK deck, deep, --no_series_res) of r1_isense.gds against r1_isense_lvs.cdl (revision 2, unit split by
# r1_isense_netlist.py); pin check (check_pins.py). Adapted from the r1_afe run_checks.sh (track T3).
# Usage (repository root, host, POSIX sh):
#   G1_CPUSET=109-111; export G1_CPUSET; G1_RESULTS_ROOT=<bulk root>; export G1_RESULTS_ROOT
#   G1_WORKDIR=designs/r1-joint/blocks/r1_isense/layout; export G1_WORKDIR; flow/run.sh sh run_checks.sh <run-id> [drc|ant|lvs|pins|all]
# Outputs: $G1_RESULTS_ROOT/r1_isense/<run-id>/{drc,antenna,lvs}; logs (machine paths replaced), the LVS summary,
# the DRC marker count per rule and run.json in ../reports/<run-id>/
set -eu
RID=$1; WHAT=${2:-all}
OUTD=$G1_RESULTS_ROOT/r1_isense/$RID
REP=../reports/$RID
mkdir -p $OUTD $REP
T=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
GDS=$(pwd)/r1_isense.gds
if [ "$WHAT" = all ] || [ "$WHAT" = drc ]; then
  python3 $T/drc/run_drc.py --path=$GDS --topcell=r1_isense --run_mode=deep --no_density --run_dir=$OUTD/drc > $OUTD/drc.log 2>&1 || true
  cp $OUTD/drc.log $REP/drc.log
fi
if [ "$WHAT" = all ] || [ "$WHAT" = ant ]; then
  python3 $T/drc/run_drc.py --path=$GDS --topcell=r1_isense --run_mode=deep --antenna_only --run_dir=$OUTD/antenna > $OUTD/antenna.log 2>&1 || true
  cp $OUTD/antenna.log $REP/antenna.log
fi
if [ "$WHAT" = all ] || [ "$WHAT" = lvs ]; then
  python3 $T/lvs/run_lvs.py --layout=$GDS --netlist=$(pwd)/r1_isense_lvs.cdl --topcell=r1_isense --run_mode=deep \
     --no_series_res --run_dir=$OUTD/lvs > $OUTD/lvs.log 2>&1 || true
  cp $OUTD/lvs.log $REP/lvs.log
  klayout -b -r tools/lvsdb_report.py -rd db=$OUTD/lvs/r1_isense.lvsdb > $REP/lvs_summary.txt 2>&1 || true
fi
if [ "$WHAT" = all ] || [ "$WHAT" = pins ]; then
  klayout -b -r check_pins.py -rd gds=$GDS -rd cdl=$(pwd)/r1_isense_lvs.cdl > $REP/pin_check.txt 2>&1 || true
fi
for f in $REP/*.log $REP/*.txt; do
  [ -f "$f" ] && sed -i -e "s#$G1_RESULTS_ROOT#<G1_RESULTS_ROOT>#g" -e "s#/work/#<repo>/#g" "$f"
done
python3 tools/write_runjson.py "$RID" "$WHAT" "$OUTD" "$REP"
