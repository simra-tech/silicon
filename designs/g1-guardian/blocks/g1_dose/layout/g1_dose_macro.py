#!/usr/bin/env python3
"""G1_DOSE placeable macro `g1_dose_macro` (30 x 30 um) around the cell of record g1_dose_pair_pcell
(sg13_hv_nmos on D_ELT, sg13_lv_nmos on D_STD, shared gate, source/body on vss).

Pins (Metal3, LEF): G_SHARED, D_ELT, D_STD as 1.5 x 0.30 um stubs on the west edge (facing the west
pads 19-21), vss as a 30 x 2 um bar on the south edge. Fill on Activ/GatPoly/Metal1-3 outside a 5 um
no-fill margin around the device cell (see macro_common.py).

Run inside the pinned container (KLayout 0.30.9, PDK commit 8437402), from this directory:
  G1_WORKDIR=designs/g1-guardian/blocks/g1_dose/layout flow/run.sh klayout -b -r g1_dose_macro.py
Writes g1_dose_macro.gds, g1_dose_macro.lef, g1_dose_macro.vh, lef_check.tcl and
../reports/filler_g1_dose_macro.log.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from macro_common import Macro, lef_check_tcl

W = H = 30.0
m = Macro('g1_dose_macro', W, H, os.path.join(HERE, 'g1_dose_pcell.gds'), 'g1_dose_pair_pcell', dx=12.98, dy=12.61)
bb = m.dev_bbox()
print('device cell bbox in macro coordinates:', bb)

# D_ELT (HV drain): Metal2 stub at the device's west edge -> Via2 -> Metal3 straight west to the pin
xE, yE = m.dev_pin('D_ELT')
m.via2_stack(xE, yE); m.wire3(xE, yE, 0.75, yE); m.west_pin('D_ELT', yE, 'INOUT')
# G_SHARED: Metal2 gate strip between the devices -> Via2 -> Metal3 west
xG, yG = m.dev_pin('G_SHARED')
m.via2_stack(xG, yG); m.wire3(xG, yG, 0.75, yG); m.west_pin('G_SHARED', yG, 'INPUT')
# D_STD (LV drain): Metal2 stub at the east edge -> Via2 -> Metal3 north over the cell, then west
xS, yS = m.dev_pin('D_STD')
yTop = round(bb.top + 1.0, 3)
m.via2_stack(xS, yS); m.wire3(xS, yS, xS, yTop); m.wire3(xS, yTop, 0.75, yTop); m.west_pin('D_STD', yTop, 'INOUT')
# vss: Metal1 substrate ring of the LV device, south-east corner (ring centre lines from g1_dose_pcell_layout.py:
# ring_in = (3.08, -0.35, 4.64, 4.88), Metal1 centre 0.15 outside) -> Via1/Via2 stack -> Metal3 south to the bar
xV, yV = 4.79 + m.dx, -0.50 + m.dy
m.m1_to_m3(xV, yV); m.wire3(xV, yV, xV, 1.0); m.south_bar('vss')

# no-fill over the device cell with a 5 um margin (all fill layers + NoMetFiller), Metal3 no-fill over the
# pin-access bands (west stubs, south bar) so Metal3 fill stays inside the LEF Metal3 obstruction
m.nofill(bb.left - 5, bb.bottom - 5, bb.right + 5, bb.top + 5)
m.nofill(0, 0, 2.3, H, layers=[(30, 23)]); m.nofill(0, 0, W, 3.1, layers=[(30, 23)])
m.boundary()

os.makedirs(os.path.join(HERE, '..', 'reports'), exist_ok=True)
out = m.finish(HERE, os.path.join(HERE, '..', 'reports', 'filler_g1_dose_macro.log'))
m.write_lef(os.path.join(HERE, 'g1_dose_macro.lef'))
m.write_vh(os.path.join(HERE, 'g1_dose_macro.vh'),
           '// G1_DOSE black box for the chip flow (LibreLane MACROS entry, see ../../g1_padring/INTEGRATION.md).\n'
           '// Analog macro, no timing arcs. Pins are Metal3 stubs on the west edge (layout/g1_dose_macro.lef);\n'
           '// vss (source, body, p+ rings) is the Metal3 bar on the south edge. D_ELT carries the thick-oxide\n'
           '// sg13_hv_nmos drain, D_STD the sg13_lv_nmos drain; G_SHARED is the common gate (0 to 3.3 V from the pad).',
           {'vss': '      // substrate / source / body', 'G_SHARED': '  // shared gate, from pad 19',
            'D_STD': '     // LV NMOS drain, to pad 20', 'D_ELT': '     // HV NMOS drain, to pad 21 (pad name kept from the ELT variant)'})
lef_check_tcl(os.path.join(HERE, 'g1_dose_macro.lef'), os.path.join(HERE, 'lef_check.tcl'))
print('wrote', out, 'pins:', [(p[0], p[1], p[2], p[3], p[4]) for p in m.pins], 'fill shapes:', m.fill_counts)
