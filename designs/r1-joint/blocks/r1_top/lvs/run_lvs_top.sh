#!/bin/sh
# Chip-level LVS of the partial R1 assembly (track T8). POSIX sh, run from the repository root.
#   sh designs/r1-joint/blocks/r1_top/lvs/run_lvs_top.sh <gds> <cdl> <out_dir> stock|limits
# Needs G1_CPUSET and G1_RESULTS_ROOT exported. "limits" uses a run-time copy of the PDK LVS directory with
# two comparer search limits added after "align" (max_depth(8), max_branch_complexity(100)): the method of
# blocks/r1_safe/layout/run_checks.sh, because the stock deck crashes or leaves the r1_safe mux trees unresolved.
# No extraction or rule line is changed.
set -eu
G=$1; C=$2; X=$3; MODE=$4
PDKD=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
mkdir -p "$X"
if [ "$MODE" = limits ]; then
  mkdir -p "$X/deck/p/libs.tech/klayout/tech"
  flow/run.sh sh -c "cp -r $PDKD/lvs $X/deck/p/libs.tech/klayout/tech/ && cp /foss/pdks/versions.txt $X/deck/"
  sed -i 's/^  align$/  align\n  max_depth(8)\n  max_branch_complexity(100)/' "$X/deck/p/libs.tech/klayout/tech/lvs/sg13g2.lvs"
  grep -n "max_depth\|max_branch" "$X/deck/p/libs.tech/klayout/tech/lvs/sg13g2.lvs" > "$X/deck_diff.txt"
  RUN="$X/deck/p/libs.tech/klayout/tech/lvs/run_lvs.py"
else
  RUN="$PDKD/lvs/run_lvs.py"
fi
date -u +%Y-%m-%dT%H:%M:%SZ > "$X/start.txt"
set +e
flow/run.sh python3 "$RUN" --layout="$G" --netlist="$C" --topcell=r1_top --run_mode=deep \
  --run_dir="$X/out" > "$X/console.log" 2>&1
echo "exit $?" > "$X/exit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$X/end.txt"
