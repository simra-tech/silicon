#!/usr/bin/env bash
# Add the PDK fill to layout/g1_bgr.gds in place (Activ, GatPoly, Metal1-3; no Metal4/5 and no TopMetal, which the
# chip-level filler adds over the macro after routing). Run inside the pinned container from this directory:
#   G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/layout flow/run.sh bash fill_g1_bgr.sh
# after g1_bgr_layout.py has written the unfilled g1_bgr.gds (which carries the <layer>/23 no-fill regions).
set -euo pipefail
tmp=$(mktemp -d)
klayout -b -r fill_pre.py -rd src=g1_bgr.gds -rd dst=$tmp/g1_bgr_prefill.gds
klayout -b -zz -r $PDK_ROOT/$PDK/libs.tech/klayout/tech/scripts/filler.py -rd output_file=$tmp/g1_bgr_filled.gds \
    -rd no_topmetal $tmp/g1_bgr_prefill.gds
klayout -b -r fill_post.py -rd src=$tmp/g1_bgr_filled.gds -rd dst=g1_bgr.gds
rm -rf $tmp
