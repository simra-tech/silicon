#!/usr/bin/env bash
# Add the PDK fill to layout/g1_t2f.gds in place (revision 2). Inside the pinned container, from the repository root:
#   G1_WORKDIR=designs/g1-guardian/blocks/g1_t2f/layout flow/run.sh bash fill_g1_t2f.sh
# The three PDK filler macros (libs.tech/klayout/tech/macros/sg13g2_filler_{ActGatP,Metal,TopMetal}.lym, run by
# libs.tech/klayout/tech/scripts/filler.py) fill only inside EdgeSeal.holes, i.e. the interior of a seal ring. A block
# has none, so fill_frame.py adds a temporary EdgeSeal (39/0) frame whose hole is the macro boundary inset by 1 um
# (block fill stays 1 um inside the boundary), filler.py runs with the PDK's default distances, and fill_frame.py
# --strip removes the frame again. The no-fill shapes (<layer>/23, 160/0) drawn by g1_t2f_layout.py stay in the GDS so
# that the chip-level filler honours them too. Scratch files go to build/g1_t2f_fill/.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
B=/work/build/g1_t2f_fill
mkdir -p $B
klayout -b -r $HERE/fill_frame.py -rd src=$HERE/g1_t2f.gds -rd dst=$B/g1_t2f_frame.gds
klayout -n sg13g2 -zz -r $PDK_ROOT/$PDK/libs.tech/klayout/tech/scripts/filler.py -rd output_file=$B/g1_t2f_filled_frame.gds $B/g1_t2f_frame.gds 2>&1 | tee $B/filler.log
klayout -b -r $HERE/fill_frame.py -rd src=$B/g1_t2f_filled_frame.gds -rd dst=$HERE/g1_t2f.gds -rd strip=1
