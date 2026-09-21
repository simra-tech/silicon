#!/usr/bin/env bash
# Fill a macro GDS with the PDK filler (Activ/GatPoly and Metal1-5; no TopMetal fill: the chip-level
# TopMetal1/2 power stripes cross the macros and the chip filler fills TopMetal after routing).
# Usage (inside the container, from the layout directory):  bash fill_macro.sh <in.gds> <out.gds> [inset_um]
# Temporary files go to /work/build/<block>/fill/.  See fill_macro.py for the EdgeSeal trick.
set -eu
in=$1; out=$2; inset=${3:-3.0}
B=/work/build/$(basename "$(cd .. && pwd)")/fill
mkdir -p $B
klayout -b -r fill_macro.py -rd mode=pre -rd gds=$in -rd out=$B/fillin.gds -rd inset=$inset 2>&1 | grep -v "^GRID\|^EPSILON\|^Success\|^Technology"
klayout -b -zz -r $PDK_ROOT/$PDK/libs.tech/klayout/tech/scripts/filler.py -rd output_file=$B/filled_raw.gds -rd no_topmetal $B/fillin.gds 2>&1 | grep -v "^GRID\|^EPSILON\|^Success\|^Technology" | tee $B/filler.log
klayout -b -r fill_macro.py -rd mode=post -rd gds=$B/filled_raw.gds -rd out=$out 2>&1 | grep -v "^GRID\|^EPSILON\|^Success\|^Technology"
