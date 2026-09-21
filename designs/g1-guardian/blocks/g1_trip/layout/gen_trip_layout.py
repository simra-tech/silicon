#!/usr/bin/env python3
"""G1_TRIP layout generator (KLayout 0.30.9 + SG13G2 PCells, run inside the pinned container):

  python3 gen_trip_layout.py [dac|cmp|cond|top]    -> writes g1_trip.gds (or a single cell) here

Cells (names equal the schematic subcircuits so that the hierarchical LVS compares cell by cell):
  g1_dac8   530-unit rppd string (4 x 1.2 um units, pitch 1.76 um with shared heads) as a
            serpentine of 4 pedestal + 4 tapped + 1 top column, a dummy column on each side and
            a dummy unit at both ends of every column; 510 thick-oxide NMOS 2/0.45 switches as
            255 shared-source pairs in a binary tree (levels 0..5 beside each tapped column,
            levels 6..7 in a final column), 3.3 V gate lines on Metal1 lanes fed by a Metal3 bus
            from eight level shifters (g1_tlvlup structure) at the bottom.
  g1_cmp    StrongARM comparator with neutralisation dummies, output inverters and NOR SR latch.
  g1_cond   ISENSE/2 divider (10 x rppd 2/76.7) and its 1 pF cmim hold capacitor.
  g1_trip   top: cond + two DACs + two hold capacitors + two comparators + clock inverter.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from g1_layout_lib import *  # noqa: F401,F403,E402

# ----------------------------------------------------------------------------- DAC ---------
P = RppdUnit.PITCH          # 1.76 unit pitch
NS = 64                     # units per string column
COLP = 4.36                 # pitch of adjacent string columns (pSD/ExtBlock/SalBlock merge)
GRP = 16.70                 # pitch of a tapped group (string column + switch columns)
TAPBAR = (4.54, 4.84)       # p+ tap bar Activ x-range relative to the string body
OXA = 5.95                  # column A (level 0) Activ x relative to the string body
XG = OXA + 2.74             # Metal2 gap lane between column A and column BC
OXB = 11.43                 # column BC (levels 1..5) Activ x
LANEX = [0.08 + 0.46 * k for k in range(5)]   # Metal2 lane x offsets over a BC pair (0..2.0)
M2PADW = 0.24               # Metal2 pad width across the lane direction (0.46 pitch, Mn.b 0.21)


def bus_index(b, inverted):
    """Metal3 gate-bus line index of dh<b> (inverted=False) / dhn<b> (inverted=True)"""
    return 2 * b + (0 if inverted else 1)


class DacBuilder:
    def __init__(self, ly, name='g1_dac8', with_shifters=True):
        self.ly = ly
        self.cell = ly.create_cell(name)
        self.D = Draw(ly, self.cell)
        self.with_shifters = with_shifters
        self.lanes = []          # (x, net, y_top): Metal1 gate lanes to drop onto the bus
        self.Y0 = 26.5 if with_shifters else 16.0   # body bottom of string slot 0
        self.X0 = 3.0

    # -- string ----------------------------------------------------------------------------
    def node(self, i):
        return self.Y0 + i * P - 0.28

    def string_column(self, x, real):
        """string column at body x; `real` = set of real slot indices (others are dummies);
        slots -1..NS drawn"""
        D = self.D
        for i in range(-1, NS + 1):
            RppdUnit(D, x, self.Y0 + i * P, dummy=(i not in real))

    def head(self, x, i):
        y = self.node(i)
        return (x + 0.02, y - 0.15, x + 3.98, y + 0.15)

    def bridge_m1(self, xl, xr, i):
        y = self.node(i)
        self.D.box('M1', xl + 3.98 - 0.30, y - 0.15, xr + 0.02 + 0.30, y + 0.15)

    def bridge_m2(self, xl, xr, i):
        y = self.node(i)
        D = self.D
        for x in (xl + 0.30, xr + 3.70):
            D.square('Via1', x, y, VIA)
        D.box('M2', xl + 0.30 - 0.15, y - 0.15, xr + 3.70 + 0.15, y + 0.15)

    # -- switch pairs ------------------------------------------------------------------------
    def pair_between(self, ox, ya, yb, lane):
        """pair centred between input positions ya (input a) and yb (input b)"""
        flip = ya > yb
        oy = (ya + yb) / 2 - HvPair.Y_S
        return HvPair(self.D, ox, oy, lane=lane, flip=flip)

    def pad(self, pair, which, x, m2w=M2PADW, m2h=0.30):
        """Metal1 pad + Via1 + Metal2 pad on strip `which` of `pair` at x.  A pad that no Metal2
        wire joins needs m2h=0.60 for the Metal2 area rule (Mn.d 0.144)."""
        y = {'a': pair.y_a(), 'b': pair.y_b(), 's': pair.y_s()}[which]
        D = self.D
        D.box('M1', x - 0.145, y - 0.15, x + 0.145, y + 0.15)
        D.square('Via1', x, y, VIA)
        D.box('M2', x - m2w / 2, y - m2h / 2, x + m2w / 2, y + m2h / 2)
        return (x, y)

    def group(self, c, xs, up):
        """tapped group c with the string body at xs; up=True: chain runs upward"""
        D = self.D
        Y0 = self.Y0

        def ytap(j):
            return self.node(j) if up else self.node(NS - j)
        oxa, oxb = xs + OXA, xs + OXB
        xg = xs + XG
        # ---- level 0: 32 pairs beside the taps
        a_pairs = []
        for k in range(32):
            y0, y1 = ytap(2 * k), ytap(2 * k + 1)
            flip = y0 > y1
            oy = min(y0, y1) - HvPair.Y_A
            pr = HvPair(D, oxa, oy, lane=0, flip=flip)
            for which, yt in (('a', y0), ('b', y1)):
                xh = xs + 3.70
                D.square('Via1', xh, yt, VIA)
                xp, yp = self.pad(pr, which, oxa + 0.50, m2w=0.30)
                D.box('M2', xh - 0.15, min(yt, yp) - 0.15, xp + 0.15, max(yt, yp) + 0.15)
            xp, yp = self.pad(pr, 's', oxa + 1.50, m2w=0.30)
            D.hwire('M2', xp, xg, yp)
            a_pairs.append(pr)
        # ---- level 1: 16 pairs in column BC, inputs through the gap lane
        prev = a_pairs
        b_pairs = []
        for j in range(16):
            ya, yb = prev[2 * j].y_s(), prev[2 * j + 1].y_s()
            pr = self.pair_between(oxb, ya, yb, lane=0)
            x0 = oxb + LANEX[0]
            for which, yin in (('a', ya), ('b', yb)):
                xp, yp = self.pad(pr, which, x0)
                D.vwire('M2', xg, yin, yp)
                D.hwire('M2', xg, xp, yp)
            self.pad(pr, 's', oxb + LANEX[1])
            b_pairs.append(pr)
        # ---- levels 2..5 in column BC, vertical Metal2 links on lanes
        prev = b_pairs
        for lvl in range(2, 6):
            cur = []
            xin = oxb + LANEX[lvl - 1]
            xout = oxb + LANEX[min(lvl, 4)]
            for j in range(len(prev) // 2):
                ya, yb = prev[2 * j].y_s(), prev[2 * j + 1].y_s()
                pr = self.pair_between(oxb, ya, yb, lane=lvl - 1)
                for which, yin in (('a', ya), ('b', yb)):
                    xp, yp = self.pad(pr, which, xin)
                    D.vwire('M2', xin, yin, yp)
                self.pad(pr, 's', xout, m2h=(0.60 if lvl == 5 else 0.30))
                cur.append(pr)
            prev = cur
        out5 = prev[0]
        # ---- gate lanes (Metal1) and TGO
        pairs_a = a_pairs
        ylo = min(p.oy for p in pairs_a) - 0.27
        yhi = max(p.oy for p in pairs_a) + HvPair.H + 0.27
        D.box('TGO', oxa - 0.52, ylo, oxb + 2.52, yhi)
        for xl, net, ytop in ((oxa - HvPair.LANE0, 'dhn0', yhi), (oxa + 2.0 + HvPair.LANE0, 'dh0', yhi)):
            self.lanes.append((xl, net, ytop))
        for k in range(5):
            self.lanes.append((oxb - HvPair.LANE0 - 0.5 * k, 'dhn%d' % (k + 1), yhi))
            self.lanes.append((oxb + 2.0 + HvPair.LANE0 + 0.5 * k, 'dh%d' % (k + 1), yhi))
        # ---- p+ tap bar between the string and column A, up to the guard ring
        self.tapbars.append((xs + TAPBAR[0], xs + TAPBAR[1], self.node(0) + 0.45))
        # level-5 output pad (Metal2 pad at lane 4) -> Metal3
        xo, yo = oxb + LANEX[4], out5.y_s()
        D.square('Via2', xo, yo, VIA)
        D.box('M3', xo - 0.15, yo - 0.15, xo + 0.15, yo + 0.15)
        return (xo, yo)

    def build(self):
        D = self.D
        Y0 = self.Y0
        self.tapbars = []
        order = ['DL', 'P0', 'P1', 'P2', 'P3', 'T0', 'T1', 'T2', 'T3', 'U', 'DR']
        xcol = {}
        x = self.X0
        for n in order:
            xcol[n] = x
            x += GRP if n.startswith('T') else COLP
        self.xcol = xcol
        real = {'DL': set(), 'DR': set(), 'P0': set(range(1, NS)), 'U': set(range(0, 19))}
        for n in order:
            self.string_column(xcol[n], real.get(n, set(range(NS))))
        # chain bridges: adjacent P columns on Metal1, across the switch columns on Metal2
        self.bridge_m1(xcol['P0'], xcol['P1'], NS)
        self.bridge_m1(xcol['P1'], xcol['P2'], 0)
        self.bridge_m1(xcol['P2'], xcol['P3'], NS)
        self.bridge_m1(xcol['P3'], xcol['T0'], 0)
        self.bridge_m2(xcol['T0'], xcol['T1'], NS)
        self.bridge_m2(xcol['T1'], xcol['T2'], 0)
        self.bridge_m2(xcol['T2'], xcol['T3'], NS)
        self.bridge_m2(xcol['T3'], xcol['U'], 0)
        # tapped groups
        m5 = []
        for c in range(4):
            m5.append(self.group(c, xcol['T%d' % c], up=(c % 2 == 0)))
        # ---- column D: levels 6 and 7
        xd = xcol['DR'] + 6.45
        self.tapbars.append((xcol['DR'] + TAPBAR[0], xcol['DR'] + TAPBAR[1], self.node(0) + 0.45))
        oyd = Y0 + 60.0
        xd0, xd1, xd2 = xd + LANEX[0], xd + LANEX[1], xd + LANEX[2]
        p1 = HvPair(D, xd, oyd, lane=0, flip=True)            # m5_2 (a, top), m5_3 (b)
        p0 = HvPair(D, xd, oyd + 7.04, lane=0, flip=True)     # m5_0 (a, top), m5_1 (b)
        targets = [p0.y_a(), p0.y_b(), p1.y_a(), p1.y_b()]     # decreasing y for groups 0..3
        for c, (xo, yo) in enumerate(m5):
            yt = targets[c]
            D.vwire('M3', xo, yo, yt)
            D.hwire('M3', xo, xd0, yt)
        for pr, ins in ((p0, ('a', 'b')), (p1, ('a', 'b'))):
            for which in ins:
                xp, yp = self.pad(pr, which, xd0, m2h=0.60)
                D.square('Via2', xp, yp, VIA)
                D.box('M3', xp - 0.15, yp - 0.15, xp + 0.15, yp + 0.15)
            self.pad(pr, 's', xd1)
        p7 = self.pair_between(xd, p0.y_s(), p1.y_s(), lane=1)
        for which, yin in (('a', p0.y_s()), ('b', p1.y_s())):
            xp, yp = self.pad(p7, which, xd1)
            D.vwire('M2', xd1, yin, yp)
        xo, yo = self.pad(p7, 's', xd2, m2h=0.60)
        self.out_pad = (xo, yo)
        ylo = p1.oy - 0.27
        yhi = p0.oy + HvPair.H + 0.27
        D.box('TGO', xd - 0.52, ylo, xd + 2.52, yhi)
        for k, net in ((0, 'dhn6'), (1, 'dhn7')):
            self.lanes.append((xd - HvPair.LANE0 - 0.5 * k, net, yhi))
        for k, net in ((0, 'dh6'), (1, 'dh7')):
            self.lanes.append((xd + 2.0 + HvPair.LANE0 + 0.5 * k, net, yhi))
        self.xright = xd + 2.0 + HvPair.LANE0 + 0.5 + 0.13
        # ---- Metal1 gate lanes down to the Metal3 bus
        ybus0 = Y0 - 2.4
        self.ybus = [ybus0 - 0.5 * n for n in range(16)]
        xb1 = min(xl for xl, _, _ in self.lanes) - 0.5
        xb2 = max(xl for xl, _, _ in self.lanes) + 0.5
        if self.with_shifters:
            self.shifters()
            xb1 = min(xb1, self.bus_xmin)
        for n in range(16):
            D.hwire('M3', xb1, xb2, self.ybus[n], w=0.24, ext=False)
        for xl, net, ytop in self.lanes:
            b = int(net[-1])
            n = bus_index(b, net.startswith('dhn'))
            yb = self.ybus[n]
            D.box('M1', xl - 0.13, yb - 0.15, xl + 0.13, ytop)
            D.square('Via1', xl, yb, VIA)
            D.box('M2', xl - 0.12, yb - 0.31, xl + 0.12, yb + 0.31)    # Mn.d 0.144, endcaps
            D.square('Via2', xl, yb, VIA)
        self.bus_x = (xb1, xb2)
        # ---- vss end of the string (P0 node 1) and vref end (U node 19)
        yv = self.node(1)
        xv = xcol['P0'] + 0.30
        D.square('Via1', xv, yv, VIA)
        D.box('M2', xv - 0.15, yv - 0.15, xv + 0.15, yv + 0.15)
        self.vss_tap = (xv, yv)
        yr = self.node(19)
        xr = xcol['U'] + 3.70
        D.square('Via1', xr, yr, VIA)
        D.box('M2', xr - 0.15, yr - 0.15, xr + 0.15, yr + 0.15)
        self.vref_tap = (xr, yr)
        # ---- without level shifters: direct gate-bus pins (bring-up cell)
        ytop_all = Y0 + NS * P + 1.81 + 0.6
        if not self.with_shifters:
            for n in range(16):
                b, inv = n // 2, (n % 2 == 0)
                name = ('dhn%d' if inv else 'dh%d') % b
                D.pin('M3', xb2 - 1.0, self.ybus[n] - 0.12, xb2, self.ybus[n] + 0.12, name)
            self.ybot_all = self.ybus[-1] - 1.0
        # ---- guard ring (vss), tap bars up to the ring
        gx1, gy1 = self.X0 - 1.5, self.ybot_all
        gx2, gy2 = self.xright + 1.5, ytop_all
        ring, ext = D.guard_ring(gx1, gy1, gx2, gy2, 0.30, kind='p')
        for x1, x2, ylo in self.tapbars:
            D.tap_bar(x1, ylo, x2, gy2 + 0.30, kind='p', cmargin=(0.0, 0.60))
        self.ring, self.ext = ring, ext
        # vss string end -> ring (Metal2 down to the ring bottom, stack to Metal1)
        xv, yv = self.vss_tap
        D.vwire('M2', xv, yv, ring[1])
        D.via('Via1', xv, ring[1])
        # vref: Metal2 up to the top, pin on Metal2 at the ring top
        xr, yr = self.vref_tap
        D.vwire('M2', xr, yr, gy2 + 1.5)
        D.pin('M2', xr - 0.3, gy2 + 0.9, xr + 0.3, gy2 + 1.5, 'vref')
        # out: Metal3 from the level-7 source pad up to the top edge
        xo, yo = self.out_pad
        D.square('Via2', xo, yo, VIA)
        D.box('M3', xo - 0.15, yo - 0.15, xo + 0.15, yo + 0.15)
        D.vwire('M3', xo, yo, gy2 + 1.5)
        D.pin('M3', xo - 0.3, gy2 + 0.9, xo + 0.3, gy2 + 1.5, 'out')
        # vss pin on the ring (Metal1)
        D.pin('M1', ring[0] - 0.13, gy1 + 5.0, ring[0] + 0.13, gy1 + 8.0, 'vss')
        self.pins = {'vref': (xr, gy2 + 1.2), 'out': (xo, gy2 + 1.2), 'ring': ring,
                     'vdd': (self.X0 + 1.5, 0.3), 'vdda': (self.bank_x + 8 * 7.0 + 1.0, 0.3),
                     'd': [(self.bank_x + 7.0 * b + 1.065, 0.3) for b in range(8)]}
        D.clean_pcell_markers()
        return self.cell

    def shifters(self):
        """Eight level shifters (schematic g1_tlvlup: LV inverter, cross-coupled HV pair, two HV
        inverters) in a bank below the gate bus, one 7.0 um column per bit.  Rows from the
        bottom: 1.2 V inverter (own vdd NWell with an n+ tie), p+ substrate tie bar, four HV NMOS
        (MN1 MN2 XO.MN XOB.MN), four HV PMOS in one vdda NWell (MP1 MP2 XO.MP XOB.MP) with the
        n+ tie bar and the vdda rail on top.  Each device column i carries one net on a Metal2
        vertical (nb, n, y, yb) joining the NMOS and PMOS drains; gate cross-connections are
        Metal3 jogs.  Inputs d0..d7 are Metal2 pins at the bottom edge."""
        D = self.D
        ylv = 3.0
        yhn = ylv + 3.6
        yhp = ylv + 7.6
        pitch = 7.0
        bx = self.X0 + 6.5
        self.bank_x = bx
        bank_x2 = bx + 8 * pitch
        # the Metal2 output verticals to the bus must clear every gate-lane drop pad (0.5 um):
        # each output is jogged on Metal2 above the vdda rail to the nearest free x
        lane_xs = [xl for xl, _, _ in self.lanes]
        used = []

        def is_free(c):
            return all(abs(c - xl) >= 0.50 for xl in lane_xs) and all(abs(c - u) >= 0.50 for u in used)

        def free_pair(xy, xyb):
            """free x for the yb output (jog level above) near xyb and for the y output (jog level
            below) near xy but left of both xyb and its free x, so the two jogs never cross"""
            cands = sorted([round(xyb + 0.05 * k, 3) for k in range(-52, 68)], key=lambda c: abs(c - xyb))
            for cb in cands:
                if not is_free(cb):
                    continue
                lim = min(xyb, cb) - 0.5
                cy = sorted([round(xy + 0.05 * k, 3) for k in range(-52, 20)], key=lambda c: abs(c - xy))
                for c in cy:
                    if c <= lim and is_free(c) and abs(c - cb) >= 0.5:
                        used.extend([cb, c])
                        return c, cb
            raise RuntimeError('no free jog positions near %g' % xy)
        # rails across the bank (Metal1): LV vss, vdd, p+ tie bar (vss), vdda + n+ tie bar
        xr1, xr2 = self.X0 - 1.5 - 0.15, self.xright + 1.5 + 0.15   # ring centre lines
        D.hwire('M1', xr1, xr2, ylv - 1.0, w=0.26, ext=False)                    # vss (LV)
        D.hwire('M1', self.X0 + 1.5, bank_x2 + 0.5, ylv + 1.80, w=0.26, ext=False)   # vdd
        D.tap_bar(xr1, ylv + 2.25, xr2, ylv + 2.55, kind='p', m1w=0.26, cmargin=(0.6, 0.6))  # vss (HV)
        D.box('NWell', bx - 0.5, yhp - 0.62, bank_x2 - 0.5, ylv + 13.02)
        D.tap_bar(bx + 0.2, ylv + 12.1, bank_x2 - 1.2, ylv + 12.4, kind='n', m1w=0.30)  # vdda tie
        D.hwire('M1', bx, bank_x2 + 1.0, ylv + 12.25, w=0.30, ext=False)         # vdda rail
        D.box('TGO', bx - 0.5, yhn - 0.52, bank_x2 - 0.5, ylv + 12.7)
        D.box('pSD', bx + 0.5 - 0.18, yhp - 0.40, bank_x2 - 1.5 + 1.31, yhp + 3.9 + 0.40)   # merged HV PMOS pSD
        xv_min = None
        for b in range(8):
            x0 = bx + pitch * b
            # ---- LV inverter
            mn = Mos(D, 'nmos', 0.5, 0.13, 1, x0 + 0.5, ylv)
            mp = Mos(D, 'pmos', 1.0, 0.13, 1, x0 + 2.8, ylv)
            D.box('NWell', x0 + 2.49, ylv - 0.31, x0 + 4.74, ylv + 1.31)
            D.box('Activ', x0 + 4.2, ylv + 0.2, x0 + 4.5, ylv + 0.7)              # n+ tie
            D.cont(x0 + 4.35, ylv + 0.45)
            D.box('M1', x0 + 4.2, ylv + 0.2, x0 + 4.5, ylv + 1.93)
            D.box('GatPoly', x0 + 0.84, ylv - 0.56, x0 + 3.27, ylv - 0.10)        # common gate bar
            xa = x0 + 1.065
            D.cont(xa, ylv - 0.33)
            D.square('M1', xa, ylv - 0.33, 0.30)
            D.square('Via1', xa, ylv - 0.33, VIA)
            s0 = mn.strip(0)
            D.box('M1', s0[0], ylv - 0.87, s0[2], s0[1])                          # S -> vss rail
            s1 = mn.strip(1)
            D.box('M1', s1[0], s1[3], s1[2], ylv + 1.40)                          # D -> ab bar
            p0 = mp.strip(0)
            D.box('M1', p0[0], p0[3], p0[2], ylv + 1.40)
            p1 = mp.strip(1)
            D.box('M1', p1[0], p1[3], p1[2], ylv + 1.93)                          # S -> vdd rail
            D.box('M1', s1[0], ylv + 1.20, p0[2], ylv + 1.40)                     # ab bar
            xab = x0 + 2.20
            D.vpad('Via1', xab, ylv + 1.30, hi='v')
            # ---- HV NMOS row
            ox = [x0 + 0.5 + 1.5 * i for i in range(4)]
            xv = [o + 1.15 for o in ox]
            for i in range(4):
                m = Mos(D, 'nmosHV', 1.9, 0.45, 1, ox[i], yhn)
                gp, gc = m.gate_strap('bottom', 'mid', gap=0.10)
                st = m.strip(0)
                D.box('M1', st[0], ylv + 2.40, st[2], st[1])                     # S -> tie bar
                st = m.strip(1)
                D.box('M1', st[0], st[3], st[2], ylv + 5.95)                      # D up
                D.vpad('Via1', xv[i], ylv + 5.80, hi='v')
                D.vpad('Via1', gc[0], gc[1], hi='v')
            # gate sources: MN1 <- a (pin), MN2 <- ab, XO.MN <- nb (col 0), XOB.MN <- y (col 2)
            yga = yhn - 0.36
            D.vwire('M2', xa, 0.3, yga)                                            # a vertical
            D.pin('M2', xa - 0.3, 0.0, xa + 0.3, 0.6, 'd%d' % b)
            D.vwire('M2', xab, ylv + 1.30, yga)                                    # ab vertical
            D.box('M2', xab - 0.12, yga - 0.15, ox[1] + 0.565 + 0.12, yga + 0.15)
            for i, src in ((2, 0), (3, 2)):
                gx = ox[i] + 0.565
                D.box('M2', gx - 0.15, yga - 0.30, gx + 0.15, yga + 0.30)         # Mn.d
                D.vpad('Via2', gx, yga, lo='s', hi='h')
                D.hwire('M3', xv[src], gx, yga)
                D.vpad('Via2', xv[src], yga, lo='v', hi='h')
                D.box('M2', xv[src] - 0.12, yga - 0.30, xv[src] + 0.12, yga + 0.30)
            # ---- column verticals (Metal2): nb (0), n (1), y (2), yb (3)
            ylo = [yga, ylv + 5.80, yga, ylv + 5.80]
            for i in range(4):
                D.vwire('M2', xv[i], ylo[i], ylv + 7.00)
            # ---- HV PMOS row
            ww = [0.3, 0.3, 3.9, 3.9]
            for i in range(4):
                m = Mos(D, 'pmosHV', ww[i], 0.45, 1, ox[i], yhp)
                gp, gc = m.gate_strap('bottom', 'mid', gap=0.10)
                st = m.strip(0)
                D.box('M1', st[0], st[3], st[2], ylv + 12.25)                     # S -> vdda rail
                st = m.strip(1)
                D.box('M1', st[0], ylv + 6.85, st[2], st[1])                      # D down
                D.vpad('Via1', xv[i], ylv + 7.00, hi='v')
                D.vpad('Via1', gc[0], gc[1], hi='v')
            # PMOS gates: MP1 <- n (col 1) @yB1, MP2 <- nb (col 0) @yB2, XO.MP <- nb @yB2, XOB.MP <- y (col 2) @yB1
            yB1, yB2 = ylv + 6.30, ylv + 6.80
            ygp = yhp - 0.36
            for i, src, yB in ((0, 1, yB1), (1, 0, yB2), (2, 0, yB2), (3, 2, yB1)):
                gx = ox[i] + 0.565
                D.vwire('M2', gx, yB, ygp)
                D.vpad('Via2', gx, yB, lo='v', hi='h')
                D.hwire('M3', xv[src], gx, yB)
                D.vpad('Via2', xv[src], yB, lo='v', hi='h')
            # ---- outputs y (col 2) -> dh<b>, yb (col 3) -> dhn<b>: jog above the vdda rail to a
            #      free x, then up to the Metal3 bus
            xfy, xfyb = free_pair(xv[2], xv[3])
            for i, inv, xf, yj in ((2, False, xfy, ylv + 12.45), (3, True, xfyb, ylv + 12.95)):
                yb = self.ybus[bus_index(b, inv)]
                D.vwire('M2', xv[i], ylv + 7.00, yj)
                D.hwire('M2', xv[i], xf, yj)
                D.vwire('M2', xf, yj, yb)
                D.vpad('Via2', xf, yb, lo='v', hi='h')
                xv_min = xf if xv_min is None else min(xv_min, xf)
        # ---- supply pins at the bottom edge: vdd (Metal2 from the vdd rail), vdda (from the rail)
        xvdd = self.X0 + 1.5
        D.via('Via1', xvdd, ylv + 1.75)
        D.vwire('M2', xvdd, 0.3, ylv + 1.75)
        D.pin('M2', xvdd - 0.3, 0.0, xvdd + 0.3, 0.6, 'vdd')
        xvdda = bank_x2 + 1.0
        D.via('Via1', xvdda, ylv + 12.25)
        D.vwire('M2', xvdda, 0.3, ylv + 12.25)
        D.pin('M2', xvdda - 0.3, 0.0, xvdda + 0.3, 0.6, 'vdda')
        self.ybot_all = ylv - 2.0
        self.bus_xmin = xv_min - 0.5

# ------------------------------------------------------------------------- comparator ------
class CmpBuilder:
    """g1_cmp: NMOS row (y 0..6) with the clocked tail in the centre and the two halves of the
    circuit mirrored about x = 0; Metal2 tracks in a channel above it (xq xp xn yn clk xnb|ynb q qb);
    PMOS row on top in one NWell with the vdd rail and n+ tie over it; p+ guard ring (vss).
    Every device is a single- or multi-finger PCell with its gate strapped on the channel-far
    side (bottom for NMOS, bottom for PMOS too, i.e. channel side) and contacted beyond the Activ
    ('left' in the left half, 'right' in the right half); source/drain strips are extended on
    Metal1 to the rails or to the track vias."""
    YP = 11.0                      # PMOS row Activ bottom
    # track order chosen for mirror symmetry of the parasitic coupling (2026-09-19, after the first
    # post-layout extraction showed the input-pair drains xp/xq with 8.0 and 9.9 fF and the clock
    # track adjacent to yn only): clk sits between the two drains, each drain sees its own latch node
    # (xn, yn) on the other side, each latch node an SR-latch output (static during the decision)
    TRACK = {'qb': 6.6, 'xn': 7.1, 'xp': 7.6, 'clk': 8.1, 'xq': 8.6, 'yn': 9.1, 'q': 9.6, 'xnb': 10.1, 'ynb': 10.1}

    def __init__(self, ly, name='g1_cmp'):
        self.ly = ly
        self.cell = ly.create_cell(name)
        self.D = Draw(ly, self.cell)
        self.span = {}      # track net -> [xmin, xmax] of its vias

    STUB_BOT, STUB_TOP = 6.35, 10.35   # every Metal1 stub spans the whole track channel (see track_via)

    def track_via(self, net, x, from_y, up):
        """Metal1 stub from from_y through the whole track channel (dead end beyond its own track),
        Via1 + Metal2 pad on the track of `net` at x.  The full-height stub makes the Metal1 of the two
        mirrored halves identical (every stub crosses under every track spanning its x), so the
        stub-under-track and stub-to-track parasitics of xp/xq and xn/yn match although the paired
        tracks lie at different heights; with stubs ending at their own track the first extraction
        (2026-09-19) gave 8.0 vs 9.9 fF on the drains and a > 8 mV post-layout offset."""
        D = self.D
        y = self.TRACK[net]
        y1, y2 = (from_y, self.STUB_TOP) if up else (self.STUB_BOT, from_y)
        D.box('M1', x - 0.08, y1, x + 0.08, y2)
        D.vpad('Via1', x, y, hi='h')
        sp = self.span.setdefault(net, [x, x])
        sp[0], sp[1] = min(sp[0], x), max(sp[1], x)

    def nmos(self, side, ox, w, l, ng):
        """NMOS with Activ bottom at y=0, mirrored in x for the left half; returns (Mos, gate pad)"""
        m = Mos(self.D, 'nmos', w, l, ng, ox, 0.0, mirror=(None if side > 0 else 'x'))
        pad, gc = m.gate_strap('bottom', 'left' if side < 0 else 'right', gap=0.10)
        return m, gc

    def pmos(self, side, ox, w, l, ng):
        m = Mos(self.D, 'pmos', w, l, ng, ox, self.YP, mirror=(None if side > 0 else 'x'))
        pad, gc = m.gate_strap('bottom', 'left' if side < 0 else 'right', gap=0.10)
        return m, gc

    def build(self):
        D = self.D
        YP = self.YP
        VSS_Y = -1.5
        VDD_Y = YP + 6.75
        # ---------------- NMOS row: tail in the centre
        tail = Mos(D, 'nmos', 16.0, 0.13, 4, -1.17, 0.0)
        # gate pads on both sides (-1.47 and +1.47, -0.36) so that the clock wiring is mirror
        # symmetric; each pad has its own Metal3 vertical to the clk track
        tpads = [tail.gate_strap('bottom', side, gap=0.10)[1] for side in ('left', 'right')]
        for i in (0, 2, 4):
            st = tail.strip(i)
            D.box('M1', st[0], VSS_Y, st[2], st[1])
        for i in (1, 3):
            st = tail.strip(i)
            D.box('M1', st[0], st[3], st[2], 4.55)
            D.vpad('Via1', tail.strip_x(i), 4.4, hi='h')
        # clk: pads -> Metal3 verticals up to the clk track (they cross the Metal2 tail bar)
        for tgc in tpads:
            D.vpad('Via1', tgc[0], tgc[1], hi='s')
            D.box('M2', tgc[0] - 0.15, tgc[1] - 0.30, tgc[0] + 0.15, tgc[1] + 0.30)
            D.vpad('Via2', tgc[0], tgc[1], lo='s', hi='v')
            D.vwire('M3', tgc[0], tgc[1], self.TRACK['clk'])
            D.vpad('Via2', tgc[0], self.TRACK['clk'], lo='h', hi='v')
            sp = self.span.setdefault('clk', [tgc[0], tgc[0]])
            sp[0], sp[1] = min(sp[0], tgc[0]), max(sp[1], tgc[0])
        # right half (side=+1) devices, then mirrored left half
        # layout order from the centre: input (12/0.34 ng=2), dummy (6/0.13), cross-coupled (3/0.13),
        # inverter N (4/0.13), latch N1 (1.5/0.13), latch N2 (1.5/0.13)
        OXN = {'in': 2.07, 'dum': 4.5, 'cc': 6.0, 'inv': 7.5, 'l1': 9.5, 'l2': 11.0}
        # PMOS x positions (right half, mirrored on the left): chosen so that every PMOS stub to
        # the channel is >= 0.45 um from every NMOS stub of another net (or exactly on top of a
        # stub of the same net), see place_pmos()
        nstubs = []      # (x, net) of the NMOS stubs into the channel, right half

        def X(ox, w_act, side):
            return ox if side > 0 else -(ox + w_act)
        for side in (+1, -1):
            # net names on this side: 'own' differential node (xq on the right, xp on the left)
            own, oth = ('xq', 'xp') if side > 0 else ('xp', 'xq')
            xown, xoth = ('yn', 'xn') if side > 0 else ('xn', 'yn')   # latch nodes
            inb = 'ynb' if side > 0 else 'xnb'
            qq, qqb = ('q', 'qb') if side > 0 else ('qb', 'q')
            inpin = 'inn' if side > 0 else 'inp'

            def stub(net, x, from_y):
                self.track_via(net, x, from_y, True)
                if side > 0:
                    nstubs.append((x, net))
            # -- input device: drains (strips 0, 2) -> own track; source (strip 1) -> tail bar
            m, gc = self.nmos(side, X(OXN['in'], 1.74, side), 12.0, 0.34, 2)
            for i in (0, 2):
                stub(own, m.strip_x(i), m.strip(i)[3])
            D.vpad('Via1', m.strip_x(1), 4.4, hi='h')
            gin = gc
            # -- neutralisation dummy: gate = this side's input, S/D -> other side's node
            m, gc = self.nmos(side, X(OXN['dum'], 0.81, side), 6.0, 0.13, 1)
            for i in (0, 1):
                stub(oth, m.strip_x(i), m.strip(i)[3])
            # input pad wire on Metal1 between the two gate pads, then Metal2 out to the cell edge
            D.hwire('M1', gin[0], gc[0], gin[1], w=0.30)
            D.vpad('Via1', gc[0], gc[1], hi='h')
            self.inpad = self.__dict__.get('inpad', {})
            self.inpad[inpin] = gc
            # -- cross-coupled NMOS: S = own node (strip 0), D = latch node xown (strip 1), G = xoth
            m, gc = self.nmos(side, X(OXN['cc'], 0.81, side), 3.0, 0.13, 1)
            stub(own, m.strip_x(0), m.strip(0)[3])
            stub(xown, m.strip_x(1), m.strip(1)[3])
            stub(xoth, gc[0], gc[1] + 0.15)
            # -- inverter NMOS: S = vss, D = inb, G = xown
            m, gc = self.nmos(side, X(OXN['inv'], 0.81, side), 4.0, 0.13, 1)
            st = m.strip(0)
            D.box('M1', st[0], VSS_Y, st[2], st[1])
            stub(inb, m.strip_x(1), m.strip(1)[3])
            stub(xown, gc[0], gc[1] + 0.15)
            # -- latch NMOS 1: D = qq, G = inb, S = vss ; latch NMOS 2: D = qq, G = qqb, S = vss
            for key, gnet in (('l1', inb), ('l2', qqb)):
                m, gc = self.nmos(side, X(OXN[key], 0.81, side), 1.5, 0.13, 1)
                st = m.strip(0)
                D.box('M1', st[0], VSS_Y, st[2], st[1])
                stub(qq, m.strip_x(1), m.strip(1)[3])
                stub(gnet, gc[0], gc[1] + 0.15)

        def clear(x, net):
            # pad (0.30) to stub (0.16) spacing 0.18 -> centre distance 0.41; exact overlap of the
            # same net is fine (identical vias merge)
            for xs, n in nstubs:
                d = abs(x - xs)
                if d < 0.42 and not (n == net and d < 0.005):
                    return False
            return True

        def place_pmos(prev, dnet, gnet, ddown=True):
            ox = max(0.3, prev + 1.5)
            while ox < 20.0:
                if (not ddown or clear(ox + 0.66, dnet)) and clear(ox + 1.11, gnet):
                    return round(ox, 3)
                ox = round(ox + 0.01, 3)
            raise RuntimeError('no PMOS position')
        # PMOS positions from the right-half nets (the left half is the exact mirror)
        PM = (('pre2', 3.0, 'xq', 'clk'), ('pre1', 6.0, 'yn', 'clk'), ('cc', 3.0, 'yn', 'xn'),
              ('inv', 1.0, 'ynb', 'yn'))
        oxp = []
        prev = -1.0
        for key, w, dnet, gnet in PM:
            prev = place_pmos(prev, dnet, gnet)
            oxp.append(prev)
        ox1 = place_pmos(prev, None, 'ynb', ddown=False)
        ox2 = place_pmos(ox1, 'q', 'qb')
        for side in (+1, -1):
            own, oth = ('xq', 'xp') if side > 0 else ('xp', 'xq')
            xown, xoth = ('yn', 'xn') if side > 0 else ('xn', 'yn')
            inb = 'ynb' if side > 0 else 'xnb'
            qq, qqb = ('q', 'qb') if side > 0 else ('qb', 'q')
            # -- PMOS row: precharge 2 (3/0.13: D = own, G = clk), precharge 1 (6/0.13: D = xown, G = clk),
            #    cross-coupled (3/0.13: D = xown, G = xoth), inverter P (1/0.13: D = inb, G = xown),
            #    latch P1 (4/0.13: S = vdd, D = n, G = inb), latch P2 (4/0.13: S = n, D = qq, G = qqb)
            for (key, w, _, _), ox, dnet, gnet in zip(PM, oxp, (own, xown, xown, inb), ('clk', 'clk', xoth, xown)):
                m, gc = self.pmos(side, X(ox, 0.81, side), w, 0.13, 1)
                st = m.strip(0)
                D.box('M1', st[0], st[3], st[2], VDD_Y)
                self.track_via(dnet, m.strip_x(1), m.strip(1)[1], False)
                self.track_via(gnet, gc[0], gc[1] - 0.15, False)
            m1, gc1 = self.pmos(side, X(ox1, 0.81, side), 4.0, 0.13, 1)
            m2, gc2 = self.pmos(side, X(ox2, 0.81, side), 4.0, 0.13, 1)
            st = m1.strip(0)
            D.box('M1', st[0], st[3], st[2], VDD_Y)
            self.track_via(inb, gc1[0], gc1[1] - 0.15, False)
            self.track_via(qqb, gc2[0], gc2[1] - 0.15, False)
            self.track_via(qq, m2.strip_x(1), m2.strip(1)[1], False)
            # n node: latch P1 drain (strip 1) and latch P2 source (strip 0) joined above the row
            a, b = m1.strip(1), m2.strip(0)
            D.box('M1', a[0], a[3], a[2], YP + 4.45)
            D.box('M1', b[0], b[3], b[2], YP + 4.45)
            D.box('M1', min(a[0], b[0]), YP + 4.25, max(a[2], b[2]), YP + 4.45)
        self.xmax_p = ox2 + 0.81 + 0.6
        self.pmos_ox = oxp + [ox1, ox2]
        xw_n = OXN['l2'] + 0.81 + 0.30 + 0.15 + 0.3     # last NMOS gate pad + margin
        xw = max(xw_n, self.xmax_p) + 0.4                # half width of the device area
        self.xw = xw
        print('cmp: pmos ox', self.pmos_ox, 'xw', xw)
        # ---------------- tracks (Metal2)
        for net, (x1, x2) in self.span.items():
            y = self.TRACK[net]
            D.hwire('M2', x1, x2, y, ext=False)
        # tail bar (Metal2) at y 4.4 between the input pair sources
        D.hwire('M2', -2.94, 2.94, 4.4, ext=False)
        # q / qb / inp / inn pins at the cell edges (Metal2), clk pin at the top centre (Metal3)
        xw = self.xw
        xe_r, xe_l = xw + 1.6, -(xw + 1.6)
        for net, xe in (('q', xe_r), ('qb', xe_l)):
            y = self.TRACK[net]
            x1, x2 = self.span[net]
            D.hwire('M2', x1, xe, y) if xe > 0 else D.hwire('M2', xe, x2, y)
            D.pin('M2', min(xe, xe - (0.6 if xe > 0 else -0.6)), y - 0.3, max(xe, xe - (0.6 if xe > 0 else -0.6)), y + 0.3, net)
        for net, xe in (('inn', xe_r), ('inp', xe_l)):
            gc = self.inpad[net]
            D.hwire('M2', gc[0], xe, gc[1])
            D.pin('M2', min(xe, xe - (0.6 if xe > 0 else -0.6)), gc[1] - 0.3, max(xe, xe - (0.6 if xe > 0 else -0.6)), gc[1] + 0.3, net)
        D.vpad('Via2', 0.0, self.TRACK['clk'], lo='h', hi='v')
        D.vwire('M3', 0.0, self.TRACK['clk'], YP + 8.6)
        D.pin('M3', -0.3, YP + 8.0, 0.3, YP + 8.6, 'clk')
        # ---------------- rails, well, ring
        D.hwire('M1', -xw + 0.3, xw - 0.3, VSS_Y, w=0.30, ext=False)
        xn = self.xmax_p + 0.6
        D.box('NWell', -xn, YP - 0.6, xn, YP + 7.5)
        D.tap_bar(-xn + 0.4, YP + 6.6, xn - 0.4, YP + 6.9, kind='n', m1w=0.30)
        D.hwire('M1', -xn + 0.2, xn - 0.2, VDD_Y, w=0.30, ext=False)
        D.vpad('Via1', 6.0, VDD_Y, hi='v')
        D.vwire('M2', 6.0, VDD_Y, YP + 8.6)
        D.pin('M2', 5.7, YP + 8.0, 6.3, YP + 8.6, 'vdd')
        ring, ext = D.guard_ring(-xw - 1.0, -2.6, xw + 1.0, YP + 8.0, 0.30, kind='p')
        D.box('M1', ring[0] - 0.13, VSS_Y - 0.15, -xw + 0.4, VSS_Y + 0.15)   # rail -> ring
        D.box('M1', xw - 0.4, VSS_Y - 0.15, ring[2] + 0.13, VSS_Y + 0.15)
        D.pin('M1', ring[0] - 0.13, 2.0, ring[0] + 0.13, 4.0, 'vss')
        self.pins = {'inp': (xe_l + 0.3, self.inpad['inp'][1]), 'inn': (xe_r - 0.3, self.inpad['inn'][1]),
                     'q': (xe_r - 0.3, self.TRACK['q']), 'qb': (xe_l + 0.3, self.TRACK['qb']),
                     'clk': (0.0, YP + 8.3), 'vdd': (6.0, YP + 8.3), 'ring': ring}
        D.clean_pcell_markers()
        return self.cell


# ------------------------------------------------------------------- capacitor helper -----
def place_cap(D, w, x, y, tab_side='right'):
    """cmim w x w with the MIM lower-left at (x, y).  Top plate (TopMetal1) leaves through a tab on
    `tab_side` to a TopVia1/Via4/Via3 stack ending on a Metal3 pad; the bottom plate (Metal5) gets
    a tab on the opposite side with a Via4/Via3 stack to Metal3.  Returns ((xt, yt), (xb, yb)):
    the Metal3 pad centres of the top and bottom plate."""
    c = Cmim(D, w, w, x, y)
    x1, y1, x2, y2 = c.mim
    if tab_side == 'right':
        tx, ty = c.top_tab('right', length=2.6, at=y1 + 3.0)
        pt = (tx - 1.0, ty)
        bx = x1 - 0.6 - 1.6
        D.box('M5', bx - 0.5, y1 + 2.5, x1 - 0.6, y1 + 3.5)
        pb = (bx, y1 + 3.0)
    else:
        tx, ty = c.top_tab('left', length=2.6, at=y1 + 3.0)
        pt = (tx + 1.0, ty)
        bx = x2 + 0.6 + 1.6
        D.box('M5', x2 + 0.6, y1 + 2.5, bx + 0.5, y1 + 3.5)
        pb = (bx, y1 + 3.0)
    D.via('TopVia1', pt[0], pt[1])
    D.via('Via4', pt[0], pt[1], padlo=0.66, padhi=0.66)
    D.via('Via3', pt[0], pt[1], padlo=0.66, padhi=0.66)
    D.via('Via4', pb[0], pb[1], padlo=0.66, padhi=0.66)
    D.via('Via3', pb[0], pb[1], padlo=0.66, padhi=0.66)
    return pt, pb, c


# ------------------------------------------------------------------ conditioning divider --
class CondBuilder:
    """g1_cond: ISENSE/2 divider, 10 x rppd 2/76.7 drawn as 20 series segments 2 x 38.35 (LVS
    combines series resistors) in a serpentine at 2.36 um pitch with a dummy segment on each side;
    1 pF cmim (26 x 26) hold capacitor on icmp beside it."""
    SEG = 38.35
    PITCH = 2.36

    def __init__(self, ly, name='g1_cond'):
        self.ly = ly
        self.cell = ly.create_cell(name)
        self.D = Draw(ly, self.cell)

    def build(self):
        D = self.D
        X0, Y0 = 4.0, 4.0
        L = self.SEG
        segs = []
        for i in range(-1, 21):
            x = X0 + i * self.PITCH
            if 0 <= i < 20:
                segs.append(Rppd(D, 2.0, L, x, Y0))
            else:
                # dummy: GatPoly + pSD + SalBlock + ExtBlock + heads, no PolyRes (not a device)
                D.box('GatPoly', x, Y0 - 0.43, x + 2.0, Y0 + L + 0.43)
                D.box('pSD', x - 0.18, Y0 - 0.61, x + 2.18, Y0 + L + 0.61)
                D.box('SalBlock', x - 0.20, Y0, x + 2.20, Y0 + L)
                D.box('ExtBlock', x - 0.18, Y0 - 0.61, x + 2.18, Y0)
                D.box('ExtBlock', x - 0.20, Y0, x + 2.20, Y0 + L)
                D.box('ExtBlock', x - 0.18, Y0 + L, x + 2.18, Y0 + L + 0.61)
                D.box('Cont', x + 0.07, Y0 - 0.36, x + 1.93, Y0 - 0.20)
                D.box('Cont', x + 0.07, Y0 + L + 0.20, x + 1.93, Y0 + L + 0.36)
                D.box('M1', x + 0.02, Y0 - 0.43, x + 1.98, Y0 - 0.13)
                D.box('M1', x + 0.02, Y0 + L + 0.13, x + 1.98, Y0 + L + 0.43)
        # serpentine joints: top between i and i+1 for even i, bottom for odd i
        for i in range(19):
            a, b = segs[i], segs[i + 1]
            if i % 2 == 0:
                D.box('M1', a.head_top[0], a.head_top[1], b.head_top[2], a.head_top[3])
            else:
                D.box('M1', a.head_bot[0], a.head_bot[1], b.head_bot[2], a.head_bot[3])
        # isense: bottom head of segment 0 -> Metal2 -> Metal3 pin at the left edge
        h = segs[0].head_bot
        xi, yi = (h[0] + h[2]) / 2, (h[1] + h[3]) / 2
        D.vpad('Via1', xi, yi, hi='h')
        D.hwire('M2', X0 - 3.5, xi, yi)
        D.vpad('Via2', X0 - 3.0, yi, lo='h', hi='h')
        D.pin('M3', X0 - 4.0, yi - 0.3, X0 - 3.0, yi + 0.3, 'isense')
        # icmp: bottom joint between segments 9 and 10 -> Metal2 -> cap top plate and pin
        h = segs[9].head_bot
        xc, yc = segs[9].head_bot[2] + 0.18, (h[1] + h[3]) / 2
        D.vpad('Via1', xc, yc, hi='h')
        # vss: bottom head of segment 19 -> Metal1 down to the ring
        h = segs[19].head_bot
        xv, yv = (h[0] + h[2]) / 2, (h[1] + h[3]) / 2
        # capacitor to the right of the string, bottom plate on the left side
        cx = X0 + 21 * self.PITCH + 3.5
        pt, pb, c = place_cap(D, 26.0, cx, Y0 + 5.0, tab_side='right')
        # icmp Metal2 from the joint down/right to the cap top plate stack (Metal3 pad) and pin
        D.vwire('M2', xc, yc, Y0 - 2.0)
        D.hwire('M2', xc, pt[0], Y0 - 2.0)
        D.vpad('Via2', pt[0], Y0 - 2.0, lo='h', hi='v')
        D.vwire('M3', pt[0], Y0 - 2.0, pt[1])
        D.hwire('M3', pt[0], pt[0] + 4.0, pt[1])
        D.pin('M3', pt[0] + 3.4, pt[1] - 0.3, pt[0] + 4.0, pt[1] + 0.3, 'icmp')
        # ring (vss) and bottom plate / vss end connections
        x_right = pt[0] + 4.0
        ring, ext = D.guard_ring(X0 - 4.0, Y0 - 3.5, x_right, Y0 + L + 3.0, 0.30, kind='p')
        D.vwire('M1', xv, yv, ring[1], w=0.30)
        D.vwire('M3', pb[0], pb[1], ring[1])
        D.box('M2', pb[0] - 0.15, ring[1] - 0.30, pb[0] + 0.15, ring[1] + 0.30)
        D.vpad('Via2', pb[0], ring[1], lo='s', hi='v')
        D.via('Via1', pb[0], ring[1])
        D.pin('M1', ring[0] - 0.13, Y0 + 10, ring[0] + 0.13, Y0 + 13, 'vss')
        self.pins = {'isense': (X0 - 3.5, yi), 'icmp': (pt[0] + 3.7, pt[1]), 'ring': ring}
        D.clean_pcell_markers()
        return self.cell


# ------------------------------------------------------------------------------ top -------
class TopBuilder:
    """g1_trip: two g1_dac8 side by side at the bottom, the conditioning divider, the two 1 pF hold
    capacitors and the two comparators (mirrored: inn on the left, inp on the right) in a strip
    above, the clock inverter under the north power bars.  Macro conventions as g1_bgr: Metal3 VSS
    bar along the south edge (y 0..2), VDD bar along the north edge (H-2..H), IOVDD bar just inside
    it; signal pins are Metal3 stubs on the west edge (ISENSE, VREF, dac_soft[7:0]) and east edge
    (dac_hard[7:0], cmp_soft, cmp_hard, clk).  Metal4 trunks feed the DAC supply pins.  A p+ guard
    ring (VSS) surrounds the macro; every sub-cell ring is tied to it."""
    W, H = 229.0, 207.0

    def __init__(self, ly):
        self.ly = ly
        self.cell = ly.create_cell('g1_trip')
        self.D = Draw(ly, self.cell)
        self.lef_pins = []

    def edge_pin(self, name, side, y, direction, x1=None):
        """Metal3 pin stub 1.5 x 0.3 at the west/east edge at height y"""
        D = self.D
        W = self.W
        if side == 'W':
            box = (0.0, y - 0.15, 1.5, y + 0.15)
        else:
            box = (W - 1.5, y - 0.15, W, y + 0.15)
        D.pin('M3', box[0], box[1], box[2], box[3], name)
        self.lef_pins.append((name, 'Metal3', box, direction, 'SIGNAL'))
        return box

    def build(self):
        ly, D = self.ly, self.D
        W, H = self.W, self.H
        dac = DacBuilder(ly, name='g1_dac8')
        dac.build()
        cmp = CmpBuilder(ly)
        cmp.build()
        cond = CondBuilder(ly)
        cond.build()
        # ---- placement
        XS, XH, YD = 3.0, 118.0, 8.0                 # DAC origins
        tS = place(self.cell, dac.cell, XS, YD)
        tH = place(self.cell, dac.cell, XH, YD)
        XC, YC = 2.0, 154.0                          # cond origin
        tC = place(self.cell, cond.cell, XC, YC)
        CY = 162.0                                   # comparator NMOS row bottom
        CXS, CXH = 141.7, 208.0                      # comparator centres; cells mirrored in x
        tCS = pya.Trans(2, True, pya.Point(um(CXS), um(CY)))
        tCH = pya.Trans(2, True, pya.Point(um(CXH), um(CY)))
        self.cell.insert(pya.CellInstArray(cmp.cell.cell_index(), tCS))
        self.cell.insert(pya.CellInstArray(cmp.cell.cell_index(), tCH))

        def P(t, p):
            return tpt(t, p[0], p[1])
        # hold capacitors (26 um MIM), top-plate tabs to the left, bottom-plate tabs to the right
        ptS, pbS, cS = place_cap(D, 26.0, 97.5, 158.5, tab_side='left')
        ptH, pbH, cH = place_cap(D, 26.0, 162.5, 158.5, tab_side='left')
        self.cap_boxes = [cS.m5, cH.m5]
        # ---- macro ring
        ring, ext = D.guard_ring(1.0, 1.0, W - 1.0, H - 1.0, 0.30, kind='p')
        # ---- signal levels (Metal3): VREF, icmp, vth above the DACs
        Y_VREF, Y_ICMP, Y_VTH = 152.5, 154.5, 156.5
        Y_VSS, Y_VDD, Y_IOVDD = 1.0, H - 1.0, H - 4.25
        # VREF: west pin -> both DAC vref pins (Metal2 pins at the DAC top, extended up on Metal2)
        vS, vH = P(tS, dac.pins['vref']), P(tH, dac.pins['vref'])
        self.edge_pin('VREF', 'W', Y_VREF, 'INPUT')
        D.hwire('M3', 0.5, vH[0], Y_VREF)
        for v in (vS, vH):
            D.vwire('M2', v[0], v[1], Y_VREF)
            D.vpad('Via2', v[0], Y_VREF, lo='v', hi='h')
        # DAC outputs -> Metal2 risers -> vth lines (Metal3) -> cap top plate and comparator inn
        for t, pt, cmpt in ((tS, ptS, tCS), (tH, ptH, tCH)):
            o = P(t, dac.pins['out'])
            D.vpad('Via2', o[0], o[1], lo='v', hi='v')
            D.vwire('M2', o[0], o[1], Y_VTH)
            D.vpad('Via2', o[0], Y_VTH, lo='v', hi='h')
            inn = P(cmpt, cmp.pins['inn'])
            xs = [pt[0], o[0], inn[0]]
            D.hwire('M3', min(xs), max(xs), Y_VTH)
            D.vwire('M3', pt[0], Y_VTH, pt[1])
            D.vwire('M3', inn[0], Y_VTH, inn[1])
            D.vpad('Via2', inn[0], inn[1], lo='h', hi='v')
        D.label('M3txt', o[0] - 3.0, Y_VTH, 'vth_hard')
        D.label('M3txt', ptS[0] + 3.0, Y_VTH, 'vth_soft')
        # icmp: cond pin (Metal3) -> down to Y_ICMP -> east to both comparator inp pins
        ic = P(tC, cond.pins['icmp'])
        D.vwire('M3', ic[0], ic[1], Y_ICMP)
        D.label('M3txt', ic[0] + 10.0, Y_ICMP, 'icmp')
        inpS, inpH = P(tCS, cmp.pins['inp']), P(tCH, cmp.pins['inp'])
        D.hwire('M3', ic[0], inpH[0], Y_ICMP)
        for inp in (inpS, inpH):
            D.vwire('M3', inp[0], Y_ICMP, inp[1])
            D.vpad('Via2', inp[0], inp[1], lo='h', hi='v')
        # ISENSE: west pin -> cond isense pin
        isn = P(tC, cond.pins['isense'])
        self.edge_pin('ISENSE', 'W', isn[1], 'INPUT')
        D.hwire('M3', 0.5, isn[0], isn[1])
        # comparator outputs q -> Metal2 risers -> Metal3 east to the east-edge pins
        Y_QS, Y_QH, Y_CLK = 194.5, 195.7, 196.9
        for cmpt, name, yl in ((tCS, 'cmp_soft', Y_QS), (tCH, 'cmp_hard', Y_QH)):
            q = P(cmpt, cmp.pins['q'])
            D.vwire('M2', q[0], q[1], yl)
            D.vpad('Via2', q[0], yl, lo='v', hi='h')
            D.hwire('M3', q[0], W - 0.5, yl)
            self.edge_pin(name, 'E', yl, 'OUTPUT')
        # clock: east pin -> Metal3 west to XCLK -> Metal2 down to the Metal3 line at 192 ->
        # cmp_soft clk and the inverter input; inverter output -> Metal3 at 188 -> cmp_hard clk
        XCLK = 172.0
        self.edge_pin('clk', 'E', Y_CLK, 'INPUT')
        D.hwire('M3', XCLK, W - 0.5, Y_CLK)
        D.vpad('Via2', XCLK, Y_CLK, lo='v', hi='h')
        D.vwire('M2', XCLK, Y_CLK, 192.0)
        D.vpad('Via2', XCLK, 192.0, lo='v', hi='h')
        ckS, ckH = P(tCS, cmp.pins['clk']), P(tCH, cmp.pins['clk'])
        D.hwire('M3', ckS[0], XCLK + 4.0, 192.0)
        D.vwire('M3', ckS[0], ckS[1], 192.0)
        # inverter (XCLKI): pmos 1/0.13 above nmos 0.5/0.13, common gate contacted on the left
        XI, YI = 175.0, 185.0
        mp = Mos(D, 'pmos', 1.0, 0.13, 1, XI, YI + 2.0)
        mn = Mos(D, 'nmos', 0.5, 0.13, 1, XI, YI)
        D.box('NWell', XI - 0.9, YI + 1.4, XI + 3.2, YI + 3.6)
        D.box('Activ', XI + 2.0, YI + 2.2, XI + 2.3, YI + 2.7)      # n+ tie (vdd)
        D.cont(XI + 2.15, YI + 2.45)
        D.box('M1', XI + 2.0, YI + 2.2, XI + 2.3, YI + 3.9)
        D.box('Activ', XI + 2.0, YI - 0.5, XI + 2.3, YI + 0.5)      # p+ tie (vss)
        D.box('pSD', XI + 1.97, YI - 0.53, XI + 2.33, YI + 0.53)
        D.cont(XI + 2.15, YI)
        D.box('M1', XI + 2.0, YI - 0.5, XI + 2.3, YI + 0.5)
        g = mn.gate(0)
        D.box('GatPoly', g[0], YI + 0.5, g[2], YI + 2.0 - 0.18)       # gate join between the devices
        D.box('GatPoly', XI - 0.45, YI + 1.0, g[2], YI + 1.5)          # tab to the left
        D.cont(XI - 0.30, YI + 1.25)
        D.vpad('Via1', XI - 0.30, YI + 1.25, hi='v')
        p0, p1 = mp.strip(0), mp.strip(1)
        n0, n1 = mn.strip(0), mn.strip(1)
        D.box('M1', p0[0], p0[3], p0[2], YI + 3.9)
        D.box('M1', XI + 0.07, YI + 3.6, XI + 2.3, YI + 3.9)
        D.vpad('Via1', XI + 1.4, YI + 3.75, hi='v')
        D.vwire('M2', XI + 1.4, YI + 3.75, Y_VDD)
        D.vpad('Via2', XI + 1.4, Y_VDD, lo='v', hi='h')
        D.box('M1', n0[0], YI - 0.5, n0[2], n0[1])
        D.box('M1', XI + 0.07, YI - 0.5, XI + 3.7, YI - 0.2)
        D.vpad('Via1', XI + 3.5, YI - 0.35, hi='v')
        D.vwire('M2', XI + 3.5, YI - 0.35, ring[3])
        D.via('Via1', XI + 3.5, ring[3])
        D.box('M1', p1[0], n1[3], p1[2], p1[1])
        xo = mn.strip_x(1)
        D.vpad('Via1', xo, YI + 1.25, hi='h')
        D.hwire('M2', xo, XI + 3.0, YI + 1.25)
        D.vwire('M2', XI + 3.0, YI + 1.25, 188.0)
        D.vpad('Via2', XI + 3.0, 188.0, lo='v', hi='h')
        D.hwire('M3', XI + 3.0, ckH[0], 188.0)
        D.label('M3txt', XI + 10.0, 188.0, 'cmp_clk_n')
        D.vwire('M3', ckH[0], ckH[1], 188.0)
        D.vwire('M2', XI - 0.30, YI + 1.25, 192.0)
        D.vpad('Via2', XI - 0.30, 192.0, lo='v', hi='h')
        # ---- power bars (Metal3): VSS south edge, VDD north edge, IOVDD inside the north edge
        for y, hw, name, use in ((Y_VDD, 1.0, 'VDD', 'POWER'), (Y_IOVDD, 0.75, 'IOVDD', 'POWER'), (Y_VSS, 1.0, 'VSS', 'GROUND')):
            D.box('M3', 0.0, y - hw, W, y + hw)
            D.box('M3pin', 0.0, y - hw, W, y + hw)
            D.label('M3txt', W / 2 + (20 if name == 'IOVDD' else 0), y, name)
            self.lef_pins.append((name, 'Metal3', (0.0, y - hw, W, y + hw), 'INOUT', use))
        for x in (5.0, 100.0, 114.0, 224.0):                       # VSS bar -> top ring bottom side
            D.box('M2', x - 0.15, ring[1] - 0.30, x + 0.15, ring[1] + 0.30)
            D.vpad('Via2', x, ring[1], lo='s', hi='v')
            D.via('Via1', x, ring[1])
        for t, bar, key in ((tS, Y_VDD, 'vdd'), (tH, Y_VDD, 'vdd'), (tS, Y_IOVDD, 'vdda'), (tH, Y_IOVDD, 'vdda')):
            px = P(t, dac.pins[key])
            D.vpad('Via3', px[0], bar, lo='h', hi='v')
            D.vwire('M4', px[0], bar, px[1] + 2.0, w=0.60)
            D.box('M3', px[0] - 0.15, px[1] + 1.7, px[0] + 0.15, px[1] + 2.3)
            D.vpad('Via3', px[0], px[1] + 2.0, lo='s', hi='v')
            D.vpad('Via2', px[0], px[1] + 2.0, lo='v', hi='s')
            D.vwire('M2', px[0], px[1], px[1] + 2.0)
        for cmpt in (tCS, tCH):                                   # comparator vdd (Metal2 riser)
            v = P(cmpt, cmp.pins['vdd'])
            D.vwire('M2', v[0], v[1], Y_VDD)
            D.vpad('Via2', v[0], Y_VDD, lo='v', hi='h')
        # ---- code pins: west edge (dac_soft) / east edge (dac_hard), Metal3 lines under the DACs,
        #      Metal2 risers to the DAC d pins
        for t, name, side in ((tS, 'dac_soft', 'W'), (tH, 'dac_hard', 'E')):
            for b in range(8):
                px = P(t, dac.pins['d'][b])
                yl = 2.8 + 0.6 * b
                self.edge_pin('%s[%d]' % (name, b), side, yl, 'INPUT')
                if side == 'W':
                    D.hwire('M3', 0.5, px[0], yl)
                else:
                    D.hwire('M3', px[0], W - 0.5, yl)
                D.vpad('Via2', px[0], yl, lo='v', hi='h')
                D.vwire('M2', px[0], yl, px[1])
        # ---- sub-cell rings to the top ring; cap bottom plates to the VSS bar on Metal4
        for t in (tS, tH):
            r = tbox(t, *dac.pins['ring'])
            D.vwire('M1', r[0] + 5.0, r[1], ring[1], w=0.30)
            D.vwire('M1', r[2] - 5.0, r[1], ring[1], w=0.30)
        r = tbox(tC, *cond.pins['ring'])
        D.hwire('M1', ring[0], r[0], r[1] + 10.0, w=0.30)
        for cmpt in (tCS, tCH):
            r = tbox(cmpt, *cmp.pins['ring'])
            D.vwire('M1', (r[0] + r[2]) / 2 + 3.0, r[3], ring[3], w=0.30)
        for pb in (pbS, pbH):
            D.vpad('Via3', pb[0], pb[1], lo='s', hi='v')
            D.vwire('M4', pb[0], pb[1], Y_VSS, w=0.60)
            D.vpad('Via3', pb[0], Y_VSS, lo='v', hi='h')
        # ---- prBoundary and no-fill regions (datatype 23 shapes, honoured by the PDK filler that
        #      fill_macro.sh runs on the macro and by the chip-level filler), 3 um margin:
        #  - DAC bodies (the 530-unit strings and the switch tree between their columns): no Activ/
        #    GatPoly/Metal1-3 fill; Metal4/5 fill above is allowed (static DC tap nodes)
        #  - comparators and the divider cell (matched devices, the icmp hold capacitor): all layers
        #  - hold capacitors with their tabs: no Metal4/5 fill under the Metal5 plates, no TopMetal
        #  - IOVDD bar zone (y 201.5 .. 204): no Metal4/5/TopMetal fill, the chip PDN lands there
        #  - TopMetal1/2 fill is never placed by fill_macro.sh (chip PDN stripes cross the macro)
        D.box('prBoundary', 0.0, 0.0, W, H)
        LOWER = ('Activ_nf', 'GatPoly_nf', 'M1_nf', 'M2_nf', 'M3_nf', 'TM1_nf', 'TM2_nf')
        MAC = (0.0, 0.0, W, H)
        for t in (tS, tH):
            b = tbox(t, dac.X0 - 1.0, dac.Y0 - 1.0, dac.xcol["DR"] + COLP + 1.0, dac.Y0 + NS * RppdUnit.PITCH + 1.0)
            D.nofill(*b, layers=LOWER, clip=MAC)
        bb = cond.cell.dbbox()
        D.nofill(*tbox(tC, bb.left, bb.bottom, bb.right, bb.top), clip=MAC)
        bb = cmp.cell.dbbox()
        for cmpt in (tCS, tCH):
            D.nofill(*tbox(cmpt, bb.left, bb.bottom, bb.right, bb.top), clip=MAC)
        for c in (cS, cH):
            D.nofill(c.m5[0] - 4.0, c.m5[1], c.m5[2] + 4.0, c.m5[3], layers=NOFILL_UPPER, clip=MAC)
        D.nofill(0.0, Y_IOVDD - 1.25, W, Y_IOVDD + 1.25, margin=0.0, layers=NOFILL_UPPER)
        D.clean_pcell_markers()
        return self.cell

    def lef(self, path):
        W, H = self.W, self.H
        # Metal1/2 everywhere, Metal3 inside the pin stubs and bars; Metal4 and above only where
        # the layout has them (the vdd/vdda Metal4 trunks, the MIM capacitors), and never over the
        # VDD (north) and VSS (south) bars so that the chip PDN can land straps on them.  The vdd
        # trunks cross the IOVDD bar on Metal4 (x = 7.5, 122.5) and stay obstructed there.
        # Metal4/Metal5: the interior up to the IOVDD bar zone (3 um inside the west/east/south edges =
        # the fill window of fill_macro.sh, so the areas above the VDD/VSS/IOVDD bars stay free for the
        # chip PDN straps); with the metal fill the interior really is occupied on these layers.  Above
        # 201.5 um only the real Metal4 shapes (the vdd/vdda trunks).  TopMetal1: the capacitors.
        Y_IOVDD = H - 4.25
        bars = [(0.0, 0.0, W, 2.5), (0.0, H - 2.5, W, H)]
        obs = [('Metal1', [(0.0, 0.0, W, H)]), ('Metal2', [(0.0, 0.0, W, H)]),
               ('Metal3', [(1.8, 2.5, W - 1.8, H - 5.3)]),
               ('Metal4', [(3.0, 3.0, W - 3.0, Y_IOVDD - 1.25)]
                + shape_obs(self.cell, 'M4', 0.2, (0.0, Y_IOVDD - 1.25, W, H - 2.5))),
               ('Metal5', [(3.0, 3.0, W - 3.0, Y_IOVDD - 1.25)]),
               ('TopMetal1', shape_obs(self.cell, 'TM1', 0.5, (0.0, 0.0, W, H), bars))]
        print('lef: Metal4 obs', obs[3][1], 'TopMetal1 obs', obs[5][1])
        write_lef(path, 'g1_trip', W, H, self.lef_pins, obs)


def dac_core_cdl(path):
    """CDL of the DAC without level shifters (string + tree), gates dh*/dhn* as ports"""
    lines = ['* g1_dac8 core (string + switch tree) for the layout bring-up',
             '.subckt dac_core vref ' + ' '.join('dh%d dhn%d' % (b, b) for b in range(8)) + ' out vss']
    prev = 'vss'
    for i in range(530):
        nxt = 'vref' if i == 529 else ('t%d' % (i - 254) if 254 <= i <= 509 else 's%d' % i)
        lines.append('RU%d %s %s vss rppd w=4u l=1.2u b=0 m=1' % (i, nxt, prev))
        prev = nxt
    nodes = ['t%d' % k for k in range(256)]
    for b in range(8):
        nxt = []
        for k in range(len(nodes) // 2):
            o = 'out' if b == 7 else 'm%d_%d' % (b, k)
            lines.append('MS%d_%da %s dhn%d %s vss sg13_hv_nmos w=2u l=0.45u m=1' % (b, k, nodes[2 * k], b, o))
            lines.append('MS%d_%db %s dh%d %s vss sg13_hv_nmos w=2u l=0.45u m=1' % (b, k, nodes[2 * k + 1], b, o))
            nxt.append(o)
        nodes = nxt
    lines.append('.ends dac_core')
    open(path, 'w').write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    # klayout -b -r gen_trip_layout.py -rd what=<dac_core|dac|cmp|cond|top> -rd out=<gds path>
    what = globals().get('what', 'top')
    out = globals().get('out', None)
    ly = pya.Layout()
    ly.dbu = 0.001
    if what == 'dac_core':
        b = DacBuilder(ly, name='dac_core', with_shifters=False)
        cell = b.build()
        write_gds(ly, out or 'dac_core.gds')
        dac_core_cdl((out or 'dac_core.gds').replace('.gds', '.cdl'))
        print('wrote', out, cell.dbbox())
    elif what == 'dac':
        b = DacBuilder(ly, name='g1_dac8')
        cell = b.build()
        write_gds(ly, out or 'g1_dac8.gds')
        print('wrote', out, cell.dbbox())
    elif what == 'cmp':
        b = CmpBuilder(ly)
        cell = b.build()
        write_gds(ly, out or 'g1_cmp.gds')
        print('wrote', out, cell.dbbox())
    elif what == 'cond':
        b = CondBuilder(ly)
        cell = b.build()
        write_gds(ly, out or 'g1_cond.gds')
        print('wrote', out, cell.dbbox())
    elif what == 'top':
        b = TopBuilder(ly)
        cell = b.build()
        write_gds(ly, out or 'g1_trip.gds')
        b.lef((out or 'g1_trip.gds').replace('.gds', '.lef'))
        print('wrote', out, cell.dbbox())
