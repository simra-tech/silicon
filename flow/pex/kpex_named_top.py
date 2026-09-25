#!/usr/bin/env python3
"""Run kpex unchanged except for one runtime patch: KLayoutExtractionContext.top_cell_bbox
looks up the LVSDB internal layout's top cell by name (--cell) instead of Layout.top_cell(),
which raises when the LVSDB carries an unplaced device-abstract cell (seen on the G1 full
chip: 'D$sg13_hv_pmos$33'). The bbox only sizes the substrate halo region. No rule deck,
tech file or model is modified."""
import sys
import klayout.db as kdb
from klayout_pex.klayout import lvsdb_extractor as le
_cell = sys.argv[sys.argv.index('--cell') + 1]
def top_cell_bbox(self):
    b1 = self.annotated_layout.cell(_cell).bbox() if self.annotated_layout.cell(_cell) else self.annotated_layout.top_cell().bbox()
    b2 = self.lvsdb.internal_layout().cell(_cell).bbox()
    return b1 if b1.area() > b2.area() else b2
le.KLayoutExtractionContext.top_cell_bbox = top_cell_bbox
from klayout_pex.__main__ import main
sys.argv[0] = 'kpex'
sys.exit(main())
