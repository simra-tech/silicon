#!/usr/bin/env python3
"""r1_bgr layout generator (KLayout batch Python, PDK PCells from library SG13_dev).

Run inside the pinned container (KLayout 0.30.9, PDK commit 8437402), from the repository root:
  G1_CPUSET=100-102 G1_WORKDIR=designs/r1-joint/blocks/r1_bgr/layout flow/run.sh klayout -b -r r1_bgr_layout.py
Writes, next to this script:
  r1_bgr.gds        top cell r1_bgr, prBoundary 189/4 = (0, 0) - (W, H)
  r1_bgr_lvs.cdl    LVS reference: schematic/r1_bgr.spice (netlist of record) in CDL form plus the layout dummies
Every device is a PDK PCell (SG13_dev: pmosHV, nmosHV, rppd, rhigh, npn13G2); everything else is drawn here.
Descends from designs/g1-guardian/blocks/g1_bgr/layout/g1_bgr_layout.py (same cell conventions, helpers, ring style).

Floorplan, bottom to top (y in um):
  vss bus (Metal3, pin)                      0 .. 2
  R channel (Metal3, 2 tracks, R1/R2 links)  3.3 .. 4.2
  resistor row, p+ ring                      rppd: D RBx12 D | R2 R2 R1 R2 R2 R2 R2 R1 R2 R2 | D RXx4 D ;
                                             rhigh: D RDETx15 D. R1/R2 units all carry current upwards.
  channel BA
  HBT bank, outer p+ ring                    8 rows x 13 columns of npn13G2 (Nx=1, one orientation), dummy row and
                                             column on each side; 6 x 11 active = 12 Q1 + 48 Q2 + 4 Q3 + QD1 + QD2,
                                             Q1 and Q3 point-symmetric about the bank centre (common centroid)
  channel CB
  NMOS row, p+ ring                          D A A A A A A A A B B A A A A A A A A D | MNI MKFB (A = MNC1 finger,
                                             B = MNC2 finger, w = 10 um each)
  channel NC
  cascode row 1 (own n-wells)                MC1_0 .. MC1_5, dummy
  channel C12
  cascode row 2 (own n-wells)                MC1_6 MC1_7 MC2 MC3 MC4 MC5, dummy
  channel DC
  mirror row (one n-well on vdd)             MPI | D MP5 MP1_0..3 MP2 MP3 MP1_4..7 MP4 MPS D
  vdd bus (Metal3, pin)
Routing layers: Metal1 inside devices, Metal2 short vertical stubs, Metal3 horizontal tracks, Metal4 vertical trunks.
No Metal5, no TopMetal. Signal pins: Metal3 stubs on the west and east edges.

Precision returns (the G1 BGR586 lesson: metal resistance in the delta-V_BE path):
  - Q1, Q3 and QD2 emitters return on their own Metal3 tracks (`vssq`) and one 2 um Metal4 trunk to the top head of
    R1 (the star). The star goes to the vss pin bus on the same trunk. The p+ guard rings and the dummies reach the
    vss bus by separate paths, so no guard current flows in the Q1 emitter return.
  - Q2 emitters (`dvbe`) go on 0.55 um Metal3 row tracks and one 1 um Metal4 trunk to the bottom head of R1.
  - Q1 is fed by its collector from MNC1 (`vbe` force tracks); the Q2 bases sense `vbe` on separate tracks that meet
    the Q1 bases only inside the Q1 cells.
"""
import json
import os
import sys

K = '/foss/pdks/ihp-sg13g2/libs.tech/klayout/python'
for p in [K, K + '/pycell4klayout-api/source/python']:
    sys.path.insert(0, p)
import pya  # noqa: E402
import sg13g2_pycell_lib  # noqa: E402,F401  (registers library SG13_dev)

HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(HERE, '..', 'schematic', 'r1_bgr.spice')
lib = pya.Library.library_by_name('SG13_dev', 'sg13g2')
ly = pya.Layout()
ly.dbu = 0.001
LAYERS = {'Activ': (1, 0), 'GatPoly': (5, 0), 'Cont': (6, 0), 'pSD': (14, 0), 'NWell': (31, 0), 'TGO': (44, 0),
          'M1': (8, 0), 'M1pin': (8, 2), 'M1txt': (8, 25), 'Via1': (19, 0),
          'M2': (10, 0), 'M2pin': (10, 2), 'M2txt': (10, 25), 'Via2': (29, 0),
          'M3': (30, 0), 'M3pin': (30, 2), 'M3txt': (30, 25), 'Via3': (49, 0),
          'M4': (50, 0), 'M4txt': (50, 25), 'prBoundary': (189, 4)}
L = {n: ly.layer(*v) for n, v in LAYERS.items()}
top = ly.create_cell('r1_bgr')

CONT, CP = 0.16, 0.34      # contact size / pitch
VIA, VP = 0.19, 0.42       # via size / pitch
W3 = 0.3                   # signal wire width
TP = 0.6                   # channel track pitch
W = 96.0                   # macro width


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


# ---------------------------------------------------------------------------------------------
# shape registry for the self-checks (Metal2 and Metal4 spacing between different nets)
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


def via1(x, y, net, nx=1, ny=1, pad2=0.0):
    """Via1 cuts; Metal1 and Metal2 pads 0.055 around the cuts (Metal2 pad grown by pad2 for min area)"""
    b = cuts('Via1', x, y, nx, ny)
    box('M1', *b)
    mbox('M2', net, b[0] - pad2, b[1] - pad2, b[2] + pad2, b[3] + pad2)


def via2(x, y, net, nx=1, ny=1, pad=0.0):
    b = cuts('Via2', x, y, nx, ny)
    mbox('M2', net, b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad)
    box('M3', b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad)


def via3(x, y, net, nx=1, ny=1, pad=0.0):
    b = cuts('Via3', x, y, nx, ny)
    box('M3', b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad)
    mbox('M4', net, b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad)


def stack(x, y, net, upto=3, nx=1, ny=1):
    """Via1 (+Via2 (+Via3)) stacked at (x, y) on existing Metal1; intermediate pads 0.4 um minimum (min area)"""
    b = cuts('Via1', x, y, nx, ny)
    box('M1', *b)
    g = lambda bb: (min(bb[0], x - 0.2), min(bb[1], y - 0.2), max(bb[2], x + 0.2), max(bb[3], y + 0.2))
    bb = g(b)
    mbox('M2', net, *bb)
    if upto >= 2:
        cuts('Via2', x, y, nx, ny)
        box('M3', *bb)
    if upto >= 3:
        cuts('Via3', x, y, nx, ny)
        mbox('M4', net, *bb)


def m2_v(x, y1, y2, net, w=W3):
    mbox('M2', net, x - w / 2, min(y1, y2) - w / 2, x + w / 2, max(y1, y2) + w / 2)


def m2_h(y, x1, x2, net, w=W3):
    mbox('M2', net, min(x1, x2) - w / 2, y - w / 2, max(x1, x2) + w / 2, y + w / 2)


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
# Router: channels with Metal3 tracks assigned by the left-edge rule, Metal2 stubs from device taps, Metal4 trunks
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


def channel(name, y0, y1):
    CH[name] = Channel(name, y0, y1)
    return CH[name]


FIXED = {}      # net -> list of [y, xs(list), width, ny_via3] Metal3 tracks drawn by the caller-side code (bank rows)
POINTS = {}     # net -> list of (x, y): fixed Metal4 landing points (resistor head stacks, buses)
TRUNK_SPEC = {}  # net -> dict(x=..., w=...)  fixed trunk position/width; others are allocated
PINS = {}        # net -> (channel, side)


def fixed_track(net, y, xs, w=W3, ny3=1):
    FIXED.setdefault(net, []).append([y, list(xs), w, ny3])


def m1_tap(ch, net, x, y, n1=1):
    """Via1 on existing Metal1 at (x, y); Metal2 stub to the channel track is drawn by the router"""
    via1(x, y, net, ny=n1)
    CH[ch].tap(net, x, y)


# =============================================================================================
# Vertical plan
VSS_Y0, VSS_Y1 = 0.0, 2.0
YA = 5.0                     # resistor bottom (body start)
RING_R = (5.8, 3.6, 90.0, 55.6)
BA = (56.25, 60.0)
YB0 = 64.33                  # HBT bank row 0 (dummy) centre
PBY = 6.71
PBX = 6.3
XB0 = 10.2
CB = (116.1, 120.85)
YN = 122.85                  # NMOS row devices bottom
NC = (134.45, 138.3)
YC1 = 140.0
C12 = (152.75, 157.3)
YC2 = 159.0
DC = (171.75, 177.2)
YD = 178.6
VDD_Y0 = YD + 13.7
VDD_Y1 = VDD_Y0 + 2.0
H = VDD_Y1

channel('BA', *BA)
channel('CB', *CB)
channel('NC', *NC)
channel('C12', *C12)
channel('DC', *DC)

# ---------------------------------------------------------------------------------------------
# power buses
box('M3', 0, VSS_Y0, W, VSS_Y1)
box('M3pin', 0, VSS_Y0, W, VSS_Y1)
label('M3txt', W / 2, (VSS_Y0 + VSS_Y1) / 2, 'vss')
box('M3', 0, VDD_Y0, W, VDD_Y1)
box('M3pin', 0, VDD_Y0, W, VDD_Y1)
label('M3txt', W / 2, (VDD_Y0 + VDD_Y1) / 2, 'vdd')
VDD_MID = (VDD_Y0 + VDD_Y1) / 2
VSS_MID = (VSS_Y0 + VSS_Y1) / 2

# vss side columns (Metal2 1.0 um), from the vss bus up to the NMOS ring
VCOL_L, VCOL_R = 1.0, W - 1.0
for x in (VCOL_L, VCOL_R):
    mbox('M2', 'vss', x - 0.5, 0.3, x + 0.5, YN + 6.0)
    for yy in (0.6, 1.4):
        for dx in (-0.21, 0.21):
            square('Via2', x + dx, yy, VIA)


def ring_to_vss_col(xl, xr, y, col_x):
    """p+ ring Metal1 side -> Via1+Via2 -> Metal3 jumper -> Via2 on the side column"""
    xs = xl if col_x < xl else xr
    box('M1', xs - 0.45, y - 0.25, xs + 0.45, y + 0.25)
    b = cuts('Via1', xs, y, 2, 1)
    mbox('M2', 'vss', b[0], b[1], b[2], b[3])
    cuts('Via2', xs, y, 2, 1)
    box('M3', min(xs, col_x) - 0.4, y - 0.15, max(xs, col_x) + 0.4, y + 0.15)
    cuts('Via2', col_x, y, 2, 1)


# =============================================================================================
# Block A: resistor row
XA, PA = 7.0, 1.9
MATCH = ['R2', 'R2', 'R1', 'R2', 'R2', 'R2', 'R2', 'R1', 'R2', 'R2']
RCOLS = ['D'] + ['RB'] * 12 + ['D'] + MATCH + ['D'] + ['RX'] * 4 + ['D']
assert len(RCOLS) == 30
RLEN = []
nrb = nr2 = 0
for kind in RCOLS:
    if kind == 'RB':
        nrb += 1
        RLEN.append(41.685 if nrb == 12 else 41.665)
    elif kind == 'R2':
        nr2 += 1
        RLEN.append(43.455 if nr2 == 8 else 43.435)
    elif kind == 'R1':
        RLEN.append(42.0)
    elif kind == 'RX':
        RLEN.append(48.0)
    else:
        RLEN.append(None)
DLEN = {0: 41.7, 13: 43.4, 24: 43.4, 29: 48.0}
for i, d in DLEN.items():
    RLEN[i] = d
assert abs(sum(RLEN[i] for i, k in enumerate(RCOLS) if k == 'RB') - 500.0) < 1e-6
assert abs(sum(RLEN[i] for i, k in enumerate(RCOLS) if k == 'R2') - 347.5) < 1e-6
assert abs(sum(RLEN[i] for i, k in enumerate(RCOLS) if k == 'R1') - 84.0) < 1e-6
assert abs(sum(RLEN[i] for i, k in enumerate(RCOLS) if k == 'RX') - 192.0) < 1e-6


def rx(i):
    return XA + PA * i


for i, kind in enumerate(RCOLS):
    x = rx(i)
    if kind == 'D':   # dummy: silicided GatPoly strip of the same width, no resistor markers (as G1)
        box('GatPoly', x, YA - 0.43, x + 1.0, YA + RLEN[i] + 0.43)
        box('pSD', x - 0.18, YA - 0.61, x + 1.18, YA + RLEN[i] + 0.61)
    else:
        pcell('rppd', {'w': '1u', 'l': '%gu' % RLEN[i], 'b': 0, 'Calculate': 'R'}, x, YA)


def head(i, end):
    x = rx(i)
    ln = RLEN[i]
    return (x + 0.02, YA + ln + 0.13, x + 0.98, YA + ln + 0.43) if end == 't' else (x + 0.02, YA - 0.43, x + 0.98, YA - 0.13)


def hc(i, end):
    h = head(i, end)
    return (h[0] + h[2]) / 2, (h[1] + h[3]) / 2


def strap(i, end):
    a, b = head(i, end), head(i + 1, end)
    box('M1', a[0], min(a[1], b[1]), b[2], max(a[3], b[3]))


def chain(cols, free):
    other = 'b' if free == 't' else 't'
    for k in range(len(cols) - 1):
        strap(cols[k], other if k % 2 == 0 else free)
    last = free if (len(cols) - 2) % 2 == 0 else other
    return (cols[0], free), (cols[-1], last)


rb = chain(list(range(1, 13)), 't')
rxc = chain([25, 26, 27, 28], 't')
assert rb == ((1, 't'), (12, 't')) and rxc == ((25, 't'), (28, 't'))
for (c, e), net in ((rb[0], 'pbias'), (rb[1], 'pcasc'), (rxc[0], 'vb2'), (rxc[1], 'vd1')):
    x, y = hc(c, e)
    m1_tap('BA', net, x, y)

# matched R1/R2 array: every unit carries current from its bottom head to its top head.
# R2: vref -> 14 -> 15 -> 17 -> 18 -> 19 -> 20 -> 22 -> 23 -> vbe3 ; R1: dvbe -> 16 -> 21 -> vss (star)
R2_ORDER = [14, 15, 17, 18, 19, 20, 22, 23]
R1_ORDER = [16, 21]
assert all(RCOLS[i] == 'R2' for i in R2_ORDER) and all(RCOLS[i] == 'R1' for i in R1_ORDER)
RCH_Y = {'hi': 4.05, 'lo': 3.45}       # Metal3 tracks of the R channel below the row (inside the ring's footprint)
LINK_TRACK = {(15, 17): 'hi', (20, 22): 'hi', (16, 21): 'lo'}
for order, tag in ((R2_ORDER, 'r2'), (R1_ORDER, 'r1')):
    for k in range(len(order) - 1):
        a, b = order[k], order[k + 1]
        net = '%s_l%d' % (tag, k)
        xa, yta = hc(a, 't')
        xg = rx(a) + 1.45                       # gap right of column a
        xb, ybb = hc(b, 'b')
        via1(xa, yta, net)
        m2_h(yta, xa, xg, net)
        if b == a + 1:                          # adjacent: all Metal2
            m2_v(xg, yta, ybb, net)
            m2_h(ybb, xg, xb, net)
            via1(xb, ybb, net)
        else:                                   # skip link: down to the R channel, Metal3 across, up to head b
            ty = RCH_Y[LINK_TRACK[(a, b)]]
            m2_v(xg, yta, ty, net)
            via2(xg, ty, net)
            via1(xb, ybb, net)
            m2_v(xb, ybb, ty, net)
            via2(xb, ty, net)
            box('M3', xg - 0.15, ty - 0.15, xb + 0.15, ty + 0.15)
# terminals: via stacks to the Metal4 trunks
XS = {}
XS['vref'] = hc(14, 'b')[0]
XS['dvbe'] = hc(16, 'b')[0]
XS['vssq'] = hc(21, 't')[0]
XS['vbe3'] = hc(23, 't')[0]
for net, c, e, n in (('vref', 14, 'b', 2), ('dvbe', 16, 'b', 2), ('vssq', 21, 't', 2), ('vbe3', 23, 't', 2)):
    x, y = hc(c, e)
    stack(x, y, net, 3, nx=n)
    POINTS.setdefault(net, []).append((x, y))
TRUNK_SPEC['vref'] = dict(x=XS['vref'], w=1.0)
TRUNK_SPEC['dvbe'] = dict(x=XS['dvbe'], w=1.0)
TRUNK_SPEC['vssq'] = dict(x=XS['vssq'], w=2.0)
TRUNK_SPEC['vbe3'] = dict(x=XS['vbe3'], w=0.6)
# the star (R1 top head) goes to the vss bus on the vssq trunk: Via3 array on the bus
POINTS['vssq'].append((XS['vssq'], VSS_MID))
for i in range(4):
    for j in range(3):
        square('Via3', XS['vssq'] - 0.63 + 0.42 * i, VSS_MID - 0.42 + 0.42 * j, VIA)

# rhigh RDET: 15 segments of 49 um + 2 dummies
XH, PH, RH_L = 65.8, 1.4, 49.0
for j in range(17):
    x = XH + PH * j
    if j in (0, 16):
        box('GatPoly', x, YA - 0.43, x + 0.5, YA + RH_L + 0.43)
        box('pSD', x - 0.18, YA - 0.61, x + 0.68, YA + RH_L + 0.61)
    else:
        pcell('rhigh', {'w': '0.5u', 'l': '%gu' % RH_L, 'b': 0, 'Calculate': 'R'}, x, YA)


def rh_head(j, end):
    x = XH + PH * j
    return (x + 0.02, YA + RH_L + 0.15, x + 0.48, YA + RH_L + 0.41) if end == 't' else (x + 0.02, YA - 0.41, x + 0.48, YA - 0.15)


for k in range(1, 15):
    end = 'b' if k % 2 == 1 else 't'
    a, b = rh_head(k, end), rh_head(k + 1, end)
    box('M1', a[0], a[1], b[2], b[3])
x = XH + PH * 1 + 0.25
box('M1', x - 0.25, YA + RH_L + 0.10, x + 0.25, YA + RH_L + 0.50)
m1_tap('BA', 'det', x, YA + RH_L + 0.30)
x = XH + PH * 15 + 0.25
box('M1', x - 0.25, YA - 0.50, x + 0.25, YA - 0.10)
via1(x, YA - 0.30, 'vss')
m2_v(x, YA - 0.30, VSS_MID, 'vss')
via2(x, VSS_MID, 'vss', 2, 1)

# resistor guard ring and its vss connections (bus straps away from the R channel and the vssq trunk)
RA = guard_ring_p(*RING_R)
for xx in (10.0, 24.0, 60.0, 80.0):
    box('M1', xx - 0.45, RA[1] - 0.25, xx + 0.45, RA[1] + 0.25)
    via1(xx, RA[1], 'vss', 2, 1)
    m2_v(xx, RA[1], VSS_MID, 'vss')
    via2(xx, VSS_MID, 'vss', 2, 1)
ring_to_vss_col(RA[0], RA[2], 30.0, VCOL_L)
ring_to_vss_col(RA[0], RA[2], 30.0, VCOL_R)

# =============================================================================================
# Block B: HBT bank
NROW, NCOL = 8, 13


def bx(i):
    return XB0 + PBX * i


def by(j):
    return YB0 + PBY * j


PAT = [['Q2'] * 11 for _ in range(6)]
for a, c in ((1, 1), (1, 3), (1, 5), (1, 7), (1, 9), (4, 1), (4, 3), (4, 5), (4, 7), (4, 9), (2, 5), (3, 5)):
    PAT[a][c] = 'Q1'
for a, c in ((2, 2), (3, 8), (2, 8), (3, 2)):
    PAT[a][c] = 'Q3'
PAT[0][0] = 'QD1'
PAT[5][10] = 'QD2'
cnt = {}
for row in PAT:
    for k in row:
        cnt[k] = cnt.get(k, 0) + 1
assert cnt == {'Q1': 12, 'Q2': 48, 'Q3': 4, 'QD1': 1, 'QD2': 1}, cnt
# common-centroid check (point symmetry about the bank centre) for Q1, Q3 and Q2
for kind in ('Q1', 'Q3', 'Q2'):
    pos = [(a, c) for a in range(6) for c in range(11) if PAT[a][c] == kind]
    if kind == 'Q2':
        sa = sum(a for a, _ in pos) / len(pos) - 2.5
        sc = sum(c for _, c in pos) / len(pos) - 5.0
        assert abs(sa) < 1e-9 and abs(sc) < 1e-9, (kind, sa, sc)
    else:
        assert all((5 - a, 10 - c) in pos for a, c in pos), kind
N_DUMMY_HBT = NROW * NCOL - 66
EM_OFF = {'vssq': -0.6, 'dvbe': 0.475}
ROWTRK = {'vbe_s': (-1.5, 0.3), 'vssq': (-0.6, 0.9), 'dvbe': (0.475, 0.55), 'c2': (1.5, 0.3),
          'vbe_f': (2.3, 0.3), 'vbe3': (2.9, 0.3), 'vd1': (3.5, 0.3), 'vd2': (4.1, 0.3)}
ROW_TAPS = {}   # (a, net) -> xs


def rowtap(a, net, x):
    ROW_TAPS.setdefault((a, net), []).append(x)


def hbt_cell(x, y, kind, a=None):
    pcell('npn13G2', {'Nx': 1}, x, y)
    reg('M2', 'em_%g_%g' % (x, y), x - 0.925, y - 0.785, x + 0.925, y + 0.77)
    xl, xr, yb, yt = x - 2.90, x + 2.90, y - 2.88, y + 3.33
    cont_row(x - 2.75, x + 2.75, yb)
    cont_row(x - 2.75, x + 2.75, yt)
    cont_col(y - 2.60, y + 3.05, xl)
    cont_col(y - 2.60, y + 3.05, xr)
    hw = 0.13
    ring('M1', xl + hw, yb + hw, xr - hw, yt - hw, 2 * hw)
    if kind == 'D':
        box('M1', x - 0.15, yb, x + 0.15, yt)      # C, E, B all to the cell ring (vss)
        return
    if kind != 'Q2':                               # collector-base strap (Q1, Q3, QD1, QD2)
        box('M1', x - 0.92, y - 1.26, x - 0.62, y + 1.25)
    box('M1', x - 0.925, y + 1.01, x + 0.925, y + 1.75)   # collector Metal1 extended for the Via1 at y + 1.5
    if kind in ('Q2', 'Q1'):                        # base tap on the vbe sense track (stacked Via1 + Via2)
        box('M1', x - 0.975, y - 1.75, x + 0.975, y - 1.02)
        stack(x + 0.6, y - 1.5, 'vbe_s', 2)
        rowtap(a, 'vbe_s', x + 0.6)
    if kind == 'Q2':
        stack(x - 0.6, y + 1.5, 'c2', 2)
        rowtap(a, 'c2', x - 0.6)
        cuts('Via2', x, y + EM_OFF['dvbe'], 3, 1)
        rowtap(a, 'dvbe', x)
        return
    if kind in ('Q1', 'Q3', 'QD2'):
        cuts('Via2', x, y + EM_OFF['vssq'], 4, 1)
        rowtap(a, 'vssq', x)
    cnet = {'Q1': 'vbe_f', 'Q3': 'vbe3', 'QD1': 'vd1', 'QD2': 'vd2'}[kind]
    via1(x - 0.6, y + 1.5, cnet)
    m2_v(x - 0.6, y + 1.5, y + ROWTRK[cnet][0], cnet)
    via2(x - 0.6, y + ROWTRK[cnet][0], cnet)
    rowtap(a, cnet, x - 0.6)
    if kind == 'QD1':                               # emitter (vd2): Metal2 up from the emitter pad
        m2_v(x + 0.6, y + 0.5, y + ROWTRK['vd2'][0], 'vd2')
        via2(x + 0.6, y + ROWTRK['vd2'][0], 'vd2')
        rowtap(a, 'vd2', x + 0.6)


for j in range(NROW):
    for i in range(NCOL):
        if j in (0, NROW - 1) or i in (0, NCOL - 1):
            hbt_cell(bx(i), by(j), 'D')
        else:
            hbt_cell(bx(i), by(j), PAT[j - 1][i - 1], j - 1)
# outer p+ ring, bridged to the cell rings (G1)
HB = guard_ring_p(bx(0) - 3.15 - 0.6, by(0) - 3.13 - 0.6, bx(NCOL - 1) + 3.15 + 0.6, by(NROW - 1) + 3.58 + 0.6)
for i in range(NCOL):
    x = bx(i)
    box('M1', x - 0.15, by(NROW - 1) + 3.20, x + 0.15, HB[3])
    box('M1', x - 0.15, HB[1], x + 0.15, by(0) - 2.75)
for j in range(NROW):
    y = by(j)
    box('M1', HB[0], y - 0.15, bx(0) - 2.77, y + 0.15)
    box('M1', bx(NCOL - 1) + 2.77, y - 0.15, HB[2], y + 0.15)
for j in (0, 3, NROW - 1):
    ring_to_vss_col(HB[0], HB[2], by(j) + 0.0, VCOL_L)
    ring_to_vss_col(HB[0], HB[2], by(j) + 0.0, VCOL_R)
# bank row tracks (drawn after the trunk allocation, see below)
for (a, net), xs in ROW_TAPS.items():
    dy, w = ROWTRK[net]
    fixed_track(net, by(a + 1) + dy, xs, w, 2 if net == 'vssq' else 1)

# =============================================================================================
# MOS helpers (G1). PCell origin = Activ lower-left; footprint lf = l + 0.68 wide, w tall.


def mos(kind, w, l, x, y):
    pcell('pmosHV' if kind == 'p' else 'nmosHV', {'w': '%gu' % w, 'l': '%gu' % l, 'ng': 1}, x, y)
    return dict(x=x, y=y, w=w, l=l, lf=l + 0.68, gx=x + 0.34 + l / 2)


def gate_tab(d):
    gx, y = d['gx'], d['y']
    box('GatPoly', gx - 0.15, y - 1.0, gx + 0.15, y - 0.18)
    square('Cont', gx, y - 0.70, CONT)
    box('M1', gx - 0.15, y - 0.95, gx + 0.15, y - 0.45)
    return gx, y - 0.70


def sd_pad(d, side, yv):
    x = d['x'] - 0.15 if side == 'L' else d['x'] + d['lf'] + 0.15
    if side == 'L':
        box('M1', x - 0.2, yv - 0.2, d['x'] + 0.23, yv + 0.2)
    else:
        box('M1', d['x'] + d['lf'] - 0.23, yv - 0.2, x + 0.2, yv + 0.2)
    return x, yv


# =============================================================================================
# Block N: NMOS row (MNC1 x 16 fingers, MNC2 x 2 fingers, w = 10 / l = 1 each; MNI, MKFB)
XN0, PN = 16.0, 2.8
FING = ['D'] + ['A'] * 8 + ['B'] * 2 + ['A'] * 8 + ['D']
NR_TOP = YN + 11.0
x_last = None
for k, f in enumerate(FING):
    x = XN0 + PN * k
    d = mos('n', 10, 1, x, YN)
    x_last = x + d['lf']
    gx, gy = gate_tab(d)
    if f == 'D':      # dummy finger: source, drain and gate to the ring (vss)
        box('M1', x + 0.07, YN + 0.3, x + 0.23, NR_TOP + 0.15)
        box('M1', x + d['lf'] - 0.23, YN + 0.3, x + d['lf'] - 0.07, NR_TOP + 0.15)
        box('M1', gx - 0.15, YN - 1.8 - 0.15, gx + 0.15, gy)
        continue
    snet, dnet = ('vbe_f', 'n1') if f == 'A' else ('c2', 'pcasc')
    px, py = sd_pad(d, 'L', YN + 0.5)
    m1_tap('CB', snet, px, py)
    px, py = sd_pad(d, 'R', YN + 9.5)
    m1_tap('NC', dnet, px, py)
    m1_tap('CB', 'vb2', gx, gy)
    x_last = x + d['lf']
SMALL = [('MNI', 1, 0.5, x_last + 1.6, ('vss', 'kick', 'det')),
         ('MKFB', 1, 4, x_last + 1.6 + 1.18 + 1.6, ('vss', 'pbias', 'kick'))]
for name, w, l, x, (snet, dnet, gnet) in SMALL:
    d = mos('n', w, l, x, YN)
    box('M1', x + 0.07, YN + 0.3, x + 0.23, NR_TOP + 0.15)      # source up into the ring
    px, py = sd_pad(d, 'R', YN + w / 2)
    box('M1', d['x'] + d['lf'] - 0.23, py, d['x'] + d['lf'], YN + 9.5)          # drain strip up to the tap level
    box('M1', d['x'] + d['lf'] - 0.23, YN + 9.3, px + 0.2, YN + 9.7)
    m1_tap('NC', dnet, px, YN + 9.5)
    gx, gy = gate_tab(d)
    m1_tap('CB', gnet, gx, gy)
    x_last = x + d['lf']
box('TGO', XN0 - 0.5, YN - 1.5, x_last + 0.5, YN + 10.6)
NR = guard_ring_p(XN0 - 1.2, YN - 1.8, x_last + 1.2, NR_TOP)
ring_to_vss_col(NR[0], NR[2], YN + 5.0, VCOL_L)
ring_to_vss_col(NR[0], NR[2], YN + 5.0, VCOL_R)

# =============================================================================================
# Blocks C1, C2: cascode rows (own n-wells, body = source)
XC0, PC = 9.7, 8.0
CASC1 = [('MC1_0', 'd1_0', 'n1'), ('MC1_1', 'd1_1', 'n1'), ('MC1_2', 'd1_2', 'n1'), ('MC1_3', 'd1_3', 'n1'),
         ('MC1_4', 'd1_4', 'n1'), ('MC1_5', 'd1_5', 'n1'), ('DUMC1', None, None)]
CASC2 = [('MC1_6', 'd1_6', 'n1'), ('MC1_7', 'd1_7', 'n1'), ('MC2', 'd2', 'pbias'), ('MC3', 'd3', 'vref'),
         ('MC4', 'd4', 'iptat'), ('MC5', 'd5', 'vb2'), ('DUMC2', None, None)]
N_DUMMY_PC = 0


def casc_row(devs, YC, ch_down, ch_up, tx):
    global N_DUMMY_PC
    for k, (name, snet, dnet) in enumerate(devs):
        x = XC0 + PC * k
        d = mos('p', 10, 4, x, YC)
        box('NWell', x - 0.62, YC - 0.62, x + 5.30, YC + 12.4)
        box('TGO', x - 0.62, YC - 1.5, x + 5.30, YC + 12.4)
        ntap_strip(x + 0.3, YC + 11.2, x + 4.4, YC + 11.6)
        box('M1', x + 0.07, YC + 9.9, x + 0.23, YC + 11.6)
        box('M1', x + 0.07, YC + 11.2, x + 0.3, YC + 11.6)
        gx, gy = gate_tab(d)
        if snet is None:                           # dummy: drain and gate to the tie, tie to vdd by a Metal4 trunk
            N_DUMMY_PC += 1
            box('M1', x + 4.45, YC + 9.9, x + 4.61, YC + 11.6)
            box('M1', x + 4.4, YC + 11.2, x + 4.61, YC + 11.6)
            via1(gx, gy, 'vdd_dum')
            m2_v(gx, gy, YC + 11.4, 'vdd_dum')
            via1(gx, YC + 11.4, 'vdd_dum')
            cuts('Via2', gx, YC + 11.4)
            cuts('Via3', gx, YC + 11.4)
            box('M3', gx - 0.2, YC + 11.2, gx + 0.2, YC + 11.6)
            mbox('M4', 'vdd', gx - 0.2, YC + 11.2, gx + 0.2, YC + 11.6)
            POINTS.setdefault('vdd', []).append((gx, YC + 11.4))
            continue
        m1_tap(ch_up, snet, x + tx, YC + 11.4)
        px, py = sd_pad(d, 'R', YC + 0.5)
        m1_tap(ch_down, dnet, px, py)
        m1_tap(ch_down, 'pcasc', gx, gy)


casc_row(CASC1, YC1, 'NC', 'C12', 1.2)
casc_row(CASC2, YC2, 'C12', 'DC', 1.2)
XDUMC = XC0 + PC * 6 + 0.34 + 2.0
TRUNK_SPEC['vdd'] = dict(x=XDUMC, w=0.6)
POINTS['vdd'].append((XDUMC, VDD_MID))
for j in range(3):
    square('Via3', XDUMC, VDD_MID - 0.42 + 0.42 * j, VIA)

# =============================================================================================
# Block D: mirror row (one n-well on vdd)
XD, PD = 7.0, 5.4
XD_END = XD + PD * 14 + 4.68
XMPI = XD_END + 0.92
MIR = ['D', 'MP5', 'MP1_0', 'MP1_1', 'MP1_2', 'MP1_3', 'MP2', 'MP3', 'MP1_4', 'MP1_5', 'MP1_6', 'MP1_7', 'MP4', 'MPS', 'D']
MIR_D = {'MPS': 'det', 'MP2': 'd2', 'MP3': 'd3', 'MP4': 'd4', 'MP5': 'd5'}
for i in range(8):
    MIR_D['MP1_%d' % i] = 'd1_%d' % i
TAP_Y1, TAP_Y2 = YD + 11.6, YD + 12.0
N_DUMMY_PM = 0
for j, name in enumerate(MIR):
    x = XD + PD * j
    d = mos('p', 10, 4, x, YD)
    box('M1', x + 0.07, YD + 9.9, x + 0.23, TAP_Y2)
    gx, gy = gate_tab(d)
    if name == 'D':
        N_DUMMY_PM += 1
        box('M1', x + 4.45, YD + 9.9, x + 4.61, TAP_Y2)
        via1(gx, gy, 'vdd')
        m2_v(gx, gy, TAP_Y1 + 0.2, 'vdd')
        via1(gx, TAP_Y1 + 0.2, 'vdd')
        continue
    px, py = sd_pad(d, 'R', YD + 0.5)
    m1_tap('DC', MIR_D[name], px, py)
    m1_tap('DC', 'pbias', gx, gy)
d = mos('p', 2, 0.5, XMPI, YD)
box('M1', XMPI + 0.07, YD + 1.9, XMPI + 0.23, TAP_Y2)
px, py = sd_pad(d, 'R', YD + 1.0)
m1_tap('DC', 'kick', px, py)
gx, gy = gate_tab(d)
m1_tap('DC', 'det', gx, gy)
box('NWell', XD - 1.2, YD - 1.2, XMPI + 1.18 + 1.2, YD + 13.0)
box('TGO', XD - 1.2, YD - 1.5, XMPI + 1.18 + 1.2, YD + 13.0)
ntap_strip(XD - 0.3, TAP_Y1, XMPI + 1.18 + 0.3, TAP_Y2)
for j in range(15):                                 # tie strip -> vdd bus, one Metal2 strap per device
    xx = XD + PD * j + 1.2
    via1(xx, TAP_Y1 + 0.2, 'vdd')
    mbox('M2', 'vdd', xx - 0.25, TAP_Y1 + 0.05, xx + 0.25, VDD_Y1 - 0.2)
    for jj in range(3):
        square('Via2', xx, VDD_Y0 + 0.3 + 0.5 * jj, VIA)

# =============================================================================================
# pins (Metal3 on the west / east edge, on the net's track in the given channel)
PINS = {'vref': ('BA', 'W'), 'dvbe': ('BA', 'W'), 'vbe_s': ('CB', 'W'), 'iptat': ('C12', 'W'),
        'pbias': ('DC', 'E'), 'pcasc': ('NC', 'E')}
PIN_NAME = {'vbe_s': 'vbe'}
for net, (ch, side) in PINS.items():
    CH[ch].extra.setdefault(net, []).append(0.0 if side == 'W' else W)

# =============================================================================================
# trunks: every net present in more than one place (channel, bank row track, fixed point) gets one Metal4 trunk
YR = {name: ((c.y0 + c.y1) / 2) for name, c in CH.items()}
places = {}
for name, c in CH.items():
    for n in c.nets():
        places.setdefault(n, []).append(('ch', name))
for n, trs in FIXED.items():
    for t in trs:
        places.setdefault(n, []).append(('fx', t[0]))
for n, pts in POINTS.items():
    for p in pts:
        places.setdefault(n, []).append(('pt', p[1]))


def place_y(p):
    return YR[p[1]] if p[0] == 'ch' else p[1]


def chan_bounds(p):
    if p[0] == 'ch':
        return CH[p[1]].y0, CH[p[1]].y1
    return p[1], p[1]


TRUNKS = {}   # net -> dict(x, w, y0, y1)
PREF = {'vbe_s': 14.0, 'vd2': 84.0, 'vd1': 60.7, 'c2': 43.0, 'vbe_f': 30.0, 'kick': 84.0, 'det': 67.5,
        'pbias': 9.4, 'pcasc': 30.3, 'vb2': 55.0, 'n1': 30.0}


def m4_free(x, w, y0, y1):
    for n, t in TRUNKS.items():
        if t['y1'] < y0 - 0.5 or t['y0'] > y1 + 0.5:
            continue
        if abs(t['x'] - x) < (t['w'] + w) / 2 + 0.3:
            return False
    return True


order = sorted(places, key=lambda n: (n not in TRUNK_SPEC, n))
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
        for t in FIXED.get(net, []):
            xs += t[1]
        pref = PREF.get(net, sum(xs) / len(xs))
        x = None
        for k in range(0, 2000):
            for cand in (pref + 0.05 * k, pref - 0.05 * k):
                if 8.0 <= cand <= W - 8.0 and m4_free(cand, w, lo, hi):
                    x = cand
                    break
            if x is not None:
                break
        if x is None:
            raise SystemExit('no trunk position for %s' % net)
    TRUNKS[net] = dict(x=round(x, 3), w=w, y0=lo, y1=hi)
    for p in ps:
        if p[0] == 'ch':
            CH[p[1]].extra.setdefault(net, []).append(round(x, 3))
        elif p[0] == 'fx':
            for t in FIXED[net]:
                if abs(t[0] - p[1]) < 1e-9 and round(x, 3) not in t[1]:
                    t[1].append(round(x, 3))

# =============================================================================================
# channel track assignment (left edge) and drawing
REPORT = {}
# NC: NMOS n1 drain stubs rise to the n1 track, cascode pcasc gate stubs come down to the pcasc track: n1 below pcasc
ORDER = {'NC': ['n1', 'pcasc']}
for name, c in CH.items():
    nets = c.nets()
    iv = sorted(((min(xs) - 0.25, max(xs) + 0.25, n) for n, xs in nets.items()), key=lambda t: t[0])
    tracks = []   # last x end per track
    for n in ORDER.get(name, []):                  # nets placed first, one track each, from the channel bottom
        xs = nets[n]
        tracks.append(max(xs) + 0.25)
        c.track[n] = len(tracks) - 1
    for x0, x1, n in iv:
        if n in c.track:
            continue
        for k, end in enumerate(tracks):
            if x0 > end + 0.3:
                tracks[k] = x1
                c.track[n] = k
                break
        else:
            tracks.append(x1)
            c.track[n] = len(tracks) - 1
    ntr = len(tracks)
    REPORT[name] = dict(tracks=ntr, capacity=int((c.y1 - c.y0 - 0.3) // TP))
    if ntr > REPORT[name]['capacity']:
        print('CHANNEL OVERFLOW', name, REPORT[name])
    # track order: lowest index nearest the channel bottom
    for n, k in c.track.items():
        c.track[n] = c.y0 + 0.3 + k * TP
    for n, xs in nets.items():
        y = c.track[n]
        x0, x1 = min(xs), max(xs)
        if x1 - x0 < 0.5:
            x0, x1 = (x0 + x1) / 2 - 0.25, (x0 + x1) / 2 + 0.25
        box('M3', max(x0 - 0.15, 0.0), y - 0.15, min(x1 + 0.15, W), y + 0.15)
    last = {}
    for n, x, yf in sorted(c.taps, key=lambda t: t[1]):
        y = c.track[n]
        m2_v(x, yf, y, n)
        if n in last and x - last[n][0] < 0.75:     # same net close by: merge the two stubs, one Via2
            xp, yfp = last[n]
            ya, yb = (max(min(yf, y), min(yfp, y)), min(max(yf, y), max(yfp, y)))
            mbox('M2', n, xp - 0.15, min(ya, yb) - 0.15, x + 0.15, max(ya, yb) + 0.15)
            continue
        via2(x, y, n)
        last[n] = (x, yf)
for name, c in CH.items():
    print('channel', name, REPORT[name])

# bank row tracks
for net, trs in FIXED.items():
    for y, xs, w, ny3 in trs:
        box('M3', min(xs) - 0.8, y - w / 2, max(xs) + 0.8, y + w / 2)

# trunks
for net, t in TRUNKS.items():
    ys = []
    for p in places[net]:
        if p[0] == 'ch':
            ys.append(CH[p[1]].track[net])
        else:
            ys.append(p[1])
    y0, y1 = min(ys), max(ys)
    x, w = t['x'], t['w']
    mbox('M4', net, x - w / 2, y0 - 0.7, x + w / 2, y1 + 0.7)
    nx = max(1, int((w - 0.3) // VP) + 1)
    for p in places[net]:
        if p[0] == 'ch':
            via3(x, CH[p[1]].track[net], net, nx=nx)
        elif p[0] == 'fx':
            ww = [tt[2] for tt in FIXED[net] if abs(tt[0] - p[1]) < 1e-9][0]
            ny = 2 if ww > 0.8 else 1
            via3(x, p[1], net, nx=nx, ny=ny)
    t['y0'], t['y1'] = y0, y1

# pins
for net, (ch, side) in PINS.items():
    y = CH[ch].track[net]
    x1, x2 = (0.0, 1.5) if side == 'W' else (W - 1.5, W)
    box('M3pin', x1, y - 0.15, x2, y + 0.15)
    label('M3txt', (x1 + x2) / 2, y, PIN_NAME.get(net, net))
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
        # the HBT emitter pad registry name stands for whatever net the emitter has; same-cell shapes are fine
        if c[0].startswith('em_') or c[1].startswith('em_'):
            other = c[1] if c[0].startswith('em_') else c[0]
            e = c[0] if c[0].startswith('em_') else c[1]
            ex, ey = [float(v) for v in e[3:].split('_')]
            sb = c[5] if c[0].startswith('em_') else c[4]
            if ex - 1.0 <= (sb[0] + sb[2]) / 2 <= ex + 1.0 and other in ('vd2', 'vssq', 'dvbe'):
                continue
        print(layer, 'CONFLICT', c)
        nbad += 1
if nbad:
    raise SystemExit('%d spacing conflicts, GDS not written' % nbad)

out = os.path.join(HERE, 'r1_bgr.gds')
ly.write(out)
bb = top.dbbox()
print('wrote', out, 'bbox', bb, 'area_mm2 %.5f' % (W * H * 1e-6))

# =============================================================================================
# LVS reference netlist: netlist of record in CDL form + the layout dummies
cdl = ['* r1_bgr LVS reference netlist, written by layout/r1_bgr_layout.py from schematic/r1_bgr.spice (netlist of record).',
       '* Format conversion only (X-calls -> M/R/Q, sub! -> vss, mm_ok dropped, npn13G2 le/we written out), plus the layout',
       '* dummies: %d npn13G2 (all terminals vss), %d sg13_hv_pmos 10/4 (all vdd), 2 sg13_hv_nmos 10/1 (all vss).'
       % (N_DUMMY_HBT, N_DUMMY_PM + N_DUMMY_PC)]
for line in open(SCH):
    line = line.strip()
    if not line or line.startswith('*'):
        continue
    if line.startswith('.subckt') or line.startswith('.ends'):
        cdl.append(line)
        continue
    f = line.split()
    params = [p for p in f if '=' in p and not p.startswith('mm_ok')]
    if 'sg13_hv_pmos' in f or 'sg13_hv_nmos' in f:
        cdl.append('M%s %s %s %s %s %s %s' % (f[0][1:], f[1], f[2], f[3], f[4], f[5], ' '.join(params)))
    elif 'rppd' in f or 'rhigh' in f:
        sub = 'vss' if f[3] == 'sub!' else f[3]
        cdl.append('R%s %s %s %s %s %s' % (f[0][1:], f[1], f[2], sub, f[4], ' '.join(params)))
    elif 'npn13G2' in f:
        nx = [p for p in params if p.startswith('Nx=')][0]
        cdl.append('Q%s %s %s %s %s npn13G2 le=900n we=70n %s' % (f[0][1:], f[1], f[2], f[3], f[4], nx))
    else:
        raise SystemExit('unhandled line: ' + line)
ends = cdl.pop()
for k in range(N_DUMMY_HBT):
    cdl.append('QDUM%d vss vss vss vss npn13G2 le=900n we=70n Nx=1' % (k + 1))
for k in range(N_DUMMY_PM + N_DUMMY_PC):
    cdl.append('MDUMP%d vdd vdd vdd vdd sg13_hv_pmos w=10u l=4u ng=1 m=1' % (k + 1))
for k in range(2):
    cdl.append('MDUMN%d vss vss vss vss sg13_hv_nmos w=10u l=1u ng=1 m=1' % (k + 1))
cdl.append(ends)
with open(os.path.join(HERE, 'r1_bgr_lvs.cdl'), 'w') as fh:
    fh.write('\n'.join(cdl) + '\n')
meta = dict(W=W, H=H, area_mm2=W * H * 1e-6, n_dummy_hbt=N_DUMMY_HBT, n_dummy_pmos=N_DUMMY_PM + N_DUMMY_PC, n_dummy_nmos=2,
            trunks={n: dict(x=t['x'], w=t['w'], y0=round(t['y0'], 3), y1=round(t['y1'], 3)) for n, t in TRUNKS.items()},
            channels=REPORT)
with open(os.path.join(HERE, 'r1_bgr_layout_meta.json'), 'w') as fh:
    json.dump(meta, fh, indent=1)
print('wrote r1_bgr_lvs.cdl and r1_bgr_layout_meta.json')
