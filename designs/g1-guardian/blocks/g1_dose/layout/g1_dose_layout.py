#!/usr/bin/env python3
"""G1_DOSE layout: a hand-drawn enclosed-layout (annular-gate) LV NMOS next to a
standard sg13_lv_nmos PCell of the same L and matched W, shared gate.

Run inside the pinned container (KLayout 0.30.9, PDK commit 8437402):
  G1_WORKDIR=designs/g1-guardian/blocks/g1_dose/layout flow/run.sh klayout -b -r g1_dose_layout.py
Writes g1_dose.gds (top cell g1_dose_pair) and g1_elt_l130_test.gds (L = 0.13 um
ring variant, DRC feasibility only) next to this script.

ELT geometry (all um): drain = inner Activ square of side d (one contact), gate =
closed GatPoly ring of width Lg, source = outer Activ ring of width s with a
contact ring, gate contact on a poly tab that leaves the ring across the source
ring to a pad on field oxide, p+ substrate ring (Activ + pSD, contacts, Metal1)
around the device. Drain and gate leave the cell on Metal2 so the source and
substrate Metal1 rings stay closed. Standard layers only: Activ 1/0, GatPoly 5/0,
Cont 6/0, Metal1 8/0, Via1 19/0, Metal2 10/0, pSD 14/0; no nSD, no ThickGateOx,
no PWell drawn (twin-well default, same as the nmos PCell).

Rule values used (DRC deck at PDK commit 8437402): Act.b 0.21, Act.c 0.23, Gat.a
0.13, Gat.c 0.18, Gat.d 0.07, Cnt.a 0.16, Cnt.b 0.18, Cnt.c/d 0.07, Cnt.e 0.14,
Cnt.f 0.11, Cnt.g2 0.09, M1.a 0.16, M1.b 0.18, M1.c1 0.05, V1.a 0.19, V1.b 0.22,
V1.c1 0.05, M2.a 0.20, M2.b 0.21, M2.e 0.24, pSD.a 0.31, pSD.c1 0.03, pSD.d 0.18.
"""
import sys, os
K = '/foss/pdks/ihp-sg13g2/libs.tech/klayout/python'
for p in [K, K + '/pycell4klayout-api/source/python']:
    sys.path.insert(0, p)
import pya
import sg13g2_pycell_lib  # registers library SG13_dev (technology sg13g2)

HERE = os.path.dirname(os.path.abspath(__file__))
lib = pya.Library.library_by_name('SG13_dev', 'sg13g2')
LAYERS = {'Activ': (1, 0), 'GatPoly': (5, 0), 'Cont': (6, 0), 'M1': (8, 0), 'M1pin': (8, 2), 'M1txt': (8, 25),
          'M2': (10, 0), 'M2pin': (10, 2), 'M2txt': (10, 25), 'Via1': (19, 0), 'pSD': (14, 0)}
CONT, CPITCH, VIA = 0.16, 0.34, 0.19

def um(v):
    return int(round(v * 1000))

class Draw:
    def __init__(self, ly, cell):
        self.ly, self.cell = ly, cell
        self.L = {n: ly.layer(*v) for n, v in LAYERS.items()}
    def box(self, layer, x1, y1, x2, y2):
        self.cell.shapes(self.L[layer]).insert(pya.Box(um(x1), um(y1), um(x2), um(y2)))
    def square(self, layer, cx, cy, size):
        self.box(layer, cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2)
    def ring(self, layer, x1, y1, x2, y2, w):
        """closed ring between the inner box (x1,y1,x2,y2) and the box grown by w"""
        outer = pya.Polygon(pya.Box(um(x1 - w), um(y1 - w), um(x2 + w), um(y2 + w)))
        outer.insert_hole(pya.Box(um(x1), um(y1), um(x2), um(y2)))
        self.cell.shapes(self.L[layer]).insert(outer)
    def label(self, layer, x, y, text):
        t = pya.Text(text, pya.Trans(pya.Point(um(x), um(y))))
        t.size = um(0.2)
        self.cell.shapes(self.L[layer]).insert(t)
    def cont_line(self, p1, p2, fixed, vertical, skip=lambda c: False):
        """contacts at pitch CPITCH along a line between p1 and p2 (centre coordinates)"""
        n = int(round((p2 - p1) / CPITCH)) + 1
        for i in range(n):
            c = p1 + i * CPITCH
            if skip(c):
                continue
            if vertical:
                self.square('Cont', fixed, c, CONT)
            else:
                self.square('Cont', c, fixed, CONT)
    def guard_ring(self, x1, y1, x2, y2, w=0.30):
        """p+ substrate ring: Activ ring of width w just outside the box, pSD 0.03 beyond, contacts, Metal1 ring"""
        self.ring('Activ', x1, y1, x2, y2, w)
        self.ring('pSD', x1 + 0.03, y1 + 0.03, x2 - 0.03, y2 - 0.03, w + 0.06)
        c = w / 2  # contact centre line offset outside the box
        cx1, cx2, cy1, cy2 = x1 - c, x2 + c, y1 - c, y2 + c
        for cy in (cy1, cy2):
            self.square('Cont', cx1, cy, CONT); self.square('Cont', cx2, cy, CONT)
        def side(a, b):
            span = b - a - CPITCH  # leave room next to the corner contacts
            n = int(span // CPITCH)
            if n < 1:
                return []
            start = (a + b) / 2 - (n - 1) * CPITCH / 2
            return [start + i * CPITCH for i in range(n)]
        for x in side(cx1, cx2):
            self.square('Cont', x, cy1, CONT); self.square('Cont', x, cy2, CONT)
        for y in side(cy1, cy2):
            self.square('Cont', cx1, y, CONT); self.square('Cont', cx2, y, CONT)
        hw = CONT / 2 + 0.05
        self.ring('M1', cx1 + hw, cy1 + hw, cx2 - hw, cy2 - hw, 2 * hw)
        return (cx1, cy1, cx2, cy2)  # Metal1 ring centre lines

def elt_nmos(d, Lg, s, cx, cy, tab_w=0.30, cell=None, name_suffix=''):
    """Draw one ELT NMOS centred at (cx, cy) into `cell`. Returns geometry dict.
    d: inner (drain) Activ side; Lg: gate ring width; s: source ring width."""
    D = Draw(cell.layout(), cell)
    A = d / 2 + Lg + s                  # Activ half-side
    gi, go = d / 2, d / 2 + Lg          # gate ring inner / outer half-side
    rc = go + 0.11 + CONT / 2           # source contact centre radius (Cnt.f 0.11 from the gate)
    assert A - (rc + CONT / 2) >= 0.07, 'source Activ enclosure of contact'
    assert d >= CONT + 2 * 0.11, 'drain contact needs Cnt.f on both sides'
    # Activ square, gate ring, drain contact
    D.box('Activ', cx - A, cy - A, cx + A, cy + A)
    D.ring('GatPoly', cx - gi, cy - gi, cx + gi, cy + gi, Lg)
    D.square('Cont', cx, cy, CONT)
    # gate tab to +x: poly from the ring across the source ring to a pad on field oxide
    cont_x = A + 0.14 + CONT / 2        # Cnt.e: contact on poly 0.14 from Activ
    tab_end = cont_x + CONT / 2 + 0.07  # Cnt.d poly enclosure
    D.box('GatPoly', cx + go, cy - tab_w / 2, cx + tab_end, cy + tab_w / 2)
    D.square('Cont', cx + cont_x, cy, CONT)
    D.box('M1', cx + cont_x - 0.15, cy - 0.15, cx + cont_x + 0.15, cy + 0.15)
    D.square('Via1', cx + cont_x, cy, VIA)
    # source contact ring: corners, then sides at pitch; on the tab side keep Cnt.f 0.11 to the tab poly
    for sx in (-1, 1):
        for sy in (-1, 1):
            D.square('Cont', cx + sx * rc, cy + sy * rc, CONT)
    span = 2 * rc - CPITCH
    n = int(span // CPITCH)
    if n >= 1:
        side_pos = [-(n - 1) * CPITCH / 2 + i * CPITCH for i in range(n)]
    else:
        side_pos = []
    clear = tab_w / 2 + 0.11 + CONT / 2
    for p in side_pos:
        D.square('Cont', cx + p, cy - rc, CONT); D.square('Cont', cx + p, cy + rc, CONT)
        D.square('Cont', cx - rc, cy + p, CONT)
        if abs(p) >= clear:
            D.square('Cont', cx + rc, cy + p, CONT)
    if not any(abs(p) >= clear for p in side_pos):
        # tab side too short for the regular pitch: place two contacts just clear of the tab if they fit
        pc = clear
        if pc + CONT / 2 + 0.18 <= rc - CONT / 2:
            D.square('Cont', cx + rc, cy + pc, CONT); D.square('Cont', cx + rc, cy - pc, CONT)
    # source Metal1 ring (0.26 wide over the contact ring)
    hw = CONT / 2 + 0.05
    D.ring('M1', cx - rc + hw, cy - rc + hw, cx + rc - hw, cy + rc - hw, 2 * hw)
    # drain: Metal1 pad, Via1, Metal2 strip leaving to -x
    D.box('M1', cx - 0.15, cy - 0.15, cx + 0.15, cy + 0.15)
    D.square('Via1', cx, cy, VIA)
    # p+ substrate ring
    Gi = max(A + 0.30, tab_end + 0.18)  # M1.b: ring Metal1 0.18 from the gate-pad Metal1
    g = D.guard_ring(cx - Gi, cy - Gi, cx + Gi, cy + Gi, 0.30)
    # Metal1 bridges source ring -> substrate ring on +-y (source and body both VSS)
    D.box('M1', cx - 0.13, cy + rc - hw, cx + 0.13, g[3] + hw)
    D.box('M1', cx - 0.13, g[1] - hw, cx + 0.13, cy - rc + hw)
    Go = Gi + 0.30
    # Metal2: drain strip to -x, gate strip to +x, both 0.30 wide, past the substrate ring
    D.box('M2', cx - Go - 0.60, cy - 0.15, cx + 0.15, cy + 0.15)
    D.box('M2', cx + cont_x - 0.15, cy - 0.15, cx + Go + 0.60, cy + 0.15)
    D.label('M1txt', cx, g[3], 'VSS')
    W_ext_expected = 4 * (d + Lg)      # mean of inner and outer gate-ring perimeters (square ring)
    return dict(A=A, gi=gi, go=go, rc=rc, tab_end=tab_end, Gi=Gi, Go=Go, cont_x=cont_x,
                W_mean_perimeter=W_ext_expected, drain_exit_x=cx - Go - 0.60, gate_exit_x=cx + Go + 0.60,
                m1_ring=g)

def build_pair(d=0.42, Lg=0.50, s=0.45, w_std=3.98):
    ly = pya.Layout(); ly.dbu = 0.001
    top = ly.create_cell('g1_dose_pair')
    D = Draw(ly, top)
    e = elt_nmos(d, Lg, s, 0.0, 0.0, cell=top)
    # standard device: nmos PCell w_std x Lg, single finger, placed so that its gate pad sits on the gate strip (y = 0)
    pcv = lib.layout().add_pcell_variant(lib.layout().pcell_id('nmos'),
                                         {'w': '%gu' % w_std, 'l': '%gu' % Lg, 'ng': 1})
    std = ly.cell(ly.add_lib_cell(lib, pcv))
    ox, oy = e['Go'] + 0.60 + 0.60, 0.40   # std ring (0.30 wide + 0.30 gap) starts 0.60 right of the ELT ring
    top.insert(pya.CellInstArray(std.cell_index(), pya.Trans(pya.Point(um(ox), um(oy)))))
    # PCell geometry (w=3.7, l=0.5): Activ (0,0)-(1.18,w); GatPoly x 0.34..0.84, y -0.18..w+0.18;
    # source Metal1 strip x 0.07..0.23, drain strip x 0.95..1.11, both y 0..w
    gx1, gx2 = ox + 0.34, ox + 0.84
    # gate contact pad below the PCell poly end cap
    D.box('GatPoly', gx1, oy - 0.62, gx2, oy - 0.18)
    D.square('Cont', ox + 0.59, oy - 0.40, CONT)
    D.box('M1', ox + 0.44, oy - 0.55, ox + 0.74, oy - 0.25)
    D.square('Via1', ox + 0.59, oy - 0.40, VIA)
    # shared gate on Metal2: ELT gate strip already ends at e['gate_exit_x']; continue it to the std gate pad
    D.box('M2', e['gate_exit_x'] - 0.30, -0.15, ox + 0.74, 0.15)
    # std drain: wider Metal1 over the PCell drain strip, Via1 column, Metal2 strip leaving to +x
    D.box('M1', ox + 0.90, oy + 0.30, ox + 1.20, oy + w_std - 0.30)
    for vy in (0.8, 1.5, 2.2, 2.9):
        D.square('Via1', ox + 1.05, oy + vy, VIA)
    D.box('M2', ox + 0.90, oy + 0.30, ox + 1.20, oy + w_std - 0.30)
    # std source: Metal1 strip down to the substrate ring
    ring_in = (ox - 0.30, oy - 0.75, ox + 1.48, oy + w_std + 0.35)  # pSD.j: pSD 0.30 from the gate
    g2 = D.guard_ring(*ring_in, 0.30)
    D.box('M1', ox + 0.07, g2[1], ox + 0.23, oy)
    D.box('M2', ox + 1.20, oy + 1.70, ring_in[2] + 0.30 + 0.60, oy + 2.00)
    # Metal1 bridge between the two substrate rings (one VSS net)
    D.box('M1', e['m1_ring'][2], 0.60, g2[0], 0.86)
    # terminals and labels
    D.box('M2pin', e['drain_exit_x'], -0.15, e['drain_exit_x'] + 0.30, 0.15); D.label('M2txt', e['drain_exit_x'] + 0.15, 0, 'D_ELT')
    gmid = (e['Go'] + g2[0] - 0.13) / 2
    D.box('M2pin', gmid - 0.15, -0.15, gmid + 0.15, 0.15); D.label('M2txt', gmid, 0, 'G_SHARED')
    dx = ring_in[2] + 0.30 + 0.60
    D.box('M2pin', dx - 0.30, oy + 1.70, dx, oy + 2.00); D.label('M2txt', dx - 0.15, oy + 1.85, 'D_STD')
    D.label('M1txt', ox + 0.59, g2[3], 'VSS')
    D.box('M1pin', ox + 0.46, g2[3] - 0.13, ox + 0.72, g2[3] + 0.13)
    out = os.path.join(HERE, 'g1_dose.gds')
    ly.write(out)
    print('wrote', out, 'bbox', top.dbbox())
    print('ELT: d=%.2f Lg=%.2f s=%.2f  Activ half %.2f, gate ring %.2f..%.2f, source cont radius %.2f, tab end %.2f, p+ ring inner %.2f'
          % (d, Lg, s, e['A'], e['gi'], e['go'], e['rc'], e['tab_end'], e['Gi']))
    print('ELT mean-perimeter W = 4(d+Lg) = %.3f um; std PCell w=%.2f l=%.2f ng=1' % (e['W_mean_perimeter'], w_std, Lg))

def build_l130_test(d=0.42, Lg=0.13, s=0.45):
    ly = pya.Layout(); ly.dbu = 0.001
    top = ly.create_cell('g1_elt_l130_test')
    e = elt_nmos(d, Lg, s, 0.0, 0.0, cell=top)
    D = Draw(ly, top)
    D.box('M2pin', e['drain_exit_x'], -0.15, e['drain_exit_x'] + 0.30, 0.15); D.label('M2txt', e['drain_exit_x'] + 0.15, 0, 'D_ELT')
    D.box('M2pin', e['gate_exit_x'] - 0.30, -0.15, e['gate_exit_x'], 0.15); D.label('M2txt', e['gate_exit_x'] - 0.15, 0, 'G')
    out = os.path.join(HERE, 'g1_elt_l130_test.gds')
    ly.write(out)
    print('wrote', out, 'bbox', top.dbbox(), 'mean-perimeter W = %.3f' % e['W_mean_perimeter'])

if __name__ == '__main__':
    build_pair()
    build_l130_test()
