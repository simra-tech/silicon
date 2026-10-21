#!/usr/bin/env python3
"""Drawing helpers for the r1_safe layout (KLayout batch Python, PDK PCell library SG13_dev).

Copied in part from designs/g1-guardian/blocks/g1_trip/layout/g1_layout_lib.py (G1 is read-only; this is a copy).
Coordinates are in um; the database unit is 1 nm. PCells are flattened into the cell that places them.
"""
import sys

K = '/foss/pdks/ihp-sg13g2/libs.tech/klayout/python'
for p in [K, K + '/pycell4klayout-api/source/python']:
    if p not in sys.path:
        sys.path.insert(0, p)
import pya  # noqa: E402
import sg13g2_pycell_lib  # noqa: E402,F401  (registers library SG13_dev)

LIB = pya.Library.library_by_name('SG13_dev', 'sg13g2')
LAYERS = {
    'Activ': (1, 0), 'GatPoly': (5, 0), 'Cont': (6, 0), 'pSD': (14, 0), 'NWell': (31, 0), 'TGO': (44, 0),
    'M1': (8, 0), 'M1pin': (8, 2), 'M1txt': (8, 25), 'Via1': (19, 0),
    'M2': (10, 0), 'M2pin': (10, 2), 'M2txt': (10, 25), 'Via2': (29, 0),
    'M3': (30, 0), 'M3pin': (30, 2), 'M3txt': (30, 25), 'Via3': (49, 0),
    'M4': (50, 0), 'M4pin': (50, 2), 'M4txt': (50, 25),
    'SalBlock': (28, 0), 'ExtBlock': (111, 0), 'TEXT': (63, 0), 'prBoundary': (189, 4),
}
CONT, CP = 0.16, 0.34
VIA, VP = 0.19, 0.42


def um(v):
    return int(round(v * 1000))


class Draw:
    def __init__(self, ly, cell):
        self.ly, self.cell = ly, cell
        self.L = {n: ly.layer(*v) for n, v in LAYERS.items()}
        self.pins = []

    def box(self, layer, x1, y1, x2, y2):
        self.cell.shapes(self.L[layer]).insert(
            pya.Box(um(min(x1, x2)), um(min(y1, y2)), um(max(x1, x2)), um(max(y1, y2))))

    def sq(self, layer, cx, cy, s):
        self.box(layer, cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2)

    def rect(self, layer, cx, cy, w, h):
        self.box(layer, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)

    def label(self, layer, x, y, text, size=0.3):
        t = pya.Text(text, pya.Trans(pya.Point(um(x), um(y))))
        t.size = um(size)
        self.cell.shapes(self.L[layer]).insert(t)

    def pin(self, layer, x1, y1, x2, y2, name):
        self.box(layer, x1, y1, x2, y2)
        self.box(layer + 'pin', x1, y1, x2, y2)
        self.pins.append((name, layer, min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
        self.label(layer + 'txt', (x1 + x2) / 2, (y1 + y2) / 2, name)

    def cont(self, cx, cy):
        self.sq('Cont', cx, cy, CONT)

    def cont_row(self, x1, x2, y):
        n = int((x2 - x1 - CONT) / CP + 1e-6) + 1
        x0 = (x1 + x2) / 2 - (n - 1) * CP / 2
        for i in range(n):
            self.cont(x0 + i * CP, y)

    def cont_col(self, y1, y2, x):
        n = int((y2 - y1 - CONT) / CP + 1e-6) + 1
        y0 = (y1 + y2) / 2 - (n - 1) * CP / 2
        for i in range(n):
            self.cont(x, y0 + i * CP)

    # via with pads; lo/hi: 's' square 0.30, 'h' 0.30 x 0.20 (horizontal wire), 'v' 0.20 x 0.30, None no pad
    def via(self, kind, x, y, lo='s', hi='s'):
        lom, him = {'Via1': ('M1', 'M2'), 'Via2': ('M2', 'M3'), 'Via3': ('M3', 'M4')}[kind]
        self.sq(kind, x, y, VIA)
        for m, d in ((lom, lo), (him, hi)):
            if d is None:
                continue
            if d == 's':
                self.sq(m, x, y, 0.30)
            elif d == 'h':
                self.rect(m, x, y, 0.30, 0.20)
            elif d == 'v':
                self.rect(m, x, y, 0.20, 0.30)
            elif d == 't':   # track-width pad 0.30 x 0.24
                self.rect(m, x, y, 0.30, 0.24)

    def hw(self, layer, x1, x2, y, w=0.20):
        self.box(layer, min(x1, x2) - w / 2, y - w / 2, max(x1, x2) + w / 2, y + w / 2)

    def vw(self, layer, x, y1, y2, w=0.20):
        self.box(layer, x - w / 2, min(y1, y2) - w / 2, x + w / 2, max(y1, y2) + w / 2)

    def pcell(self, name, params, trans):
        pcv = LIB.layout().add_pcell_variant(LIB.layout().pcell_id(name), params)
        c = self.ly.cell(self.ly.add_lib_cell(LIB, pcv))
        inst = self.cell.insert(pya.CellInstArray(c.cell_index(), trans))
        inst.flatten()

    def clean(self):
        self.cell.shapes(self.L['TEXT']).clear()

    def ptap(self, x1, y1, x2, y2):
        """p+ substrate tie: Activ + pSD (0.03 larger), contacts along the long side, Metal1 over it"""
        self.box('Activ', x1, y1, x2, y2)
        self.box('pSD', x1 - 0.03, y1 - 0.03, x2 + 0.03, y2 + 0.03)
        self.box('M1', x1, y1, x2, y2)
        if x2 - x1 >= y2 - y1:
            self.cont_row(x1 + 0.07, x2 - 0.07, (y1 + y2) / 2)
        else:
            self.cont_col(y1 + 0.07, y2 - 0.07, (x1 + x2) / 2)

    def ntap(self, x1, y1, x2, y2):
        """n+ well tie (Activ inside an NWell drawn by the caller), contacts, Metal1"""
        self.box('Activ', x1, y1, x2, y2)
        self.box('M1', x1, y1, x2, y2)
        if x2 - x1 >= y2 - y1:
            self.cont_row(x1 + 0.07, x2 - 0.07, (y1 + y2) / 2)
        else:
            self.cont_col(y1 + 0.07, y2 - 0.07, (x1 + x2) / 2)


def T(x, y, rot=0, mirror=False):
    return pya.Trans(rot // 90, mirror, pya.Point(um(x), um(y)))


def place(parent, child, x, y, rot=0, mirror=False):
    parent.insert(pya.CellInstArray(child.cell_index(), T(x, y, rot, mirror)))


def write_gds(ly, path):
    for c in list(ly.each_cell()):
        if c.is_proxy() and c.parent_cells() == 0:
            ly.delete_cell(c.cell_index())
    ly.write(path)
