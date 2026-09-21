#!/usr/bin/env python3
"""G1_DUT placeable macro `g1_dut_macro` (34 x 34 um) around the cell of record g1_dut (one npn13G2).

Pins (Metal3, LEF): HBT_B, HBT_C, HBT_E as 1.5 x 0.30 um stubs on the west edge (facing the west pads
22-24), vss (the PCell's p+ substrate ring) as a 34 x 2 um bar on the south edge. Fill on
Activ/GatPoly/Metal1-3 outside a 5 um no-fill margin around the device cell. The wrapper code is
../../g1_dose/layout/macro_common.py.

Run inside the pinned container (KLayout 0.30.9, PDK commit 8437402), from this directory:
  G1_WORKDIR=designs/g1-guardian/blocks/g1_dut/layout flow/run.sh klayout -b -r g1_dut_macro.py
Writes g1_dut_macro.gds, g1_dut_macro.lef, g1_dut_macro.vh, lef_check.tcl and
../reports/filler_g1_dut_macro.log.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'g1_dose', 'layout'))
from macro_common import Macro, lef_check_tcl

# 34 x 34 um: the smallest size at which the PDK filler's tile grid (Activ 5 um, Metal3 3 um, Metal1/2 2.5 um,
# anchored at the origin) places fill on all five obstructed layers around the 5 um no-fill margin
# (30 x 30 gave Metal1/Metal2 fill only). Device cell bbox (-3.35,-5.5)-(5.5,5.5) centred in the macro.
W = H = 34.0
m = Macro('g1_dut_macro', W, H, os.path.join(HERE, 'g1_dut.gds'), 'g1_dut', dx=round(W / 2 - 1.075, 3), dy=round(H / 2, 3))
bb = m.dev_bbox()
print('device cell bbox in macro coordinates:', bb)

# HBT_C: Metal2 pad north of the device -> Via2 -> Metal3 west
xC, yC = m.dev_pin('HBT_C')
m.via2_stack(xC, yC); m.wire3(xC, yC, 0.75, yC); m.west_pin('HBT_C', yC, 'INOUT')
# HBT_B: Metal2 pad south of the device -> Via2 -> Metal3 west
xB, yB = m.dev_pin('HBT_B')
m.via2_stack(xB, yB); m.wire3(xB, yB, 0.75, yB); m.west_pin('HBT_B', yB, 'INOUT')
# HBT_E: Metal2 pad east of the device -> Via2 -> Metal3 north over the cell, then west
xE, yE = m.dev_pin('HBT_E')
yTop = round(bb.top + 1.0, 3)
m.via2_stack(xE, yE); m.wire3(xE, yE, xE, yTop); m.wire3(xE, yTop, 0.75, yTop); m.west_pin('HBT_E', yTop, 'INOUT')
# vss: the PCell's p+ ring Metal1 (centre lines x = +-2.90, y = -2.88 / +3.33 in g1_dut_layout.py), SE corner
xV, yV = 2.90 + m.dx, -2.88 + m.dy
m.m1_to_m3(xV, yV); m.wire3(xV, yV, xV, 1.0); m.south_bar('vss')

m.nofill(bb.left - 5, bb.bottom - 5, bb.right + 5, bb.top + 5)
m.nofill(0, 0, 2.3, H, layers=[(30, 23)]); m.nofill(0, 0, W, 3.1, layers=[(30, 23)])
m.boundary()

os.makedirs(os.path.join(HERE, '..', 'reports'), exist_ok=True)
out = m.finish(HERE, os.path.join(HERE, '..', 'reports', 'filler_g1_dut_macro.log'))
m.write_lef(os.path.join(HERE, 'g1_dut_macro.lef'))
m.write_vh(os.path.join(HERE, 'g1_dut_macro.vh'),
           '// G1_DUT black box for the chip flow (LibreLane MACROS entry, see ../../g1_padring/INTEGRATION.md).\n'
           '// Analog macro, no timing arcs: one npn13G2 (Nx=1) with all three terminals on Metal3 stubs on the\n'
           '// west edge (layout/g1_dut_macro.lef); vss (p+ substrate ring) is the Metal3 bar on the south edge.',
           {'vss': '   // substrate ring', 'HBT_C': ' // collector, to pad 24', 'HBT_B': ' // base, to pad 23', 'HBT_E': ' // emitter, to pad 22'})
lef_check_tcl(os.path.join(HERE, 'g1_dut_macro.lef'), os.path.join(HERE, 'lef_check.tcl'))
print('wrote', out, 'pins:', [(p[0], p[1], p[2], p[3], p[4]) for p in m.pins], 'fill shapes:', m.fill_counts)
