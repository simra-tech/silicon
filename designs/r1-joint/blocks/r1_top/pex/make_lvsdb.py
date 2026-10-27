# SPDX-License-Identifier: Apache-2.0
"""r1_top try g, chip-level extraction (track T11): KLayout LVS database of the wiring layout for kpex --lvsdb.

  python3 make_lvsdb.py <r1_top_wire.gds> <out.lvsdb>

Why: the PDK LVS deck that kpex runs on the wiring layout (no devices; macros black-boxed) writes a database with no
circuit (run kpex_full try 1 and try 2: "No extracted layers found"), so kpex gets no net geometry. This script
builds the same connectivity (Metal1-TopMetal2 and Via1-TopVia2, labels on <metal>/25) with KLayout LayoutVsSchematic
and the layer names of the PDK LVS deck that kpex maps (metal1_con ... topmetal2_con, via1_drw ... topvia2_drw), and
writes it for kpex --lvsdb. No device is extracted (there is none in the wiring layout).
"""
import sys

import klayout.db as db

GDS, OUT = sys.argv[1], sys.argv[2]
ly = db.Layout()
ly.read(GDS)
top = ly.cell("r1_top_wire")
lvs = db.LayoutVsSchematic(db.RecursiveShapeIterator(ly, top, []))
MET = [("metal1_con", 8), ("metal2_con", 10), ("metal3_con", 30), ("metal4_con", 50), ("metal5_n_cap", 67),
       ("topmetal1_con", 126), ("topmetal2_con", 134)]
VIA = [("via1_drw", 19, 0, 1), ("via2_drw", 29, 1, 2), ("via3_drw", 49, 2, 3), ("via4_drw", 66, 3, 4),
       ("topvia1_n_cap", 125, 4, 5), ("topvia2_drw", 133, 5, 6)]
TXT = {8: "metal1_text", 10: "metal2_text", 30: "metal3_text", 50: "metal4_text", 67: "metal5_text",
       126: "topmetal1_text", 134: "topmetal2_text"}
M = []
for nm, l in MET:
    r = lvs.make_layer(ly.layer(l, 0), nm)
    M.append(r)
    lvs.connect(r)
    t = lvs.make_text_layer(ly.layer(l, 25), TXT[l])
    lvs.connect(r, t)
for nm, l, a, b in VIA:
    v = lvs.make_layer(ly.layer(l, 0), nm)
    lvs.connect(v)
    lvs.connect(M[a], v)
    lvs.connect(v, M[b])
lvs.extract_netlist()
nl = lvs.netlist()
c = nl.circuit_by_name("r1_top_wire")
named = sum(1 for n in c.each_net() if n.name)
print("circuit", c.name, "nets", sum(1 for n in c.each_net()), "named", named)
lvs.write(OUT)
print("wrote", OUT)
