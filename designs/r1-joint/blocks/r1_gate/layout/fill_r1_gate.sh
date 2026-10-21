#!/usr/bin/env bash
# Add the PDK fill to r1_gate_<variant>.gds, writing r1_gate_<variant>_filled.gds (the GDS of record).
# Inside the pinned container, from the repository root:
#   G1_WORKDIR=designs/r1-joint/blocks/r1_gate/layout flow/run.sh bash fill_r1_gate.sh hv   (or lv)
# Same method as the G1 fill.sh (copied, paths changed): fill_prep.py draws a temporary EdgeSeal 1 um inside the
# boundary, the PDK filler.py runs with default distances, fill_prep.py removes the EdgeSeal again.
# Scratch files go to /tmp (container-local); the log is written to fill_r1_gate_<variant>.log.
set -eu
V=$1
M=r1_gate_$V
HERE=$(cd "$(dirname "$0")" && pwd)
PREP=$HERE/fill_prep.py
B=/tmp/${M}_fill
mkdir -p $B
{
echo "# fill of $M, $(date -u +%FT%H:%MZ), klayout $(klayout -v | head -1), PDK $PDK_ROOT/$PDK"
klayout -b -r $PREP -rd mode=prep -rd gds=$HERE/$M.gds -rd cell=$M -rd out=$B/${M}_prep.gds -rd inset=1.0
klayout -n sg13g2 -zz -r $PDK_ROOT/$PDK/libs.tech/klayout/tech/scripts/filler.py -rd output_file=$B/${M}_filled_raw.gds $B/${M}_prep.gds
klayout -b -r $PREP -rd mode=clean -rd gds=$B/${M}_filled_raw.gds -rd cell=$M -rd out=$HERE/${M}_filled.gds
} 2>&1 | grep -v "^GRID\|EPSILON\|Success\|Technology SG13" | tee $HERE/fill_$M.log
