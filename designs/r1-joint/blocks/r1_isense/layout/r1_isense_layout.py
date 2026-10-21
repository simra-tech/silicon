#!/usr/bin/env python3
"""r1_isense layout generator (revision-2 netlist, sha256 af013b95...): KLayout 0.30.9 batch Python in the pinned container.

  G1_WORKDIR=designs/r1-joint/blocks/r1_isense/layout flow/run.sh klayout -b -r r1_isense_layout.py
  writes r1_isense.gds (top cell r1_isense, one child cell r1_isense_ch placed twice), r1_isense_lvs.cdl,
  r1_isense_layout.json (bounding box, pins, router statistics).

Method: as the r1_afe layout (track T3, layout/r1_afe_layout.py, copied and adapted 2026-10-21): PDK PCells (pmosHV,
nmosHV, pmos, nmos, cmim), rppd/rhigh bodies copied from the PDK PCell and stretched, helpers from
designs/g1-guardian/blocks/g1_sense/layout/g1_layout_lib.py (read only), grid maze router (maze_router.py, copy of the
r1_afe router) on Metal2-Metal4 for all signal wiring; supply trunks drawn (Metal4).

Channel cell r1_isense_ch (south to north):
  resistor band: main rppd array (w 2 um, l 30.8 um, two slots): RIN, RF (G = 14) and RP units of both sides, every
  column one side, interleaved A/B with equal first and second moments about the centre column (RIA/RIB), poly dummy
  columns at both ends; then the RDG (rppd 2 x 25 um) and RZ columns, then the rhigh columns (37.5 um units: RCA/RCB
  4 each, RH1/RH2), with the 1.2 V device rows (pmos on vdd, nmos) above the rhigh columns.
  MOS rows: three HV NMOS rows, three HV PMOS rows (wells vdda, tail, atail, ctail, gtail; input pair XM1/XM2 and
  aux pair XA1/XA2 split in halves A B / B A over two rows = common centroid), poly dummies at every device end,
  a tie strip under every row (p+ for NMOS, n+ well tie for PMOS).
  MIM (Metal5/TopMetal1) over the resistor band (cut C6 practice): XCI 1.9 pF, XCH1/2, XCCA/B, XCMA/B.
  Supply trunks on Metal4: vss and vdda on the west edge, vdd on the east edge; ports on Metal3 at the cell edges.
Top r1_isense: channel A (south) and channel B (north) as translated copies (same orientation), west routing strip,
p+ guard ring (vss), pins on Metal3 at the boundary: inputs east, outputs/controls/references west, supplies south.
Layers: no Metal5 routing, TopMetal1 only on MIM plates and tabs, no TopMetal2; boundary on 189/4 only.
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'g1-guardian', 'blocks', 'g1_sense', 'layout'))
from g1_layout_lib import *   # noqa  (pya, LIB, Draw, Mos, CONT, VIA, TV1, ...)
import r1_isense_netlist as NLM
from maze_router import Router, P, LNAME

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass
OUT = globals().get('out', os.path.join(HERE, 'r1_isense.gds'))
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
# resistor bodies: the PDK PCell geometry at l = 10 um, stretched to any length
_TMPL = {}


def res_template(kind, w):
    key = (kind, w)
    if key not in _TMPL:
        pcv = LIB.layout().add_pcell_variant(LIB.layout().pcell_id(kind), {'Calculate': 'R', 'w': '%gu' % w, 'l': '10u', 'b': 0})
        c = LIB.layout().cell(pcv)
        shapes = []
        for li in LIB.layout().layer_indexes():
            info = LIB.layout().get_info(li)
            if info.datatype != 0 or info.layer == 63:
                continue
            for s in c.shapes(li).each():
                if s.is_text():
                    continue
                b = s.bbox()
                shapes.append(((info.layer, info.datatype), b.left / 1000, b.bottom / 1000, b.right / 1000, b.top / 1000))
        _TMPL[key] = shapes
    return _TMPL[key]


DUMMY_LMAX = 1.0      # poly dummy length cap (the gate length for l <= 1 um)


def est_segs(segs, x_start):
    """estimated x extents of the segments of one row (placement arithmetic of Block.rows/mos, +0.4 per device)"""
    out, x = [], x_start
    for s in segs:
        if 'x' in s:
            x = s['x']
        x0 = x
        for d in s['devs']:
            ld = min(d['l'], DUMMY_LMAX)
            x = x + 0.2 + ld + 0.35 + d['ng'] * (d['l'] + 0.38) + 0.30 + 0.2 + ld + 0.5 + 0.4
        out.append((x0, x))
        x += 4.6 if s['kind'] in ('p', 'plv') else 1.0
    return out


_MOS_T = {}


class LongMos(Mos):
    """Mos with a gate longer than the PCell limit (10 um): the PCell geometry at l = 10 um (ng = 1), every shape right
    of the gate centre shifted and every shape across it stretched by l - 10 (flat shapes in the cell, same layers)."""

    def __init__(self, D, kind, w, l, nf, x0, y0):
        assert nf == 1 and l > 10.0
        self.D, self.kind, self.w, self.l, self.nf, self.x0, self.y0 = D, kind, w, l, nf, x0, y0
        self.wf = w
        self.pitch = l + PITCH_EXTRA
        self.actw = nf * self.pitch + 0.30
        self.is_p = kind.startswith('pmos')
        self.hv = kind.endswith('HV')
        key = (kind, w)
        if key not in _MOS_T:
            pcv = LIB.layout().add_pcell_variant(LIB.layout().pcell_id(kind), {'w': '%gu' % w, 'l': '10u', 'ng': 1})
            c = LIB.layout().cell(pcv)
            sh = []
            for li in LIB.layout().layer_indexes():
                info = LIB.layout().get_info(li)
                for s in c.shapes(li).each():
                    if s.is_text():
                        continue
                    b = s.bbox()
                    sh.append(((info.layer, info.datatype), b.left / 1000, b.bottom / 1000, b.right / 1000, b.top / 1000))
            _MOS_T[key] = sh
        xm = 0.34 + 5.0
        dl = l - 10.0
        for (lay, x1, y1, x2, y2) in _MOS_T[key]:
            if x1 >= xm:
                x1 += dl; x2 += dl
            elif x2 > xm:
                x2 += dl
            D.cell.shapes(D.ly.layer(*lay)).insert(pya.Box(um(x0 + x1), um(y0 + y1), um(x0 + x2), um(y0 + y2)))


class Block:
    """drawing + pin bookkeeping for one cell and its router."""

    def __init__(self, ly, name, W, H):
        self.ly = ly
        self.cell = ly.create_cell(name)
        self.D = Draw(ly, self.cell)
        self.W, self.H = W, H
        self.R = Router(0.0, 0.0, int(round(W / P)) + 1, int(round(H / P)) + 1)
        self.m1pins = {}
        self.grails = []
        self.stats = {}
        self.respos = {}
        self.ends_np = {}

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
    def mos(self, d, x0, yg, tie=None):
        kind = {'nmos': 'nmosHV', 'pmos': 'pmosHV', 'nmoslv': 'nmos', 'pmoslv': 'pmos'}[d['kind']]
        w, l, ng = round(d['w'], 3), round(d['l'], 3), d['ng']
        y0 = round(yg + 0.33, 4)
        m = (LongMos if l > 10.0 else Mos)(self.D, kind, w, l, ng, x0, y0)
        Dn, Gn, Sn, Bn = d['nets']
        gl, gr = m.gx(0) - 0.20, m.gx(ng - 1) + 0.20
        xs = gpts(gl + 0.2, gr - 0.2)
        er = 0.0
        if not xs:
            t = gceil(gl + 0.2); er = t + 0.2 - gr; xs = [t]
        if d['kind'] in ('nmoslv', 'pmoslv'):
            # short gates: one contact per drain strip (odd strips do not extend down), poly bar under all gates
            cx = [m.sx(k) for k in range(1, ng + 1, 2)]
            ya, yb = y0 - 0.48, y0 - 0.18
            self.box('GatPoly', m.gx(0) - l / 2, ya, max(m.gx(ng - 1) + l / 2, max(cx) + 0.15), yb)
            for c in cx:
                self.D.sq('Cont', c, y0 - 0.33, CONT)
                self.box('M1', c - 0.15, ya, c + 0.15, yb)
                self.D.sq('Via1', c, y0 - 0.33, VIA)
            rl, rr = min(cx) - 0.20, max(cx) + 0.20
            xs = gpts(rl + 0.2, rr - 0.2)
            if not xs:
                t = gceil(rl + 0.2); xs = [t]; rr = max(rr, t + 0.2); rl = min(rl, t - 0.2)
        else:
            rl, rr, ra, rb = m.gate_bar('bot', ext=(0.0, er))
        self.box('M2', rl, yg - 0.20, rr, yg + 0.20)
        self.grails.append((Gn, rl, rr, yg))
        self.m2fixed(rl, yg - 0.20, rr, yg + 0.20, Gn)
        self.pin(Gn, [(0, x, yg) for x in xs], 'm2')
        ld = min(l, DUMMY_LMAX)
        right = max(m.x1 + 0.2 + ld, rr)
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
            if side == 'bot' and net == tie:
                # source on the row's supply / well net: Metal1 fill from the rail into the tie strip, no router pin
                self.box('M1', xl, yg - 1.6, xr + er, yg - 0.8)
            elif (d['name'], net) in KELVIN_JUNCTION and len(xs) >= 2:
                # output Kelvin junction: one node of the drain rail starts the sense tree (net_s), the others
                # take the output-stage current (net)
                self.pin(net + '_s', [(0, xs[0], yc)], 'm1')
                self.pin(net, [(0, x, yc) for x in xs[1:]], 'm1')
            else:
                self.pin(SENSE.get(d['name'], {}).get(net, net), [(0, x, yc) for x in xs], 'm1')
            right = max(right, xr + er)
        # poly dummies (length capped) just outside both Activ ends
        for xd in (m.x0 - 0.20 - ld / 2, m.x1 + 0.20 + ld / 2):
            yc = m.y0 + m.wf / 2
            self.box('GatPoly', xd - ld / 2, yc - (m.wf + 0.36) / 2, xd + ld / 2, yc + (m.wf + 0.36) / 2)
        return m, right, yd

    # ---- rows of transistors --------------------------------------------------------------------------
    def rows(self, rows, x_start, y_start, tie_west=None, tie_east=None):
        """rows: list of lists of segments; segment = dict(kind in n/p/nlv/plv, well (p kinds), devs, x (optional
        absolute start)). Every segment gets its own tie strip (p+ or n+ in its NWell); HV rows get one TGO box over
        the row; NWell boxes per segment. tie_west/tie_east: {net: x} - the westmost / eastmost segment's tie strip of
        that net is extended on Metal1 to x (a supply trunk) and gets a via stack there. Returns info, extents."""
        info = []
        yg = gceil(y_start + 2 * P + 0.6)
        prev = None
        xmin_all, xmax_all = 1e9, -1e9
        for r, segs in enumerate(rows):
            if prev is not None:
                need = 3 * P
                pk = [s['kind'] for s in prev['segs']]
                ck = [s['kind'] for s in segs]
                if any(k in ('p', 'plv') for k in ck) and any(k in ('n', 'nlv') for k in pk):
                    need = 4 * P
                if any(k in ('n', 'nlv') for k in ck) and any(k in ('p', 'plv') for k in pk):
                    need = 4 * P + 1.2
                # NWell of different nets above each other: 1.8 um apart (estimated extents of this row)
                est = est_segs(segs, x_start)
                for a in prev['segs']:
                    for b, (bx0, bx1) in zip(segs, est):
                        if a['kind'] in ('p', 'plv') and b['kind'] in ('p', 'plv') and a['well'] != b['well']:
                            if a['x1'] + 1.0 + 2.6 > bx0 - 1.0 and bx1 + 1.0 + 2.6 > a['x0'] - 1.0:
                                need = max(need, 7 * P)
                hv_prev = all(k in ('n', 'p') for k in pk); hv_cur = all(k in ('n', 'p') for k in ck)
                if hv_prev != hv_cur:
                    need = max(need, 6 * P)
                yg = gceil(prev['yd'] + need)
            x = x_start
            placed_all = []
            ydmax = yg
            for s in segs:
                if 'x' in s:
                    assert s['x'] >= x - 1e-6, ('segment overlap', s['x'], x)
                    x = s['x']
                s['x0'] = x
                placed = []
                for d in s['devs']:
                    ld = min(d['l'], DUMMY_LMAX)
                    x0 = round(x + 0.2 + ld + 0.35, 2)
                    m, right, yd = self.mos(d, x0, yg, tie=('vss' if s['kind'] in ('n', 'nlv') else s['well']))
                    placed.append(m)
                    ydmax = max(ydmax, yd)
                    x = right + 0.5
                s['x1'] = x
                s['placed'] = placed
                placed_all += placed
                yt = round(yg - 2 * P, 4)
                ptap = s['kind'] in ('n', 'nlv')
                tnet = 'vss' if ptap else s['well']
                xa, xb = s['x0'], s['x1']
                self.box('M1', xa, yg - 1.93, xb, yg - 1.25)      # widened tie strip Metal1 (supply bus of the row)
                self.D.tap_strip(xa, xb, yt, ptype=ptap, w=0.30, inset=0.2)
                self.pin(tnet, [(0, xx, yt) for xx in gpts(xa + 0.4, xb - 0.4)], 'm1')
                if not ptap:
                    y_lo = min(m.y0 for m in placed); y_hi = max(m.y1 for m in placed)
                    ax = min(m.x0 for m in placed); bx = max(m.x1 for m in placed)
                    self.box('pSD', ax - 0.18, y_lo - 0.40, bx + 0.18, y_hi + 0.40)
                s['yt'] = yt
                x += 4.6 if not ptap else 1.0
            # supply trunk connections of the tie strips (Metal1 extension + via stack to Metal4)
            for side, spec in (('W', tie_west or {}), ('E', tie_east or {})):
                for net, xt in spec.items():
                    cand = [s for s in segs if ('vss' if s['kind'] in ('n', 'nlv') else s['well']) == net]
                    if not cand:
                        continue
                    s = cand[0] if side == 'W' else cand[-1]
                    y0b, y1b = s['yt'] - 0.33, s['yt'] + 0.35
                    if side == 'W':
                        self.box('M1', xt - 0.75, y0b, s['x0'] + 0.1, y1b)
                    else:
                        self.box('M1', s['x1'] - 0.1, y0b, xt + 0.75, y1b)
                    yc = round((y0b + y1b) / 2, 3)
                    for v in ('Via1', 'Via2', 'Via3'):
                        for dx in (-0.25, 0.25):
                            self.D.sq(v, xt + dx, yc, VIA)
                    for lay in ('M2', 'M3'):
                        self.box(lay, xt - 0.75, y0b, xt + 0.75, y1b)
                    self.R.reserve(0, xt - 0.75, y0b, xt + 0.75, y1b, net)
                    self.R.reserve(1, xt - 0.75, y0b, xt + 0.75, y1b, net)
            xr = max(s['x1'] for s in segs)
            row = dict(row=r, segs=segs, yg=yg, yd=ydmax, x0=x_start, x1=xr,
                       ymin_act=min(m.y0 for m in placed_all), ymax_act=max(m.y1 for m in placed_all))
            info.append(row)
            xmin_all, xmax_all = min(xmin_all, x_start), max(xmax_all, xr)
            prev = row
        # TGO per HV row (full row), NWell per p segment
        for row in info:
            if all(s['kind'] in ('n', 'p') for s in row['segs']):
                xa = min(s['x0'] for s in row['segs']); xb = max(s['x1'] for s in row['segs'])
                self.box('TGO', xa - 0.8, row['segs'][0]['yt'] - 0.8, xb + 0.8, row['yd'] + 0.8)
            for s in row['segs']:
                if s['kind'] in ('p', 'plv'):
                    self.box('NWell', s['x0'] - 1.0, s['yt'] - 1.0, s['x1'] + 1.0, row['yd'] + 1.0)
        ylo = info[0]['segs'][0]['yt'] - 1.0
        yhi = info[-1]['yd'] + 1.0
        for row in info:
            row.pop('segs_placed', None)
        return info, (xmin_all, xmax_all, ylo, yhi)

    # ---- resistor array ---------------------------------------------------------------------------------
    def res_group(self, g, x_start, y_b):
        """g: dict(kind, w, slots=[L...], cols=[[dev or None per slot]], dummies=n). Columns at pitch w + 0.4 (w = 2)
        or w + 0.6 (w = 1); the column centre is on the router grid. Records self.respos[dev name] = (xc, ys, L, w).
        Returns (x_end, y_top, slot offsets)."""
        w, kind = g['w'], g['kind']
        pitch = 2.4 if w == 2 else 1.6
        tmpl = res_template(kind, w)
        offs, y = [], y_b
        for k, L in enumerate(g['slots']):
            if k > 0:
                prev_top = offs[-1] + g['slots'][k - 1]
                pin_top = gceil(prev_top + 0.75)
                y = s5(pin_top + P + 0.75)
                while gfloor(y - 0.75) < pin_top + P - 1e-6:
                    y = s5(y + 0.05)
                y = max(y, s5(prev_top + g.get('gap', 0.0)))
            offs.append(round(y, 4))
        x = gceil(x_start + w / 2) - w / 2
        nd = g.get('dummies', 1)
        cols = [[None] * len(g['slots'])] * nd + list(g['cols']) + [[None] * len(g['slots'])] * nd
        xs0 = x
        slotkind = g.get('slotkind', [kind] * len(g['slots']))
        for c, col in enumerate(cols):
            xc = round(x, 4)
            for k, dev in enumerate(col):
                ys, L = offs[k], g['slots'][k]
                if dev is None:
                    self.box('GatPoly', xc, ys + 0.25, xc + w, ys + L - 0.25)
                    continue
                tm = res_template(dev['kind'], w)
                for (lay, x1, y1, x2, y2) in tm:
                    if y2 <= 5.0 + 1e-6:
                        pass
                    elif y1 >= 5.0 - 1e-6:
                        y1 += L - 10.0; y2 += L - 10.0
                    else:
                        y2 += L - 10.0
                    self.cell.shapes(self.ly.layer(*lay)).insert(pya.Box(um(xc + x1), um(ys + y1), um(xc + x2), um(ys + y2)))
                assert abs(dev['l'] - L) < 1e-6, (dev['name'], dev['l'], L)
                self.respos[dev['name']] = (xc, ys, L, w, k, c)
            x = round(x + pitch, 4)
        xe = x - pitch + w
        for k, L in enumerate(g['slots']):
            ys = offs[k]
            self.box('SalBlock', xs0 - 0.2, ys, xe + 0.2, ys + L)
            self.box('pSD', xs0 - 0.18, ys - 0.61, xe + 0.18, ys + L + 0.61)
            if slotkind[k] == 'rhigh':
                self.box('nSD', xs0 - 0.18, ys - 0.61, xe + 0.18, ys + L + 0.61)
            self.box('EXTBlock', xs0 - 0.2, ys - 0.61, xe + 0.2, ys + L + 0.61)
            self.R.block_area([0], xs0 - 0.4, ys + 0.3, xe + 0.4, ys + L - 0.3)
        return xe, offs[-1] + g['slots'][-1], offs

    def res_head(self, name, end):
        xc, ys, L, w, k, c = self.respos[name]
        hd = 0.43 if True else 0.41
        if end == 'b':
            return (xc + 0.02, ys - 0.43, xc + w - 0.02, ys - 0.13)
        return (xc + 0.02, ys + L + 0.13, xc + w - 0.02, ys + L + 0.43)

    def res_pin(self, unit, e, net):
        xc, ys, L, w, _, _ = self.respos[unit]
        xp = round(xc + w / 2, 4)
        if e == 'b':
            yp = gfloor(ys - 0.75)
            self.box('M1', xp - 0.17, yp - 0.17, xp + 0.17, ys - 0.13)
        else:
            yp = gceil(ys + L + 0.75)
            self.box('M1', xp - 0.17, ys + L + 0.13, xp + 0.17, yp + 0.17)
        self.pin(SENSE.get(unit, {}).get(net, net), [(0, xp, yp)], 'm1')

    def res_chain(self, units, nets, nopin=(), tap=()):
        """units: device names in series order; nets: len(units)+1 net names (nets[k], nets[k+1] are the ends of
        unit k). Consecutive units that are vertical neighbours (same column, adjacent slots) or horizontal
        neighbours (adjacent columns, same slot) are strapped on Metal1; every other end gets a router pin."""
        n = len(units)
        ends = []        # (a_end, b_end) per unit: 'b' bottom / 't' top
        strap = [None] * (n - 1)
        a_end = None
        for k in range(n):
            u = self.respos[units[k]]
            nxt = self.respos[units[k + 1]] if k + 1 < n else None
            if a_end is None:
                if nxt is not None and nxt[5] == u[5] and nxt[4] == u[4] - 1:
                    a_end = 't'
                else:
                    a_end = 'b'
            b_end = 't' if a_end == 'b' else 'b'
            ends.append((a_end, b_end))
            a_end = None
            if nxt is not None:
                same_col = nxt[5] == u[5] and abs(nxt[0] - u[0]) < 1e-6
                if same_col and ((nxt[4] == u[4] + 1 and b_end == 't') or (nxt[4] == u[4] - 1 and b_end == 'b')):
                    strap[k] = 'v'
                    a_end = 'b' if b_end == 't' else 't'
                elif nxt[4] == u[4] and abs(abs(nxt[0] - u[0]) - (u[3] + 0.4)) < 1e-6 and abs(nxt[1] - u[1]) < 1e-6:
                    strap[k] = 'h'
                    a_end = b_end
        for k in range(n - 1):
            if strap[k] is None:
                continue
            ha = self.res_head(units[k], ends[k][1]); hb = self.res_head(units[k + 1], ends[k + 1][0])
            self.box('M1', min(ha[0], hb[0]), min(ha[1], hb[1]), max(ha[2], hb[2]), max(ha[3], hb[3]))
            self.D.label('M1txt', (ha[0] + ha[2]) / 2, (ha[1] + ha[3]) / 2, nets[k + 1], 0.1)
            if nets[k + 1] in tap:
                self.res_pin(units[k + 1], ends[k + 1][0], nets[k + 1])
        for k in range(n):
            for e, net, linked in ((ends[k][0], nets[k], k > 0 and strap[k - 1] is not None),
                                   (ends[k][1], nets[k + 1], k < n - 1 and strap[k] is not None)):
                if linked:
                    continue
                if net in nopin:
                    self.ends_np[net] = (units[k], e)
                    continue
                self.res_pin(units[k], e, net)
        return strap

    # ---- MIM -------------------------------------------------------------------------------------------
    def mim(self, d, mx, my):
        s = round(d['w'], 3)
        self.D.pcell('cmim', {'Calculate': 'C', 'w': '%gu' % s, 'l': '%gu' % s}, mx, my)
        top, bot = d['nets'][0], d['nets'][1]
        xt = gceil(mx + s + 1.2); yt = gfloor(my + s / 2)
        self.box('TM1', mx + s / 2, yt - 0.82, xt + 0.82, yt + 0.82)
        self.D.sq('TV1', xt, yt, TV1)
        self.D.sq('M5', xt, yt, TV1 + 2 * TV1_M5)
        self.D.sq('Via4', xt, yt, VIA)
        self.D.sq('M4', xt, yt, 0.40)
        self.pin(top, [(2, xt, yt)], 'm4')
        xb = gfloor(mx + s / 2); yb = gfloor(my - 1.5)
        self.box('M5', xb - 0.31, yb - 0.31, xb + 0.31, my - 0.3)
        self.D.sq('Via4', xb, yb, VIA)
        self.D.sq('M4', xb, yb, 0.40)
        self.pin(bot, [(2, xb, yb)], 'm4')
        return (mx - 0.6, my - 0.6 - 1.9, xt + 0.82, my + s + 0.6)

    # ---- supply trunk (Metal4, vertical) -----------------------------------------------------------------
    def trunk(self, net, x1, x2, y1, y2):
        self.box('M4', x1, y1, x2, y2)
        self.R.reserve(2, x1, y1, x2, y2, net)
        xs = gpts(x1 + 0.2, x2 - 0.2)
        nodes = [(2, x, y) for x in xs for y in gpts(y1 + 1.0, y2 - 1.0)]
        self.pin(net, nodes, 'm4')

    # ---- output ------------------------------------------------------------------------------------------
    def draw_routes(self):
        lay = {'M2': 'M2', 'M3': 'M3', 'M4': 'M4', 'Via2': 'Via2', 'Via3': 'Via3'}
        for kind, net, ln, x1, y1, x2, y2 in self.R.shapes():
            self.box(lay[ln], x1, y1, x2, y2)
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
        for k, paths in self.R.paths.items():
            if not paths:
                continue
            net = ALIAS.get(self.R.names[k], self.R.names[k])    # router aliases of Kelvin trees
            n = sorted(self.R.used_nodes(k))[0]
            x, y = self.R.xy(n[1], n[2])
            self.D.label(LNAME[n[0]] + 'txt', x, y, net, 0.1)


# =================================================================================================
# channel plan
X_VSS = (0.8, 2.4)       # west trunks (Metal4)
# Kelvin trees (router-only net names; the layout net is the same): the output-stage current flows in outp/outn
# (xmo/xml drains, MIM caps); the feedback switch, the CM-sense resistor and the edge pin hang on outp_s/outn_s, which
# joins the current tree at one node of the xmo drain rail. vss_k: Kelvin tap of the RPA arm to the vss trunk.
KELVIN_JUNCTION = {('xmoa', 'outp'), ('xmob', 'outn')}
SENSE = {'xsfb': {'outp': 'outp_s'}, 'xsfa': {'outn': 'outn_s'}, 'xrca_s0': {'outp': 'outp_s'}, 'xrcb_s0': {'outn': 'outn_s'}}
ALIAS = {'vss_k': 'vss', 'outp_s': 'outp', 'outn_s': 'outn'}
X_VDDA = (3.2, 4.8)
X0 = 6.4                 # devices start
GAP_MAIN = 5.6           # gap between the two slots of the main array (input bands isp/isn)
BAND_W = 1.6             # width of the input bands (Metal3)
RF_PAT = 'ABBAABBAABBAAB'                 # columns -7..-1, +1..+7 around the centre column (RIA/RIB)
RP_PAT = 'AABABBABBAABB' + 'AABBAABAABABB'  # columns -20..-8, +8..+20
ROWS_N = [['xmfd', 'xmc1s', 'xms1', 'xmbf', 'xms2', 'xmc2s', 'xmfe', 'xmgd'],
          ['xsfa', 'xspa', 'xmfdc', 'xmn1', 'xmbfc', 'xmn2', 'xmfec', 'xspb', 'xsfb', 'xmgm'],
          ['xmoa', 'xmob', 'xls1_xmn1', 'xls1_xmn2', 'xls1_xmb1n', 'xls1_xmb2n', 'xsva', 'xmbn', 'xmb2', 'xmb3', 'xmb5',
           'xmbnc', 'xsvb', 'xsh1', 'xsh2', 'xls2_xmn1', 'xls2_xmn2', 'xls2_xmb1n', 'xls2_xmb2n']]


def build_channel(ly, W=None, H=None):
    devs = NLM.channel_devices()
    by = {d['name']: d for d in devs}
    W = W or 400.0
    H = H or 400.0
    blk = Block(ly, 'r1_isense_ch', W, H)
    blk.by = by
    # ---------------- resistor band
    pos = list(range(-20, 21))
    cols = {}
    fa = iter(['xrfa%d' % i for i in range(1, 15)]); fb = iter(['xrfb%d' % i for i in range(1, 15)])
    pa = iter(['xrpa%d' % i for i in range(1, 27)]); pb = iter(['xrpb%d' % i for i in range(1, 27)])
    rfpos = list(range(-7, 0)) + list(range(1, 8))
    rppos = list(range(-20, -7)) + list(range(8, 21))
    side = {}
    for p, t in zip(rfpos, RF_PAT):
        side[p] = ('RF', t)
    for p, t in zip(rppos, RP_PAT):
        side[p] = ('RP', t)
    # chain placement: RF chains as explicit snakes (hops in the bottom band; the last RF unit strapped to RIN),
    # RP chains as a generic snake over their columns (left to right)
    def single(c, down):
        return [(c, 1), (c, 0)] if down else [(c, 0), (c, 1)]

    def pair(c1, c2, top=False):
        return [(c1, 1), (c1, 0), (c2, 0), (c2, 1)] if top else [(c1, 0), (c1, 1), (c2, 1), (c2, 0)]
    seqA = single(-7, True) + pair(-4, -3) + pair(5, 6) + pair(2, 1) + [(0, 0)]
    seqB = pair(-6, -5) + pair(3, 4) + single(7, False) + pair(-2, -1, top=True) + [(0, 1)]
    cols = {p: [None, None] for p in pos}
    chainA = ['xrfa%d' % i for i in range(1, 15)] + ['xria']
    chainB = ['xrfb%d' % i for i in range(1, 15)] + ['xrib']
    for seq, ch, t in ((seqA, chainA, 'A'), (seqB, chainB, 'B')):
        assert len(seq) == len(ch)
        for (c, sl), n in zip(seq, ch):
            assert cols[c][sl] is None and (c == 0 or side[c] == ('RF', t)), (c, sl, n)
            cols[c][sl] = by[n]
    for t, names in (('A', ['xrpa%d' % i for i in range(1, 27)]), ('B', ['xrpb%d' % i for i in range(1, 27)])):
        it = iter(names); cur = 'b'
        for p in pos:
            if p != 0 and side[p] == ('RP', t):
                o = (0, 1) if cur == 'b' else (1, 0)
                for sl in o:
                    cols[p][sl] = by[next(it)]
                cur = 't' if cur == 'b' else 'b'
    rpA = [cols[p][sl].get('name') for p in pos if p != 0 and side[p] == ('RP', 'A') for sl in (0, 1)]
    gmain = dict(kind='rppd', w=2, slots=[30.8, 30.8], cols=[cols[p] for p in pos], dummies=2, gap=GAP_MAIN)
    xe, ytop_main, offs_main = blk.res_group(gmain, X0, 3.2)
    # RDG (2 x 25 um segments, w 1) and RZ (3.6 um) columns
    rdg = lambda n: sorted([d for d in devs if d['orig'] == n], key=lambda d: d['seg'])
    gd = dict(kind='rppd', w=1, slots=[25.0, 25.0], cols=[[rdg('xrdg1')[0], rdg('xrdg1')[1]], [rdg('xrdg2')[0], rdg('xrdg2')[1]]], dummies=1)
    xe_d, ytop_d, _ = blk.res_group(gd, xe + 0.8, 3.2)
    gz = dict(kind='rppd', w=1, slots=[3.6], cols=[[by['xrza']], [by['xrzb']]], dummies=1)
    xe_z, ytop_z, _ = blk.res_group(gz, xe + 0.8, gceil(ytop_d + 2.4) + 0.8)
    rh = lambda n: sorted([d for d in devs if d['orig'] == n], key=lambda d: d['seg'])
    hcols = [[d] for d in rh('xrca')] + [[by['xrh1']], [by['xrh2']]] + [[d] for d in rh('xrcb')]
    gh = dict(kind='rhigh', w=1, slots=[37.5], cols=hcols, dummies=1)
    xh0 = max(xe_d, xe_z) + 0.8
    xe_h, ytop_h, _ = blk.res_group(gh, xh0, 3.2)
    # chains
    blk.res_chain(chainA, ['rfoa'] + ['rfa%d' % i for i in range(1, 14)] + ['sa', 'isp'], nopin=('isp',), tap=('sa',))
    blk.res_chain(chainB, ['rfob'] + ['rfb%d' % i for i in range(1, 14)] + ['sb', 'isn'], nopin=('isn',), tap=('sb',))
    # the vss end of the RPA arm is a Kelvin tap (router net vss_k, no current) to the vss trunk at the channel's vss
    # reference point; it is the counterpart of the vref end of the RPB arm
    blk.res_chain(['xrpa%d' % i for i in range(1, 27)], ['vss_k'] + ['rpa%d' % i for i in range(1, 26)] + ['rpas'])
    blk.res_chain(['xrpb%d' % i for i in range(1, 27)], ['vref'] + ['rpb%d' % i for i in range(1, 26)] + ['rpbs'])
    assert blk.ends_np['isp'][1] == 't' and blk.ends_np['isn'][1] == 'b', blk.ends_np
    bands = {}
    for net, (u, e) in blk.ends_np.items():
        xc, ys, L, w, _, _ = blk.respos[u]
        if e == 't':
            h0 = ys + L + 0.13; yv = round(ys + L + 0.7, 3); m1 = (h0, ys + L + 1.0); r2 = (h0, gceil(ys + L + 1.0))
            yc = gceil(ys + L + 0.75)
        else:
            h1 = ys - 0.13; yv = round(ys - 0.7, 3); m1 = (ys - 1.0, h1); r2 = (gfloor(ys - 1.0), h1)
            yc = gfloor(ys - 0.75)
        blk.box('M1', xc + 0.02, m1[0], xc + w - 0.02, m1[1])
        blk.box('M2', xc + 0.02, m1[0], xc + w - 0.02, m1[1])
        for dx in (0.45, 1.0, 1.55):
            blk.D.sq('Via1', xc + dx, yv, VIA)
            blk.D.sq('Via2', xc + dx, yv, VIA)
        blk.R.reserve(0, xc - 0.2, r2[0] - 0.2, xc + w + 0.2, r2[1] + 0.2, net)
        bands[net] = (xc, yc)
    blk.bands = bands
    for n in ('xrdg1', 'xrdg2'):
        s = rdg(n)
        blk.res_chain([d['name'] for d in s], [s[0]['nets'][0], s[0]['nets'][1], s[1]['nets'][1]])
    blk.res_chain(['xrza'], by['xrza']['nets'][:2])
    blk.res_chain(['xrzb'], by['xrzb']['nets'][:2])
    for n in ('xrca', 'xrcb'):
        s = rh(n)
        blk.res_chain([d['name'] for d in s], [s[0]['nets'][0]] + [d['nets'][1] for d in s])
    blk.res_chain(['xrh1'], by['xrh1']['nets'][:2])
    blk.res_chain(['xrh2'], by['xrh2']['nets'][:2])
    res_top = max(ytop_main, ytop_d, ytop_z, ytop_h)
    # ---------------- 1.2 V rows above the rhigh columns
    lv = [[dict(kind='nlv', devs=[by['xls1_xmin'], by['xls2_xmin']])],
          [dict(kind='plv', well='vdd', devs=[by[n] for n in ('xls1_xmip', 'xls2_xmip', 'xmbl', 'xmla', 'xmlb')])]]
    xeast = None
    lvinfo, (lx1, lx2, ly1, ly2) = blk.rows(lv, xh0 + 1.6, ytop_h + 1.0,
                                            tie_east={'vdd': W - 1.6} if W < 399 else None)
    # ---------------- MOS rows
    nrows = [[dict(kind='n', devs=[by[n] for n in r])] for r in ROWS_N]
    tail_x = None
    p1 = [dict(kind='p', well='vdda', devs=[by[n] for n in ('xmbp', 'xmb4', 'xmb6', 'xmp1', 'xmta', 'xmp2', 'xmtg', 'xmbpc')]),
          dict(kind='p', well='gtail', devs=[by['xmg1'], by['xmg2']])]
    p2 = [dict(kind='p', well='vdda', devs=[by[n] for n in ('xls1_xmp1', 'xls1_xmp2', 'xls1_xmb1p', 'xls1_xmb2p', 'xmpc1',
                                                           'xmpc2', 'xls2_xmp1', 'xls2_xmp2', 'xls2_xmb1p', 'xls2_xmb2p')]),
          dict(kind='p', well='tail', devs=[by['xm1_h0'], by['xm2_h0']]),
          dict(kind='p', well='atail', devs=[by['xa1_h0'], by['xa2_h0']])]
    p3 = [dict(kind='p', well='vdda', devs=[by['xmt'], by['xmtc']]),
          dict(kind='p', well='tail', devs=[by['xm2_h1'], by['xm1_h1']]),
          dict(kind='p', well='atail', devs=[by['xa2_h1'], by['xa1_h1']]),
          dict(kind='p', well='ctail', devs=[by['xmf1'], by['xmf2']])]
    # common centroid: the tail and atail segments of p2 and p3 start at the same x
    for k in (1, 2):
        e2, e3 = est_segs(p2, X0), est_segs(p3, X0)
        xk = gceil(max(e2[k - 1][1], e3[k - 1][1]) + 4.6)
        p2[k]['x'] = xk; p3[k]['x'] = xk
    ystart = max(res_top + 1.6, ly2 + 0.8)
    info, (rx1, rx2, ry1, ry2) = blk.rows(nrows + [p1, p2, p3], X0, ystart,
                                          tie_west={'vss': sum(X_VSS) / 2, 'vdda': sum(X_VDDA) / 2})
    blk.stats.update(res_top=res_top, res_x_end=xe_h, lv_rows=[(r['yg'], r['yd']) for r in lvinfo],
                     rows=[dict(yg=r['yg'], yd=r['yd'], x1=r['x1'], segs=[(s['kind'], s.get('well'), round(s['x0'], 2), round(s['x1'], 2)) for s in r['segs']]) for r in info])
    Wn = gceil(max(xe_h + 1.6, rx2 + 1.6, lx2 + 1.6) + 4.0)
    Hn = gceil(ry2 + 2.4)
    blk.stats.update(width_needed=Wn, height_needed=Hn)
    placed = [n for r in ROWS_N for n in r] + [d['name'] for row in (p1, p2, p3) for s in row for d in s['devs']] + \
             [d['name'] for row in lv for s in row for d in s['devs']]
    mosn = [d['name'] for d in devs if d['kind'] in ('nmos', 'pmos', 'nmoslv', 'pmoslv')]
    assert sorted(placed) == sorted(mosn), set(placed) ^ set(mosn)
    resn = [d['name'] for d in devs if d['kind'] in ('rppd', 'rhigh')]
    assert sorted(blk.respos) == sorted(resn), set(blk.respos) ^ set(resn)
    return blk, (Wn, Hn)


CAP_ORDER = [['xci', 'xch1', 'xch2'], ['xcca', 'xccb', 'xcma', 'xcmb']]
EDGE_W = ['vcm', 'outp', 'outn', 'vref', 'ibias', 'az_lv', 'azh_lv']
EDGE_E = ['isp', 'isn']
# hold and summing nodes: routed first; other nets pay GUARD_COST next to them. Guarding the auto-zero clock nets as
# well was tried (layout-dev-12, pex-dev-07) and raised the post-layout offset (-216 -> -295 uV); not used.
GUARDED = ['h1', 'h2', 'xh1', 'xh2', 'sa', 'sb']
GUARD_COST = 6                                    # per grid node next to, over or under a guarded route


def finish_channel(blk, Wc, Hc, log=print):
    by = blk.by
    # MIM over the resistor band (shelf packing from the south-west)
    x, y = X0 + 1.6, 4.0
    rowh = 0.0
    capbox = []
    for shelf in CAP_ORDER:
        x = X0 + 1.6
        for n in shelf:
            s = by[n]['w']
            b = blk.mim(by[n], round(x, 3), round(y + 1.9, 3))
            capbox.append((n, b))
            x = gceil(x + s + 4.8)
            rowh = max(rowh, s + 4.4)
        y = y + rowh; rowh = 0.0
    blk.stats['caps'] = capbox
    blk.stats['caps_top'] = y
    R = blk.R
    # supply trunks
    blk.trunk('vss', X_VSS[0], X_VSS[1], 0.0, Hc)
    kk = R.nid('vss_k')
    knodes = [(2, x, y) for x in gpts(X_VSS[0] + 0.2, X_VSS[1] - 0.2) for y in gpts(Hc / 2 - 1.2, Hc / 2 + 1.2)]
    for (l, x, y) in knodes:
        i, j = R.ij(x, y); R.res[l, i, j] = kk
    for pin in R.pins[R.nid('vss')]:
        pin[:] = [n for n in pin if R.res[n] == R.nid('vss')]
    blk.pin('vss_k', knodes, 'm4')
    blk.trunk('vdda', X_VDDA[0], X_VDDA[1], 0.0, Hc)
    blk.trunk('vdd', Wc - 2.4, Wc - 0.8, 0.0, Hc)
    R.block_edges()
    edge = {}
    for q, net in enumerate(EDGE_W):
        y = gfloor(8.0 + q * (Hc - 16.0) / (len(EDGE_W) - 1))
        R.unblock(1, 0.0, y)
        blk.pin(net + '_s' if net in ('outp', 'outn') else net, [(1, 0.0, y)], 'm3')
        edge.setdefault(net, []).append(('W', 0.0, y))
    for net in EDGE_E:
        # input band: Metal3, BAND_W wide, from the RIA/RIB head stack to the east edge (no router pin)
        xb, y = blk.bands[net]
        blk.box('M3', xb + 0.02, y - BAND_W / 2, Wc, y + BAND_W / 2)
        R.reserve(1, xb, y - BAND_W / 2, Wc, y + BAND_W / 2, net)
        edge.setdefault(net, []).append(('E', Wc, y))
    g = R.route_guarded(GUARDED, cost=GUARD_COST, log=log)
    ok = R.route_all(rounds=ROUTE_ROUNDS, log=log) and len(g) == len(GUARDED)
    blk.stats['route_ok'] = ok
    blk.stats['route_failed'] = R.failed
    blk.draw_routes()
    for net, lst in edge.items():
        for (_, x, y) in lst:
            blk.D.label('M3txt', x, y, net, 0.1)
    for net, xr in (('vss', X_VSS), ('vdda', X_VDDA), ('vdd', (Wc - 2.4, Wc - 0.8))):
        blk.D.label('M4txt', sum(xr) / 2, Hc / 2, net, 0.1)
    blk.D.boundary(0, 0, Wc, Hc)
    return edge


MARGIN = 3.2          # guard ring band
STRIP = 4.8           # west routing strip
GAP = 1.6             # between the channels
SOUTH_PINS = ['vcm', 'vref', 'ibias_a', 'az_a', 'azh_a']     # west of the supply stubs, x = 1.6 + 0.8 q
NORTH_PINS = ['az_b', 'azh_b', 'ibias_b']


def build_top(ly, chcell, Wc, Hc, edge, log=print):
    insts, ports = NLM.top_info()
    W = round(MARGIN + STRIP + Wc + MARGIN, 4)
    ya = MARGIN + 2.4
    yb = round(ya + Hc + GAP, 4)
    H = round(yb + Hc + MARGIN, 4)
    xc = MARGIN + STRIP
    blk = Block(ly, 'r1_isense', W, H)
    R = blk.R
    for name, y in (('xcha', ya), ('xchb', yb)):
        blk.D.inst(chcell, xc, y)
    pm = dict(insts)
    for name, y0 in (('xcha', ya), ('xchb', yb)):
        R.block_area([0, 1, 2], xc, y0, xc + Wc, y0 + Hc)
        for port, lst in edge.items():
            if port in EDGE_E:
                continue
            for (side, x, y) in lst:
                X, Y = round(xc + x, 4), round(y0 + y, 4)
                R.unblock(1, X, Y)
                blk.pin(pm[name][port], [(1, X, Y)], 'm3')
    # supply trunks: continue the channel trunks between the channels and down to the south edge (Metal4 -> Metal3 pins)
    sup = {}
    for net, (x1, x2) in (('vss', X_VSS), ('vdda', X_VDDA), ('vdd', (Wc - 2.4, Wc - 0.8))):
        X1, X2 = xc + x1, xc + x2
        blk.box('M4', X1, 0.0, X2, yb + 0.01)
        R.reserve(2, X1, 0.0, X2, yb, net)
        # Metal3 pin stub at the south edge with a Via3 array
        blk.box('M3', X1, 0.0, X2, 2.4)
        blk.box('M3pin', X1, 0.0, X2, 1.2)
        for yy in (0.6, 1.2, 1.8):
            for xx in gpts(X1 + 0.25, X2 - 0.25)[:2] or [(X1 + X2) / 2]:
                blk.D.sq('Via3', xx, yy, VIA)
        R.block_area([1], X1, 0.0, X2, 2.4)
        blk.D.label('M3txt', (X1 + X2) / 2, 0.6, net, 0.3)
        sup[net] = (X1, X2)
    R.block_edges()
    # p+ guard ring (vss)
    blk.D.tap_ring(2.7, 2.7, W - 2.7, H - 2.7, w=0.6, ptype=True)
    ring = [(0, x, 2.4) for x in gpts(4.0, W - 4.0)] + [(0, x, H - 2.4) for x in gpts(4.0, W - 4.0)]
    ring += [(0, 2.4, y) for y in gpts(4.0, H - 4.0)] + [(0, W - 2.4, y) for y in gpts(4.0, H - 4.0)]
    ring = [n for n in ring if not any(a - 0.6 <= n[1] <= b + 0.6 for a, b in sup.values())]
    blk.pin('vss', ring, 'm1')
    # vss trunk joins the ring: vss trunk Metal4 nodes as pins
    X1, X2 = sup['vss']
    blk.pin('vss', [(2, x, y) for x in gpts(X1 + 0.2, X2 - 0.2) for y in gpts(4.0, ya - 1.0)], 'm4')
    bp = []
    # west pins: per channel near the channel's edge pins, shared vref/vcm once
    used_y = []
    # floorplan S7 (PLAN.md D10 amendment): outputs on the west edge; controls, bias and references of channel A and
    # the shared vref/vcm on the south edge, those of channel B on the north edge; supplies on the south edge
    for name, y0 in (('xcha', ya), ('xchb', yb)):
        for port in ('outp', 'outn'):
            net = pm[name][port]
            y = round(y0 + edge[port][0][2], 4)
            bp.append((net, 'W', 0.8, y))
    for q, net in enumerate(SOUTH_PINS):
        bp.append((net, 'S', round(1.6 + 0.8 * q, 4), 0.8))
    for q, net in enumerate(NORTH_PINS):
        bp.append((net, 'N', round(1.6 + 0.8 * q, 4), round(H - 0.8, 4)))
    bands = []
    for name, y0 in (('xcha', ya), ('xchb', yb)):
        for port in EDGE_E:
            net = pm[name][port]
            y = round(y0 + edge[port][0][2], 4)
            blk.box('M3', xc + Wc - 0.01, y - BAND_W / 2, W, y + BAND_W / 2)
            blk.box('M3pin', W - 1.2, y - BAND_W / 2, W, y + BAND_W / 2)
            R.reserve(1, xc + Wc, y - BAND_W / 2, W, y + BAND_W / 2, net)
            bands.append((net, 'E', round(W - 0.6, 4), y))
    for net, side, x, y in bp:
        R.unblock(1, x, y)
        blk.pin(net, [(1, x, y)], 'm3')
    ok = R.route_all(rounds=ROUTE_ROUNDS, log=log)
    blk.stats.update(route_ok=ok, route_failed=R.failed, W=W, H=H)
    blk.draw_routes()
    for net, side, x, y in bp:
        if side == 'W':
            blk.box('M3', 0.0, y - 0.2, x + 0.2, y + 0.2); blk.box('M3pin', 0.0, y - 0.2, x + 0.2, y + 0.2)
        elif side == 'S':
            blk.box('M3', x - 0.2, 0.0, x + 0.2, y + 0.2); blk.box('M3pin', x - 0.2, 0.0, x + 0.2, y + 0.2)
        elif side == 'N':
            blk.box('M3', x - 0.2, y - 0.2, x + 0.2, H); blk.box('M3pin', x - 0.2, y - 0.2, x + 0.2, H)
        else:
            blk.box('M3', x - 0.2, y - 0.2, W, y + 0.2); blk.box('M3pin', x - 0.2, y - 0.2, W, y + 0.2)
        blk.D.label('M3txt', x, y, net, 0.3)
    for net, side, x, y in bands:
        blk.D.label('M3txt', x, y, net, 0.3)
    bp = bp + bands
    blk.D.boundary(0, 0, W, H)
    blk.stats['pins'] = bp + [(n, 'S', (a + b) / 2, 0.6) for n, (a, b) in sup.items()]
    return blk


def main():
    import time
    t0 = time.time()
    ly = pya.Layout(); ly.dbu = 0.001
    NLM.write_cdl()
    ly0 = pya.Layout(); ly0.dbu = 0.001
    b0, (Wc, Hc) = build_channel(ly0)
    print('channel size', Wc, Hc, json.dumps(b0.stats))
    if globals().get('dry', '0') == '1':
        return
    blk, _ = build_channel(ly, Wc, Hc)
    edge = finish_channel(blk, Wc, Hc)
    print('channel routed', blk.stats['route_ok'], blk.stats['route_failed'], '%.0f s' % (time.time() - t0))
    top = build_top(ly, blk.cell, Wc, Hc, edge)
    print('top routed', top.stats['route_ok'], top.stats['route_failed'], 'size', top.stats['W'], top.stats['H'],
          'area %.5f mm2' % (top.stats['W'] * top.stats['H'] * 1e-6), '%.0f s' % (time.time() - t0))
    ly.write(OUT)
    st = dict(channel=dict(W=Wc, H=Hc, route_ok=blk.stats['route_ok'], failed=blk.stats['route_failed'],
                           rows=blk.stats['rows'], lv_rows=blk.stats['lv_rows'], caps=blk.stats['caps'],
                           caps_top=blk.stats.get('caps_top'), res_top=blk.stats['res_top']),
              top=dict(W=top.stats['W'], H=top.stats['H'], area_mm2=round(top.stats['W'] * top.stats['H'] * 1e-6, 6),
                       route_ok=top.stats['route_ok'], failed=top.stats['route_failed'], pins=top.stats['pins']),
              runtime_s=round(time.time() - t0, 1))
    json.dump(st, open(os.path.join(os.path.dirname(OUT), 'r1_isense_layout.json'), 'w'), indent=1)


main()
