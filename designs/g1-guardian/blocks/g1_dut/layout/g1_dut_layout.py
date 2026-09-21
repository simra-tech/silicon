#!/usr/bin/env python3
"""G1_DUT layout: one npn13G2 PCell (Nx=1, default emitter 0.07 x 0.90 um) with
Metal2 terminals HBT_E, HBT_B, HBT_C and the PCell's own p+ substrate ring
contacted on Metal1 as VSS.

Run inside the pinned container (KLayout 0.30.9, PDK commit 8437402):
  G1_WORKDIR=designs/g1-guardian/blocks/g1_dut/layout flow/run.sh klayout -b -r g1_dut_layout.py
Writes g1_dut.gds (top cell g1_dut) next to this script.

The PCell geometry used below was read from the instantiated cell (see README):
  C  Metal1 pad  (-0.925..0.925, 1.010..1.250)
  B  Metal1 pad  (-0.975..0.975, -1.260..-1.020)
  E  Metal2 pad  (-0.925..0.925, -0.785..0.770)
  p+ ring Activ  outer (-3.15..3.15, -3.13..3.58), inner (-2.65..2.65, -2.63..3.08)
"""
import sys, os
K = '/foss/pdks/ihp-sg13g2/libs.tech/klayout/python'
for p in [K, K + '/pycell4klayout-api/source/python']:
    sys.path.insert(0, p)
import pya
import sg13g2_pycell_lib  # registers library SG13_dev (technology sg13g2)

lib = pya.Library.library_by_name('SG13_dev', 'sg13g2')
ly = pya.Layout()
ly.dbu = 0.001
L = {n: ly.layer(*v) for n, v in {
    'Activ': (1, 0), 'GatPoly': (5, 0), 'Cont': (6, 0), 'M1': (8, 0), 'M1pin': (8, 2), 'M1txt': (8, 25),
    'M2': (10, 0), 'M2pin': (10, 2), 'M2txt': (10, 25), 'Via1': (19, 0), 'pSD': (14, 0)}.items()}

def um(v):
    return int(round(v * 1000))

def box(cell, layer, x1, y1, x2, y2):
    cell.shapes(L[layer]).insert(pya.Box(um(x1), um(y1), um(x2), um(y2)))

def square(cell, layer, cx, cy, size):
    box(cell, layer, cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2)

def label(cell, layer, x, y, text):
    t = pya.Text(text, pya.Trans(pya.Point(um(x), um(y))))
    t.size = um(0.2)
    cell.shapes(L[layer]).insert(t)

top = ly.create_cell('g1_dut')

# --- the HBT PCell, Nx = 1 (emitter 0.07 x 0.90 um^2)
pcv = lib.layout().add_pcell_variant(lib.layout().pcell_id('npn13G2'), {'Nx': 1})
hbt = ly.cell(ly.add_lib_cell(lib, pcv))
top.insert(pya.CellInstArray(hbt.cell_index(), pya.Trans()))

# --- contacts and Metal1 on the PCell's p+ substrate ring (ring centre lines x=+-2.90, y=-2.88 / +3.33)
CONT, PITCH = 0.16, 0.34
def cont_row(x1, x2, y):
    n = int((x2 - x1 - CONT) // PITCH) + 1
    x0 = (x1 + x2) / 2 - (n - 1) * PITCH / 2
    for i in range(n):
        square(top, 'Cont', x0 + i * PITCH, y, CONT)
def cont_col(y1, y2, x):
    n = int((y2 - y1 - CONT) // PITCH) + 1
    y0 = (y1 + y2) / 2 - (n - 1) * PITCH / 2
    for i in range(n):
        square(top, 'Cont', x, y0 + i * PITCH, CONT)
xl, xr, yb, yt = -2.90, 2.90, -2.88, 3.33
cont_row(-2.75, 2.75, yb); cont_row(-2.75, 2.75, yt)
cont_col(-2.60, 3.05, xl); cont_col(-2.60, 3.05, xr)
hw = 0.13  # Metal1 ring half-width (0.26 wide: 0.05 enclosure of the 0.16 contact)
box(top, 'M1', xl - hw, yb - hw, xr + hw, yb + hw)
box(top, 'M1', xl - hw, yt - hw, xr + hw, yt + hw)
box(top, 'M1', xl - hw, yb - hw, xl + hw, yt + hw)
box(top, 'M1', xr - hw, yb - hw, xr + hw, yt + hw)
label(top, 'M1txt', xr, 0.0, 'VSS')
box(top, 'M1pin', xr - hw, -0.5, xr + hw, 0.5)

# --- collector: widen the Metal1 pad to 0.29 um so Via1 has 0.05 enclosure, Via1 x4, Metal2 up to a terminal
box(top, 'M1', -0.925, 1.010, 0.925, 1.300)
for cx in (-0.675, -0.225, 0.225, 0.675):
    square(top, 'Via1', cx, 1.155, 0.19)
box(top, 'M2', -0.925, 1.010, 0.925, 1.300)
box(top, 'M2', -0.15, 1.010, 0.15, 4.50)
box(top, 'M2', -0.5, 4.50, 0.5, 5.50); box(top, 'M2pin', -0.5, 4.50, 0.5, 5.50); label(top, 'M2txt', 0, 5.0, 'HBT_C')

# --- base: same, downwards
# (Metal2 pad kept 0.27 um below the emitter Metal2 pad: rule M2.e asks 0.24 um between wide parallel lines)
box(top, 'M1', -0.975, -1.350, 0.975, -1.020)
for cx in (-0.675, -0.225, 0.225, 0.675):
    square(top, 'Via1', cx, -1.200, 0.19)
box(top, 'M2', -0.975, -1.350, 0.975, -1.055)
box(top, 'M2', -0.15, -4.50, 0.15, -1.055)
box(top, 'M2', -0.5, -5.50, 0.5, -4.50); box(top, 'M2pin', -0.5, -5.50, 0.5, -4.50); label(top, 'M2txt', 0, -5.0, 'HBT_B')

# --- emitter: already on Metal2, strip to the right
box(top, 'M2', 0.90, -0.15, 4.50, 0.15)
box(top, 'M2', 4.50, -0.5, 5.50, 0.5); box(top, 'M2pin', 4.50, -0.5, 5.50, 0.5); label(top, 'M2txt', 5.0, 0, 'HBT_E')

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'g1_dut.gds')
ly.write(out)
print('wrote', out, 'top bbox', top.dbbox())
