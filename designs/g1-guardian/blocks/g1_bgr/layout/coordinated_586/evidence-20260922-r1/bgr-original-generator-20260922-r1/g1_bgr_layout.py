#!/usr/bin/env python3
"""G1_BGR layout generator (KLayout batch Python, PDK PCells from library SG13_dev).

Run inside the pinned container (KLayout 0.30.9, PDK commit 8437402):
  G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/layout flow/run.sh klayout -b -r g1_bgr_layout.py
Writes g1_bgr.gds (top cell g1_bgr) and g1_bgr.lef next to this script. Every device is a PDK PCell
instance (library SG13_dev: pmosHV, nmosHV, rppd, rhigh, npn13G2); everything else is drawn here.
Before writing, the script checks that no two Metal2 verticals of different nets violate the Metal2
spacing (a short found in the first LVS run of this generator came from exactly that).

Floorplan (bottom to top, all dimensions um, macro 84 x 124, origin bottom-left):
  y   0 ..   2   vss bus (Metal3, pin on the south edge)
  y   5 ..  58   resistor arrays: 23 rppd columns (w=1, ~50 um segments, pitch 1.9, common centroid
                 R2 around R1, RX and RB outside, dummies at the ends) and 17 rhigh columns (RDET,
                 w=0.5, 15 x 49 um, pitch 1.4, dummies at the ends), one p+ guard ring
  y  60 ..  66   channel BA (Metal3 tracks)
  y  67 ..  82   HBT array: 2 rows x 11 npn13G2, row 1 = D Q2 Q2 Q2 Q2 Q1 Q2 Q2 Q2 Q2 D (1:8 common
                 centroid), row 0 = D D D QD2 QD1 Q1B Q3 D D D D, PCell p+ rings merged, outer p+ ring
  y  82 ..  88   channel CB
  y  89 .. 103   cascode PMOS MC5 MC3 MC1 MC2 MC4 (own n-wells, body = source) | NMOS group in a p+ ring
                 (x 46.8 .. 76.2): MNC1/MNC2 as 4 interdigitated 10 um fingers (a b b a), MNI MKFB MSW1
                 MSW2 MNI2
  y 104 .. 110   channel DC
  y 112 .. 120   mirror PMOS row: 12 half fingers (w=5, l=4) MPS MP5 MP4 MP2 MP1 MP3 | MP3 MP1 MP2 MP4 MP5 MPS
                 (mirror symmetric = common centroid), MPI MPI2 at the left, one n-well tied to vdd
  y 122 .. 124   vdd bus (Metal3, pin on the north edge)
Signal pins: Metal3 stubs on the west (vref iptat vbe dvbe) and east (pbias pcasc r4) edges.
Routing: Metal1 inside devices, Metal2 vertical, Metal3 horizontal.
"""
import os
import sys

K = '/foss/pdks/ihp-sg13g2/libs.tech/klayout/python'
for p in [K, K + '/pycell4klayout-api/source/python']:
    sys.path.insert(0, p)
import pya  # noqa: E402
import sg13g2_pycell_lib  # noqa: E402,F401  (registers library SG13_dev)

HERE = os.path.dirname(os.path.abspath(__file__))
lib = pya.Library.library_by_name('SG13_dev', 'sg13g2')
ly = pya.Layout()
ly.dbu = 0.001
LAYERS = {'Activ': (1, 0), 'GatPoly': (5, 0), 'Cont': (6, 0), 'pSD': (14, 0), 'NWell': (31, 0), 'TGO': (44, 0),
          'M1': (8, 0), 'M1pin': (8, 2), 'M1txt': (8, 25), 'Via1': (19, 0),
          'M2': (10, 0), 'M2pin': (10, 2), 'M2txt': (10, 25), 'Via2': (29, 0),
          'M3': (30, 0), 'M3pin': (30, 2), 'M3txt': (30, 25),
          # no-fill layers (the SG13_dev NoFillerStack PCell writes the same nine <layer>/23 rectangles) and the
          # all-metal NoMetFiller marker; the chip-level PDK filler subtracts all of them (padring density probe)
          'Activ_nf': (1, 23), 'GatPoly_nf': (5, 23), 'M1_nf': (8, 23), 'M2_nf': (10, 23), 'M3_nf': (30, 23),
          'M4_nf': (50, 23), 'M5_nf': (67, 23), 'TM1_nf': (126, 23), 'TM2_nf': (134, 23), 'NoMetFiller': (160, 0),
          'prBoundary': (189, 4)}
NOFILL_ALL = ('Activ_nf', 'GatPoly_nf', 'M1_nf', 'M2_nf', 'M3_nf', 'M4_nf', 'M5_nf', 'TM1_nf', 'TM2_nf', 'NoMetFiller')
L = {n: ly.layer(*v) for n, v in LAYERS.items()}
top = ly.create_cell('g1_bgr')

CONT, CP = 0.16, 0.34      # contact size / pitch
VIA, VP = 0.19, 0.42       # via size / pitch
W3 = 0.3                   # signal wire width (Metal2 vertical, Metal3 horizontal)
MACRO_W, MACRO_H = 84.0, 124.0
N_DUMMY_HBT = 9            # must match schematic/make_lvs_cdl.py


def um(v):
    return int(round(v * 1000))


def box(layer, x1, y1, x2, y2):
    top.shapes(L[layer]).insert(pya.Box(um(min(x1, x2)), um(min(y1, y2)), um(max(x1, x2)), um(max(y1, y2))))


def ring(layer, x1, y1, x2, y2, w):
    """closed ring of width w just outside the box (x1,y1,x2,y2)"""
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


def _cuts(layer, x, y, n, d):
    """n via cuts centred on (x, y), spaced VP along d ('x' or 'y'); returns the pad box (0.3 wide)"""
    for i in range(n):
        o = (i - (n - 1) / 2) * VP
        square(layer, x + o if d == 'x' else x, y + o if d == 'y' else y, VIA)
    ext = (n - 1) * VP / 2 + 0.15
    return (x - ext, y - 0.15, x + ext, y + 0.15) if d == 'x' else (x - 0.15, y - ext, x + 0.15, y + ext)


def via1(x, y, n=1, d='y', net=None):
    """Via1 (n cuts along d; the PDK LEF gives 20 Ohm per cut) with Metal1 and Metal2 pads, 0.055 enclosure.
    With a net name the Metal2 pad takes part in the Metal2 spacing self-check."""
    pad = _cuts('Via1', x, y, n, d)
    box('M1', *pad)
    box('M2', *pad)
    if net:
        M2_SEGS.append((net, *pad))


def via2(x, y, n=1, d='x', net=None):
    pad = _cuts('Via2', x, y, n, d)
    box('M2', *pad)
    box('M3', *pad)
    if net:
        M2_SEGS.append((net, *pad))


def via_array(layer, x1, y1, x2, y2, margin=0.1):
    """fill a rectangle with vias at pitch VP, keeping `margin` to the rectangle edges"""
    nx = int((x2 - x1 - 2 * margin - VIA) // VP) + 1
    ny = int((y2 - y1 - 2 * margin - VIA) // VP) + 1
    x0 = (x1 + x2) / 2 - (nx - 1) * VP / 2
    y0 = (y1 + y2) / 2 - (ny - 1) * VP / 2
    for i in range(nx):
        for j in range(ny):
            square(layer, x0 + i * VP, y0 + j * VP, VIA)


M2_SEGS = []   # (net, x1, y1, x2, y2) of every Metal2 vertical drawn through m2_v, for the collision check


def m2_v(x, y1, y2, w=W3, net=None):
    x1, y1_, x2, y2_ = x - w / 2, min(y1, y2) - w / 2, x + w / 2, max(y1, y2) + w / 2
    box('M2', x1, y1_, x2, y2_)
    M2_SEGS.append((net, x1, y1_, x2, y2_))


def m3_h(y, x1, x2, w=W3):
    box('M3', min(x1, x2) - w / 2, y - w / 2, max(x1, x2) + w / 2, y + w / 2)


def guard_ring_p(x1, y1, x2, y2, w=0.30, net='vss'):
    """p+ substrate ring around the box: Activ + pSD, contacts, 0.26 um Metal1 ring. Returns the
    Metal1 centre lines (xl, yb, xr, yt)."""
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
    label('M1txt', xl, (yb + yt) / 2, net)
    return xl, yb, xr, yt


def ntap_strip(x1, y1, x2, y2, net):
    """n+ well tie (Activ without pSD, inside an NWell drawn by the caller), contacts, Metal1"""
    box('Activ', x1, y1, x2, y2)
    box('M1', x1, y1, x2, y2)
    cont_row(x1 + 0.07, x2 - 0.07, (y1 + y2) / 2)
    label('M1txt', (x1 + x2) / 2, (y1 + y2) / 2, net)


class Router:
    """Metal3 horizontal tracks (one y per net per channel) and Metal2 vertical columns, with the
    extents taken from the registered taps; every tap places a Via2."""

    def __init__(self):
        self.tracks = {}
        self.cols = {}

    def tap(self, net, y, x, n=1):
        via2(x, y, n, net=net)
        self.tracks.setdefault((net, y), []).append(x)

    def extend(self, net, y, x):
        self.tracks.setdefault((net, y), []).append(x)

    def vtap(self, net, x, y, n=1):
        via2(x, y, n, net=net)
        self.cols.setdefault((net, x), []).append(y)

    def finish(self):
        for (net, y), xs in self.tracks.items():
            m3_h(y, max(min(xs), 0.15), min(max(xs), MACRO_W - 0.15))
            # the resistor mid-jogs stay unlabelled: a labelled intermediate net stops the LVS deck from
            # combining the series segments into one resistor (seen in run 0: R2 extracted as 2 x 157.5u)
            if not net.endswith('_mid'):
                label('M3txt', (min(xs) + max(xs)) / 2, y, net)
        for (net, x), ys in self.cols.items():
            m2_v(x, min(ys), max(ys), net=net)
            label('M2txt', x, (min(ys) + max(ys)) / 2, net)


R = Router()


def m1_to_track(net, x, y_m1, ty, n1=1, d1='y', n2=1):
    """Via1 (n1 cuts along d1) at (x, y_m1) on existing Metal1, Metal2 vertical to the track y, Via2 (n2 cuts)
    there. n1 = n2 = 2 on the DC current path through R1 and R2 (see README, wiring resistance)."""
    via1(x, y_m1, n1, d1, net=net)
    m2_v(x, y_m1, ty, net=net)
    R.tap(net, ty, x, n2)


def m2_to_track(net, x, y_m2, ty, n2=1):
    m2_v(x, y_m2, ty, net=net)
    R.tap(net, ty, x, n2)


# ---------------------------------------------------------------------------------------------
# track map (Metal3 y positions)
BA = {'vd2': 59.8, 'vd1': 60.4, 'vbe3': 61.0, 'b1b': 61.6, 'dvbe': 62.2, 'vref': 62.8, 'vb2': 63.4,
      'pbias': 64.0, 'pcasc': 64.6, 'det': 65.2}
BANDM = {'vbe': 73.6}
CB = {'c2': 82.4, 'dvbe': 83.0, 'vbe': 83.6, 'b1b': 84.2, 'n1': 84.8, 'pcasc': 85.4, 'vref': 86.0,
      'vb2': 86.6, 'iptat': 87.2}
DC = {'pbias': 104.2, 'd1': 104.8, 'd2': 105.4, 'd3': 106.0, 'd4': 106.6, 'd5': 107.2, 'det': 107.8,
      'kick': 108.4, 'r4n': 109.0, 'r4': 109.6}
# vertical Metal2 columns in the side channels
VCOL = {'vss_l': 1.0, 'dvbe': 2.3, 'vref': 3.2, 'vb2': 4.1,          # 0.9 um pitch: room for 2-cut Via2 pads
        'b1b': 80.0, 'det': 80.6, 'pcasc': 81.2, 'pbias': 81.8, 'vss_r': 83.0}

# ---------------------------------------------------------------------------------------------
# power buses
VSS_Y, VDD_Y = 1.0, 123.0
box('M3', 0, 0, MACRO_W, 2.0)
box('M3pin', 0, 0, MACRO_W, 2.0)
label('M3txt', MACRO_W / 2, 1.0, 'vss')
box('M3', 0, 122.0, MACRO_W, 124.0)
box('M3pin', 0, 122.0, MACRO_W, 124.0)
label('M3txt', MACRO_W / 2, 123.0, 'vdd')
PINS = {'vss': ('Metal3', 0, 0, MACRO_W, 2.0, 'GROUND'), 'vdd': ('Metal3', 0, 122.0, MACRO_W, 124.0, 'POWER')}


def side_pin(net, y, side):
    """0.3 um Metal3 stub from the macro edge to x=1.5 (west) or x=82.5 (east), merged with the track"""
    if side == 'W':
        x1, x2 = 0.0, 1.5
        R.extend(net, y, 0.0)
    else:
        x1, x2 = MACRO_W - 1.5, MACRO_W
        R.extend(net, y, MACRO_W)
    box('M3pin', x1, y - 0.15, x2, y + 0.15)
    label('M3txt', (x1 + x2) / 2, y, net)
    PINS[net] = ('Metal3', x1, y - 0.15, x2, y + 0.15, 'SIGNAL')


# vss side columns: Metal2 1.0 um wide from the bus up to the NMOS ring level, Via2 arrays on the bus
for x in (VCOL['vss_l'], VCOL['vss_r']):
    m2_v(x, 0.8, 99.5, w=1.0, net='vss')
    via_array('Via2', x - 0.5, 0.3, x + 0.5, 1.9)
    label('M2txt', x, 50, 'vss')


def ring_to_vss_col(xl, xr, y, col_x):
    """connect a p+ ring's Metal1 (vertical side at xl or xr) to a vss Metal2 column: Via1+Via2 stack on
    the ring, Metal3 jumper (crosses the signal Metal2 columns), Via2 on the column"""
    xs = xl if col_x < xl else xr
    box('M1', xs - 0.45, y - 0.25, xs + 0.45, y + 0.25)
    via1(xs, y, 2, 'x', net='vss')
    via2(xs, y, 2, 'x', net='vss')
    box('M3', min(xs, col_x) - 0.15, y - 0.15, max(xs, col_x) + 0.15, y + 0.15)
    via2(col_x, y, 2, 'x', net='vss')
    label('M3txt', (xs + col_x) / 2, y, 'vss')


def ring_to_ring(x, y_a, y_b):
    """Metal2 jumper between two p+ ring Metal1 sides (horizontal sides at y_a and y_b) at x"""
    for y in (y_a, y_b):
        box('M1', x - 0.45, y - 0.25, x + 0.45, y + 0.25)
        via1(x, y, 2, 'x', net='vss')
    m2_v(x, min(y_a, y_b), max(y_a, y_b), w=0.5, net='vss')
    label('M2txt', x, (y_a + y_b) / 2, 'vss')


# ---------------------------------------------------------------------------------------------
# Block A: resistors
YA = 5.0
XA, PA = 7.5, 1.9          # rppd columns (body x from XA + PA*i to +1)
XH, PH = 53.0, 1.4         # rhigh columns (body x from XH + PH*j to +0.5)
RPPD_COLS = (['D'] + ['RB'] * 5 + ['RX'] * 2 + ['R2'] * 3 + ['R1'] + ['R2'] * 3 + ['RX'] * 2 + ['RB'] * 5 + ['D'])
RLEN = {'RB': 50.0, 'RX': 48.0, 'R2': 52.5, 'R1': 51.5, 'D': 50.0}
assert len(RPPD_COLS) == 23 and sum(RLEN[c] for c in RPPD_COLS if c == 'R2') == 315.0
assert sum(RLEN[c] for c in RPPD_COLS if c == 'RB') == 500.0 and sum(RLEN[c] for c in RPPD_COLS if c == 'RX') == 192.0


def rppd_x(i):
    return XA + PA * i


for i, kind in enumerate(RPPD_COLS):
    x = rppd_x(i)
    if kind == 'D':   # dummy: silicided GatPoly strip of the same width and length, no resistor markers
        box('GatPoly', x, YA - 0.43, x + 1.0, YA + RLEN[kind] + 0.43)
        box('pSD', x - 0.18, YA - 0.61, x + 1.18, YA + RLEN[kind] + 0.61)
    else:
        pcell('rppd', {'w': '1u', 'l': '%gu' % RLEN[kind], 'b': 0, 'Calculate': 'R'}, x, YA)


def rppd_head(i, end):
    """Metal1 head rectangle of rppd column i: ('t'|'b') -> (x1, y1, x2, y2)"""
    x = rppd_x(i)
    ln = RLEN[RPPD_COLS[i]]
    return (x + 0.02, YA + ln + 0.13, x + 0.98, YA + ln + 0.43) if end == 't' else (x + 0.02, YA - 0.43, x + 0.98, YA - 0.13)


def rppd_strap(i, end):
    a = rppd_head(i, end)
    b = rppd_head(i + 1, end)
    box('M1', a[0], a[1], b[2], b[3])


def rppd_term(i, end):
    h = rppd_head(i, end)
    return (h[0] + h[2]) / 2, (h[1] + h[3]) / 2


# serpentine chains: (columns, first free end) -> straps alternate starting opposite to the free end
def chain(cols, free):
    other = 'b' if free == 't' else 't'
    for k in range(len(cols) - 1):
        rppd_strap(cols[k], other if k % 2 == 0 else free)
    last = free if (len(cols) - 2) % 2 == 0 else other
    return (cols[0], free), (cols[-1], last)


rb1 = chain([1, 2, 3, 4, 5], 't')      # (1,'t') .. (5,'b')
rb2 = chain([17, 18, 19, 20, 21], 'b')  # (17,'b') .. (21,'t')
r2a = chain([8, 9, 10], 't')            # (8,'t') .. (10,'b')
r2b = chain([12, 13, 14], 'b')          # (12,'b') .. (14,'t')
rxa = chain([6, 7], 't')                # (6,'t') .. (7,'t')
rxb = chain([15, 16], 't')              # (15,'t') .. (16,'t')
assert rb1[1] == (5, 'b') and rb2[0] == (17, 'b') and r2a[1] == (10, 'b') and r2b[0] == (12, 'b')
assert rxa[1] == (7, 't') and rxb[0] == (15, 't') and rb2[1] == (21, 't') and r2b[1] == (14, 't')
# jogs between the two halves of RB, R2 (Metal3 below the array) and RX (Metal3 above the array)
for (ca, cb), y, net in (((5, 17), 3.5, 'rb_mid'), ((10, 12), 2.9, 'r2_mid')):
    for c in (ca, cb):
        x, ym = rppd_term(c, 'b')
        m1_to_track(net, x, ym, y)
for c in (7, 15):
    x, ym = rppd_term(c, 't')
    m1_to_track('rx_mid', x, ym, 58.9)
# terminals to the BA channel
for c, net in ((1, 'pbias'), (21, 'pcasc'), (6, 'vb2'), (16, 'vd1')):
    x, ym = rppd_term(c, 't')
    m1_to_track(net, x, ym, BA[net])
for c, net in ((8, 'vref'), (14, 'vbe3'), (11, 'dvbe')):       # R1/R2 current path: 2-cut vias
    x, ym = rppd_term(c, 't')
    m1_to_track(net, x, ym, BA[net], n1=2, d1='x', n2=2)
# R1 bottom: star ground at the HBT ring (Q1's emitter sits on that ring, so the ring return drop stays out
# of delta-V_BE). Metal2 at x = 28.1 (between the col-10 mid-jog pad at 27.0 and the R1 top tap at 28.9),
# 2-cut Via1 pair on an extension of the R1 bottom head, up to the outer HBT ring's bottom side (HB[1]).
x, ym = rppd_term(11, 'b')
R1_GND_X = 28.1
box('M1', R1_GND_X - 0.4, ym - 0.15, x + 0.48, ym + 0.15)
via1(R1_GND_X, ym, 2, 'x', net='vss')

# rhigh RDET: 15 segments of 49 um + 2 dummies
RH_L = 49.0
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


for k in range(1, 15):   # straps between segment k and k+1: bottom for odd k, top for even k
    end = 'b' if k % 2 == 1 else 't'
    a, b = rh_head(k, end), rh_head(k + 1, end)
    box('M1', a[0], a[1], b[2], b[3])
# terminals: segment 1 top -> det, segment 15 bottom -> vss (0.5 x 0.4 Metal1 pads for the Via1)
x = XH + PH * 1 + 0.25
box('M1', x - 0.25, YA + RH_L + 0.10, x + 0.25, YA + RH_L + 0.50)
m1_to_track('det', x, YA + RH_L + 0.30, BA['det'])
x = XH + PH * 15 + 0.25
box('M1', x - 0.25, YA - 0.50, x + 0.25, YA - 0.10)
via1(x, YA - 0.30)
m2_v(x, YA - 0.30, VSS_Y, net='vss')
via2(x, VSS_Y)

# resistor guard ring and its vss connections
RA = guard_ring_p(6.3, 3.6, 77.3, 58.9)
for xx in (12.0, 36.0, 66.0):
    box('M1', xx - 0.45, RA[1] - 0.25, xx + 0.45, RA[1] + 0.25)
    via1(xx, RA[1], 2, 'x', net='vss')
    m2_v(xx, RA[1], VSS_Y, net='vss')
    via2(xx, VSS_Y, 2, 'x', net='vss')
ring_to_vss_col(RA[0], RA[2], 30.0, VCOL['vss_l'])
ring_to_vss_col(RA[0], RA[2], 30.0, VCOL['vss_r'])

# ---------------------------------------------------------------------------------------------
# Block B: HBT array
XB, PB = 10.55, 6.3
YB0 = 70.6
YB1 = YB0 + 6.71
ROW1 = ['D', 'Q2A', 'Q2B', 'Q2C', 'Q2D', 'Q1', 'Q2E', 'Q2F', 'Q2G', 'Q2H', 'D']
ROW0 = ['D', 'D', 'D', 'QD2', 'QD1', 'Q1B', 'Q3', 'D', 'D', 'D', 'D']
assert sum(r.count('D') for r in (ROW0, ROW1)) == N_DUMMY_HBT
# nets: (C, B, E)
HBT_NETS = {'Q1': ('vbe', 'vbe', 'vss'), 'Q1B': ('vbe', 'b1b', 'vss'), 'Q3': ('vbe3', 'vbe3', 'vss'),
            'QD1': ('vd1', 'vd1', 'vd2'), 'QD2': ('vd2', 'vd2', 'vss')}
for q in 'ABCDEFGH':
    HBT_NETS['Q2' + q] = ('c2', 'vbe', 'dvbe')


def hbt_cell(x, y, name, row):
    pcell('npn13G2', {'Nx': 1}, x, y)
    # contacts and Metal1 on the PCell's own p+ ring (centre lines x+-2.90, y-2.88 / y+3.33)
    xl, xr, yb, yt = x - 2.90, x + 2.90, y - 2.88, y + 3.33
    cont_row(x - 2.75, x + 2.75, yb)
    cont_row(x - 2.75, x + 2.75, yt)
    cont_col(y - 2.60, y + 3.05, xl)
    cont_col(y - 2.60, y + 3.05, xr)
    hw = 0.13
    ring('M1', xl + hw, yb + hw, xr - hw, yt - hw, 2 * hw)
    label('M1txt', xr, y + 0.2, 'vss')
    if name == 'D':
        box('M1', x - 0.15, yb, x + 0.15, yt)      # C, E, B all to the vss ring
        return
    cnet, bnet, enet = HBT_NETS[name]
    # emitter (Metal2 pad -0.925..0.925 x -0.785..0.77)
    if enet == 'vss':
        box('M1', x - 0.15, yb - 0.15, x + 0.15, yb + 0.15)
        via1(x, yb)
        m2_v(x, y - 0.6, yb, net='vss')
    elif row == 1:
        m2_to_track(enet, x, y + 0.6, CB[enet])
    else:
        m2_to_track(enet, x, y - 0.6, BA[enet])
    # base: Metal1 pad extended downwards, Via1 at x+0.6, Metal2 down (Q3 carries the R2 current: 2-cut vias)
    dbl = name == 'Q3'
    box('M1', x - 0.975, y - (1.86 if dbl else 1.75), x + 0.975, y - 1.02)
    ty = BANDM[bnet] if row == 1 else BA[bnet]
    m1_to_track(bnet, x + 0.6, y - 1.5, ty, n1=2 if dbl else 1, d1='y', n2=2 if dbl else 1)
    if cnet == bnet:
        box('M1', x - 0.92, y - 1.26, x - 0.62, y + 1.25)   # collector-base strap, 0.27 from the emitter Metal1 (M1.e 0.22)
    else:
        box('M1', x - 0.925, y + 1.01, x + 0.925, y + 1.75)
        ty = CB[cnet] if row == 1 else BANDM[cnet]
        m1_to_track(cnet, x - 0.6, y + 1.5, ty)


for i, name in enumerate(ROW1):
    hbt_cell(XB + PB * i, YB1, name, 1)
for i, name in enumerate(ROW0):
    hbt_cell(XB + PB * i, YB0, name, 0)
# outer p+ ring, bridged to the PCell rings by Metal1 at every column (top and bottom) and row (sides)
HB = guard_ring_p(XB - 3.15 - 0.6, YB0 - 3.13 - 0.6, XB + PB * 10 + 3.15 + 0.6, YB1 + 3.58 + 0.6)
for i in range(11):
    x = XB + PB * i
    box('M1', x - 0.15, YB1 + 3.20, x + 0.15, HB[3])
    box('M1', x - 0.15, HB[1], x + 0.15, YB0 - 2.75)
for y in (YB0, YB1):
    box('M1', HB[0], y - 0.15, XB - 2.77, y + 0.15)
    box('M1', XB + PB * 10 + 2.77, y - 0.15, HB[2], y + 0.15)
ring_to_ring(8.0, RA[3], HB[1])      # between the ring corner and the cell-0 bridge (x 10.4..10.7)
ring_to_ring(75.6, RA[3], HB[1])     # between the cell-10 bridge (73.4..73.7) and the ring side (77.3)
# ring sides to the vss columns (low-resistance return for the emitter currents; the ring Metal1 alone is
# 0.5 Ohm/um): two jumpers per side, between the rows and above row 1
for yj in (YB0 + 4.0, YB1 + 2.0):
    ring_to_vss_col(HB[0], HB[2], yj, VCOL['vss_l'])
    ring_to_vss_col(HB[0], HB[2], yj, VCOL['vss_r'])
# R1 bottom star ground: Metal2 from the R1 bottom head up to the ring's bottom side, 2-cut Via1 pair there
box('M1', R1_GND_X - 0.45, HB[1] - 0.25, R1_GND_X + 0.45, HB[1] + 0.25)
via1(R1_GND_X, HB[1], 2, 'x', net='vss')
m2_v(R1_GND_X, YA - 0.28, HB[1], net='vss')
label('M2txt', R1_GND_X, 30.0, 'vss')
# band-M vbe up to the CB vbe track through the array (between cells 5 and 6)
xv = XB + PB * 5 + 2.2
R.vtap('vbe', xv, BANDM['vbe'])
R.vtap('vbe', xv, CB['vbe'])
R.extend('vbe', BANDM['vbe'], xv)
R.extend('vbe', CB['vbe'], xv)

# ---------------------------------------------------------------------------------------------
# MOS helpers. PCell origin = Activ lower-left; footprint Lf = l + 0.68 wide, w tall; S/D Metal1
# strips at x+0.07..0.23 and x+Lf-0.23..x+Lf-0.07; gate poly x+0.34..x+0.34+l, y-0.18..y+w+0.18.
def mos(kind, w, l, x, y):
    pcell('pmosHV' if kind == 'p' else 'nmosHV', {'w': '%gu' % w, 'l': '%gu' % l, 'ng': 1}, x, y)
    return dict(x=x, y=y, w=w, l=l, lf=l + 0.68, gx=x + 0.34 + l / 2)


def gate_tab(d):
    """GatPoly tab below the gate with a contact and a 0.3 x 0.5 Metal1 pad; returns (x, y) of the pad centre"""
    gx, y = d['gx'], d['y']
    box('GatPoly', gx - 0.15, y - 1.0, gx + 0.15, y - 0.18)
    square('Cont', gx, y - 0.70, CONT)
    box('M1', gx - 0.15, y - 0.95, gx + 0.15, y - 0.45)
    return gx, y - 0.70


def sd_pad(d, side, yv):
    """Metal1 pad on the S/D strip with the Via1 centre 0.15 um outside the Activ edge; returns (x, y)"""
    x = d['x'] - 0.15 if side == 'L' else d['x'] + d['lf'] + 0.15
    if side == 'L':
        box('M1', x - 0.2, yv - 0.2, d['x'] + 0.23, yv + 0.2)
    else:
        box('M1', d['x'] + d['lf'] - 0.23, yv - 0.2, x + 0.2, yv + 0.2)
    return x, yv


def sd_strip_x(d, side):
    return d['x'] + 0.15 if side == 'L' else d['x'] + d['lf'] - 0.15


# ---------------------------------------------------------------------------------------------
# Block C: cascodes (left) and NMOS group (right)
YC = 91.0
XC, PC = 8.0, 8.0
CASC = [('MC5', 'd5', 'vb2'), ('MC3', 'd3', 'vref'), ('MC1', 'd1', 'n1'), ('MC2', 'd2', 'pbias'), ('MC4', 'd4', 'iptat')]
for k, (name, snet, dnet) in enumerate(CASC):
    x = XC + PC * k
    d = mos('p', 10, 4, x, YC)
    box('NWell', x - 0.62, YC - 0.62, x + 5.30, YC + 12.4)
    box('TGO', x - 0.62, YC - 1.5, x + 5.30, YC + 12.4)
    ntap_strip(x + 0.3, YC + 11.2, x + 4.4, YC + 11.6, snet)          # body tie = source
    box('M1', x + 0.07, YC + 9.9, x + 0.23, YC + 11.6)                # source strip up into the tie
    box('M1', x + 0.07, YC + 11.2, x + 0.3, YC + 11.6)                # ... and onto the tie Metal1 (run 0: 0.07 gap, source floating)
    m1_to_track(snet, x + 2.35, YC + 11.4, DC[snet])                  # source/body to the mirror drain track
    px, py = sd_pad(d, 'R', YC + 0.5)
    if name == 'MC3':                                                 # vref leg: R2 current, 2-cut vias
        box('M1', d['x'] + d['lf'] - 0.23, py - 0.4, px + 0.2, py + 0.4)
        m1_to_track(dnet, px, py, CB[dnet], n1=2, d1='y', n2=2)
    else:
        m1_to_track(dnet, px, py, DC[dnet] if dnet in DC else CB[dnet])
    gx, gy = gate_tab(d)
    m1_to_track('pcasc', gx, gy, CB['pcasc'])

# NMOS group: MNC1/MNC2 fingers (S/D assignment per finger), then the small devices
FING = [('MNC1', 'vbe', 'n1'), ('MNC2', 'c2', 'pcasc'), ('MNC2', 'pcasc', 'c2'), ('MNC1', 'n1', 'vbe')]
XN, PN = 48.0, 2.8
ntgo = [XN - 0.5, YC - 1.5, 0, YC + 10.6]
for k, (name, lnet, rnet) in enumerate(FING):
    x = XN + PN * k
    d = mos('n', 10, 1, x, YC)
    ntgo[2] = x + d['lf'] + 0.5
    for side, net in (('L', lnet), ('R', rnet)):
        px, py = sd_pad(d, side, YC + 0.5)
        m1_to_track(net, px, py, CB[net])
    gx, gy = gate_tab(d)
    m1_to_track('vb2', gx, gy, CB['vb2'])
# x positions chosen so that every Metal2 column that rises into channel DC (gate at x+0.34+l/2, drain at
# x+l+0.83) stays >= 0.51 um (centre to centre) from the mirror-row columns above it, which come down into
# the same channel at 14.34+5.4j (gates) and 16.83+5.4j (drains). Run 0 had MNI2's gate column on the MP3
# gate column (r4 shorted to pbias) and MSW2's gate 0.16 um from the MP5 drain column.
SMALL = [('MNI', 1, 0.5, 60.31, ('vss', 'kick', 'det')),      # (name, w, l, x, (S, D, G)); columns 60.90 / 61.64
         ('MKFB', 1, 4, 62.16, ('vss', 'pbias', 'kick')),     # 64.50 / 66.99
         ('MSW1', 2, 0.5, 68.91, ('b1b', 'vbe', 'r4')),       # gate 69.50 (S/D go down to CB)
         ('MSW2', 1, 0.5, 71.41, ('vss', 'b1b', 'r4n')),      # gate 72.00
         ('MNI2', 1, 0.5, 73.91, ('vss', 'r4n', 'r4'))]       # 74.50 / 75.24
NR_TOP = YC + 11.0    # NMOS p+ ring inner top edge
for name, w, l, x, (snet, dnet, gnet) in SMALL:
    d = mos('n', w, l, x, YC)
    ntgo[2] = x + d['lf'] + 0.5
    # source
    if snet == 'vss':
        xs = sd_strip_x(d, 'L')
        box('M1', xs - 0.15, YC + 0.3, xs + 0.15, NR_TOP + 0.15)    # Metal1 up into the ring
    else:
        px, py = sd_pad(d, 'L', YC + w / 2)
        m1_to_track(snet, px, py, CB[snet])
    # drain
    px, py = sd_pad(d, 'R', YC + w / 2)
    m1_to_track(dnet, px, py, DC[dnet] if dnet in DC else CB[dnet])
    # gate
    gx, gy = gate_tab(d)
    m1_to_track(gnet, gx, gy, DC[gnet] if gnet in DC else CB[gnet])
box('TGO', ntgo[0], ntgo[1], ntgo[2], ntgo[3])
NR = guard_ring_p(46.8, YC - 1.8, 76.2, NR_TOP)      # right side clear of the MNI2 drain pad (Metal1 to 75.44)
ring_to_vss_col(NR[0], NR[2], YC + 5.0, VCOL['vss_r'])

# ---------------------------------------------------------------------------------------------
# Block D: mirror row
YD = 112.0
XD, PD = 12.0, 5.4
MIR = ['MPS', 'MP5', 'MP4', 'MP2', 'MP1', 'MP3', 'MP3', 'MP1', 'MP2', 'MP4', 'MP5', 'MPS']
MIR_D = {'MPS': 'det', 'MP1': 'd1', 'MP2': 'd2', 'MP3': 'd3', 'MP4': 'd4', 'MP5': 'd5'}
TAP_Y1, TAP_Y2 = YD + 6.6, YD + 7.0
for j, name in enumerate(MIR):
    x = XD + PD * j
    d = mos('p', 5, 4, x, YD)
    box('M1', x + 0.07, YD + 4.9, x + 0.23, TAP_Y2)                  # source strip up into the vdd tie
    px, py = sd_pad(d, 'R', YD + 0.5)
    m1_to_track(MIR_D[name], px, py, DC[MIR_D[name]])
    gx, gy = gate_tab(d)
    m1_to_track('pbias', gx, gy, DC['pbias'])
for name, x, dnet, gnet in (('MPI', 7.5, 'kick', 'det'), ('MPI2', 9.8, 'r4n', 'r4')):
    d = mos('p', 2, 0.5, x, YD)
    box('M1', x + 0.07, YD + 1.9, x + 0.23, TAP_Y2)
    px, py = sd_pad(d, 'R', YD + 1.0)
    m1_to_track(dnet, px, py, DC[dnet])
    gx, gy = gate_tab(d)
    m1_to_track(gnet, gx, gy, DC[gnet])
XD_END = XD + PD * 11 + 4.68
box('NWell', 6.3, YD - 1.2, XD_END + 1.2, YD + 8.5)
box('TGO', 6.3, YD - 1.5, XD_END + 1.2, YD + 8.5)
ntap_strip(7.5, TAP_Y1, XD_END, TAP_Y2, 'vdd')
for xx in (15.0, 25.0, 35.0, 45.0, 55.0, 65.0, 75.0):               # tie strip -> vdd bus
    via1(xx, TAP_Y1 + 0.2)
    m2_v(xx, TAP_Y1 + 0.25, 123.65, w=0.5, net='vdd')
    via_array('Via2', xx - 0.25, 122.2, xx + 0.25, 123.8, margin=0.03)

# ---------------------------------------------------------------------------------------------
# side columns (Metal2) joining the channels, and the pins
for net, (ya, yb_) in (('dvbe', (BA['dvbe'], CB['dvbe'])), ('vref', (BA['vref'], CB['vref'])), ('vb2', (BA['vb2'], CB['vb2'])),
                       ('b1b', (BA['b1b'], CB['b1b'])), ('pcasc', (BA['pcasc'], CB['pcasc'])),
                       ('det', (BA['det'], DC['det'])), ('pbias', (BA['pbias'], DC['pbias']))):
    for yy in (ya, yb_):
        R.vtap(net, VCOL[net], yy, 2 if net in ('dvbe', 'vref') else 1)
        R.extend(net, yy, VCOL[net])
side_pin('vref', CB['vref'], 'W')
side_pin('iptat', CB['iptat'], 'W')
side_pin('vbe', CB['vbe'], 'W')
side_pin('dvbe', CB['dvbe'], 'W')
side_pin('pbias', DC['pbias'], 'E')
side_pin('pcasc', CB['pcasc'], 'E')
side_pin('r4', DC['r4'], 'E')
R.finish()

# ---------------------------------------------------------------------------------------------
# no-fill regions (all layers) with a 2.5 um margin around the matched structures, clipped to the macro:
# the rppd array R1/R2/RX/RB (pSD extent 7.32..50.48 x 4.39..58.11), the HBT array (outer ring 6.5..77.6 x
# 66.57..81.79), the cascodes (n-wells 7.38..45.3 x 90.38..103.4), the MNC1/MNC2 pair (Activ 48.0..58.08 x
# 91..101) and the mirror row (n-well 6.3..77.28 x 110.8..120.5). RDET (start-up detector), the small NMOS, the
# buses and the channels may take fill. Metal3 also stays free in the LEF pin margins outside the Metal3
# obstruction, so chip-level Metal3 routing next to the pins never meets fill. Fill inside the macro is added
# afterwards by fill_g1_bgr.sh (PDK filler).
NOFILL = [(4.8, 1.9, 53.0, 60.6), (4.0, 64.0, 80.1, 84.3), (4.9, 87.9, 47.8, 105.9), (45.5, 88.5, 60.6, 103.5),
          (3.8, 108.3, 79.8, 123.0)]
for x1, y1, x2, y2 in NOFILL:
    for lname in NOFILL_ALL:
        box(lname, max(x1, 0.0), max(y1, 0.0), min(x2, MACRO_W), min(y2, MACRO_H))
M3_OBS = (1.8, 2.6, MACRO_W - 2.0, 121.4)        # Metal3 obstruction of the LEF (see the LEF writer below)
for x1, y1, x2, y2 in ((0, 0, M3_OBS[0], MACRO_H), (M3_OBS[2], 0, MACRO_W, MACRO_H),
                       (0, 0, MACRO_W, M3_OBS[1]), (0, M3_OBS[3], MACRO_W, MACRO_H)):
    box('M3_nf', x1, y1, x2, y2)
box('prBoundary', 0, 0, MACRO_W, MACRO_H)

# ---------------------------------------------------------------------------------------------
# self-check: Metal2 verticals of different nets must keep the Metal2 spacing (0.21 um; 0.24 if one of
# them is wider than 0.39 um). Overlaps of different nets are shorts. Same-net overlaps are fine.


def m2_conflicts():
    bad = []
    for i, (na, ax1, ay1, ax2, ay2) in enumerate(M2_SEGS):
        for nb, bx1, by1, bx2, by2 in M2_SEGS[i + 1:]:
            if na == nb:
                continue
            need = 0.24 if (ax2 - ax1 > 0.39 or bx2 - bx1 > 0.39) else 0.21
            dx = max(bx1 - ax2, ax1 - bx2)
            dy = max(by1 - ay2, ay1 - by2)
            if dx < need - 1e-6 and dy < need - 1e-6:
                bad.append((na, nb, round(dx, 3), round(dy, 3), (ax1, ay1, ax2, ay2), (bx1, by1, bx2, by2)))
    return bad


conf = m2_conflicts()
for c in conf:
    print('M2 CONFLICT', c)
if conf:
    raise SystemExit('%d Metal2 conflicts, GDS not written' % len(conf))

# ---------------------------------------------------------------------------------------------
# write GDS and LEF
out = os.path.join(HERE, 'g1_bgr.gds')
ly.write(out)
print('wrote', out, 'bbox', top.dbbox())

lef = ['VERSION 5.8 ;', 'BUSBITCHARS "[]" ;', 'DIVIDERCHAR "/" ;', '', 'MACRO g1_bgr', '  CLASS BLOCK ;',
       '  ORIGIN 0 0 ;', '  FOREIGN g1_bgr 0 0 ;', '  SIZE %g BY %g ;' % (MACRO_W, MACRO_H), '  SYMMETRY X Y ;']
for net in ('vdd', 'vss', 'r4', 'vref', 'iptat', 'pbias', 'pcasc', 'vbe', 'dvbe'):
    layer, x1, y1, x2, y2, use = PINS[net]
    direction = 'INPUT' if net == 'r4' else ('INOUT' if use != 'SIGNAL' else 'OUTPUT')
    lef += ['  PIN %s' % net, '    DIRECTION %s ;' % direction, '    USE %s ;' % use, '    PORT',
            '      LAYER %s ;' % layer, '        RECT %g %g %g %g ;' % (x1, y1, x2, y2), '    END', '  END %s' % net]
lef += ['  OBS', '    LAYER Metal1 ;', '      RECT 0 0 %g %g ;' % (MACRO_W, MACRO_H),
        '    LAYER Metal2 ;', '      RECT 0 0 %g %g ;' % (MACRO_W, MACRO_H),
        '    LAYER Metal3 ;', '      RECT %g %g %g %g ;' % M3_OBS,
        '  END', 'END g1_bgr', '', 'END LIBRARY', '']
with open(os.path.join(HERE, 'g1_bgr.lef'), 'w') as f:
    f.write('\n'.join(lef))
print('wrote g1_bgr.lef')
