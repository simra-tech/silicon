#!/usr/bin/env python3
"""UNADOPTED CANDIDATE: 2x hold capacitors on a copy of the NF4 TRIP macro.

Input: the NF4 TRIP macro cut from the chip of record (g1_trip_nf4.gds, sha256 c8efefe3...d384, see
sim/postlayout/README.md). Output: the same macro plus one 26 x 26 um cmim PCell (PDK SG13_dev, flattened
into the top cell like the existing ones) under each existing hold capacitor, in parallel with it:
  CHS2 (vth_soft) MIM (97.5, 129.5)  - below CHS (97.5, 158.5), over the soft DAC top / DAC gap
  CHH2 (vth_hard) MIM (161.5, 129.5) - below CHH (162.5, 158.5), over the hard DAC top
  CH2  (icmp)     MIM (59.06, 129.5) - below CH (59.06, 163.0, inside g1_cond), over the soft DAC top
Sites: nearest 26 x 26 squares free of Metal5/TopMetal1/MIM/Via4/TopVia1 in the macro and in the chip
shapes over it (2.1 um margin), outside the two comparator boxes grown by 3 um and below the IOVDD/VDD bar
zone. None of the new squares lies over a comparator (the input pairs are untouched).
Connections (no other routing): the new top plate joins the existing top plate with a 3 um TopMetal1
bridge across the gap; the new Metal5 bottom plate joins the existing Metal5 bottom plate (VSS) with a
3 um Metal5 bridge; the bridges do not overlap each other. No-fill markers (Metal4/5, TopMetal1/2,
datatype 23) cover each new capacitor with its bridges, 4 um beyond Metal5 in x, as in gen_trip_layout.py.

  klayout -b -r gen_hold2x.py -rd src=<g1_trip_nf4.gds> -rd out=<g1_trip_nf4_hold2x.gds>
(run from this directory in the pinned container; imports ../../g1_layout_lib.py)
"""
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))
import pya  # noqa: E402
from g1_layout_lib import Draw, Cmim, NOFILL_UPPER  # noqa: E402

W = 26.0
NEW = [  # name, new MIM lower-left, existing MIM lower-left, TM1 bridge x, M5 bridge x
    ('CHS2', (97.5, 129.5), (97.5, 158.5), 100.0, 118.0),
    ('CHH2', (161.5, 129.5), (162.5, 158.5), 166.0, 182.0),
    ('CH2', (59.06, 129.5), (59.06, 163.0), 63.0, 79.0),
]

ly = pya.Layout()
ly.read(src)
top = ly.top_cell()
assert top.name == 'g1_trip'
D = Draw(ly, top)
n_text0 = top.shapes(D.L['TEXT']).size()
assert n_text0 == 0, 'input top cell has TEXT (63/0) shapes; clean_pcell_markers would remove them'
MAC = (0.0, 0.0, 229.0, 207.0)
for name, (x, y), (ex, ey), xt, xm in NEW:
    c = Cmim(D, W, W, x, y)
    top_new, bot_old = y + W, ey                 # new MIM top edge, existing MIM bottom edge
    D.box('TM1', xt, top_new - 0.6, xt + 3.0, bot_old + 0.6)           # top plates (tab rule as top_tab)
    D.box('M5', xm, top_new + 0.6 - 0.2, xm + 3.0, bot_old - 0.6 + 0.2)  # bottom plates (VSS)
    D.nofill(min(c.m5[0], ex - 0.6) - 4.0, c.m5[1], max(c.m5[2], ex + W + 0.6) + 4.0, bot_old + 0.6,
             margin=0.0, layers=NOFILL_UPPER, clip=MAC)
    print('added', name, 'MIM', c.mim)
D.clean_pcell_markers()
for cc in list(ly.each_cell()):
    if cc.is_proxy() and cc.parent_cells() == 0:
        ly.delete_cell(cc.cell_index())
ly.write(out)
print('wrote', out)
