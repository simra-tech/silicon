#!/usr/bin/env python3
"""Build a device-free LVSDB for the top-interconnect view (the kpex LVS deck returns an
empty layout netlist for a layout without device-bearing circuits). Metal/via layers are
registered under the kpex ihp-sg13g2 LVS layer names so kpex maps them to the same GDS
pairs as in a normal run; labels (<layer>/25) name the nets. No schematic comparison."""
import sys, klayout.db as kdb
gds, out, topname = sys.argv[1], sys.argv[2], sys.argv[3]
ly = kdb.Layout(); ly.read(gds); top = ly.cell(topname)
lvs = kdb.LayoutVsSchematic(kdb.RecursiveShapeIterator(ly, top, []))
M = [('metal1', 8, 'metal1_con'), ('metal2', 10, 'metal2_con'), ('metal3', 30, 'metal3_con'), ('metal4', 50, 'metal4_con'),
     ('metal5', 67, 'metal5_n_cap'), ('topmetal1', 126, 'topmetal1_con'), ('topmetal2', 134, 'topmetal2_con')]
V = [(19, 'via1_drw', 8, 10), (29, 'via2_drw', 10, 30), (49, 'via3_drw', 30, 50), (66, 'via4_drw', 50, 67),
     (125, 'topvia1_n_cap', 67, 126), (133, 'topvia2_drw', 126, 134)]
R = {}
for base, l, name in M:
    R[l] = lvs.make_layer(ly.layer(l, 0), name); lvs.connect(R[l])
    t = lvs.make_text_layer(ly.layer(l, 25), base + '_text'); lvs.connect(R[l], t)
for l, name, lo, hi in V:
    v = lvs.make_layer(ly.layer(l, 0), name); lvs.connect(v); lvs.connect(v, R[lo]); lvs.connect(v, R[hi])
lvs.extract_netlist()
nl = lvs.netlist(); c = nl.circuit_by_name(topname)
named = sum(1 for n in c.each_net() if n.name)
print('nets', sum(1 for n in c.each_net()), 'named', named)
lvs.reference = kdb.Netlist()
lvs.write(out)
