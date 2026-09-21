#!/usr/bin/env python3
"""Shared KLayout drawing helpers for the G1 analog macros (G1_TRIP, G1_OSC).

Run inside the pinned container (KLayout 0.30.9 with the PDK PCell library `SG13_dev`,
PDK commit 8437402).  Every device is a PDK PCell (`nmos`, `pmos`, `nmosHV`, `pmosHV`,
`rppd`, `cmim`) instantiated through `add_pcell_variant` and flattened into the block cell, so
the block cells contain plain shapes and the LVS deep mode never has to resolve devices whose
source/drain diffusion is shared between two PCell instances (the HV switch pairs below).
This module adds the wiring around the devices (gate tabs and lanes, via pads, guard rings,
tap bars, pins) from the DRC values of the PDK JSON (`sg13g2_tech_mod.json`, `drc_rules`):

  Act.b 0.21  Gat.b 0.18  Gat.b1 0.25 (HV)  Gat.c 0.18  Gat.d 0.07  Cnt.a 0.16  Cnt.b 0.18
  Cnt.c/d 0.07  Cnt.e 0.14 (Cont on GatPoly to Activ)  Cnt.f 0.11  M1.a 0.16  M1.b 0.18
  M1.c1 0.05  M1.d 0.09 (area)  M1.e 0.22 (w > 0.3)  Mn.a 0.20  Mn.b 0.21  Mn.d 0.144
  Mn.e 0.24 (w > 0.39)  V1/Vn.a 0.19  V1/Vn.b 0.22  V1.c1/Vn.c1 0.05 (endcap)  Vn.c 0.005
  TV1.a/b 0.42  TV1.c 0.10 (M5)  TV1.d 0.42 (TM1)  TM1.a/b 1.64  NW.a/b 0.62  NW.c 0.31
  NW.c1 0.62 (HV)  NW.d 0.31  NW.f 0.24  pSD.a/b 0.31  pSD.c1 0.03  pSD.d 0.18  pSD.i 0.30
  pSD.i1 0.40  pSD.j 0.30  pSD.j1 0.40  TGO.a/b 0.27  TGO.c/d 0.34  TGO.e 0.86  Mim.b 0.6
  Mim.c 0.6  Mim.d 0.36  Sal.b 0.42  Sal.d 0.20  EXTB.b/c 0.31  Rppd.b/d 0.18  Rppd.c 0.20
  LU.a/b 20 (tie within 20 um of every S/D diffusion)

PCell geometry (measured on the instantiated cells with build/g1_trip/lay/probe3.py, see the
block READMEs): MOS PCells have their Activ lower-left at the origin, Metal1 source/drain
strips 0.16 wide at x = 0.07 + i*P (P = l + 0.38, i = 0..ng) over the full Activ height w/ng,
gate fingers at x = 0.34 + i*P of width l with 0.18 end caps, ThickGateOx (HV) 0.27 (x) /
0.52 (y) around Activ, pSD 0.18/0.30 (LV PMOS) or 0.18/0.40 (HV PMOS), NWell 0.31 (LV) or
0.62 (HV).  `rppd` (`Calculate='R'`) has the PolyRes body at 0..w x 0..l, GatPoly heads to
-0.43 / l+0.43, one contact bar per head at -0.36..-0.20 / l+0.20..l+0.36 and Metal1 heads at
-0.43..-0.13 / l+0.13..l+0.43 (x 0.02..w-0.02); pSD and EXTBlock 0.18..0.20 around, SalBlock
-0.20..w+0.20 x 0..l.  `cmim` (`Calculate='C'`) has the MIM plate at 0..w x 0..l, Metal5
0.6 around it and the TopMetal1 top plate inset 0.3..0.4 with the Vmim array inside.
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
    'Activ': (1, 0), 'GatPoly': (5, 0), 'Cont': (6, 0), 'nSD': (7, 0), 'pSD': (14, 0),
    'M1': (8, 0), 'M1pin': (8, 2), 'M1txt': (8, 25),
    'M2': (10, 0), 'M2pin': (10, 2), 'M2txt': (10, 25),
    'M3': (30, 0), 'M3pin': (30, 2), 'M3txt': (30, 25),
    'M4': (50, 0), 'M4pin': (50, 2), 'M4txt': (50, 25),
    'M5': (67, 0), 'M5pin': (67, 2), 'M5txt': (67, 25),
    'TM1': (126, 0), 'TM1pin': (126, 2), 'TM1txt': (126, 25),
    'Via1': (19, 0), 'Via2': (29, 0), 'Via3': (49, 0), 'Via4': (66, 0), 'TopVia1': (125, 0),
    'NWell': (31, 0), 'TGO': (44, 0), 'MIM': (36, 0), 'Vmim': (129, 0),
    'SalBlock': (28, 0), 'ExtBlock': (111, 0), 'PolyRes': (128, 0), 'prBnd': (189, 0),
    'RES': (52, 0), 'TEXT': (63, 0), 'HeatTrans': (51, 0), 'Substrate': (40, 0),
    'prBoundary': (189, 4), 'Recog_diode': (99, 31), 'EdgeSeal': (39, 0),
    # no-fill layers (datatype 23, honoured by the PDK filler and the chip-level filler) + NoMetFiller
    'Activ_nf': (1, 23), 'GatPoly_nf': (5, 23), 'M1_nf': (8, 23), 'M2_nf': (10, 23), 'M3_nf': (30, 23),
    'M4_nf': (50, 23), 'M5_nf': (67, 23), 'TM1_nf': (126, 23), 'TM2_nf': (134, 23), 'NoMetFiller': (160, 0),
}
NOFILL_ALL = ('Activ_nf', 'GatPoly_nf', 'M1_nf', 'M2_nf', 'M3_nf', 'M4_nf', 'M5_nf', 'TM1_nf', 'TM2_nf', 'NoMetFiller')
NOFILL_METAL = ('M1_nf', 'M2_nf', 'M3_nf', 'M4_nf', 'M5_nf', 'TM1_nf', 'TM2_nf', 'NoMetFiller')
NOFILL_UPPER = ('M4_nf', 'M5_nf', 'TM1_nf', 'TM2_nf')
CONT = 0.16      # Cnt.a
CPITCH = 0.34    # Cnt.a + Cnt.b
VIA = 0.19       # V1.a / Vn.a
VPITCH = 0.42    # V1.a + V1.b (+ margin)
TV1 = 0.42       # TV1.a
M1W = 0.20       # default Metal1 wire width
MNW = 0.24       # default Metal2..5 wire width (>= Mn.a 0.20; 0.24 covers a via with Vn.c)
PAD1 = 0.30      # Metal1 landing pad for Cont/Via1 (area 0.09 = M1.d, encl. 0.055 >= V1.c1)
PADN = 0.30      # Metal2..5 landing pad for vias (0.055 >= Vn.c1; area is met by the wire)
GAP1 = 0.24      # Metal1 spacing used between different nets (>= M1.e 0.22)
GAPN = 0.26      # Metal2..5 spacing used between different nets (>= Mn.e 0.24)


def um(v):
    return int(round(v * 1000))


def r3(v):
    return round(v, 3)


class Draw:
    """Rectangle/via/label drawing into one KLayout cell (coordinates in um)."""

    def __init__(self, ly, cell):
        self.ly, self.cell = ly, cell
        self.L = {n: ly.layer(*v) for n, v in LAYERS.items()}

    # ---- primitives -------------------------------------------------------
    def box(self, layer, x1, y1, x2, y2):
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        self.cell.shapes(self.L[layer]).insert(pya.Box(um(x1), um(y1), um(x2), um(y2)))
        return (x1, y1, x2, y2)

    def nofill(self, x1, y1, x2, y2, margin=3.0, layers=NOFILL_ALL, clip=None):
        """no-fill rectangle (the box grown by `margin`, clipped to `clip`) on the given no-fill layers:
        the PDK filler (libs.tech/klayout/tech/macros/sg13g2_filler_*.lym) and the chip-level filler
        leave it empty"""
        b = [x1 - margin, y1 - margin, x2 + margin, y2 + margin]
        if clip is not None:
            b = [max(b[0], clip[0]), max(b[1], clip[1]), min(b[2], clip[2]), min(b[3], clip[3])]
        for layer in layers:
            self.box(layer, *b)
        return tuple(b)

    def square(self, layer, cx, cy, size):
        return self.box(layer, cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2)

    def hwire(self, layer, x1, x2, y, w=None, ext=True):
        """horizontal wire of width w from x1 to x2 (centre line y); ends extended by w/2 so that
        L-corners with a vwire of the same width leave no notch"""
        w = w or (M1W if layer == 'M1' else MNW)
        e = w / 2 if ext else 0.0
        return self.box(layer, min(x1, x2) - e, y - w / 2, max(x1, x2) + e, y + w / 2)

    def vwire(self, layer, x, y1, y2, w=None, ext=True):
        w = w or (M1W if layer == 'M1' else MNW)
        e = w / 2 if ext else 0.0
        return self.box(layer, x - w / 2, min(y1, y2) - e, x + w / 2, max(y1, y2) + e)

    def ring(self, layer, x1, y1, x2, y2, w):
        """closed ring between the inner box and the box grown by w"""
        outer = pya.Polygon(pya.Box(um(x1 - w), um(y1 - w), um(x2 + w), um(y2 + w)))
        outer.insert_hole(pya.Box(um(x1), um(y1), um(x2), um(y2)))
        self.cell.shapes(self.L[layer]).insert(outer)

    def label(self, layer, x, y, text, size=0.3):
        t = pya.Text(text, pya.Trans(pya.Point(um(x), um(y))))
        t.size = um(size)
        self.cell.shapes(self.L[layer]).insert(t)

    def pin(self, layer, x1, y1, x2, y2, name):
        """drawing + pin shape + label on the metal layer `layer` ('M1'..'M5','TM1')"""
        self.box(layer, x1, y1, x2, y2)
        self.box(layer + 'pin', x1, y1, x2, y2)
        self.label(layer + 'txt', (x1 + x2) / 2, (y1 + y2) / 2, name)

    # ---- contacts and vias -------------------------------------------------
    def cont(self, cx, cy):
        self.square('Cont', cx, cy, CONT)

    def cont_line(self, p1, p2, fixed, vertical):
        """contacts at pitch CPITCH between centre coordinates p1..p2 (inclusive if it fits)"""
        n = int((p2 - p1) / CPITCH + 1e-6) + 1
        start = (p1 + p2) / 2 - (n - 1) * CPITCH / 2
        for i in range(n):
            c = start + i * CPITCH
            if vertical:
                self.cont(fixed, c)
            else:
                self.cont(c, fixed)

    def via(self, kind, cx, cy, pads=True, padlo=None, padhi=None):
        """single via with landing pads. kind: 'Via1' (M1-M2), 'Via2' (M2-M3), 'Via3', 'Via4', 'TopVia1'."""
        lo, hi = {'Via1': ('M1', 'M2'), 'Via2': ('M2', 'M3'), 'Via3': ('M3', 'M4'),
                  'Via4': ('M4', 'M5'), 'TopVia1': ('M5', 'TM1')}[kind]
        if kind == 'TopVia1':
            self.square('TopVia1', cx, cy, TV1)
            if pads:
                self.square('M5', cx, cy, TV1 + 0.24)     # TV1.c 0.10 -> 0.12
                self.square('TM1', cx, cy, 1.64)          # TV1.d 0.42 -> 0.61, TM1.a 1.64
            return
        self.square(kind, cx, cy, VIA)
        if pads:
            self.square(lo, cx, cy, padlo or (PAD1 if lo == 'M1' else PADN))
            self.square(hi, cx, cy, padhi or PADN)

    def vpad(self, kind, x, y, lo='v', hi='v', lopad=True, hipad=True):
        """via (Via1..Via4) with endcap-safe pads on both metals: `lo`/`hi` give the direction of
        the wire on the lower/upper metal: 'v' (vertical wire, pad 0.24 wide x 0.30 tall),
        'h' (0.30 x 0.24) or 's' (0.30 square).  Metal1 pads are always 0.30 square."""
        lom, him = {'Via1': ('M1', 'M2'), 'Via2': ('M2', 'M3'), 'Via3': ('M3', 'M4'),
                    'Via4': ('M4', 'M5')}[kind]
        self.square(kind, x, y, VIA)
        for m, d, on in ((lom, lo, lopad), (him, hi, hipad)):
            if not on:
                continue
            if m == 'M1' or d == 's':
                self.square(m, x, y, 0.30)
            elif d == 'v':
                self.box(m, x - 0.12, y - 0.15, x + 0.12, y + 0.15)
            else:
                self.box(m, x - 0.15, y - 0.12, x + 0.15, y + 0.12)

    def via_array(self, kind, x1, y1, x2, y2):
        """vias filling the box (x1,y1,x2,y2) at pitch VPITCH, box drawn on both metals"""
        lo, hi = {'Via1': ('M1', 'M2'), 'Via2': ('M2', 'M3'), 'Via3': ('M3', 'M4'), 'Via4': ('M4', 'M5')}[kind]
        self.box(lo, x1, y1, x2, y2)
        self.box(hi, x1, y1, x2, y2)
        nx = max(1, int((x2 - x1 - 0.10 - VIA) / VPITCH + 1e-6) + 1)
        ny = max(1, int((y2 - y1 - 0.10 - VIA) / VPITCH + 1e-6) + 1)
        for i in range(nx):
            for j in range(ny):
                cx = (x1 + x2) / 2 + (i - (nx - 1) / 2) * VPITCH
                cy = (y1 + y2) / 2 + (j - (ny - 1) / 2) * VPITCH
                self.square(kind, cx, cy, VIA)

    def stack(self, cx, cy, lo, hi):
        """via stack from metal `lo` to metal `hi` ('M1'..'M5','TM1') at (cx, cy)"""
        order = ['M1', 'M2', 'M3', 'M4', 'M5', 'TM1']
        vias = ['Via1', 'Via2', 'Via3', 'Via4', 'TopVia1']
        i, j = order.index(lo), order.index(hi)
        for k in range(i, j):
            self.via(vias[k], cx, cy)

    # ---- taps and rings ----------------------------------------------------
    def guard_ring(self, x1, y1, x2, y2, w=0.30, kind='p', m1w=0.26):
        """p+ substrate tie ring (Activ + pSD, contacts, Metal1) or n+ well tie ring (Activ inside
        an NWell) just outside the inner box (x1,y1,x2,y2).  Returns the Metal1 ring centre lines
        (cx1, cy1, cx2, cy2) and the outer extent of the drawn layers."""
        self.ring('Activ', x1, y1, x2, y2, w)
        if kind == 'p':
            self.ring('pSD', x1 + 0.03, y1 + 0.03, x2 - 0.03, y2 - 0.03, w + 0.06)   # pSD.c1 0.03
            outer = w + 0.03
        else:
            self.box('NWell', x1 - w - 0.31, y1 - w - 0.31, x2 + w + 0.31, y2 + w + 0.31)
            outer = w + 0.31
        c = w / 2
        cx1, cx2, cy1, cy2 = x1 - c, x2 + c, y1 - c, y2 + c
        for cy in (cy1, cy2):
            self.cont(cx1, cy)
            self.cont(cx2, cy)

        def side(a, b):
            span = b - a - CPITCH
            n = int(span // CPITCH)
            if n < 1:
                return []
            start = (a + b) / 2 - (n - 1) * CPITCH / 2
            return [start + i * CPITCH for i in range(n)]
        for x in side(cx1, cx2):
            self.cont(x, cy1)
            self.cont(x, cy2)
        for y in side(cy1, cy2):
            self.cont(cx1, y)
            self.cont(cx2, y)
        hw = m1w / 2
        self.ring('M1', cx1 + hw, cy1 + hw, cx2 - hw, cy2 - hw, 2 * hw)
        return (cx1, cy1, cx2, cy2), (x1 - outer, y1 - outer, x2 + outer, y2 + outer)

    def tap_bar(self, x1, y1, x2, y2, kind='p', m1w=None, cmargin=(0.0, 0.0)):
        """straight substrate (p+) or well (n+) tie: Activ box with contacts and Metal1 over it.
        The box is the Activ; pSD (p) is 0.03 larger; for 'n' the caller draws the NWell.
        cmargin = extra contact-free length at the (low, high) end, e.g. where the bar merges
        into a guard ring whose own contacts sit there."""
        self.box('Activ', x1, y1, x2, y2)
        if kind == 'p':
            self.box('pSD', x1 - 0.03, y1 - 0.03, x2 + 0.03, y2 + 0.03)
        w = min(x2 - x1, y2 - y1)
        if (x2 - x1) >= (y2 - y1):
            self.cont_line(x1 + w / 2 + cmargin[0], x2 - w / 2 - cmargin[1], (y1 + y2) / 2, vertical=False)
        else:
            self.cont_line(y1 + w / 2 + cmargin[0], y2 - w / 2 - cmargin[1], (x1 + x2) / 2, vertical=True)
        mw = m1w or max(0.26, w)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        if (x2 - x1) >= (y2 - y1):
            self.box('M1', x1, cy - mw / 2, x2, cy + mw / 2)
        else:
            self.box('M1', cx - mw / 2, y1, cx + mw / 2, y2)

    # ---- PCells -------------------------------------------------------------
    def pcell(self, name, params, trans):
        """instantiate a PDK PCell with the transformation `trans` (pya.Trans, dbu units) and
        flatten it into this cell"""
        pcv = LIB.layout().add_pcell_variant(LIB.layout().pcell_id(name), params)
        cell = self.ly.cell(self.ly.add_lib_cell(LIB, pcv))
        inst = self.cell.insert(pya.CellInstArray(cell.cell_index(), trans))
        inst.flatten()
        return cell

    def clean_pcell_markers(self):
        """remove the PCell text markers (layer 63) that flattening leaves behind"""
        self.cell.shapes(self.L['TEXT']).clear()


def T(x, y, rot=0, mirror=False):
    """pya.Trans at (x, y) um with rotation rot (0/90/180/270) and optional mirror (applied first,
    KLayout convention: mirror about the x axis, then rotate)"""
    return pya.Trans(rot // 90, mirror, pya.Point(um(x), um(y)))


def tbox(t, x1, y1, x2, y2):
    """transform a um box by pya.Trans t; returns (x1, y1, x2, y2) in um"""
    b = t * pya.Box(um(x1), um(y1), um(x2), um(y2))
    return (b.left / 1000, b.bottom / 1000, b.right / 1000, b.top / 1000)


def tpt(t, x, y):
    p = t * pya.Point(um(x), um(y))
    return (p.x / 1000, p.y / 1000)


# --------------------------------------------------------------------------- devices
class Mos:
    """A PDK MOS PCell placed with its Activ lower-left corner at (ox, oy) in the parent cell,
    optionally mirrored in x (mirror='x': x -> 2*ox + act_w - x, i.e. fingers reversed) so that
    two single-finger devices can share a diffusion strip.

    kind: 'nmos' | 'pmos' | 'nmosHV' | 'pmosHV';  w = total width, l, ng fingers.
    Terminal geometry (parent coordinates):
      strip(i)  : Metal1 S/D strip i (i = 0..ng), returns (x1, y1, x2, y2)
      gate(i)   : GatPoly finger i
      activ     : Activ box;  tgo : ThickGateOx box (HV) ; well : NWell box (PMOS)
    """
    P_EXTRA = 0.38  # finger pitch = l + 0.38

    def __init__(self, D, kind, w, l, ng, ox, oy, mirror=None):
        self.D, self.kind, self.w, self.l, self.ng, self.ox, self.oy = D, kind, w, l, ng, ox, oy
        self.wf = r3(w / ng)
        self.hv = kind.endswith('HV')
        self.p = kind.startswith('p')
        params = {'w': '%gu' % w, 'l': '%gu' % l, 'ng': ng}
        self.pitch = l + self.P_EXTRA
        self.act_w = r3(0.68 + ng * l + (ng - 1) * self.P_EXTRA)
        if mirror == 'x':
            # M90 (= R180 after M0) mirrors x -> -x; shift so that the Activ lands at ox..ox+act_w
            t = pya.Trans(2, True, pya.Point(um(ox + self.act_w), um(oy)))
        else:
            t = pya.Trans(pya.Point(um(ox), um(oy)))
        self.mirror = mirror
        D.pcell(kind, params, t)
        self.activ = (ox, oy, ox + self.act_w, oy + self.wf)
        if self.hv:
            self.tgo = (ox - 0.27, oy - 0.52, ox + self.act_w + 0.27, oy + self.wf + 0.52)
        if self.p:
            e = 0.62 if self.hv else 0.31
            self.well = (ox - e, oy - e, ox + self.act_w + e, oy + self.wf + e)
            self.psd = (ox - 0.18, oy - (0.40 if self.hv else 0.30), ox + self.act_w + 0.18, oy + self.wf + (0.40 if self.hv else 0.30))

    def _x(self, xl):
        """local x (unmirrored PCell frame) to parent x"""
        if self.mirror == 'x':
            return self.ox + self.act_w - xl
        return self.ox + xl

    def strip(self, i):
        xa = self._x(0.07 + i * self.pitch)
        xb = self._x(0.23 + i * self.pitch)
        return (min(xa, xb), self.oy, max(xa, xb), self.oy + self.wf)

    def strip_x(self, i):
        return self._x(0.15 + i * self.pitch)

    def gate(self, i):
        xa = self._x(0.34 + i * self.pitch)
        xb = self._x(0.34 + i * self.pitch + self.l)
        return (min(xa, xb), self.oy - 0.18, max(xa, xb), self.oy + self.wf + 0.18)

    def gate_x(self, i):
        return self._x(0.34 + i * self.pitch + self.l / 2)

    # ---- gate connection -----------------------------------------------------
    def gate_strap(self, side='bottom', pad='left', ext=0.0, gap=0.10):
        """GatPoly bar joining all fingers below (side='bottom') or above ('top') the Activ, with
        one contact + Metal1 pad beyond the Activ on the `pad` side ('left'|'right') or, with
        pad='mid', centred under the fingers.  Returns (Metal1 pad box, contact centre)."""
        D = self.D
        if side == 'bottom':
            yb1, yb2 = self.oy - gap - 0.46, self.oy - gap        # poly bar (Gat.d 0.07)
            yc = self.oy - gap - 0.26                              # contact centre (Cnt.e 0.14)
        else:
            yb1, yb2 = self.oy + self.wf + gap, self.oy + self.wf + gap + 0.46
            yc = self.oy + self.wf + gap + 0.26
        gxs = [self.gate(i) for i in range(self.ng)]
        gx1 = min(g[0] for g in gxs)
        gx2 = max(g[2] for g in gxs)
        if pad == 'left':
            xc = self.ox - 0.30 - ext
            D.box('GatPoly', xc - 0.15, yb1, gx2, yb2)
        elif pad == 'right':
            xc = self.ox + self.act_w + 0.30 + ext
            D.box('GatPoly', gx1, yb1, xc + 0.15, yb2)
        else:
            xc = (gx1 + gx2) / 2
            D.box('GatPoly', min(gx1, xc - 0.15), yb1, max(gx2, xc + 0.15), yb2)
        D.cont(xc, yc)
        padbox = D.box('M1', xc - 0.15, yc - 0.15, xc + 0.15, yc + 0.15)
        return padbox, (xc, yc)

    # ---- source/drain joins -------------------------------------------------
    def join(self, strips, side='top', extra=0.0, w=0.20):
        """Metal1 bar joining the given strip indices above ('top') or below ('bottom') the Activ.
        Strips are extended to the bar. Returns the bar box (x1, y1, x2, y2)."""
        D = self.D
        xs = [self.strip_x(i) for i in strips]
        if side == 'top':
            y1 = self.oy + self.wf + 0.20 + extra
            y2 = y1 + w
            for i in strips:
                s = self.strip(i)
                D.box('M1', s[0], s[3], s[2], y2)
        else:
            y2 = self.oy - 0.20 - extra
            y1 = y2 - w
            for i in strips:
                s = self.strip(i)
                D.box('M1', s[0], y1, s[2], s[1])
        return D.box('M1', min(xs) - 0.08, y1, max(xs) + 0.08, y2)

    def extend(self, i, side='top', to=None, w=0.16):
        """extend strip i on Metal1 to y=`to` (above or below). Returns end point (x, y)."""
        s = self.strip(i)
        x = self.strip_x(i)
        if side == 'top':
            self.D.box('M1', x - w / 2, s[3], x + w / 2, to)
        else:
            self.D.box('M1', x - w / 2, to, x + w / 2, s[1])
        return (x, to)


class HvPair:
    """Two `nmosHV` 2/0.45 switches sharing their source diffusion, rotated so that the channel
    width runs along x.  Local frame (before `flip`): Activ 0..2.0 x 0..1.96, Metal1 strips
    (horizontal, x 0..2.0) at y 0.07..0.23 (drain A, input a), 0.90..1.06 (shared source =
    output) and 1.73..1.89 (drain B, input b); gate A poly at y 0.34..0.79, gate B at
    1.17..1.62, both x -0.18..2.18.  Gate A is contacted on the left through a poly tab under
    Metal1 lane `lane` (lanes at x = -0.49 - 0.5*lane), gate B on the right (x = 2.49 + 0.5*lane).
    flip=True mirrors the pair about y = 0.98 (drain A on top).  With `ny` > 0 the pair is
    mirrored/shifted so the origin (ox, oy) stays the lower-left of the Activ."""
    W = 2.0
    H = 1.96
    Y_A, Y_S, Y_B = 0.15, 0.98, 1.81
    GA, GB = (0.34, 0.79), (1.17, 1.62)
    LANE_W = 0.26
    LANE_PITCH = 0.50
    LANE0 = 0.49            # first lane centre distance from the Activ edge

    def __init__(self, D, ox, oy, lane=0, flip=False, nlanes=None):
        self.D, self.ox, self.oy, self.flip, self.lane = D, ox, oy, flip, lane
        # unrotated pair: A at (0,0), B mirrored in x about 0.98; then R90 and shift by (2.0, 0)
        R = pya.Trans(1, False, pya.Point(um(ox + self.W), um(oy)))   # R90 then displace
        if flip:
            # mirror about y = 0.98 in the pair frame: apply before R: (x,y)->(x, 1.96-y) in
            # rotated frame == in the unrotated frame x -> 1.96 - x, i.e. swap A and B places
            A = pya.Trans(2, True, pya.Point(um(1.96), 0))    # M90: x -> 1.96 - x
            B = pya.Trans(pya.Point(0, 0))
        else:
            A = pya.Trans(pya.Point(0, 0))
            B = pya.Trans(2, True, pya.Point(um(1.96), 0))
        params = {'w': '2u', 'l': '0.45u', 'ng': 1}
        D.pcell('nmosHV', params, R * A)
        D.pcell('nmosHV', params, R * B)
        self.activ = (ox, oy, ox + self.W, oy + self.H)
        self.tgo = (ox - 0.52, oy - 0.27, ox + self.W + 0.52, oy + self.H + 0.27)
        # gate tabs and contacts
        ga = self._y(sum(self.GA) / 2)
        gb = self._y(sum(self.GB) / 2)
        xa = ox - self.LANE0 - self.LANE_PITCH * lane
        xb = ox + self.W + self.LANE0 + self.LANE_PITCH * lane
        D.box('GatPoly', xa - 0.15, ga - 0.225, ox + 0.0, ga + 0.225)
        D.box('GatPoly', ox + self.W, gb - 0.225, xb + 0.15, gb + 0.225)
        D.cont(xa, ga)
        D.cont(xb, gb)
        self.gate_a = (xa, ga)
        self.gate_b = (xb, gb)

    def _y(self, yl):
        return self.oy + (self.H - yl if self.flip else yl)

    def y_a(self):
        return self._y(self.Y_A)

    def y_b(self):
        return self._y(self.Y_B)

    def y_s(self):
        return self._y(self.Y_S)

    def pad(self, which, x, layer='M2'):
        """Metal1 pad + Via1 (+ Metal2 pad) on strip `which` ('a'|'b'|'s') at x (parent coords).
        Returns the pad centre."""
        y = {'a': self.y_a(), 'b': self.y_b(), 's': self.y_s()}[which]
        self.D.box('M1', x - 0.145, y - 0.15, x + 0.145, y + 0.15)
        self.D.square('Via1', x, y, VIA)
        self.D.square('M2', x, y, PADN)
        return (x, y)


class RppdUnit:
    """rppd 4 x 1.2 unit with the body lower-left at (ox, oy); heads (Metal1) at y oy-0.43..-0.13
    and oy+1.33..1.63, contact bars at oy-0.36..-0.20 and oy+1.40..1.56.  Units stacked at pitch
    1.76 share their heads (identical GatPoly/Cont/Metal1 shapes merge)."""
    W, L = 4.0, 1.2
    PITCH = 1.76

    def __init__(self, D, ox, oy, dummy=False):
        self.D, self.ox, self.oy = D, ox, oy
        if dummy:
            # physical copy without the PolyRes/RES recognition layers: not a device
            D.box('GatPoly', ox, oy - 0.43, ox + self.W, oy + self.L + 0.43)
            D.box('pSD', ox - 0.18, oy - 0.61, ox + self.W + 0.18, oy + self.L + 0.61)
            D.box('SalBlock', ox - 0.20, oy, ox + self.W + 0.20, oy + self.L)
            D.box('ExtBlock', ox - 0.18, oy - 0.61, ox + self.W + 0.18, oy)
            D.box('ExtBlock', ox - 0.20, oy, ox + self.W + 0.20, oy + self.L)
            D.box('ExtBlock', ox - 0.18, oy + self.L, ox + self.W + 0.18, oy + self.L + 0.61)
            D.box('Cont', ox + 0.07, oy - 0.36, ox + self.W - 0.07, oy - 0.20)
            D.box('Cont', ox + 0.07, oy + self.L + 0.20, ox + self.W - 0.07, oy + self.L + 0.36)
            D.box('M1', ox + 0.02, oy - 0.43, ox + self.W - 0.02, oy - 0.13)
            D.box('M1', ox + 0.02, oy + self.L + 0.13, ox + self.W - 0.02, oy + self.L + 0.43)
        else:
            params = {'w': '4u', 'l': '1.2u', 'b': 0, 'ps': '0.18u', 'Calculate': 'R'}
            D.pcell('rppd', params, pya.Trans(pya.Point(um(ox), um(oy))))
        self.head_bot = (ox + 0.02, oy - 0.43, ox + self.W - 0.02, oy - 0.13)
        self.head_top = (ox + 0.02, oy + self.L + 0.13, ox + self.W - 0.02, oy + self.L + 0.43)


class RppdCol:
    """Column of `n` real rppd 4x1.2 units (plus `ndum` dummies at each end) stacked at pitch
    1.76 with shared heads, lower-left of the first real unit at (ox, oy).  node(i) for
    i = 0..n is the y centre of head i (node 0 = bottom of unit 0, node n = top of unit n-1)."""

    def __init__(self, D, ox, oy, n, ndum=1):
        self.D, self.ox, self.oy, self.n, self.ndum = D, ox, oy, n, ndum
        P = RppdUnit.PITCH
        for i in range(-ndum, n + ndum):
            RppdUnit(D, ox, oy + i * P, dummy=not (0 <= i < n))
        self.x1, self.x2 = ox + 0.02, ox + RppdUnit.W - 0.02
        self.ybot = oy - ndum * P - 0.61
        self.ytop = oy + (n + ndum - 1) * P + RppdUnit.L + 0.61

    def node(self, i):
        return self.oy + i * RppdUnit.PITCH - 0.28

    def head(self, i):
        y = self.node(i)
        return (self.x1, y - 0.15, self.x2, y + 0.15)


class Rppd:
    """rppd PCell (any w, l) with the body lower-left at (ox, oy): body ox..ox+w x oy..oy+l,
    heads on Metal1 at y oy-0.43..-0.13 (bottom) and oy+l+0.13..oy+l+0.43 (top)."""

    def __init__(self, D, w, l, ox, oy):
        self.D, self.w, self.l, self.ox, self.oy = D, w, l, ox, oy
        params = {'w': '%gu' % w, 'l': '%gu' % l, 'b': 0, 'ps': '0.18u', 'Calculate': 'R'}
        D.pcell('rppd', params, pya.Trans(pya.Point(um(ox), um(oy))))
        self.head_bot = (ox + 0.02, oy - 0.43, ox + w - 0.02, oy - 0.13)
        self.head_top = (ox + 0.02, oy + l + 0.13, ox + w - 0.02, oy + l + 0.43)
        self.extent = (ox - 0.20, oy - 0.61, ox + w + 0.20, oy + l + 0.61)   # ExtBlock/pSD


class Cmim:
    """cmim PCell with the MIM plate lower-left at (ox, oy): MIM ox..ox+w x oy..oy+l, Metal5
    bottom plate 0.6 around, TopMetal1 top plate inside the MIM (inset 0.3..0.4)."""

    def __init__(self, D, w, l, ox, oy):
        self.D, self.w, self.l, self.ox, self.oy = D, w, l, ox, oy
        params = {'w': '%gu' % w, 'l': '%gu' % l, 'Calculate': 'C'}
        D.pcell('cmim', params, pya.Trans(pya.Point(um(ox), um(oy))))
        self.mim = (ox, oy, ox + w, oy + l)
        self.m5 = (ox - 0.6, oy - 0.6, ox + w + 0.6, oy + l + 0.6)
        self.tm1_inner = (ox + 0.5, oy + 0.5, ox + w - 0.5, oy + l - 0.5)

    def top_tab(self, side, length=2.0, width=1.64, at=None):
        """TopMetal1 tab from the top plate out of the MIM on `side` ('left','right','top','bottom'),
        `at` = centre coordinate along the edge. Returns the outer end (x, y) of the tab centreline."""
        D = self.D
        x1, y1, x2, y2 = self.mim
        if side in ('left', 'right'):
            yc = at if at is not None else (y1 + y2) / 2
            if side == 'left':
                D.box('TM1', x1 - 0.6 - length, yc - width / 2, x1 + 0.6, yc + width / 2)
                return (x1 - 0.6 - length, yc)
            D.box('TM1', x2 - 0.6, yc - width / 2, x2 + 0.6 + length, yc + width / 2)
            return (x2 + 0.6 + length, yc)
        xc = at if at is not None else (x1 + x2) / 2
        if side == 'bottom':
            D.box('TM1', xc - width / 2, y1 - 0.6 - length, xc + width / 2, y1 + 0.6)
            return (xc, y1 - 0.6 - length)
        D.box('TM1', xc - width / 2, y2 - 0.6, xc + width / 2, y2 + 0.6 + length)
        return (xc, y2 + 0.6 + length)


def new_layout(top_name):
    ly = pya.Layout()
    ly.dbu = 0.001
    top = ly.create_cell(top_name)
    return ly, top


def place(parent, child, x, y, rot=0, mirror=False):
    """instantiate `child` in `parent` at (x, y) with rotation rot (0/90/180/270 deg) and optional
    mirror (KLayout convention: mirror about the x axis first, then rotate)."""
    t = pya.Trans(rot // 90, mirror, pya.Point(um(x), um(y)))
    parent.insert(pya.CellInstArray(child.cell_index(), t))
    return t


def write_gds(ly, path):
    """write the GDS; PCell library proxies that flattening left unused are dropped first"""
    for c in list(ly.each_cell()):
        if c.is_proxy() and c.parent_cells() == 0:
            ly.delete_cell(c.cell_index())
    ly.write(path)


# --------------------------------------------------------------------------- row engine
class RowLayout:
    """Standard-cell-like two-row layout of single-finger LV transistors: NMOS row with sources
    on a Metal1 vss rail below, PMOS row with sources on a Metal1 vdd rail above, every other
    terminal on a Metal1 stub to a Metal2 track in the channel between the rows (tracks are
    shared by nets whose x spans do not overlap).  Gates are strapped on the rail side (NMOS) or
    channel side (PMOS) and contacted right of the Activ.  PMOS x positions are chosen so that
    their stubs keep 0.42 um from every NMOS stub of another net.  Nets listed in `ports` get a
    Metal3 vertical from the track up to `port_y` (above the PMOS row) ending in a Metal3 pad.

    devices: list of dicts {name, kind: 'n'|'p', w, l, S, D, G} with net names; vss/vdd are the
    rail nets.  All coordinates relative to (ox, oy) = lower-left of the NMOS row Activ."""

    def __init__(self, D, ox, oy, devices, ports=(), rails=('vss', 'vdd'), avoid_x=()):
        self.D, self.ox, self.oy = D, ox, oy
        self.devices = devices
        self.ports = list(ports)
        self.vss, self.vdd = rails
        self.avoid_x = list(avoid_x)     # x positions the port verticals must keep 0.5 um from
        self.stubs = {}        # net -> list of (x, from_y, up)
        self.port_pos = {}

    def _add(self, net, x, from_y, up):
        self.stubs.setdefault(net, []).append((x, from_y, up))

    def build(self):
        D = self.D
        ox, oy = self.ox, self.oy
        nm = [d for d in self.devices if d['kind'] == 'n']
        pm = [d for d in self.devices if d['kind'] == 'p']
        VSS_Y = oy - 1.5
        # ---- NMOS row
        x = ox
        self.nx = {}
        nstub_x = []
        hmax_n = 0.0
        for d in nm:
            m = Mos(D, 'nmos', d['w'], d['l'], 1, x, oy)
            pad, gc = m.gate_strap('bottom', 'right', gap=0.10)
            self.nx[d['name']] = m
            hmax_n = max(hmax_n, d['w'])
            for term, i in (('S', 0), ('D', 1)):
                net = d[term]
                st = m.strip(i)
                if net == self.vss:
                    D.box('M1', st[0], VSS_Y, st[2], st[1])
                else:
                    self._add(net, m.strip_x(i), st[3], True)
                    nstub_x.append((m.strip_x(i), net))
            self._add(d['G'], gc[0], gc[1] + 0.15, True)
            nstub_x.append((gc[0], d['G']))
            x += m.act_w + 0.72
        self.x_n_end = x
        # ---- tracks: interval colouring of the nets' x spans (with the PMOS stubs still unknown
        #      the PMOS positions are decided first with a provisional channel)
        def clear(xx, net):
            for xs, n in nstub_x:
                dd = abs(xx - xs)
                if dd < 0.42 and not (n == net and dd < 0.005):
                    return False
            return True
        # ---- PMOS placement (x only), keeping >= 0.42 from NMOS stubs of other nets; the gate tab
        #      goes to the right or, if that conflicts, to the left of the Activ
        px_list = []
        pside = []
        x = ox
        pstubs = []
        for d in pm:
            act_w = 0.68 + d['l']
            cand = x
            while True:
                okS = (d['S'] == self.vdd) or clear(cand + 0.15, d['S'])
                okD = clear(cand + 0.66, d['D'])
                if okS and okD:
                    if clear(cand + act_w + 0.30, d['G']):
                        side = 'right'
                        break
                    if clear(cand - 0.30, d['G']) and all(abs(cand - 0.30 - xs) >= 0.42 for xs, _ in pstubs):
                        side = 'left'
                        break
                cand = round(cand + 0.01, 3)
            px_list.append(cand)
            pside.append(side)
            if d['S'] != self.vdd:
                pstubs.append((cand + 0.15, d['S']))
            pstubs.append((cand + 0.66, d['D']))
            pstubs.append(((cand + act_w + 0.30) if side == 'right' else (cand - 0.30), d['G']))
            x = cand + act_w + 0.72
        self.x_p_end = x
        spans = {}
        for net, lst in self.stubs.items():
            xs = [s[0] for s in lst]
            spans[net] = [min(xs), max(xs)]
        for xx, net in pstubs:
            sp = spans.setdefault(net, [xx, xx])
            sp[0], sp[1] = min(sp[0], xx), max(sp[1], xx)
        # port x positions: right of the net's span, unique (>= 0.6 apart)
        self.port_x = {}
        prev = -1e9
        for net in sorted(self.ports, key=lambda n: spans.get(n, [ox, ox])[1]):
            sp = spans.setdefault(net, [ox, ox])
            xp = max(sp[1] + 0.6, prev + 0.6)
            while any(abs(xp - a) < 0.5 for a in self.avoid_x):
                xp = round(xp + 0.05, 3)
            self.port_x[net] = xp
            sp[1] = xp + 0.15
            prev = xp
        # nets with a single stub and no port need no track (dangling) -> still draw a track pad
        order = sorted(spans.items(), key=lambda kv: kv[1][0])
        tracks = []      # list of last x2 per track
        self.track_y = {}
        y0 = oy + hmax_n + 0.8
        for net, (x1, x2) in order:
            for i, last in enumerate(tracks):
                if x1 > last + 0.6:
                    tracks[i] = x2
                    self.track_y[net] = y0 + 0.5 * i
                    break
            else:
                tracks.append(x2)
                self.track_y[net] = y0 + 0.5 * (len(tracks) - 1)
        ntr = len(tracks)
        YP = y0 + 0.5 * (ntr - 1) + 0.9
        self.YP = YP
        hmax_p = max(d['w'] for d in pm) if pm else 1.0
        VDD_Y = YP + hmax_p + 0.75
        self.VDD_Y, self.VSS_Y = VDD_Y, VSS_Y
        # ---- PMOS row
        self.px = {}
        for d, px, side in zip(pm, px_list, pside):
            m = Mos(D, 'pmos', d['w'], d['l'], 1, px, YP)
            pad, gc = m.gate_strap('bottom', side, gap=0.10)
            self.px[d['name']] = m
            for term, i in (('S', 0), ('D', 1)):
                net = d[term]
                st = m.strip(i)
                if net == self.vdd:
                    D.box('M1', st[0], st[3], st[2], VDD_Y)
                else:
                    self._add(net, m.strip_x(i), st[1], False)
            self._add(d['G'], gc[0], gc[1] - 0.15, False)
        # ---- draw stubs and tracks
        for net, lst in self.stubs.items():
            y = self.track_y[net]
            xs = sorted(s[0] for s in lst)
            for xx, fy, up in lst:
                hw = 0.15 if abs(fy - y) < 0.7 else 0.08
                D.box('M1', xx - hw, min(fy, y), xx + hw, max(fy, y))
                D.vpad('Via1', xx, y, hi='h')
            for a, b in zip(xs, xs[1:]):
                if 0.005 < b - a < 0.48:
                    D.box('M1', a - 0.15, y - 0.15, b + 0.15, y + 0.15)
            x1, x2 = spans[net]
            if net in self.ports:
                # port: Via2 + Metal3 pad at the track end; the caller continues on Metal3
                xp = self.port_x[net]
                D.hwire('M2', x1, xp + 0.15, y, ext=False)
                D.vpad('Via2', xp, y, lo='h', hi='v')
                self.port_pos[net] = (xp, y)
            else:
                if x2 - x1 < 0.6:
                    x1, x2 = x1 - 0.3, x2 + 0.3
                D.hwire('M2', x1, x2, y, ext=False)
        # ---- rails, well, tie
        xr1, xr2 = ox - 1.0, max(self.x_n_end, self.x_p_end) + 0.3
        D.hwire('M1', xr1, xr2, VSS_Y, w=0.30, ext=False)
        D.box('NWell', xr1 - 0.5, YP - 0.6, xr2 + 0.5, VDD_Y + 1.2)
        D.tap_bar(xr1, VDD_Y + 0.4, xr2, VDD_Y + 0.7, kind='n', m1w=0.30)
        D.box('M1', xr1, VDD_Y - 0.15, xr2, VDD_Y + 0.7)
        self.extent = (xr1 - 0.5, VSS_Y - 0.5, xr2 + 0.5, VDD_Y + 1.2)
        return self



def shape_obs(cell, layer_key, margin=0.2, clip=None, exclude=()):
    """LEF obstruction rectangles (um) for `layer_key`: the bounding box of every merged shape of
    that layer in `cell` (hierarchy flattened), grown by `margin`, clipped to `clip` (x1, y1, x2, y2)
    and with the `exclude` boxes removed.  Used for Metal4 and above, where the obstruction must
    cover only what the layout really has so that the chip-level PDN can land its straps on the
    Metal3 supply bars (chip dry run 2026-09-19, pdngen PDN-0006 with full-area obstructions)."""
    ly = cell.layout()
    li = ly.layer(*LAYERS[layer_key])
    r = pya.Region(cell.begin_shapes_rec(li))
    r.merge()
    if margin:
        r.size(int(round(margin * 1000)))
        r.merge()
    if clip is not None:
        r &= pya.Region(pya.Box(*[int(round(v * 1000)) for v in clip]))
    for e in exclude:
        r -= pya.Region(pya.Box(*[int(round(v * 1000)) for v in e]))
    out = []
    for p in r.each():
        b = p.bbox()
        out.append((b.left / 1e3, b.bottom / 1e3, b.right / 1e3, b.top / 1e3))
    return sorted(out)


def write_lef(path, macro, W, H, pins, obs):
    """LEF 5.8 macro (CLASS BLOCK) with the given pins [(name, layer, (x1,y1,x2,y2), direction, use)]
    and obstructions [(layer, [rects])]; pin/obstruction layer names as in the PDK tech LEF."""
    L = ['VERSION 5.8 ;', 'BUSBITCHARS "[]" ;', 'DIVIDERCHAR "/" ;', '', 'MACRO %s' % macro,
         '  CLASS BLOCK ;', '  ORIGIN 0 0 ;', '  FOREIGN %s 0 0 ;' % macro, '  SIZE %g BY %g ;' % (W, H),
         '  SYMMETRY X Y ;']
    for name, layer, (x1, y1, x2, y2), direction, use in pins:
        L += ['  PIN %s' % name, '    DIRECTION %s ;' % direction, '    USE %s ;' % use, '    PORT',
              '      LAYER %s ;' % layer, '        RECT %g %g %g %g ;' % (r3(x1), r3(y1), r3(x2), r3(y2)),
              '    END', '  END %s' % name]
    L.append('  OBS')
    for layer, rects in obs:
        L.append('    LAYER %s ;' % layer)
        for (x1, y1, x2, y2) in rects:
            L.append('      RECT %g %g %g %g ;' % (r3(x1), r3(y1), r3(x2), r3(y2)))
    L += ['  END', 'END %s' % macro, '', 'END LIBRARY', '']
    open(path, 'w').write('\n'.join(L))
