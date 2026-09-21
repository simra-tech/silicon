#!/usr/bin/env python3
"""Shared KLayout (0.30.9) Python helpers for the G1 analog macro generators (G1_SENSE, G1_GATE).

Runs inside the pinned container (flow/run.sh) where the PDK PCell library `SG13_dev` is on the
Python path. Everything is drawn on the SG13G2 GDS layers; the rule values quoted in comments are
from the PDK DRC deck at commit 8437402 (libs.tech/klayout/tech/drc, values in
python/sg13g2_pycell_lib/sg13g2_tech_mod.json).

PCell geometry relied on (probed by instantiating the cells, build/g1_sense_lay/probe_geo.py):
  nmosHV/pmosHV/nmos/pmos (w total, l, ng fingers, finger height wf = w/ng, max 10 um per finger
  for the HV cells): Activ (0,0)-(ng*(l+0.38)+0.30, wf); source/drain Metal1 strips 0.16 wide at
  x = 0.07..0.23 + k*(l+0.38), k = 0..ng, y = 0..wf, contacts 0.16 at 0.34 pitch inside them;
  gate k: GatPoly x = 0.34..0.34+l + k*(l+0.38), y = -0.18..wf+0.18.
  pmosHV adds pSD (Activ + 0.18 in x, + 0.40 in y), NWell and ThickGateOx (Activ + 0.62);
  nmosHV adds ThickGateOx (Activ + 0.27 in x, + 0.52 in y); pmos (LV): pSD +0.18/+0.30, NWell +0.31.
  rppd (Calculate=R, w, l): body PolyRes+SalBlock (0,0)-(w,l) (the body poly is on PolyRes 128/0),
  GatPoly heads y = -0.43..0 and l..l+0.43 with a contact bar at y = -0.36..-0.20 / l+0.20..l+0.36
  and Metal1 heads x = 0.02..w-0.02, y = -0.43..-0.13 / l+0.13..l+0.43; pSD/EXTBlock 0.18 (x) and
  to -0.61/l+0.61 (y), SalBlock -0.2..w+0.2 in x.
  cmim (Calculate=C, w, l): MIM (0,0)-(w,l), Metal5 bottom plate -0.6..w+0.6, TopMetal1 top plate
  0.16..w-0.16 with the Vmim array.
LVS deck facts used here: net names come from text on datatype 25 of the metal layers; the pin
datatype 2 is for the LEF only; no text may read "well" or "sub!" (tap-device markers); p+ Activ in
the substrate is the substrate tie (pwell net), n+ Activ in NWell is the well tie.
"""
import os, sys
K = '/foss/pdks/ihp-sg13g2/libs.tech/klayout/python'
for p in [K, K + '/pycell4klayout-api/source/python']:
    if p not in sys.path:
        sys.path.insert(0, p)
import pya
import sg13g2_pycell_lib  # noqa: registers library SG13_dev (technology sg13g2)

LIB = pya.Library.library_by_name('SG13_dev', 'sg13g2')

LAYERS = {
    'Activ': (1, 0), 'GatPoly': (5, 0), 'Cont': (6, 0), 'nSD': (7, 0),
    'M1': (8, 0), 'M1pin': (8, 2), 'M1txt': (8, 25),
    'M2': (10, 0), 'M2pin': (10, 2), 'M2txt': (10, 25),
    'pSD': (14, 0), 'Via1': (19, 0), 'SalBlock': (28, 0), 'Via2': (29, 0),
    'M3': (30, 0), 'M3pin': (30, 2), 'M3txt': (30, 25),
    'NWell': (31, 0), 'MIM': (36, 0), 'TGO': (44, 0), 'Via3': (49, 0),
    'M4': (50, 0), 'M4pin': (50, 2), 'M4txt': (50, 25), 'Via4': (66, 0),
    'M5': (67, 0), 'M5pin': (67, 2), 'M5txt': (67, 25),
    'EXTBlock': (111, 0), 'TV1': (125, 0), 'TM1': (126, 0), 'TM1pin': (126, 2), 'TM1txt': (126, 25),
    'PolyRes': (128, 0), 'Vmim': (129, 0), 'prBoundary': (189, 0), 'prBoundary4': (189, 4),
    'NoMetFiller': (160, 0), 'EdgeSeal': (39, 0),
}
NOFILL_LAYERS = [(1, 23), (5, 23), (8, 23), (10, 23), (30, 23), (50, 23), (67, 23), (126, 23), (134, 23)]
METALS = ['M1', 'M2', 'M3', 'M4', 'M5', 'TM1']
VIAS = {('M1', 'M2'): 'Via1', ('M2', 'M3'): 'Via2', ('M3', 'M4'): 'Via3', ('M4', 'M5'): 'Via4', ('M5', 'TM1'): 'TV1'}

GRID = 0.005
CONT, CPITCH = 0.16, 0.34      # Cnt.a, Cnt.a + Cnt.b
VIA, VPITCH, VENC = 0.19, 0.50, 0.105  # V1.a/Vn.a; pitch > V1.b1 0.29 + 0.19 (any array size); > V1.c1 0.05
PAD = VIA + 2 * VENC           # 0.40 landing pad: 0.16 um2 > Mn.d min metal area 0.144 for an isolated pad
TV1, TV1_M5, TV1_TM1 = 0.42, 0.12, 0.45  # TV1.a, > TV1.c 0.10, > TV1.d 0.42
PITCH_EXTRA = 0.38             # finger pitch = l + 0.38 in the MOS PCells
HV_MAX_WF = 10.0               # pmosHV/nmosHV refuse fingers wider than 10 um (probe_w2.py)


def um(v):
    return int(round(v * 1000))


def snap(v):
    return round(v / GRID) * GRID


class Draw:
    """Thin drawing wrapper on one cell (all coordinates in um)."""

    def __init__(self, ly, cell):
        self.ly, self.cell = ly, cell
        self.L = {n: ly.layer(*v) for n, v in LAYERS.items()}

    # ---- primitives -------------------------------------------------------------------------
    def box(self, layer, x1, y1, x2, y2):
        if x2 < x1: x1, x2 = x2, x1
        if y2 < y1: y1, y2 = y2, y1
        self.cell.shapes(self.L[layer]).insert(pya.Box(um(x1), um(y1), um(x2), um(y2)))

    def sq(self, layer, cx, cy, size):
        self.box(layer, cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2)

    def label(self, layer, x, y, text, size=0.3):
        t = pya.Text(text, pya.Trans(pya.Point(um(x), um(y))))
        t.size = um(size)
        self.cell.shapes(self.L[layer]).insert(t)

    def pin(self, layer, x1, y1, x2, y2, name):
        """Pin: drawing shape + pin-purpose shape + text label at the centre (layer = 'M1'..'TM1')."""
        self.box(layer, x1, y1, x2, y2)
        self.box(layer + 'pin', x1, y1, x2, y2)
        self.label(layer + 'txt', (x1 + x2) / 2, (y1 + y2) / 2, name)

    def ring(self, layer, x1, y1, x2, y2, w):
        """closed ring between the inner box (x1,y1,x2,y2) and the box grown by w."""
        outer = pya.Polygon(pya.Box(um(x1 - w), um(y1 - w), um(x2 + w), um(y2 + w)))
        outer.insert_hole(pya.Box(um(x1), um(y1), um(x2), um(y2)))
        self.cell.shapes(self.L[layer]).insert(outer)

    def wire(self, layer, pts, w):
        """Manhattan wire through pts [(x,y),...]; each segment a box grown by w/2 at both ends."""
        for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
            if abs(xa - xb) < 1e-9:
                self.box(layer, xa - w / 2, min(ya, yb) - w / 2, xa + w / 2, max(ya, yb) + w / 2)
            elif abs(ya - yb) < 1e-9:
                self.box(layer, min(xa, xb) - w / 2, ya - w / 2, max(xa, xb) + w / 2, ya + w / 2)
            else:
                raise ValueError('wire segments must be Manhattan: %s -> %s' % ((xa, ya), (xb, yb)))

    def hwire(self, layer, xa, xb, y, w):
        self.box(layer, min(xa, xb) - w / 2, y - w / 2, max(xa, xb) + w / 2, y + w / 2)

    def vwire(self, layer, x, ya, yb, w):
        self.box(layer, x - w / 2, min(ya, yb) - w / 2, x + w / 2, max(ya, yb) + w / 2)

    # ---- vias ----------------------------------------------------------------------------------
    def via1(self, cx, cy, lo, hi, pad=PAD):
        """One via between adjacent metals lo -> hi at (cx, cy) with square landing pads on both."""
        v = VIAS[(lo, hi)]
        if v == 'TV1':
            self.sq('TV1', cx, cy, TV1)
            self.sq('M5', cx, cy, TV1 + 2 * TV1_M5)
            self.sq('TM1', cx, cy, max(TV1 + 2 * TV1_TM1, 1.64))
        else:
            self.sq(v, cx, cy, VIA)
            self.sq(lo, cx, cy, pad)
            self.sq(hi, cx, cy, pad)

    def stack(self, cx, cy, lo, hi, pad=PAD):
        """Via stack from metal lo up to metal hi (single vias, 0.31 um pads)."""
        i, j = METALS.index(lo), METALS.index(hi)
        for k in range(i, j):
            self.via1(cx, cy, METALS[k], METALS[k + 1], pad)

    def via_fill(self, x1, y1, x2, y2, lo, hi, pitch=VPITCH):
        """Fill the rectangle with vias lo->hi (adjacent metals only), pads = the rectangle on both."""
        v = VIAS[(lo, hi)]
        assert v != 'TV1'
        self.box(lo, x1, y1, x2, y2); self.box(hi, x1, y1, x2, y2)
        nx = max(1, int((x2 - x1 - 2 * VENC - VIA) // pitch) + 1)
        ny = max(1, int((y2 - y1 - 2 * VENC - VIA) // pitch) + 1)
        ox = (x1 + x2) / 2 - (nx - 1) * pitch / 2
        oy = (y1 + y2) / 2 - (ny - 1) * pitch / 2
        for i in range(nx):
            for j in range(ny):
                self.sq(v, snap(ox + i * pitch), snap(oy + j * pitch), VIA)

    def stack_fill(self, x1, y1, x2, y2, lo, hi, pitch=VPITCH):
        i, j = METALS.index(lo), METALS.index(hi)
        for k in range(i, j):
            self.via_fill(x1, y1, x2, y2, METALS[k], METALS[k + 1], pitch)

    # ---- contacts / taps -------------------------------------------------------------------------
    def cont_row(self, x1, x2, y):
        """contacts along y between x1 and x2 (centres) at CPITCH, centred."""
        span = x2 - x1
        n = int(span // CPITCH) + 1
        ox = (x1 + x2) / 2 - (n - 1) * CPITCH / 2
        for i in range(n):
            self.sq('Cont', snap(ox + i * CPITCH), y, CONT)

    def cont_col(self, y1, y2, x):
        span = y2 - y1
        n = int(span // CPITCH) + 1
        oy = (y1 + y2) / 2 - (n - 1) * CPITCH / 2
        for i in range(n):
            self.sq('Cont', x, snap(oy + i * CPITCH), CONT)

    def tap_strip(self, x1, x2, y, ptype=True, w=0.30, inset=0.15):
        """Horizontal tie strip (Activ w wide, contacts, Metal1 0.26) between x1 and x2 at centre y.
        ptype: substrate tie (adds pSD); else NWell tie (must lie inside NWell). `inset` keeps the
        contacts away from the ends (0.6 when the strip ends overlap a contacted ring)."""
        self.box('Activ', x1, y - w / 2, x2, y + w / 2)
        if ptype:
            self.box('pSD', x1 - 0.03, y - w / 2 - 0.03, x2 + 0.03, y + w / 2 + 0.03)   # pSD.c1 0.03
        self.cont_row(x1 + inset, x2 - inset, y)
        self.box('M1', x1, y - 0.13, x2, y + 0.13)

    def tap_ring(self, x1, y1, x2, y2, w=0.30, ptype=True):
        """Substrate (ptype) or NWell (ntype, must lie inside NWell) tie ring just outside the box
        (x1,y1,x2,y2), Activ width w, contact ring, Metal1 ring 0.26 wide.
        Returns the Metal1 ring centre-line box (cx1, cy1, cx2, cy2)."""
        self.ring('Activ', x1, y1, x2, y2, w)
        if ptype:
            self.ring('pSD', x1 + 0.03, y1 + 0.03, x2 - 0.03, y2 - 0.03, w + 0.06)   # pSD.c1 0.03
        c = w / 2
        cx1, cx2, cy1, cy2 = x1 - c, x2 + c, y1 - c, y2 + c
        for cy in (cy1, cy2):
            self.sq('Cont', cx1, cy, CONT); self.sq('Cont', cx2, cy, CONT)
        def side(a, b):
            span = b - a - CPITCH
            n = int(span // CPITCH)
            if n < 1:
                return []
            start = (a + b) / 2 - (n - 1) * CPITCH / 2
            return [snap(start + i * CPITCH) for i in range(n)]
        for x in side(cx1, cx2):
            self.sq('Cont', x, cy1, CONT); self.sq('Cont', x, cy2, CONT)
        for y in side(cy1, cy2):
            self.sq('Cont', cx1, y, CONT); self.sq('Cont', cx2, y, CONT)
        hw = CONT / 2 + 0.05
        self.ring('M1', cx1 + hw, cy1 + hw, cx2 - hw, cy2 - hw, 2 * hw)
        return (cx1, cy1, cx2, cy2)

    # ---- PCells --------------------------------------------------------------------------------
    def pcell(self, name, params, x, y, trans=None):
        pcv = LIB.layout().add_pcell_variant(LIB.layout().pcell_id(name), params)
        cell = self.ly.cell(self.ly.add_lib_cell(LIB, pcv))
        t = trans if trans is not None else pya.Trans(pya.Point(um(x), um(y)))
        self.cell.insert(pya.CellInstArray(cell.cell_index(), t))
        return cell

    def inst(self, cell, x, y, rot=0, mirror=False):
        t = pya.Trans(rot, mirror, um(x), um(y))
        self.cell.insert(pya.CellInstArray(cell.cell_index(), t))

    def boundary(self, x1, y1, x2, y2):
        """Cell boundary on prBoundary.boundary 189/4 only (the PDK layer map's DIEAREA). Nothing is
        drawn on 189/0: the chip-level density deck takes 189/0 as the chip outline, so a macro must
        not carry it."""
        self.box('prBoundary4', x1, y1, x2, y2)

    def nofill(self, x1, y1, x2, y2):
        """No-fill region: the PDK NoFillerStack PCell (Activ, GatPoly, Metal1-5, TopMetal1/2 on
        datatype 23) plus NoMetFiller 160/0, all as the same box; the PDK filler macros exclude them."""
        self.pcell('NoFillerStack', {'w': '%gu' % (x2 - x1), 'l': '%gu' % (y2 - y1)}, x1, y1)
        self.box('NoMetFiller', x1, y1, x2, y2)


class Mos:
    """One MOS PCell (nmosHV, pmosHV, nmos, pmos) with `nf` fingers of height wf at Activ origin
    (x0, y0). Strip k (k = 0..nf) is the source/drain Metal1 strip left of gate k; gates k = 0..nf-1.
    Side geometry as a distance d outward from the Activ edge on 'bot' or 'top':
      poly gate bar d 0.18..0.48 with one contact per gate at d 0.33 and a Metal1 pad gx +- 0.15,
      Metal2 gate rail d 0.14..0.52 (0.38 wide), Metal1 source/drain rail d 0.78..1.28 (0.50)."""
    RAIL_LO, RAIL_HI = 0.78, 1.28
    GBAR_LO, GBAR_HI = 0.18, 0.48
    GRAIL_LO, GRAIL_HI = 0.14, 0.52
    GC = 0.33

    def __init__(self, D, kind, w, l, nf, x0, y0):
        self.D, self.kind, self.w, self.l, self.nf, self.x0, self.y0 = D, kind, w, l, nf, x0, y0
        self.wf = w / nf
        if kind.endswith('HV') and self.wf > HV_MAX_WF + 1e-9:
            raise ValueError('%s finger %g um > 10 um' % (kind, self.wf))
        self.pitch = l + PITCH_EXTRA
        self.actw = nf * self.pitch + 0.30
        params = {'w': '%gu' % w, 'l': '%gu' % l, 'ng': nf}
        D.pcell(kind, params, x0, y0)
        self.is_p = kind.startswith('pmos')
        self.hv = kind.endswith('HV')

    # geometry queries
    def sx(self, k):            # centre x of strip k
        return self.x0 + 0.15 + k * self.pitch
    def gx(self, k):            # centre x of gate k
        return self.x0 + 0.34 + self.l / 2 + k * self.pitch
    @property
    def x1(self):
        return self.x0 + self.actw
    @property
    def y1(self):
        return self.y0 + self.wf
    @property
    def xc(self):
        return (self.x0 + self.x1) / 2
    def edge(self, side):
        return self.y0 if side == 'bot' else self.y1
    def sgn(self, side):
        return -1 if side == 'bot' else 1
    def yd(self, side, d):
        return self.edge(side) + self.sgn(side) * d
    def strips(self, parity):
        return [k for k in range(self.nf + 1) if k % 2 == parity]

    # ---- structures ------------------------------------------------------------------------------
    def gate_bar(self, side, gates=None, m2=True, ext=(0.0, 0.0)):
        """Poly bar joining the given (contiguous) gates on `side`, one contact + Metal1 pad per gate
        and, if m2, a Via1 per gate and a Metal2 rail. Returns (x_left, x_right, y_lo, y_hi) of the
        Metal2 rail (or of the poly bar when m2 is False)."""
        D = self.D
        gates = list(range(self.nf)) if gates is None else gates
        ya, yb = self.yd(side, self.GBAR_LO), self.yd(side, self.GBAR_HI)
        xl, xr = self.gx(gates[0]) - self.l / 2, self.gx(gates[-1]) + self.l / 2
        D.box('GatPoly', xl, ya, xr, yb)
        yc = self.yd(side, self.GC)
        for k in gates:
            g = self.gx(k)
            D.sq('Cont', g, yc, CONT)
            D.box('M1', g - 0.15, ya, g + 0.15, yb)
            if m2:
                D.sq('Via1', g, yc, VIA)
        if not m2:
            return (xl, xr, min(ya, yb), max(ya, yb))
        ra, rb = self.yd(side, self.GRAIL_LO), self.yd(side, self.GRAIL_HI)
        rl, rr = self.gx(gates[0]) - 0.20 - ext[0], self.gx(gates[-1]) + 0.20 + ext[1]
        D.box('M2', rl, ra, rr, rb)
        return (rl, rr, min(ra, rb), max(ra, rb))

    def gate_pad(self, k, side, m2=True, padw=0.40):
        """Individual gate contact for finger k on `side`: poly head (0.30 wide, or the gate length if
        larger), contact, Metal1 pad, Via1 and a Metal2 pad padw wide at the gate-rail height.
        Returns (x, y) of the via."""
        D = self.D
        g = self.gx(k)
        ya, yb = self.yd(side, self.GBAR_LO), self.yd(side, self.GBAR_HI)
        hw = max(self.l, 0.30) / 2
        D.box('GatPoly', g - hw, self.yd(side, 0.10), g + hw, yb)   # head starts 0.10 outside the Activ (Gat.d, Cnt.f)
        yc = self.yd(side, self.GC)
        D.sq('Cont', g, yc, CONT)
        D.box('M1', g - 0.15, ya, g + 0.15, yb)
        if m2:
            D.sq('Via1', g, yc, VIA)
            ra, rb = self.yd(side, self.GRAIL_LO), self.yd(side, self.GRAIL_HI)
            D.box('M2', g - padw / 2, ra, g + padw / 2, rb)
        return (g, yc)

    def rail(self, side, strips, ext=(0.0, 0.0), lo=None, hi=None):
        """Metal1 rail on `side` for the given strips: strip extensions from the Activ edge to the rail
        plus the rail box spanning them (ext = extra length left/right).
        Returns (x_left, x_right, y_lo, y_hi)."""
        D = self.D
        lo = self.RAIL_LO if lo is None else lo
        hi = self.RAIL_HI if hi is None else hi
        for k in strips:
            x = self.sx(k)
            D.box('M1', x - 0.08, self.edge(side), x + 0.08, self.yd(side, hi))
        xl = self.sx(strips[0]) - 0.13 - ext[0]
        xr = self.sx(strips[-1]) + 0.13 + ext[1]
        ya, yb = self.yd(side, lo), self.yd(side, hi)
        D.box('M1', xl, ya, xr, yb)
        return (xl, xr, min(ya, yb), max(ya, yb))

    def strip_pad(self, k, side, d, hi='M2', m2box=None):
        """Via pad on strip k at level d on `side` (d < 0: over the strip inside the Activ; d > 0
        needs the Metal1 strip extension of a rail to be there): Metal1 0.34 pad, Via1, Metal2 pad
        (and a stack up to `hi`). m2box = (y_lo, y_hi) draws the Metal2 pad as a 0.40 wide box
        between those y instead of a square. Returns (x, y)."""
        D = self.D
        x, y = self.sx(k), self.yd(side, d)
        D.sq('M1', x, y, 0.34)
        if m2box is not None:
            D.sq('Via1', x, y, VIA)
            D.box('M2', x - 0.20, m2box[0], x + 0.20, m2box[1])
            if hi != 'M2':
                D.stack(x, y, 'M2', hi)
        else:
            D.stack(x, y, 'M1', hi)
        return (x, y)

    def dummy(self, x, h_extra=0.36):
        """Poly-only dummy finger (no Activ: not a device) centred at x, gate length l, height wf + h_extra."""
        yc = self.y0 + self.wf / 2
        h = self.wf + h_extra
        self.D.box('GatPoly', x - self.l / 2, yc - h / 2, x + self.l / 2, yc + h / 2)

    def end_dummies(self, clear=0.20):
        """Dummies just outside both Activ ends (Gat.d 0.07 to Activ: use `clear`)."""
        self.dummy(self.x0 - clear - self.l / 2)
        self.dummy(self.x1 + clear + self.l / 2)


def row(D, kind, specs, x0, y0, gap=1.40, dummies=True):
    """Place devices [(w, l, nf), ...] side by side from x0 (Activ origins at y0) with `gap` between
    Activ boxes; with `dummies`, one poly dummy centred in each gap and one at both row ends
    (gap must be >= l + 0.40 for this). Returns [Mos]."""
    out, x = [], x0
    for i, (w, l, nf) in enumerate(specs):
        m = Mos(D, kind, w, l, nf, x, y0)
        out.append(m)
        x = m.x1 + gap
    if dummies:
        for a, b in zip(out[:-1], out[1:]):
            a.dummy((a.x1 + b.x0) / 2)
        out[0].dummy(out[0].x0 - 0.20 - out[0].l / 2)
        out[-1].dummy(out[-1].x1 + 0.20 + out[-1].l / 2)
    return out


def row_width(specs, gap=1.40):
    return sum(nf * (l + PITCH_EXTRA) + 0.30 for (w, l, nf) in specs) + gap * (len(specs) - 1)


def cover_row(D, mos_list, kind, x_ext=0.0):
    """Merge the per-device implant/oxide/well boxes of a row into one (TGO.e 0.86 and NW.b 0.62
    forbid the small gaps the PCell boxes would leave): ThickGateOx over HV rows, NWell + pSD over
    PMOS rows. Returns the covered (x1, y1, x2, y2) of the Activ envelope."""
    x1 = min(m.x0 for m in mos_list) - x_ext
    x2 = max(m.x1 for m in mos_list) + x_ext
    y1 = min(m.y0 for m in mos_list)
    y2 = max(m.y1 for m in mos_list)
    if kind == 'pmosHV':
        D.box('TGO', x1 - 0.62, y1 - 0.62, x2 + 0.62, y2 + 0.62)
        D.box('NWell', x1 - 0.62, y1 - 0.62, x2 + 0.62, y2 + 0.62)
        D.box('pSD', x1 - 0.18, y1 - 0.40, x2 + 0.18, y2 + 0.40)
    elif kind == 'nmosHV':
        D.box('TGO', x1 - 0.27, y1 - 0.52, x2 + 0.27, y2 + 0.52)
    elif kind == 'pmos':
        D.box('NWell', x1 - 0.31, y1 - 0.31, x2 + 0.31, y2 + 0.31)
        D.box('pSD', x1 - 0.18, y1 - 0.30, x2 + 0.18, y2 + 0.30)
    return (x1, y1, x2, y2)


def new_layout(top):
    ly = pya.Layout()
    ly.dbu = 0.001
    cell = ly.create_cell(top)
    return ly, cell, Draw(ly, cell)


def write_gds(ly, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    ly.write(path)
    print('wrote', path)
