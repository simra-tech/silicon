#!/usr/bin/env python3
"""r1_osc layout generator (KLayout batch Python, PDK PCells from library SG13_dev).

Run inside the pinned container (KLayout 0.30.9, PDK commit 8437402), from the repository root:
  G1_CPUSET=100-102 G1_WORKDIR=designs/r1-joint/blocks/r1_osc/layout flow/run.sh klayout -b -r r1_osc_layout.py
Writes, next to this script:
  r1_osc.gds               top cell r1_osc (flat), prBoundary 189/4 = (0, 0) - (W, H)
  r1_osc_lvs.cdl           LVS reference: schematic/r1_osc.spice (netlist of record) in CDL form + the dummy MIM units
  r1_osc_layout_meta.json  macro size, track order, dummy counts, self-check results
Every device is a PDK PCell (nmos, pmos, rppd, cmim, dpantenna), flattened. Drawing helpers: r1_layout_lib.py
(a copy of the G1 g1_osc library). Descends from designs/g1-guardian/blocks/g1_osc/layout/gen_osc_layout.py.

Floorplan (y up):
  VSS bar (Metal3, pin `vss`)                                  south edge
  resistor block (west)  | transistor rows (RowLayout: NMOS row, Metal2 channel, PMOS row; east of the resistors)
                         | Metal4 track channel above the rows (one horizontal track per net, Metal3 verticals)
  CTH (vth hold MIM)     | lane of Metal3 verticals | bank A: unit array + CF_A
  above the resistors    |                          | bank B: unit array + CF_B
  VDD bar (Metal3, pin `vdd`)                                  north edge
  p+ guard ring (Activ + pSD + Metal1) 1 um inside the macro edge, tied to the VSS bar.

Resistors: rppd w = 1 um at 1.9 um pitch, all heads with connections at the top, links Metal1 straps:
  RA = 2 x 24.15 um, RB = 2 x 24.15 um (va, vdd, vdd, vb), RT1/RT2 = 8 + 8 segments (7 x 48.04 + 48.02 um each),
  RBIAS = 2 x 40 um; a dummy strip (GatPoly + pSD, no resistor marker) at each group edge.
Trim banks: 31 cmim units 4.03 x 4.03 um (25 fF) per bank on a 5.9 um grid, 4 rows x 8 columns inside, bit 4 = rows
  3-4, bit 3 = row 2, row 1 = bit 2 (4) | bit 1 (2) | bit 0 (1) | va landing slot; dummy units (same PCell, same
  orientation, both plates on vss) on the west column and on the south and north rows; CF on the east side at the
  same gap as the units. Unit top plates and CF are joined on TopMetal1 (the plate layer); the bottom plate of each bit
  group is one Metal5 polygon. Metal5 and TopMetal1 are used only for the MIM plates and their joins; every
  connection leaves the plates through Via4 onto Metal4 under the bank and runs on Metal1-Metal4.
Shielding: the output buffer is at the east end of the rows; `osc_clk` runs on Metal2/Metal3 inside the row area to
  the east pin and never enters the track channel. The lowest channel track is vss and a second vss track lies
  between va and vb. The bank bit lines leave the arrays under the vss dummy column.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from r1_layout_lib import (Draw, RowLayout, Rppd, Cmim, pya, um, VIA)  # noqa: E402

SCH = os.path.join(HERE, '..', 'schematic', 'r1_osc.spice')
OUT_GDS = os.path.join(HERE, 'r1_osc.gds')
OUT_CDL = os.path.join(HERE, 'r1_osc_lvs.cdl')
OUT_META = os.path.join(HERE, 'r1_osc_layout_meta.json')
MOS_MODELS = ('sg13_lv_nmos', 'sg13_lv_pmos')


# =============================================================================================
# netlist of record: parse and flatten (instance path names joined by '.')
def parse(path):
    subs, cur = {}, None
    for ln in open(path):
        s = ln.strip()
        if not s or s.startswith('*'):
            continue
        t = s.split()
        if t[0].lower() == '.subckt':
            cur = t[1]
            subs[cur] = dict(ports=t[2:], lines=[])
        elif t[0].lower() == '.ends':
            cur = None
        elif cur:
            subs[cur]['lines'].append(t)
    return subs


SUBS = parse(SCH)


def flatten(sub, prefix, nmap, out):
    for t in SUBS[sub]['lines']:
        nets = [x for x in t[1:] if '=' not in x]
        par = dict(x.split('=', 1) for x in t[1:] if '=' in x)
        model = nets[-1]
        conn = [nmap.get(n, (prefix + n) if prefix else n) for n in nets[:-1]]
        conn = ['vss' if c == 'sub!' else c for c in conn]
        name = prefix + t[0]
        if model in SUBS:
            flatten(model, name + '.', dict(zip(SUBS[model]['ports'], conn)), out)
        else:
            out.append(dict(name=name, model=model, nets=conn, par=par))


PRIM = []
flatten('r1_osc', '', {p: p for p in SUBS['r1_osc']['ports']}, PRIM)
BYNAME = {p['name']: p for p in PRIM}


def um_of(v):
    return float(v.rstrip('u'))


# =============================================================================================
ly = pya.Layout()
ly.dbu = 0.001
cell = ly.create_cell('r1_osc')
D = Draw(ly, cell)
for k, v in {'MIM': (36, 0), 'Vmim': (129, 0)}.items():
    D.L[k] = ly.layer(*v)

# self-check registry (Metal3/Metal4 rectangles drawn at top level, with their nets)
REG = {'M3': [], 'M4': []}
CAPS = []        # (name, w, l, m, top net, (x, y) on Metal4, bottom net, (x, y) on Metal4) for the PEX netlist
PEXLAB = []      # (name, x, y) Metal4 labels for the unnamed bank bottom-plate nets (PEX input only)


def rbox(layer, net, x1, y1, x2, y2):
    b = D.box(layer, x1, y1, x2, y2)
    if layer in REG:
        REG[layer].append((net, min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
    return b


def via3(net, x, y, lo='s', hi='s'):
    D.square('Via3', x, y, VIA)
    rbox('M3', net, x - 0.15, y - 0.15, x + 0.15, y + 0.15)
    rbox('M4', net, x - 0.15, y - 0.15, x + 0.15, y + 0.15)


def m3v(net, x, y1, y2, w=0.24):
    rbox('M3', net, x - w / 2, min(y1, y2) - 0.15, x + w / 2, max(y1, y2) + 0.15)


def m4h(net, y, x1, x2, w=0.24):
    rbox('M4', net, min(x1, x2) - 0.15, y - w / 2, max(x1, x2) + 0.15, y + w / 2)


# =============================================================================================
# geometry constants
P = 5.9                 # MIM unit grid pitch (Metal5 gap 0.67 >= Mn.f 0.60; TopMetal1 gap 2.12 >= TM1.b 1.64)
U = 4.03                # unit MIM side (cap_cmim w = l = 4.03 um)
SEGP = 1.9              # rppd segment pitch
XR0 = 3.0               # first resistor segment x
YTOP = 52.04            # resistor body top (all groups aligned at the top)
XROW = 54.6             # NMOS row Activ lower-left x
YROW = 4.0              # NMOS row Activ bottom
TRK_P = 0.8             # Metal4 channel track pitch
LANE_P = 1.0            # lane Metal3 vertical pitch (0.6 gave 14-31 fF on the bit nodes, pex-rc-20261021-c)

# =============================================================================================
# 1. transistor rows (three RowLayout groups)
MOS = {}
for p in PRIM:
    if p['model'] in MOS_MODELS:
        d, g, s, b = p['nets']
        assert b == ('vss' if p['model'].endswith('nmos') else 'vdd'), p
        MOS[p['name']] = dict(kind='n' if p['model'].endswith('nmos') else 'p', w=um_of(p['par']['w']),
                              l=um_of(p['par']['l']), S=s, D=d, G=g, m=int(p['par'].get('m', 1)))


def comp_n(c):
    return ['%s.XMT' % c, '%s.XM1' % c, '%s.XM2' % c, '%s.XI1.XMN' % c, '%s.XI2.XMN' % c]


def comp_p(c):
    return ['%s.XM3' % c, '%s.XM4' % c, '%s.XI1.XMP' % c, '%s.XI2.XMP' % c]


LOG_N = ['XMRA', 'XEN.XMN', 'XNQ.XMN0', 'XNQ.XMN1', 'XNQ.XMN2', 'XNQB.XMN0', 'XNQB.XMN1', 'XRSTB.XMN0', 'XRSTB.XMN1',
         'XRSTA.XMN', 'XB1.XMN', 'XMRB']
LOG_P = ['XEN.XMP', 'XNQ.XMP0', 'XNQ.XMP1', 'XNQ.XMP2', 'XNQB.XMP0', 'XNQB.XMP1', 'XRSTB.XMP0', 'XRSTB.XMP1',
         'XRSTA.XMP', 'XB1.XMP']
# five compact row groups, west to east: trim switches (next to the lane), comparator A + bias, latch logic with the
# reset switches MRA/MRB, comparator B, output inverter XB2. The loop nets ca, cb, rsta, rstb stay inside one group or
# between neighbours; only qn_b (output path, not in the loop) crosses comparator B.
# History: one 89 um row put the PMOS ~50 um east of their NMOS partners (25 fF per internal node, +2.6 ns loop
# delay, run post-c22-tt-20261021-a); three and four groups: post-probe-20261021-c / -d.
GROUP_DEF = [('SWT', sum([['XCA.XMS%d' % k, 'XCB.XMS%d' % k] for k in range(5)], []), []),
             ('CMPA', ['XMBD'] + comp_n('XCMPA'), comp_p('XCMPA')),
             ('LOG', LOG_N, LOG_P),
             ('CMPB', comp_n('XCMPB'), comp_p('XCMPB')),
             ('BUF', ['XB2.XMN'], ['XB2.XMP'])]
ALLN = sum([g[1] + g[2] for g in GROUP_DEF], [])
assert sorted(ALLN) == sorted(MOS), (set(MOS) ^ set(ALLN))
BITS_A = ['XCA.b%d' % k for k in range(5)]
BITS_B = ['XCB.b%d' % k for k in range(5)]
EXTERNAL = set(['en', 'trim0', 'trim1', 'trim2', 'trim3', 'trim4', 'va', 'vb', 'vth', 'vbn', 'osc_clk'] + BITS_A + BITS_B)


def gnets(names):
    return set(n for nm in names for n in (MOS[nm]['S'], MOS[nm]['D'], MOS[nm]['G'])) - {'vss', 'vdd'}


GN = {g[0]: gnets(g[1] + g[2]) for g in GROUP_DEF}

# lane (Metal3 verticals from the banks down to the channel): x positions known before the rows are built
LANE_NETS = ['vss', 'va'] + BITS_A + ['vb'] + BITS_B
LANE_X0 = 53.3
LANE_X = {n: LANE_X0 + LANE_P * i for i, n in enumerate(LANE_NETS)}
ROWS = {}
INTER = []
ox = XROW
for gname, nlist, plist in GROUP_DEF:
    devs = []
    for nm in nlist + plist:
        d = MOS[nm]
        for k in range(d['m']):
            devs.append(dict(name=nm + ('_%d' % k if d['m'] > 1 else ''), kind=d['kind'], w=d['w'], l=d['l'],
                             S=d['S'], D=d['D'], G=d['G']))
    ports = sorted(n for n in GN[gname] if n in EXTERNAL or any(n in GN[o] for o in GN if o != gname))
    for n in ports:
        if n not in EXTERNAL and n not in INTER:
            INTER.append(n)
    r = RowLayout(D, ox, YROW, devs, ports=ports, avoid_x=list(LANE_X.values()))
    r.build()
    ROWS[gname] = r
    print('group', gname, 'extent', [round(v, 2) for v in r.extent], 'tracks', len(set(r.track_y.values())), 'ports', ports)
    ox = r.extent[2] + 1.0 + 1.5
BUF = ROWS['BUF']
# the osc_clk Metal3 run to the east pin is checked against every Metal3 port vertical by the self-check (section 7)
for r in ROWS.values():
    for net, (x, y) in r.port_pos.items():
        REG['M3'].append((net, x - 0.12, y - 0.15, x + 0.12, y + 0.15))
ROW_EXT = (min(r.extent[0] for r in ROWS.values()), min(r.extent[1] for r in ROWS.values()),
           max(r.extent[2] for r in ROWS.values()), max(r.extent[3] for r in ROWS.values()))
DEVS = [d for r in ROWS.values() for d in r.devices]
print('rows extent', ROW_EXT, 'inter-group nets', INTER)

# =============================================================================================
# 2. channel tracks (Metal4 horizontal)
TRACKS = sorted(INTER) + ['vss'] + BITS_A + BITS_B + ['en', 'trim0', 'trim1', 'trim2', 'trim3', 'trim4'] + \
         ['vbn', 'vss#2', 'va', 'vss#1', 'vb', 'vss#3', 'vth', 'vdd']
SHIELDS = ['vss#1', 'vss#2', 'vss#3']   # grounded tracks between vbn | va | vb | vth (pex-rc-20261021-g: vb-vth 8.2 fF,
#                                        va-vbn 5.5 fF without them)
TY0 = ROW_EXT[3] + 1.5
TY = {k: TY0 + TRK_P * i for i, k in enumerate(TRACKS)}
TNET = {k: k.split('#')[0] for k in TRACKS}
CONN = {k: [] for k in TRACKS}   # track key -> list of (x, y_from): Metal3 vertical from y_from to the track + Via3


def connect(key, x, y_from):
    CONN[key].append((x, y_from))


for r in ROWS.values():
    for net, (x, y) in r.port_pos.items():
        if net != 'osc_clk':
            connect(net, x, y)

# =============================================================================================
# 3. resistor block
GROUPS = [('D', 40.0, None), ('RBIAS', 40.0, 'vbn'), ('RBIAS', 40.0, 'vdd'), ('D', 48.04, None)] + \
         [('RT', 48.04 if j % 8 != 7 else 48.02, None) for j in range(16)] + \
         [('D', 48.04, None)] + \
         [('RA', 24.15, 'va'), ('RA', 24.15, 'vdd'), ('RB', 24.15, 'vdd'), ('RB', 24.15, 'vb')] + [('D', 24.15, None)]
SEG = []
for i, (kind, ln, _) in enumerate(GROUPS):
    x = XR0 + SEGP * i
    y0 = YTOP - ln
    if kind == 'D':
        D.box('GatPoly', x, y0 - 0.43, x + 1.0, YTOP + 0.43)
        D.box('pSD', x - 0.18, y0 - 0.61, x + 1.18, YTOP + 0.61)
        SEG.append(None)
    else:
        SEG.append(Rppd(D, 1.0, ln, x, y0))
RES_RIGHT = XR0 + SEGP * (len(GROUPS) - 1) + 1.0
assert abs(sum(g[1] for g in GROUPS[4:12]) - 384.3) < 1e-6 and abs(sum(g[1] for g in GROUPS[12:20]) - 384.3) < 1e-6


def hc(i, end):
    h = SEG[i].head_top if end == 't' else SEG[i].head_bot
    return (h[0] + h[2]) / 2, (h[1] + h[3]) / 2


def join(i, j, end):
    a = SEG[i].head_top if end == 't' else SEG[i].head_bot
    b = SEG[j].head_top if end == 't' else SEG[j].head_bot
    D.box('M1', a[0], min(a[1], b[1]), b[2], max(a[3], b[3]))


join(1, 2, 'b')          # RBIAS
for j in range(15):      # RT chain: links bottom (j even) / top (j odd); vdd top 4, vth top 11/12, vss top 19
    join(4 + j, 5 + j, 'b' if j % 2 == 0 else 't')
join(21, 22, 'b')        # RA
join(23, 24, 'b')        # RB
join(22, 23, 't')        # RA/RB vdd heads
HEADS = [(1, 'vbn'), (2, 'vdd'), (4, 'vdd'), (11, 'vth'), (19, 'vss'), (21, 'va'), (22, 'vdd'), (24, 'vb')]
assert [GROUPS[i][0] for i in (1, 2, 21, 24)] == ['RBIAS', 'RBIAS', 'RA', 'RB']
HEAD_X = []
for i, net in HEADS:
    x, y = hc(i, 't')
    D.vpad('Via1', x, y, hi='v')
    D.box('M2', x - 0.12, y - 0.30, x + 0.12, y + 0.30)
    D.square('Via2', x, y, VIA)
    rbox('M3', net, x - 0.12, y - 0.15, x + 0.12, y + 0.15)
    connect(net, x, y)
    HEAD_X.append(x)

# =============================================================================================
# 4. MIM: CTH above the resistor block, banks A and B east of the lane
Y_CAP0 = TY[TRACKS[-1]] + 2.5           # lowest Metal5 edge above the channel


def pick_x(cands, avoid, d=0.7):
    for c in cands:
        if all(abs(c - a) >= d for a in avoid):
            return c
    raise SystemExit('no free x')


# CTH (26 x 26): vth top plate tab down to an island; Metal5 (vss) Via4 + Via3 at the lower-left margin
CTH_X, CTH_Y = 6.0, YTOP + 5.0
cth = Cmim(D, 26.0, 26.0, CTH_X, CTH_Y)
xi = pick_x([CTH_X + 13.0 + 0.1 * k for k in range(60)], HEAD_X, 0.9)
yi = CTH_Y - 2.4
D.box('TM1', xi - 0.82, yi - 0.82, xi + 0.82, CTH_Y + 0.6)
D.via('TopVia1', xi, yi)
D.via('Via4', xi, yi, padlo=0.66, padhi=0.66)
via3('vth', xi, yi)
connect('vth', xi, yi)
xs_ = pick_x([CTH_X + 0.6 + 0.1 * k for k in range(80)], HEAD_X + [xi], 0.9)
for dx in (0.0, 0.42):
    D.square('Via4', xs_ + dx, CTH_Y - 0.3, VIA)
rbox('M4', 'vss', xs_ - 0.15, CTH_Y - 0.45, xs_ + 0.57, CTH_Y - 0.15)
via3('vss', xs_, CTH_Y - 0.3)
connect('vss', xs_, CTH_Y - 0.3)
D.label('M4txt', xi, yi, 'vth')
CAPS.append(('CTH', 26.0, 26.0, 1, 'vth', (xi, yi), 'vss', (xs_, CTH_Y - 0.3)))

# banks
LANE_TOP = {}
BANK_INFO = {}


def bank(tag, bx, by, top, bits):
    """unit array + CF; returns the Metal4 line endpoints (net -> y) for the lane"""
    g = {}
    for c in range(9):
        for r in range(6):
            if c == 0 or r in (0, 5):
                g[(c, r)] = 'D'
            elif r in (3, 4):
                g[(c, r)] = 4
            elif r == 2:
                g[(c, r)] = 3
            else:
                g[(c, r)] = 0 if c == 1 else (1 if c <= 3 else (2 if c <= 7 else 'VA'))
    cnt = {}
    for v in g.values():
        cnt[v] = cnt.get(v, 0) + 1
    assert cnt == {'D': 22, 4: 16, 3: 8, 2: 4, 1: 2, 0: 1, 'VA': 1}, cnt
    X = lambda c: bx + P * c
    Y = lambda r: by + P * r
    for (c, r), k in g.items():
        if k != 'VA':
            Cmim(D, U, U, X(c), Y(r))
    cfx, cfy = X(9), by + 16.765 - 14.275
    Cmim(D, 28.55, 28.55, cfx, cfy)
    # Metal5: merge neighbours of the same group (gap and 4-corner fills); dummies merge with the CF plate
    for (c, r), k in g.items():
        if k == 'VA':
            continue
        if g.get((c + 1, r)) == k:
            D.box('M5', X(c) + U + 0.6, Y(r) - 0.6, X(c + 1) - 0.6, Y(r) + U + 0.6)
        if g.get((c, r + 1)) == k:
            D.box('M5', X(c) - 0.6, Y(r) + U + 0.6, X(c) + U + 0.6, Y(r + 1) - 0.6)
        if g.get((c + 1, r)) == k and g.get((c, r + 1)) == k and g.get((c + 1, r + 1)) == k:
            D.box('M5', X(c) + U, Y(r) + U, X(c + 1), Y(r + 1))
    for r in (0, 5):
        D.box('M5', X(8) + U + 0.6, Y(r) - 0.6, cfx - 0.6, Y(r) + U + 0.6)
    # TopMetal1: active network (units + VA slot pad + CF), dummy network
    act = [cr for cr, k in g.items() if k != 'D']
    D.box('TM1', X(8) + 0.125, Y(1) + 0.125, X(8) + U - 0.125, Y(1) + U - 0.125)   # VA slot pad (no MIM)

    def hstrap(c, r, x2=None):
        yc = Y(r) + U / 2
        D.box('TM1', X(c) + U - 0.2, yc - 0.82, (x2 if x2 is not None else X(c + 1)) + 0.2, yc + 0.82)

    def vstrap(c, r):
        xc = X(c) + U / 2
        D.box('TM1', xc - 0.82, Y(r) + U - 0.2, xc + 0.82, Y(r + 1) + 0.2)
    for (c, r) in act:
        if (c + 1, r) in act:
            hstrap(c, r)
    for c in (1, 8):
        for r in range(1, 4):
            vstrap(c, r)
    for r in range(1, 5):
        hstrap(8, r, x2=cfx + 0.6)
    for c in range(8):
        hstrap(c, 0)
        hstrap(c, 5)
    for r in range(5):
        vstrap(0, r)
    # dummy plates to vss: TopVia1 in the dummy column gap (0,2)-(0,3)
    xd, yd = X(0) + U / 2, Y(2) + U + (P - U) / 2
    D.square('TopVia1', xd, yd, 0.42)
    # VA slot: Metal5 island, 3 x 3 TopVia1, Via4 onto the va line
    D.box('M5', X(8), Y(1), X(8) + U, Y(1) + U)
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            D.square('TopVia1', X(8) + U / 2 + 0.84 * i, Y(1) + U / 2 + 0.84 * j, 0.42)
    # Metal4 lines to the lane (Via4 in the bottom Metal5 margin of the group's west unit, stub up to the line)
    lines = {}
    spec = [(bits[0], 1, 1, Y(1) + 0.6), (bits[1], 2, 1, Y(1) + 1.4), (bits[2], 4, 1, Y(1) + 2.2),
            (bits[3], 1, 2, Y(2) - 0.3), (bits[4], 1, 3, Y(3) - 0.3)]
    for net, c, r, yl in spec:
        xv = X(c) + U / 2
        yv = Y(r) - 0.3
        D.square('Via4', xv, yv, VIA)
        D.square('Via4', xv + 0.42, yv, VIA)
        rbox('M4', net, xv - 0.15, min(yv, yl) - 0.15, xv + 0.57, max(yv, yl) + 0.15)
        m4h(net, yl, LANE_X[net], xv)
        lines[net] = yl
        CAPS.append(('%s.CT%d' % (tag, bits.index(net)), 4.03, 4.03, 2 ** bits.index(net), top, None, net, (xv, yv)))
        PEXLAB.append(('b%s%d' % (tag.lower(), bits.index(net)), LANE_X[net], yl))
    yva = Y(1) + 3.0
    for i in (-1, 0, 1):
        D.square('Via4', X(8) + U / 2 + 0.42 * i, yva, VIA)
    m4h(top, yva, LANE_X[top], X(8) + U / 2 + 0.6)
    lines[top] = yva
    # dummy / CF Metal5 (vss): Via4 pair in the dummy column gap (0,1)-(0,2)
    yv = Y(1) + U + (P - U) / 2
    for dx in (-0.21, 0.21):
        D.square('Via4', X(0) + U / 2 + dx, yv, VIA)
    rbox('M4', 'vss', X(0) + U / 2 - 0.4, yv - 0.15, X(0) + U / 2 + 0.4, yv + 0.15)
    m4h('vss', yv, LANE_X['vss'], X(0) + U / 2)
    CAPS.append(('%s.CF' % tag, 28.55, 28.55, 1, top, None, 'vss', (X(0) + U / 2, yv)))
    for i, c in enumerate(CAPS):
        if c[0].startswith(tag + '.') and c[5] is None:
            CAPS[i] = c[:5] + ((X(8) + U / 2, yva),) + c[6:]
    BANK_INFO[tag] = dict(bx=bx, by=by, cf=(cfx, cfy), dummies=cnt['D'], units=31, vss_line=yv)
    return lines, yv


BX = LANE_X[LANE_NETS[-1]] + 1.5 + 0.6
BY_A = Y_CAP0 + 0.6
BY_B = BY_A + 6 * P
lines_a, vssa = bank('A', BX, BY_A, 'va', BITS_A)
lines_b, vssb = bank('B', BX, BY_B, 'vb', BITS_B)
for lines in (lines_a, lines_b):
    for net, yl in lines.items():
        via3(net, LANE_X[net], yl)
        connect(net, LANE_X[net], yl)
for yv in (vssa, vssb):
    via3('vss', LANE_X['vss'], yv)
connect('vss', LANE_X['vss'], max(vssa, vssb))
D.label('M4txt', LANE_X['va'] + 0.6 * 0, lines_a['va'], 'va')
D.label('M4txt', LANE_X['vb'], lines_b['vb'], 'vb')
CAP_RIGHT = BX + 9 * P + 28.55 + 0.6

# =============================================================================================
# 5. macro box, bars, pins, ring
W = round(max(CAP_RIGHT, ROW_EXT[2]) + 3.4, 1)
H = round(BY_B + 5 * P + U + 0.6 + 3.0, 1)
D.box('prBoundary', 0, 0, W, H)
VSS_Y0, VSS_Y1 = 0.0, 2.0
VDD_Y0, VDD_Y1 = H - 2.0, H
for (y0, y1, name) in ((VSS_Y0, VSS_Y1, 'vss'), (VDD_Y0, VDD_Y1, 'vdd')):
    rbox('M3', name, 0, y0, W, y1)
    D.box('M3pin', 0, y0, W, y1)
    D.label('M3txt', W / 2, (y0 + y1) / 2, name)
ringc, _ = D.guard_ring(1.0, 1.0, W - 1.0, H - 1.0, 0.30, kind='p')
RING_VIA_X = (6.0, 30.0, W - 6.0)
for x in RING_VIA_X:
    D.box('M2', x - 0.15, ringc[1] - 0.30, x + 0.15, ringc[1] + 0.30)
    D.vpad('Via2', x, ringc[1], lo='s', hi='v')
    D.via('Via1', x, ringc[1])
# west pins
for net in ('en', 'trim0', 'trim1', 'trim2', 'trim3', 'trim4'):
    y = TY[net]
    rbox('M3', net, 0.0, y - 0.15, 1.5, y + 0.15)
    D.box('M3pin', 0.0, y - 0.15, 1.5, y + 0.15)
    D.label('M3txt', 0.75, y, net)
    connect(net, 1.0, y)
# vss drops to the VSS bar (west edge and between resistors and rows), both vss tracks
XD1 = 2.3
connect('vss', XD1, VSS_Y1 - 0.2)
for k in SHIELDS:
    connect(k, XD1, VSS_Y1 - 0.2)
connect('vss', LANE_X['vss'], VSS_Y1 - 0.2)
for k in SHIELDS:
    connect(k, LANE_X['vss'], TY['vss'])
# row groups: vss rail -> VSS bar; vdd rail -> Metal2 riser east of the group -> vdd track
for r in ROWS.values():
    cand = [r.extent[0] + 1.6 + 0.1 * k for k in range(int((r.extent[2] - r.extent[0] - 2.6) / 0.1))]
    cand = [x for x in cand if all(abs(x - xr) > 1.2 for xr in RING_VIA_X)]
    xs_v = [cand[0]] + ([c for c in cand if c >= (r.extent[0] + r.extent[2]) / 2][:1] if r.extent[2] - r.extent[0] > 8.0 else [])
    assert cand, 'no vss rail via position'
    for x in xs_v:
        D.vpad('Via1', x, r.VSS_Y, hi='v')
        D.vwire('M2', x, r.VSS_Y, 1.0)
        D.vpad('Via2', x, 1.0, lo='v', hi='h')
    xv = r.extent[2] + 0.5
    D.hwire('M1', r.extent[2] - 1.0, xv, r.VDD_Y, w=0.30)
    D.vpad('Via1', xv, r.VDD_Y, hi='v')
    D.vwire('M2', xv, r.VDD_Y, TY['vdd'])
    D.vpad('Via2', xv, TY['vdd'], lo='v', hi='s')
    rbox('M3', 'vdd', xv - 0.2, TY['vdd'] - 0.2, xv + 0.2, TY['vdd'] + 0.2)
    connect('vdd', xv, TY['vdd'])
XE = W - 2.3
connect('vdd', XE, VDD_Y0 + 0.2)
# osc_clk: Metal3 east from the row port to the east pin (stays below the channel)
xo, yo = BUF.port_pos['osc_clk']
yo2 = yo - 1.5          # jog down: the qn_b port vertical of the BUF group starts just above the osc_clk port
rbox('M3', 'osc_clk', xo - 0.12, yo2 - 0.15, xo + 0.12, yo + 0.15)
rbox('M3', 'osc_clk', xo - 0.12, yo2 - 0.15, W, yo2 + 0.15)
D.box('M3pin', W - 1.5, yo2 - 0.15, W, yo2 + 0.15)
D.label('M3txt', W - 0.75, yo2, 'osc_clk')
# vth antenna diode (dpantenna) on the vth port vertical above the PMOS row (G1 revision 5 placement)
xd, yport = ROWS['CMPA'].port_pos['vth']
yd = ROWS['CMPA'].extent[3] + 0.15 + 0.39
D.pcell('dpantenna', {'w': '0.78u', 'l': '0.78u'}, pya.Trans(pya.Point(um(xd - 0.39), um(yd - 0.39))))
D.box('M1', xd - 0.31, yd - 0.31, xd + 0.31, yd + 0.31)
D.via('Via1', xd, yd)
D.box('M2', xd - 0.20, yd - 0.36, xd + 0.20, yd + 0.36)
D.via('Via2', xd, yd)
assert yport < yd < TY['vth']
# internal net labels (names for the post-layout node references)
for net in ('ca', 'cb', 'q', 'qb', 'rsta', 'rstb', 'en_n', 'qn_b'):
    r = [r for r in ROWS.values() if net in r.stubs][0]
    xs = [s[0] for s in r.stubs[net]]
    D.label('M2txt', (min(xs) + max(xs)) / 2, r.track_y[net], net)

# shield tracks (vss#1..3) also joined to the vss track east of the va/vb connections
xs_va = [p[0] for k in ('va', 'vb') for p in CONN[k]]
ch_x = [p[0] for k in TRACKS for p in CONN[k] if abs(p[1] - TY[k]) > 0.01]
xsh = pick_x([max(xs_va) + 0.8 + 0.1 * k for k in range(200)], ch_x, 0.8)
for k in SHIELDS:
    connect(k, xsh, TY['vss'])
connect('vss', xsh, TY['vss'])

# =============================================================================================
# 6. draw the channel: tracks, Metal3 verticals, Via3
D.label('M4txt', min(p[0] for p in CONN['vbn']), TY['vbn'], 'vbn')
for k in TRACKS:
    pts = CONN[k]
    assert pts, k
    net = TNET[k]
    ty = TY[k]
    xs = [p[0] for p in pts]
    m4h(net, ty, min(xs), max(xs), w=0.20 if net in ('en', 'trim0', 'trim1', 'trim2', 'trim3', 'trim4') else 0.24)
    for x, y in pts:
        if abs(y - ty) > 0.01:
            m3v(net, x, y, ty)
        via3(net, x, ty)

# =============================================================================================
# 7. self-checks: Metal3 / Metal4 spacing between different nets (drawn at top level)


def overlap_gap(a, b):
    dx = max(a[1] - b[3], b[1] - a[3], 0.0)
    dy = max(a[2] - b[4], b[2] - a[4], 0.0)
    if dx > 0 and dy > 0:
        return (dx * dx + dy * dy) ** 0.5
    return max(dx, dy)


ERR = []
for layer, lst in REG.items():
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            a, b = lst[i], lst[j]
            if a[0] == b[0]:
                continue
            gap = overlap_gap(a, b)
            if gap < 0.22:
                ERR.append((layer, a, b, round(gap, 3)))
for e in ERR[:40]:
    print('SELFCHECK', e)
mim = pya.Region(cell.begin_shapes_rec(D.L['MIM'])).merged()
N_MIM = mim.count()
assert N_MIM == 2 * (31 + 22 + 1) + 1, N_MIM
print('selfcheck errors', len(ERR), 'MIM plates', N_MIM)

# =============================================================================================
# 8. output: GDS, LVS CDL, meta
D.clean_pcell_markers()
for c in list(ly.each_cell()):             # as write_gds() of the library, but without GDS timestamps (reproducible sha256)
    if c.is_proxy() and c.parent_cells() == 0:
        ly.delete_cell(c.cell_index())
opt = pya.SaveLayoutOptions()
opt.gds2_write_timestamps = False
ly.write(OUT_GDS, opt)


def cdl():
    out = ['* r1_osc LVS reference netlist, written by layout/r1_osc_layout.py from schematic/r1_osc.spice (netlist of',
           '* record). Format conversion only (X-calls of primitives -> M/R/C/D, sub! -> vss, mm_ok and ng dropped). The %d dummy'
           % (2 * BANK_INFO['A']['dummies']),
           '* cap_cmim units of the layout (both plates on vss) are not listed: the PDK LVS deck purges two-terminal devices',
           '* whose terminals are on one net (run layout-lvs-20261021-a). Their count is checked in r1_osc_layout_meta.json.']
    for name, s in SUBS.items():
        out.append('.subckt %s %s' % (name, ' '.join(s['ports'])))
        for t in s['lines']:
            nets = [x for x in t[1:] if '=' not in x]
            par = dict(x.split('=', 1) for x in t[1:] if '=' in x)
            model, conn = nets[-1], ['vss' if n == 'sub!' else n for n in nets[:-1]]
            inst = t[0][1:]
            if model in MOS_MODELS:
                out.append('M%s %s %s w=%s l=%s m=%s' % (inst, ' '.join(conn), model, par['w'], par['l'], par.get('m', '1')))
            elif model == 'rppd':
                out.append('R%s %s rppd w=%s l=%s b=%s m=%s' % (inst, ' '.join(conn), par['w'], par['l'], par.get('b', '0'),
                                                               par.get('m', '1')))
            elif model == 'cap_cmim':
                out.append('C%s %s cap_cmim w=%s l=%s m=%s' % (inst, ' '.join(conn), par['w'], par['l'], par.get('m', '1')))
            elif model == 'dpantenna':
                out.append('D%s %s dpantenna w=%s l=%s' % (inst, ' '.join(conn), par['w'], par['l']))
            elif model in SUBS:
                out.append('%s %s %s' % (t[0], ' '.join(conn), model))
            else:
                raise SystemExit('unknown model ' + model)
        out.append('.ends')
    return '\n'.join(out) + '\n'


open(OUT_CDL, 'w').write(cdl())
meta = dict(W=W, H=H, area_mm2=W * H * 1e-6, tracks=TRACKS, track_y={k: round(v, 3) for k, v in TY.items()},
            row_groups={g: dict(extent=r.extent, tracks=len(set(r.track_y.values()))) for g, r in ROWS.items()}, banks=BANK_INFO,
            caps=CAPS, pex_labels=PEXLAB, lane_x=LANE_X, mim_plates=N_MIM, dummy_units=2 * BANK_INFO['A']['dummies'], resistor_block=[XR0, YTOP, RES_RIGHT], selfcheck_errors=len(ERR), n_mos=len(DEVS))
json.dump(meta, open(OUT_META, 'w'), indent=1, default=str)
print('wrote', OUT_GDS, 'W x H = %.1f x %.1f um = %.5f mm2' % (W, H, W * H * 1e-6))
if ERR:
    sys.exit(2)
