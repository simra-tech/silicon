#!/usr/bin/env python3
"""Remove orphan top cells (device abstracts with no parent, e.g. 'D$sg13_hv_pmos$33') from an
LVSDB's internal layout so kpex's top_cell() lookup is unambiguous. The netlist, the
real top cell and every instanced cell are left unchanged; removed cells are reported."""
import sys, json, klayout.db as kdb
src, dst, top = sys.argv[1], sys.argv[2], sys.argv[3]
l = kdb.LayoutVsSchematic(); l.read(src)
ly = l.internal_layout()
tops = [c for c in ly.top_cells() if c.name != top]
rep = [dict(name=c.name, shapes=sum(c.shapes(li).size() for li in ly.layer_indices())) for c in tops]
for c in tops: ly.delete_cell(c.cell_index())
l.write(dst)
print(json.dumps(dict(removed=rep, remaining_tops=[c.name for c in ly.top_cells()])))
