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
        self.labels = {}
        self.grails = []     # (net, x1, x2, y): gate rails, bridged to router pads closer than 0.3 um
        self.stats = {}

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
        for side, strips, lo, hi, yc, net in (('bot', m.strips(0), 0.88, 1.38, yg - P, Sn),
                                               ('top', m.strips(1), dt - 0.25, dt + 0.25, yd, Dn)):
            xl, xr = m.sx(strips[0]) - 0.13, m.sx(strips[-1]) + 0.13
            xs = gpts(xl + 0.2, xr - 0.2)
            er = 0.0
            if not xs:
                t = gceil(xl + 0.2); er = t + 0.2 - xr; xs = [t]
            m.rail(side, strips, ext=(0.0, er), lo=lo, hi=hi)
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
        # bottom plate: Metal5 tab south, Via4 to the Metal4 pin node
        xb = gfloor(mx + s / 2); yb = gfloor(my - 1.5)
        self.box('M5', xb - 0.31, yb - 0.31, xb + 0.31, my - 0.3)
        self.D.sq('Via4', xb, yb, VIA)
        self.D.sq('M4', xb, yb, 0.40)
        self.pin(bot, [(2, xb, yb)], 'm4')

    # ---- output ------------------------------------------------------------------------------------------
    def draw_routes(self):
        lay = {'M2': 'M2', 'M3': 'M3', 'M4': 'M4', 'Via2': 'Via2', 'Via3': 'Via3'}
        for kind, net, ln, x1, y1, x2, y2 in self.R.shapes():
            self.box(lay[ln], x1, y1, x2, y2)
        # Via1 + Metal1 pad on every used Metal1-type pin node
        for k in list(self.R.paths):
            for (l, i, j) in self.R.used_nodes(k):
                if l == 0 and (i, j) in self.m1pins:
                    x, y = self.R.xy(i, j)
                    self.D.sq('Via1', x, y, VIA)
                    self.D.sq('M1', x, y, 0.34)
                    self.D.sq('M2', x, y, 0.40)
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
    ok = R.route_all(rounds=ROUTE_ROUNDS, log=log)
    blk.stats['route_ok'] = ok
    blk.stats['route_failed'] = R.failed
    blk.draw_routes()
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
    # p+ guard ring (substrate tie, vss) with its centre line on the grid at 2.4 um from the edge
    blk.D.tap_ring(2.7, 2.7, W - 2.7, H - 2.7, w=0.6, ptype=True)
    ring = [(0, x, 2.4) for x in gpts(4.0, W - 4.0)] + [(0, x, H - 2.4) for x in gpts(4.0, W - 4.0)]
    blk.pin('vss', ring, 'm1')
    # block pins on Metal3: south edge (to r1_adc, r1_bgr, r1_ctrl level shifters, VDDA trunk), west edge inputs
    bp = []
    n = len(SOUTH)
    for q, net in enumerate(SOUTH):
        x = gfloor(8.0 + q * (W - 16.0) / (n - 1))
        R.unblock(1, x, 0.8)
        blk.pin(net, [(1, x, 0.8)], 'm3')
        bp.append((net, 'S', x, 0.8))
    for net, ch, port in (('sinp', ysin, 'inp'), ('sinn', ysin, 'inn'), ('cosp', ycos, 'inp'), ('cosn', ycos, 'inn')):
        y = round(ch + edge[port][0][2], 4)
        R.unblock(1, 0.8, y)
        blk.pin(net, [(1, 0.8, y)], 'm3')
        bp.append((net, 'W', 0.8, y))
    ok = R.route_all(rounds=ROUTE_ROUNDS, log=log)
    blk.stats.update(route_ok=ok, route_failed=R.failed, W=W, H=H)
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
    json.dump(st, open(os.path.join(os.path.dirname(OUT), 'r1_afe_layout.json'), 'w'), indent=1)


if __name__ == '__main__' or True:
    main()
