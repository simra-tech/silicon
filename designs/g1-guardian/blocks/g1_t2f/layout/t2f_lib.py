#!/usr/bin/env python3
"""Drawing helpers for the G1_T2F layout generator (KLayout 0.30.9 batch Python, PDK PCells from the
SG13_dev library, PDK commit 8437402). Coordinates in um, database unit 1 nm, everything snapped to
the 5 nm rule grid.

PCell geometry, read from the instantiated cells (build/g1_t2f_lay/probe.py in this working tree):
  MOS PCells (nmos, pmos, nmosHV, pmosHV; w = total width, ng fingers of w/ng, max 10 um per finger),
    origin at the Activ lower-left corner:
    Activ x 0..act_w, y 0..wf;  act_w = 0.68 + ng*l + (ng-1)*0.38;  wf = w/ng
    gate i: GatPoly x = 0.34 + i*(l+0.38) .. +l, y -0.18 .. wf+0.18
    S/D Metal1 strips 0.16 wide, full finger height, centred at x = 0.15 + j*(l+0.38), j = 0..ng
    pmosHV: NWell, ThickGateOx and pSD(-0.18/-0.40) around Activ, NWell/TGO -0.62; nmosHV: TGO -0.27/-0.52;
    pmos: NWell -0.31, pSD -0.18/-0.30; nmos: nothing beyond Activ/GatPoly/Cont/Metal1
  npn13G2 (Nx=1), origin at the emitter centre: C Metal1 pad (+-0.925, 1.01..1.25), B Metal1 pad
    (+-0.975, -1.26..-1.02), E Metal2 pad (+-0.925, -0.785..0.77) over a Metal1 pad (+-0.35) with 8 Via1;
    p+ ring Activ outer (+-3.15, -3.13..3.58) inner (+-2.65, -2.63..3.08), pSD to (+-3.35, -3.33..3.78);
    nBuLay (26/0) +-2.45 x -2.43..2.88
  rppd (Calculate=R): poly body x 0..w, y 0..l; Metal1 heads x 0.02..w-0.02, y -0.43..-0.13 and l+0.13..l+0.43;
    pSD -0.18 (x) / -0.61 (y); SalBlock and EXTBlock -0.2 (x)
  cmim (Calculate=C): MIM (36/0) 0..w x 0..l, Metal5 plate -0.6 around, TopMetal1 plate 0.14 inside, Vmim array
Rule values used (sg13g2_tech_mod.json): Act.b 0.21, Gat.b 0.18, Gat.c 0.18, Cnt.a 0.16, Cnt.b 0.18,
Cnt.c/d 0.07, Cnt.e 0.14, M1.a/b 0.16/0.18 (M1.e 0.22 next to lines wider than 0.3), M1.d area 0.09,
V1.a/b 0.19/0.22, V1.c/c1 0.01/0.05, Mn.a/b 0.20/0.21 (Mn.e 0.24 next to lines wider than 0.39,
Mn.f 0.60 next to lines wider than 10), Vn.c/c1 0.005/0.05, NW.a/b 0.62, NW.b1 1.80 (different nets),
NW.c1/d1/e1/f1 0.62 inside ThickGateOx, NW.e/f 0.24 outside, TGO.a/b 0.27, TGO.c/d 0.34, TGO.e 0.86,
pSD.a/b 0.31, pSD.c1 0.03, pSD.d 0.18, pSD.i1/j1 0.40, NBL.d 2.2, NBL.e 1.0, NBL.f 0.5,
TV1.a/b 0.42, TV1.c 0.10, TV1.d 0.42, TM1.a/b 1.64, MIM.b/e 0.60, Sal.a/b 0.42, EXTB.b 0.31.
"""
import sys
K = '/foss/pdks/ihp-sg13g2/libs.tech/klayout/python'
for p in [K, K + '/pycell4klayout-api/source/python']:
    sys.path.insert(0, p)
import pya
import sg13g2_pycell_lib  # noqa: F401  registers library SG13_dev

LIB = pya.Library.library_by_name('SG13_dev', 'sg13g2')
LAYERS = {
    'Activ': (1, 0), 'GatPoly': (5, 0), 'Cont': (6, 0), 'pSD': (14, 0), 'NWell': (31, 0), 'TGO': (44, 0),
    'M1': (8, 0), 'M1pin': (8, 2), 'M1txt': (8, 25), 'Via1': (19, 0),
    'M2': (10, 0), 'M2pin': (10, 2), 'M2txt': (10, 25), 'Via2': (29, 0),
    'M3': (30, 0), 'M3pin': (30, 2), 'M3txt': (30, 25), 'Via3': (49, 0),
    'M4': (50, 0), 'M4pin': (50, 2), 'M4txt': (50, 25), 'Via4': (66, 0),
    'M5': (67, 0), 'M5pin': (67, 2), 'M5txt': (67, 25), 'TV1': (125, 0),
    'TM1': (126, 0), 'TM1pin': (126, 2), 'TM1txt': (126, 25), 'MIM': (36, 0), 'Vmim': (129, 0),
    'prBoundary': (189, 4),
}
METALS = ['M1', 'M2', 'M3', 'M4', 'M5', 'TM1']
VIAS = {('M1', 'M2'): 'Via1', ('M2', 'M3'): 'Via2', ('M3', 'M4'): 'Via3', ('M4', 'M5'): 'Via4', ('M5', 'TM1'): 'TV1'}
CONT, CPITCH = 0.16, 0.34          # contact size and pitch
VIA, VPITCH = 0.19, 0.42           # Via1..Via4 size and pitch
STUB_W = 0.20                      # Metal2 vertical stubs (0.44 um column pitch leaves 0.24 space)
TRACK_W = 0.30                     # Metal3 horizontal tracks (0.6 um pitch)
TRACK_P = 0.60
GATE_PAD = 0.30                    # Metal1 pad on a gate contact (area >= 0.09 um^2)


def g(v):
    """snap to the 5 nm grid, return integer nm"""
    return int(round(v * 200.0)) * 5


class Draw:
    """Shape insertion into one cell with layer bookkeeping and a record of Metal2 stubs and Metal3
    tracks for a same-layer overlap self-check (net-aware) before the real DRC/LVS."""
    def __init__(self, ly, cell):
        self.ly, self.cell = ly, cell
        self.L = {n: ly.layer(*v) for n, v in LAYERS.items()}
        self.segs = []          # (layer, net, x1, y1, x2, y2) for the self-check

    # ---------------------------------------------------------------- primitives
    def box(self, layer, x1, y1, x2, y2, net=None):
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        self.cell.shapes(self.L[layer]).insert(pya.Box(g(x1), g(y1), g(x2), g(y2)))
        if net is not None and layer in ('M2', 'M3'):
            self.segs.append((layer, net, x1, y1, x2, y2))

    def square(self, layer, cx, cy, size, net=None):
        self.box(layer, cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2, net)

    def ring(self, layer, x1, y1, x2, y2, w):
        """ring of width w just outside the box (x1,y1,x2,y2)"""
        outer = pya.Polygon(pya.Box(g(x1 - w), g(y1 - w), g(x2 + w), g(y2 + w)))
        outer.insert_hole(pya.Box(g(x1), g(y1), g(x2), g(y2)))
        self.cell.shapes(self.L[layer]).insert(outer)

    def label(self, layer, x, y, text):
        t = pya.Text(text, pya.Trans(pya.Point(g(x), g(y))))
        t.size = g(0.25)
        self.cell.shapes(self.L[layer]).insert(t)

    def pin(self, layer, x1, y1, x2, y2, name):
        """pin shape (datatype 2) + text (datatype 25) + drawing on `layer`"""
        self.box(layer, x1, y1, x2, y2, name)
        self.box(layer + 'pin', x1, y1, x2, y2)
        self.label(layer + 'txt', (x1 + x2) / 2, (y1 + y2) / 2, name)

    def hwire(self, layer, x1, x2, y, w=TRACK_W, net=None):
        self.box(layer, min(x1, x2) - w / 2, y - w / 2, max(x1, x2) + w / 2, y + w / 2, net)

    def vwire(self, layer, x, y1, y2, w=STUB_W, net=None):
        self.box(layer, x - w / 2, min(y1, y2) - w / 2, x + w / 2, max(y1, y2) + w / 2, net)

    def via(self, x, y, l1, l2, pad=0.30, nx=1, ny=1, net=None, pads=None):
        """via stack between metals l1 and l2 (either order) centred at (x, y); nx x ny vias per level;
        square pads of size `pad` (plus the via array extent) on every metal touched, overridable per
        metal with pads={'M2': (w, h)}. TopVia1 gets the 1.64 TopMetal1 pad it needs."""
        i1, i2 = METALS.index(l1), METALS.index(l2)
        if i1 > i2:
            i1, i2 = i2, i1
        pads = pads or {}
        for i in range(i1, i2 + 1):
            m = METALS[i]
            pw, ph = pads.get(m, (pad, pad))
            pw = max(pw, VIA + 0.01 + (nx - 1) * VPITCH)
            ph = max(ph, VIA + 0.10 + (ny - 1) * VPITCH)
            if m == 'TM1':
                self.square('TM1', x, y, max(pw, 1.64), net)
            elif m == 'M5' and METALS[i2] == 'TM1' and i == i2 - 1:
                self.square('M5', x, y, max(pw, 0.42 + 0.20), net)
            else:
                self.box(m, x - pw / 2, y - ph / 2, x + pw / 2, y + ph / 2, net)
        for i in range(i1, i2):
            v = VIAS[(METALS[i], METALS[i + 1])]
            if v == 'TV1':
                self.square('TV1', x, y, 0.42)
            else:
                for a in range(nx):
                    for b in range(ny):
                        self.square(v, x + (a - (nx - 1) / 2) * VPITCH, y + (b - (ny - 1) / 2) * VPITCH, VIA)

    def cont_row(self, x1, x2, y):
        """contacts at 0.34 pitch centred between x1 and x2 (contact centres inside [x1, x2])"""
        n = int((x2 - x1) // CPITCH) + 1
        x0 = (x1 + x2) / 2 - (n - 1) * CPITCH / 2
        for i in range(n):
            self.square('Cont', x0 + i * CPITCH, y, CONT)

    def cont_col(self, y1, y2, x):
        n = int((y2 - y1) // CPITCH) + 1
        y0 = (y1 + y2) / 2 - (n - 1) * CPITCH / 2
        for i in range(n):
            self.square('Cont', x, y0 + i * CPITCH, CONT)

    def tap_strip(self, x1, x2, y1, y2, ptype, m1w=None):
        """substrate (ptype) or well tie strip: Activ (+pSD 0.03 around for p type), one contact row or
        column, Metal1 over it (m1w wide, centred)."""
        self.box('Activ', x1, y1, x2, y2)
        if ptype:
            self.box('pSD', x1 - 0.03, y1 - 0.03, x2 + 0.03, y2 + 0.03)
        if x2 - x1 >= y2 - y1:
            yc = (y1 + y2) / 2
            self.cont_row(x1 + 0.15, x2 - 0.15, yc)
            h = m1w or (y2 - y1)
            self.box('M1', x1, yc - h / 2, x2, yc + h / 2)
        else:
            xc = (x1 + x2) / 2
            self.cont_col(y1 + 0.15, y2 - 0.15, xc)
            h = m1w or (x2 - x1)
            self.box('M1', xc - h / 2, y1, xc + h / 2, y2)

    def guard_ring(self, x1, y1, x2, y2, w=0.40, ptype=True, m1w=0.30):
        """p+ (or n+) tie ring of width w just outside the box, contacts, Metal1 ring of width m1w
        centred on the ring. Returns the centre-line coordinates (cx1, cy1, cx2, cy2)."""
        self.ring('Activ', x1, y1, x2, y2, w)
        if ptype:
            self.ring('pSD', x1 + 0.03, y1 + 0.03, x2 - 0.03, y2 - 0.03, w + 0.06)
        c = w / 2
        cx1, cx2, cy1, cy2 = x1 - c, x2 + c, y1 - c, y2 + c
        self.cont_row(cx1, cx2, cy1)
        self.cont_row(cx1, cx2, cy2)
        self.cont_col(cy1 + CPITCH, cy2 - CPITCH, cx1)
        self.cont_col(cy1 + CPITCH, cy2 - CPITCH, cx2)
        hw = m1w / 2
        self.ring('M1', cx1 + hw, cy1 + hw, cx2 - hw, cy2 - hw, m1w)
        return (cx1, cy1, cx2, cy2)

    def pcell(self, name, params, x, y, rot=0):
        pcv = LIB.layout().add_pcell_variant(LIB.layout().pcell_id(name), params)
        c = self.ly.cell(self.ly.add_lib_cell(LIB, pcv))
        self.cell.insert(pya.CellInstArray(c.cell_index(), pya.Trans(rot, False, pya.Point(g(x), g(y)))))
        return c

    # ---------------------------------------------------------------- routing helpers
    def stub(self, x, y_from, y_to, net, lower='M1'):
        """Metal2 vertical (STUB_W) from a pin at (x, y_from) on `lower` (Metal1 pad + Via1, or nothing if
        lower == 'M2') to a Metal3 track at y_to (Via2 there). Ends extend 0.15 beyond the via centres."""
        m2 = {'M2': (STUB_W, 0.30)}
        if lower == 'M1':
            self.via(x, y_from, 'M1', 'M2', pad=0.30, net=net, pads=m2)
        self.via(x, y_to, 'M2', 'M3', pad=0.30, net=net, pads=m2)
        y1, y2 = min(y_from, y_to), max(y_from, y_to)
        self.box('M2', x - STUB_W / 2, y1 - 0.15, x + STUB_W / 2, y2 + 0.15, net)

    def track(self, y, x1, x2, net, w=TRACK_W, label=True):
        """Metal3 horizontal track between x1 and x2 at y, with the net name as a Metal3 text at its
        midpoint (internal labels name the nets in the LVS/PEX extraction; they do not disturb the
        compare)."""
        self.box('M3', min(x1, x2) - w / 2, y - w / 2, max(x1, x2) + w / 2, y + w / 2, net)
        if label:
            self.label('M3txt', (x1 + x2) / 2, y, net)

    def check_overlaps(self, min_space=0.20):
        """report Metal2/Metal3 segments of different nets closer than min_space (same layer)"""
        bad = 0
        for i in range(len(self.segs)):
            la, na, ax1, ay1, ax2, ay2 = self.segs[i]
            for j in range(i + 1, len(self.segs)):
                lb, nb, bx1, by1, bx2, by2 = self.segs[j]
                if la != lb or na == nb:
                    continue
                dx = max(bx1 - ax2, ax1 - bx2)
                dy = max(by1 - ay2, ay1 - by2)
                if dx < min_space - 1e-9 and dy < min_space - 1e-9:
                    print(f"SELF-CHECK {la}: {na} ({ax1:.2f},{ay1:.2f},{ax2:.2f},{ay2:.2f}) vs {nb} "
                          f"({bx1:.2f},{by1:.2f},{bx2:.2f},{by2:.2f}) gap dx={dx:.3f} dy={dy:.3f}")
                    bad += 1
        return bad


class Mos:
    """One MOS PCell instance (kind in nmos, pmos, nmosHV, pmosHV) with terminal geometry.
    w is the total width, ng the finger count (each finger w/ng high)."""
    def __init__(self, D, name, kind, w, l, ng, x, y):
        self.D, self.name, self.kind, self.w, self.l, self.ng, self.x, self.y = D, name, kind, w, l, ng, x, y
        D.pcell(kind, {'w': '%gu' % w, 'l': '%gu' % l, 'ng': ng}, x, y)
        self.wf = w / ng
        self.pitch = l + 0.38
        self.act_w = 0.68 + ng * l + (ng - 1) * 0.38
        self.hv = kind.endswith('HV')
        self.p = kind.startswith('p')

    def sx(self, j):              # centre x of S/D strip j (0..ng)
        return self.x + 0.15 + j * self.pitch

    def gx(self, i):              # centre x of gate i (0..ng-1)
        return self.x + 0.34 + self.l / 2 + i * self.pitch

    @property
    def x2(self):
        return self.x + self.act_w

    @property
    def y2(self):
        return self.y + self.wf

    def strip_to(self, j, y, w=0.16):
        """extend S/D strip j on Metal1 vertically to y (rail or bar connection)"""
        self.D.box('M1', self.sx(j) - w / 2, min(self.y, y), self.sx(j) + w / 2, max(self.y2, y))

    def strip_pad(self, j, yv, size=0.30):
        """Metal1 pad on strip j at height yv (for a Via1); returns (x, y)"""
        self.D.square('M1', self.sx(j), yv, size)
        return (self.sx(j), yv)

    def gate_pad(self, i, side, ext=0.62, pw=None):
        """poly extension beyond the Activ edge on `side` ('top'/'bottom') with one contact and a Metal1
        pad; returns the contact centre (x, y)."""
        gx = self.gx(i)
        pw = pw or max(GATE_PAD, self.l)
        if side == 'bottom':
            yc = self.y - 0.40
            self.D.box('GatPoly', gx - pw / 2, self.y - ext, gx + pw / 2, self.y - 0.17)
        else:
            yc = self.y2 + 0.40
            self.D.box('GatPoly', gx - pw / 2, self.y2 + 0.17, gx + pw / 2, self.y2 + ext)
        self.D.square('Cont', gx, yc, CONT)
        self.D.square('M1', gx, yc, GATE_PAD)
        return (gx, yc)

    def gate_bridge(self, i, other, pw=None):
        """poly bridge between gate i of self and gate i of `other` (same x, `other` above self)"""
        gx = self.gx(i)
        pw = pw or max(GATE_PAD, min(self.l, other.l))
        self.D.box('GatPoly', gx - pw / 2, self.y2 + 0.17, gx + pw / 2, other.y - 0.17)

    def gate_contact_at(self, i, yc):
        """contact on the poly at (gx, yc) with a Metal1 pad (poly must already be there)"""
        gx = self.gx(i)
        self.D.square('Cont', gx, yc, CONT)
        self.D.square('M1', gx, yc, GATE_PAD)
        return (gx, yc)


class Hbt:
    """npn13G2 PCell (Nx=1) at emitter centre (cx, cy). Its p+ ring is contacted (Cont + Metal1 ring
    segments on the ring centre lines x = cx +- 2.90, y = cy - 2.88 / cy + 3.33). Terminals:
    C on Metal2 going up from the collector pad, B on Metal2 going down from the base pad, E on the
    PCell's Metal2 pad (x +- 0.925, y -0.785 .. 0.77). `dummy` ties C, B and E to the ring on Metal1."""
    def __init__(self, D, name, cx, cy, dummy=False):
        self.D, self.name, self.cx, self.cy = D, name, cx, cy
        D.pcell('npn13G2', {'Nx': 1}, cx, cy)
        xl, xr, yb, yt = cx - 2.90, cx + 2.90, cy - 2.88, cy + 3.33
        self.ring = (xl, yb, xr, yt)
        D.cont_row(xl + 0.34, xr - 0.34, yb)
        D.cont_row(xl + 0.34, xr - 0.34, yt)
        D.cont_col(yb + 0.34, yt - 0.34, xl)
        D.cont_col(yb + 0.34, yt - 0.34, xr)
        hw = 0.15
        D.box('M1', xl - hw, yb - hw, xr + hw, yb + hw)
        D.box('M1', xl - hw, yt - hw, xr + hw, yt + hw)
        D.box('M1', xl - hw, yb - hw, xl + hw, yt + hw)
        D.box('M1', xr - hw, yb - hw, xr + hw, yt + hw)
        self.c_pad = (cx - 0.925, cy + 1.01, cx + 0.925, cy + 1.25)
        self.b_pad = (cx - 0.975, cy - 1.26, cx + 0.975, cy - 1.02)
        if dummy:
            # collector and base pads to the ring on Metal1, emitter Metal1 pad sideways to the ring
            D.box('M1', cx - 0.15, cy + 1.01, cx + 0.15, yt)
            D.box('M1', cx - 0.15, yb, cx + 0.15, cy - 1.02)
            D.box('M1', cx - 0.35, cy - 0.10, xr, cy + 0.10)
            return
        # collector: widen the Metal1 pad for three Via1, Metal2 pad (0.24 above the emitter Metal2 pad,
        # rule Mn.e), Metal2 strip upward starts at self.c
        D.box('M1', cx - 0.925, cy + 0.98, cx + 0.925, cy + 1.28)
        for dx in (-0.45, 0.0, 0.45):
            D.square('Via1', cx + dx, cy + 1.13, VIA)
        D.box('M2', cx - 0.70, cy + 1.01, cx + 0.70, cy + 1.28)
        # base: same, downward (Metal2 pad kept 0.265 below the emitter Metal2 pad)
        D.box('M1', cx - 0.975, cy - 1.30, cx + 0.975, cy - 1.00)
        for dx in (-0.45, 0.0, 0.45):
            D.square('Via1', cx + dx, cy - 1.15, VIA)
        D.box('M2', cx - 0.70, cy - 1.30, cx + 0.70, cy - 1.05)

    @property
    def c(self):
        return (self.cx, self.cy + 1.13)

    @property
    def b(self):
        return (self.cx, self.cy - 1.15)

    @property
    def e(self):
        return (self.cx, self.cy)


class Row:
    """HV CMOS logic row. NMOS PCells stand with their Activ bottom at yn, PMOS PCells with their Activ
    bottom at yp = yn + hn + GAP (hn, hp = tallest NMOS / PMOS of the row). Every cell is ng fingers
    wide; its columns are x = 0.15 + 0.44 k from the cell origin (even k: S/D strips, odd k: gates).
    Gate contacts sit on a poly bridge between the two devices at y_gate; cell outputs are joined on a
    Metal1 bar at y_bar; the pins leave on Metal2 stubs (STUB_W) straight down to Metal3 tracks in the
    channel below the vss rail: track k is at yn - 2.2 - 0.6 k.
    Rails: vss (p+ tie strip, Metal1 0.6) at yn - 1.4; vdd (n+ tie strip inside the well) at yp + hp + 1.4.
    finish() draws the rails, the n-well and the ThickGateOx box for the whole row."""
    GAP = 2.0

    def __init__(self, D, x0, yn, hn, hp, name, l=0.5, hv=True):
        self.D, self.x0, self.x, self.yn, self.hn, self.hp, self.name, self.l = D, x0, x0, yn, hn, hp, name, l
        self.hv = hv
        self.nkind, self.pkind = ('nmosHV', 'pmosHV') if hv else ('nmos', 'pmos')
        self.yp = yn + hn + self.GAP
        self.yc = yn + hn + self.GAP / 2
        self.y_gate = self.yc - 0.30
        self.y_bar = self.yc + 0.70
        self.vss_y = yn - 1.4
        self.vdd_y = self.yp + hp + 1.4
        self.pins = {}          # net -> list of (x, y, lower_layer) pin points for stubs
        self.cells = []

    def track_y(self, k):
        return self.yn - 2.2 - TRACK_P * k

    def col(self, x, k):
        return x + 0.15 + 0.44 * k

    def add_pin(self, net, x, y, lower='M1'):
        self.pins.setdefault(net, []).append((x, y, lower))

    def place(self, name, ng, wn, wp, n_strips, p_strips, gates, out=None, pitch=0.60):
        """Generic cell: an NMOS (wn total, may be None) and a PMOS (wp total, may be None) with ng
        fingers each. n_strips / p_strips: list of ng+1 net names per S/D strip ('vss'/'vdd' -> rail,
        None -> unconnected); gates: list of ng net names (bridge + contact + stub). `out`: the net
        joined by the Metal1 bar between the two devices; its Metal2 stub column is the first P strip
        carrying `out` (or the N strip if there is no PMOS). All other named strips get a pin at the
        strip (a stub column of their own, going down for NMOS strips, up for PMOS strips)."""
        D, x = self.D, self.x
        n = Mos(D, name + 'N', self.nkind, wn, self.l, ng, x, self.yn) if wn else None
        p = Mos(D, name + 'P', self.pkind, wp, self.l, ng, x, self.yp) if wp else None
        dev = n or p
        # rails
        if n:
            for j, net in enumerate(n_strips):
                if net == 'vss':
                    n.strip_to(j, self.vss_y)
        if p:
            for j, net in enumerate(p_strips):
                if net == 'vdd':
                    p.strip_to(j, self.vdd_y)
        # output bar
        if out is not None:
            xs = []
            if n:
                for j, net in enumerate(n_strips):
                    if net == out:
                        n.strip_to(j, self.y_bar)
                        xs.append(n.sx(j))
            if p:
                for j, net in enumerate(p_strips):
                    if net == out:
                        p.strip_to(j, self.y_bar)
                        xs.append(p.sx(j))
            xa, xb = min(xs), max(xs)
            D.box('M1', xa - 0.08, self.y_bar - 0.10, xb + 0.08, self.y_bar + 0.10)
            xo = None
            if p:
                for j, net in enumerate(p_strips):
                    if net == out:
                        xo = p.sx(j)
                        break
            if xo is None:
                xo = xs[0]
            self.add_pin(out, xo, self.y_bar)
        # other signal strips: pin on the strip itself (mid height)
        if n:
            for j, net in enumerate(n_strips):
                if net and net not in ('vss', out):
                    self.add_pin(net, n.sx(j), self.yn + 0.40)
        if p:
            for j, net in enumerate(p_strips):
                if net and net not in ('vdd', out):
                    self.add_pin(net, p.sx(j), self.yp + p.wf - 0.40)
        # gates: poly bridge (or extension) and contact at y_gate
        for i, net in enumerate(gates):
            if n and p:
                n.gate_bridge(i, p)
            elif n:
                D.box('GatPoly', n.gx(i) - GATE_PAD / 2, n.y2 + 0.17, n.gx(i) + GATE_PAD / 2, self.y_gate + 0.18)
            else:
                D.box('GatPoly', p.gx(i) - GATE_PAD / 2, self.y_gate - 0.18, p.gx(i) + GATE_PAD / 2, p.y - 0.17)
            gx, gy = dev.gate_contact_at(i, self.y_gate)
            if net:
                self.add_pin(net, gx, gy)
        self.cells.append((name, n, p))
        self.x += dev.act_w + pitch
        return n, p

    def inv(self, name, inp, out, wn=1.0, wp=2.0):
        return self.place(name, 1, wn, wp, ['vss', out], ['vdd', out], [inp], out)

    def nand2(self, name, a, b, out, wn=2.0, wp=2.0):
        # NMOS chain from vss: b, a (input a next to the output, as in the schematic's series order)
        return self.place(name, 2, 2 * wn, 2 * wp, ['vss', None, out], ['vdd', out, 'vdd'], [b, a], out)

    def nand3(self, name, a, b, c, out, wn=3.0, wp=2.0):
        return self.place(name, 3, 3 * wn, 3 * wp, ['vss', None, None, out], ['vdd', out, 'vdd', out], [c, b, a], out)

    def finish(self, margin=0.60):
        """rails, n-well and ThickGateOx for the whole row; returns (x1, x2)"""
        D = self.D
        x1, x2 = self.x0 - margin, self.x - 0.60 + margin
        D.tap_strip(x1, x2, self.yn - 1.60, self.yn - 1.20, True, m1w=0.60)
        D.tap_strip(x1, x2, self.yp + self.hp + 1.20, self.yp + self.hp + 1.60, False, m1w=0.60)
        if self.hv:
            D.box('NWell', x1 - 0.30, self.yp - 0.62, x2 + 0.30, self.yp + self.hp + 2.0)
            D.box('TGO', x1 - 0.30, self.yn - 0.52, x2 + 0.30, self.yp + self.hp + 0.62)
            if any(p for _, _, p in self.cells):
                D.box('pSD', x1 + 0.42, self.yp - 0.40, x2 - 0.42, self.yp + self.hp + 0.40)   # merged PMOS pSD
        else:
            D.box('NWell', x1 - 0.30, self.yp - 0.31, x2 + 0.30, self.yp + self.hp + 2.0)
            if any(p for _, _, p in self.cells):
                D.box('pSD', x1 + 0.42, self.yp - 0.30, x2 - 0.42, self.yp + self.hp + 0.30)
        self.x1, self.x2 = x1, x2
        return x1, x2

    def stubs_to(self, net, k, x_ext=None):
        """Metal2 stubs from every pin of `net` down to track k and the Metal3 track itself, spanning
        the pins (extended to x_ext if given). Returns the track y."""
        y = self.track_y(k)
        xs = [x for x, _, _ in self.pins.get(net, [])]
        if x_ext is not None:
            xs = xs + list(x_ext if isinstance(x_ext, (list, tuple)) else [x_ext])
        for x, yp, lower in self.pins.get(net, []):
            self.D.stub(x, yp, y, net, lower)
        if len(xs) > 1:
            self.D.track(y, min(xs), max(xs), net)
        return y
