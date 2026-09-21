#!/usr/bin/env python3
"""G1_OSC layout generator (KLayout 0.30.9 + SG13G2 PCells, run inside the pinned container):

  klayout -b -r gen_osc_layout.py -rd out=<gds>

One cell `g1_osc` (PCells flattened):
  - transistor row block (RowLayout: NMOS row, Metal2 track channel, PMOS row) with the two
    5-T comparators, the bias diode, the trim/reset switches and the latch logic;
  - resistor block to the left: rppd 1 um segments at 1.36 um pitch, RA/RB as 2 x 58.5 (ABBA
    interleaved), RT1/RT2 as 6 x 64.05 each, RBIAS as 2 x 67.15, a dummy segment on each side;
  - capacitors above in three columns (cmim PCells), top plates tabbed to the left, bottom
    plates to the right, Metal3 verticals to a Metal4 track channel (y 17.5..26.5) that also
    carries the pins to the west/east edges;
  - pins on Metal3: en, trim[3:0] (west), osc_clk (east), VDD bar (north), VSS bar (south);
    p+ guard ring (VSS) around the block.
The library g1_layout_lib.py is a copy of blocks/g1_trip/layout/g1_layout_lib.py.
"""
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from g1_layout_lib import *  # noqa: F401,F403,E402

SEG_PITCH = 1.85          # separate pSD/SalBlock/ExtBlock per segment (segment lengths differ)


def devices():
    """transistor list of g1_osc (nets as in sim/netlist/g1_osc.spice, flattened)"""
    d = []

    def n(name, w, l, S, D, G):
        d.append(dict(name=name, kind='n', w=w, l=l, S=S, D=D, G=G))

    def p(name, w, l, S, D, G):
        d.append(dict(name=name, kind='p', w=w, l=l, S=S, D=D, G=G))
    # comparator A and B (g1_osc_cmp): MT 2/0.5, M1/M2 4/0.3, M3/M4 pmos 2/0.3, two inverters
    for k, vin in (('a', 'va'), ('b', 'vb')):
        n('MT' + k, 2.0, 0.5, 'vss', 'tail' + k, 'vbn')
        n('M1' + k, 4.0, 0.3, 'tail' + k, 'd1' + k, vin)
        n('M2' + k, 4.0, 0.3, 'tail' + k, 'o1' + k, 'vth')
        p('M3' + k, 2.0, 0.3, 'vdd', 'd1' + k, 'd1' + k)
        p('M4' + k, 2.0, 0.3, 'vdd', 'o1' + k, 'd1' + k)
        n('I1n' + k, 0.5, 0.13, 'vss', 'o2' + k, 'o1' + k)
        p('I1p' + k, 1.0, 0.13, 'vdd', 'o2' + k, 'o1' + k)
        n('I2n' + k, 0.5, 0.13, 'vss', 'c' + k, 'o2' + k)
        p('I2p' + k, 1.0, 0.13, 'vdd', 'c' + k, 'o2' + k)
    n('MBD', 2.0, 0.5, 'vss', 'vbn', 'vbn')
    # trim switches and reset switches
    for i in range(4):
        n('MS%d' % i, 4.0, 0.13, 'vss', 'b%d' % i, 'trim%d' % i)
        n('MSB%d' % i, 4.0, 0.13, 'vss', 'bb%d' % i, 'trim%d' % i)
    n('MRA', 4.0, 0.13, 'vss', 'va', 'rsta')
    n('MRB', 4.0, 0.13, 'vss', 'vb', 'rstb')
    # logic: XEN inv, NOR3(ca, en_n, qb)->q, NOR2(cb, q)->qb, NAND2(qb, en)->rstb, XRSTA, XB1, XB2
    n('ENn', 0.5, 0.13, 'vss', 'en_n', 'en')
    p('ENp', 1.0, 0.13, 'vdd', 'en_n', 'en')
    for i, g in enumerate(('ca', 'en_n', 'qb')):
        n('NQn%d' % i, 0.5, 0.13, 'vss', 'q', g)
    p('NQp0', 3.0, 0.13, 'vdd', 'p0', 'ca')
    p('NQp1', 3.0, 0.13, 'p0', 'p1', 'en_n')
    p('NQp2', 3.0, 0.13, 'p1', 'q', 'qb')
    for i, g in enumerate(('cb', 'q')):
        n('NQBn%d' % i, 0.5, 0.13, 'vss', 'qb', g)
    p('NQBp0', 2.0, 0.13, 'vdd', 'p0b', 'cb')
    p('NQBp1', 2.0, 0.13, 'p0b', 'qb', 'q')
    n('RSTBn0', 1.0, 0.13, 'n0', 'rstb', 'qb')
    n('RSTBn1', 1.0, 0.13, 'vss', 'n0', 'en')
    p('RSTBp0', 1.0, 0.13, 'vdd', 'rstb', 'qb')
    p('RSTBp1', 1.0, 0.13, 'vdd', 'rstb', 'en')
    for name, a, y in (('RSTA', 'q', 'rsta'), ('B1', 'q', 'qn_b'), ('B2', 'qn_b', 'osc_clk')):
        n(name + 'n', 0.5, 0.13, 'vss', y, a)
        p(name + 'p', 1.0, 0.13, 'vdd', y, a)
    return d


def dummy_seg(D, x, y, L):
    """rppd-like 1 x L dummy (no PolyRes: not a device)"""
    D.box('GatPoly', x, y - 0.43, x + 1.0, y + L + 0.43)
    D.box('pSD', x - 0.18, y - 0.61, x + 1.18, y + L + 0.61)
    D.box('SalBlock', x - 0.20, y, x + 1.20, y + L)
    D.box('ExtBlock', x - 0.18, y - 0.61, x + 1.18, y)
    D.box('ExtBlock', x - 0.20, y, x + 1.20, y + L)
    D.box('ExtBlock', x - 0.18, y + L, x + 1.18, y + L + 0.61)
    D.box('Cont', x + 0.07, y - 0.36, x + 0.93, y - 0.20)
    D.box('Cont', x + 0.07, y + L + 0.20, x + 0.93, y + L + 0.36)
    D.box('M1', x + 0.02, y - 0.43, x + 0.98, y - 0.13)
    D.box('M1', x + 0.02, y + L + 0.13, x + 0.98, y + L + 0.43)


def build(ly, out='g1_osc.gds'):
    cell = ly.create_cell('g1_osc')
    D = Draw(ly, cell)
    # Metal4 track order (1.0 um pitch): the timing nodes va and vb between static nets
    NETS = ['en', 'b0', 'va', 'trim0', 'b1', 'vb', 'trim1', 'vth', 'trim2', 'vbn', 'trim3',
            'osc_clk', 'b2', 'b3', 'bb0', 'bb1', 'bb2', 'bb3', 'vss']
    # ---------------- transistor row block
    ports = [n for n in NETS if n != 'vss']
    # x positions of the capacitor pad verticals (see the cap placement below): the row block
    # port verticals must not coincide with them
    CAP_X = [2.0 - 2.8, 41.5 - 2.8, 82.5 - 2.8, 82.5 - 3.8, 82.5 - 4.8,
             2.0 + 31.65 + 1.8, 2.0 + 31.65 + 2.8, 2.0 + 31.65 + 3.8,
             41.5 + 31.65 + 1.8, 41.5 + 31.65 + 2.8, 41.5 + 31.65 + 3.8]
    row = RowLayout(D, 0.0, 2.0, devices(), ports=ports, avoid_x=CAP_X)
    row.build()
    print('osc row block extent', row.extent, 'tracks', len(set(row.track_y.values())))
    TY0 = row.extent[3] + 1.5
    TY = {net: TY0 + 1.0 * i for i, net in enumerate(NETS)}      # Metal4 track y
    # ---------------- resistor block (x < 0): segments at 1.36 pitch, Activ-less rppd
    XR0 = -42.0
    YR = 2.0
    segs = {}
    order = [('dum', 0), ('RA', 1), ('RB', 1), ('RB', 2), ('RA', 2)] + [('RT1', k) for k in range(1, 7)] + \
            [('RT2', k) for k in range(1, 7)] + [('RBIAS', 1), ('RBIAS', 2), ('dum', 1)]
    L = {'RA': 58.5, 'RB': 58.5, 'RT1': 64.05, 'RT2': 64.05, 'RBIAS': 67.15, 'dum': 64.05}
    for i, (nm, k) in enumerate(order):
        x = XR0 + i * SEG_PITCH
        if nm == 'dum':
            dummy_seg(D, x, YR, L[nm])
        else:
            segs[(nm, k)] = Rppd(D, 1.0, L[nm], x, YR)

    def top(nm, k):
        h = segs[(nm, k)].head_top
        return ((h[0] + h[2]) / 2, (h[1] + h[3]) / 2)

    def bot(nm, k):
        h = segs[(nm, k)].head_bot
        return ((h[0] + h[2]) / 2, (h[1] + h[3]) / 2)

    def m1_join(a, b, head):
        ha = segs[a].head_top if head == 'top' else segs[a].head_bot
        hb = segs[b].head_top if head == 'top' else segs[b].head_bot
        D.box('M1', min(ha[0], hb[0]), ha[1], max(ha[2], hb[2]), ha[3])
    # RA: RA1 top = vdd, RA1 bottom -- RA2 bottom on Metal2 (across RB), RA2 top = va
    for a, b in ((('RA', 1), ('RA', 2)),):
        pa, pb = bot(*a), bot(*b)
        D.vpad('Via1', pa[0], pa[1], hi='h')
        D.vpad('Via1', pb[0], pb[1], hi='h')
        D.hwire('M2', pa[0], pb[0], pa[1])
    m1_join(('RB', 1), ('RB', 2), 'bot')                      # RB1 top = vdd, RB2 top = vb
    chain = [('RT1', k) for k in range(1, 7)] + [('RT2', k) for k in range(1, 7)]
    for i in range(len(chain) - 1):
        m1_join(chain[i], chain[i + 1], 'bot' if i % 2 == 0 else 'top')   # seg1 top = vdd
    m1_join(('RBIAS', 1), ('RBIAS', 2), 'bot')                # RBIAS1 top = vdd, RBIAS2 top = vbn
    # with 12 segments: joints bottom,top,...: seg6-seg7 joint is index 5 -> 'top' => vth is the
    # top of seg6/seg7 (joined); seg12 top = vss
    vdd_heads = [top('RA', 1), top('RB', 1), top('RT1', 1), top('RBIAS', 1)]
    va_head, vb_head = top('RA', 2), top('RB', 2)
    vth_head = top('RT1', 6)
    vss_head = top('RT2', 6)
    vbn_head = top('RBIAS', 2)
    # ---------------- capacitors: three columns
    caps = {}
    # trim capacitors at the bottom of each column (short bottom-plate wires to the switches in the
    # row block: the off-state series path of a trim capacitor puts its bottom-plate parasitic on va/vb)
    col = [('CT2_A', 16.33, 'va', 'b2'), ('CT3_A', 23.09, 'va', 'b3'), ('CF_A', 31.65, 'va', 'vss')]
    col2 = [('CT2_B', 16.33, 'vb', 'bb2'), ('CT3_B', 23.09, 'vb', 'bb3'), ('CF_B', 31.65, 'vb', 'vss')]
    col3 = [('CT0_A', 8.16, 'va', 'b0'), ('CT1_A', 11.55, 'va', 'b1'), ('CT0_B', 8.16, 'vb', 'bb0'),
            ('CT1_B', 11.55, 'vb', 'bb1'), ('CTH', 26.0, 'vth', 'vss')]
    YC0 = TY0 + 1.0 * len(NETS) + 3.5
    top_pads, bot_pads = [], []
    for cx, lst, tl in ((2.0, col, {'va': 2.2, 'vb': 2.2, 'vth': 2.2}),
                        (41.5, col2, {'vb': 2.2}),
                        (82.5, col3, {'vb': 2.2, 'va': 3.2, 'vth': 4.2})):
        y = YC0
        bl = 1.2
        colw = max(w for _, w, _, _ in lst)
        for name, w, tnet, bnet in lst:
            c = Cmim(D, w, w, cx, y)
            x1, y1, x2, y2 = c.mim
            ty = y1 + 3.0
            tlen = tl[tnet]
            tx, _ = c.top_tab('left', length=tlen + 0.4, at=ty)
            pt = (x1 - 0.6 - tlen, ty)
            D.via('TopVia1', pt[0], pt[1])
            D.via('Via4', pt[0], pt[1], padlo=0.66, padhi=0.66)
            D.via('Via3', pt[0], pt[1], padlo=0.66, padhi=0.66)
            top_pads.append((tnet, pt))
            bx = cx + colw + 0.6 + bl
            D.box('M5', x2 + 0.6, ty - 0.5, bx + 0.4, ty + 0.5)
            pb = (bx, ty)
            D.via('Via4', pb[0], pb[1], padlo=0.66, padhi=0.66)
            D.via('Via3', pb[0], pb[1], padlo=0.66, padhi=0.66)
            bot_pads.append((bnet, pb))
            caps[name] = c
            y = y2 + 3.0
            bl += 1.0
    pex_labels = []
    # ---------------- Metal4 tracks and Metal3 verticals
    # track x-extent per net: from the leftmost to the rightmost connection
    conn = {net: [] for net in NETS}
    for net, pt in top_pads + bot_pads:
        conn[net].append(pt)
    for net, pos in row.port_pos.items():
        conn[net].append(pos)
    conn['va'].append(va_head)
    conn['vb'].append(vb_head)
    conn['vth'].append(vth_head)
    conn['vbn'].append(vbn_head)
    conn['vss'].append(vss_head)
    W_L, W_R = XR0 - 3.0, 118.0
    for net in ('en', 'trim0', 'trim1', 'trim2', 'trim3'):
        conn[net].append((W_L + 0.5, TY[net]))
    conn['osc_clk'].append((W_R - 0.5, TY['osc_clk']))
    conn['vss'].append((W_L + 2.0, TY['vss']))
    conn['vss'].append((W_R - 2.0, TY['vss']))
    # the top pads of one column on the same net share one Metal3 vertical (same x)
    for net in NETS:
        pts = conn[net]
        ty = TY[net]
        xs = [p[0] for p in pts]
        D.hwire('M4', min(xs), max(xs), ty, ext=False)
        if net in ('va', 'vb', 'vth', 'vbn'):
            D.label('M4txt', (min(xs) + max(xs)) / 2, ty, net)       # schematic top-level net names
        elif net.startswith('b'):
            # capacitor bottom-plate nets (b<i>, bb<i>): schematic names live inside g1_osc_cbank, so
            # the label would be an unmatched port for LVS; it is added to the PEX input only
            pex_labels.append((net, (min(xs) + max(xs)) / 2, ty))
        byx = {}
        for x, y in pts:
            byx.setdefault(round(x, 3), []).append(y)
        for x, ys in byx.items():
            ylo, yhi = min(ys + [ty]), max(ys + [ty])
            if yhi - ylo > 0.01:
                D.vwire('M3', x, ylo, yhi)
            D.vpad('Via3', x, ty, lo='v', hi='h')
    # ---------------- antenna diode on vth (schematic revision 5, 2026-09-19): the net has only gates
    # (M2 of both comparators), poly resistors and the cmim top plate, so the chip-level antenna check
    # flagged its two gates (Ant.b, cumulative metal / gate area 283 > 200 without a diode).  A
    # dpantenna PCell (p+ in n-well, 0.78 x 0.78 um; anode vth, cathode = n-well on vdd) sits just
    # above the PMOS row, its n-well overlapping the row block's n-well (tied to vdd by the row's n+
    # bar), on the Metal3 vertical of the row block's vth port, which passes over it on its way to
    # the Metal4 vth track.  (dantenna below the row was tried first; its ngspice model stalls the
    # transient, see the schematic generator.)
    xd, yport = row.port_pos['vth']
    yd = row.extent[3] + 0.15 + 0.39          # p+ Activ 0.15 above the row block's n-well edge (overlap)
    D.pcell('dpantenna', {'w': '0.78u', 'l': '0.78u'}, pya.Trans(pya.Point(um(xd - 0.39), um(yd - 0.39))))
    D.box('M1', xd - 0.31, yd - 0.31, xd + 0.31, yd + 0.31)   # the PCell's Metal1 has no Cont enclosure (M1.c1)
    D.via('Via1', xd, yd)
    D.box('M2', xd - 0.20, yd - 0.36, xd + 0.20, yd + 0.36)   # Mn.d 0.144
    D.via('Via2', xd, yd)
    assert yport < yd < TY['vth'], 'diode must sit on the vth port vertical'
    diode_box = (xd - 0.70, yd - 0.70, xd + 0.70, yd + 0.70)
    # macro box: XL..XR x YB..YT; ring 1 um inside it, power bars on the south/north edges,
    # pins as Metal3 stubs 1.5 x 0.3 on the west/east edges
    XL, XR = W_L - 1.5, W_R + 1.5
    YB = -8.0
    YT = max(c.mim[3] for c in caps.values()) + 8.0
    D.box('prBoundary', XL, YB, XR, YT)
    # ---------------- no-fill regions (datatype 23 shapes, honoured by the PDK filler that
    # fill_macro.sh runs on the macro and by the chip-level filler), 3 um margin:
    #  - resistor block: no Activ/GatPoly/Metal1-3 fill next to the matched rppd segments and their
    #    heads/joins (Metal4/5 fill above it is allowed: the va/vb/vth verticals are Metal3)
    #  - row block (comparators, switches, logic): no fill on any layer it uses (Activ .. Metal3)
    #  - capacitor columns with their tabs: no Metal4/5 fill under the Metal5 bottom plates and next to
    #    the Via3/Via4 pads, no TopMetal fill (chip filler) near the plates; Activ .. Metal3 fill under
    #    the capacitors is allowed
    #  - Metal4 track channel (timing nodes va/vb): no Metal2-5 fill; Activ/GatPoly/Metal1 allowed
    #  - antenna diode: all layers
    #  - TopMetal1/2 fill is never placed by fill_macro.sh (chip PDN stripes cross the macro); the
    #    TopMetal no-fill shapes steer the chip-level filler away from the sensitive regions
    LOWER = ('Activ_nf', 'GatPoly_nf', 'M1_nf', 'M2_nf', 'M3_nf', 'TM1_nf', 'TM2_nf')
    MAC = (XL, YB, XR, YT)
    D.nofill(XR0 - 1.0, YR - 1.0, XR0 + len(order) * SEG_PITCH + 1.0, YR + max(L.values()) + 1.0, layers=LOWER, clip=MAC)
    D.nofill(row.extent[0], row.extent[1], row.extent[2], row.extent[3], layers=LOWER, clip=MAC)
    D.nofill(*diode_box, margin=1.5, clip=MAC)
    for cx, lst, tl in ((2.0, col, None), (41.5, col2, None), (82.5, col3, None)):
        boxes = [caps[name].m5 for name, _, _, _ in lst]
        D.nofill(min(b[0] for b in boxes) - 6.0, min(b[1] for b in boxes), max(b[2] for b in boxes) + 6.0, max(b[3] for b in boxes),
                 layers=NOFILL_UPPER, clip=MAC)
    D.nofill(W_L, TY0 - 1.0, W_R, TY0 + 1.0 * (len(NETS) - 1) + 1.0, margin=1.0,
             layers=('M2_nf', 'M3_nf', 'M4_nf', 'M5_nf', 'TM1_nf', 'TM2_nf'), clip=MAC)
    lef_pins = []
    for net in ('en', 'trim0', 'trim1', 'trim2', 'trim3'):
        name = net if net == 'en' else 'trim[%s]' % net[-1]
        D.pin('M3', XL, TY[net] - 0.15, W_L + 0.8, TY[net] + 0.15, name)
        lef_pins.append((name, 'Metal3', (XL, TY[net] - 0.15, XL + 1.5, TY[net] + 0.15), 'INPUT', 'SIGNAL'))
    D.pin('M3', W_R - 0.8, TY['osc_clk'] - 0.15, XR, TY['osc_clk'] + 0.15, 'osc_clk')
    lef_pins.append(('osc_clk', 'Metal3', (XR - 1.5, TY['osc_clk'] - 0.15, XR, TY['osc_clk'] + 0.15), 'OUTPUT', 'SIGNAL'))
    # ---------------- power: VDD bar north edge, VSS bar south edge, ring
    Y_VDD = YT - 1.0
    Y_VSS = YB + 1.0
    D.box('M3', XL, Y_VDD - 1.0, XR, Y_VDD + 1.0)
    D.box('M3pin', XL, Y_VDD - 1.0, XR, Y_VDD + 1.0)
    D.label('M3txt', 40.0, Y_VDD, 'VDD')
    D.box('M3', XL, Y_VSS - 1.0, XR, Y_VSS + 1.0)
    D.box('M3pin', XL, Y_VSS - 1.0, XR, Y_VSS + 1.0)
    D.label('M3txt', 40.0, Y_VSS, 'VSS')
    lef_pins.append(('VDD', 'Metal3', (XL, Y_VDD - 1.0, XR, Y_VDD + 1.0), 'INOUT', 'POWER'))
    lef_pins.append(('VSS', 'Metal3', (XL, Y_VSS - 1.0, XR, Y_VSS + 1.0), 'INOUT', 'GROUND'))
    ring, ext = D.guard_ring(XL + 1.0, YB + 1.0, XR - 1.0, YT - 1.0, 0.30, kind='p')
    # resistor vdd heads -> Metal2 collector at y 71 -> Metal3 up to the VDD bar
    for h in vdd_heads:
        D.vpad('Via1', h[0], h[1], hi='v')
        D.vwire('M2', h[0], h[1], 71.0)
    xs = [h[0] for h in vdd_heads]
    D.hwire('M2', min(xs), max(xs), 71.0)
    D.vpad('Via2', xs[0], 71.0, lo='h', hi='v')
    D.vwire('M3', xs[0], 71.0, Y_VDD)
    # row block vdd rail -> Metal2 east of the caps? no: Metal2 riser right of the block up to the bar
    xv = row.extent[2] + 1.0
    D.hwire('M1', row.extent[2] - 1.0, xv, row.VDD_Y, w=0.30)
    D.vpad('Via1', xv, row.VDD_Y, hi='v')
    D.vwire('M2', xv, row.VDD_Y, Y_VDD)
    D.vpad('Via2', xv, Y_VDD, lo='v', hi='h')
    # row block vss rail -> VSS bar (Metal3 stubs); vss track ends -> VSS bar via the ring sides
    for x in (5.0, 25.0, 45.0):
        D.vpad('Via1', x, row.VSS_Y, hi='v')
        D.vwire('M2', x, row.VSS_Y, Y_VSS)
        D.vpad('Via2', x, Y_VSS, lo='v', hi='h')
    for x in (W_L + 2.0, W_R - 2.0):
        D.vwire('M3', x, TY['vss'], Y_VSS)
    for x in (W_L + 2.0, W_R - 2.0, 60.0):
        D.box('M2', x - 0.15, ring[1] - 0.30, x + 0.15, ring[1] + 0.30)
        D.vpad('Via2', x, ring[1], lo='s', hi='v')
        D.via('Via1', x, ring[1])
    # signal heads of the resistors: via on the Metal1 head, Metal3 vertical (drawn above) needs Via1/Via2
    for h in (va_head, vb_head, vth_head, vss_head, vbn_head):
        D.vpad('Via1', h[0], h[1], hi='v')
        D.box('M2', h[0] - 0.12, h[1] - 0.30, h[0] + 0.12, h[1] + 0.30)
        D.vpad('Via2', h[0], h[1], lo='v', hi='v')
    D.clean_pcell_markers()
    # ---------------- move the macro to the origin (lower-left of the macro box at 0, 0)
    t = pya.Trans(pya.Point(um(-XL), um(-YB)))
    for li in ly.layer_indexes():
        cell.shapes(li).transform(t)
    Wm, Hm = XR - XL, YT - YB
    with open(out.replace('.gds', '_pexlabels.txt'), 'w') as f:
        for net, x, y in pex_labels:
            f.write('%s 50/25 %.3f %.3f\n' % (net, x - XL, y - YB))
    pins = [(n, l, (x1 - XL, y1 - YB, x2 - XL, y2 - YB), d, u) for (n, l, (x1, y1, x2, y2), d, u) in lef_pins]
    # Metal1/2 everywhere, Metal3 inside the pin stubs and bars; Metal4 and above only where the
    # layout has them (Metal4 tracks, capacitor bottom plates on Metal5, top plates on TopMetal1)
    # and never over the VDD/VSS bars, so that the chip PDN can land its straps on the bars
    # Metal4/Metal5: the interior (3 um inside the edges = the fill window of fill_macro.sh, so the
    # 3 um above the VDD/VSS bars stay free for the chip PDN straps); with the metal fill the interior
    # really is occupied on these layers.  TopMetal1: the capacitor plates only (from the shapes).
    bars = [(0.0, 0.0, Wm, 2.5), (0.0, Hm - 2.5, Wm, Hm)]
    obs = [('Metal1', [(0.0, 0.0, Wm, Hm)]), ('Metal2', [(0.0, 0.0, Wm, Hm)]),
           ('Metal3', [(1.8, 2.5, Wm - 1.8, Hm - 2.5)]),
           ('Metal4', [(3.0, 3.0, Wm - 3.0, Hm - 3.0)]),
           ('Metal5', [(3.0, 3.0, Wm - 3.0, Hm - 3.0)]),
           ('TopMetal1', shape_obs(cell, 'TM1', 0.5, (0.0, 0.0, Wm, Hm), bars))]
    return cell, (Wm, Hm, pins, obs)


if __name__ == '__main__':
    out = globals().get('out', 'g1_osc.gds')
    ly = pya.Layout()
    ly.dbu = 0.001
    cell, (Wm, Hm, pins, obs) = build(ly, out)
    write_gds(ly, out)
    write_lef(out.replace('.gds', '.lef'), 'g1_osc', Wm, Hm, pins, obs)
    print('wrote', out, cell.dbbox())
