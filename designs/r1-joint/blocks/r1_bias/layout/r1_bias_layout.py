#!/usr/bin/env python3
"""r1_bias layout generator (KLayout batch Python, PDK PCells from library SG13_dev). Track T9.

Run inside the pinned container (KLayout 0.30.9, PDK commit 8437402), from the repository root:
  G1_CPUSET=116-119 G1_WORKDIR=designs/r1-joint/blocks/r1_bias/layout flow/run.sh klayout -b -r r1_bias_layout.py
Writes, next to this script:
  r1_bias.gds              top cell r1_bias, prBoundary 189/4 = (0, 0) - (W, H)
  r1_bias_lvs.cdl          LVS reference: schematic/r1_bias.spice (netlist of record, revision 1d) flattened to CDL,
                           plus the layout dummies (PMOS 12/4 with every terminal on vdda)
  r1_bias_layout_meta.json bounding box, bands, channels, trunks, MIM landing points (for pex_build.py)
Method and helpers from blocks/r1_bgr/layout/r1_bgr_layout.py (same cell conventions, guard rings, channel router:
Metal2 stubs from the device taps, Metal3 horizontal tracks in the channels, Metal4 vertical trunks). The MIM
connections follow blocks/r1_osc/layout (top-plate tab to a TopVia1 + Via4 island, bottom plate by Via4).

Floorplan, bottom to top (the bandgap r1_bgr is on the west side, the consumers on the north side, C4 floorplan):
  vss bus (Metal3, pin)
  channel RB
  POR resistor band, p+ ring: rppd  D RRA x2 RRB x10 D | rhigh  D divider x27 D pull-down x27 D
     (MIM capacitors 32x32 cdel, 18x18 vrh, vrl, tapa above this band on Metal5/TopMetal1)
  channel R1
  POR HBT band: 4 npn13G2 (replica), p+ ring | thin-oxide output inverters (LV NMOS in a p+ ring, LV PMOS in a vdd well)
  channel H
  POR NMOS band (thick oxide), p+ ring
  channel NP
  POR PMOS band (one n-well on vdda)
  channel PS
  POR delay stack band: 2 x 10 series PMOS 0.5/4 (one n-well on vdda)          -- POR p+ ring ends here
  channel B
  revision 2 (D20) VREF buffer band r1_vbuf, own p+ ring:
     V2: NMOS bias diode XMB x5, tail XMT x2, sink XM8 x4 (sources on a Metal1 vss bar) | source follower XM7 x4 10/1
     channel V1 | V1a: input pair units A B B A (A = XM1, B = XM2, 8/24) | channel V2c | V1b: B A A B | channel V3c
     V3: PMOS mirror XM3/XM4 5/20 (one n-well on vdda, tie strip)
     compensation capacitor: two MIM plates 48.3 um over the band (TopMetal1 top plate x1, Metal5 bottom plate vss)
  channel B2
  cascode row B: dummy, 8 single-unit legs (+ ibvb for the buffer), replica cascodes MCR/MCL, dummy
  channel A
  cascode row A: dummy, 4 two-unit AFE legs, dummy
  channel M (gate bus pbias, mirror drains)
  mirror row: D + 15 units 12/4 (common centroid for the 2-unit AFE legs) + D, one n-well on vdda, same orientation
  vdda bus (Metal3, pin)
  output pins (Metal3, north edge)
Pins: west pbias, pcasc, vref (bandgap side); north the 11 outputs; east por_n, vdd, vref_b; vdda/vss buses span the width.
"""
import json
import os
import re
import sys

K = '/foss/pdks/ihp-sg13g2/libs.tech/klayout/python'
for p in [K, K + '/pycell4klayout-api/source/python']:
    sys.path.insert(0, p)
import pya  # noqa: E402
import sg13g2_pycell_lib  # noqa: E402,F401  (registers library SG13_dev)

HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(HERE, '..', 'schematic', 'r1_bias.spice')   # netlist of record, revision 2
lib = pya.Library.library_by_name('SG13_dev', 'sg13g2')
ly = pya.Layout()
ly.dbu = 0.001
LAYERS = {'Activ': (1, 0), 'GatPoly': (5, 0), 'Cont': (6, 0), 'pSD': (14, 0), 'NWell': (31, 0), 'TGO': (44, 0),
          'M1': (8, 0), 'M1pin': (8, 2), 'M1txt': (8, 25), 'Via1': (19, 0),
          'M2': (10, 0), 'M2pin': (10, 2), 'M2txt': (10, 25), 'Via2': (29, 0),
          'M3': (30, 0), 'M3pin': (30, 2), 'M3txt': (30, 25), 'Via3': (49, 0),
          'M4': (50, 0), 'M4txt': (50, 25), 'HeatTrans': (51, 0), 'Via4': (66, 0), 'M5': (67, 0), 'TopVia1': (125, 0), 'TM1': (126, 0),
          'prBoundary': (189, 4)}
L = {n: ly.layer(*v) for n, v in LAYERS.items()}
top = ly.create_cell('r1_bias')

CONT, CP = 0.16, 0.34      # contact size / pitch
VIA, VP = 0.19, 0.42       # via size / pitch
W3 = 0.3                   # signal wire width
TP = 0.6                   # channel track pitch
W = 120.0                  # macro width
# channel track counts (set from the router report; the generator stops on an overflow)
NT = dict(RB=2, R1=8, H=10, NP=16, PS=6, B=8, V1=8, V2c=8, V3c=8, B2=8, A=8, M=9)


def um(v):
    return int(round(v * 1000))


def box(layer, x1, y1, x2, y2):
    top.shapes(L[layer]).insert(pya.Box(um(min(x1, x2)), um(min(y1, y2)), um(max(x1, x2)), um(max(y1, y2))))


def ring(layer, x1, y1, x2, y2, w):
    outer = pya.Polygon(pya.Box(um(x1 - w), um(y1 - w), um(x2 + w), um(y2 + w)))
    outer.insert_hole(pya.Box(um(x1), um(y1), um(x2), um(y2)))
    top.shapes(L[layer]).insert(outer)


def label(layer, x, y, text):
    t = pya.Text(text, pya.Trans(pya.Point(um(x), um(y))))
    t.size = um(0.3)
    top.shapes(L[layer]).insert(t)


def square(layer, cx, cy, s):
    box(layer, cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2)


def pcell(name, params, x, y):
    pcv = lib.layout().add_pcell_variant(lib.layout().pcell_id(name), params)
    c = ly.cell(ly.add_lib_cell(lib, pcv))
    top.insert(pya.CellInstArray(c.cell_index(), pya.Trans(pya.Trans.R0, um(x), um(y))))
    return c


def cont_row(x1, x2, y):
    n = int((x2 - x1 - CONT) // CP) + 1
    x0 = (x1 + x2) / 2 - (n - 1) * CP / 2
    for i in range(n):
        square('Cont', x0 + i * CP, y, CONT)


def cont_col(y1, y2, x):
    n = int((y2 - y1 - CONT) // CP) + 1
    y0 = (y1 + y2) / 2 - (n - 1) * CP / 2
    for i in range(n):
        square('Cont', x, y0 + i * CP, CONT)


SEGS = {'M2': [], 'M4': []}


def reg(layer, net, x1, y1, x2, y2):
    if layer in SEGS:
        SEGS[layer].append((net, min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))


def mbox(layer, net, x1, y1, x2, y2):
    box(layer, x1, y1, x2, y2)
    reg(layer, net, x1, y1, x2, y2)


def cuts(layer, x, y, nx=1, ny=1):
    for i in range(nx):
        for j in range(ny):
            square(layer, x + (i - (nx - 1) / 2) * VP, y + (j - (ny - 1) / 2) * VP, VIA)
    return (x - (nx - 1) * VP / 2 - 0.15, y - (ny - 1) * VP / 2 - 0.15, x + (nx - 1) * VP / 2 + 0.15, y + (ny - 1) * VP / 2 + 0.15)


def via1(x, y, net, nx=1, ny=1):
    b = cuts('Via1', x, y, nx, ny)
    box('M1', *b)
    mbox('M2', net, *b)


def via2(x, y, net, nx=1, ny=1):
    b = cuts('Via2', x, y, nx, ny)
    mbox('M2', net, *b)
    box('M3', *b)


def via3(x, y, net, nx=1, ny=1):
    b = cuts('Via3', x, y, nx, ny)
    box('M3', *b)
    mbox('M4', net, *b)


def m2_v(x, y1, y2, net, w=W3):
    mbox('M2', net, x - w / 2, min(y1, y2) - w / 2, x + w / 2, max(y1, y2) + w / 2)


def guard_ring_p(x1, y1, x2, y2, w=0.30):
    """p+ substrate ring around the box: Activ + pSD, contacts, 0.26 um Metal1 ring. Returns the Metal1 centre lines."""
    ring('Activ', x1, y1, x2, y2, w)
    ring('pSD', x1 + 0.03, y1 + 0.03, x2 - 0.03, y2 - 0.03, w + 0.06)
    c = w / 2
    xl, xr, yb, yt = x1 - c, x2 + c, y1 - c, y2 + c
    for cy in (yb, yt):
        square('Cont', xl, cy, CONT)
        square('Cont', xr, cy, CONT)

    def side(a, b):
        n = int((b - a - CP) // CP)
        if n < 1:
            return []
        s = (a + b) / 2 - (n - 1) * CP / 2
        return [s + i * CP for i in range(n)]
    for x in side(xl, xr):
        square('Cont', x, yb, CONT)
        square('Cont', x, yt, CONT)
    for y in side(yb, yt):
        square('Cont', xl, y, CONT)
        square('Cont', xr, y, CONT)
    hw = 0.13
    ring('M1', xl + hw, yb + hw, xr - hw, yt - hw, 2 * hw)
    return xl, yb, xr, yt


def ntap_strip(x1, y1, x2, y2):
    """n+ well tie (Activ without pSD, inside an NWell drawn by the caller), contacts, Metal1"""
    box('Activ', x1, y1, x2, y2)
    box('M1', x1, y1, x2, y2)
    cont_row(x1 + 0.07, x2 - 0.07, (y1 + y2) / 2)


# ---------------------------------------------------------------------------------------------
# Router (r1_bgr): channels with Metal3 tracks, Metal2 stubs from device taps, Metal4 trunks
class Channel:
    def __init__(self, name, y0, y1):
        self.name, self.y0, self.y1 = name, y0, y1
        self.taps = []          # (net, x, y_from)
        self.extra = {}         # net -> extra x positions (pins, trunks)
        self.track = {}         # net -> y

    def tap(self, net, x, y_from):
        self.taps.append((net, x, y_from))

    def nets(self):
        s = {}
        for n, x, _ in self.taps:
            s.setdefault(n, []).append(x)
        for n, xs in self.extra.items():
            s.setdefault(n, []).extend(xs)
        return s


CH = {}
POINTS = {}      # net -> list of (x, y): fixed Metal4 landing points
TRUNK_SPEC = {}  # net -> dict(x=..., w=...)
FIXED_M4 = []    # (net, x1, y1, x2, y2) Metal4 pads that trunks of other nets must avoid
PIN_N = []       # nets with a pin on the north edge (at the trunk x)


def m1_tap(ch, net, x, y):
    """Via1 on existing Metal1 at (x, y); Metal2 stub to the channel track is drawn by the router"""
    via1(x, y, net)
    CH[ch].tap(net, x, y)


def ch_h(n):
    return 0.3 + n * TP + 0.15


# =============================================================================================
# vertical plan
YB_VSS = (0.0, 2.0)
y = 2.15
CH['RB'] = Channel('RB', y, y + ch_h(NT['RB']))
y = CH['RB'].y1
RES_RING_IN_Y1 = y + 0.45                      # inner box of the resistor ring
YA = RES_RING_IN_Y1 + 1.3                      # resistor body bottom
LMAX = 27.28
RES_RING_IN_Y2 = YA + LMAX + 1.3
y = RES_RING_IN_Y2 + 0.35
CH['R1'] = Channel('R1', y, y + ch_h(NT['R1']))
YH = CH['R1'].y1 + 0.1 + 4.03                  # HBT centre row
y = YH + 4.48 + 0.1
CH['H'] = Channel('H', y, y + ch_h(NT['H']))
YN = CH['H'].y1 + 0.1 + 0.3 + 1.8              # NMOS band device bottom
NR_TOP = YN + 4.0 + 1.4
y = NR_TOP + 0.3 + 0.1
CH['NP'] = Channel('NP', y, y + ch_h(NT['NP']))
YP = CH['NP'].y1 + 1.3                         # PMOS band device bottom
PW_TOP = YP + 13.0
y = PW_TOP + 0.1
CH['PS'] = Channel('PS', y, y + ch_h(NT['PS']))
YS = CH['PS'].y1 + 1.3                         # delay stack device bottom
SW_TOP = YS + 3.5
POR_RING_IN_Y2 = SW_TOP + 0.5
y = POR_RING_IN_Y2 + 0.3 + 0.1
CH['B'] = Channel('B', y, y + ch_h(NT['B']))
# revision 2: buffer band
VB_RING_IN_Y1 = CH['B'].y1 + 0.1 + 0.3
Y_V2 = VB_RING_IN_Y1 + 1.8                     # NMOS bias/sink row device bottom
V2_TOP = Y_V2 + 10.1
V2_RAIL = V2_TOP + 0.45                        # Metal1 vss bar (sources of the V2 row)
y = V2_RAIL + 0.15 + 0.3
CH['V1'] = Channel('V1', y, y + ch_h(NT['V1']))
Y_V1A = CH['V1'].y1 + 1.3                      # input pair row a
y = Y_V1A + 8.0 + 0.8
CH['V2c'] = Channel('V2c', y, y + ch_h(NT['V2c']))
Y_V1B = CH['V2c'].y1 + 1.3                     # input pair row b
y = Y_V1B + 8.0 + 0.8
CH['V3c'] = Channel('V3c', y, y + ch_h(NT['V3c']))
Y_V3 = CH['V3c'].y1 + 1.3                      # PMOS row (n-well on vdda)
TIE_V3 = (Y_V3 + 11.6, Y_V3 + 12.0)
V3_TOP = Y_V3 + 13.0
VB_RING_IN_Y2 = V3_TOP + 0.5
y = VB_RING_IN_Y2 + 0.3 + 0.1
CH['B2'] = Channel('B2', y, y + ch_h(NT['B2']))
BIAS_RING_IN_Y1 = CH['B2'].y1 + 0.1 + 0.3
YCB = BIAS_RING_IN_Y1 + 1.8                    # cascode row B device bottom
y = YCB + 14.4 + 0.1
CH['A'] = Channel('A', y, y + ch_h(NT['A']))
YCA = CH['A'].y1 + 1.3
y = YCA + 14.4 + 0.1
CH['M'] = Channel('M', y, y + ch_h(NT['M']))
YD = CH['M'].y1 + 1.3                          # mirror row device bottom
WU, LU = 12.0, 4.0                             # unit leg device (netlist of record)
MW_TOP = YD + WU + 3.0
BIAS_RING_IN_Y2 = MW_TOP + 0.5
VDDA_Y0 = BIAS_RING_IN_Y2 + 0.3 + 0.5
VDDA_Y1 = VDDA_Y0 + 2.0
H = round(VDDA_Y1 + 1.6, 3)
PIN_Y = H - 0.7
VDDA_MID = (VDDA_Y0 + VDDA_Y1) / 2
VSS_MID = 1.0

print('plan', ' '.join('%s=%.2f..%.2f' % (n, c.y0, c.y1) for n, c in CH.items()), 'YA %.2f YH %.2f YN %.2f YP %.2f YS %.2f YV2 %.2f YV1A %.2f YV1B %.2f YV3 %.2f YCB %.2f YCA %.2f YD %.2f H %.2f' % (YA, YH, YN, YP, YS, Y_V2, Y_V1A, Y_V1B, Y_V3, YCB, YCA, YD, H))
# ---------------------------------------------------------------------------------------------
# power buses and edge columns
box('M3', 0, YB_VSS[0], W, YB_VSS[1])
box('M3pin', 0, YB_VSS[0], W, YB_VSS[1])
label('M3txt', W / 2, VSS_MID, 'vss')
box('M3', 0, VDDA_Y0, W, VDDA_Y1)
box('M3pin', 0, VDDA_Y0, W, VDDA_Y1)
label('M3txt', W / 2, VDDA_MID, 'vdda')

VCOL_L, VCOL_R = 1.0, W - 1.0
for x in (VCOL_L, VCOL_R):
    mbox('M2', 'vss', x - 0.5, 0.3, x + 0.5, H - 0.3)
    for yy in (0.6, 1.4):
        for dx in (-0.21, 0.21):
            square('Via2', x + dx, yy, VIA)
# outer p+ ring of the block, under the vss columns
OR = guard_ring_p(1.15, 1.15, W - 1.15, H - 1.15)
for x in (OR[0], OR[2]):
    yy = 3.0
    while yy < H - 3.0:
        box('M1', x - 0.25, yy - 0.3, x + 0.25, yy + 0.3)
        cuts('Via1', x, yy, 1, 2)
        yy += 10.0


def ring_to_vss_col(xl, xr, y, col_x):
    """p+ ring Metal1 side -> Via1+Via2 -> Metal3 jumper -> Via2 on the side column"""
    xs = xl if col_x < xl else xr
    box('M1', xs - 0.45, y - 0.25, xs + 0.45, y + 0.25)
    b = cuts('Via1', xs, y, 2, 1)
    mbox('M2', 'vss', b[0], b[1], b[2], b[3])
    cuts('Via2', xs, y, 2, 1)
    box('M3', min(xs, col_x) - 0.4, y - 0.15, max(xs, col_x) + 0.4, y + 0.15)
    cuts('Via2', col_x, y, 2, 1)


def ring_both(R, y):
    ring_to_vss_col(R[0], R[2], y, VCOL_L)
    ring_to_vss_col(R[0], R[2], y, VCOL_R)


# =============================================================================================
# MOS helpers (r1_bgr). PCell origin = Activ lower-left; footprint lf = ng*l + (ng-1)*0.38 + 0.68.
KIND = {'p': 'pmosHV', 'n': 'nmosHV', 'pl': 'pmos', 'nl': 'nmos'}


def mos_long(kind, w, l, x, y):
    """single-finger MOS with L > 10 um (the PDK PCell limits L to 10 um and warns "using maximum length 10u"):
    the 10 um PCell is flattened into the top cell and stretched in x across the gate (shapes right of the gate
    centre move by l - 10, shapes that span it grow by l - 10). Revision 2 input pair 8/24 and mirror 5/20."""
    pcv = lib.layout().add_pcell_variant(lib.layout().pcell_id(KIND[kind]), {'w': '%gu' % w, 'l': '10u', 'ng': 1})
    c = ly.cell(ly.add_lib_cell(lib, pcv))
    gc = um(0.34 + 5.0)
    dl = um(l - 10.0)
    for li in ly.layer_indexes():
        it = c.begin_shapes_rec(li)
        while not it.at_end():
            sh = it.shape()
            if sh.is_text():
                it.next()
                continue
            pg = sh.polygon.transformed(it.trans())
            b = pg.bbox()
            if b.left >= gc:
                pg = pg.moved(dl, 0)
            elif b.right > gc:
                assert pg.is_box(), ('non-box shape across the gate', kind, w, l, li)
                pg = pya.Polygon(pya.Box(b.left, b.bottom, b.right + dl, b.top))
            top.shapes(li).insert(pg.moved(um(x), um(y)))
            it.next()
    ly.delete_cell(c.cell_index())
    lf = l + 0.68
    return dict(x=x, y=y, w=w, l=l, lf=lf, gx=x + 0.34 + l / 2)


def mos(kind, w, l, x, y, ng=1):
    lf = ng * l + (ng - 1) * 0.38 + 0.68
    if l > 10.0:
        assert ng == 1 and w <= 10.0
        return mos_long(kind, w, l, x, y)
    if w > 10.0:
        # The PDK PCell limits one finger to 10 um (pmosHV_maxW); the netlist of record unit is 12/4 with one finger.
        # Draw the 10 um PCell and extend every layer of it by w - 10 at the top, with the same contact pitch.
        assert kind == 'p' and ng == 1
        pcell(KIND[kind], {'w': '10u', 'l': '%gu' % l, 'ng': 1}, x, y)
        e = w - 10.0
        box('Activ', x, y + 9.7, x + lf, y + w)
        box('GatPoly', x + 0.34, y + 9.9, x + 0.34 + l, y + w + 0.18)
        box('HeatTrans', x + 0.34, y + 9.9, x + 0.34 + l, y + w + 0.18)
        for xs in (x + 0.07, x + lf - 0.23):
            box('M1', xs, y + 9.7, xs + 0.16, y + w)
            yc = y + 10.27
            while yc + 0.16 <= y + w - 0.07 + 1e-9:
                box('Cont', xs, yc, xs + 0.16, yc + 0.16)
                yc += 0.345
        box('pSD', x - 0.18, y + 9.6, x + lf + 0.18, y + w + 0.4)
        box('NWell', x - 0.62, y + 9.6, x + lf + 0.62, y + w + 0.62)
        box('TGO', x - 0.62, y + 9.6, x + lf + 0.62, y + w + 0.62)
        return dict(x=x, y=y, w=w, l=l, lf=lf, gx=x + 0.34 + l / 2)
    pcell(KIND[kind], {'w': '%gu' % (w * ng), 'l': '%gu' % l, 'ng': ng}, x, y)
    return dict(x=x, y=y, w=w, l=l, lf=lf, gx=x + 0.34 + l / 2)


def gate_tab(d):
    gx, y = d['gx'], d['y']
    box('GatPoly', gx - 0.15, y - 1.0, gx + 0.15, y - 0.18)
    square('Cont', gx, y - 0.70, CONT)
    box('M1', gx - 0.15, y - 0.95, gx + 0.15, y - 0.45)
    return gx, y - 0.70


def sd_pad(d, yv):
    x = d['x'] + d['lf'] + 0.15
    box('M1', d['x'] + d['lf'] - 0.23, yv - 0.2, x + 0.2, yv + 0.2)
    return x, yv


DEVS = []        # (name, model, d, g, s, b, w, l) as drawn (for the meta file)


def mos_dev(name, kind, w, l, x, y, Lnet, Rnet, Gnet, rail, rail_y, ch_up, ch_down, gap=1.0):
    """one single-finger MOS: left strip -> rail (Metal1 up to rail_y) or a tap up into ch_up; right strip -> rail or
    a pad tap down into ch_down; gate tab below -> tap down into ch_down. Returns the next x."""
    d = mos(kind, w, l, x, y)
    gx, gy = gate_tab(d)
    m1_tap(ch_down, Gnet, gx, gy)
    if Lnet == rail:
        box('M1', x + 0.07, y + w - 0.1, x + 0.23, rail_y)
    else:
        box('M1', x + 0.07, y + w - 0.1, x + 0.23, y + w + 0.6)
        m1_tap(ch_up, Lnet, x + 0.15, y + w + 0.45)
    if Rnet == rail:
        box('M1', x + d['lf'] - 0.23, y + w - 0.1, x + d['lf'] - 0.07, rail_y)
    else:
        px, py = sd_pad(d, y + min(0.5, w / 2))
        m1_tap(ch_down, Rnet, px, py)
    DEVS.append((name, KIND[kind], w, l, x, y))
    return x + d['lf'] + gap


# =============================================================================================
# Band 1: POR resistors (rppd replica divider, rhigh VDDA divider and por_raw pull-down)
XA0, PA = 6.0, 1.9
RPPD = ['D'] + ['RA'] * 2 + ['RB'] * 10 + ['D']
RPPD_L = {'RA': 22.95, 'RB': 26.03}
XR0, PR = XA0 + 13 * PA + 1.0 + 1.2, 1.4
RHI = ['D'] + ['DV'] * 27 + ['D'] + ['PD'] * 27 + ['D']
PD_L = [27.22] * 26 + [27.28]
assert abs(sum(PD_L) - 735.0) < 1e-6 and abs(2 * 22.95 - 45.9) < 1e-9 and abs(10 * 26.03 - 260.3) < 1e-6


def rp_x(i):
    return XA0 + PA * i


def rh_x(j):
    return XR0 + PR * j


# rppd: the RA units are lifted so that every top head of the chain is at the same height
RP_Y = {}
RP_LEN = {}
for i, k in enumerate(RPPD):
    ln = RPPD_L['RB'] if k in ('RB', 'D') else RPPD_L['RA']
    if k == 'D':
        ln = RPPD_L['RA'] if i == 0 else RPPD_L['RB']
    yb = YA + (RPPD_L['RB'] - ln)
    RP_Y[i], RP_LEN[i] = yb, ln
    x = rp_x(i)
    if k == 'D':
        box('GatPoly', x, yb - 0.43, x + 1.0, yb + ln + 0.43)
        box('pSD', x - 0.18, yb - 0.61, x + 1.18, yb + ln + 0.61)
    else:
        pcell('rppd', {'w': '1u', 'l': '%gu' % ln, 'b': 0, 'Calculate': 'R'}, x, yb)


def rp_head(i, end):
    x, yb, ln = rp_x(i), RP_Y[i], RP_LEN[i]
    return (x + 0.02, yb + ln + 0.13, x + 0.98, yb + ln + 0.43) if end == 't' else (x + 0.02, yb - 0.43, x + 0.98, yb - 0.13)


RH_LEN = {}
for j, k in enumerate(RHI):
    x = rh_x(j)
    if k == 'DV':
        ln = 27.0
    elif k == 'PD':
        ln = PD_L[j - 29]
    else:
        ln = 27.0 if j < 56 else 27.28
    RH_LEN[j] = ln
    if k == 'D':
        box('GatPoly', x, YA - 0.43, x + 0.5, YA + ln + 0.43)
        box('pSD', x - 0.18, YA - 0.61, x + 0.68, YA + ln + 0.61)
    else:
        pcell('rhigh', {'w': '0.5u', 'l': '%gu' % ln, 'b': 0, 'Calculate': 'R'}, x, YA)


def rh_head(j, end):
    x, ln = rh_x(j), RH_LEN[j]
    return (x + 0.02, YA + ln + 0.15, x + 0.48, YA + ln + 0.41) if end == 't' else (x + 0.02, YA - 0.41, x + 0.48, YA - 0.15)


def chain(cols, headf):
    """series chain: unit k enters at the top for even k; strap after unit k at the bottom (k even) or top (k odd).
    Returns the node head after every unit: list of (end, (x, y)) where end is 't' or 'b'."""
    nodes = []
    for k in range(len(cols)):
        end = 'b' if k % 2 == 0 else 't'
        a = headf(cols[k], end)
        if k + 1 < len(cols):
            b = headf(cols[k + 1], end)
            box('M1', a[0], min(a[1], b[1]), b[2], max(a[3], b[3]))
            nodes.append((end, ((a[2] + b[0]) / 2, (min(a[1], b[1]) + max(a[3], b[3])) / 2)))
        else:
            nodes.append((end, ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2)))
    return nodes


def head_c(h):
    return (h[0] + h[2]) / 2, (h[1] + h[3]) / 2


def res_tap(net, end, x, y):
    if end == 't':
        m1_tap('R1', net, x, y)
    else:
        m1_tap('RB', net, x, y)


def res_to_vss_bus(x, y):
    via1(x, y, 'vss')
    m2_v(x, y, VSS_MID, 'vss')
    via2(x, VSS_MID, 'vss', 1, 2)


# rppd chain: vrh (top of RA0) - RA0 - RA1 - vrl (top) - RB x10 - vq (top)
rpn = chain(list(range(1, 13)), rp_head)
assert rpn[1][0] == 't' and rpn[11][0] == 't'
x, yy = head_c(rp_head(1, 't'))
res_tap('xpor_vrh', 't', x, yy)
res_tap('xpor_vrl', 't', *rpn[1][1])
res_tap('xpor_vq', 't', *rpn[11][1])
# rhigh divider: vdda (top of unit 0) - 16 units - na (top) - 1 unit - tapa (bottom) - 10 units - vss (bottom)
dvn = chain(list(range(1, 28)), rh_head)
assert dvn[15][0] == 't' and dvn[16][0] == 'b' and dvn[26][0] == 'b'
x, yy = head_c(rh_head(1, 't'))
box('M1', x - 0.23, yy - 0.2, x + 0.23, yy + 0.25)
res_tap('vdda', 't', x, yy)
res_tap('xpor_na', 't', *dvn[15][1])
res_tap('xpor_tapa', 'b', *dvn[16][1])
res_to_vss_bus(*dvn[26][1])
# pull-down: por_raw (top of unit 0) - 27 units - vss (bottom)
pdn = chain(list(range(29, 56)), rh_head)
assert pdn[26][0] == 'b'
x, yy = head_c(rh_head(29, 't'))
box('M1', x - 0.23, yy - 0.2, x + 0.23, yy + 0.25)
res_tap('xpor_por_raw', 't', x, yy)
res_to_vss_bus(*pdn[26][1])
RR = guard_ring_p(XA0 - 1.2, RES_RING_IN_Y1, rh_x(56) + 0.5 + 1.2, RES_RING_IN_Y2)
ring_both(RR, YA + 14.0)

# =============================================================================================
# MIM capacitors above the resistor band (Metal5 bottom plates on vss, TopMetal1 top plates)
CAPS = []
MIM_Y = YA - 0.5
MIMS = [('XPOR.XCDEL', 'xpor_cdel', 32.0), ('XPOR.XCF_vrh', 'xpor_vrh', 18.0), ('XPOR.XCF_vrl', 'xpor_vrl', 18.0),
        ('XPOR.XCF_tapa', 'xpor_tapa', 18.0)]
xm = 10.0
mx = []
for name, net, s in MIMS:
    pcell('cmim', {'w': '%gu' % s, 'l': '%gu' % s, 'Calculate': 'C'}, xm, MIM_Y)
    mx.append((name, net, s, xm))
    xm += s + 3.0
# bottom-plate join (Metal5 strip along the bottom margins) and one vss landing (Via4 -> Metal4 -> vss trunk)
box('M5', mx[0][3] - 0.6, MIM_Y - 0.6, mx[-1][3] + mx[-1][2] + 0.6, MIM_Y)
XVSS_T = mx[0][3] + 1.5
for dx in (0.0, 0.42):
    square('Via4', XVSS_T - 0.21 + dx, MIM_Y - 0.3, VIA)
mbox('M4', 'vss', XVSS_T - 0.5, MIM_Y - 0.5, XVSS_T + 0.5, MIM_Y - 0.1)
TRUNK_SPEC['vss'] = dict(x=XVSS_T, w=1.0)
POINTS.setdefault('vss', []).append((XVSS_T, MIM_Y - 0.3))
POINTS['vss'].append((XVSS_T, VSS_MID))
for i in range(2):
    for j in range(3):
        square('Via3', XVSS_T - 0.21 + 0.42 * i, VSS_MID - 0.42 + 0.42 * j, VIA)
# top-plate tabs up to islands (TopVia1 + Via4) landing on the net's Metal4 trunk
for name, net, s, x0 in mx:
    xi = x0 + s / 2
    yi = MIM_Y + s + 2.4
    box('TM1', xi - 0.82, MIM_Y + s - 0.6, xi + 0.82, yi + 0.82)
    square('TopVia1', xi, yi, 0.42)
    square('M5', xi, yi, 0.66)
    square('Via4', xi, yi, VIA)
    mbox('M4', net, xi - 0.33, yi - 0.33, xi + 0.33, yi + 0.33)
    TRUNK_SPEC[net] = dict(x=xi, w=0.6)
    POINTS.setdefault(net, []).append((xi, yi))
    CAPS.append(dict(name=name, net_top=net, net_bot='vss', w=s, l=s, top=(xi, yi), bot=(XVSS_T, MIM_Y - 0.3)))

# =============================================================================================
# Band 2: HBT replica (4 x npn13G2, collector = base = vq, emitter = vss) and the thin-oxide output stage
PBX = 6.3
XHB0 = 9.0


def hbt_q(x, y):
    pcell('npn13G2', {'Nx': 1}, x, y)
    reg('M2', 'vss', x - 0.925, y - 0.785, x + 0.925, y + 0.77)      # emitter Metal2 pad of the PCell (vss)
    xl, xr, yb, yt = x - 2.90, x + 2.90, y - 2.88, y + 3.33
    cont_row(x - 2.75, x + 2.75, yb)
    cont_row(x - 2.75, x + 2.75, yt)
    cont_col(y - 2.60, y + 3.05, xl)
    cont_col(y - 2.60, y + 3.05, xr)
    hw = 0.13
    ring('M1', xl + hw, yb + hw, xr - hw, yt - hw, 2 * hw)
    box('M1', x - 0.92, y - 1.26, x - 0.62, y + 1.25)      # collector-base strap
    box('M1', x - 0.925, y + 1.01, x + 0.925, y + 1.75)    # collector Metal1 extended for the Via1 at y + 1.5
    cuts('Via2', x, y - 0.6, 4, 1)                         # emitter -> Metal3 vss row track
    m1_tap('H', 'xpor_vq', x - 0.6, y + 1.5)


for i in range(4):
    hbt_q(XHB0 + PBX * i, YH)
DEVS.append(('XPOR.XQR_*', 'npn13G2 x4', 0, 0, XHB0, YH))
HB = guard_ring_p(XHB0 - 3.15 - 0.6, YH - 3.13 - 0.6, XHB0 + PBX * 3 + 3.15 + 0.6, YH + 3.58 + 0.6)
for i in range(4):
    x = XHB0 + PBX * i
    box('M1', x - 0.15, YH + 3.20, x + 0.15, HB[3])
    box('M1', x - 0.15, HB[1], x + 0.15, YH - 2.75)
box('M1', HB[0], YH - 0.15, XHB0 - 2.77, YH + 0.15)
box('M1', XHB0 + PBX * 3 + 2.77, YH - 0.15, HB[2], YH + 0.15)
box('M3', VCOL_L - 0.4, YH - 0.6 - 0.45, XHB0 + PBX * 3 + 0.8, YH - 0.6 + 0.45)   # emitter track to the vss column
cuts('Via2', VCOL_L, YH - 0.6, 2, 2)
ring_to_vss_col(HB[0], HB[2], YH + 2.6, VCOL_L)

# thin-oxide output stage (1.2 V domain): XDN1/XDN2 in a p+ ring, XDP1/XDP2 in a vdd n-well
YLV = YH - 2.0
x = XHB0 + PBX * 3 + 3.15 + 0.9 + 2.5
xn0 = x
for name, Rn, Gn in (('XPOR.XDN1', 'xpor_o3', 'xpor_por_raw'), ('XPOR.XDN2', 'por_n', 'xpor_o3')):
    x = mos_dev(name, 'nl', 0.5, 0.13, x, YLV, 'vss', Rn, Gn, 'vss', YLV + 0.5 + 1.25, 'H', 'R1', gap=1.0)
LVN = guard_ring_p(xn0 - 1.0, YLV - 1.8, x - 1.0 + 1.0, YLV + 0.5 + 1.1)
xp0 = x + 3.5
x = xp0
for name, Rn, Gn in (('XPOR.XDP1', 'xpor_o3', 'xpor_por_raw'), ('XPOR.XDP2', 'por_n', 'xpor_o3')):
    x = mos_dev(name, 'pl', 1.0, 0.13, x, YLV, 'vdd', Rn, Gn, 'vdd', YLV + 1.0 + 1.7, 'H', 'R1', gap=1.0)
ntap_strip(xp0 - 0.2, YLV + 2.3, x - 1.0 + 0.4, YLV + 2.7)
box('NWell', xp0 - 0.8, YLV - 0.8, x - 1.0 + 0.9, YLV + 3.2)
m1_tap('H', 'vdd', xp0 + 1.0, YLV + 2.5)
box('M1', HB[2], YH - 2.15, LVN[0], YH - 1.85)        # LV NMOS ring bridged to the HBT ring (vss)

# =============================================================================================
# Band 3: POR NMOS (thick oxide, body vss), sources on vss up into the p+ ring
X0 = 6.0
NMOS = [  # name, w, l, L (top), R (bottom pad), G
    ('XPOR.XCA.XML1', 2, 4, 'vss', 'xpor_xca_d1', 'xpor_xca_d1'),
    ('XPOR.XCA.XML2', 2, 4, 'vss', 'xpor_xca_d2', 'xpor_xca_d1'),
    ('XPOR.XCA.XMG', 1, 2, 'vss', 'xpor_oa', 'xpor_xca_d2'),
    ('XPOR.XIA.XN', 0.5, 0.5, 'vss', 'xpor_gooda', 'xpor_oa'),
    ('XPOR.XHA', 1, 0.5, 'xpor_tapa', 'xpor_na', 'xpor_gooda'),
    ('XPOR.XNR.XN1', 1, 0.5, 'xpor_xnr_x', 'xpor_rst', 'xpor_gooda'),
    ('XPOR.XNR.XN2', 1, 0.5, 'vss', 'xpor_xnr_x', 'xpor_goodd'),
    ('XPOR.XRST', 1, 0.5, 'vss', 'xpor_cdel', 'xpor_rst'),
    ('XPOR.XSCH.XN1', 0.5, 0.5, 'vss', 'xpor_xsch_sn', 'xpor_cdel'),
    ('XPOR.XSCH.XN2', 0.5, 0.5, 'xpor_xsch_sn', 'xpor_sy', 'xpor_cdel'),
    ('XPOR.XSCH.XN3', 0.5, 0.5, 'vdda', 'xpor_xsch_sn', 'xpor_sy'),
    ('XPOR.XIR.XN', 0.5, 0.5, 'vss', 'xpor_ready', 'xpor_sy'),
    ('XPOR.XDPS', 1, 0.5, 'vdd', 'xpor_por_raw', 'xpor_ready'),
    ('XPOR.XNL', 4, 4, 'vss', 'xpor_nl', 'xpor_nl'),
    ('XPOR.XNM', 4, 4, 'vss', 'xpor_pl', 'xpor_nl'),
    ('XPOR.XID.XN', 0.5, 0.5, 'vss', 'xpor_goodd', 'xpor_od'),
    ('XPOR.XIDB.XN', 0.5, 0.5, 'vss', 'xpor_badd', 'xpor_goodd'),
    ('XPOR.XHD1', 1, 0.5, 'xpor_vrl', 'xpor_refd', 'xpor_goodd'),
    ('XPOR.XHD2', 1, 0.5, 'xpor_vrh', 'xpor_refd', 'xpor_badd'),
    ('XPOR.XCD.XMG', 1, 2, 'vss', 'xpor_od', 'xpor_xcd_d2'),
    ('XPOR.XCD.XML2', 2, 4, 'vss', 'xpor_xcd_d2', 'xpor_xcd_d1'),
    ('XPOR.XCD.XML1', 2, 4, 'vss', 'xpor_xcd_d1', 'xpor_xcd_d1'),
]
x = X0
for name, w, l, Ln, Rn, Gn in NMOS:
    x = mos_dev(name, 'n', w, l, x, YN, Ln, Rn, Gn, 'vss', NR_TOP + 0.15, 'NP', 'H', gap=1.0)
XN_END = x - 1.0
box('TGO', X0 - 0.5, YN - 1.5, XN_END + 0.5, NR_TOP - 0.6)
NR = guard_ring_p(X0 - 1.2, YN - 1.8, XN_END + 1.2, NR_TOP)
ring_both(NR, YN + 2.0)
print('NMOS band end x %.2f' % XN_END)

# =============================================================================================
# Band 4: POR PMOS (thick oxide, one n-well on vdda); sources on vdda up into the tie strip
PMOS = [  # name, w, l, L (top), R (bottom pad), G
    ('XPOR.XMPR', 10, 4, 'vdda', 'xpor_dr', 'pbias'),
    ('XPOR.XMPL', 10, 4, 'vdda', 'xpor_dl', 'pbias'),
    ('XPOR.XPL', 10, 4, 'vdda', 'xpor_pl', 'xpor_pl'),
    ('XPOR.XCPL', 10, 10, 'vdda', 'vdda', 'xpor_pl'),
    ('XPOR.XCA.XMT', 5, 4, 'vdda', 'xpor_xca_tail', 'xpor_pl'),
    ('XPOR.XCA.XM1', 8, 2, 'xpor_xca_tail', 'xpor_xca_d1', 'xpor_tapa'),
    ('XPOR.XCA.XM2', 8, 2, 'xpor_xca_tail', 'xpor_xca_d2', 'xpor_vrh'),
    ('XPOR.XCA.XMGL', 2.5, 4, 'vdda', 'xpor_oa', 'xpor_pl'),
    ('XPOR.XIA.XP', 1, 0.5, 'vdda', 'xpor_gooda', 'xpor_oa'),
    ('XPOR.XNR.XP1', 1, 0.5, 'vdda', 'xpor_rst', 'xpor_gooda'),
    ('XPOR.XNR.XP2', 1, 0.5, 'vdda', 'xpor_rst', 'xpor_goodd'),
    ('XPOR.XSCH.XP1', 1, 0.5, 'vdda', 'xpor_xsch_sp', 'xpor_cdel'),
    ('XPOR.XSCH.XP2', 1, 0.5, 'xpor_xsch_sp', 'xpor_sy', 'xpor_cdel'),
    ('XPOR.XSCH.XP3', 1, 0.5, 'vss', 'xpor_xsch_sp', 'xpor_sy'),
    ('XPOR.XIR.XP', 1, 0.5, 'vdda', 'xpor_ready', 'xpor_sy'),
    ('XPOR.XID.XP', 1, 0.5, 'vdda', 'xpor_goodd', 'xpor_od'),
    ('XPOR.XIDB.XP', 1, 0.5, 'vdda', 'xpor_badd', 'xpor_goodd'),
    ('XPOR.XCD.XMGL', 2.5, 4, 'vdda', 'xpor_od', 'xpor_pl'),
    ('XPOR.XCD.XM2', 8, 2, 'xpor_xcd_tail', 'xpor_xcd_d2', 'xpor_refd'),
    ('XPOR.XCD.XM1', 8, 2, 'xpor_xcd_tail', 'xpor_xcd_d1', 'vdd'),
    ('XPOR.XCD.XMT', 5, 4, 'vdda', 'xpor_xcd_tail', 'xpor_pl'),
]
TIE_P = (YP + 11.6, YP + 12.0)
x = X0
for name, w, l, Ln, Rn, Gn in PMOS:
    x = mos_dev(name, 'p', w, l, x, YP, Ln, Rn, Gn, 'vdda', TIE_P[1], 'PS', 'NP', gap=0.9)
XP_END = x - 0.9
box('NWell', X0 - 1.2, YP - 1.2, XP_END + 1.2, PW_TOP)
box('TGO', X0 - 1.2, YP - 1.5, XP_END + 1.2, PW_TOP)
ntap_strip(X0 - 0.3, TIE_P[0], XP_END + 0.3, TIE_P[1])
for xx in (X0 + 2.0, XP_END - 2.0):
    m1_tap('PS', 'vdda', xx, (TIE_P[0] + TIE_P[1]) / 2)
print('PMOS band end x %.2f' % XP_END)

# =============================================================================================
# Band 5: delay stack, 2 x 10 series PMOS 0.5/4 (one Activ per 10; the inner diffusions are the stack nodes)
TIE_S = (YS + 2.1, YS + 2.5)
XS0 = X0
d1 = mos('p', 0.5, 4, XS0, YS, ng=10)
XS1 = XS0 + d1['lf'] + 1.2
d2 = mos('p', 0.5, 4, XS1, YS, ng=10)
for d in (d1, d2):     # gate bar under all fingers, one contact
    g0 = d['x'] + 0.34
    g1 = d['x'] + d['lf'] - 0.34
    box('GatPoly', g0, YS - 0.56, g1, YS - 0.10)
xg = d1['x'] + 0.34 + 2.0
box('GatPoly', xg - 0.15, YS - 1.0, xg + 0.15, YS - 0.1)
square('Cont', xg, YS - 0.70, CONT)
box('M1', xg - 0.15, YS - 0.95, xg + 0.15, YS - 0.45)
m1_tap('PS', 'xpor_pl', xg, YS - 0.70)
xg2 = d2['x'] + 0.34 + 2.0
box('GatPoly', xg2 - 0.15, YS - 1.0, xg2 + 0.15, YS - 0.1)
square('Cont', xg2, YS - 0.70, CONT)
box('M1', xg2 - 0.15, YS - 0.95, xg2 + 0.15, YS - 0.45)
m1_tap('PS', 'xpor_pl', xg2, YS - 0.70)
box('M1', XS0 + 0.07, YS + 0.2, XS0 + 0.23, TIE_S[1])                  # stack top (vdda) to the tie
xa = d1['x'] + d1['lf'] - 0.15
xb = d2['x'] + 0.15
box('M1', xa - 0.08, YS + 0.2, xa + 0.08, YS + 1.15)                   # node st_10: end of stack 1 to start of 2
box('M1', xb - 0.08, YS + 0.2, xb + 0.08, YS + 1.15)
box('M1', xa - 0.08, YS + 0.85, xb + 0.08, YS + 1.15)
for d in (d1, d2):     # inner diffusions (stack nodes st_k): strips lengthened to 0.16 x 0.75 for M1.d
    for i in range(1, 10):
        xs = d['x'] + 0.07 + i * (4 + 0.38)
        box('M1', xs, YS, xs + 0.16, YS + 0.75)
px, py = sd_pad(d2, YS + 0.25)
m1_tap('PS', 'xpor_cdel', px, py)
XST_END = d2['x'] + d2['lf']
box('NWell', XS0 - 1.2, YS - 1.2, XST_END + 1.2, SW_TOP)
box('TGO', XS0 - 1.2, YS - 1.5, XST_END + 1.2, SW_TOP)
ntap_strip(XS0 - 0.3, TIE_S[0], XST_END + 0.3, TIE_S[1])
m1_tap('B', 'vdda', XS0 + 3.0, (TIE_S[0] + TIE_S[1]) / 2)
m1_tap('B', 'vdda', XST_END - 3.0, (TIE_S[0] + TIE_S[1]) / 2)
DEVS.append(('XPOR.XST_0..19', 'pmosHV 0.5/4 x20 (2 x ng=10)', 0.5, 4, XS0, YS))
print('stack band end x %.2f' % XST_END)

# POR p+ guard ring (around bands 1-5)
PR_ = guard_ring_p(3.4, RES_RING_IN_Y1 - 1.0, W - 3.4, POR_RING_IN_Y2)
for yy in (YA + 5.0, YP + 6.0, YS + 1.0):
    ring_both(PR_, yy)

# =============================================================================================
# Revision 2 (D20): VREF buffer band r1_vbuf (own p+ ring). Net names = flattened CDL names (xvb_<net>).
VB = 'xvb_'
X0V = 6.0
# --- V2: NMOS bias diode / tail / sink units (sources up to a Metal1 vss bar), then the source-follower output XM7
V2_ORDER = [('XVB.XMB', 5.0, 'ibvb'), ('XVB.XMB', 5.0, 'ibvb'), ('XVB.XMT', 5.0, VB + 'ns'), ('XVB.XMB', 5.0, 'ibvb'),
            ('XVB.XMT', 5.0, VB + 'ns'), ('XVB.XMB', 5.0, 'ibvb'), ('XVB.XMB', 5.0, 'ibvb')] + [('XVB.XM8', 10.0, 'vref_b')] * 4
x = X0V
for name, w_, dn in V2_ORDER:
    x = mos_dev(name, 'n', w_, 2.0, x, Y_V2, 'vss', dn, 'ibvb', 'vss', V2_RAIL + 0.15, 'V1', 'B', gap=1.0)
XV2_SINK_END = x - 1.0
x += 1.0
# XM7 x4 10/1: drain (left strip) on vdda up into channel V1, source (right strip) vref_b and gate x1 down into channel B
for i in range(4):
    x = mos_dev('XVB.XM7', 'n', 10.0, 1.0, x, Y_V2, 'vdda', 'vref_b', VB + 'x1', 'vss', V2_RAIL + 0.15, 'V1', 'B', gap=1.0)
XV2_END = x - 1.0
box('TGO', X0V - 0.5, Y_V2 - 1.5, XV2_END + 0.5, Y_V2 + 10.8)
# Metal1 vss bar over the V2 sources (bias, tail and sink units only), tied to the left side of the band ring
VR = guard_ring_p(3.4, VB_RING_IN_Y1, W - 3.4, VB_RING_IN_Y2)
box('M1', VR[0], V2_RAIL - 0.15, XV2_SINK_END + 0.3, V2_RAIL + 0.15)
assert XV2_END < W - 5.0, XV2_END
print('V2 row: sink end x %.2f, XM7 end x %.2f' % (XV2_SINK_END, XV2_END))

# --- V1a / V1b: input pair, common centroid (A = XM1: drain d1, gate vref; B = XM2: drain x1, gate vref_b)
LPU = 24.0 + 0.68
XP0 = round((W - (4 * LPU + 3 * 1.0)) / 2, 2)
PAIR = {'A': ('XVB.XM1', VB + 'd1', 'vref'), 'B': ('XVB.XM2', VB + 'x1', 'vref_b')}
for row, yrow, cu, cd in (('ABBA', Y_V1A, 'V2c', 'V1'), ('BAAB', Y_V1B, 'V3c', 'V2c')):
    x = XP0
    for k in row:
        nm, dn, gn = PAIR[k]
        x = mos_dev(nm, 'n', 8.0, 24.0, x, yrow, VB + 'ns', dn, gn, None, None, cu, cd, gap=1.0)
XP_END = x - 1.0
# p+ substrate tie across the band in channel V2c (LU.b: N+ Activ <= 20 um from a tie; run layout-drc-20261026-r2a
# flagged the inner pair units), joined to both sides of the band ring on Activ and Metal1
YT_V2C = round((CH['V2c'].y0 + CH['V2c'].y1) / 2, 2)
box('Activ', 3.4, YT_V2C - 0.15, W - 3.4, YT_V2C + 0.15)
box('pSD', 3.43, YT_V2C - 0.21, W - 3.43, YT_V2C + 0.21)
xc = 4.0
while xc < W - 4.0:
    square('Cont', xc, YT_V2C, CONT)
    xc += 1.0
box('M1', VR[0], YT_V2C - 0.13, VR[2], YT_V2C + 0.13)
box('TGO', XP0 - 0.5, Y_V1A - 1.5, XP_END + 0.5, Y_V1B + 8.8)
box('TGO', X0V - 0.5, Y_V2 + 10.8, XV2_END + 0.5, Y_V1A - 1.5)
print('pair rows x %.2f .. %.2f' % (XP0, XP_END))

# --- V3: PMOS mirror (one n-well on vdda, sources to the tie strip)
V3_ORDER = [('XVB.XM3', 5.0, 20.0, VB + 'd1', VB + 'd1'), ('XVB.XM4', 5.0, 20.0, VB + 'x1', VB + 'd1')]
x = X0V
for name, w_, l_, dn, gn in V3_ORDER:
    x = mos_dev(name, 'p', w_, l_, x, Y_V3, 'vdda', dn, gn, 'vdda', TIE_V3[1], 'B2', 'V3c', gap=0.9)
XV3_END = x - 0.9
box('NWell', X0V - 1.2, Y_V3 - 1.2, XV3_END + 1.2, V3_TOP)
box('TGO', X0V - 1.2, Y_V3 - 1.5, XV3_END + 1.2, V3_TOP)
ntap_strip(X0V - 0.3, TIE_V3[0], XV3_END + 0.3, TIE_V3[1])
for xx in (X0V + 2.0, XV3_END - 2.0):
    m1_tap('B2', 'vdda', xx, (TIE_V3[0] + TIE_V3[1]) / 2)
print('V3 row end x %.2f' % XV3_END)
for yy in (Y_V2 + 4.0, Y_V1A + 4.0, Y_V1B + 4.0, Y_V3 + 6.0):
    ring_both(VR, yy)

# --- compensation capacitor x1 to vss: two MIM plates over the band; bottom plates (vss) joined on Metal5, one Via4
#     landing on the vss trunk; top plates (x1): one island each, joined on Metal3 between the two Metal4 landings
S_CC = 48.3
MIMV_Y = VB_RING_IN_Y1 + 0.5
xm0 = round((W - (2 * S_CC + 3.0)) / 2, 2)
CCX = [xm0, xm0 + S_CC + 3.0]
for i, x0 in enumerate(CCX):
    pcell('cmim', {'w': '%gu' % S_CC, 'l': '%gu' % S_CC, 'Calculate': 'C'}, x0, MIMV_Y)
box('M5', CCX[0] - 0.6, MIMV_Y - 0.6, CCX[1] + S_CC + 0.6, MIMV_Y)
assert CCX[0] - 0.6 < XVSS_T - 0.5, (CCX[0], XVSS_T)
for dx in (0.0, 0.42):
    square('Via4', XVSS_T - 0.21 + dx, MIMV_Y - 0.3, VIA)
mbox('M4', 'vss', XVSS_T - 0.5, MIMV_Y - 0.5, XVSS_T + 0.5, MIMV_Y - 0.1)
POINTS['vss'].append((XVSS_T, MIMV_Y - 0.3))
YI_CC = MIMV_Y + S_CC + 2.4
XI_CC = []
for i, x0 in enumerate(CCX):
    xi = x0 + S_CC / 2
    box('TM1', xi - 0.82, MIMV_Y + S_CC - 0.6, xi + 0.82, YI_CC + 0.82)
    square('TopVia1', xi, YI_CC, 0.42)
    square('M5', xi, YI_CC, 0.66)
    square('Via4', xi, YI_CC, VIA)
    mbox('M4', VB + 'x1', xi - 0.33, YI_CC - 0.33, xi + 0.33, YI_CC + 0.33)
    for dx in (-0.21, 0.21):
        square('Via3', xi + dx, YI_CC, VIA)
    XI_CC.append(xi)
    CAPS.append(dict(name='XVB.XCC%d' % (i + 1), net_top=VB + 'x1', net_bot='vss', w=S_CC, l=S_CC, top=(xi, YI_CC), bot=(XVSS_T, MIMV_Y - 0.3)))
box('M3', XI_CC[0] - 0.4, YI_CC - 0.3, XI_CC[1] + 0.4, YI_CC + 0.3)      # top plates joined on Metal3
TRUNK_SPEC[VB + 'x1'] = dict(x=XI_CC[0], w=0.6)
POINTS.setdefault(VB + 'x1', []).append((XI_CC[0], YI_CC))
FIXED_M4.append((VB + 'x1', XI_CC[1] - 0.33, YI_CC - 0.33, XI_CC[1] + 0.33, YI_CC + 0.33))
assert all(not (c.y0 - 0.5 < YI_CC < c.y1 + 0.5) for c in CH.values()), 'Cc island bar inside a channel'
print('MIM plates x %.2f, %.2f y %.2f..%.2f, islands y %.2f' % (CCX[0], CCX[1], MIMV_Y, MIMV_Y + S_CC, YI_CC))

# =============================================================================================
# Bias distribution: mirror row + two cascode rows
LEGS = [('ib_afe_s1', 2), ('ib_afe_s2', 2), ('ib_afe_c1', 2), ('ib_afe_c2', 2), ('ib_is_a', 1), ('ib_is_b', 1),
        ('ib_sf_oa', 1), ('ib_sf_na', 1), ('ib_sf_ob', 1), ('ib_sf_nb', 1), ('ib_adc_ref', 1)]
# mirror units: 2-unit AFE legs placed symmetric about the row centre (common centroid), single legs between
# revision 2: unit ibvb (r1_vbuf bias) next to the centre; the AFE pairs stay symmetric about the row centre
MORDER = ['ib_afe_s1', 'ib_is_a', 'ib_afe_c1', 'ib_sf_oa', 'ib_afe_s2', 'ib_sf_na', 'ib_afe_c2', 'ib_adc_ref', 'ibvb',
          'ib_afe_c2', 'ib_sf_ob', 'ib_afe_s2', 'ib_sf_nb', 'ib_afe_c1', 'ib_is_b', 'ib_afe_s1']
assert sorted(MORDER) == sorted(sum([[n] * m for n, m in LEGS + [('ibvb', 1)]], []))
for n, m in LEGS:
    if m == 2:
        p = [i for i, k in enumerate(MORDER) if k == n]
        assert p[0] + p[1] == len(MORDER) - 1, (n, p)


def dnet(leg):
    return 'xl_%s_d' % leg


PD_ = 5.4
MIR = ['D'] + MORDER + ['D']
XD = (W - (PD_ * (len(MIR) - 1) + WU / 3 * 0 + (LU + 0.68))) / 2
XD = round(XD, 2)
TAP_Y1, TAP_Y2 = YD + WU + 1.6, YD + WU + 2.0
N_DUM = 0
MIRX = {}
for j, name in enumerate(MIR):
    x = XD + PD_ * j
    d = mos('p', WU, LU, x, YD)
    box('M1', x + 0.07, YD + WU - 0.1, x + 0.23, TAP_Y2)
    gx, gy = gate_tab(d)
    if name == 'D':
        N_DUM += 1
        box('M1', x + d['lf'] - 0.23, YD + WU - 0.1, x + d['lf'] - 0.07, TAP_Y2)
        via1(gx, gy, 'vdda')
        m2_v(gx, gy, TAP_Y1 + 0.2, 'vdda')
        via1(gx, TAP_Y1 + 0.2, 'vdda')
        continue
    MIRX.setdefault(name, []).append(x)
    px, py = sd_pad(d, YD + 0.5)
    m1_tap('M', dnet(name), px, py)
    m1_tap('M', 'pbias', gx, gy)
XD_END = XD + PD_ * (len(MIR) - 1) + LU + 0.68
box('NWell', XD - 1.2, YD - 1.2, XD_END + 1.2, MW_TOP)
box('TGO', XD - 1.2, YD - 1.5, XD_END + 1.2, MW_TOP)
ntap_strip(XD - 0.3, TAP_Y1, XD_END + 0.3, TAP_Y2)
for j in range(len(MIR)):                       # tie strip -> vdda bus, one Metal2 strap per device
    xx = XD + PD_ * j + 1.2
    via1(xx, TAP_Y1 + 0.2, 'vdda')
    mbox('M2', 'vdda', xx - 0.25, TAP_Y1 + 0.05, xx + 0.25, VDDA_Y1 - 0.2)
    for jj in range(3):
        square('Via2', xx, VDDA_Y0 + 0.3 + 0.5 * jj, VIA)

# cascode rows (own n-well per leg, body = source = the leg's mirror drain)
CASC_A = [('D', 1), ('ib_afe_s1', 2), ('ib_afe_c1', 2), ('ib_afe_s2', 2), ('ib_afe_c2', 2), ('D', 1)]
CASC_B = [('D', 1), ('ib_is_a', 1), ('ib_sf_oa', 1), ('ib_sf_na', 1), ('ib_adc_ref', 1), ('ibvb', 1), ('ib_sf_ob', 1),
          ('ib_sf_nb', 1), ('ib_is_b', 1), ('MCR', 1), ('MCL', 1), ('D', 1)]
WELL_GAP = 2.08


def casc_row(groups, YC, ch_up, ch_down):
    global N_DUM
    widths = [(m - 1) * 5.4 + LU + 0.68 for _, m in groups]
    total = sum(widths) + 1.24 * len(groups) + WELL_GAP * (len(groups) - 1)
    x = round((W - total) / 2 + 0.62, 2)
    xs_out = {}
    for (leg, m), wd in zip(groups, widths):
        if leg in ('MCR', 'MCL'):
            w_, snet, dnet_, out = 10.0, ('xpor_dr' if leg == 'MCR' else 'xpor_dl'), None, ('xpor_vrh' if leg == 'MCR' else 'xpor_nl')
        else:
            w_ = WU
            snet = 'vdda' if leg == 'D' else dnet(leg)
            out = leg
        for u in range(m):
            xu = x + 5.4 * u
            d = mos('p', w_, LU, xu, YC)
            box('M1', xu + 0.07, YC + w_ - 0.1, xu + 0.23, YC + w_ + 1.6)
            box('M1', xu + 0.07, YC + w_ + 1.2, xu + 0.3, YC + w_ + 1.6)
            gx, gy = gate_tab(d)
            if leg == 'D':
                N_DUM += 1
                box('M1', xu + d['lf'] - 0.23, YC + w_ - 0.1, xu + d['lf'] - 0.07, YC + w_ + 1.6)
                box('M1', xu + 4.4, YC + w_ + 1.2, xu + d['lf'] - 0.07, YC + w_ + 1.6)
                via1(gx, gy, 'vdda')
                m2_v(gx, gy, YC + w_ + 1.4, 'vdda')
                via1(gx, YC + w_ + 1.4, 'vdda')
                m1_tap(ch_up, 'vdda', xu + 1.2, YC + w_ + 1.4)
                continue
            m1_tap(ch_up, snet, xu + 1.2, YC + w_ + 1.4)
            px, py = sd_pad(d, YC + 0.5)
            m1_tap(ch_down, out, px, py)
            m1_tap(ch_down, 'pcasc', gx, gy)
            xs_out.setdefault(out, []).append(px)
        xe = x + wd
        box('NWell', x - 0.62, YC - 0.62, xe + 0.62, YC + w_ + 2.4)
        box('TGO', x - 0.62, YC - 1.5, xe + 0.62, YC + w_ + 2.4)
        ntap_strip(x + 0.3, YC + w_ + 1.2, xe - 0.28, YC + w_ + 1.6)
        x = xe + 1.24 + WELL_GAP
    return xs_out


casc_row(CASC_A, YCA, 'M', 'A')
casc_row(CASC_B, YCB, 'A', 'B2')
BR = guard_ring_p(3.4, BIAS_RING_IN_Y1, W - 3.4, BIAS_RING_IN_Y2)
for yy in (YCB + 6.0, YCA + 6.0, YD + 6.0):
    ring_both(BR, yy)

# =============================================================================================
# pins
PINS_WE = {'pbias': ('M', 'W'), 'pcasc': ('A', 'W'), 'por_n': ('R1', 'E'), 'vdd': ('H', 'E'), 'vref': ('V1', 'W'), 'vref_b': ('V3c', 'E')}
for net, (ch, side) in PINS_WE.items():
    CH[ch].extra.setdefault(net, []).append(0.0 if side == 'W' else W)
PIN_N = [n for n, _ in LEGS]
# vdda: Metal4 trunk at a fixed x from the vdda bus down to the POR channels
XVDDA_T = W - 7.0
TRUNK_SPEC['vdda'] = dict(x=XVDDA_T, w=1.0)
POINTS.setdefault('vdda', []).append((XVDDA_T, VDDA_MID))
for i in range(2):
    for j in range(3):
        square('Via3', XVDDA_T - 0.21 + 0.42 * i, VDDA_MID - 0.42 + 0.42 * j, VIA)

# =============================================================================================
# trunks: every net present in more than one place gets one Metal4 trunk
YR = {name: ((c.y0 + c.y1) / 2) for name, c in CH.items()}
places = {}
for name, c in CH.items():
    for n in c.nets():
        places.setdefault(n, []).append(('ch', name))
for n, pts in POINTS.items():
    for p in pts:
        places.setdefault(n, []).append(('pt', p[1]))
for n in PIN_N:
    places.setdefault(n, []).append(('pin', PIN_Y))


def chan_bounds(p):
    if p[0] == 'ch':
        return CH[p[1]].y0, CH[p[1]].y1
    return p[1] - 0.4, p[1] + 0.4


TRUNKS = {}


def m4_free(x, w, y0, y1):
    for n, t in TRUNKS.items():
        if t['y1'] < y0 - 0.5 or t['y0'] > y1 + 0.5:
            continue
        if abs(t['x'] - x) < (t['w'] + w) / 2 + 0.3:
            return False
    for n, x1, yy1, x2, yy2 in FIXED_M4:
        if yy2 < y0 - 0.5 or yy1 > y1 + 0.5:
            continue
        if x + w / 2 + 0.3 > x1 and x - w / 2 - 0.3 < x2:
            return False
    return True


PREF = {}
order = sorted(places, key=lambda n: (n not in TRUNK_SPEC, n not in PIN_N, n))
for net in order:
    ps = places[net]
    if len(ps) < 2:
        continue
    lo = min(chan_bounds(p)[0] for p in ps)
    hi = max(chan_bounds(p)[1] for p in ps)
    if net in TRUNK_SPEC:
        x, w = TRUNK_SPEC[net]['x'], TRUNK_SPEC[net]['w']
        if not m4_free(x, w, lo, hi):
            raise SystemExit('fixed trunk %s collides' % net)
    else:
        w = 0.6
        xs = []
        for name, c in CH.items():
            xs += [t[1] for t in c.taps if t[0] == net]
        pref = round(PREF.get(net, sum(xs) / len(xs)), 2)
        x = None
        for k in range(0, 3000):
            for cand in (pref + 0.05 * k, pref - 0.05 * k):
                if 5.0 <= cand <= W - 5.0 and m4_free(cand, w, lo, hi):
                    x = cand
                    break
            if x is not None:
                break
        if x is None:
            raise SystemExit('no trunk position for %s' % net)
    x = round(x, 2)
    TRUNKS[net] = dict(x=x, w=w, y0=lo, y1=hi)
    for p in ps:
        if p[0] == 'ch':
            CH[p[1]].extra.setdefault(net, []).append(x)

# =============================================================================================
# channel track assignment: nets tapped only from below take the lowest tracks, nets tapped only from above the
# highest, mixed nets the middle (so that Metal2 stubs from opposite sides of the channel cannot cross)
REPORT = {}
OVER = []
for name, c in CH.items():
    nets = c.nets()
    side = {}
    for n, x, yf in c.taps:
        side.setdefault(n, set()).add('b' if yf < c.y0 else 'a')
    cls = {n: (0 if side.get(n) == {'b'} else 2 if side.get(n) == {'a'} else 1) for n in nets}
    tracks_all = []
    # mixed nets: one track each, ordered so that a net whose stub rises from below near (< 0.7 um) a stub that
    # comes down from above of another net lies below that net (topological order of these constraints)
    mixed = sorted(n for n in nets if cls[n] == 1)
    below = {n: [x for nn, x, yf in c.taps if nn == n and yf < c.y0] for n in mixed}
    above = {n: [x for nn, x, yf in c.taps if nn == n and yf >= c.y0] for n in mixed}
    succ = {n: set() for n in mixed}
    for a in mixed:
        for b in mixed:
            if a != b and any(abs(xa - xb) < 0.7 for xa in below[a] for xb in above[b]):
                succ[a].add(b)
    morder, temp = [], set(mixed)
    while temp:
        free = sorted(n for n in temp if not any(n in succ[m] for m in temp if m != n))
        if not free:
            raise SystemExit('mixed-track cycle in channel %s: %s' % (name, sorted(temp)))
        morder.append(free[0])
        temp.discard(free[0])
    for cl in (0, 1, 2):
        if cl == 1:
            for k, n in enumerate(morder):
                c.track[n] = (1, k)
            tracks_all.append(len(morder))
            continue
        iv = sorted(((min(xs) - 0.25, max(xs) + 0.25, n) for n, xs in nets.items() if cls[n] == cl), key=lambda t: t[0])
        tracks = []
        for x0, x1, n in iv:
            for k, end in enumerate(tracks):
                if x0 > end + 0.3:
                    tracks[k] = x1
                    c.track[n] = (cl, k)
                    break
            else:
                tracks.append(x1)
                c.track[n] = (cl, len(tracks) - 1)
        tracks_all.append(len(tracks))
    base = [0, tracks_all[0], tracks_all[0] + tracks_all[1]]
    ntr = sum(tracks_all)
    cap = int((c.y1 - c.y0 - 0.3) // TP) + 1
    REPORT[name] = dict(tracks=ntr, by_class=tracks_all, capacity=cap)
    if ntr > cap:
        OVER.append((name, ntr, cap))
    for n, (cl, k) in c.track.items():
        c.track[n] = c.y0 + 0.3 + (base[cl] + k) * TP
for name, c in CH.items():
    print('channel', name, REPORT[name])
if OVER:
    raise SystemExit('CHANNEL OVERFLOW %s' % OVER)

for name, c in CH.items():
    nets = c.nets()
    for n, xs in nets.items():
        yt = c.track[n]
        x0, x1 = min(xs), max(xs)
        if x1 - x0 < 0.5:
            x0, x1 = (x0 + x1) / 2 - 0.25, (x0 + x1) / 2 + 0.25
        box('M3', max(x0 - 0.15, 0.0), yt - 0.15, min(x1 + 0.15, W), yt + 0.15)
    last = {}
    for n, x, yf in sorted(c.taps, key=lambda t: t[1]):
        yt = c.track[n]
        m2_v(x, yf, yt, n)
        if n in last and x - last[n][0] < 0.75 and (last[n][1] < c.y0) == (yf < c.y0):
            xp, yfp = last[n]
            ya, yb = (max(min(yf, yt), min(yfp, yt)), min(max(yf, yt), max(yfp, yt)))
            mbox('M2', n, xp - 0.15, min(ya, yb) - 0.15, x + 0.15, max(ya, yb) + 0.15)
            continue
        via2(x, yt, n)
        last[n] = (x, yf)

# trunks
for net, t in TRUNKS.items():
    ys = []
    for p in places[net]:
        ys.append(CH[p[1]].track[net] if p[0] == 'ch' else p[1])
    y0, y1 = min(ys), max(ys)
    x, w = t['x'], t['w']
    mbox('M4', net, x - w / 2, y0 - 0.7, x + w / 2, y1 + (0.7 if net not in PIN_N else 0.45))
    nx = max(1, int((w - 0.3) // VP) + 1)
    for p in places[net]:
        if p[0] == 'ch':
            via3(x, CH[p[1]].track[net], net, nx=nx)
        elif p[0] == 'pin':
            via3(x, PIN_Y, net, nx=1, ny=2)
            box('M3', x - 0.3, H - 1.25, x + 0.3, H)
            box('M3pin', x - 0.3, H - 1.25, x + 0.3, H)
            label('M3txt', x, H - 0.6, net)
    t['y0'], t['y1'] = y0, y1
for n in PIN_N:
    if n not in TRUNKS:
        raise SystemExit('output %s has no trunk' % n)

# west / east pins on the channel tracks
for net, (ch, side) in PINS_WE.items():
    yt = CH[ch].track[net]
    x1, x2 = (0.0, 1.5) if side == 'W' else (W - 1.5, W)
    box('M3pin', x1, yt - 0.15, x2, yt + 0.15)
    label('M3txt', (x1 + x2) / 2, yt, net)
box('prBoundary', 0, 0, W, H)

# =============================================================================================
# self-check: Metal2 and Metal4 shapes of different nets keep the spacing (0.21 um; 0.24 with a wide shape)


def conflicts(segs):
    bad = []
    segs = sorted(segs, key=lambda s: s[1])
    for i, (na, ax1, ay1, ax2, ay2) in enumerate(segs):
        for nb, bx1, by1, bx2, by2 in segs[i + 1:]:
            if bx1 > ax2 + 0.3:
                break
            if na == nb:
                continue
            need = 0.24 if (min(ax2 - ax1, ay2 - ay1) > 0.39 or min(bx2 - bx1, by2 - by1) > 0.39) else 0.21
            dx = max(bx1 - ax2, ax1 - bx2)
            dy = max(by1 - ay2, ay1 - by2)
            if dx < need - 1e-6 and dy < need - 1e-6:
                bad.append((na, nb, round(dx, 3), round(dy, 3), (ax1, ay1, ax2, ay2), (bx1, by1, bx2, by2)))
    return bad


nbad = 0
for layer in ('M2', 'M4'):
    for c in conflicts(SEGS[layer]):
        print(layer, 'CONFLICT', c)
        nbad += 1
if nbad:
    raise SystemExit('%d spacing conflicts, GDS not written' % nbad)

out = os.path.join(HERE, 'r1_bias.gds')
ly.write(out)
print('wrote', out, 'W %.2f H %.2f area_mm2 %.5f' % (W, H, W * H * 1e-6))

# =============================================================================================
# LVS reference: the netlist of record flattened to CDL (internal nets prefixed by the instance path, lower case),
# plus the layout dummies


def read_subckts(path):
    subs, cur = {}, None
    for line in open(path):
        s = line.strip()
        if not s or s.startswith('*'):
            continue
        f = s.split()
        if f[0].lower() == '.subckt':
            cur = dict(pins=[p for p in f[2:] if '=' not in p], params={p.split('=')[0]: p.split('=')[1] for p in f[2:] if '=' in p}, lines=[])
            subs[f[1]] = cur
        elif f[0].lower() == '.ends':
            cur = None
        elif cur is not None:
            cur['lines'].append(f)
    return subs


SUBS = read_subckts(SCH)
PRIM = {'sg13_hv_pmos', 'sg13_hv_nmos', 'sg13_lv_pmos', 'sg13_lv_nmos', 'rppd', 'rhigh', 'npn13G2', 'cap_cmim'}
CDL = []


HIER = {}         # flat CDL net name -> hierarchical name of the netlist of record (xpor_xca_tail -> xpor.xca.tail)


def flatten(sub, path, nmap, params, hpath=''):
    S = SUBS[sub]

    def net(n):
        if n in nmap:
            return nmap[n]
        if n == 'sub!':
            return 'vss'
        if not path:
            return n
        flat = ('%s_%s' % (path, n)).lower()
        HIER[flat] = ('%s.%s' % (hpath, n)).lower()
        return flat

    for f in S['lines']:
        name = f[0]
        tokens = [t for t in f[1:] if '=' not in t]
        kv = {t.split('=')[0]: t.split('=')[1] for t in f[1:] if '=' in t}
        model = tokens[-1]
        nodes = tokens[:-1]
        inst = ('%s_%s' % (path, name)).lower() if path else name.lower()
        if model in PRIM:
            m = kv.get('m', '1')
            if m.startswith('{'):
                m = params[m.strip('{}')]
            m = int(float(m))
            for k in range(m):
                nm = inst + ('_u%d' % k if m > 1 else '')
                nn = [net(x) for x in nodes]
                if model.startswith('sg13_'):
                    CDL.append('M%s %s %s %s %s %s w=%s l=%s ng=1 m=1' % (nm, nn[0], nn[1], nn[2], nn[3], model, kv['w'], kv['l']))
                elif model in ('rppd', 'rhigh'):
                    CDL.append('R%s %s %s %s %s w=%s l=%s m=1 b=0' % (nm, nn[0], nn[1], nn[2], model, kv['w'], kv['l']))
                elif model == 'npn13G2':
                    CDL.append('Q%s %s %s %s %s npn13G2 le=900n we=70n Nx=%s' % (nm, nn[0], nn[1], nn[2], nn[3], kv['Nx']))
                elif model == 'cap_cmim':
                    CDL.append('C%s %s %s cap_cmim w=%s l=%s m=1' % (nm, nn[0], nn[1], kv['w'], kv['l']))
        else:
            sp = SUBS[model]
            sub_params = dict(sp['params'])
            sub_params.update({k: v for k, v in kv.items()})
            child_map = {pin: net(n) for pin, n in zip(sp['pins'], nodes)}
            flatten(model, inst, child_map, sub_params, ('%s.%s' % (hpath, name) if hpath else name).lower())


TOP_PINS = SUBS['r1_bias']['pins']
flatten('r1_bias', '', {p: p for p in TOP_PINS}, {})
NDEV_SCH = len(CDL)
hdr = ['* r1_bias LVS reference netlist, written by layout/r1_bias_layout.py from schematic/r1_bias.spice (netlist of',
       '* record, revision 2), flattened: internal nets carry the instance path (xpor_..., xvb_..., xl_<leg>_d), m>1 written as',
       '* separate units, sub! -> vss. The %d layout dummies (sg13_hv_pmos 12/4, every terminal on vdda) are not listed:' % N_DUM,
       '* the PDK LVS deck drops devices whose terminals are all on one net (run layout-lvs-20261021-b).',
       '.subckt r1_bias ' + ' '.join(TOP_PINS)]
with open(os.path.join(HERE, 'r1_bias_lvs.cdl'), 'w') as fh:
    fh.write('\n'.join(hdr + CDL + ['.ends']) + '\n')
meta = dict(W=W, H=H, area_mm2=round(W * H * 1e-6, 6), n_dummy_pmos=N_DUM, n_devices_schematic_units=NDEV_SCH,
            bands=dict(YA=YA, YH=YH, YN=YN, YP=YP, YS=YS, YV2=Y_V2, YV1A=Y_V1A, YV1B=Y_V1B, YV3=Y_V3, YCB=YCB, YCA=YCA, YD=YD),
            trunks={n: dict(x=t['x'], w=t['w'], y0=round(t['y0'], 3), y1=round(t['y1'], 3)) for n, t in TRUNKS.items()},
            channels=REPORT, caps=CAPS, mirror_units=MIRX, hier=HIER,
            pins=dict(north=PIN_N, west=['pbias', 'pcasc', 'vref', 'vdda', 'vss'], east=['por_n', 'vdd', 'vref_b', 'vdda', 'vss']))
with open(os.path.join(HERE, 'r1_bias_layout_meta.json'), 'w') as fh:
    json.dump(meta, fh, indent=1)
print('wrote r1_bias_lvs.cdl (%d schematic units; %d layout dummies not listed) and r1_bias_layout_meta.json' % (NDEV_SCH, N_DUM))
