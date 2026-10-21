#!/usr/bin/env python3
"""Run kpex (klayout_pex 0.3.12) with one runtime patch; arguments as for kpex. Run in the pinned container:
  flow/run.sh python3 designs/r1-joint/blocks/r1_safe/layout/kpex_wrap.py --pdk ihp_sg13g2 --gds ... --2.5D --mode CC ...
Why: the PDK LVS drops devices with all terminals on one net (layout dummies) but leaves their device cells in the
LVS internal layout as extra top cells, and KLayoutExtractionContext.top_cell_bbox calls Layout.top_cell(), which
fails with several top cells. The patch takes the bbox of the LVS internal top cell (the extracted cell) instead.
Nothing else is changed; the installed package is not modified."""
import sys
import klayout.db as kdb
import klayout_pex.klayout.lvsdb_extractor as le


def top_cell_bbox(self):
    b2 = self.lvsdb.internal_top_cell().bbox()
    try:
        b1 = self.annotated_layout.top_cell().bbox()
    except RuntimeError:
        b1 = kdb.Box()
    return b1 if b1.area() > b2.area() else b2


le.KLayoutExtractionContext.top_cell_bbox = top_cell_bbox
from klayout_pex.__main__ import main  # noqa: E402
sys.argv[0] = 'kpex'
sys.exit(main())
