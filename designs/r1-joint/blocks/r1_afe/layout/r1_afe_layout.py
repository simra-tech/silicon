#!/usr/bin/env python3
"""r1_afe layout generator (revision E netlist): KLayout 0.30.9 batch Python in the pinned container.

  G1_WORKDIR=designs/r1-joint/blocks/r1_afe/layout flow/run.sh klayout -b -r r1_afe_layout.py
  writes r1_afe.gds (top cell r1_afe, one child cell r1_afe_ch placed twice), r1_afe_lvs.cdl,
  r1_afe_layout.json (bounding box, pins, router statistics).

Method (G1 practice, designs/g1-guardian/blocks/g1_sense/layout): PDK PCells (pmosHV, nmosHV, cmim) and
an rppd body copied from the PDK PCell, drawn by Python; helpers from g1_layout_lib.py (read only).
New here: a grid maze router (maze_router.py) on Metal2-Metal4 does all signal and supply wiring, so the
layout connectivity is generated from the netlist and checked independently by the PDK LVS deck.

Structure:
  r1_afe_ch  one channel (both stages, gain switches, anti-alias filters, CMFB, bias mirrors):
             resistor array at the bottom (rppd w = 1 um, unit columns, poly dummy columns at both ends,
             P/N interleaved), NMOS rows, PMOS rows (one NWell), every row with its own tie strip,
             MIM units on Metal5/TopMetal1 over the resistors and the transistors (cut C6),
             ports on the channel edge (Metal3).
  r1_afe     sine channel (south), VCM1 divider and its capacitor, cosine channel (north) as a translated
             copy (same orientation), east routing strip, p+ guard ring, pins on Metal3 at the boundary.
Revision E2 (2026-10-21): MIM plate orientation from r1_afe_netlist.orient() (CM-sense caps with the bottom plate on
the OTA output, the output cap XCOD with alternating units); the P/N pairs and the CM-sense nets are routed first
(CH_FIRST, TOP_FIRST, locked against rip-up); after routing, each pair is balanced per routing layer with dead-end
trim stubs on the shorter net (Router.add_stub), plus an optional extra trim from a JSON file (-rd trim=<file>,
from the extraction of the previous iteration). Device-terminal port positions and per-net wire statistics are
written to r1_afe_ports.json (input of pex/pex_rc_build.py).
Layers: no TopMetal2 anywhere; TopMetal1 only on the MIM top plates and their 1.64 um tabs (the PDK MIM
has its top plate on TopMetal1); boundary on 189/4 only.
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'g1-guardian', 'blocks', 'g1_sense', 'layout'))
from g1_layout_lib import *   # noqa  (pya, LIB, Draw, Mos, new_layout, write_gds, CONT, ...)
import r1_afe_netlist as NLM
from maze_router import Router, P, LNAME

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass
OUT = globals().get('out', os.path.join(HERE, 'r1_afe.gds'))
ROUTE_ROUNDS = int(globals().get('rounds', '6'))
TRIM = json.load(open(globals()['trim'])) if globals().get('trim') else {}
LOCK = globals().get("lock", "0") == "1"
BALANCE = globals().get('balance', '1') == '1'
STRAPS = globals().get('straps', '1') == '1'     # E2: Metal5 supply straps in the east strip (build_top)
WIDEN = globals().get('widen', '1') == '1'       # E2: widen vdd/vss after routing (Router.widen)
TOP_HALO = int(globals().get('tophalo', '40'))
VDDGRID = globals().get('vddgrid', '1') == '1'   # E3: channel vdd grid (Metal5 plate, Metal4 row buses and trunk)
VSSGRID = globals().get('vssgrid', '1') == '1'   # E3 (revision F): channel vss grid (Metal4 NMOS row buses and trunk)
TRUNK_ALL = globals().get('trunkall', '1') == '1'  # E3 final: grid trunks over all bus rows; vss trunk down to the east vss pin
ISLANDFIX = globals().get('islandfix', '1') == '1'  # E3 final (dev11): drop grid segments with no path up to the plate or trunk
JUMPERS = globals().get('jumpers', '1') == '1'  # E4 (revision F1): Metal4 jumpers from a vdd row bus without plate cover to the bus of the next row
VSSMESH = globals().get('vssmesh', '1') == '1'  # layout E4 iteration 2 (layout-e4-dev13x): Metal4 jumpers between adjacent vss row buses every 16 um; -rd vssmesh=0 gives E4-dev12b
# P/N pairs of the channel and of the top level, balanced per layer after routing
CH_PAIRS = [('outp', 'outn'), ('op2', 'on2'), ('m1p', 'm1n'), ('x1p', 'x1n'), ('x2p', 'x2n'), ('inp', 'inn')]
CH_FIRST = ['xa1_vcms', 'xa2_vcms'] + [n for pr in CH_PAIRS for n in pr]
TOP_PAIRS = [('souts_p', 'souts_n'), ('soutc_p', 'soutc_n'), ('sinp', 'sinn'), ('cosp', 'cosn')]
TOP_FIRST = [n for pr in TOP_PAIRS for n in pr]


def gceil(v):
    return round(math.ceil(v / P - 1e-6) * P, 4)


def gfloor(v):
    return round(math.floor(v / P + 1e-6) * P, 4)


def gpts(a, b):
    out, x = [], gceil(a)
    while x <= b + 1e-6:
        out.append(round(x, 4)); x += P
    return out


def s5(v):
    return round(round(v / 0.005) * 0.005, 4)


# ------------------------------------------------------------------------------------------------
# rppd body: the PDK PCell geometry at l = 10 um, stretched to any length (the PCell rounds some lengths
# to 3 significant digits, e.g. 153.85 -> 154, so it is not used directly)
_RPPD = None


def rppd_template():
    global _RPPD
    if _RPPD is None:
        pcv = LIB.layout().add_pcell_variant(LIB.layout().pcell_id('rppd'), {'Calculate': 'R', 'w': '1u', 'l': '10u', 'b': 0})
        c = LIB.layout().cell(pcv)
        shapes = []
        for li in LIB.layout().layer_indexes():
            info = LIB.layout().get_info(li)
            if info.datatype not in (0,) or info.layer == 63:
                continue
            for s in c.shapes(li).each():
                if s.is_text():
                    continue
                b = s.bbox()
                shapes.append(((info.layer, info.datatype), b.left / 1000, b.bottom / 1000, b.right / 1000, b.top / 1000))
        _RPPD = shapes
    return _RPPD


class Block:
    """drawing + pin bookkeeping for one cell and its router."""

    def __init__(self, ly, name, W, H):
        self.ly = ly
        self.cell = ly.create_cell(name)
        self.D = Draw(ly, self.cell)
        self.W, self.H = W, H
        self.R = Router(0.0, 0.0, int(round(W / P)) + 1, int(round(H / P)) + 1)
        self.m1pins = {}     # (i, j) -> net : Metal2 node whose Via1 + Metal1 pad is drawn when used
        self.m5pins = {}     # (i, j) -> net : Metal4 node under a Metal5 strap; Via4 drawn when used (E2)
        self.straps = []
        self.labels = {}
        self.grails = []     # (net, x1, x2, y): gate rails, bridged to router pads closer than 0.3 um
        self.stats = {}
        self.ports = []      # device-terminal ports for the RC extraction: dict(dev, term, net, layer, box|pt)

    def port(self, dev, term, net, layer, box=None, pt=None):
        self.ports.append(dict(dev=dev, term=term, net=net, layer=layer,
                               box=[round(v, 4) for v in box] if box else None, pt=[round(v, 4) for v in pt] if pt else None))

    def L(self, name):
        return self.ly.layer(*LAYERS[name])

    def box(self, layer, x1, y1, x2, y2):
        self.D.box(layer, x1, y1, x2, y2)

    def m2fixed(self, x1, y1, x2, y2, net):
        self.R.reserve(0, x1, y1, x2, y2, net)

    def pin(self, net, nodes, kind):
        pin = self.R.add_pin(net, nodes)
        if kind == 'm1':
            for (l, i, j) in pin:
                self.m1pins[(i, j)] = net
        return pin

    # ---- MOS ---------------------------------------------------------------------------------------
    def mos(self, d, x0, yg):
        kind = 'nmosHV' if d['kind'] == 'nmos' else 'pmosHV'
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
        self.box('M2', rl, yg - 0.20, rr, yg + 0.20)      # rail as tall as the router pads (no 0.01 um jogs)
        self.grails.append((Gn, rl, rr, yg))
        ra, rb = yg - 0.20, yg + 0.20
        self.m2fixed(rl, ra, rr, rb, Gn)
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
        return m, right, yd

    # ---- rows of transistors --------------------------------------------------------------------------
    def rows(self, rows, x_start, y_start, ptype_from):
        """rows: list of (kind, [devices]); rows with index >= ptype_from are PMOS. Returns geometry info."""
        info = []
        yg = gceil(y_start + 2 * P + 0.6)
        xmin_all, xmax_all = 1e9, -1e9
        nblock, pblock = None, None
        prev_top = None
        for r, (kind, devs) in enumerate(rows):
            if r == ptype_from and prev_top is not None:
                yg = gceil(prev_top + 4 * P)
            x = x_start
            placed = []
            ydmax = yg
            for d in devs:
                x0 = round(x + 0.2 + d['l'] + 0.35, 2)
                m, right, yd = self.mos(d, x0, yg)
                placed.append(m)
                ydmax = max(ydmax, yd)
                x = right + 0.2 + d['l'] + 0.35 - (0.2 + d['l']) + 0.15
            xr = x
            yt = round(yg - 2 * P, 4)
            ptap = r < ptype_from
            # tie strip under the row (contacts all along: LU.c/LU.d)
            self.D.tap_strip(x_start, xr, yt, ptype=ptap, w=0.30, inset=0.2)
            self.pin('vss' if ptap else 'vdd', [(0, xx, yt) for xx in gpts(x_start + 0.4, xr - 0.4)], 'm1')
            if not ptap:
                y_lo = min(m.y0 for m in placed); y_hi = max(m.y1 for m in placed)
                xa = min(m.x0 for m in placed); xb = max(m.x1 for m in placed)
                self.box('pSD', xa - 0.18, y_lo - 0.40, xb + 0.18, y_hi + 0.40)
            info.append(dict(row=r, kind=kind, yg=yg, yt=yt, yd=ydmax, x0=x_start, x1=xr, n=len(devs),
                             ymin_act=min(m.y0 for m in placed), ymax_act=max(m.y1 for m in placed)))
            xmin_all, xmax_all = min(xmin_all, x_start), max(xmax_all, xr)
            prev_top = ydmax
            yg = gceil(ydmax + 3 * P)
        # thick gate oxide over every row, one NWell over the PMOS rows
        ylo = info[0]['yt'] - 0.8
        yhi = info[-1]['yd'] + 0.8
        self.box('TGO', xmin_all - 0.8, ylo, xmax_all + 0.8, yhi)
        pr = [i for i in info if i['row'] >= ptype_from]
        if pr:
            self.box('NWell', xmin_all - 1.0, pr[0]['yt'] - 1.0, xmax_all + 1.0, pr[-1]['yd'] + 1.0)
        return info, (xmin_all, xmax_all, ylo, yhi)

    # ---- resistor array ---------------------------------------------------------------------------------
    def rcolumn_geom(self):
        pass

    def resistor_array(self, groups, x_start, y_b, dummies=2):
        """groups: list of dict(slots=[L1, L2, ...] (bottom to top body lengths), cols=[[seg or None per slot], ...]).
        seg = (dev, flip) with dev a split rppd device; consecutive columns of one resistor are strapped.
        Returns (x_end, y_top)."""
        tmpl = rppd_template()
        x = gceil(x_start + 0.5) - 0.5
        ytop_all = y_b
        colpos = []
        for gi, g in enumerate(groups):
            # slot offsets
            offs, y = [], y_b
            for k, L in enumerate(g['slots']):
                if k > 0:
                    prev_top = offs[-1] + g['slots'][k - 1]
                    pin_top = gceil(prev_top + 0.75)
                    y = s5(pin_top + P + 0.75)
                    while gfloor(y - 0.75) < pin_top + P - 1e-6:
                        y = s5(y + 0.05)
                offs.append(round(y, 4))
            if gi > 0:
                x = round(x + 0.8, 4)
            cols = list(g['cols'])
            if gi == 0:
                cols = [[None] * len(g['slots'])] * dummies + cols
            if gi == len(groups) - 1:
                cols = cols + [[None] * len(g['slots'])] * dummies
            xs0 = x
            for c, col in enumerate(cols):
                xc = round(x, 4)
                for k, seg in enumerate(col):
                    ys, L = offs[k], g['slots'][k]
                    if seg is None:
                        self.box('GatPoly', xc, ys + 0.25, xc + 1.0, ys + L - 0.25)
                        continue
                    for (lay, x1, y1, x2, y2) in tmpl:
                        if y2 <= 5.0 + 1e-6:
                            pass
                        elif y1 >= 5.0 - 1e-6:
                            y1 += L - 10.0; y2 += L - 10.0
                        else:
                            y2 += L - 10.0
                        self.cell.shapes(self.ly.layer(*lay)).insert(pya.Box(um(xc + x1), um(ys + y1), um(xc + x2), um(ys + y2)))
                    colpos.append((seg, xc, ys, L))
                x = round(x + 1.6, 4)
            xe = x - 1.6 + 1.0
            for k, L in enumerate(g['slots']):
                ys = offs[k]
                self.box('SalBlock', xs0 - 0.2, ys, xe + 0.2, ys + L)
                self.box('pSD', xs0 - 0.18, ys - 0.61, xe + 0.18, ys + L + 0.61)
                self.box('EXTBlock', xs0 - 0.2, ys - 0.61, xe + 0.2, ys + L + 0.61)
                # no Metal2 over the bodies
                self.R.block_area([0], xs0 - 0.4, ys + 0.3, xe + 0.4, ys + L - 0.3)
                ytop_all = max(ytop_all, ys + L)
            x = round(x + 0.0, 4)
        # ends, straps and pins
        bydev = {}
        for (seg, xc, ys, L) in colpos:
            bydev.setdefault(seg['orig'], []).append((seg, xc, ys, L))
        for orig, segs in bydev.items():
            segs.sort(key=lambda t: t[0].get('seg', 0))
            n = len(segs)
            for q, (seg, xc, ys, L) in enumerate(segs):
                na, nb = seg['nets'][0], seg['nets'][1]
                # orientation: even segments a at the bottom, odd ones a at the top
                bot, top = (na, nb) if q % 2 == 0 else (nb, na)
                for where, net in (('bot', bot), ('top', top)):
                    strapped = None
                    if q + 1 < n and net == segs[q + 1][0]['nets'][0]:
                        strapped = segs[q + 1]
                    elif q > 0 and net == segs[q - 1][0]['nets'][1]:
                        strapped = 'prev'
                    if strapped is not None:
                        if strapped != 'prev':
                            xn = strapped[1]
                            yh = (ys - 0.43, ys - 0.13) if where == 'bot' else (ys + L + 0.13, ys + L + 0.43)
                            self.box('M1', min(xc, xn) + 0.02, yh[0], max(xc, xn) + 0.98, yh[1])
                            self.D.label('M1txt', (xc + xn) / 2 + 0.5, (yh[0] + yh[1]) / 2, net, 0.1)
                        continue
                    xp = round(xc + 0.5, 4)
                    if where == 'bot':
                        yp = gfloor(ys - 0.75)
                        self.box('M1', xp - 0.17, yp - 0.17, xp + 0.17, ys - 0.13)
                    else:
                        yp = gceil(ys + L + 0.75)
                        self.box('M1', xp - 0.17, ys + L + 0.13, xp + 0.17, yp + 0.17)
                    self.port(seg['name'], 0 if net == na else 1, net, 1, pt=(xp, yp))
                    self.pin(net, [(0, xp, yp)], 'm1')
        return x, ytop_all

    # ---- MIM -------------------------------------------------------------------------------------------
    def mim(self, d, mx, my):
        s = round(d['w'], 3)
        self.D.pcell('cmim', {'Calculate': 'C', 'w': '%gu' % s, 'l': '%gu' % s}, mx, my)
        top, bot = d['nets'][0], d['nets'][1]
        # top plate: TopMetal1 tab east to a TopVia1 on a Metal5 island, Via4 down to the Metal4 pin node
        xt = gceil(mx + s + 1.2); yt = gfloor(my + s / 2)
        self.box('TM1', mx + s / 2, yt - 0.82, xt + 0.82, yt + 0.82)   # from the plate centre (the PCell top plate inset depends on the size)
        self.D.sq('TV1', xt, yt, TV1)
        self.D.sq('M5', xt, yt, TV1 + 2 * TV1_M5)
        self.D.sq('Via4', xt, yt, VIA)
        self.D.sq('M4', xt, yt, 0.40)
        self.pin(top, [(2, xt, yt)], 'm4')
        self.port(d['name'], 0, top, 4, pt=(xt, yt))
        # bottom plate: Metal5 tab south, Via4 to the Metal4 pin node
        xb = gfloor(mx + s / 2); yb = gfloor(my - 1.5)
        self.box('M5', xb - 0.31, yb - 0.31, xb + 0.31, my - 0.3)
        self.D.sq('Via4', xb, yb, VIA)
        self.D.sq('M4', xb, yb, 0.40)
        self.pin(bot, [(2, xb, yb)], 'm4')
        self.port(d['name'], 1, bot, 4, pt=(xb, yb))

    # ---- output ------------------------------------------------------------------------------------------
    def draw_routes(self):
        lay = {'M2': 'M2', 'M3': 'M3', 'M4': 'M4', 'Via2': 'Via2', 'Via3': 'Via3'}
        for kind, net, ln, x1, y1, x2, y2 in self.R.shapes():
            self.box(lay[ln], x1, y1, x2, y2)
        for kind, net, ln, x1, y1, x2, y2 in self.R.fat_shapes():
            self.box(lay[ln], x1, y1, x2, y2)
        # Via1 + Metal1 pad on every used Metal1-type pin node
        for k in list(self.R.paths):
            for (l, i, j) in self.R.used_nodes(k):
                if l == 0 and (i, j) in self.m1pins:
                    x, y = self.R.xy(i, j)
                    self.D.sq('Via1', x, y, VIA)
                    self.D.sq('M1', x, y, 0.34)
                    self.D.sq('M2', x, y, 0.40)
        # E2: Metal5 straps and the Via4 on every used strap node
        for (net, x1, y1, x2, y2) in self.straps:
            self.box('M5', x1, y1, x2, y2)
        for (net, fx, fy, xc) in getattr(self, 'feet', []):
            xa, xb = fx[0] - 0.2, fx[-1] + 0.2
            ya, yb = fy[0] - 0.2, fy[-1] + 0.2
            self.box('M3', xa, ya, xb, yb)
            self.box('M4', xa, ya, xb, yb)
            self.box('M5', min(xa, xc - 2.4), ya, max(xb, xc + 2.4), yb + 0.4)
            self.box('M5', xc - 2.4, ya, xc + 2.4, [s_ for s_ in self.straps if s_[0] == net][0][2] + 0.1)
            for x in fx:
                for y in fy:
                    self.D.sq('Via3', x, y, VIA)
                    self.D.sq('Via4', x, y, VIA)
        import numpy as _np
        for (net, x1, y1, x2, y2) in self.straps:     # Via4 on every Metal4 node of the net under its own strap
            k = self.R.nets.get(net)
            if k is None:
                continue
            for (i, j) in zip(*_np.nonzero(self.R.occ[2] == k)):
                x, y = self.R.xy(int(i), int(j))
                if x1 + 0.3 <= x <= x2 - 0.3 and y1 + 0.3 <= y <= y2 - 0.3 and self.R.res[2, i, j] in (-1, k):
                    self.D.sq('Via4', x, y, VIA)
                    self.D.sq('M4', x, y, 0.40)
                    self.stats['strap_vias'] = self.stats.get('strap_vias', 0) + 1
        # bridge router pads that end just short of a same-net gate rail (avoids M2.b notches)
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
        # one label per routed net (text datatype 25 on the layer of a node of the net)
        for k, paths in self.R.paths.items():
            if not paths:
                continue
            net = self.R.names[k]
            n = sorted(self.R.used_nodes(k))[0]
            x, y = self.R.xy(n[1], n[2])
            self.D.label(LNAME[n[0]] + 'txt', x, y, net, 0.1)


def route_and_balance(blk, first, pairs, cellname, log=print):
    R = blk.R
    ok = R.route_all(rounds=ROUTE_ROUNDS, log=log, first=first, lock=LOCK)
    if not ok:
        log('%s: locked priority routing failed %s; re-routing without the lock' % (cellname, R.failed))
        for k in list(R.paths):
            R.unroute(k)
        R.lock = set()
        ok = R.route_all(rounds=ROUTE_ROUNDS, log=log, first=first, lock=False)
    before, after, trims = {}, {}, {}
    for a, b in pairs:
        if a not in R.nets or b not in R.nets:
            continue
        ka, kb = R.nets[a], R.nets[b]
        sa, sb = R.net_stats(ka), R.net_stats(kb)
        before[a], before[b] = sa, sb
        if BALANCE and ok:
            for l in range(3):
                d = sa['edges'][l] - sb['edges'][l]
                ls = 1 if l == 0 else l    # no Metal2 stubs (Metal2 notches next to device rails, dev1 M2.b): Metal3
                if d > 0:
                    R.add_stub(kb, ls, d, log=log)
                elif d < 0:
                    R.add_stub(ka, ls, -d, log=log)
    if ok:
        for key, ed in TRIM.items():       # extra trim from the previous extraction: 'cell:net' -> [M2, M3, M4] edges
            c, net = key.split(':')
            if c == cellname and net in R.nets:
                for l, n in enumerate(ed):
                    if n > 0 and l > 0:
                        trims[key] = trims.get(key, [0, 0, 0])
                        trims[key][l] += R.add_stub(R.nets[net], l, int(n), log=log)
    if ok and WIDEN:
        for net in ('vss', 'vdd'):        # E2: supply widening (RC extraction showed 70-140 Ohm supply paths)
            if net in R.nets:
                nb, nv = R.widen(R.nets[net])
                blk.stats.setdefault('widen', {})[net] = dict(boxes=nb, extra_vias=nv)
                log('%s: widened %s: %d boxes, %d extra vias' % (cellname, net, nb, nv))
    for a, b in pairs:
        if a in R.nets and b in R.nets:
            after[a], after[b] = R.net_stats(R.nets[a]), R.net_stats(R.nets[b])
    blk.stats['pairs_before'] = before
    blk.stats['pairs_after'] = after
    blk.stats['trim_placed'] = trims
    return ok


def build_channel(ly, W=400.0, H=600.0):
    devs = NLM.channel_devices()
    by = {d['name']: d for d in devs}
    mos = [d for d in devs if d['kind'] in ('nmos', 'pmos')]
    res = [d for d in devs if d['kind'] == 'rppd']
    caps = [d for d in devs if d['kind'] == 'cmim']

    # --- transistor rows (south to north); names from r1_afe_netlist.channel_devices()
    def tgs(side, kind):
        names = []
        for s in side:
            n = 9 if s.startswith('xs1') else 5
            ts = ['xt%d' % (i + 1) for i in range(n - 1)] + ['xtf']
            names += ['%s_%s_%s' % (s, t, kind) for t in ts]
        return names
    tgn = tgs(['xs1p', 'xs2p'], 'xn') + ['xa1_xtc1_xn', 'xi1_xn', 'xi2_xn', 'xi3_xn', 'xi4_xn', 'xa1_xtc2_xn'] + tgs(['xs2n', 'xs1n'], 'xn')
    tgp = tgs(['xs1p', 'xs2p'], 'xp') + ['xa1_xtc1_xp', 'xi1_xp', 'xi2_xp', 'xi3_xp', 'xi4_xp', 'xa1_xtc2_xp'] + tgs(['xs2n', 'xs1n'], 'xp')
    a1n = ['xa1_xmb0', 'xa1_xmb1', 'xa1_xmb4', 'xa1_xmb6', 'xa1_xmn3a', 'xa1_xmn3', 'xa1_xmn5', 'xa1_xmn7', 'xa1_xmc3',
           'xa1_xmnt', 'xa1_xmc4', 'xa1_xmn8', 'xa1_xmn6', 'xa1_xmn4', 'xa1_xmn4a']
    a2n = ['xa2_xmb0', 'xa2_xmb1', 'xa2_xmb4', 'xa2_xmb6', 'xa2_xmn3a', 'xa2_xmn3', 'xa2_xmn5', 'xa2_xmn7', 'xa2_xmc3',
           'xa2_xmc4', 'xa2_xmn8', 'xa2_xmn6', 'xa2_xmn4', 'xa2_xmn4a']
    a1p = ['xa1_xmb2', 'xa1_xmb3', 'xa1_xmb5', 'xa1_xmpt', 'xa1_xmp5', 'xa1_xmp7', 'xa1_xmct', 'xa1_xmc1', 'xa1_xmc2',
           'xa1_xmp8', 'xa1_xmp6']
    a2p1 = ['xa2_xmp3', 'xa2_xmp1', 'xa2_xmp2', 'xa2_xmp4', 'xa2_xmpt']
    a2p2 = ['xa2_xmb2', 'xa2_xmb3', 'xa2_xmb5', 'xa2_xmp5', 'xa2_xmp7', 'xa2_xmct', 'xa2_xmc1', 'xa2_xmc2', 'xa2_xmp8', 'xa2_xmp6']
    half = len(tgp) // 2
    rows = [('n', tgn), ('n', ['xa1_xmn1', 'xa1_xmn2']), ('n', a1n), ('n', a2n),
            ('p', tgp[:half]), ('p', tgp[half:]), ('p', ['xa1_xmp3', 'xa1_xmp1', 'xa1_xmp2', 'xa1_xmp4']), ('p', a1p),
            ('p', a2p1), ('p', a2p2)]
    placed_names = [n for _, r in rows for n in r]
    assert sorted(placed_names) == sorted(d['name'] for d in mos), set(d['name'] for d in mos) ^ set(placed_names)

    # --- resistor groups (P/N interleaved)
    def segs(name):
        return sorted([d for d in res if d['orig'] == name], key=lambda d: d.get('seg', 0))
    u1 = []
    for t in ['xu%d' % (i + 1) for i in range(8)] + ['xuf']:
        for s in ('xs1p', 'xs1n'):
            u1.append('%s_%s_xr' % (s, t))
    gA = dict(slots=[segs(u1[0])[0]['l']], cols=[[sg] for n in u1 for sg in segs(n)])
    rs = ['xa1_xrs1', 'xa1_xrs2', 'xa2_xrs1', 'xa2_xrs2']
    gB = dict(slots=[segs(rs[0])[0]['l']], cols=[[sg] for n in rs for sg in segs(n)])
    S2 = lambda s, i: by['%s_xs%d_xr' % (s, i)]
    gC = dict(slots=[S2('xs2p', 1)['l']],
              cols=[[S2(sd, i)] for i in (1, 2, 3, 4) for sd in (('xs2p', 'xs2n') if i % 2 else ('xs2n', 'xs2p'))])
    gD = dict(slots=[by['xs2p_xrf']['l']], cols=[[by['xs2p_xrf']], [by['xs2n_xrf']]])
    gE = dict(slots=[by['xa1_xrz1']['l'], by['xa2_xrz1']['l'], by['xro1']['l']],
              cols=[[by['xa1_xrz1'], by['xa2_xrz1'], by['xro1']], [by['xa1_xrz2'], by['xa2_xrz2'], by['xro2']]])
    groups = [gA, gB, gC, gD, gE]
    nres = sum(1 for g in groups for c in g['cols'] for s in c if s is not None)
    assert nres == len(res), (nres, len(res))

    # --- caps: matched blocks (rows of units)
    def cu(name):
        return sorted([d for d in caps if d['orig'] == name], key=lambda d: d.get('unit', 0))
    cf1p, cf1n = cu('xs1p_xcf'), cu('xs1n_xcf')
    cf2p, cf2n = cu('xs2p_xcf'), cu('xs2n_xcf')
    co1, co2, cod = cu('xco1'), cu('xco2'), cu('xcod')
    abba = lambda A, B: [[A[0], B[0], B[1], A[1]], [B[2], A[2], A[3], B[3]]]
    cblocks = [abba(cf2p, cf2n), [cod[:2], cod[2:]], abba(cf1p, cf1n), abba(co1, co2),
               [[by['xa1_xcc1'], by['xa1_xcc2']]], [[by['xa1_xcc1b'], by['xa1_xcc2b']]], [[by['xa1_xcs1'], by['xa1_xcs2']]],
               [[by['xa1_xcx1'], by['xa1_xcx2']]], [[by['xa2_xcc1'], by['xa2_xcc2']]], [[by['xa2_xcs1'], by['xa2_xcs2']]]]
    if 'xa2_xcx1' in by:     # revision F: OTA2 cross-coupled Miller caps
        cblocks.append([[by['xa2_xcx1'], by['xa2_xcx2']]])
    ncap = sum(len(r) for b in cblocks for r in b)
    assert ncap == len(caps), (ncap, len(caps))

    # --- sizes: first a dry estimate of the width
    blk = Block(ly, 'r1_afe_ch', W, H)
    xr_end, yr_top = blk.resistor_array(groups, 2.4, 3.2)
    rows_d = [(k, [by[n] for n in r]) for k, r in rows]
    info, (rx1, rx2, ry1, ry2) = blk.rows(rows_d, 2.4, yr_top + 1.6, 4)
    Wn = gceil(max(xr_end, rx2) + 2.4)
    Hn = gceil(ry2 + 2.4)
    blk.stats.update(rows=info, res_end=xr_end, res_top=yr_top, width_needed=Wn, height_needed=Hn)
    return blk, rows_d, groups, cblocks, (Wn, Hn)


def place_caps(blk, cblocks, x0, y0, x1, y1):
    """shelf packing of the cap blocks inside (x0, y0)-(x1, y1); returns the top y used."""
    x, y, rowh = x0, y0, 0.0
    used = []
    for b in cblocks:
        s = b[0][0]['w']
        px, py = s + 4.8, s + 4.4
        bw, bh = len(b[0]) * px, len(b) * py
        if x + bw > x1 + 1e-6:
            x, y, rowh = x0, y + rowh, 0.0
        for r, row in enumerate(b):
            for c, d in enumerate(row):
                blk.mim(d, round(x + c * px, 3), round(y + r * py + 1.6, 3))
        used.append((x, y, bw, bh))
        x += bw; rowh = max(rowh, bh)
    return y + rowh


def vdd_grid(blk, Wc, Hc, log=print, net='vdd', kind='p', use_plate=True, trunk_lo=None):
    """E3 (revision F): low-resistance vdd distribution inside the channel, built before routing.
    The E2 extraction showed 25-104 Ohm from the channel vdd pin to the PMOS source rails and up to 7 mV of uneven
    drop between the OTA2 bias reference and its current sources (+31 mV output CM). Here:
      * Metal5 plate (vdd) on the free Metal5 area above the MIM shelf (MIM bottom plates grown by 1.2 um removed,
        slivers below 4 um removed, largest polygon kept);
      * at every second tie-strip node of each PMOS row: a via stack Metal1-Metal2-Metal3-Metal4, and Via4 to the
        plate where the plate covers the node;
      * PMOS rows not covered by the plate: a Metal4 bus on the tie track and the track above it (1.4 um), extended
        east to a vertical Metal4 trunk (2 tracks) near the east edge that rises into the plate.
    All these nodes form one router pin of net vdd (merged with the tie-strip pins), so the router only connects the
    remaining vdd terminals and the east vdd pins to it.
    E3 (revision F, 2026-10-26): the same function builds the vss grid of the NMOS rows (net='vss', kind='n',
    use_plate=False): Metal4 buses on the tie track and the track above it, via stacks Metal1-Metal4 at every second
    tie node, and an east Metal4 trunk below the vdd trunk (the E3-dev2 extraction had a 50-125 Ohm gradient along
    the NMOS rows)."""
    R = blk.R
    ly = blk.ly
    k = R.nid(net)
    m5 = pya.Region(blk.cell.begin_shapes_rec(blk.L('M5')))
    m5.merge()
    um_ = lambda v: int(round(v * 1000))
    rows = [r for r in blk.stats['rows'] if r['kind'] == kind]
    ylo = min(r['yt'] for r in rows) - 2.4         # plate only over the PMOS rows (no vdd shield over the signal area)
    win = pya.Region(pya.Box(um_(1.6), um_(ylo), um_(Wc - 1.2), um_(Hc - 1.2)))
    if not use_plate:
        win = pya.Region()
    plate = win - m5.sized(um_(1.2))
    plate = plate.sized(-um_(2.0)).sized(um_(2.0)) & win
    if not use_plate:
        plate = pya.Region()
    polys = sorted(plate.each(), key=lambda q: -q.area())
    plate = pya.Region(polys[0]) if polys else pya.Region()
    # slits: 16 x 3.2 um holes in rows every 16 um (y) and every 24 um (x, rows staggered by 12 um), so that no
    # plate part is wider than 30 um without a slit (Slt.c.M5); slit width 3.2 um (Slt.a/b: 2.8-20 um)
    holes = pya.Region()
    bb = plate.bbox()
    q = 0
    y = bb.bottom + um_(8.0)
    while y < bb.top:
        x = bb.left + um_(4.0) + (um_(12.0) if q % 2 else 0)
        while x < bb.right:
            holes.insert(pya.Box(x, y, x + um_(16.0), y + um_(3.2)))
            x += um_(24.0)
        y += um_(16.0); q += 1
    plate = (plate - holes).sized(-um_(1.0)).sized(um_(1.0))
    polys = sorted(plate.each(), key=lambda q_: -q_.area())
    plate = pya.Region(polys[0]) if polys else pya.Region()
    inner = plate.sized(-um_(0.8))
    def inplate(x, y):
        return not (inner & pya.Region(pya.Box(um_(x) - 1, um_(y) - 1, um_(x) + 1, um_(y) + 1))).is_empty()
    xt0 = gfloor(Wc - 4.8)                        # trunk tracks xt0, xt0 + P
    nodes, stacks, buses = [], [], []
    for r in rows:
        yt = r['yt']
        xs = gpts(r['x0'] + 0.4, r['x1'] - 0.4)[::2]
        cover = sum(1 for x in xs if inplate(x, yt)) / max(1, len(xs))
        bus = cover < 0.8
        for x in xs:
            top = 5 if inplate(x, yt) else (4 if bus else 0)
            if top:
                stacks.append((x, yt, top))
                nodes += [(0, x, yt), (1, x, yt), (2, x, yt)]
        if bus:
            xe = round(xt0 + P, 4)
            bx = gpts(r['x0'] + 0.4, xe)
            buses.append((bx[0], yt, bx[-1]))
            for x in bx:
                nodes += [(2, x, yt), (2, x, round(yt + P, 4))]
        r[net + '_plate_cover'] = round(cover, 2)
        r[net + '_bus'] = bus
    trunk = None
    if buses:
        y0 = min(b[1] for b in buses)
        ys = [y for y in gpts(y0, Hc - 2.4)] if use_plate else []
        y1 = y0
        for y in ys:                              # trunk rises until it is well inside the plate
            y1 = y
            if inplate(xt0, y) and inplate(xt0 + P, y) and y > y0 + 4.0 and inplate(xt0, y - 3.2):
                break
        if not use_plate:                         # vss: trunk spans the NMOS rows (tie track + 1 of the top row)
            y1 = round(max(b[1] for b in buses) + P, 4)
        if TRUNK_ALL:   # E3 final (dev10): the trunk spans every bus row (dev9: vdd rows 7-9 had no trunk, 50-55 Ohm)
            y1 = max(y1, round(max(b[1] for b in buses) + P, 4))
        if trunk_lo is not None:   # E3 final: vss trunk down to the east vss pin below the NMOS rows (pin -> trunk short)
            y0 = min(y0, gfloor(trunk_lo))
        trunk = (xt0, y0, y1)
        for y in gpts(y0, y1):
            nodes += [(2, xt0, y), (2, round(xt0 + P, 4), y)]
        for y in gpts(y0, y1)[::2]:
            if inplate(xt0, y):
                stacks.append((xt0, y, 'v4')); stacks.append((round(xt0 + P, 4), y, 'v4'))
    # reserve and merge into one pin of vdd (drop nodes that another net already owns)
    good = []
    # E3 (revision F): keep a gap of 2 grid steps (x) on both bus tracks around every node another net already owns
    # (layout-e3-dev4: an output-cap pin inside the vss bus row was left unreachable and floated)
    foreign = set()
    for (l, x, y) in set(nodes):
        i, j = R.ij(x, y)
        if R.inside(i, j) and R.res[l, i, j] not in (-1, k):
            foreign.add((l, x, y))
    near, prev = set(), {}
    for (l, x, y) in foreign:
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-1, 0, 1):
                near.add((l, round(x + dx * P, 4), round(y + dy * P, 4)))
    for (l, x, y) in sorted(set(nodes)):
        i, j = R.ij(x, y)
        if not R.inside(i, j) or (l, x, y) in near:
            continue
        if R.res[l, i, j] in (-1, k):
            prev[(l, i, j)] = int(R.res[l, i, j])
            R.res[l, i, j] = k
            good.append((l, i, j))
    goodset = set(good)
    # E3 (revision F): draw only the bus and trunk parts whose router nodes this net owns (a node owned by another
    # net splits the bus; layout-e3-dev3 drew the full vss bus over 4 foreign nodes and shorted outp/outn to vss)
    def own(l, x, y):
        return (l, *R.ij(x, y)) in goodset
    segs = []
    for (xa, yt, xe) in buses:
        run = []
        for x in gpts(xa, xe) + [None]:
            if x is not None and own(2, x, yt) and own(2, x, round(yt + P, 4)):
                run.append(x)
                continue
            if len(run) >= 2:
                segs.append((run[0], yt, run[-1]))
            run = []
    if trunk:
        xt0_, ya, yb = trunk
        run, tsegs = [], []
        for y in gpts(ya, yb) + [None]:
            if y is not None and own(2, xt0_, y) and own(2, round(xt0_ + P, 4), y):
                run.append(y)
                continue
            if len(run) >= 2:
                tsegs.append((xt0_, run[0], run[-1]))
            run = []
    else:
        tsegs = []
    stacks_d = [s_ for s_ in stacks if s_[2] == 'v4' or all(own(l_, s_[0], s_[1]) for l_ in (0, 1, 2))]
    # keep only connected parts (layout-e3-dev6: a bus island between two gaps, with no via stack, floated with the
    # output-cap vss pin the router attached to it): a bus segment needs a via stack in it or must reach the trunk
    tx = trunk[0] if trunk else None
    def on_trunk(y):
        return any(ya - 1e-6 <= y <= yb + 1e-6 for (_, ya, yb) in tsegs)
    # E3 final (layout-e3-dev11): a segment must also reach the supply. A segment with only Metal1-Metal4 stacks (no
    # stack up to the Metal5 plate, not on the trunk) is an island (layout-e3-dev10: the vdd bus of row 152.0 fed the
    # OTA1 XMP7 source with no metal path to vdd; LVS matched through a non-metal connection). Such a segment is
    # dropped with its stacks, and the router connects those device pins.
    def up(st):
        return st[2] == 5
    # E4 (revision F1, layout-e4-dev12): a vdd bus segment with no stack up to the plate and no trunk connection (the
    # OTA1 row at y = 152 um under the MIM caps: the bias diode XMB2 and the row devices were router-connected with
    # 56-82 Ohm while the folded-cascode sources XMP3/4 sat on a plate-fed row; 9-11 mV of source-gate difference moved
    # the stage-1 output CM to 0.06 V at tt, r1afe-elim-e3d11) gets up to 3 vertical Metal4 jumpers (2 tracks wide) to
    # a kept bus segment of the adjacent bus row, on columns whose router nodes are free.
    def conn(sg):
        xa, yt, xe = sg
        return ((any(st[1] == yt and xa - 1e-6 <= st[0] <= xe + 1e-6 and up(st) for st in stacks_d) if ISLANDFIX else
                 any(st[1] == yt and xa - 1e-6 <= st[0] <= xe + 1e-6 and st[2] != 'v4' for st in stacks_d))
                or (tx is not None and xe >= tx - 1e-6 and on_trunk(yt)))
    jumpers, jkept = [], set()
    if JUMPERS and net == 'vdd':
        kept = [sg for sg in segs if conn(sg)]
        rest = [sg for sg in segs if not conn(sg)]
        rowy = sorted(set(b[1] for b in buses))
        changed = True
        while changed and rest:
            changed = False
            for sg in list(rest):
                xa, yt, xe = sg
                for t in kept:
                    xb, yb, xf = t
                    if yb == yt or any(min(yb, yt) < y_ < max(yb, yt) for y_ in rowy):
                        continue
                    ya_, yz_ = (round(yb + P, 4), yt) if yb < yt else (round(yt + P, 4), yb)
                    cols = []
                    for x in gpts(max(xa, xb), min(xe, xf) - P):
                        ok = True
                        for xx in (x, round(x + P, 4)):
                            for y_ in gpts(ya_, yz_):
                                i, j = R.ij(xx, y_)
                                if not R.inside(i, j) or R.res[2, i, j] not in (-1, k) or (2, xx, y_) in near:
                                    ok = False; break
                            if not ok:
                                break
                        if ok:
                            cols.append(x)
                    sel = []
                    for x in ([cols[0], cols[len(cols) // 2], cols[-1]] if len(cols) >= 3 else cols):
                        if all(abs(x - x_) >= 4 * P for x_ in sel):
                            sel.append(x)
                    if not sel:
                        continue
                    for x in sel:
                        for xx in (x, round(x + P, 4)):
                            for y_ in gpts(ya_, yz_):
                                i, j = R.ij(xx, y_)
                                if (2, i, j) not in goodset:
                                    prev[(2, i, j)] = int(R.res[2, i, j])
                                    R.res[2, i, j] = k
                                    good.append((2, i, j)); goodset.add((2, i, j))
                        jumpers.append((x, ya_, yz_))
                    jkept.add(sg); kept.append(sg); rest.remove(sg); changed = True
                    break
    segs = [sg for sg in segs if conn(sg) or sg in jkept]
    if VSSMESH and net == 'vss':
        # E4 iteration 2 (layout-e4-dev13x): the OTA2 NMOS row bus carries the output-stage current past the CMFB sinks to the east trunk;
        # mesh the row buses so that the gradient along the row is lower (r1afe-dm2-e4d12b2: channel vss wiring sets the
        # DC -180 deg of the post-layout DM2 return ratio)
        rowy = sorted(set(sg[1] for sg in segs))
        for ya, yb in zip(rowy, rowy[1:]):
            lo = [sg for sg in segs if sg[1] == ya]; hi = [sg for sg in segs if sg[1] == yb]
            for (xa, _, xe) in lo:
                for (xb, _, xf) in hi:
                    y0_, y1_ = round(ya + P, 4), yb
                    last = None
                    for x in gpts(max(xa, xb), min(xe, xf) - P):
                        if last is not None and x - last < 16.0 - 1e-6:
                            continue
                        ok = True
                        for xx in (x, round(x + P, 4)):
                            for y_ in gpts(y0_, y1_):
                                i_, j_ = R.ij(xx, y_)
                                if not R.inside(i_, j_) or R.res[2, i_, j_] not in (-1, k) or (2, xx, y_) in near:
                                    ok = False; break
                            if not ok:
                                break
                        if not ok:
                            continue
                        for xx in (x, round(x + P, 4)):
                            for y_ in gpts(y0_, y1_):
                                i_, j_ = R.ij(xx, y_)
                                if (2, i_, j_) not in goodset:
                                    prev[(2, i_, j_)] = int(R.res[2, i_, j_])
                                    R.res[2, i_, j_] = k
                                    good.append((2, i_, j_)); goodset.add((2, i_, j_))
                        jumpers.append((x, y0_, y1_)); last = x
    if ISLANDFIX:
        stacks_d = [st for st in stacks_d if st[2] != 4
                    or any(st[1] == yt and xa - 1e-6 <= st[0] <= xe + 1e-6 for (xa, yt, xe) in segs)]
    tsegs = [(x_, ya, yb) for (x_, ya, yb) in tsegs
             if any(xe >= x_ - 1e-6 and ya - 1e-6 <= yt <= yb + 1e-6 for (_, yt, xe) in segs)
             or any(st[2] == 'v4' and ya - 1e-6 <= st[1] <= yb + 1e-6 for st in stacks_d)]
    stacks_d = [st for st in stacks_d if st[2] != 'v4' or on_trunk(st[1])]
    # E3 (revision F): the grid pin holds only drawn nodes; reserved but undrawn nodes go back to the router; another pin
    # of the net joins the grid pin only if it touches a drawn node or a drawn via stack (layout-e3-dev4/-dev5: an
    # output-cap vss pin was merged through an undrawn node and floated)
    drawn = set()
    for (x, ya_, yz_) in jumpers:
        for y_ in gpts(ya_, yz_):
            drawn.add((2, *R.ij(x, y_))); drawn.add((2, *R.ij(round(x + P, 4), y_)))
    for (xa, yt, xe) in segs:
        for x in gpts(xa, xe):
            drawn.add((2, *R.ij(x, yt))); drawn.add((2, *R.ij(x, round(yt + P, 4))))
    for (xt0_, ya, yb) in tsegs:
        for y in gpts(ya, yb):
            drawn.add((2, *R.ij(xt0_, y))); drawn.add((2, *R.ij(round(xt0_ + P, 4), y)))
    anchors = set()
    for (x, y, top) in stacks_d:
        if top == 'v4':
            drawn.add((2, *R.ij(x, y)))
            continue
        for l_ in (0, 1, 2):
            drawn.add((l_, *R.ij(x, y)))
        anchors.add((0, *R.ij(x, y)))
    released = 0
    for n_ in goodset - drawn:
        if prev.get(n_) == -1:
            R.res[n_] = -1
            released += 1
    merged = list(drawn)
    rest = []
    for pin in R.pins.get(k, []):
        if any(n_ in drawn or n_ in anchors for n_ in pin):
            merged += list(pin)
        else:
            rest.append(pin)
    R.pins[k] = [sorted(set(merged))] + rest
    g = dict(plate=plate, stacks=stacks_d, buses=segs, trunk=None, trunks=tsegs, dropped=len(set(nodes)) - len(good),
             released=released)
    g['jumpers'] = jumpers
    if not hasattr(blk, 'grids'):
        blk.grids = []
    blk.grids.append(g)
    if net == 'vdd':
        blk.vddgrid = g
    st = dict(plate_um2=round(plate.area() / 1e6, 1), stacks=len(g['stacks']), buses=len(buses), bus_segments=len(segs), trunk=trunk, trunk_segments=tsegs,
              dropped_nodes=g['dropped'], released_nodes=g['released'], jumpers=jumpers, rows=[dict(yt=r['yt'], cover=r[net + '_plate_cover'], bus=r[net + '_bus']) for r in rows])
    blk.stats[net + 'grid'] = st
    log('%s grid: %s' % (net, st))


def draw_vdd_grid(blk):
    for g in getattr(blk, 'grids', []):
        draw_grid(blk, g)


def draw_grid(blk, g):
    blk.cell.shapes(blk.L('M5')).insert(g['plate'])
    for (x, y, top) in g['stacks']:
        if top == 'v4':
            blk.D.sq('M4', x, y, 0.40); blk.D.sq('Via4', x, y, VIA)
            continue
        blk.D.sq('M1', x, y, 0.34); blk.D.sq('Via1', x, y, VIA); blk.D.sq('M2', x, y, 0.40)
        blk.D.sq('Via2', x, y, VIA); blk.D.sq('M3', x, y, 0.40); blk.D.sq('Via3', x, y, VIA); blk.D.sq('M4', x, y, 0.40)
        if top == 5:
            blk.D.sq('Via4', x, y, VIA)
    for (xa, yt, xe) in g['buses']:
        blk.box('M4', xa - 0.3, yt - 0.3, xe + 0.3, yt + P + 0.3)
    for (xt0, y0, y1) in g.get('trunks', []):
        blk.box('M4', xt0 - 0.3, y0 - 0.3, xt0 + P + 0.3, y1 + 0.3)
    for (x, y0, y1) in g.get('jumpers', []):
        blk.box('M4', x - 0.3, y0 - 0.3, x + P + 0.3, y1 + 0.3)


CH_EAST = ['vss', 'outp', 'outn', 'vss', 'ib1', 'ib2', 'vcm1', 'vcm2', 'vdd', 'c1', 'c2', 'c3', 'c4', 'vdd', 'vss', 'vdd']
CH_WEST = [('inp', 20.0), ('inn', 24.0)]


def finish_channel(blk, cblocks, Wc, Hc, log=print):
    ytop = place_caps(blk, cblocks, 2.4, 1.6, Wc - 4.0, Hc - 2.0)
    blk.stats['caps_top'] = ytop
    if ytop > Hc - 1.6:
        log('WARNING caps exceed the channel height: %.1f > %.1f' % (ytop, Hc))
    R = blk.R
    R.block_edges()
    edge = {}
    n = len(CH_EAST)
    for q, net in enumerate(CH_EAST):
        y = gfloor(6.0 + q * (Hc - 12.0) / (n - 1))
        R.unblock(1, Wc, y)
        blk.pin(net, [(1, Wc, y)], 'm3')
        edge.setdefault(net, []).append(('E', Wc, y))
    for net, y in CH_WEST:
        R.unblock(1, 0.0, y)
        blk.pin(net, [(1, 0.0, y)], 'm3')
        edge.setdefault(net, []).append(('W', 0.0, y))
    if VDDGRID:
        vdd_grid(blk, Wc, Hc, log=log)
    if VSSGRID:
        ylo_vss = [gfloor(6.0 + q * (Hc - 12.0) / (len(CH_EAST) - 1)) for q, nn in enumerate(CH_EAST) if nn == 'vss']
        ylo_vss = [y for y in ylo_vss if y < min(r['yt'] for r in blk.stats['rows'] if r['kind'] == 'n')]
        vdd_grid(blk, Wc, Hc, log=log, net='vss', kind='n', use_plate=False,
                 trunk_lo=(max(ylo_vss) if (ylo_vss and TRUNK_ALL) else None))
    ok = route_and_balance(blk, CH_FIRST, CH_PAIRS, 'r1_afe_ch', log=log)
    blk.stats['route_ok'] = ok
    blk.stats['route_failed'] = R.failed
    blk.draw_routes()
    draw_vdd_grid(blk)
    for net, lst in edge.items():
        for (_, x, y) in lst:
            blk.ports.append(dict(dev='@pin', term=0, net=net, layer=3, box=None, pt=[x, y]))
    for net, lst in edge.items():
        for (_, x, y) in lst:
            blk.D.label('M3txt', x, y, net, 0.1)
    blk.D.boundary(0, 0, Wc, Hc)
    return edge


MARGIN = 4.0          # guard ring band around the core
STRIP = 16.0          # east routing strip
SOUTHBAND = 12.8      # routing band between the guard ring and the sine channel
SOUTH = ['vss', 'souts_p', 'souts_n', 'vcm2', 'ib_s1', 'ib_s2', 'c1', 'c2', 'c3', 'c4', 'ib_c1', 'ib_c2',
         'soutc_p', 'soutc_n', 'vdd', 'vss', 'vdd']


def build_top(ly, chcell, Wc, Hc, edge, log=print):
    top_devs, insts, ports = NLM.top_devices()
    by = {d['name']: d for d in top_devs}
    res = sorted([d for d in top_devs if d['kind'] == 'rppd'], key=lambda d: (d['orig'], d.get('seg', 0)))
    caps = sorted([d for d in top_devs if d['kind'] == 'cmim'], key=lambda d: d.get('unit', 0))
    # divider strip height from a dry resistor array
    rd1 = [d for d in res if d['orig'] == 'xrd1']; rd2 = [d for d in res if d['orig'] == 'xrd2']
    groups = [dict(slots=[rd1[0]['l']], cols=[[d] for d in rd1]), dict(slots=[rd2[0]['l']], cols=[[d] for d in rd2])]
    s = caps[0]['w']
    hdiv = gceil(max(rd1[0]['l'], rd2[0]['l']) + 6.4)
    hdiv = max(hdiv, gceil(2 * (s + 4.4) + 3.2))
    W = round(MARGIN + Wc + STRIP + MARGIN, 4)
    ysin = MARGIN + SOUTHBAND
    ydiv = round(ysin + Hc + 1.6, 4)
    ycos = round(ydiv + hdiv + 1.6, 4)
    H = round(ycos + Hc + MARGIN, 4)
    blk = Block(ly, 'r1_afe', W, H)
    R = blk.R
    for name, y in (('xsin', ysin), ('xcos', ycos)):
        blk.D.inst(chcell, MARGIN, y)
    # divider (rppd columns) and its MIM (4 units, 2 x 2)
    xe, yt = blk.resistor_array(groups, MARGIN + 2.4, ydiv + 2.4)
    cx = gceil(xe + 4.0)
    for k, d in enumerate(caps):
        blk.mim(d, cx + (k % 2) * (s + 4.8), ydiv + 2.4 + (k // 2) * (s + 4.4))
    # channel areas are obstacles except their edge pins
    pinmap = {}
    for name, pm in insts:
        y0 = ysin if name == 'xsin' else ycos
        R.block_area([0, 1, 2], MARGIN, y0, MARGIN + Wc, y0 + Hc)
        for port, lst in edge.items():
            for (side, x, y) in lst:
                X, Y = round(MARGIN + x, 4), round(y0 + y, 4)
                R.unblock(1, X, Y)
                blk.pin(pm[port], [(1, X, Y)], 'm3')
    R.block_edges()
    # E2: Metal5 supply straps along the east routing strip (vss west, vdd east), 4.8 um wide, from the south band to
    # the top of the cosine channel. Each strap is one router pin (Metal4 nodes every 4.8 um on its centre line); a
    # used node gets a Via4 to the strap. Metal5 is otherwise unused at the top level (no TopMetal1/2 added).
    blk.straps = []
    blk.feet = []
    if STRAPS:
        xs0 = MARGIN + Wc
        nS = len(SOUTH)
        sx = [(net, gfloor(8.0 + q * (W - 16.0) / (nS - 1))) for q, net in enumerate(SOUTH)]
        for net, xc in (('vss', xs0 + 4.0), ('vdd', xs0 + 12.0)):
            xc = gfloor(xc)
            y0, y1 = gceil(MARGIN + 1.6), gfloor(H - MARGIN - 1.6)
            nodes = [(2, xc, y) for y in gpts(y0, y1)][::6]
            blk.pin(net, nodes, 'm5')
            blk.straps.append((net, xc - 2.4, y0 - 0.4, xc + 2.4, y1 + 0.4))
            for (_, x, y) in nodes:
                blk.m5pins[R.ij(x, y)] = net
            # foot: the south pin of this net nearest to the strap gets a 3 x 2 Via3/Via4 array under a Metal5 foot
            # that joins the strap (reserved before routing; dev9: 35-48 Ohm from the south pins to the channels)
            xp = min((x for n_, x in sx if n_ == net), key=lambda x: abs(x - xc))
            fx = [round(xp + d, 4) for d in (-P, 0.0, P)]
            fy = [0.8, 1.6]
            for l in (1, 2):
                for x in fx:
                    for y in fy:
                        R.res[l][R.ij(x, y)] = R.nid(net)
            blk.feet.append((net, fx, fy, xc))
    # p+ guard ring (substrate tie, vss) with its centre line on the grid at 2.4 um from the edge
    blk.D.tap_ring(2.7, 2.7, W - 2.7, H - 2.7, w=0.6, ptype=True)
    ring = [(0, x, 2.4) for x in gpts(4.0, W - 4.0)] + [(0, x, H - 2.4) for x in gpts(4.0, W - 4.0)]
    if not STRAPS:
        blk.pin('vss', ring, 'm1')
    # block pins on Metal3: south edge (to r1_adc, r1_bgr, r1_ctrl level shifters, VDDA trunk), west edge inputs
    bp = []
    n = len(SOUTH)
    for q, net in enumerate(SOUTH):
        x = gfloor(8.0 + q * (W - 16.0) / (n - 1))
        R.unblock(1, x, 0.8)
        blk.pin(net, [(1, x, 0.8)], 'm3')
        bp.append((net, 'S', x, 0.8))
    if STRAPS:
        # E2: the guard ring is a vss pin only at a few nodes next to each south vss pin, so the router cannot use the
        # 0.6 um Metal1 ring as a long supply conductor (dev7: 270-1370 Ohm from the vss pins to the channels)
        for (net, side, x, y) in bp:
            if net == 'vss':
                blk.pin('vss', [n for n in ring if n[2] == 2.4 and abs(n[1] - x) <= 1.6 + 1e-6], 'm1')
    for net, ch, port in (('sinp', ysin, 'inp'), ('sinn', ysin, 'inn'), ('cosp', ycos, 'inp'), ('cosn', ycos, 'inn')):
        y = round(ch + edge[port][0][2], 4)
        R.unblock(1, 0.8, y)
        blk.pin(net, [(1, 0.8, y)], 'm3')
        bp.append((net, 'W', 0.8, y))
    R.halo_cost = TOP_HALO
    ok = route_and_balance(blk, TOP_FIRST, TOP_PAIRS, 'r1_afe', log=log)
    blk.stats.update(route_ok=ok, route_failed=R.failed, W=W, H=H)
    for net, side, x, y in bp:
        blk.ports.append(dict(dev='@pin', term=0, net=net, layer=3, box=None, pt=[x, y]))
    for name, pm in insts:   # channel instance ports: top net at the channel edge pin
        y0 = ysin if name == 'xsin' else ycos
        for port, lst in edge.items():
            for (side, x, y) in lst:
                blk.ports.append(dict(dev='@' + name, term=port, net=pm[port], layer=3, box=None,
                                      pt=[round(MARGIN + x, 4), round(y0 + y, 4)]))
    blk.stats['inst_origin'] = {'xsin': [MARGIN, ysin], 'xcos': [MARGIN, ycos]}
    blk.draw_routes()
    for net, side, x, y in bp:
        if side == 'S':
            blk.box('M3', x - 0.2, 0.0, x + 0.2, y + 0.2); blk.box('M3pin', x - 0.2, 0.0, x + 0.2, y + 0.2)
        else:
            blk.box('M3', 0.0, y - 0.2, x + 0.2, y + 0.2); blk.box('M3pin', 0.0, y - 0.2, x + 0.2, y + 0.2)
        blk.D.label('M3txt', x, y, net, 0.3)
    blk.D.boundary(0, 0, W, H)
    blk.stats['pins'] = bp
    return blk


def main():
    import time
    t0 = time.time()
    ly = pya.Layout(); ly.dbu = 0.001
    NLM.write_cdl()
    ly0 = pya.Layout(); ly0.dbu = 0.001
    b0, _, _, _, (Wc, Hc) = build_channel(ly0)
    print('channel size', Wc, Hc)
    blk, rows_d, groups, cblocks, _ = build_channel(ly, Wc, Hc)
    edge = finish_channel(blk, cblocks, Wc, Hc)
    print('channel routed', blk.stats['route_ok'], blk.stats['route_failed'], '%.0f s' % (time.time() - t0))
    top = build_top(ly, blk.cell, Wc, Hc, edge)
    print('top routed', top.stats['route_ok'], top.stats['route_failed'], 'size', top.stats['W'], top.stats['H'],
          'area %.4f mm2' % (top.stats['W'] * top.stats['H'] * 1e-6), '%.0f s' % (time.time() - t0))
    for c in list(ly.each_cell()):
        pass
    ly.write(OUT)
    st = dict(channel=dict(W=Wc, H=Hc, route_ok=blk.stats['route_ok'], failed=blk.stats['route_failed'],
                           rows=blk.stats['rows'], caps_top=blk.stats.get('caps_top')),
              top=dict(W=top.stats['W'], H=top.stats['H'], route_ok=top.stats['route_ok'], failed=top.stats['route_failed'],
                       pins=top.stats['pins']), runtime_s=round(time.time() - t0, 1))
    st['channel'].update(pairs_before=blk.stats['pairs_before'], pairs_after=blk.stats['pairs_after'], trim_placed=blk.stats['trim_placed'])
    st['top'].update(pairs_before=top.stats['pairs_before'], pairs_after=top.stats['pairs_after'], trim_placed=top.stats['trim_placed'])
    st['trim_input'] = TRIM
    st['vddgrid'] = blk.stats.get('vddgrid')
    st['vssgrid'] = blk.stats.get('vssgrid')
    st['widen'] = dict(channel=blk.stats.get('widen'), top=top.stats.get('widen'), strap_vias=top.stats.get('strap_vias'))
    json.dump(st, open(os.path.join(os.path.dirname(OUT), 'r1_afe_layout.json'), 'w'), indent=1)
    nets = {}
    for cname, b in (('r1_afe_ch', blk), ('r1_afe', top)):
        nets[cname] = {b.R.names[k]: b.R.net_stats(k) for k in b.R.paths}
    json.dump({'r1_afe_ch': blk.ports, 'r1_afe': top.ports, 'inst_origin': top.stats['inst_origin'], 'channel_size': [Wc, Hc],
               'net_stats': nets}, open(os.path.join(os.path.dirname(OUT), 'r1_afe_ports.json'), 'w'))


if __name__ == '__main__' or True:
    main()
