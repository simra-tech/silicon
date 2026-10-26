#!/usr/bin/env python3
"""Drawing helpers for the r1_adc layout generator (KLayout 0.30.9 batch Python, pinned container).
Block, MOS rows and MIM helpers follow r1_afe/layout/r1_afe_layout.py (revision E2): device terminals become router pins
on a 0.8 um grid (maze_router.py, Metal2-Metal4); every connection is drawn by the router from the netlist.
New here: LV devices (nmos/pmos PCells, l = 0.13 um gate heads widened to 0.30 um for Cnt.g), rows with one bulk net
per segment (NWell islands for vref, vrefl and the bootstrap nodes cbp), rectangular MIM with a TopMetal1 tab."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'g1-guardian', 'blocks', 'g1_sense', 'layout'))
from g1_layout_lib import *   # noqa  (pya, LIB, Draw, Mos, um, CONT, VIA, TV1, TV1_M5, LAYERS ...)
from maze_router import Router, P, LNAME


def gceil(v):
    return round(math.ceil(v / P - 1e-6) * P, 4)


def gfloor(v):
    return round(math.floor(v / P + 1e-6) * P, 4)


def gnear(v):
    return round(round(v / P) * P, 4)


def gpts(a, b):
    out, x = [], gceil(a)
    while x <= b + 1e-6:
        out.append(round(x, 4)); x += P
    return out


def s5(v):
    return round(round(v / 0.005) * 0.005, 4)


PCELL = {'nmos': 'nmos', 'pmos': 'pmos', 'nmosHV': 'nmosHV', 'pmosHV': 'pmosHV'}


class Block:
    def __init__(self, ly, name, W, H):
        self.ly = ly
        self.name = name
        self.cell = ly.create_cell(name)
        self.D = Draw(ly, self.cell)
        self.W, self.H = W, H
        self.R = Router(0.0, 0.0, int(round(W / P)) + 1, int(round(H / P)) + 1)
        self.m1pins = {}
        self.grails = []
        self.stats = {}
        self.ports = []
        self.devpos = {}
        self.straps4 = []      # pre-drawn Metal4 straps (net, x1, y1, x2, y2)
        self.extra = []        # (layer, x1, y1, x2, y2) drawn after routing

    def L(self, name):
        return self.ly.layer(*LAYERS[name])

    def box(self, layer, x1, y1, x2, y2):
        self.D.box(layer, x1, y1, x2, y2)

    def pin(self, net, nodes, kind='m2'):
        pin = self.R.add_pin(net, nodes)
        if kind == 'm1':
            for (l, i, j) in pin:
                self.m1pins[(i, j)] = net
        return pin

    def port(self, dev, term, net, layer, box=None, pt=None):
        self.ports.append(dict(dev=dev, term=term, net=net, layer=layer,
                               box=[round(v, 4) for v in box] if box else None, pt=[round(v, 4) for v in pt] if pt else None))

    # ---- MOS ------------------------------------------------------------------------------------------
    def mos(self, d, x0, yg):
        kind = PCELL[d['kind']]
        w, l, ng = round(d['w'], 3), round(d['l'], 3), d['ng']
        y0 = round(yg + 0.33, 4)
        m = Mos(self.D, kind, w, l, ng, x0, y0)
        Dn, Gn, Sn, Bn = d['nets']
        gl, gr = m.gx(0) - 0.20, m.gx(ng - 1) + 0.20
        xs = gpts(gl + 0.2, gr - 0.2)
        er = 0.0
        if not xs:
            t = gceil(gl + 0.2); er = t + 0.2 - gr; xs = [t]
        rl, rr, ra, rb = m.gate_bar('bot', ext=(0.0, er))
        if l < 0.30:      # widen the poly bar so every gate contact has 0.07 um poly around it (Cnt.g)
            self.box('GatPoly', m.gx(0) - 0.15, m.yd('bot', 0.48), m.gx(ng - 1) + 0.15, m.yd('bot', 0.18))
        if m.wf < 0.30 - 1e-9:  # dogbone PCell (W < 0.3): its poly ends 0.18 below the narrow channel, not the pads
            for k in range(ng):
                self.box('GatPoly', m.gx(k) - l / 2, m.yd('bot', 0.20), m.gx(k) + l / 2, y0 + 0.05)
        self.box('M2', rl, yg - 0.20, rr, yg + 0.20)
        self.grails.append((Gn, rl, rr, yg))
        self.R.reserve(0, rl, yg - 0.20, rr, yg + 0.20, Gn)
        self.pin(Gn, [(0, x, yg) for x in xs], 'm2')
        right = max(m.x1 + 0.2 + l, rr)
        kmax = int(math.ceil((0.33 + m.wf + 0.5) / P - 1e-6))
        yd = round(yg + kmax * P, 4)
        dt = yd - (y0 + m.wf)
        for side, strips, lo, hi, yc, net, term in (('bot', m.strips(0), 0.88, 1.38, yg - P, Sn, 2),
                                                     ('top', m.strips(1), dt - 0.25, dt + 0.25, yd, Dn, 0)):
            xl, xr = m.sx(strips[0]) - 0.13, m.sx(strips[-1]) + 0.13
            xs = gpts(xl + 0.2, xr - 0.2)
            er = 0.0
            if not xs:
                t = gceil(xl + 0.2); er = t + 0.2 - xr; xs = [t]
            rb_ = m.rail(side, strips, ext=(0.0, er), lo=lo, hi=hi)
            self.port(d['name'], term, net, 1, box=(rb_[0], rb_[2], rb_[1], rb_[3]))
            self.pin(net, [(0, x, yc) for x in xs], 'm1')
            right = max(right, xr + er)
        m.end_dummies()
        self.devpos[d['name']] = (m.x0, m.y0, m.x1, m.y1)
        return m, right, yd

    @staticmethod
    def dev_width(d):
        l, ng = d['l'], d['ng']
        act = ng * (l + 0.38) + 0.30
        return act + 2 * (0.2 + l + 0.35) + 0.6

    def seg_width(self, devs):
        return sum(self.dev_width(d) for d in devs)

    def row(self, segs, yg, kind):
        """one row of devices at gate-rail y yg. segs: [dict(x0, devs, bulk)]; kind 'n' / 'p' (LV) or 'nHV' / 'pHV'.
        Each segment gets its own tie strip (bulk net) under it and, for PMOS, its own NWell. Returns top y."""
        ydmax = yg
        out = []
        for sg in segs:
            x = sg['x0']
            placed = []
            for d in sg['devs']:
                x0 = round(x + 0.2 + d['l'] + 0.35, 2)
                m, right, yd = self.mos(d, x0, yg)
                placed.append(m)
                ydmax = max(ydmax, yd)
                x = right + 0.5
            out.append((sg, placed, sg['x0'], x))
        yt = round(yg - 2 * P, 4)
        ptap = kind.startswith('n')
        for sg, placed, xa, xb in out:
            self.D.tap_strip(xa, xb, yt, ptype=ptap, w=0.30, inset=0.2)
            self.pin(sg['bulk'], [(0, xx, yt) for xx in gpts(xa + 0.4, xb - 0.4)], 'm1')
            y_lo = min(m.y0 for m in placed); y_hi = max(m.y1 for m in placed)
            ma = min(m.x0 for m in placed); mb = max(m.x1 for m in placed)
            if not ptap:
                self.box('pSD', ma - 0.18, y_lo - 0.40, mb + 0.18, y_hi + 0.40)
                self.box('NWell', xa - 0.8, yt - 0.8, xb + 0.8, ydmax + 0.6)
            if kind.endswith('HV'):
                self.box('TGO', xa - 0.8, yt - 0.8, xb + 0.8, ydmax + 0.8)
            sg['xend'] = xb
        return ydmax, yt

    # ---- MIM ------------------------------------------------------------------------------------------
    def mim_rect(self, name, w, l, mx, my, top, bot, tab='E', vias_bot=1):
        """MIM w x l at (mx, my); top plate: TopMetal1 tab on side `tab` to a TopVia1 on a Metal5 island, Via4 to a
        Metal4 router pin; bottom plate: Via4 under the MIM centre (vias_bot x vias_bot nodes) to Metal4 router pins."""
        self.D.pcell('cmim', {'Calculate': 'C', 'w': '%gu' % w, 'l': '%gu' % l}, mx, my)
        if tab == 'E':
            xt = gceil(mx + w + 1.25); yt = gnear(my + l / 2)
            self.box('TM1', mx + w / 2, yt - 0.82, xt + 0.82, yt + 0.82)
        elif tab == 'W':
            xt = gfloor(mx - 1.25); yt = gnear(my + l / 2)
            self.box('TM1', xt - 0.82, yt - 0.82, mx + w / 2, yt + 0.82)
        elif tab == 'N':
            xt = gnear(mx + w / 2); yt = gceil(my + l + 1.25)
            self.box('TM1', xt - 0.82, my + l / 2, xt + 0.82, yt + 0.82)
        else:
            xt = gnear(mx + w / 2); yt = gfloor(my - 1.25)
            self.box('TM1', xt - 0.82, yt - 0.82, xt + 0.82, my + l / 2)
        self.D.sq('TV1', xt, yt, TV1)
        self.D.sq('M5', xt, yt, TV1 + 2 * TV1_M5)
        self.D.sq('Via4', xt, yt, VIA)
        self.D.sq('M4', xt, yt, 0.40)
        self.pin(top, [(2, xt, yt)], 'm4')
        self.port(name, 0, top, 4, pt=(xt, yt))
        nodes = []
        xc, yc = mx + w / 2, my + l / 2
        k = vias_bot
        for a in range(k):
            for b in range(k):
                x = gnear(xc + (a - (k - 1) / 2) * 2 * P); y = gnear(yc + (b - (k - 1) / 2) * 2 * P)
                self.D.sq('Via4', x, y, VIA); self.D.sq('M4', x, y, 0.40)
                nodes.append((2, x, y))
        self.pin(bot, nodes, 'm4')
        self.port(name, 1, bot, 4, pt=(nodes[0][1], nodes[0][2]))
        return (xt, yt)

    # ---- output -----------------------------------------------------------------------------------------
    def draw_routes(self):
        for kind, net, ln, x1, y1, x2, y2 in self.R.shapes():
            self.box(ln, x1, y1, x2, y2)
        for kind, net, ln, x1, y1, x2, y2 in self.R.fat_shapes():
            self.box(ln, x1, y1, x2, y2)
        for k in list(self.R.paths):
            for (l, i, j) in self.R.used_nodes(k):
                if l == 0 and (i, j) in self.m1pins:
                    x, y = self.R.xy(i, j)
                    self.D.sq('Via1', x, y, VIA)
                    self.D.sq('M1', x, y, 0.34)
                    self.D.sq('M2', x, y, 0.40)
        for (net, x1, x2, yr) in self.grails:
            k = self.R.nets.get(net)
            if k is None:
                continue
            for (l, i, j) in self.R.used_nodes(k):
                x, y = self.R.xy(i, j)
                if l != 0 or abs(y - yr) > 1e-6:
                    continue
                if 0 < x1 - (x + 0.2) < 0.3:
                    self.box('M2', x + 0.2 - 0.01, yr - 0.2, x1 + 0.01, yr + 0.2)
                elif 0 < (x - 0.2) - x2 < 0.3:
                    self.box('M2', x2 - 0.01, yr - 0.2, x - 0.2 + 0.01, yr + 0.2)
        for (net, x1, y1, x2, y2) in self.straps4:
            self.box('M4', x1, y1, x2, y2)
        for (ln, x1, y1, x2, y2) in self.extra:
            self.box(ln, x1, y1, x2, y2)
        for k, paths in self.R.paths.items():
            if not paths:
                continue
            net = self.R.names[k]
            n = sorted(self.R.used_nodes(k))[0]
            x, y = self.R.xy(n[1], n[2])
            self.D.label(LNAME[n[0]] + 'txt', x, y, net.split('@')[0], 0.1)
