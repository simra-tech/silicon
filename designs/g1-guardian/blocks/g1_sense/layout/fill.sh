#!/usr/bin/env bash
# Fill a G1 analog macro with the PDK filler (Activ/GatPoly, Metal1-5, TopMetal1/2) inside its boundary.
# Usage (repo root):  G1_WORKDIR=designs/g1-guardian/blocks/<block>/layout flow/run.sh bash ../../g1_sense/layout/fill.sh <macro>
#   reads  <macro>.gds (top cell <macro>, boundary on 189/4, no-fill regions on datatype 23 / NoMetFiller)
#   writes <macro>_filled.gds and fill_<macro>.log ; intermediate files under build/<macro>_fill/
# The PDK filler macros only fill inside an EdgeSeal ring, so fill_prep.py adds a temporary one 1 um
# inside the boundary and removes it again from the result (no EdgeSeal remains in the macro).
set -eu
M=$1
PREP=$(dirname "$0")/fill_prep.py
B=../../../../../build/${M}_fill
mkdir -p $B
{
echo "# fill of $M, $(date -u +%FT%H:%MZ), klayout $(klayout -v | head -1), PDK $PDK_ROOT/$PDK"
klayout -b -r $PREP -rd mode=prep -rd gds=$M.gds -rd cell=$M -rd out=$B/${M}_prep.gds -rd inset=1.0
klayout -n sg13g2 -zz -r $PDK_ROOT/$PDK/libs.tech/klayout/tech/scripts/filler.py -rd output_file=$B/${M}_filled_raw.gds $B/${M}_prep.gds
klayout -b -r $PREP -rd mode=clean -rd gds=$B/${M}_filled_raw.gds -rd cell=$M -rd out=${M}_filled.gds
} 2>&1 | grep -v "^GRID\|EPSILON\|Success\|Technology SG13" | tee fill_$M.log
