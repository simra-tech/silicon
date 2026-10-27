# SPDX-License-Identifier: Apache-2.0
"""T11 probe: hierarchy, layers and labels of the try-g GDS (development aid). klayout -b -r probe_g3.py -rd g=<gds>"""
import klayout.db as db
from collections import Counter
ly = db.Layout(); ly.read(g)  # noqa: F821
top = ly.cell("r1_top")
print("top cells", [c.name for c in ly.top_cells()])
print("top", top.name, "cells", ly.cells(), "dbu", ly.dbu)
ch = Counter()
for inst in top.each_inst():
    ch[inst.cell.name] += 1
print("top instances", dict(ch))
for li in ly.layer_indexes():
    info = ly.get_info(li)
    n = top.shapes(li).size()
    if n:
        texts = [s.text_string for s in top.shapes(li).each() if s.is_text()]
        print("top layer", info, "shapes", n, "texts", len(texts), texts[:12])
for name in ("r1_ctrl_top", "r1_adc", "r1_afe", "r1_padring", "sg13g2_IOPadIn", "sg13g2_IOPadAnalog", "r1_bias", "r1_ls"):
    c = ly.cell(name)
    if c is None:
        print("no cell", name); continue
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        texts = [s.text_string for s in c.shapes(li).each() if s.is_text()]
        if texts:
            print(name, info, len(texts), texts[:10])
    print(name, "child cells", Counter(i.cell.name for i in c.each_inst()).most_common(8))
