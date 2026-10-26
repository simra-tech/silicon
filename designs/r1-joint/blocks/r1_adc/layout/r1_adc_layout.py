#!/usr/bin/env python3
"""r1_adc layout generator (revision 5 netlist of record, unchanged): KLayout 0.30.9 batch Python in the pinned container.

  G1_WORKDIR=designs/r1-joint/blocks/r1_adc/layout flow/run.sh klayout -b -r r1_adc_layout.py [-rd out=<gds>]
  writes r1_adc.gds (top cell r1_adc, child cell r1_adc_slice placed twice as a translated copy), r1_adc_lvs.cdl
  (via r1_adc_netlist.py), r1_adc_decap.json, r1_adc_layout.json (box, pins, router statistics, CDAC map, ports).

Floorplan (box 439.0 x 182.3 um, integration checklist e):
  * south band (y 1.6 - 54): reference buffer r1_refbuf5 (thick-oxide rows) at the centre, comparator biases and their
    rppd resistors at the west, wide vref / vrefl buses (Metal3 + Metal4, full width) at y 45 - 51.
  * decoupling MIM (vref 4 plates, vrefl 2, error-amplifier Cg 1, vref_in filter 2; 95 um tall plates, total area as
    the netlist of record) over the whole south part of the block, above the FEOL of the south band and of the lower
    part of both slices (MIM over MOS, Metal1-4 routing below).
  * two slices r1_adc_slice (213.6 x 111.2 um) side by side, identical translated copies: CDAC array (34 x 12 slots
    of 5.45 um: N LSB 4 rows, N MSB, P MSB, P LSB 4 rows, one dummy ring), in0 bootstrapped switches + Cboot at the
    west end, in1 switches + Cboot at the east end, bottom-plate drivers in two rows under the array, comparators
    r1_cmp4 + r1_cmp5n below them.
  * north channel: long input pairs COS (west pins -> slice B in0) and ISA (east pins -> slice A in1) between vss
    shield lines, the comparator clock generator r1_cmp4_clkgen at the north-west next to the clk pin.
  * p+ guard ring at the boundary, pins on Metal3 at the checklist positions.
Layers: Metal1-Metal4 routing (maze router + hand-drawn buses), Metal5 only as MIM bottom plates and TopVia1 islands,
TopMetal1 only on MIM plates, their sheets and 1.64 um tabs; no TopMetal2. Boundary on 189/4.
"""
import json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from adc_lib import *            # noqa  Block, gceil, gfloor, gnear, gpts, s5, pya, LAYERS, Mos, VIA, TV1, ...
import r1_adc_netlist as NLM
from maze_router import P, LNAME

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass
OUT = globals().get('out', os.path.join(HERE, 'r1_adc.gds'))
ROUNDS = int(globals().get('rounds', '6'))
TRIM = json.load(open(globals()['trim'])) if globals().get('trim') else {}

W, H = 439.0, 182.3
SX = [3.2, 223.2]                 # slice origins (x); y origin SY
SY = 54.4                         # on the 0.8 um router grid; slice edge pins at global 110.4 / 114.4 (stubs jog to 110 / 114)
WS, HS = 213.6, 111.2
SP = 5.45                         # CDAC slot pitch
NC, NR = 34, 12
AX, AY = 14.15, 45.2              # array origin inside the slice
CU, C0S, CBS = NLM.CU, NLM.C0S, NLM.CBS
GAPS = {(4, 0), (5, 0), (6, 0), (7, 0), (5, 33), (6, 33)}    # ring slots left open for the plate tabs
LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s)


# =====================================================================================================================
# device drawing
# =====================================================================================================================
class Blk(Block):
    def __init__(self, ly, name, W_, H_):
        Block.__init__(self, ly, name, W_, H_)
        self.labels = []          # (layer, x, y, text)
        self.devinfo = {}         # device -> dict(term -> (layer, x, y)) for top-level labels
        self.tgo = []             # ThickGateOx boxes drawn by mrow (gaps below TGO.e 0.86 are filled afterwards)

    SPLIT = ('top_p', 'top_n')    # nets carried by the TopMetal1 sheet: device pins join the nearer island half

    def pin(self, net, nodes, kind='m2'):
        """device pins on a sheet net go to the router net of the nearer island (net@W west of the array centre,
        net@E east of it); the TopMetal1 sheet joins the two halves."""
        if net in self.SPLIT and self.name == 'r1_adc_slice':
            xm = sum(n[1] for n in nodes) / len(nodes)
            net = net + ('@W' if xm < AX + NC * SP / 2 else '@E')
        return Block.pin(self, net, nodes, kind)

    def port(self, dev, term, net, layer, box=None, pt=None):
        Block.port(self, dev, term, net.split('@')[0], layer, box=box, pt=pt)

    def reserve_box(self, layer_idx, x1, y1, x2, y2, net):
        self.R.reserve(layer_idx, x1, y1, x2, y2, net)

    def dev(self, d, xa, yg):
        """draw device d with its footprint starting at xa, gate rail at yg. Returns (right, top).
        The LV PCells (nmos, pmos) accept at most 10 um per finger and silently fall back to 0.15 um above that, so a
        wider finger is split: ng becomes ng * ceil(wf / 10). Total W and L stay as in the netlist of record."""
        if self.name == 'r1_adc_slice' and any(n in self.SPLIT for n in d['nets']):
            side = '@W' if xa < AX + NC * SP / 2 else '@E'
            d = dict(d, nets=[n + side if n in self.SPLIT else n for n in d['nets']])
        if d['kind'] in ('nmos', 'pmos') and d['w'] / d['ng'] > 10.0 + 1e-9:
            d = dict(d, ng=d['ng'] * int(math.ceil(d['w'] / d['ng'] / 10.0 - 1e-9)))
        if d['kind'] in ('nmos', 'pmos') and d['w'] / d['ng'] < 0.30 - 1e-9:
            return self.narrow(d, xa, yg)
        if d['kind'] in ('nmosHV', 'pmosHV') or d['l'] >= 0.45:
            x0 = round(xa + 0.2 + d['l'] + 0.35, 3)
            m, right, yd = self.mos(d, x0, yg)
            Dn, Gn, Sn, Bn = d['nets']
            self.devinfo[d['name']] = dict(g=(0, gnear(m.gx(0)), yg), d=(0, None, yd), s=(0, None, yg - P))
            return right + 0.2 + d['l'] + 0.35 - 0.35, yd + 0.2
        return self.lvmos(d, xa, yg)

    def narrow(self, d, xa, yg):
        """single-finger LV MOS with W < 0.30 um: the PCell draws a dogbone (0.30 um contact pads, gate at x0 + 0.37),
        so the Mos strip model does not apply. Gate bar below to a contact and the Metal2 gate rail at yg; source strip
        down to a Metal1 rail at yg - P; drain strip up to a Metal1 rail at yg + 2P."""
        kind = d['kind']; w, l = round(d['w'], 3), round(d['l'], 3)
        assert d['ng'] == 1, d
        Dn, Gn, Sn, Bn = d['nets']
        x0 = s5(xa + 0.6); y0 = round(yg + 0.33, 4)
        self.D.pcell(kind, {'w': '%gu' % w, 'l': '%gu' % l, 'ng': 1}, x0, y0)
        gx = round(x0 + 0.37 + l / 2, 4); xs_ = round(x0 + 0.15, 4); xd_ = round(x0 + 0.37 + l + 0.07 + 0.15, 4)
        self.box('GatPoly', gx - l / 2, yg - 0.15, gx + l / 2, y0 - 0.12)
        self.D.sq('Cont', gx, yg, 0.16); self.D.sq('M1', gx, yg, 0.30); self.D.sq('Via1', gx, yg, VIA)
        xn = gnear(gx)
        gl, gr = min(gx, xn) - 0.2, max(gx, xn) + 0.2
        self.box('M2', gl, yg - 0.20, gr, yg + 0.20)
        self.R.reserve(0, gl, yg - 0.20, gr, yg + 0.20, Gn)
        self.pin(Gn, [(0, xn, yg)], 'm2')
        yS, yD = round(yg - P, 4), round(yg + 2 * P, 4)
        for xc, ya, yb, yr, net, term in ((xs_, yS - 0.25, y0 + 0.28, yS, Sn, 2), (xd_, y0 + 0.02, yD + 0.25, yD, Dn, 0)):
            self.box('M1', xc - 0.08, ya, xc + 0.08, yb)
            xr = gnear(xc) if term == 0 else gfloor(xc)
            rl, rr = min(xc - 0.13, xr - 0.2), max(xc + 0.13, xr + 0.2)
            self.box('M1', rl, yr - 0.25, rr, yr + 0.25)
            self.port(d['name'], term, net, 1, box=(rl, yr - 0.25, rr, yr + 0.25))
            self.pin(net, [(0, xr, yr)], 'm1')
        self.devinfo[d['name']] = dict(g=(0, xn, yg), d=(0, None, yD), s=(0, None, yS))
        self.devpos[d['name']] = (x0, y0, x0 + 0.37 + l + 0.37, y0 + 0.30)
        return max(xd_ + 0.13, gr) + 0.6, yD + 0.45

    def lvmos(self, d, xa, yg):
        """LV MOS with l < 0.45 um: gate bar + Metal2 rail at the bottom (yg), source strips up to a Metal1 rail at
        yS, drain strips by Via1 inside the active to Metal2 risers and a Metal2 rail at yD = yS + P."""
        kind = d['kind']
        w, l, ng = round(d['w'], 3), round(d['l'], 3), d['ng']
        Dn, Gn, Sn, Bn = d['nets']
        x0 = s5(xa + 1.1)
        y0 = round(yg + 0.33, 4)
        if w / ng < 0.15 - 1e-9:
            raise RuntimeError('finger below 0.15 um: %s' % d['name'])
        m = Mos(self.D, kind, w, l, ng, x0, y0)
        wf = m.wf
        # gate
        rl, rr, ra, rb = m.gate_bar('bot')
        if l < 0.30:
            self.box('GatPoly', m.gx(0) - 0.15, m.yd('bot', 0.48), m.gx(ng - 1) + 0.15, m.yd('bot', 0.18))
        gx = [x for x in gpts(rl + 0.2, rr - 0.2)]
        if not gx:
            gx = [gnear((rl + rr) / 2)]
        gl, gr = min(rl, gx[0] - 0.2), max(rr, gx[-1] + 0.2)
        self.box('M2', gl, yg - 0.20, gr, yg + 0.20)
        self.grails.append((Gn, gl, gr, yg))      # draw_routes closes short gaps between the rail end and a via pad
        self.R.reserve(0, gl, yg - 0.20, gr, yg + 0.20, Gn)
        self.pin(Gn, [(0, x, yg) for x in gx], 'm2')
        # strips
        S = m.strips(0)
        Dk = m.strips(1)
        yS = gceil(y0 + wf + 0.40)
        yD = round(yS + P, 4)
        sxD = [m.sx(k) for k in Dk]
        cand = [x for x in gpts(xa + 0.25, m.sx(S[-1]) + 0.13) if all(abs(x - q) >= 0.60 for q in sxD)]
        cand = [x for x in cand if x <= m.sx(S[0]) + 0.13 or len(S) > 1]
        if not cand:
            raise RuntimeError('no source pin node for %s' % d['name'])
        xs_pin = cand[:1] if len(cand) == 1 else [cand[0]]
        for k in S:
            x = m.sx(k)
            self.box('M1', x - 0.08, y0 + wf - 0.01, x + 0.08, yS + 0.15)
        sl = min(xs_pin[0] - 0.17, m.sx(S[0]) - 0.13)
        sr = max(xs_pin[-1] + 0.17, m.sx(S[-1]) + 0.13)
        self.box('M1', sl, yS - 0.17, sr, yS + 0.17)      # 0.34 tall: flush with the 0.34 Via1 pad of an m1 pin
        self.pin(Sn, [(0, x, yS) for x in xs_pin], 'm1')
        self.port(d['name'], 2, Sn, 1, box=(sl, yS - 0.17, sr, yS + 0.17))
        # drain
        yv = round(y0 + wf - min(0.18, wf / 2), 4)
        for x in sxD:
            hp = min(0.18, wf / 2)
            self.box('M1', x - 0.13, yv - hp, x + 0.13, yv + hp)
            self.D.sq('Via1', x, yv, VIA)
            self.box('M2', x - 0.13, yv - 0.15, x + 0.13, yD + 0.2)
            self.R.reserve(0, x - 0.13, yv - 0.15, x + 0.13, yD + 0.2, Dn)
            # no router node next to the riser below the rail, not even for the drain net (M2.b notch)
            self.R.reserve(0, x - 0.13, yv - 0.15, x + 0.13, yD - 0.6, None, clear=0.42)
        dc = [x for x in gpts(sxD[0] - 0.13, sxD[-1] + 1.0)]
        dpin = [dc[-1]] if len(dc) and dc[-1] > sxD[-1] else dc[:1]
        dl = min(sxD[0] - 0.13, dpin[0] - 0.2)
        dr = max(sxD[-1] + 0.13, dpin[-1] + 0.2)
        self.box('M2', dl, yD - 0.2, dr, yD + 0.2)
        self.R.reserve(0, dl, yD - 0.2, dr, yD + 0.2, Dn)
        self.pin(Dn, [(0, x, yD) for x in dpin], 'm2')
        self.port(d['name'], 0, Dn, 2, box=(dl, yD - 0.2, dr, yD + 0.2))
        self.port(d['name'], 1, Gn, 2, box=(gl, yg - 0.2, gr, yg + 0.2))
        self.devinfo[d['name']] = dict(g=(0, gx[0], yg), d=(0, dpin[0], yD), s=(0, xs_pin[0], yS))
        self.devpos[d['name']] = (m.x0, m.y0, m.x1, m.y1)
        right = max(dr, m.x1 + 0.3, gr, sr)
        return right + 0.25, yD + 0.2

    def mrow(self, segs, yg, kind):
        """segments of devices on one gate rail yg. segs: [dict(x0, devs, bulk)]; kind 'n', 'p', 'nHV', 'pHV'.
        Each segment: tie strip (bulk net) at yg - 2P, NWell for PMOS, TGO for thick oxide. Returns (top, ends)."""
        top = yg
        ends = []
        for sg in segs:
            x = sg['x0']
            for d in sg['devs']:
                r, t = self.dev(d, x, yg)
                top = max(top, t)
                x = r + sg.get('gap', 0.3)
            xa, xb = sg['x0'], x
            yt = round(yg - 2 * P, 4)
            ptap = kind.startswith('n')
            self.D.tap_strip(xa + 0.2, xb - 0.2, yt, ptype=ptap, w=0.30, inset=0.2)
            self.pin(sg['bulk'], [(0, xx, yt) for xx in gpts(xa + 0.6, xb - 0.6)], 'm1')
            if not ptap:
                self.box('NWell', xa - 0.6, yt - 0.8, xb + 0.6, top + 0.3)
            if kind.endswith('HV'):
                tb = (xa - 0.6 - (0.3 if not ptap else 0), yt - 0.9, xb + 0.6 + (0.3 if not ptap else 0), top + 0.6)
                self.box('TGO', *tb)
                self.tgo.append(tb)
            ends.append((xa, xb))
            sg['xend'] = xb
        return top, ends

    def seg_w(self, devs, gap=0.3):
        """estimated footprint width of a device list (dry run on a scratch layout)."""
        ly = pya.Layout(); ly.dbu = 0.001
        b = Blk(ly, 'scratch', 400.0, 60.0)
        x = 0.0
        for d in devs:
            r, t = b.dev(d, x, 10.4)
            x = r + gap
        return x

    def label(self, layer, x, y, text):
        self.labels.append((layer, x, y, text))


# =====================================================================================================================
# CDAC array
# =====================================================================================================================
def cc_assign(n_r, n_c, counts, split_at='centre'):
    """common-centroid assignment on an n_r x n_c grid: point-symmetric pairs (r, c) <-> (n_r-1-r, n_c-1-c) sorted by
    distance from the centre, each pair to the bit furthest behind its share. counts: [(name, pairs)]; a name may be a
    tuple (a, b) for a pair split into two singletons. Returns {(r, c): name}."""
    cr, cc = (n_r - 1) / 2, (n_c - 1) / 2
    pairs = []
    for r in range(n_r):
        for c in range(n_c):
            r2, c2 = n_r - 1 - r, n_c - 1 - c
            if (r, c) < (r2, c2):
                pairs.append(((r, c), (r2, c2)))
    pairs.sort(key=lambda p: ((p[0][0] - cr) ** 2 + ((p[0][1] - cc) * 1.0) ** 2, p[0]))
    total = sum(n for _, n in counts)
    assert total == len(pairs), (total, len(pairs))
    done = {name: 0 for name, _ in counts}
    out = {}
    split = [nm for nm, n in counts if isinstance(nm, tuple)]
    if split_at == 'edge':          # the split pair takes the outermost pair (CB clear of the other side's CB)
        pairs = [pairs[-1]] + pairs[:-1]
    for q, (a, b) in enumerate(pairs):
        if q == 0 and split:
            nm = split[0]
            out[a], out[b] = nm[0], nm[1]
            done[nm] += 1
            continue
        best = None
        for nm, n in counts:
            if isinstance(nm, tuple) or done[nm] >= n:
                continue
            key = ((done[nm] + 0.5) / n, -n)
            if best is None or key < best[0]:
                best = (key, nm)
        nm = best[1]
        out[a], out[b] = nm, nm
        done[nm] += 1
    return out


def cdac_map():
    """slot (r, c) -> dict(kind, w, top, bot) for the whole slice array (rows 0..11, cols 0..33)."""
    lsb = cc_assign(4, 32, [(7, 32), (6, 16), (5, 8), (4, 4), (3, 2), (2, 1), ((1, 0), 1)])
    # MSB rows: (C8, CB) on the end pair; the P row is the mirror of the N row, so the two bridge caps (Metal5 plate
    # 5.43 um, too wide to sit next to each other at the 5.45 um pitch) are at opposite ends: N at col 32, P at col 1.
    msb = cc_assign(1, 32, [(12, 8), (11, 4), (10, 2), (9, 1), ((8, 'cb'), 1)], split_at='edge')
    slots = {}
    for c in range(NC):
        for r in range(NR):
            if r in (0, NR - 1) or c in (0, NC - 1):
                if (r, c) not in GAPS:
                    slots[(r, c)] = dict(kind='dummy', w=CU, top='gnd', bot='gnd', sheet='ring')
    for side, rows, mrow in (('n', [1, 2, 3, 4], 5), ('p', [10, 9, 8, 7], 6)):
        for q, r in enumerate(rows):
            for c in range(32):
                b = lsb[(q, c)]
                slots[(r, c + 1)] = dict(kind='u', w=C0S if b == 0 else CU, top='lsb_' + side, bot='b%s%d' % (side, b),
                                         sheet='lsb_' + side, bit=b)
        for c in range(32):
            b = msb[(0, c)] if side == 'n' else msb[(0, 31 - c)]
            if b == 'cb':
                slots[(mrow, c + 1)] = dict(kind='u', w=CBS, top='top_' + side, bot='lsb_' + side, sheet='top_' + side, bit='cb')
            else:
                slots[(mrow, c + 1)] = dict(kind='u', w=CU, top='top_' + side, bot='b%s%d' % (side, b), sheet='top_' + side, bit=b)
    return slots


def slot_c(r, c):
    return (round(AX + (c + 0.5) * SP, 4), round(AY + (r + 0.5) * SP, 4))


def draw_cdac(blk, coll_x):
    """draw the array; coll_x: {bottom net: collector x}. Returns tab islands {name: (x, y)} and stats."""
    D = blk.D
    slots = cdac_map()
    # units
    for (r, c), s in slots.items():
        xc, yc = slot_c(r, c)
        w = s['w']
        D.pcell('cmim', {'Calculate': 'C', 'w': '%gu' % w, 'l': '%gu' % w}, s5(xc - w / 2), s5(yc - w / 2))
    # TopMetal1 sheets (centre-to-centre bridges 3.46 um wide) and Metal5 ring merge
    def sheet(rc):
        s = slots.get(rc)
        return s['sheet'] if s else None
    for (r, c), s in slots.items():
        xc, yc = slot_c(r, c)
        for dr, dc in ((0, 1), (1, 0)):
            nb = (r + dr, c + dc)
            if sheet(nb) == s['sheet']:
                x2, y2 = slot_c(*nb)
                if dr == 0:
                    blk.box('TM1', xc, yc - 1.73, x2, yc + 1.73)
                else:
                    blk.box('TM1', xc - 1.73, yc, xc + 1.73, y2)
                if s['sheet'] == 'ring':
                    if dr == 0:
                        blk.box('M5', xc, yc - 2.49, x2, yc + 2.49)
                    else:
                        blk.box('M5', xc - 2.49, yc, xc + 2.49, y2)
    # Metal5 ring through the west tab gaps (rows 3 -> 8 at col 0) and the east gaps (rows 4 -> 7 at col 33)
    for c, ra, rb in ((0, 3, 8), (33, 4, 7)):
        xa, ya = slot_c(ra, c); xb, yb = slot_c(rb, c)
        blk.box('M5', xa - 2.49, ya, xa + 2.49, yb)
    # bottom plates: Via4 at the unit centre, Metal4 stub to the net's Metal3 track of the row
    tracks = {}
    for r in range(1, NR - 1):
        nets = sorted(set(s['bot'] for (rr, c), s in slots.items() if rr == r and s['kind'] == 'u'),
                      key=lambda n: (len(n), n))
        for t, n in enumerate(nets):
            tracks[(r, n)] = round(AY + r * SP + 0.45 + 0.6 * t, 4)
    span = {}
    for (r, c), s in slots.items():
        if s['kind'] != 'u':
            continue
        xc, yc = slot_c(r, c)
        yt = tracks[(r, s['bot'])]
        D.sq('Via4', xc, yc, VIA); D.sq('M4', xc, yc, 0.40)
        blk.box('M4', xc - 0.2, min(yc, yt), xc + 0.2, max(yc, yt))     # 0.40 wide: no notch at the 0.40 pads
        D.sq('Via3', xc, yt, VIA); D.sq('M4', xc, yt, 0.40); D.sq('M3', xc, yt, 0.40)
        k = (r, s['bot'])
        span.setdefault(k, []).append(xc)
    # tracks to the collectors; collectors (Metal4, vertical) from below the array to the top track of the net
    yc0 = gfloor(AY - 0.4)
    ctop = {}
    for (r, n), xs in span.items():
        x = coll_x[n]
        xa, xb = min(xs + [x]), max(xs + [x])
        yt = tracks[(r, n)]
        blk.box('M3', xa - 0.2, yt - 0.15, xb + 0.2, yt + 0.15)
        blk.R.reserve(1, xa - 0.2, yt - 0.15, xb + 0.2, yt + 0.15, None)
        D.sq('Via3', x, yt, VIA); D.sq('M3', x, yt, 0.40); D.sq('M4', x, yt, 0.40)
        ctop[n] = max(ctop.get(n, 0), yt)
    for n, x in coll_x.items():
        blk.box('M4', x - 0.15, yc0, x + 0.15, ctop[n] + 0.2)
        blk.R.reserve(2, x - 0.15, yc0 + 0.6, x + 0.15, ctop[n] + 0.2, None)
        blk.pin(n, [(2, x, yc0)], 'm4')
        blk.port('@coll', 0, n, 4, pt=(x, yc0))
    # whole array band: no router use of Metal3/Metal4 inside (tracks, stubs, collectors), Metal2 free
    blk.R.block_area([1, 2], AX, AY, AX + NC * SP, AY + NR * SP)
    # tabs: TopMetal1 from the end unit through the gap slot to a TopVia1 island west / east of the array
    xw = gfloor(AX - 1.0); xe = gceil(AX + NC * SP + 1.0)
    isl = {}
    for (r, c, net, xi) in ((4, 0, 'lsb_n', xw), (5, 0, 'top_n@W', xw), (6, 0, 'top_p@W', xw), (7, 0, 'lsb_p', xw),
                            (5, 33, 'top_n@E', xe), (6, 33, 'top_p@E', xe)):
        xc, yc = slot_c(r, c + (1 if c == 0 else -1))
        yi = gnear(slot_c(r, c)[1])
        if c == 0:
            blk.box('TM1', xi - 0.82, yi - 0.82, xc, yi + 0.82)
        else:
            blk.box('TM1', xc, yi - 0.82, xi + 0.82, yi + 0.82)
        island(blk, xi, yi, net)
        isl[net] = (xi, yi)
    # dummy ring: two TopMetal1 parts (west column split by the gaps) -> tabs at the west corners, joined to Metal5
    for r in (0, NR - 1):
        xc, yc = slot_c(r, 0)
        yi = gnear(yc)
        blk.box('TM1', xw - 0.82, yi - 0.82, xc, yi + 0.82)
        blk.box('M5', xw - 0.33, yi - 0.33, xc, yi + 0.33)
        island(blk, xw, yi, 'gnd')
        isl['ring%d' % r] = (xw, yi)
    return slots, tracks, isl


def island(blk, x, y, net, pin=True):
    """TopVia1 island: TopMetal1 1.64 square, TopVia1, Metal5 0.66, Via4, Metal4 0.40 (router pin)."""
    blk.box('TM1', x - 0.82, y - 0.82, x + 0.82, y + 0.82)
    blk.D.sq('TV1', x, y, TV1)
    blk.D.sq('M5', x, y, TV1 + 2 * TV1_M5)
    blk.D.sq('Via4', x, y, VIA)
    blk.D.sq('M4', x, y, 0.40)
    if pin:
        blk.pin(net, [(2, x, y)], 'm4')
        blk.port('@isl', 0, net.split('@')[0], 4, pt=(x, y))


def cboot(blk, d, mx, my, xi, yi, xb, yb):
    """bootstrap capacitor: MIM 11.49 at (mx, my), top plate tab to the island (xi, yi), bottom plate Via4 at (xb, yb)."""
    w = d['w']
    blk.D.pcell('cmim', {'Calculate': 'C', 'w': '%gu' % w, 'l': '%gu' % w}, mx, my)
    top, bot = d['nets']
    cx = mx + w / 2
    blk.box('TM1', xi - 0.82, min(yi, my + w / 2), xi + 0.82, max(yi, my + w / 2))
    island(blk, xi, yi, top)
    blk.D.sq('Via4', xb, yb, VIA); blk.D.sq('M4', xb, yb, 0.40)
    blk.pin(bot, [(2, xb, yb)], 'm4')
    blk.port(d['name'], 1, bot, 4, pt=(xb, yb))


# =====================================================================================================================
# slice
# =====================================================================================================================
SLICE_SOUTH = [('gnd', 4.0), ('vdd', 12.0), ('vbn', 140.0), ('vbp', 144.0), ('vrefl', 100.0), ('vref', 106.4),
               ('vrefl', 112.8), ('gnd', 60.0), ('vdd', 68.0), ('gnd', 160.0), ('vdd', 170.4), ('gnd', 200.0), ('vdd', 208.0)]
SLICE_WEST = [('in0p', 56.0), ('in0n', 60.0)]
SLICE_EAST = [('in1p', 76.0), ('in1n', 80.0)]     # global 130.4 / 134.4 (ISB pins 130 / 134)
SLICE_PAIRS = [('top_p@W', 'top_n@W'), ('top_p@E', 'top_n@E'), ('in0p', 'in0n'), ('in1p', 'in1n'),
               ('xc4_dip', 'xc4_din'), ('op', 'on'), ('xc5_dip', 'xc5_din'), ('onp', 'onn')]


def build_slice(ly):
    devs = NLM.slice_devices(NLM.NDUMMY)
    by = {d['name']: d for d in devs}
    blk = Blk(ly, 'r1_adc_slice', WS, HS)
    R = blk.R
    # ---- drivers (two rows under the array) ------------------------------------------------------------------
    nl = ['xdn%d' % k for k in range(8)]
    nm = ['xdn%d' % k for k in range(8, 13)]
    pm = ['xdp%d' % k for k in range(12, 7, -1)]
    pl = ['xdp%d' % k for k in range(7, -1, -1)]
    pmos_groups = [('vrefl', [n + '_xmp' for n in nl] + ['xlrn']), ('vref', [n + '_xmp' for n in nm + pm]),
                   ('vrefl', ['xlrp'] + [n + '_xmp' for n in pl])]
    nmos_list = [n + '_xmn' for n in nl + nm + pm + pl]
    wP = [blk.seg_w([by[n] for n in g], 0.6) for _, g in pmos_groups]
    gapP = 3.6
    totP = sum(wP) + gapP * 2
    x = gfloor(AX + NC * SP / 2 - totP / 2)
    ygp, ygn = 39.2, 32.0
    segs = []
    for (bulk, g), wd in zip(pmos_groups, wP):
        segs.append(dict(x0=x, devs=[by[n] for n in g], bulk=bulk, gap=0.6))
        x = gceil(x + wd + gapP)
    topP, endsP = blk.mrow(segs, ygp, 'p')
    # NMOS drivers below their PMOS (same order; lsb resets have no NMOS)
    xs_n = []
    segsn = [dict(x0=segs[0]['x0'], devs=[], bulk='gnd', gap=0.6)]
    for n in nmos_list:
        segsn[0]['devs'].append(by[n])
    topN, endsN = blk.mrow(segsn, ygn, 'n')
    log('slice drivers: P row x %.1f-%.1f top %.2f, N row top %.2f' % (endsP[0][0], endsP[-1][1], topP, topN))
    # collectors: one per bottom net, at a grid x near the driver drain pin, >= 0.6 um from slot centres
    centres = [AX + (c + 0.5) * SP for c in range(NC)]
    used = set()
    coll_x = {}
    def okx(x):
        return all(abs(x - q) >= 0.6 for q in centres) and all(abs(x - u) >= 0.8 - 1e-6 for u in used)
    order = [('bn%d' % k, 'xdn%d_xmp' % k) for k in range(8)] + [('lsb_n', 'xlrn')] + \
            [('bn%d' % k, 'xdn%d_xmp' % k) for k in range(8, 13)] + [('bp%d' % k, 'xdp%d_xmp' % k) for k in range(12, 7, -1)] + \
            [('lsb_p', 'xlrp')] + [('bp%d' % k, 'xdp%d_xmp' % k) for k in range(7, -1, -1)]
    for net, dn in order:
        x0 = blk.devinfo[dn]['d'][1]
        for dx in [0, 0.8, -0.8, 1.6, -1.6, 2.4, -2.4, 3.2, -3.2, 4.0, -4.0]:
            x = round(x0 + dx, 4)
            if okx(x):
                break
        else:
            raise RuntimeError('no collector x for ' + net)
        used.add(x)
        coll_x[net] = x
    slots, tracks, isl = draw_cdac(blk, coll_x)
    # ---- end regions: bootstrapped switches (FEOL between the two Cboots), Cboots, trk inverters ------------------
    def boot_rows(pre, x0, flip):
        sw = lambda n: by['%s_%s' % (pre, n)]
        rows = [('n', [sw('xms'), sw('xm9')], 'gnd'), ('n', [sw('xm1'), sw('xm5'), sw('xm7')], 'gnd'),
                ('n', [sw('xm10'), sw('xm11')], 'gnd'), ('p', [sw('xm3'), sw('xm8')], pre + '_cbp'), ('p', [sw('xm4')], 'vdd')]
        return rows
    def place_boot(xL, side):
        # side 'W' (in0) or 'E' (in1): N switch rows from y 47.2, P switch rows above them (FEOL under the Cboots)
        t = '0' if side == 'W' else '1'
        out = []
        y = 47.2
        for half, pre in (('n', 'xs%sn' % t), ('p', 'xs%sp' % t)):
            sw = lambda n, pre=pre: by['%s_%s' % (pre, n)]
            y0 = y
            tp, _ = blk.mrow([dict(x0=xL, devs=[sw('xms'), sw('xm9')], bulk='gnd', gap=0.4)], y, 'n')
            tp2, _ = blk.mrow([dict(x0=xL, devs=[sw('xm1'), sw('xm5'), sw('xm7')], bulk='gnd', gap=0.4)], gceil(tp + 2.0), 'n')
            tp3, _ = blk.mrow([dict(x0=xL, devs=[sw('xm10'), sw('xm11')], bulk='gnd', gap=0.4)], gceil(tp2 + 2.0), 'n')
            yp = gceil(tp3 + 3.2)
            tp4, e4 = blk.mrow([dict(x0=xL, devs=[sw('xm3'), sw('xm8')], bulk=pre + '_cbp', gap=0.4)], yp, 'p')
            tp5, _ = blk.mrow([dict(x0=gceil(e4[0][1] + 2.4), devs=[sw('xm4')], bulk='vdd', gap=0.4)], yp, 'p')
            out.append((half, y0, max(tp4, tp5)))
            y = gceil(max(tp4, tp5) + 3.2)
        return out
    bw = place_boot(0.0, 'W')
    be = place_boot(AX + NC * SP + 2.4 - 1.6, 'E')
    log('boot rows', bw, be)
    # Cboots: N below the axis (y 52.4..63.9), P above (91.9..103.4); islands just inside the gap to the switches
    for side, xm in (('0', 0.6), ('1', round(AX + NC * SP + 1.0, 3))):     # east: Metal5 0.6 um from the ring (M5.f)
        dN = by['xs%sn_cboot' % side]; dP = by['xs%sp_cboot' % side]
        xi = gnear(xm + 5.8)
        cboot(blk, dN, xm, 52.4, xi, 65.6, gnear(xm + 3.0), 58.4)
        cboot(blk, dP, xm, 91.92, xi, 90.4, gnear(xm + 3.0), 97.6)
    # trk inverters and rstb logic: lower region, west part
    trk = [[by[n] for n in ('xnt0a', 'xnt0b', 'xnt1a', 'xnt1b', 'xnr1', 'xnr2', 'xnr3')],
           [by[n] for n in ('xpt0a', 'xpt0b', 'xpt1a', 'xpt1b', 'xpr1', 'xpr2', 'xpr3')]]
    t1, et1 = blk.mrow([dict(x0=1.6, devs=trk[0], bulk='gnd', gap=0.6)], 4.0, 'n')
    t2, et2 = blk.mrow([dict(x0=1.6, devs=trk[1], bulk='vdd', gap=0.6)], gceil(t1 + 3.2), 'p')
    log('trk rows x end %.1f %.1f top %.2f' % (et1[0][1], et2[0][1], t2))
    # ---- comparators: lower region, east part --------------------------------------------------------------------
    c4 = lambda n: by['xc4_' + n]
    c5 = lambda n: by['xc5_' + n]
    A_n = [c5('xci1'), c5('xs1_xm1'), c5('xs1_xm2'), c5('xci2'), c5('xs1_xmt1'), c5('xs1_xmtc'), c5('xmh1'), c5('xmh2'),
           c4('xmr1'), c4('xmr2')]
    A_p = [c4('xs1_xm1'), c4('xs1_xm2'), c5('xmr1'), c5('xmr2'), c5('xmt2')]
    # cmp4 integration caps (pmos W 80 L 4, 8 fingers of 10 um): FEOL under the CDAC array (Metal1/Metal2 only there)
    C_p = [c4('xci1'), c4('xci2')]
    # xc4_xs1_xmtc (W 16 L 0.5) in 4 fingers of 4 um: keeps the B_p row NWell 0.24 um clear of the driver N-row tap
    B_p = [c5('xmp1'), c5('xmp2'), c5('xbp1'), c5('xbp2'), c4('xs1_xmt1'), dict(c4('xs1_xmtc'), ng=4), c4('xmh1'), c4('xmh2'),
           c4('xmp1'), c4('xmp2'), c4('xbp1'), c4('xbp2')]
    B_n = [c5('xmn1'), c5('xmn2'), c5('xbn1'), c5('xbn2'), c4('xmt2'), c4('xmn1'), c4('xmn2'), c4('xbn1'), c4('xbn2')]
    wAn, wAp = blk.seg_w(A_n, 0.4), blk.seg_w(A_p, 0.4)
    wBn, wBp = blk.seg_w(B_n, 0.4), blk.seg_w(B_p, 0.4)
    log('comparator widths: A_n %.1f A_p %.1f B_n %.1f B_p %.1f' % (wAn, wAp, wBn, wBp))
    xAp = gfloor(WS - 1.2 - wAp)
    xAn = gfloor(xAp - 3.2 - wAn)
    tAp, eAp = blk.mrow([dict(x0=xAp, devs=A_p, bulk='vdd', gap=0.4)], 4.0, 'p')
    tAn, eAn = blk.mrow([dict(x0=xAn, devs=A_n, bulk='gnd', gap=0.4)], 4.0, 'n')
    wCp = blk.seg_w(C_p, 0.4)
    ygc = gceil(max(tAp, tAn) + 3.2)
    ycap = 47.2
    tCp, eCp = blk.mrow([dict(x0=gfloor(AX + NC * SP / 2 - wCp / 2), devs=C_p, bulk='vdd', gap=0.4)], ycap, 'p')
    log('cmp4 cap row (under the array): yg %.2f x %.1f-%.1f top %.2f' % (ycap, eCp[0][0], eCp[0][1], tCp))
    # small comparator devices: NMOS west of the driver N row, PMOS east of the driver P row
    tBn, eBn = blk.mrow([dict(x0=2.0, devs=B_n, bulk='gnd', gap=0.4)], ygn, 'n')
    # B_p: lower region west, on the cap-row rail (east of the trk rows, west of the cap row). The driver P row
    # east end would put its NWell over the east boot NMOS rows.
    tBp, eBp = blk.mrow([dict(x0=gceil(max(et1[0][1], et2[0][1]) + 2.4), devs=B_p, bulk='vdd', gap=0.4)], ygc, 'p')
    log('cmp rows: A x %.1f-%.1f top %.2f; B_n x %.1f-%.1f; B_p x %.1f-%.1f; trk top %.2f; drivers x %.1f-%.1f'
        % (xAn, eAp[0][1], max(tAp, tAn), eBn[0][0], eBn[0][1], eBp[0][0], eBp[0][1], t2, endsP[0][0], endsP[-1][1]))
    if eBn[0][1] > endsN[0][0] - 2.0 or eBp[0][1] > xAn - 2.0 or xAn < et1[0][1] + 2.0:
        log('WARNING lower-region overlap')
    # ---- edge pins ---------------------------------------------------------------------------------------------------
    R.block_edges()
    edge = {}
    for net, x in SLICE_SOUTH:
        R.unblock(1, x, 0.0)
        blk.pin(net, [(1, x, 0.0)], 'm3')
        edge.setdefault(net, []).append(('S', x, 0.0))
    for net, y in SLICE_WEST:
        R.unblock(1, 0.0, y)
        blk.pin(net, [(1, 0.0, y)], 'm3')
        edge.setdefault(net, []).append(('W', 0.0, y))
    for net, y in SLICE_EAST:
        R.unblock(1, WS, y)
        blk.pin(net, [(1, WS, y)], 'm3')
        edge.setdefault(net, []).append(('E', WS, y))
    # ---- route -------------------------------------------------------------------------------------------------------
    # comparator clocks first, with a soft halo (other nets keep the next track free for the ground shield)
    CLK = ['clkb', 'clkn', 'clk', 'clknb']
    R.halo_cost, R.halo_only = 40, set(CLK)
    first = CLK + [n for pr in SLICE_PAIRS for n in pr]
    ok = route_pairs(blk, first, SLICE_PAIRS, 'r1_adc_slice')
    blk.stats['route_ok'] = ok
    blk.stats['route_failed'] = R.failed
    blk.draw_routes()
    blk.D.boundary(0, 0, WS, HS)
    blk.stats['cdac'] = dict(slots=len(slots), units=sum(1 for s in slots.values() if s['kind'] == 'u'),
                             dummies=sum(1 for s in slots.values() if s['kind'] == 'dummy'), islands=isl,
                             collectors=coll_x)
    blk.edge = edge
    blk.slots = slots
    return blk


def route_pairs(blk, first, pairs, cellname):
    R = blk.R
    ok = R.route_all(rounds=ROUNDS, log=log, first=first, lock=True)
    if not ok:
        log('%s: locked priority routing failed %s; re-routing without the lock' % (cellname, R.failed))
        for k in list(R.paths):
            R.unroute(k)
        R.lock = set()
        ok = R.route_all(rounds=ROUNDS, log=log, first=first, lock=False)
    before, after = {}, {}
    for a, b in pairs:
        if a not in R.nets or b not in R.nets:
            continue
        ka, kb = R.nets[a], R.nets[b]
        sa, sb = R.net_stats(ka), R.net_stats(kb)
        before[a], before[b] = sa, sb
        if ok:
            for l in range(3):
                d = sa['edges'][l] - sb['edges'][l]
                ls = 1 if l == 0 else l
                if d > 0:
                    R.add_stub(kb, ls, d, log=log)
                elif d < 0:
                    R.add_stub(ka, ls, -d, log=log)
    if ok:
        for key, ed in TRIM.items():
            c, net = key.split(':')
            if c == cellname and net in R.nets:
                for l, n in enumerate(ed):
                    if n > 0 and l > 0:
                        R.add_stub(R.nets[net], l, int(n), log=log)
        # comparator clocks (slice) and the clock input (top): ground shield tracks on both sides where free
        gname = 'gnd' if cellname == 'r1_adc_slice' else 'vss'
        for net in (('clk', 'clkb', 'clkn', 'clknb') if cellname == 'r1_adc_slice' else ('clk',)):
            if net in R.nets and gname in R.nets:
                kept, tot = R.shield(R.nets[net], R.nets[gname])
                blk.stats.setdefault('shield', {})[net] = dict(shielded_edges=kept, edge_sides=tot)
                log('%s: shield %s %d of %d edge-sides (%d free candidates)' % (cellname, net, kept, tot, R.shield_cand))
        for net in ('gnd', 'vss', 'vdd', 'vdda', 'vref', 'vrefl'):
            if net in R.nets:
                nb, nv = R.widen(R.nets[net])
                blk.stats.setdefault('widen', {})[net] = dict(boxes=nb, extra_vias=nv)
    for a, b in pairs:
        if a in R.nets and b in R.nets:
            after[a], after[b] = R.net_stats(R.nets[a]), R.net_stats(R.nets[b])
    blk.stats['pairs_before'] = before
    blk.stats['pairs_after'] = after
    return ok


# =====================================================================================================================
# top
# =====================================================================================================================
DEC_H = 95.0
DEC_Y = 3.4
DEC_GAP = 3.2
VREF_Y = (49.2, 50.8)
VREFL_Y = (45.2, 46.8)


def decap_plan():
    """plate widths on the 0.01 um grid (the drawn area is within 0.5 um2 of the netlist of record). The filter plates
    (xfilt_xcf, on vref_in) are 90 um tall from y DEC_Y + 5 so that the TopMetal1 jumper of their Metal5 plate fits
    below them (antenna, see build_top)."""
    hf = DEC_H - 5.0
    w = {'cd': round(4900.0 / DEC_H, 2), 'cg': round(2500.0 / DEC_H, 2), 'cf': round(6724.0 / hf / 2, 2)}
    h = {'cd': DEC_H, 'cg': DEC_H, 'cf': hf}
    y = {'cd': DEC_Y, 'cg': DEC_Y, 'cf': DEC_Y + 5.0}
    order = [('xfilt_xcf', 0, 'cf'), ('xref_xcd', 0, 'cd'), ('xref_xcd', 1, 'cd'), ('xref_xcdl', 0, 'cd'),
             ('xref_xcg', 0, 'cg'), ('xref_xcdl', 1, 'cd'), ('xref_xcd', 2, 'cd'), ('xref_xcd', 3, 'cd'), ('xfilt_xcf', 1, 'cf')]
    tot = sum(w[k] for _, _, k in order) + DEC_GAP * (len(order) - 1)
    x = round((W - tot) / 2, 2)
    plan = []
    for name, u, k in order:
        plan.append(dict(name=name, u=u, x=x, y=y[k], w=w[k], h=h[k], kind=k))
        x = round(x + w[k] + DEC_GAP, 2)
    shapes = {}
    for p in plan:
        shapes.setdefault(p['name'], []).append([p['w'], p['h']])
    return plan, shapes


NORTH, WEST, EAST, SOUTH = NLM.NORTH, NLM.WEST, NLM.EAST, NLM.SOUTH


def build_top(ly, sl):
    plan, shapes = decap_plan()
    top_devs = NLM.top_devices()
    by = {d['name']: d for d in top_devs}
    blk = Blk(ly, 'r1_adc', W, H)
    R = blk.R
    D = blk.D
    for x0 in SX:
        D.inst(sl.cell, x0, SY)
    # ---- slices: obstacles except their edge pins ---------------------------------------------------------------
    smap = {0: NLM.slice_map('a'), 1: NLM.slice_map('b')}
    for q, x0 in enumerate(SX):
        R.block_area([0, 1, 2], x0, SY, x0 + WS, SY + HS)
        for port, lst in sl.edge.items():
            net = smap[q][port] if port in smap[q] else port
            for (side, x, y) in lst:
                X, Y = round(x0 + x, 4), round(SY + y, 4)
                R.unblock(1, X, Y)
                if side == 'S':
                    blk.pin(net, [(1, X, Y)], 'm3')
    # ---- guard ring (p+ substrate tie, vss) -----------------------------------------------------------------------
    D.tap_ring(1.0, 1.0, W - 1.0, H - 1.0, w=0.6, ptype=True)
    # ---- decoupling plates ------------------------------------------------------------------------------------------
    # TopMetal1 top plates: all on vss, one sheet (bridges across the gaps), tied to the vss Metal4 strap through
    # TopVia1 islands in the gaps. Metal5 bottom plates: the signal; Via4 straight down to the Metal4 reference buses
    # (vref, vrefl), to a Metal4 pin (xref_ng), or (vref_in, filter) through a TopMetal1 jumper only, so that no
    # gate sees the filter plate before TopMetal1 (Ant.b; vref_in has no diffusion inside the block).
    for i, p in enumerate(plan):
        d = [t for t in top_devs if t['orig'] == p['name']][p['u']]
        D.pcell('cmim', {'Calculate': 'C', 'w': '%gu' % p['w'], 'l': '%gu' % p['h']}, p['x'], p['y'])
        assert d['nets'][0] == 'vss', d
        p['net'] = d['nets'][1]
    gapc = [round(plan[i]['x'] + plan[i]['w'] + DEC_GAP / 2, 3) for i in range(len(plan) - 1)]
    ys = 3.2                                    # vss Metal4 strap
    yi = 9.6                                    # vss islands in the gaps
    for i in range(len(plan) - 1):
        pa, pb = plan[i], plan[i + 1]
        xa, xb = pa['x'] + pa['w'] - 2.0, pb['x'] + 2.0
        for yb in (yi, 30.0, 70.0, 90.0):
            D.box('TM1', xa, yb - 1.0, xb, yb + 1.0)
        xg = gapc[i]
        D.sq('TV1', xg, yi, TV1); D.sq('M5', xg, yi, TV1 + 2 * TV1_M5); D.sq('Via4', xg, yi, VIA)
        D.box('M4', xg - 0.2, ys - 0.4, xg + 0.2, yi + 0.2)
        R.reserve(2, xg - 0.2, ys - 0.4, xg + 0.2, yi + 0.2, 'vss')
    D.box('M4', 4.0, ys - 0.4, W - 4.0, ys + 0.4)
    R.reserve(2, 4.0, ys - 0.4, W - 4.0, ys + 0.4, 'vss')
    for x in gpts(6.0, W - 6.0)[::12]:
        D.box('M1', x - 0.2, 0.7, x + 0.2, ys + 0.2)
        for v, lo, hi in (('Via1', 'M1', 'M2'), ('Via2', 'M2', 'M3'), ('Via3', 'M3', 'M4')):
            D.sq(v, x, ys, VIA); D.sq(lo, x, ys, 0.40); D.sq(hi, x, ys, 0.40)
        R.reserve(0, x - 0.2, ys - 0.2, x + 0.2, ys + 0.2, 'vss'); R.reserve(1, x - 0.2, ys - 0.2, x + 0.2, ys + 0.2, 'vss')
    blk.pin('vss', [(2, x, ys) for x in gpts(6.0, W - 6.0)][::4], 'm4')
    # bottom plates
    bus = {'vref': VREF_Y, 'vrefl': VREFL_Y}
    for p in plan:
        if p['net'] in bus:
            ya, yb = bus[p['net']]
            for x in gpts(p['x'] + 1.0, p['x'] + p['w'] - 1.0)[::2]:
                for y in (ya + 0.4, yb - 0.4):
                    D.sq('Via4', x, y, VIA)
        elif p['net'] == 'xref_ng':
            xn = gnear(p['x'] + p['w'] / 2)
            for x in (xn - 0.8, xn, xn + 0.8):
                D.sq('Via4', x, 40.0, VIA)
            D.box('M4', xn - 1.0, 39.8, xn + 1.0, 40.2)
            R.reserve(2, xn - 1.0, 39.8, xn + 1.0, 40.2, 'xref_ng')
            blk.pin('xref_ng', [(2, xn, 40.0)], 'm4')
        else:      # vref_in: TopVia1 on a Metal5 extension below the plate, TopMetal1 jumper, TopVia1 on a Metal5 island
            yj = 5.6
            xa_ = gnear(p['x'] + p['w'] / 2 - 2.0); xb_ = xa_ + 4.0
            D.box('M5', xa_ - 0.33, yj - 0.33, xa_ + 0.33, p['y'] - 0.3)
            D.sq('TV1', xa_, yj, TV1)
            D.box('TM1', xa_ - 0.82, yj - 0.82, xb_ + 0.82, yj + 0.82)
            D.sq('TV1', xb_, yj, TV1); D.sq('M5', xb_, yj, TV1 + 2 * TV1_M5); D.sq('Via4', xb_, yj, VIA)
            D.sq('M4', xb_, yj, 0.40)
            R.reserve(2, xb_ - 0.2, yj - 0.2, xb_ + 0.2, yj + 0.2, 'vref_in')
            blk.pin('vref_in', [(2, xb_, yj)], 'm4')
    # ---- reference buses (Metal3 + Metal4, full width) ------------------------------------------------------------
    for net, (ya, yb) in (('vref', VREF_Y), ('vrefl', VREFL_Y)):
        for lay, li in (('M3', 1), ('M4', 2)):
            D.box(lay, 4.0, ya, W - 4.0, yb)
            R.reserve(li, 4.0, ya, W - 4.0, yb, net)
        for x in gpts(5.0, W - 5.0)[::3]:
            for y in (ya + 0.4, yb - 0.4):
                D.sq('Via3', x, y, VIA)
        nodes = [(l, x, y) for l in (1, 2) for x in gpts(4.4, W - 4.4) for y in gpts(ya + 0.3, yb - 0.3)]
        blk.pin(net, nodes, 'm4')
        blk.label('M4txt', 6.0, (ya + yb) / 2, net)
    # ---- reference buffer (thick oxide), biases ---------------------------------------------------------------------
    rb = lambda n: by['xref_' + n]
    xmib = [rb('xmib_s%d' % k) for k in range(4)]
    xmsf = [rb('xmsf_s%d' % k) for k in range(4)]
    w1 = blk.seg_w(xmib[:2], 0.8)
    xc = W / 2
    r1 = [dict(x0=gfloor(xc - w1 - 1.6), devs=xmib[:2], bulk='vss', gap=0.8),
          dict(x0=gceil(xc + 1.6), devs=xmib[2:], bulk='vss', gap=0.8)]
    t1, _ = blk.mrow(r1, 7.2, 'nHV')
    r2l = [rb('xmibl_s0'), rb('xmb0'), rb('xmt')]
    r2r = [rb('xm1'), rb('xm2'), rb('xmsfl_s0')]
    w2l = blk.seg_w(r2l, 0.8)
    r2 = [dict(x0=gfloor(xc - w2l - 1.6), devs=r2l, bulk='vss', gap=0.8), dict(x0=gceil(xc + 1.6), devs=r2r, bulk='vss', gap=0.8)]
    t2, _ = blk.mrow(r2, gceil(t1 + 3.2), 'nHV')
    w3 = blk.seg_w(xmsf[:2], 0.8)
    r3 = [dict(x0=gfloor(xc - w3 - 1.6), devs=xmsf[:2], bulk='vss', gap=0.8), dict(x0=gceil(xc + 1.6), devs=xmsf[2:], bulk='vss', gap=0.8)]
    t3, _ = blk.mrow(r3, gceil(t2 + 3.2), 'nHV')
    w4 = blk.seg_w([rb('xm3'), rb('xm4')], 0.8)
    r4 = [dict(x0=gfloor(xc - w4 / 2), devs=[rb('xm3'), rb('xm4')], bulk='vdda', gap=0.8)]
    t4, _ = blk.mrow(r4, gceil(t3 + 4.0), 'pHV')
    log('refbuf rows top %.2f %.2f %.2f %.2f' % (t1, t2, t3, t4))
    # TGO.e: ThickGateOx boxes closer than 0.86 um are merged (fill the gap over the common x range)
    for a in blk.tgo:
        for b in blk.tgo:
            gap = b[1] - a[3]
            xl, xr = max(a[0], b[0]), min(a[2], b[2])
            if 0 < gap < 0.86 and xr > xl:
                blk.box('TGO', xl, a[3] - 0.01, xr, b[1] + 0.01)
    # comparator biases: rppd segments (west), diodes
    res = sorted([d for d in top_devs if d['kind'] == 'rppd'], key=lambda d: (d['orig'], d['seg']))
    groups = [dict(slots=[40.0], cols=[[d] for d in res if d['orig'] == 'xcbias_xrb']),
              dict(slots=[40.0], cols=[[d] for d in res if d['orig'] == 'xcbiasn_xrb'])]
    xe, ytop = resistor_array(blk, groups, 8.0, 6.4)
    tb1, _ = blk.mrow([dict(x0=gceil(xe + 2.4), devs=[by['xcbiasn_xmbd']], bulk='vss', gap=0.6)], 8.0, 'n')
    tb2, _ = blk.mrow([dict(x0=gceil(xe + 2.4), devs=[by['xcbias_xmbd']], bulk='vdd', gap=0.6)], gceil(tb1 + 3.2), 'p')
    # ---- clock generator (north-west) -----------------------------------------------------------------------------
    ck = lambda n: by['xckg_' + n]
    cn = [ck('xnd0'), ck('xnd1'), ck('xnd2'), ck('xnd3'), ck('xnd4'), ck('xna'), ck('xnb'), ck('xni')]
    cp_ = [ck('xpd0'), ck('xpd1'), ck('xpd2'), ck('xpd3'), ck('xpd4'), ck('xpa'), ck('xpb'), ck('xpi')]
    tk1, _ = blk.mrow([dict(x0=8.0, devs=cn, bulk='vss', gap=0.4)], 175.2, 'n')
    wk = blk.seg_w(cn, 0.4)
    tk2, ek2 = blk.mrow([dict(x0=gceil(8.0 + wk + 2.4), devs=cp_, bulk='vdd', gap=0.4)], 175.2, 'p')
    for k in range(5):
        d = ck('cd%d' % k)
        mx = gceil(ek2[0][1] + 2.0) + k * 7.2     # 7.2 pitch: TopMetal1 tab islands 1.64 um clear of the next plate
        blk.mim_rect(d['name'], d['w'], d['l'], mx, 175.2, d['nets'][0], d['nets'][1], tab='E')
    log('clkgen top %.2f %.2f, x end %.2f' % (tk1, tk2, ek2[0][1] + 34))
    # ---- long input pairs (hand-drawn), north channel shields -------------------------------------------------------
    long_pairs(blk)
    # ---- block pins -------------------------------------------------------------------------------------------------
    R.block_edges()
    bp = []
    for net, x in NORTH:
        bp.append((net, 'N', x, H))
    for net, y in WEST:
        bp.append((net, 'W', 0.0, y))
    for net, y in EAST:
        bp.append((net, 'E', W, y))
    for net, x in SOUTH:
        bp.append((net, 'S', x, 0.0))
    for (net, side, x, y) in bp:
        if side == 'S':
            xg = gnear(x)
            R.unblock(1, xg, 0.8); blk.pin(net, [(1, xg, 0.8)], 'm3')
        elif net == 'clk':
            R.unblock(1, gnear(x), gfloor(H - 0.8)); blk.pin(net, [(1, gnear(x), gfloor(H - 0.8))], 'm3')
        elif net in ('ain_sin_p', 'ain_sin_n', 'ain_isb_p', 'ain_isb_n'):
            pass       # straight Metal3 stubs to the slice edge pins (drawn below)
        elif net == 'ibias':
            pass
    # reserve the edge pin boxes and the straight input stubs (drawn after routing) for their nets
    for (net, side, x, y) in bp:
        if side == 'N':
            R.reserve(1, x - 0.2, H - 1.2, x + 0.2, H, net)
        elif side == 'W':
            R.reserve(1, 0.0, y - 0.2, 1.0, y + 0.2, net)
        elif side == 'E':
            R.reserve(1, W - 1.0, y - 0.2, W, y + 0.2, net)
        elif side == 'S':
            R.reserve(1, min(x, gnear(x)) - 0.2, 0.0, max(x, gnear(x)) + 0.2, 1.0, net)
    for net, y in (('ain_sin_p', 110.0), ('ain_sin_n', 114.0)):
        R.reserve(1, 0.0, y - 0.2, SX[0] + 0.2, y + 0.6, net)
    for net, y in (('ain_isb_p', 130.0), ('ain_isb_n', 134.0)):
        R.reserve(1, SX[1] + WS - 0.2, y - 0.2, W, y + 0.6, net)
    # guard ring as vss at a few nodes next to the south vss pin
    blk.pin('vss', [(0, x, 0.8) for x in gpts(146.0, 154.0)], 'm1')
    # ---- route ------------------------------------------------------------------------------------------------------
    TOP_PAIRS = []
    R.halo_cost, R.halo_only = 40, {'clk'}
    ok = route_pairs(blk, ['clk', 'vref', 'vrefl'], TOP_PAIRS, 'r1_adc')
    blk.stats.update(route_ok=ok, route_failed=R.failed)
    blk.draw_routes()
    # pins: Metal3 boxes, pin shapes, labels
    for (net, side, x, y) in bp:
        L = 'M3'
        if side == 'S':
            xg = gnear(x)       # pin at the checklist x, jog at y 0.6-1.0 to the router node (xg, 0.8)
            D.box(L, x - 0.2, 0.0, x + 0.2, 1.0); D.box('M3pin', x - 0.2, 0.0, x + 0.2, 1.0)
            D.label('M3txt', x, 0.5, net, 0.3)
            if abs(xg - x) > 1e-6:
                D.box(L, min(x, xg) - 0.2, 0.6, max(x, xg) + 0.2, 1.0)
        elif side == 'N':
            yb = H - 1.2
            D.box(L, x - 0.2, yb, x + 0.2, H); D.box('M3pin', x - 0.2, yb, x + 0.2, H)
            D.label('M3txt', x, H - 0.4, net, 0.3)
            if net == 'clk':
                xg = gnear(x)
                D.box(L, min(x, xg) - 0.2, gfloor(H - 0.8) - 0.2, max(x, xg) + 0.2, H - 0.4)
        elif side == 'W':
            D.box(L, 0.0, y - 0.2, 1.0, y + 0.2); D.box('M3pin', 0.0, y - 0.2, 1.0, y + 0.2)
            D.label('M3txt', 0.4, y, net, 0.3)
        else:
            D.box(L, W - 1.0, y - 0.2, W, y + 0.2); D.box('M3pin', W - 1.0, y - 0.2, W, y + 0.2)
            D.label('M3txt', W - 0.4, y, net, 0.3)
    # straight input stubs (SIN -> slice A in0, ISB -> slice B in1)
    for net, y in (('ain_sin_p', 110.0), ('ain_sin_n', 114.0)):
        D.box('M3', 0.0, y - 0.2, SX[0] + 0.2, y + 0.6)
    for net, y in (('ain_isb_p', 130.0), ('ain_isb_n', 134.0)):
        D.box('M3', SX[1] + WS - 0.2, y - 0.2, W, y + 0.6)
    # top-level labels for slice-internal ports (sar_* nets, top plates) over the child metal
    for q, x0 in enumerate(SX):
        for (lay, x, y, text) in sl.portlabels:
            net = smap[q][text]
            D.box('M2' if lay == 'M2txt' else 'M4', x0 + x - 0.1, SY + y - 0.1, x0 + x + 0.1, SY + y + 0.1)
            D.label(lay, x0 + x, SY + y, net, 0.1)
    for (lay, x, y, text) in blk.labels:
        D.label(lay, x, y, text, 0.2)
    D.boundary(0, 0, W, H)
    blk.stats['decap_plan'] = plan
    blk.stats['pins'] = bp
    return blk, shapes


def long_pairs(blk):
    """COS (west pins -> slice B in0) and ISA (east pins -> slice A in1): hand-drawn Metal4 verticals at the block
    edges, Metal2 horizontals in the north channel, Metal3 verticals in the middle gap; vss shields (Metal2) in the
    channel, Metal3 in the gap. All reserved for their nets in the top router."""
    D, R = blk.D, blk.R
    w = 0.3
    def seg(lay, x1, y1, x2, y2, net):
        li = {'M2': 0, 'M3': 1, 'M4': 2}[lay]
        xa, xb = max(0.0, min(x1, x2) - w / 2), min(W, max(x1, x2) + w / 2)     # never past the block edge
        D.box(lay, xa, min(y1, y2) - w / 2, xb, max(y1, y2) + w / 2)
        R.reserve(li, xa, min(y1, y2) - w / 2, xb, max(y1, y2) + w / 2, net)
    def via(x, y, lo, hi, net):
        names = {(0, 1): 'Via2', (1, 2): 'Via3'}
        L = ['M2', 'M3', 'M4']
        for a in range(lo, hi):
            D.sq(names[(a, a + 1)], x, y, VIA)
            D.sq(L[a], x, y, 0.40); D.sq(L[a + 1], x, y, 0.40)
            R.reserve(a, x - 0.2, y - 0.2, x + 0.2, y + 0.2, net); R.reserve(a + 1, x - 0.2, y - 0.2, x + 0.2, y + 0.2, net)
    xS0, xS1 = SX[0] + WS, SX[1]          # 216.8, 223.2
    # COS: p (0,130) -> x 1.6 up to 167.2 -> east to 220.8 -> down to 110 -> east to 223.2
    for net, yp, xv, yh, xg, yend in (('ain_cos_p', 130.0, 1.6, 167.2, 220.8, 110.4), ('ain_cos_n', 134.0, 0.8, 168.0, 221.6, 114.4)):
        seg('M3', 0.0, yp, xv, yp, net); via(xv, yp, 1, 2, net)
        D.box('M3', 0.0, yp - 0.2, xv + 0.2, yp + 0.2)
        seg('M4', xv, yp, xv, yh, net); via(xv, yh, 0, 2, net)
        seg('M2', xv, yh, xg, yh, net); via(xg, yh, 0, 1, net)
        seg('M3', xg, yh, xg, yend, net)
        seg('M3', xg, yend, xS1 + 0.2, yend, net)
    # ISA: p (439,110) -> x 437.6 up to 169.6 -> west to 218.4 -> down to 130.4 -> west to 216.8 (slice A in1)
    for net, yp, xv, yh, xg, yend in (('ain_isa_p', 110.0, 437.6, 169.6, 218.4, 130.4), ('ain_isa_n', 114.0, 438.4, 170.4, 217.6, 134.4)):
        seg('M3', W, yp, xv, yp, net); via(xv, yp, 1, 2, net)
        D.box('M3', xv - 0.2, yp - 0.2, W, yp + 0.2)          # 0.40 wide like the pin box (no notch)
        seg('M4', xv, yp, xv, yh, net); via(xv, yh, 0, 2, net)
        seg('M2', xv, yh, xg, yh, net); via(xg, yh, 0, 1, net)
        seg('M3', xg, yh, xg, yend, net)
        seg('M3', xg, yend, xS0, yend, net)
    # ibias: west pin (0, 165) -> x 2.4 down to y 42.4 (router pin there)
    seg('M3', 0.0, 165.0, 2.4, 165.0, 'ibias'); via(2.4, 165.0, 1, 2, 'ibias')
    seg('M4', 2.4, 165.0, 2.4, 42.4, 'ibias')
    blk.pin('ibias', [(2, 2.4, 42.4)], 'm4')
    # shields: Metal2 in the channel (vss), Metal3 in the gap
    for y, xa, xb in ((166.4, 2.4, 436.8), (168.8, 2.4, 436.8), (171.2, 2.4, 436.8)):
        seg('M2', xa, y, xb, y, 'vss')
    for x in (219.2, 220.0):
        seg('M3', x, 166.4, x, 117.6, 'vss'); via(x, 166.4, 0, 1, 'vss')
    blk.pin('vss', [(0, 3.2, 166.4), (0, 436.0, 168.8), (0, 3.2, 171.2)], 'm2')
    blk.label('M2txt', 30.0, 167.2, 'ain_cos_p'); blk.label('M2txt', 30.0, 168.0, 'ain_cos_n')
    blk.label('M2txt', 400.0, 169.6, 'ain_isa_p'); blk.label('M2txt', 400.0, 170.4, 'ain_isa_n')
    blk.label('M4txt', 2.4, 100.0, 'ibias')
    for y in (166.4, 168.8, 171.2):
        blk.label('M2txt', 100.0, y, 'vss')


# =====================================================================================================================
# rppd array (copied from r1_afe/layout/r1_afe_layout.py revision E2, vertical straight columns)
# =====================================================================================================================
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


def resistor_array(blk, groups, x_start, y_b, dummies=2):
    tmpl = rppd_template()
    x = gceil(x_start + 0.5) - 0.5
    ytop_all = y_b
    colpos = []
    for gi, g in enumerate(groups):
        offs = [y_b]
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
                    blk.box('GatPoly', xc, ys + 0.25, xc + 1.0, ys + L - 0.25)
                    continue
                for (lay, x1, y1, x2, y2) in tmpl:
                    if y2 <= 5.0 + 1e-6:
                        pass
                    elif y1 >= 5.0 - 1e-6:
                        y1 += L - 10.0; y2 += L - 10.0
                    else:
                        y2 += L - 10.0
                    blk.cell.shapes(blk.ly.layer(*lay)).insert(pya.Box(um(xc + x1), um(ys + y1), um(xc + x2), um(ys + y2)))
                colpos.append((seg, xc, ys, L))
            x = round(x + 1.6, 4)
        xe = x - 1.6 + 1.0
        for k, L in enumerate(g['slots']):
            ys = offs[k]
            blk.box('SalBlock', xs0 - 0.2, ys, xe + 0.2, ys + L)
            blk.box('pSD', xs0 - 0.18, ys - 0.61, xe + 0.18, ys + L + 0.61)
            blk.box('EXTBlock', xs0 - 0.2, ys - 0.61, xe + 0.2, ys + L + 0.61)
            blk.R.block_area([0], xs0 - 0.4, ys + 0.3, xe + 0.4, ys + L - 0.3)
            ytop_all = max(ytop_all, ys + L)
    bydev = {}
    for (seg, xc, ys, L) in colpos:
        bydev.setdefault(seg['orig'], []).append((seg, xc, ys, L))
    for orig, segs in bydev.items():
        segs.sort(key=lambda t: t[0].get('seg', 0))
        n = len(segs)
        for q, (seg, xc, ys, L) in enumerate(segs):
            na, nb = seg['nets'][0], seg['nets'][1]
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
                        blk.box('M1', min(xc, xn) + 0.02, yh[0], max(xc, xn) + 0.98, yh[1])
                    continue
                xp = round(xc + 0.5, 4)
                if where == 'bot':
                    yp = gfloor(ys - 0.75)
                    blk.box('M1', xp - 0.17, yp - 0.17, xp + 0.17, ys - 0.13)
                else:
                    yp = gceil(ys + L + 0.75)
                    blk.box('M1', xp - 0.17, ys + L + 0.13, xp + 0.17, yp + 0.17)
                blk.port(seg['name'], 0 if net == na else 1, net, 1, pt=(xp, yp))
                blk.pin(net, [(0, xp, yp)], 'm1')
    return x, ytop_all


# =====================================================================================================================
def slice_port_labels(sl):
    """positions of the slice-internal port nets (sar_* interface, top plates) for top-level labels."""
    out = []
    di = sl.devinfo
    def g(dev):
        l, x, y = di[dev]['g']; return ('M2txt', x, y)
    def dr(dev):
        l, x, y = di[dev]['d']; return ('M2txt', x, y)
    out.append(g('xpt0a') + ('trk0',)); out.append(g('xpt1a') + ('trk1',))
    for k in range(13):
        out.append(g('xdp%d_xmp' % k) + ('cp%d' % k,)); out.append(g('xdn%d_xmp' % k) + ('cn%d' % k,))
    out.append(g('xc4_xmt2') + ('clk',)); out.append(g('xc4_xs1_xmt1') + ('clkb',))
    out.append(g('xc5_xs1_xmt1') + ('clkn',)); out.append(g('xc5_xmt2') + ('clknb',))
    out.append(dr('xc4_xbp1')[:0] + g('xc4_xbp1') + ('op',)); out.append(g('xc4_xbp2') + ('on',))
    out.append(g('xc5_xbp1') + ('onp',)); out.append(g('xc5_xbp2') + ('onn',))
    for net, nm in (('top_p@E', 'top_p'), ('top_n@E', 'top_n')):
        x, y = sl.stats['cdac']['islands'][net]
        out.append(('M4txt', x, y, nm))
    return out


def main():
    t0 = time.time()
    ly = pya.Layout(); ly.dbu = 0.001
    sl = build_slice(ly)
    log('slice routed', sl.stats['route_ok'], sl.stats['route_failed'], '%.0f s' % (time.time() - t0))
    sl.portlabels = slice_port_labels(sl)
    top, shapes = build_top(ly, sl)
    log('top routed', top.stats['route_ok'], top.stats['route_failed'], '%.0f s' % (time.time() - t0))
    json.dump(shapes, open(os.path.join(HERE, 'r1_adc_decap.json'), 'w'), indent=1)
    import importlib
    importlib.reload(NLM)
    NLM.write_cdl()
    ly.write(OUT)
    rr = os.environ.get('G1_RESULTS_ROOT')
    log('wrote', (OUT.replace(rr, '<G1_RESULTS_ROOT>') if rr else OUT).replace('/work/', '<repo>/'))
    meta = dict(box=[W, H], slice=dict(origins=[[x, SY] for x in SX], size=[WS, HS], stats=sl.stats),
                top=dict(stats=top.stats), log=LOG,
                ports=dict(slice=sl.ports, top=top.ports))
    json.dump(meta, open(os.path.join(HERE, 'r1_adc_layout.json'), 'w'), indent=1, default=str)


main()
