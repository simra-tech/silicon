#!/usr/bin/env python3
"""r1_safe comparator layout cell `r1s_cmp` (KLayout batch Python, PDK PCells from library SG13_dev).

Netlist of record: designs/r1-joint/blocks/r1_safe/schematic/r1_safe.spice, subckt r1_safe_cmp (lines 809-848).
Import:      from r1_safe_cmp_cell import build_cmp ; cell = build_cmp(ly)      (ly.dbu = 0.001)
Standalone (pinned container, KLayout 0.30.9, PDK commit 8437402), from the repository root:
  G1_WORKDIR=designs/r1-joint/blocks/r1_safe/layout flow/run.sh klayout -b -r r1_safe_cmp_cell.py -rd out=<dir>
  writes <dir>/r1s_cmp.gds, <dir>/r1s_cmp_lvs.cdl and r1_safe_cmp_cell_meta.json (next to this script).

Cell: W = 59.0 um, H = 109.35 um, origin lower left, prBoundary 189/4 = outline. Metal1..Metal4 only.
Every device is a PDK PCell flattened into the cell. Floorplan (y in um, bottom to top):
  0.0 .. 0.7       Metal3 pins ibias, inp, inn, out (bottom edge)
  1.0 .. 2.2       vss rail (Metal3, full width)
  1.7 .. 22.3      NMOS mirror ML1/ML2: two nmosHV rows w 40 / l 10 / ng 4 (finger 10 um; the PCell takes at most
                   10 um per finger), row 1 strips d1 vss d2 vss d1, row 2 d2 vss d1 vss d2 (2-D common centroid),
                   all gates d1.  Right of it (x 44.6 .. 58): bias and logic: MBN+MB2 (one nmosHV ng 2),
                   MG, MI1N+MD1N (one nmosHV ng 2), MD2N (LV); vdd well with MD1P (HV) and MD2P (LV).
  16.9 .. 18.1     vdd rail (Metal3, full width)
  23.4 .. 23.7     p+ substrate bar
  24.7 .. 28.7     tail strip: pmosHV w 80 / l 2 / ng 20 (finger 4), drains
                   vdda(dummy) ta tb tb ta ta tb tb ta o1 vbp, sources vdda: 8 MTA, 8 MTB (centroids both on
                   strip 9), 2 MGL, MBP, one dummy finger (gate on vdda).  Right of it: MI1P, MH2+MH3 (ng 2).
  29.15 .. 30.35   vdda rail (Metal3, full width) over the tail n+ tie
  30.8 .. 107.8    degeneration resistors: 18 rppd strips w 2 / l 77 at pitch 2.4: D | A1 A2 B1 B2 B2 B1 A2 A1
                   A1 A2 B1 B2 B2 B1 A2 A1 | D.  Each resistor = 4 series segments of 77 um = 308 um, common
                   centroid; dummies = GatPoly/pSD/SalBlock/EXTBlock without RES 52/0 and PolyRes 128/0.
  column x 45.8 .. 52.0: input pair A (MA1/MA2, well ta) y 35.4 .. 66.1, input pair B (MB1/MB2I, well tb)
                   y 77.8 .. 108.5.  Rotated islands (fingers horizontal): tie | dummy | A(2f) | B(4f) | A(2f) |
                   dummy | tie, A/B = 2 / 4 fingers w 5 l 2 (ABBA in 2-finger units), dummies all on the well net.
  column x 53.8 .. 57.8: MH1a/b/c as one pmosHV ng 3 (w 0.5 / l 8 per finger, strips hs hn2 hn1 vdda).
  108.75 .. 109.05 p+ ring top; refn / refp Metal3 pins on the top edge.
Routing: Metal1/Metal2 local, Metal3 rails, channel tracks over the resistor bottom, jogs; Metal4 vertical trunks
(inp, inn, d1, d2, o1, o2, vbp, ibias, out, tb, sb1, sb2).  p+ ring (vss) around the cell interior.

DRC values used (sg13g2_tech_mod.json / deck): Act.b 0.21, Gat.b 0.18, Cnt.e 0.14, M1.b 0.18, Mn.b 0.21,
Mn.d area 0.144 (stack pads 0.4 x 0.4), Vn 0.19, NW.b1 1.8, NW.c1 0.62, NW.e 0.24, NW.f 0.24, NW.d1 0.62,
TGO.b 0.27, TGO.d 0.34, Sal.d 0.20, EXTB.c 0.31.
"""
import json
import os
import sys

K = '/foss/pdks/ihp-sg13g2/libs.tech/klayout/python'
for _p in [K, K + '/pycell4klayout-api/source/python']:
    if _p not in sys.path:
        sys.path.insert(0, _p)
import pya  # noqa: E402
import sg13g2_pycell_lib  # noqa: E402,F401  (registers library SG13_dev)

HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(HERE, '..', 'schematic', 'r1_safe.spice')
LIB = pya.Library.library_by_name('SG13_dev', 'sg13g2')

W = 59.0
H = 109.35
LAYERS = {
    'Activ': (1, 0), 'GatPoly': (5, 0), 'Cont': (6, 0), 'pSD': (14, 0), 'NWell': (31, 0), 'TGO': (44, 0),
    'M1': (8, 0), 'Via1': (19, 0), 'M2': (10, 0), 'Via2': (29, 0), 'M3': (30, 0), 'M3pin': (30, 2),
    'M3txt': (30, 25), 'Via3': (49, 0), 'M4': (50, 0), 'SalBlock': (28, 0), 'ExtBlock': (111, 0),
    'prBoundary': (189, 4),
}
SPACE = {'M1': 0.18, 'M2': 0.21, 'M3': 0.21, 'M4': 0.21}
META = {}


def um(v):
    return int(round(v * 1000))


class Draw:
    def __init__(self, ly, cell):
        self.ly, self.cell = ly, cell
        self.L = {n: ly.layer(*v) for n, v in LAYERS.items()}
        self.reg = {k: [] for k in SPACE}

    def box(self, layer, x1, y1, x2, y2, net=None):
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        self.cell.shapes(self.L[layer]).insert(pya.Box(um(x1), um(y1), um(x2), um(y2)))
        if net is not None and layer in self.reg:
            self.reg[layer].append((net, (x1, y1, x2, y2)))

    def sq(self, layer, cx, cy, s, net=None):
        self.box(layer, cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2, net)

    def hw(self, layer, x1, x2, y, net, w=0.3):
        self.box(layer, min(x1, x2) - w / 2, y - w / 2, max(x1, x2) + w / 2, y + w / 2, net)

    def vw(self, layer, x, y1, y2, net, w=0.3):
        self.box(layer, x - w / 2, min(y1, y2) - w / 2, x + w / 2, max(y1, y2) + w / 2, net)

    def label(self, x, y, text):
        t = pya.Text(text, pya.Trans(pya.Point(um(x), um(y))))
        t.size = um(0.3)
        self.cell.shapes(self.L['M3txt']).insert(t)

    def via(self, n, x, y, net, lo=0.3, hi=0.3):
        """Via<n> (n = 1, 2, 3) between Metal<n> and Metal<n+1> with square pads lo / hi (0 = no pad)"""
        self.sq('Via%d' % n, x, y, 0.19)
        if lo:
            self.sq('M%d' % n, x, y, lo, net)
        if hi:
            self.sq('M%d' % (n + 1), x, y, hi, net)

    def stack(self, x, y, m_from, m_to, net, end=0.3):
        """vias from Metal<m_from> to Metal<m_to>; intermediate pads 0.4 (min area), end pads `end`"""
        for n in range(m_from, m_to):
            lo = (0.3 if n == 1 else end) if n == m_from else 0.4
            hi = end if n + 1 == m_to else 0.4
            self.via(n, x, y, net, lo=lo, hi=hi)

    def cont_row(self, x1, x2, y):
        n = int((x2 - x1 - 0.16) / 0.34 + 1e-6) + 1
        x0 = (x1 + x2) / 2 - (n - 1) * 0.34 / 2
        for i in range(n):
            self.sq('Cont', x0 + i * 0.34, y, 0.16)

    def cont_col(self, y1, y2, x):
        n = int((y2 - y1 - 0.16) / 0.34 + 1e-6) + 1
        y0 = (y1 + y2) / 2 - (n - 1) * 0.34 / 2
        for i in range(n):
            self.sq('Cont', x, y0 + i * 0.34, 0.16)

    def ptap(self, x1, y1, x2, y2, net='vss'):
        """p+ substrate tie bar: Activ + pSD (0.03 larger), contacts 0.12 inside the ends, Metal1 over it"""
        self.box('Activ', x1, y1, x2, y2)
        self.box('pSD', x1 - 0.03, y1 - 0.03, x2 + 0.03, y2 + 0.03)
        if x2 - x1 >= y2 - y1:
            self.cont_row(x1 + 0.07, x2 - 0.07, (y1 + y2) / 2)
        else:
            self.cont_col(y1 + 0.07, y2 - 0.07, (x1 + x2) / 2)
        self.box('M1', x1, y1, x2, y2, net)

    def ntap(self, x1, y1, x2, y2, net):
        """n+ well tie bar (caller draws the NWell): Activ, contacts, Metal1"""
        self.box('Activ', x1, y1, x2, y2)
        self.cont_row(x1 + 0.07, x2 - 0.07, (y1 + y2) / 2)
        self.box('M1', x1, y1, x2, y2, net)

    def pcell(self, name, params, trans):
        pcv = LIB.layout().add_pcell_variant(LIB.layout().pcell_id(name), params)
        cell = self.ly.cell(self.ly.add_lib_cell(LIB, pcv))
        inst = self.cell.insert(pya.CellInstArray(cell.cell_index(), trans))
        inst.flatten()

    def check(self):
        """same-layer spacing / short check of the registered routing shapes (different nets)"""
        bad = []
        for layer, shapes in self.reg.items():
            s = SPACE[layer] - 1e-6
            n = len(shapes)
            srt = sorted(shapes, key=lambda t: t[1][0])
            for i in range(n):
                na, a = srt[i]
                for j in range(i + 1, n):
                    nb, b = srt[j]
                    if b[0] - a[2] >= s:
                        break
                    if na == nb:
                        continue
                    dx = max(0.0, b[0] - a[2], a[0] - b[2])
                    dy = max(0.0, b[1] - a[3], a[1] - b[3])
                    if (dx * dx + dy * dy) ** 0.5 < s:
                        bad.append((layer, na, a, nb, b))
        return bad


class Dev:
    """MOS PCell with its Activ lower-left at (x0, y0); rot 0 or 90 (fingers horizontal, local x -> parent y,
    local y -> parent x0 + wf - y).  Local frame as the PCell: strips at x 0.07 + i*P, gates at 0.34 + i*P."""

    def __init__(self, d, kind, w, l, ng, x0, y0, rot=0):
        self.d, self.kind, self.l, self.ng, self.x0, self.y0, self.rot = d, kind, l, ng, x0, y0, rot
        self.wf = round(w / ng, 4)
        self.P = round(l + 0.38, 4)
        self.A = round(0.68 + ng * l + (ng - 1) * 0.38, 4)
        if rot == 0:
            t = pya.Trans(0, False, um(x0), um(y0))
        else:
            t = pya.Trans(1, False, um(x0 + self.wf), um(y0))
        d.pcell(kind, {'w': '%gu' % w, 'l': '%gu' % l, 'ng': ng}, t)

    def P2(self, x, y):
        if self.rot == 0:
            return (round(self.x0 + x, 4), round(self.y0 + y, 4))
        return (round(self.x0 + self.wf - y, 4), round(self.y0 + x, 4))

    def lbox(self, layer, x1, y1, x2, y2, net=None):
        a, b = self.P2(x1, y1), self.P2(x2, y2)
        self.d.box(layer, a[0], a[1], b[0], b[1], net)

    def sx(self, i):
        return round(0.15 + i * self.P, 4)

    def gx(self, i):
        return (round(0.34 + i * self.P, 4), round(0.34 + i * self.P + self.l, 4))

    def strip_pt(self, i, y):
        """parent point on strip i at local y"""
        return self.P2(self.sx(i), y)

    def ext(self, i, y_to, net):
        """extend strip i (Metal1, 0.16 wide) from the Activ edge to local y_to"""
        y_from = 0.0 if y_to < 0 else self.wf
        self.lbox('M1', self.sx(i) - 0.08, y_from, self.sx(i) + 0.08, y_to, net)

    def strap(self, gates, side, cx, net=None):
        """GatPoly bar joining `gates` on side 'lo' (local y < 0) or 'hi' (y > wf), one contact + Metal1 pad at
        local x cx. Returns the parent pad centre."""
        x1 = min(min(self.gx(i)[0] for i in gates), cx - 0.15)
        x2 = max(max(self.gx(i)[1] for i in gates), cx + 0.15)
        if side == 'lo':
            yb, yc = (-0.56, -0.10), -0.36
        else:
            yb, yc = (self.wf + 0.10, self.wf + 0.56), self.wf + 0.36
        self.lbox('GatPoly', x1, yb[0], x2, yb[1])
        self.lbox('Cont', cx - 0.08, yc - 0.08, cx + 0.08, yc + 0.08)
        self.lbox('M1', cx - 0.15, yc - 0.15, cx + 0.15, yc + 0.15, net)
        return self.P2(cx, yc)


# =============================================================================================
def build_cmp(ly):
    top = ly.create_cell('r1s_cmp')
    d = Draw(ly, top)
    pins = {}

    def pin(net, x1, y1, x2, y2):
        d.box('M3', x1, y1, x2, y2, net)
        d.box('M3pin', x1, y1, x2, y2)
        d.label((x1 + x2) / 2, (y1 + y2) / 2, net)
        pins[net] = [round(v, 3) for v in (x1, y1, x2, y2)]

    d.box('prBoundary', 0, 0, W, H)

    # ---------------------------------------------------------------- p+ ring (vss), Activ 0.3 .. 0.6 inside
    RI = (0.6, 0.6, W - 0.6, H - 0.6)
    d.ptap(0.3, 0.3, W - 0.3, 0.6)
    d.ptap(0.3, H - 0.6, W - 0.3, H - 0.3)
    d.box('Activ', 0.3, 0.6, 0.6, H - 0.6)
    d.box('Activ', W - 0.6, 0.6, W - 0.3, H - 0.6)
    d.box('pSD', 0.27, 0.27, 0.63, H - 0.27)
    d.box('pSD', W - 0.63, 0.27, W - 0.27, H - 0.27)
    d.cont_col(0.6 + 0.19, H - 0.6 - 0.19, 0.45)
    d.cont_col(0.6 + 0.19, H - 0.6 - 0.19, W - 0.45)
    d.box('M1', 0.3, 0.3, 0.6, H - 0.3, 'vss')
    d.box('M1', W - 0.6, 0.3, W - 0.3, H - 0.3, 'vss')

    # ---------------------------------------------------------------- rails
    RAILS = {'vss': (1.0, 2.2), 'vdd': (16.9, 18.1), 'vdda': (29.15, 30.35)}
    for net, (y1, y2) in RAILS.items():
        pin(net, 0.0, y1, W, y2)
    for x in (0.45, W - 0.45):
        d.stack(x, 1.6, 1, 3, 'vss', end=0.3)

    # ---------------------------------------------------------------- resistor array
    Yr, LR = 30.8, 77.0
    XR = [round(1.2 + 2.4 * k, 3) for k in range(18)]
    for k in range(18):
        x = XR[k]
        if k in (0, 17):
            d.box('GatPoly', x, Yr - 0.43, x + 2.0, Yr + LR + 0.43)
            d.box('pSD', x - 0.18, Yr - 0.61, x + 2.18, Yr + LR + 0.61)
            d.box('SalBlock', x - 0.2, Yr, x + 2.2, Yr + LR)
            d.box('ExtBlock', x - 0.2, Yr, x + 2.2, Yr + LR)
            d.box('ExtBlock', x - 0.18, Yr - 0.61, x + 2.18, Yr + LR + 0.61)
        else:
            d.pcell('rppd', {'w': '2u', 'l': '%gu' % LR, 'b': 0, 'ps': '0.18u', 'Calculate': 'R'},
                    pya.Trans(0, False, um(x), um(Yr)))
    d.box('pSD', XR[0] - 0.18, Yr - 0.61, XR[17] + 2.18, Yr + LR + 0.61)
    d.box('ExtBlock', XR[0] - 0.18, Yr - 0.61, XR[17] + 2.18, Yr + LR + 0.61)
    HB, HT = round(Yr - 0.28, 3), round(Yr + LR + 0.28, 3)

    def hx(p):
        return round(XR[p + 1] + 1.0, 3)
    PAT = ['A1', 'A2', 'B1', 'B2', 'B2', 'B1', 'A2', 'A1'] * 2
    for (a, b, j) in ((0, 7, 3), (1, 6, 2), (2, 5, 1), (3, 4, 0), (8, 15, 3), (9, 14, 2), (10, 13, 1), (11, 12, 0)):
        net = 'r%s_t%d' % (PAT[a], a)
        y = round(HT - 0.78 - 0.6 * j, 3)
        for p in (a, b):
            d.via(1, hx(p), HT, net, lo=0, hi=0.3)
            d.vw('M2', hx(p), HT, y, net)
        d.hw('M2', hx(a), hx(b), y, net)
    for (a, b, j) in ((7, 8, 0), (6, 9, 1), (5, 10, 2), (4, 11, 3)):
        net = 'r%s_b%d' % (PAT[a], a)
        y = round(HB + 0.78 + 0.6 * j, 3)
        for p in (a, b):
            d.via(1, hx(p), HB, net, lo=0, hi=0.3)
            d.vw('M2', hx(p), HB, y, net)
        d.hw('M2', hx(a), hx(b), y, net)
    # channel tracks (Metal3) over the resistor bottom: net -> y, from the resistor terminal to the column
    CH = {'ta': 31.4, 'tb': 32.05, 'sb2': 32.7, 'sb1': 33.35, 'sa2': 34.0, 'sa1': 34.65}
    TERM = {0: 'ta', 1: 'ta', 2: 'tb', 3: 'tb', 15: 'sa1', 14: 'sa2', 13: 'sb1', 12: 'sb2'}
    COLX = {'ta': 46.04, 'tb': 47.6, 'sb1': 48.2, 'sa1': 48.2, 'sb2': 49.4, 'sa2': 49.4}
    TAIL_TA_Y, TAIL_TB_Y = 25.9, 27.5
    for p, net in TERM.items():
        x = hx(p)
        d.via(1, x, HB, net, lo=0, hi=0.3)
        if p in (0, 2, 12, 13, 14, 15):            # one terminal per net up to its channel track
            d.vw('M2', x, HB, CH[net], net)
            d.via(2, x, CH[net], net, lo=0.3, hi=0.4)
        if p in (0, 1, 2, 3):                       # tail side: down to the tail drain track
            d.vw('M2', x, HB, TAIL_TA_Y if net == 'ta' else TAIL_TB_Y, net)
    for net, y in CH.items():
        x1 = hx([p for p, n in TERM.items() if n == net][0] if net in ('sa1', 'sa2', 'sb1', 'sb2') else
                (0 if net == 'ta' else 2))
        d.hw('M3', x1, COLX[net], y, net)

    # ---------------------------------------------------------------- NMOS mirror (two rows)
    Y1, Y2 = 1.7, 12.3
    r1 = Dev(d, 'nmosHV', 40, 10, 4, 1.5, Y1)
    r2 = Dev(d, 'nmosHV', 40, 10, 4, 1.5, Y2)
    MX = [round(1.5 + r1.sx(i), 3) for i in range(5)]
    # row 1: gates strapped below, contacts under strips 0 and 4 (d1)
    r1.lbox('GatPoly', 0.0, -0.56, r1.A, -0.10)
    for i in (0, 4):
        r1.lbox('Cont', r1.sx(i) - 0.08, -0.44, r1.sx(i) + 0.08, -0.28)
        r1.lbox('M1', r1.sx(i) - 0.15, -0.51, r1.sx(i) + 0.15, -0.21, 'd1')
        r1.ext(i, -0.21, 'd1')
    # row 2: gates strapped above, contact over strip 2 (d1)
    r2.strap([0, 1, 2, 3], 'hi', r2.sx(2), 'd1')
    r2.ext(2, r2.wf + 0.21, 'd1')
    d.box('TGO', 1.23, 0.95, 43.59, 23.05)
    for i in (1, 3):                                # vss strips: rows joined, stacks to the vss rail
        d.box('M1', MX[i] - 0.08, Y1 + 10.0, MX[i] + 0.08, Y2, 'vss')
        d.stack(MX[i], 1.95, 1, 3, 'vss')
    JOG = [('d1', 9.5, (0, 4), 47.0), ('d2', 10.5, (2,), 50.6), ('d2', 13.5, (0, 4), 50.6), ('d1', 14.5, (2,), 47.0)]
    for net, y, strips, xe in JOG:
        for i in strips:
            d.stack(MX[i], y, 1, 3, net, end=0.4)
        d.hw('M3', MX[strips[0]], xe, y, net)
        d.via(3, xe, y, net, lo=0, hi=0.4)

    # ---------------------------------------------------------------- p+ bar over the mirror
    d.ptap(0.95, 23.4, 43.6, 23.7)
    d.box('Activ', 0.3, 23.4, 0.95, 23.7)
    d.box('pSD', 0.27, 23.37, 0.95, 23.73)
    d.box('M1', 0.3, 23.4, 0.95, 23.7, 'vss')

    # ---------------------------------------------------------------- tail strip (vdda well)
    Yt = 24.7
    tl = Dev(d, 'pmosHV', 80, 2, 20, 1.9, Yt)
    TX = [round(1.9 + tl.sx(i), 3) for i in range(21)]
    DR = {0: 'vdda', 2: 'ta', 4: 'tb', 6: 'tb', 8: 'ta', 10: 'ta', 12: 'tb', 14: 'tb', 16: 'ta', 18: 'o1', 20: 'vbp'}
    TIE_Y = (29.6, 29.9)
    d.ntap(1.9, TIE_Y[0], 53.15, TIE_Y[1], 'vdda')
    for x in (2.6, 16.0, 24.0, 32.0, 42.0):
        d.stack(x, 29.75, 1, 3, 'vdda', end=0.3)
    for i in range(21):
        if i % 2 == 1 or DR[i] == 'vdda':          # sources and the dummy drain up to the tie
            tl.ext(i, TIE_Y[0] - Yt + 0.15, 'vdda')
    # dummy finger 0: own gate tab, contacted left of the Activ and tied to strip 0 (vdda)
    tl.lbox('GatPoly', -0.45, -0.56, tl.gx(0)[1], -0.10)
    tl.lbox('Cont', -0.38, -0.44, -0.22, -0.28)
    tl.lbox('M1', -0.45, -0.51, tl.sx(0) + 0.08, -0.21, 'vdda')
    tl.ext(0, -0.21, 'vdda')
    # fingers 1..19: one bar, contact right of the Activ, tied to strip 20 (vbp, MBP diode)
    tl.lbox('GatPoly', tl.gx(1)[0], -0.56, tl.A + 0.45, -0.10)
    tl.lbox('Cont', tl.A + 0.22, -0.44, tl.A + 0.38, -0.28)
    tl.lbox('M1', tl.sx(20) - 0.08, -0.51, tl.A + 0.45, -0.21, 'vbp')
    tl.ext(20, -0.21, 'vbp')
    d.box('TGO', 1.28, 24.05, 50.42, 29.32)
    for i in (2, 8, 10, 16):
        d.via(1, TX[i], TAIL_TA_Y, 'ta')
    for i in (4, 6, 12, 14):
        d.via(1, TX[i], TAIL_TB_Y, 'tb')
    d.hw('M2', hx(0), TX[16], TAIL_TA_Y, 'ta')
    d.hw('M2', hx(2), TX[14], TAIL_TB_Y, 'tb')
    O1_Y = 24.64
    tl.ext(18, -0.21, 'o1')
    d.via(1, TX[18], O1_Y, 'o1')
    VBP_Y = 28.6
    d.via(1, TX[20], VBP_Y, 'vbp')

    # ---------------------------------------------------------------- right of the tail: MI1P, MH2/MH3
    mi = Dev(d, 'pmosHV', 2, 0.5, 1, 52.3, 25.0)          # strips vdda | o2, gate o1
    mh = Dev(d, 'pmosHV', 2, 0.5, 2, 54.2, 25.0)          # strips d2 | hs | d1, gates o1 | o2
    p_mi = mi.strap([0], 'lo', 0.59, 'o1')
    mh.lbox('GatPoly', mh.gx(0)[0], -0.56, mh.gx(0)[1], 0.0)
    mh.lbox('GatPoly', mh.gx(1)[0], -0.56, mh.gx(1)[1], 0.0)
    p_mh2 = mh.P2(0.59, -0.36)
    p_mh3 = mh.P2(1.47, -0.36)
    for p, net in ((p_mh2, 'o1'), (p_mh3, 'o2')):
        d.sq('Cont', p[0], p[1], 0.16)
        d.sq('M1', p[0], p[1], 0.3, net)
    d.hw('M1', p_mi[0], p_mh2[0], O1_Y, 'o1')
    mi.ext(0, TIE_Y[0] - 25.0 + 0.15, 'vdda')
    mi.ext(1, 28.0 - 25.0 + 0.15, 'o2')
    d.via(1, 52.3 + mi.sx(1), 28.0, 'o2')
    d.via(1, p_mh3[0], p_mh3[1], 'o2', lo=0)
    d.vw('M2', p_mh3[0], p_mh3[1], 28.0, 'o2')
    d.hw('M2', 52.3 + mi.sx(1), p_mh3[0], 28.0, 'o2')
    MHX = [round(54.2 + mh.sx(i), 3) for i in range(3)]
    D2_JOG_Y, D1_JOG_Y = 32.0, 35.4
    d.box('M1', MHX[0] - 0.08, 26.0, MHX[0] + 0.08, D2_JOG_Y + 0.15, 'd2')
    d.stack(MHX[0], D2_JOG_Y, 1, 3, 'd2', end=0.4)
    d.hw('M3', 50.6, MHX[0], D2_JOG_Y, 'd2')
    d.via(3, 50.6, D2_JOG_Y, 'd2', lo=0, hi=0.4)
    d.box('M1', MHX[2] - 0.08, 26.0, MHX[2] + 0.08, D1_JOG_Y + 0.15, 'd1')
    d.stack(MHX[2], D1_JOG_Y, 1, 3, 'd1', end=0.4)
    d.hw('M3', 47.0, MHX[2], D1_JOG_Y, 'd1')
    d.box('M1', MHX[1] - 0.08, 26.0, MHX[1] + 0.08, 31.0 + 0.23, 'hs')
    # tail o1 / vbp lines (Metal2) to the Metal4 trunks
    X_O1, X_O2, X_VBP = 53.2, 53.8, 52.4
    d.hw('M2', TX[18], X_O1, O1_Y, 'o1')
    d.stack(X_O1, O1_Y, 1, 4, 'o1', end=0.4)
    d.hw('M2', TX[20], X_VBP, VBP_Y, 'vbp')
    d.stack(X_VBP, VBP_Y, 2, 4, 'vbp', end=0.4)
    d.stack(X_O2, 28.0, 2, 4, 'o2', end=0.4)
    d.hw('M2', 52.3 + mi.sx(1), X_O2, 28.0, 'o2')

    # ---------------------------------------------------------------- MH1a/b/c column
    mh1 = Dev(d, 'pmosHV', 1.5, 8, 3, 55.0, 31.0, rot=90)   # strips (parent y up): hs, hn2, hn1, vdda
    p_mh1 = mh1.strap([0, 1, 2], 'hi', 24.9, 'vbp')
    for i, net in ((1, 'hn2'), (2, 'hn1')):         # floating internal strips: Metal1 area (M1.d)
        mh1.lbox('M1', mh1.sx(i) - 0.15, 0.0, mh1.sx(i) + 0.15, mh1.wf, net)
    TIE2 = (57.4, 57.7)
    d.ntap(54.6, TIE2[0], 56.0, TIE2[1], 'vdda')
    d.box('M1', 52.85, TIE2[0], 54.6, TIE2[1], 'vdda')
    d.box('M1', 55.1, 31.0 + mh1.sx(3) - 0.08, 55.4, TIE2[0], 'vdda')
    d.via(1, 53.0, TIE_Y[0] + 0.15, 'vdda', hi=0)
    d.via(1, 53.0, TIE2[0] + 0.15, 'vdda', hi=0)
    d.vw('M2', 53.0, TIE_Y[0] + 0.15, TIE2[0] + 0.15, 'vdda')
    d.stack(X_VBP, p_mh1[1], 1, 4, 'vbp', end=0.4)
    d.hw('M1', X_VBP, p_mh1[0], p_mh1[1], 'vbp')
    d.vw('M4', X_VBP, 6.9, p_mh1[1], 'vbp')
    # vdda well: tail + right region + column (one net)
    d.box('NWell', 1.28, 24.0, 57.8, 30.2)
    d.box('NWell', 53.82, 30.2, 57.8, 58.0)
    d.box('TGO', 51.68, 24.1, 56.88, 27.62)

    # ---------------------------------------------------------------- input pairs (rotated islands)
    XP = 46.4
    TRK = {'dA': 47.0, 'sA': 48.2, 'sB': 49.4, 'dB': 50.6}
    XGL, XGR = round(XP - 0.36, 3), round(XP + 5.0 + 0.36, 3)

    def pair(Yw, well, gA, gB, sA, sB, tag):
        nets = {'dA': 'd1', 'dB': 'd2', 'sA': sA, 'sB': sB}
        t1 = round(Yw + 0.4, 3)
        y = round(t1 + 0.3 + 1.0, 3)
        isl = []
        for kind, ng in (('dum', 1), ('A', 2), ('B', 4), ('A', 2), ('dum', 1)):
            dv = Dev(d, "pmosHV", 5 * ng, 2, ng, XP, y, rot=90)
            isl.append((kind, dv, y))
            y = round(y + dv.A + 0.5, 3)
        ytop = round(y - 0.5, 3)
        t2 = round(ytop + 1.0, 3)
        out = {'t1': t1, 't2': t2}
        strips = {k: [] for k in nets}
        pads = {'A': [], 'B': []}
        for n_i, (kind, dv, yi) in enumerate(isl):
            sy = [round(yi + dv.sx(i), 3) for i in range(dv.ng + 1)]
            cy = round(dv.A / 2, 3)
            if kind == 'dum':
                dv.strap([0], 'lo', cy, well)
                if n_i == 0:          # strips, gate pad and the lower tie joined on the right side
                    d.box('M1', 51.25, t1, 51.91, sy[1] + 0.08, well)
                else:
                    d.box('M1', 51.25, sy[0] - 0.08, 51.91, t2 + 0.3, well)
                continue
            if kind == 'A':
                pads['A'].append(dv.strap(list(range(dv.ng)), 'hi', cy, gA))
                seq = ['dA', 'sA', 'dA']
            else:
                pads['B'].append(dv.strap(list(range(dv.ng)), 'lo', cy, gB))
                seq = ['dB', 'sB', 'dB', 'sB', 'dB']
            for i, k in enumerate(seq):
                d.via(1, TRK[k], sy[i], nets[k])
                strips[k].append(sy[i])
        # gate join of the two A islands (left side, Metal1)
        d.box('M1', XGL - 0.15, pads['A'][0][1], XGL + 0.15, pads['A'][1][1], gA)
        # ties (n+ in the well), Metal1 extended to both sides
        for ty in (t1, t2):
            d.ntap(XP, ty, XP + 5.0, ty + 0.3, well)
            d.box('M1', XGL - 0.15, ty, XGR + 0.15, ty + 0.3, well)
        d.box('NWell', XP - 0.62, Yw, XP + 5.62, round(t2 + 0.7, 3))
        d.box('pSD', XP - 0.40, round(isl[0][2] - 0.18, 3), XP + 5.40, round(ytop + 0.18, 3))
        d.box('TGO', XP - 0.62, round(isl[0][2] - 0.62, 3), XP + 5.62, round(ytop + 0.62, 3))
        out.update(strips=strips, padA=pads['A'], padB=pads['B'][0], top=round(t2 + 0.7, 3))
        return out

    PA = pair(35.4, 'ta', 'inp', 'inn', 'sa1', 'sa2', 'A')
    PB = pair(77.8, 'tb', 'refn', 'refp', 'sb1', 'sb2', 'B')
    # d1 / d2 tracks: continuous from pair B down to the stacks under pair A
    d.vw('M2', TRK['dA'], D1_JOG_Y, max(PB['strips']['dA']), 'd1')
    d.vw('M2', TRK['dB'], 36.0, max(PB['strips']['dB']), 'd2')
    d.stack(TRK['dA'], D1_JOG_Y, 2, 4, 'd1', end=0.4)
    d.stack(TRK['dB'], 36.0, 2, 4, 'd2', end=0.4)
    d.vw('M4', 47.0, 9.5, D1_JOG_Y, 'd1')
    d.vw('M4', 50.6, 4.06, 36.0, 'd2')
    # pair A sources down to the channel (Metal2), well tie ta down (Metal2)
    d.vw('M2', TRK['sA'], CH['sa1'], max(PA['strips']['sA']), 'sa1')
    d.vw('M2', TRK['sB'], CH['sa2'], max(PA['strips']['sB']), 'sa2')
    d.via(2, TRK['sA'], CH['sa1'], 'sa1', lo=0.3, hi=0.4)
    d.via(2, TRK['sB'], CH['sa2'], 'sa2', lo=0.3, hi=0.4)
    d.via(1, XGL, PA['t1'] + 0.15, 'ta', lo=0)
    d.vw('M2', XGL, CH['ta'], PA['t1'] + 0.15, 'ta')
    d.via(2, XGL, CH['ta'], 'ta', lo=0.3, hi=0.4)
    # pair B sources and tie: in-pair Metal2, stack at the lowest strip, Metal4 down to the channel
    d.vw('M2', TRK['sA'], min(PB['strips']['sA']), max(PB['strips']['sA']), 'sb1')
    d.vw('M2', TRK['sB'], min(PB['strips']['sB']), max(PB['strips']['sB']), 'sb2')
    for x, yy, net in ((TRK['sA'], min(PB['strips']['sA']), 'sb1'), (TRK['sB'], min(PB['strips']['sB']), 'sb2'),
                       (47.6, PB['t1'] + 0.15, 'tb')):
        d.stack(x, yy, 1 if net == 'tb' else 2, 4, net, end=0.4)
        d.vw('M4', x, CH[net], yy, net)
        d.via(3, x, CH[net], net, lo=0.4, hi=0.4)
    # gate trunks: inp / inn down to the bottom pins (Metal4), refn / refp up to the top pins (Metal3)
    pa_inp = PA['padA'][0]
    d.stack(XGL, pa_inp[1], 1, 4, 'inp', end=0.4)
    d.vw('M4', XGL, 0.35, pa_inp[1], 'inp')
    d.stack(XGR, PA['padB'][1], 1, 4, 'inn', end=0.4)
    d.vw('M4', XGR, 0.35, PA['padB'][1], 'inn')
    pb_refn = PB['padA'][1]
    d.stack(XGL, pb_refn[1], 1, 3, 'refn', end=0.4)
    d.vw('M3', XGL, pb_refn[1], H - 0.4, 'refn')
    d.stack(XGR, PB['padB'][1], 1, 3, 'refp', end=0.4)
    d.vw('M3', XGR, PB['padB'][1], H - 0.4, 'refp')
    pin('refn', XGL - 0.3, H - 0.8, XGL + 0.3, H)
    pin('refp', XGR - 0.3, H - 0.8, XGR + 0.3, H)

    # ---------------------------------------------------------------- bias + logic block (right of the mirror)
    YN = 1.7
    nb = Dev(d, 'nmosHV', 8, 1, 2, 44.6, YN)          # strips ibias | vss | vbp, gates ibias
    p_nb = nb.strap([0, 1], 'hi', nb.sx(0) + 0.69, 'ibias')
    nb.lbox('M1', nb.sx(0) - 0.08, nb.wf, nb.sx(0) + 0.08, 4.9 + 0.15, 'ibias')
    nb.lbox('M1', nb.sx(0) - 0.08, nb.wf + 0.21, p_nb[0] - 44.6 + 0.15, nb.wf + 0.51, 'ibias')
    X_IB = round(44.6 + nb.sx(0), 3)
    d.stack(X_IB, 6.6, 1, 4, 'ibias', end=0.4)
    d.vw('M4', X_IB, 0.35, 6.6, 'ibias')
    nb.ext(1, -1.25, 'vss')
    nb.ext(2, 6.9 - YN + 0.15, 'vbp')
    d.via(1, 44.6 + nb.sx(2), 6.9, 'vbp')
    d.hw('M2', 44.6 + nb.sx(2), X_VBP, 6.9, 'vbp')
    d.stack(X_VBP, 6.9, 2, 4, 'vbp', end=0.4)
    mg = Dev(d, 'nmosHV', 2, 2, 1, 48.4, YN)          # strips vss | o1, gate d2
    p_mg = mg.strap([0], 'hi', 1.34, 'd2')
    mg.ext(0, -1.25, 'vss')
    mg.ext(1, 7.6 - YN + 0.15, 'o1')
    d.via(1, 48.4 + mg.sx(1), 7.6, 'o1')
    d.stack(p_mg[0], p_mg[1], 1, 3, 'd2', end=0.4)
    d.hw('M3', p_mg[0], 50.6, p_mg[1], 'd2')
    d.via(3, 50.6, p_mg[1], 'd2', lo=0, hi=0.4)
    ni = Dev(d, 'nmosHV', 2, 0.45, 2, 51.8, YN)       # strips o2 | vss | o3, gates o1 | o2
    NIX = [round(51.8 + ni.sx(i), 3) for i in range(3)]
    gp = []
    for g in (0, 1):
        g1, g2 = ni.gx(g)
        ni.lbox('GatPoly', g1, ni.wf, g2, ni.wf + 0.56)
        c = round((g1 + g2) / 2, 3)
        ni.lbox('Cont', c - 0.08, ni.wf + 0.25, c + 0.08, ni.wf + 0.41)
        ni.lbox('M1', c - 0.15, ni.wf + 0.18, c + 0.15, ni.wf + 0.48, 'o1' if g == 0 else 'o2')
        gp.append(ni.P2(c, ni.wf + 0.33))
    ni.ext(1, -1.25, 'vss')
    ni.ext(0, 8.3 - YN + 0.15, 'o2')
    ni.ext(2, 12.3 - YN + 0.15, 'o3')
    d.box('M1', gp[0][0] - 0.08, gp[0][1], gp[0][0] + 0.08, 7.6, 'o1')
    d.box('M1', gp[1][0] - 0.08, gp[1][1], gp[1][0] + 0.08, 8.3, 'o2')
    d.via(1, gp[0][0], 7.6, 'o1')
    d.via(1, NIX[0], 8.3, 'o2')
    d.via(1, gp[1][0], 8.3, 'o2')
    d.hw('M2', 48.4 + mg.sx(1), X_O1, 7.6, 'o1')
    d.stack(X_O1, 7.6, 2, 4, 'o1', end=0.4)
    d.vw('M4', X_O1, 7.6, O1_Y, 'o1')
    d.hw('M2', NIX[0], X_O2, 8.3, 'o2')
    d.stack(X_O2, 8.3, 2, 4, 'o2', end=0.4)
    d.vw('M4', X_O2, 8.3, 28.0, 'o2')
    d.box('TGO', 43.5, 0.95, 54.1, 6.8)
    # vdd well: MD1P (HV) and MD2P (LV), tie under the vdd rail
    md1 = Dev(d, 'pmosHV', 2, 0.5, 1, 53.0, 14.0)     # strips vdd | o3, gate o2
    p_md1 = md1.strap([0], 'lo', -0.30, 'o2')
    d.via(1, p_md1[0], p_md1[1], 'o2', lo=0)
    d.vw('M2', p_md1[0], 8.3, p_md1[1], 'o2')
    md2 = Dev(d, 'pmos', 1, 0.13, 1, 55.3, 14.0)      # strips vdd | out, gate o3
    md2.lbox('GatPoly', -0.45, -0.64, md2.gx(0)[1], -0.18)
    p_md2 = md2.P2(-0.30, -0.41)
    d.sq('Cont', p_md2[0], p_md2[1], 0.16)
    d.sq('M1', p_md2[0], p_md2[1], 0.3, 'o3')
    VT = (16.95, 17.25)
    d.ntap(53.0, VT[0], 56.11, VT[1], 'vdd')
    for x in (53.6, 55.6):
        d.stack(x, 17.1, 1, 3, 'vdd', end=0.3)
    md1.ext(0, VT[0] - 14.0 + 0.1, 'vdd')
    md2.ext(0, VT[0] - 14.0 + 0.1, 'vdd')
    md1.ext(1, 12.3 - 14.0 - 0.15, 'o3')
    md2.ext(1, 11.5 - 14.0 - 0.15, 'out')
    d.box('M1', p_md2[0] - 0.08, 12.3, p_md2[0] + 0.08, p_md2[1], 'o3')
    d.box('NWell', 52.38, 13.38, 56.42, 17.5)
    d.box('TGO', 52.3, 13.2, 54.8, 16.62)
    mdn = Dev(d, 'nmos', 0.5, 0.13, 1, 57.0, 9.5)     # strips out | vss, gate o3
    mdn.lbox('GatPoly', -0.45, -0.64, mdn.gx(0)[1], -0.18)
    p_mdn = mdn.P2(-0.30, -0.41)
    d.sq('Cont', p_mdn[0], p_mdn[1], 0.16)
    d.sq('M1', p_mdn[0], p_mdn[1], 0.3, 'o3')
    d.box('M1', p_mdn[0] - 0.08, p_mdn[1], p_mdn[0] + 0.08, 12.3, 'o3')
    mdn.ext(0, 11.5 - 9.5 + 0.15, 'out')
    d.box('M1', 57.0 + mdn.sx(1) - 0.08, 9.6, W - 0.45, 9.9, 'vss')
    for x in (NIX[2], 53.0 + md1.sx(1), p_md2[0], p_mdn[0]):
        d.via(1, x, 12.3, 'o3')
    d.hw('M2', NIX[2], p_mdn[0], 12.3, 'o3')
    d.box('M1', NIX[2] - 0.15, 12.15, 53.0 + md1.sx(1) + 0.15, 12.45, 'o3')
    X_OUT = 56.5
    for x in (55.3 + md2.sx(1), 57.0 + mdn.sx(0)):
        d.via(1, x, 11.5, 'out')
    d.hw('M2', 55.3 + md2.sx(1), 57.0 + mdn.sx(0), 11.5, 'out')
    d.stack(X_OUT, 11.5, 2, 4, 'out', end=0.4)
    d.vw('M4', X_OUT, 0.35, 11.5, 'out')

    # ---------------------------------------------------------------- bottom pins (Metal3) with Via3 from the trunks
    for net, x in (('ibias', X_IB), ('inp', XGL), ('inn', XGR), ('out', X_OUT)):
        pin(net, x - 0.3, 0.0, x + 0.3, 0.7)
        d.via(3, x, 0.35, net, lo=0, hi=0.4)

    META.update(W=W, H=H, pins=pins, rails={k: [v[0], v[1]] for k, v in RAILS.items()},
                ring_activ=[0.3, 0.3, W - 0.3, H - 0.3])
    META['self_check'] = ['%s %s %s / %s %s' % b for b in d.check()]
    return top


# =============================================================================================
def write_cdl(path):
    lines = open(SCH).read().splitlines()
    i0 = [i for i, s in enumerate(lines) if s.startswith('.subckt r1_safe_cmp ')][0]
    i1 = [i for i, s in enumerate(lines) if s.startswith('.ends r1_safe_cmp')][0]
    out = ['* r1s_cmp LVS reference netlist, written by layout/r1_safe_cmp_cell.py from schematic/r1_safe.spice',
           '* (netlist of record, subckt r1_safe_cmp). Format conversion only: X -> M/R, w = total width (w*m),',
           '* ng / mm_ok dropped, rppd substrate terminal kept (vss). Layout dummies (all terminals on one net) are not',
           '* listed: the PDK LVS extraction drops such devices.',
           '.subckt r1s_cmp inp inn refp refn out ibias vdda vdd vss']
    ndev = 0
    for s in lines[i0 + 1:i1]:
        s = s.strip()
        if not s or s.startswith('*'):
            continue
        f = s.split()
        prm = dict(p.split('=') for p in f if '=' in p)
        if f[5] in ('sg13_hv_pmos', 'sg13_hv_nmos', 'sg13_lv_pmos', 'sg13_lv_nmos'):
            w = float(prm['w'].rstrip('u')) * int(prm.get('m', '1'))
            out.append('M%s %s %s %s %s %s w=%gu l=%s m=1' % (f[0][1:], f[1], f[2], f[3], f[4], f[5], w, prm['l']))
        elif f[4] == 'rppd':
            out.append('R%s %s %s %s rppd w=%s l=%s m=1 b=0' % (f[0][1:], f[1], f[2], f[3], prm['w'], prm['l']))
        else:
            raise SystemExit('unhandled line: ' + s)
        ndev += 1
    # The layout dummies (pair A: 2 x pmosHV 5/2 on ta, pair B: 2 x 5/2 on tb, tail: 1 x 4/2 on vdda, all
    # terminals on one net) are dropped by the PDK LVS extraction (devices with all terminals on one net are not
    # kept in the extracted netlist, run cmpcell-dev-02), so they are not listed here either.
    dummies = []
    out += dummies
    out.append('.ends r1s_cmp')
    with open(path, 'w') as fh:
        fh.write('\n'.join(out) + '\n')
    return ndev, len(dummies)


def main(outdir):
    ly = pya.Layout()
    ly.dbu = 0.001
    top = build_cmp(ly)
    for c in list(ly.each_cell()):
        if c.cell_index() != top.cell_index() and c.parent_cells() == 0:
            ly.delete_cell(c.cell_index())
    os.makedirs(outdir, exist_ok=True)
    gds = os.path.join(outdir, 'r1s_cmp.gds')
    ly.write(gds)
    ndev, ndum = write_cdl(os.path.join(outdir, 'r1s_cmp_lvs.cdl'))
    META.update(devices_netlist=ndev, cdl_dummy_lines=ndum,
                layout_dummies=dict(pmosHV_5_2_pair_A_on_ta=2, pmosHV_5_2_pair_B_on_tb=2, pmosHV_4_2_tail_on_vdda=1,
                                    rppd_strips_no_RES=2,
                                    note='MOS dummies have all terminals on one net; the PDK LVS extraction drops '
                                         'them, so the CDL lists none'),
                resistor_segments=dict(per_resistor=4, length_um=77.0, total_um=308.0),
                netlist_of_record='designs/r1-joint/blocks/r1_safe/schematic/r1_safe.spice (subckt r1_safe_cmp)')
    with open(os.path.join(HERE, 'r1_safe_cmp_cell_meta.json'), 'w') as fh:
        json.dump(META, fh, indent=1)
    print('wrote', gds, 'bbox', top.dbbox(), 'self-check findings:', len(META['self_check']))
    for b in META['self_check'][:40]:
        print('  CHECK', b)


if __name__ == '__main__' or 'out' in globals():
    main(globals().get('out', HERE))
