#!/bin/sh
# Layout E6 (track T3j): DRC main + maximal, antenna, LVS (run_checks.sh), supply islands and pin check of one layout run.
# usage (host, repo root): G1_RESULTS_ROOT=<bulk>; export G1_RESULTS_ROOT; sh designs/r1-joint/blocks/r1_afe/layout/run_checks_e5.sh <layout run id>
set -u
RID=$1
cd "$(dirname "$0")/../../../../.."
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"; G1_CPUSET=${G1_CPUSET:-106-108}; G1_WORKDIR=designs/r1-joint/blocks/r1_afe/layout
export G1_RESULTS_ROOT G1_CPUSET G1_WORKDIR
O=$G1_RESULTS_ROOT/r1_afe/$RID; REP=designs/r1-joint/blocks/r1_afe/reports/$RID; mkdir -p $REP
flow/run.sh sh run_checks.sh $RID all $O/r1_afe.gds > $O/checks.out 2>&1; echo "checks rc $?" >> $O/checks.out
flow/run.sh klayout -b -r tools/supply_island_check.py -rd gds=$O/r1_afe.gds -rd ports=$O/r1_afe_ports.json 2>/dev/null > $REP/supply_island_check.json
flow/run.sh klayout -b -r tools/pin_layer_check.py -rd gds=$O/r1_afe.gds -rd ref=/work/designs/r1-joint/blocks/r1_afe/layout/r1_afe_revE5.gds 2>/dev/null > $REP/pin_layer_check.json
for f in $O/drc/*.lyrdb $O/antenna/*.lyrdb; do echo "$(basename $f) items $(grep -c '<item>' $f)"; done > $REP/drc_db_items.txt
echo done > $O/checks.done
