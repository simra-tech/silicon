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
Layout B (2026-10-26, T2b): wide supply / reference straps drawn before routing and given to the router as pins (slice:
  Metal4 vdd, gnd and Kelvin driver-ground straps, Metal4 vref / vrefl straps over the driver rows with 2 um Metal3
  feeders from the south pins; top: decoupling TopMetal1 sheet used as the vss plane with Via4 / TopVia1 drops onto the
  slice gnd strap, vdd strap under the slices, vdda strap to the buffer), comparator input pairs at the east end of the
  comparator row (short top-plate routes, halo on the top-plate nets), symmetric COS input pair. See README "Layout B".
Layout B5 (2026-10-27, T2k, D21): box 439.0 x 205.42 um = this analog part (y 0 - 182.3) + the hardened SAR sub-macro
  r1_adc_sar (release t2j-ll-h2312-h) as a cell reference at (0, 182.3); the slice routes its 36 SAR ports to north
  edge pins, the top router joins them to the macro south pins; clock generator moved to x 157.6; macro supplies:
  vdd Metal4 riser + Metal5 bus, vss TopMetal1 strap + Metal5 bus; north pins = macro pins (README "Layout B5").
  -rd out=<gds> writes the GDS elsewhere; needs G1_RESULTS_ROOT (the macro GDS, hash-checked).
Layers: Metal1-Metal4 routing (maze router + hand-drawn buses), Metal5 only as MIM bottom plates and TopVia1 islands,
TopMetal1 only on MIM plates, their sheets and 1.64 um tabs; no TopMetal2. Boundary on 189/4.
"""
import json, math, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from adc_lib import *            # noqa  Block, gceil, gfloor, gnear, gpts, s5, pya, LAYERS, Mos, VIA, TV1, ...
import r1_adc_netlist as NLM
from maze_router import P, LNAME, FREE, BLOCK

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass
OUT = globals().get('out', os.path.join(HERE, 'r1_adc.gds'))
ROUNDS = int(globals().get('rounds', '6'))
TRIM = json.load(open(globals()['trim'])) if globals().get('trim') else {}

W, H = 439.0, 182.3               # H: analog part (layouts A-B4); B5 box height HB5
HB5 = round(H + 23.12, 2)
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


def via_array(D, via, x1, y1, x2, y2):
    """layout B: array of Via1..Via4 cuts (0.19 at 0.50 pitch, 0.105 enclosure) or TopVia1 cuts (0.42 at 0.84 pitch,
    0.12 Metal5 / 0.45 TopMetal1 enclosure) filling the box; the caller draws the metals."""
    if via == 'TV1':
        a, pitch, enc = TV1, 0.84, 0.45
    else:
        a, pitch, enc = VIA, VPITCH, 0.105 + 0.02
    nx = max(1, int((x2 - x1 - 2 * enc - a) / pitch + 1e-6) + 1)
    ny = max(1, int((y2 - y1 - 2 * enc - a) / pitch + 1e-6) + 1)
    x0 = (x1 + x2) / 2 - (nx - 1) * pitch / 2
    y0 = (y1 + y2) / 2 - (ny - 1) * pitch / 2
    for i in range(nx):
        for j in range(ny):
            D.sq(via, round(x0 + i * pitch, 4), round(y0 + j * pitch, 4), a)
    return nx * ny


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
        mode = self.stacks.get(d['name'])
        nodes = None
        if mode:
            # layout B4: multi-cut source stack (see src_stack); replaces the single m1 router pin of the source
            nodes, sl2 = self.src_stack(d['name'], Sn, mode, xa, yS, cand, sxD, m.sx(S[-1]) + 0.13)
        if nodes:
            sl = min(sl, sl2)
            self.box('M1', sl, yS - 0.17, sr, yS + 0.17)
            self.pin(Sn, nodes, 'm2')
        else:
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

    stacks = {}                   # layout B4: device name -> 'p' (strap above, STRAP_REF) / 'n' (strap below, STRAP_GNDK)
    stack_keepout = []            # layout B4: (net, x1, y1, x2, y2) Metal3 boxes of other nets a stack must clear
    stack_log = []

    def src_stack(self, name, net, mode, xa, yS, cand, sxD, xmax):
        """layout B4 (2026-10-27): multi-cut via stack from a CDAC driver source rail (Metal1 at yS) to its Metal4 strap.
        Columns: every source pin candidate on the router grid and, 0.5 um west of it, an off-grid column (cut pitch
        0.5 um), kept >= 0.6 um from every drain strip and >= xa - 0.3. 'p' (PMOS, strap STRAP_REF over the row): three
        cut rows yS, yS - 0.5, yS - 1.0 of Via1, Via2, Via3, Metal1-4 pads over the rows (the Metal4 pad merges into the
        strap). 'n' (NMOS, strap STRAP_GNDK below the gate rail): two rows of Via1 / Via2, a Metal3 strip down to the
        strap, three rows of Via3 under the strap. All boxes are reserved for the net; the grid nodes inside them form
        the source pin (the Metal4 / strap node makes the router connection zero length). Returns (pin nodes, rail x min)."""
        cols = []
        for c in sorted(set([round(c - 0.5, 4) for c in cand] + list(cand))):
            if c < xa - 0.3 or c > xmax + 1e-6 or any(abs(c - q) < 0.6 - 1e-6 for q in sxD):
                continue
            if cols and c - cols[-1] < 0.5 - 1e-6:
                continue
            cols.append(c)
        rows = [yS, round(yS - 0.5, 4), round(yS - 1.0, 4)] if mode == 'p' else [yS, round(yS - 0.5, 4)]
        ylo, yhi = rows[-1], rows[0]
        if mode == 'n':
            y3a = STRAP_GNDK[0] + 0.1
            vrows3 = [round(STRAP_GNDK[0] + 0.3 + 0.5 * k, 4) for k in range(3)]
        keep = []
        fmode = False
        for c in cols:
            bx = (c - 0.2, (y3a if mode == 'n' else ylo - 0.2), c + 0.2, yhi + 0.2)
            # dev1: stacks next to a feeder of the same net met the feeder Via3 array and the router vias on the feeder
            # nodes (V2.b, V3.a, V3.b): every feeder is a keep-out (0.8 um), whatever its net
            near = [(n2, b) for (n2, *b) in self.stack_keepout
                    if bx[0] - 0.8 < b[2] and b[0] < bx[2] + 0.8 and bx[1] - 0.8 < b[3] and b[1] < bx[3] + 0.8]
            if near:
                # dev4: a PMOS column on its own reference feeder (the Metal3 feeder covers the column): Via1 / Via2 only,
                # the Metal3 pad merges into the feeder, the feeder Via3 rows join the strap; the Metal3 grid nodes of
                # the pad join the device pin, so the router adds no via next to the off-grid cuts
                if mode == 'p' and all(n2 == net and b[0] + 0.2 <= c - 0.5 and c + 0.2 <= b[2] for n2, b in near):
                    fmode = True
                    keep.append(c)
                continue
            keep.append(c)
        cols = keep
        if fmode:
            # dev4 V2.b: the router still places Via2 on the feeder grid nodes; feeder-mode cuts on grid nodes only
            # (column on the grid, rows yS and yS - 0.8), so a router via coincides with a cut
            cols = [c for c in cols if abs(c / P - round(c / P)) < 1e-6]
            rows = [yS, round(yS - P, 4)]
            ylo, yhi = rows[-1], rows[0]
        if not cols:
            self.stack_log.append((name, 'no column'))
            return [], 1e9
        D, R = self.D, self.R
        groups = []
        for c in cols:
            if groups and c - groups[-1][-1] <= 0.5 + 1e-6:
                groups[-1].append(c)
            else:
                groups.append([c])
        nodes = []
        ncut = 0
        for g in groups:
            x1, x2 = g[0], g[-1]
            self.box('M1', x1 - 0.17, ylo - 0.17, x2 + 0.17, yhi + 0.17)
            self.box('M2', x1 - 0.2, ylo - 0.2, x2 + 0.2, yhi + 0.2)
            R.reserve(0, x1 - 0.2, ylo - 0.2, x2 + 0.2, yhi + 0.2, net)
            if mode == 'p' and fmode:
                self.box('M3', x1 - 0.2, ylo - 0.2, x2 + 0.2, yhi + 0.2)
                R.reserve(1, x1 - 0.2, ylo - 0.2, x2 + 0.2, yhi + 0.2, net)
                vias = ('Via1', 'Via2')
            elif mode == 'p':
                for L in ('M3', 'M4'):
                    self.box(L, x1 - 0.2, ylo - 0.2, x2 + 0.2, yhi + 0.2)
                R.reserve(1, x1 - 0.2, ylo - 0.2, x2 + 0.2, yhi + 0.2, net)
                R.reserve(2, x1 - 0.2, ylo - 0.2, x2 + 0.2, yhi + 0.2, net)
                vias = ('Via1', 'Via2', 'Via3')
            else:
                self.box('M3', x1 - 0.2, y3a, x2 + 0.2, yhi + 0.2)
                R.reserve(1, x1 - 0.2, y3a, x2 + 0.2, yhi + 0.2, net)
                vias = ('Via1', 'Via2')
            for c in g:
                for y in rows:
                    for v in vias:
                        D.sq(v, c, y, VIA); ncut += 1
                if mode == 'n':
                    for y in vrows3:
                        D.sq('Via3', c, y, VIA); ncut += 1
            for gx in gpts(x1 - 0.2, x2 + 0.2):
                for gy in gpts(ylo - 0.2, yhi + 0.2):
                    nodes.append((0, gx, gy))
                    if mode == 'p' and fmode:
                        nodes.append((1, gx, gy))
                    elif mode == 'p':
                        nodes += [(1, gx, gy), (2, gx, gy)]
                if mode == 'n':
                    for gy in gpts(y3a, yhi + 0.2):
                        nodes.append((1, gx, gy))
                    nodes += [(2, gx, gy) for gy in gpts(STRAP_GNDK[0] + 0.3, STRAP_GNDK[1] - 0.3)]
        self.stack_log.append((name, mode + ('-feeder' if fmode else ''), cols, ncut))
        return nodes, cols[0] - 0.17

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
    # layout B5: Metal3 stays free in the two dummy-ring rows (row 0 and row NR-1 have no bottom-plate tracks), so the
    # SAR lines can hop over the cmp4 cap-row Metal2 rails under row 0 and jog under the top row
    blk.R.block_area([2], AX, AY, AX + NC * SP, AY + NR * SP)
    blk.R.block_area([1], AX, AY + SP, AX + NC * SP, AY + (NR - 1) * SP)
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
# layout B: no gnd edge pins (slice gnd = Metal4 strap fed from the top-level TopMetal1 vss sheet through the drops
# SLICE_DROPS); vref pins x 100.0 / 106.4 / 112.8 (MSB driver group), vrefl pins at the two LSB driver groups
SLICE_SOUTH = [('vdd', 12.0), ('vbn', 144.8), ('vbp', 148.8), ('vref', 100.0), ('vref', 106.4), ('vref', 112.8),
               ('vrefl', 72.0), ('vrefl', 136.0), ('vdd', 68.0), ('vdd', 170.4), ('vdd', 208.0)]
# slice straps (local y, Metal4): vdd, gnd, Kelvin driver ground gnd@K, reference straps over the driver P row
STRAP_VDD = (17.6, 20.8)
STRAP_GND = (22.4, 25.6)
STRAP_GNDK = (28.0, 29.6)
STRAP_REF = (40.0, 41.6)
# drop points (local x on the gnd strap, y at its centre): every decoupling-plate gap that falls on slice A or slice B
SLICE_DROPS = [('gnd', 11.06, 24.0), ('gnd', 37.2, 24.0), ('gnd', 65.84, 24.0), ('gnd', 91.98, 24.0), ('gnd', 120.62, 24.0),
               ('gnd', 146.76, 24.0), ('gnd', 175.4, 24.0), ('gnd', 201.54, 24.0)]
SLICE_WEST = [('in0p', 56.0), ('in0n', 60.0)]
SLICE_EAST = [('in1p', 76.0), ('in1n', 80.0)]     # global 130.4 / 134.4 (ISB pins 130 / 134)
# layout B5 (2026-10-27, T2k, D21): the hardened SAR sub-macro r1_adc_sar (release t2j-ll-h2312-h, 439.0 x 23.12 um)
# sits on top of the analog part at (0, H); the ADC box is 439.0 x HB5. Its south pins are at the x of the slice SAR
# ports; the slice routes each SAR port to a north edge pin (Metal3) at the macro pin x (slice A frame), the top router
# joins the slice north pins to the macro pins across the north channel.
SAR_PINS_JSON = os.path.join(HERE, '..', 'sar', 'flow', 'pins.json')
SAR_H = 23.12
SAR_GDS_SHA = '70e2c5b7b3d50b7952af2044063dd1068d1200b99aeb560d47e150a9298afc92'
SAR_SLICE_NET = {'clk': 'clk', 'clkb': 'clkb', 'clkn': 'clkn', 'clknb': 'clknb', 'p': 'op', 'n': 'on', 'np': 'onp',
                 'nn': 'onn', 'trk0': 'trk0', 'trk1': 'trk1'}


def sar_pins():
    """r1_adc_sar pins (flow/pins.json): list of dict(net, edge, x, y) in the macro frame."""
    return json.load(open(SAR_PINS_JSON))['pins']


def sar_south_map():
    """macro south pin -> (slice 'a'/'b' or None, slice-local port name, macro x). mclk: (None, 'sar_mclk', x)."""
    out = {}
    for p in sar_pins():
        if p['edge'] != 'S':
            continue
        n = p['net']
        m = re.match(r'^(cp|cn)([ab])\[(\d+)\]$', n)
        if m:
            out[n] = (m.group(2), '%s%s' % (m.group(1), m.group(3)), p['x']); continue
        m = re.match(r'^clkn([ab])(b?)$', n)
        if m:
            out[n] = (m.group(1), 'clkn' + m.group(2), p['x']); continue
        m = re.match(r'^(clk|trk|o)([ab])(.*)$', n)
        if m and n != 'mclk':
            kind, ch, rest = m.groups()
            key = {'clk': 'clk' + rest, 'trk': 'trk' + rest, 'o': rest}[kind]
            out[n] = (ch, SAR_SLICE_NET[key], p['x']); continue
        assert n == 'mclk', n
        out[n] = (None, 'sar_mclk', p['x'])
    return out


def slice_north():
    """slice north edge pins (port, local x): slice A macro pin x - SX[0] on the router grid."""
    return sorted([(port, gnear(x - SX[0])) for (ch, port, x) in sar_south_map().values() if ch == 'a'], key=lambda t: t[1])


SLICE_PAIRS = [('top_p@W', 'top_n@W'), ('top_p@E', 'top_n@E'), ('in0p', 'in0n'), ('in1p', 'in1n'),
               ('xc4_dip', 'xc4_din'), ('op', 'on'), ('xc5_dip', 'xc5_din'), ('onp', 'onn')]


def build_slice(ly):
    devs = NLM.slice_devices(NLM.NDUMMY)
    by = {d['name']: d for d in devs}
    # layout B: Kelvin driver ground. The sources of the CDAC bottom-plate driver NMOS are routed as the router net
    # gnd@K to their own Metal4 strap STRAP_GNDK, which joins the main gnd strap at one star point (port records keep
    # the net name gnd; LVS sees one net)
    for k in range(13):
        for sd in ('n', 'p'):
            d = by['xd%s%d_xmn' % (sd, k)]
            assert d['nets'][2] == 'gnd', d
            by[d['name']] = dict(d, nets=[d['nets'][0], d['nets'][1], 'gnd@K', d['nets'][3]])
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
    # layout B4: multi-cut source stacks on every driver (PMOS to STRAP_REF, NMOS to STRAP_GNDK); keep-out: the Metal3
    # feeders of the south pins (other nets than the device source)
    blk.stacks = {n: 'p' for _, g in pmos_groups for n in g}
    blk.stacks.update({n + '_xmn': 'n' for n in nl + nm + pm + pl})
    _fw = {'vdd': (0.8, STRAP_VDD[1]), 'vref': (1.0, STRAP_REF[1]), 'vrefl': (1.0, STRAP_REF[1])}
    blk.stack_keepout = [(n, x - _fw[n][0], 0.0, x + _fw[n][0], _fw[n][1]) for n, x in SLICE_SOUTH if n in _fw]
    blk.stack_log = []
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
    log('layout B4 source stacks: %s' % blk.stack_log)
    blk.stats['source_stacks'] = blk.stack_log
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
    # layout B: the r1_cmp5n input pair (xs1_xm1/2, gates on top_p / top_n) at the east end of the row, next to the
    # r1_cmp4 input pair at the west end of A_p: both comparator inputs sit below the east top-plate islands
    A_n = [c5('xci1'), c5('xci2'), c5('xs1_xmt1'), c5('xs1_xmtc'), c5('xmh1'), c5('xmh2'),
           c4('xmr1'), c4('xmr2'), c5('xs1_xm1'), c5('xs1_xm2')]
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
    # ---- layout B: supply and reference straps (Metal4) and their Metal3 feeders, drawn before routing -------------
    D = blk.D
    strap_nodes = {}
    def strap(net, x1, x2, ya, yb):
        blk.box('M4', x1, ya, x2, yb)
        # layout B4: reserve for the router net (net name without the '#k' strap key). Layouts B-B3 reserved the
        # reference straps for 'vref#k' / 'vrefl#k', so the strap nodes were dropped from the 'vref' / 'vrefl' pins and
        # the drivers reached the reference only through the Metal3 feeders (finding B4-1)
        R.reserve(2, x1, ya, x2, yb, net.split('#')[0])
        strap_nodes.setdefault(net, []).extend((2, x, y) for x in gpts(x1 + 0.4, x2 - 0.4) for y in gpts(ya + 0.3, yb - 0.3))
    strap('vdd', 0.8, WS - 0.8, *STRAP_VDD)
    strap('gnd', 0.8, WS - 0.8, *STRAP_GND)
    xk1, xk2 = gfloor(endsN[0][0] - 0.8), gceil(endsN[0][1] + 0.8)
    strap('gnd@K', xk1, xk2, *STRAP_GNDK)
    # star point: the only joint of gnd@K and gnd, at the centre of the driver row (between the drop points)
    xst = gnear((xk1 + xk2) / 2)
    blk.box('M4', xst - 0.8, STRAP_GND[1] - 0.1, xst + 0.8, STRAP_GNDK[0] + 0.1)
    R.reserve(2, xst - 0.8, STRAP_GND[1], xst + 0.8, STRAP_GNDK[0], 'gnd')
    # reference straps over the driver P row: vrefl (LSB groups) and vref (MSB group), one per NWell group
    for (bulk, g), sg in zip(pmos_groups, segs):
        strap(bulk + '#%d' % len(strap_nodes), gfloor(sg['x0'] - 0.4), gceil(sg['xend'] + 0.4), *STRAP_REF)
    # the two vrefl straps stay separate router pins: each has its own feeder, the router joins them inside the slice
    # (dev1: one merged pin left the second vrefl group unconnected inside the slice, LVS split vrefl)
    sx = {k: (sg['x0'], sg['xend']) for k, sg in zip([k for k in strap_nodes if '#' in k], segs)}
    log('layout B straps: gnd@K x %.1f-%.1f, star x %.1f; P groups %s' % (xk1, xk2, xst,
        ['%s %.1f-%.1f' % (b, sg['x0'], sg['xend']) for (b, _), sg in zip(pmos_groups, segs)]))
    # feeders: Metal3 from the south pin up to the strap of the net, Via3 array on the overlap
    ftop = {'vdd': STRAP_VDD, 'vref': STRAP_REF, 'vrefl': STRAP_REF}
    fw = {'vdd': 0.8, 'vref': 1.0, 'vrefl': 1.0}
    feeders = []
    for net, x in SLICE_SOUTH:
        if net not in ftop:
            continue
        ya, yb = ftop[net]
        blk.box('M3', x - fw[net], 0.0, x + fw[net], yb)
        R.reserve(1, x - fw[net], 0.0, x + fw[net], yb, net)
        if net in ('vref', 'vrefl'):
            # layout B4 (dev2 V3.a): the reference straps are now router pins of their net, so router vias can land on
            # the feeder nodes; Via3 cuts on grid nodes only (they coincide with a router via), Metal4 0.2 um below the
            # strap for a second row
            blk.box('M4', x - fw[net], ya - 0.2, x + fw[net], yb)
            for xx in gpts(x - fw[net] + 0.15, x + fw[net] - 0.15):
                for yy in gpts(ya - 0.05, yb - 0.15):
                    D.sq('Via3', xx, yy, VIA)
        else:
            blk.box('M4', x - fw[net], ya, x + fw[net], yb)
            via_array(D, 'Via3', x - fw[net], ya, x + fw[net], yb)
        key = net if net in strap_nodes else [k for k, (a, b) in sx.items() if k.split('#')[0] == net and a <= x <= b][0]
        strap_nodes[key].extend((1, xx, y) for xx in gpts(x - fw[net] + 0.4, x + fw[net] - 0.4) for y in gpts(0.0, yb - 0.3))
        feeders.append((net, x))
    for key, nodes in strap_nodes.items():
        blk.pin(key.split('#')[0], sorted(set(nodes)), 'm4')
    blk.stats['straps'] = dict(vdd=STRAP_VDD, gnd=STRAP_GND, gndk=[STRAP_GNDK, xk1, xk2, xst], ref=STRAP_REF, feeders=feeders)
    # ---- edge pins ---------------------------------------------------------------------------------------------------
    R.block_edges()
    edge = {}
    for net, x in SLICE_SOUTH:
        R.unblock(1, x, 0.0)
        if net not in ftop:
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
    # layout B5: SAR ports to the north edge (Metal3 edge node at the slice A macro pin x)
    xs_n = [x for _, x in slice_north()]
    assert len(set(xs_n)) == len(xs_n), 'two slice north pins on one grid column'
    for net, x in slice_north():
        R.unblock(1, x, HS)
        R.unblock(0, x, HS)          # Metal2 below the edge node: the only free layer over the array
        blk.pin(net, [(1, x, HS)], 'm3')
        edge.setdefault(net, []).append(('N', x, HS))
    # ---- route -------------------------------------------------------------------------------------------------------
    # comparator clocks first, with a soft halo (other nets keep the next track free for the ground shield)
    CLK = ['clkb', 'clkn', 'clk', 'clknb']
    R.halo_cost, R.halo_only = 40, set(CLK) | {'top_p@W', 'top_n@W', 'top_p@E', 'top_n@E'}    # layout B: top plates too
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
        for net in (('clk', 'clkb', 'clkn', 'clknb') if cellname == 'r1_adc_slice' else tuple(B5_CLOCKS)):
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
VREF_Y = (47.6, 49.2)        # layout B: 1.6 um lower than layout A (room for the vdd strap)
VREFL_Y = (45.2, 46.8)
TOP_VDD_Y = (49.8, 54.0)     # layout B: vdd strap under the slices (Metal4 full width, Metal3 between the pin stubs)
TOP_VSS_Y = (2.0, 4.4)       # layout B: vss Metal4 strap (layout A: 0.8 um at y 3.2)
TOP_VDDA_Y = (30.4, 32.8)    # layout B: vdda strap from the pin to the buffer (Metal4)
FEED_X = {'vdda': 50.0, 'vdd': 100.0, 'vss': 150.0}
# layout B4 (2026-10-27, assembly try f, r1_top/reports/integration_checklist_f.md): supply and reference pins 1.0 um
# wide at the macro edge (chip-level EM), centres unchanged
SUPPLY_PINS = ('vdd', 'vdda', 'vss', 'vref_in')
SUPPLY_PIN_HW = 0.5
# layout B4 (D21, SAR sub-macro r1_adc_sar for B5): router keep-out at the north edge, all routing layers, y >= NORTH_KEEP_Y
# and x >= NORTH_KEEP_X0 (east of the comparator clock generator); the pin stubs stay
NORTH_KEEP_Y, NORTH_KEEP_X0 = 171.6, 107.2      # layout B4 only; B5 has no north keep-out
# layout B5: comparator clock generator moved from x 8 (under the macro's slice-A pins) to the north band between the
# slice-A and slice-B macro pin groups; its five 10 fF delay MIMs over its device rows (MIM over MOS, as the decap)
CKG_X0 = 157.6
# layout B5 supplies of the SAR macro (INTEGRATION.md 3, 4): vdd riser (Metal4, inter-slice gap) from the top vdd strap
# to a Metal5 bus over the macro VDD straps; vss: TopMetal1 strap (inter-slice gap) from the decoupling TopMetal1 sheet
# (the top-level vss plane) to a Metal5 bus over the macro VSS straps. Macro straps: VDD x 14.08 + 54 n, VSS x 17.28 +
# 54 n, 1.6 um wide, macro y 3.56-22.90 (LEF)
VDD_RISER_X = (220.8, 223.2)
VSS_TM1_X = (216.8, 222.2)        # TM1.b 1.64 um to the slice TopMetal1 (215.06 / 223.88)
SAR_VDD_BUS_Y = (4.0, 7.0)          # macro frame
SAR_VSS_BUS_Y = (15.0, 18.0)
SAR_CLK_Y5 = 180.0                  # clk: Metal5 from the macro clk pin (Metal4 at x 6.24) to the clock generator


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


B5_CLOCKS = ['clk', 'sar_mclk', 'sar_clka', 'sar_clkab', 'sar_clkna', 'sar_clknab', 'sar_clkb', 'sar_clkbb', 'sar_clknb',
             'sar_clknbb']
B5_NODE_Y = 180.8                   # router node of a macro south pin (Metal2); a Metal2 jog joins it to the pin


def b5_sar_connect(blk):
    """layout B5: router pins at the macro south pins, the clk feed point, supply straps (reserved before routing)."""
    R, D = blk.R, blk.D
    jogs = []
    for name, (ch, port, x) in sorted(sar_south_map().items()):
        net = port if ch is None else NLM.slice_map(ch)[port]
        xg = gnear(x)
        R.unblock(0, xg, B5_NODE_Y)
        blk.pin(net, [(0, xg, B5_NODE_Y)], 'm2')
        # clear 0.42: a foreign pad closer than 0.21 um to the jog is reserved; the next pin node (>= 0.44 um) is not
        R.reserve(0, min(x, xg) - 0.2, B5_NODE_Y - 0.2, max(x, xg) + 0.2, H, net, clear=0.42)
        jogs.append((net, x, xg))
    blk.stats['b5_jogs'] = jogs
    # macro area: no router use above the analog box
    R.block_area([0, 1, 2], 0.0, H - 0.3, W, H + 1.0)
    # clk: Metal4 pad under the Metal5 feed end (drawn in b5_draw) is the router pin of clk
    xc = gnear(CKG_X0 + 0.8)
    R.unblock(2, xc, SAR_CLK_Y5)
    blk.pin('clk', [(2, xc, SAR_CLK_Y5)], 'm4')
    R.reserve(2, xc - 0.2, SAR_CLK_Y5 - 0.2, xc + 0.2, SAR_CLK_Y5 + 0.2, 'clk')
    blk.stats['b5_clk_feed'] = (xc, SAR_CLK_Y5)
    # vdd riser (Metal4) from the top vdd strap to y H - 0.3; router pins along it for the clock generator
    x1, x2 = VDD_RISER_X
    R.reserve(2, x1, TOP_VDD_Y[0], x2, H - 0.3, 'vdd')
    blk.pin('vdd', [(2, x, y) for x in gpts(x1 + 0.4, x2 - 0.4) for y in gpts(TOP_VDD_Y[1] + 0.8, H - 1.2)][::3], 'm4')


def b5_draw(blk):
    """layout B5: Metal2 jogs to the macro pins, macro north pins as ADC pins, supply straps and buses, clk feed."""
    D = blk.D
    for net, x, xg in blk.stats['b5_jogs']:
        D.box('M2', min(x, xg) - 0.2, B5_NODE_Y - 0.2, max(x, xg) + 0.2, B5_NODE_Y + 0.2)
        D.box('M2', x - 0.2, B5_NODE_Y - 0.2, x + 0.2, H + 0.3)
    # vdd: Metal4 riser, Via4 array, Metal5 riser to the VDD bus over the macro, Via4 on each macro VDD strap
    x1, x2 = VDD_RISER_X
    yb1, yb2 = H + SAR_VDD_BUS_Y[0], H + SAR_VDD_BUS_Y[1]
    D.box('M4', x1, TOP_VDD_Y[0], x2, H - 0.3)
    D.box('M5', x1, H - 2.6, x2, yb2)
    n4 = via_array(D, 'Via4', x1, H - 2.6, x2, H - 0.3)
    D.box('M5', 13.6, yb1, 394.2, yb2)
    nv = 0
    for n in range(8):
        xs = 14.08 + 54 * n
        nv += via_array(D, 'Via4', xs, yb1, xs + 1.6, yb2)
    # vss: TopMetal1 strap from the decoupling sheet to the VSS bus; TopVia1 array; Via4 on each macro VSS strap
    t1, t2 = VSS_TM1_X
    ys1, ys2 = H + SAR_VSS_BUS_Y[0], H + SAR_VSS_BUS_Y[1]
    D.box('TM1', t1, DEC_Y + DEC_H - 3.0, t2, ys2)
    D.box('M5', 16.8, ys1, 397.4, ys2)
    ntv = via_array(D, 'TV1', t1, ys1, t2, ys2)
    nvs = 0
    for n in range(8):
        xs = 17.28 + 54 * n
        nvs += via_array(D, 'Via4', xs, ys1, xs + 1.6, ys2)
    # clk feed: Via4 on the macro clk Metal4 (x 6.14-6.34, macro y 19.5-22.825), Metal5 down to SAR_CLK_Y5 and east to
    # the router pin (Metal4 pad + Via4)
    xk, yk = 6.24, H + 21.2
    D.box('M4', xk - 0.1, yk - 0.3, xk + 0.1, yk + 0.3)
    D.sq('Via4', xk, yk, VIA)
    xc, yc = blk.stats['b5_clk_feed']
    D.box('M5', xk - 0.2, yc - 0.2, xk + 0.2, yk + 0.25)
    D.box('M5', xk - 0.2, yc - 0.2, xc + 0.2, yc + 0.2)
    D.sq('Via4', xc, yc, VIA); D.sq('M4', xc, yc, 0.40)
    # north pins of the ADC = macro north pins (Metal2, 0.40 x 0.585 at the macro edge); B5 pin list
    pins = []
    for p in sar_pins():
        if p['edge'] != 'N':
            continue
        # label in the CDL form adc_raw_a<k>: with adc_raw_a[k] (layouts A-B4) the strict-port LVS fails (dev5); in B4 the
        # north pins had no devices, so the name form was never compared
        net = p['net'].replace('[', '<').replace(']', '>')
        x = p['x']
        D.box('M2', x - 0.2, HB5 - 0.4, x + 0.2, HB5)          # = the macro pin shape (10/2), inside its Metal2
        D.box('M2pin', x - 0.2, HB5 - 0.4, x + 0.2, HB5)
        D.label('M2txt', x, HB5 - 0.3, net, 0.2)
        pins.append((net, round(x, 3), HB5))
    blk.stats['b5'] = dict(north_pins=pins, vdd_riser=dict(x=VDD_RISER_X, via4=n4), vdd_bus_via4=nv,
                           vss_tm1=dict(x=VSS_TM1_X, tv1=ntv), vss_bus_via4=nvs, clk_feed=(xk, yk, xc, yc))
    log('B5 straps: vdd riser via4 %d, vdd bus via4 %d, vss TV1 %d, vss bus via4 %d' % (n4, nv, ntv, nvs))


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
                if (side == 'S' and net != 'vdd') or side == 'N':
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
    ys = 3.2                                    # vss Metal4 strap (centre)
    yi = 9.6                                    # vss islands in the gaps
    # layout B: the TopMetal1 top-plate sheet (all plates on vss) is the vss plane. Each gap: a 3.0 um TopMetal1 bridge,
    # a Metal5 island 1.0 x 3.0 um with 3 TopVia1 and 12 Via4, a 1.6 um Metal4 riser to the 2.4 um vss strap; and, where
    # the gap falls on a slice, a drop at the slice gnd strap (global y SY + STRAP_GND centre): bridge, island, TopVia1,
    # Via4 and a Metal4 pad on the slice strap (SLICE_DROPS)
    ydr = round(SY + sum(STRAP_GND) / 2, 4)
    drops = []
    def drop(xg, yc, h):
        D.box('TM1', xg - 0.5, yc - h / 2, xg + 0.5, yc + h / 2)
        D.box('M5', xg - 0.5, yc - h / 2, xg + 0.5, yc + h / 2)
        n1 = via_array(D, 'TV1', xg - 0.5, yc - h / 2, xg + 0.5, yc + h / 2)
        n4 = via_array(D, 'Via4', xg - 0.5, yc - h / 2, xg + 0.5, yc + h / 2)
        D.box('M4', xg - 0.5, yc - h / 2, xg + 0.5, yc + h / 2)
        return n1, n4
    for i in range(len(plan) - 1):
        pa, pb = plan[i], plan[i + 1]
        xa, xb = pa['x'] + pa['w'] - 2.0, pb['x'] + 2.0
        for yb, hb in ((yi, 3.0), (30.0, 2.0), (70.0, 2.0), (90.0, 2.0)):
            D.box('TM1', xa, yb - hb / 2, xb, yb + hb / 2)
        xg = gapc[i]
        drop(xg, yi, 3.0)
        D.box('M4', xg - 0.8, TOP_VSS_Y[0], xg + 0.8, yi + 1.5)
        R.reserve(2, xg - 0.8, TOP_VSS_Y[0], xg + 0.8, yi + 1.5, 'vss')
        if any(x0 + 2.0 < xg < x0 + WS - 2.0 for x0 in SX):
            D.box('TM1', xa, ydr - 1.5, xb, ydr + 1.5)
            n1, n4 = drop(xg, ydr, 3.0)
            drops.append(dict(x=xg, y=ydr, tv1=n1, via4=n4, slice='a' if xg < SX[1] else 'b',
                              local_x=round(xg - (SX[0] if xg < SX[1] else SX[1]), 3)))
    blk.stats['vss_drops'] = drops
    log('layout B vss drops', drops)
    D.box('M4', 4.0, TOP_VSS_Y[0], W - 4.0, TOP_VSS_Y[1])
    R.reserve(2, 4.0, TOP_VSS_Y[0], W - 4.0, TOP_VSS_Y[1], 'vss')
    # vss pin feeder (Metal3 2 um, Via3 array into the strap)
    xf = FEED_X['vss']
    D.box('M3', xf - 1.0, 0.0, xf + 1.0, TOP_VSS_Y[1]); R.reserve(1, xf - 1.0, 0.0, xf + 1.0, TOP_VSS_Y[1], 'vss')
    via_array(D, 'Via3', xf - 1.0, TOP_VSS_Y[0], xf + 1.0, TOP_VSS_Y[1])
    for x in [x for x in gpts(6.0, W - 6.0)[::12] if all(abs(x - f) > 2.4 for f in FEED_X.values())]:
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
    # ---- layout B: vdd strap under the slices, vdd and vdda feeders, vdda strap to the buffer ----------------------
    va, vb = TOP_VDD_Y
    nodes = []
    D.box('M4', 4.0, va, W - 4.0, vb); R.reserve(2, 4.0, va, W - 4.0, vb, 'vdd')
    nodes += [(2, x, y) for x in gpts(4.4, W - 4.4) for y in gpts(va + 0.3, vb - 0.3)]
    # Metal3 in parallel, except around the slice south pins of other nets (their stubs cross the strap on Metal3)
    excl = []
    for q, x0 in enumerate(SX):
        for (net, x) in SLICE_SOUTH:
            if net != 'vdd':
                excl.append((x0 + x - 1.4, x0 + x + 1.4))
    vstub = [round(x0 + x, 4) for x0 in SX for (net, x) in SLICE_SOUTH if net == 'vdd']
    segs3, xa_ = [], 4.0
    for (e1, e2) in sorted(excl) + [(W - 4.0, W)]:
        if e1 - xa_ > 2.0:
            segs3.append((xa_, e1))
        xa_ = max(xa_, e2)
    for (x1, x2) in segs3:
        D.box('M3', x1, va, x2, vb); R.reserve(1, x1, va, x2, vb, 'vdd')
        nodes += [(1, x, y) for x in gpts(x1 + 0.4, x2 - 0.4) for y in gpts(va + 0.3, vb - 0.3)]
        for xv in [x1 + 1.0 + k * 8.0 for k in range(int((x2 - x1 - 2.0) / 8.0) + 1)]:
            if all(abs(xv - X) > 2.2 for X in vstub + [FEED_X['vdd']]):     # dev2: overlapping arrays (V3.a)
                via_array(D, 'Via3', xv - 1.0, va, min(xv + 1.0, x2), vb)
    for X in vstub:          # stubs to the slice vdd pins (the slice feeder starts at the slice edge)
        D.box('M3', X - 0.8, va, X + 0.8, SY); R.reserve(1, X - 0.8, va, X + 0.8, SY, 'vdd')
        via_array(D, 'Via3', X - 0.8, va, X + 0.8, vb)
        nodes.append((1, X, SY))
    # vdd pin feeder: Metal3 to below the vrefl bus, Metal2 under both reference buses, Metal3 into the strap
    xf = FEED_X['vdd']
    yb1 = VREFL_Y[0] - 1.2
    D.box('M3', xf - 1.0, 0.0, xf + 1.0, yb1); R.reserve(1, xf - 1.0, 0.0, xf + 1.0, yb1, 'vdd')
    D.box('M2', xf - 1.0, yb1 - 0.8, xf + 1.0, va + 0.8); R.reserve(0, xf - 1.0, yb1 - 0.8, xf + 1.0, va + 0.8, 'vdd')
    D.box('M3', xf - 1.0, va, xf + 1.0, vb); R.reserve(1, xf - 1.0, va, xf + 1.0, vb, 'vdd')
    via_array(D, 'Via2', xf - 1.0, yb1 - 0.8, xf + 1.0, yb1)
    via_array(D, 'Via2', xf - 1.0, va, xf + 1.0, va + 0.8)
    via_array(D, 'Via3', xf - 1.0, va + 0.8, xf + 1.0, vb)
    nodes += [(1, x, y) for x in gpts(xf - 0.6, xf + 0.6) for y in gpts(0.8, yb1 - 0.3)]
    blk.pin('vdd', sorted(set(nodes)), 'm4')
    # vdda: Metal3 feeder from the pin, Metal4 strap to the buffer (followers, xm3 / xm4 sources)
    xf = FEED_X['vdda']
    da, db = TOP_VDDA_Y
    xe_ = gceil(W / 2 + 26.0)
    D.box('M3', xf - 1.0, 0.0, xf + 1.0, db); R.reserve(1, xf - 1.0, 0.0, xf + 1.0, db, 'vdda')
    D.box('M4', xf - 1.0, da, xe_, db); R.reserve(2, xf - 1.0, da, xe_, db, 'vdda')
    via_array(D, 'Via3', xf - 1.0, da, xf + 1.0, db)
    nodes = [(2, x, y) for x in gpts(xf, xe_ - 0.4) for y in gpts(da + 0.3, db - 0.3)]
    nodes += [(1, x, y) for x in gpts(xf - 0.6, xf + 0.6) for y in gpts(0.8, db - 0.3)]
    blk.pin('vdda', sorted(set(nodes)), 'm4')
    blk.stats['top_straps'] = dict(vdd=TOP_VDD_Y, vss=TOP_VSS_Y, vdda=[TOP_VDDA_Y, xe_], feeders=FEED_X, vdd_m3=segs3)
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
    # ---- layout B2 (2026-10-26): buffer output straps -------------------------------------------------------------
    # Layout B (PEX B.1) joined the follower sources, the bias sinks and the reference buses only through router wires:
    # 136 Ohm from the vref follower to the bus, and the sink current flowed follower -> bus -> sink (static drop 19 mV
    # at the slice pins). B2: Metal2 straps with Via1 at every grid node on the follower source rails and the sink drain
    # rails; vref: Metal3 strap over the sink rails, four Metal3 verticals (sinks - followers - up to y 44.8) and Metal2
    # jumpers under the vrefl bus into the vref bus; vrefl: Metal3 straps on its follower / sink rails, a Metal4 run
    # between them and a Metal4 vertical into the vrefl bus (east of the vdda strap).
    def rail(dev, term):
        b = [q for q in blk.ports if q['dev'] == dev and q['term'] == term][0]['box']
        return b[0], b[1], b[2], b[3]
    def grid_vias(via, x1, y1, x2, y2):
        # cuts only at router grid nodes (a router via of the same net at a node coincides; dev1 V2.b: 0.5 um pitch
        # arrays next to router vias), 0.2 um from the box edge (0.105 enclosure)
        n = 0
        for x in gpts(x1 + 0.2, x2 - 0.2):
            for y in gpts(y1 + 0.2, y2 - 0.2):
                D.sq(via, x, y, VIA); n += 1
        return n
    def m2_strap(dev, term, net):
        x1, y1, x2, y2 = rail(dev, term)
        yc = round((y1 + y2) / 2, 4)
        xs = gpts(x1 + 0.3, x2 - 0.3)
        D.box('M2', xs[0] - 0.2, yc - 0.2, xs[-1] + 0.2, yc + 0.2); R.reserve(0, xs[0] - 0.2, yc - 0.2, xs[-1] + 0.2, yc + 0.2, net)
        for x in xs:
            D.sq('Via1', x, yc, VIA)
        blk.pin(net, [(0, x, yc) for x in xs], 'm4')
        return xs[0], xs[-1], yc
    fol = [m2_strap('xref_xmsf_s%d' % k, 2, 'vref') for k in range(4)]
    snk = [m2_strap('xref_xmib_s%d' % k, 0, 'vref') for k in range(4)]
    ys_, xs1, xs2 = snk[0][2], max(snk[0][0], gceil(FEED_X['vdd'] + 2.0)), snk[-1][1]     # clear of the vdd feeder (Metal3, x 99-101)
    D.box('M3', xs1 - 0.2, ys_ - 0.2, xs2 + 0.2, ys_ + 0.2); R.reserve(1, xs1 - 0.2, ys_ - 0.2, xs2 + 0.2, ys_ + 0.2, 'vref')
    for (a, b, y) in snk:
        for x in gpts(max(a, xs1), b):
            D.sq('Via2', x, y, VIA)
    yf = fol[0][2]
    VX = [gnear(fol[0][0] + 17.6), gnear(fol[1][0] + 13.6), gnear(fol[2][0] + 4.8), gnear(fol[3][0] + 15.2)]
    ytop3 = VREFL_Y[0] - 0.4
    for xv in VX:
        D.box('M3', xv - 1.0, ys_ - 0.2, xv + 1.0, ytop3); R.reserve(1, xv - 1.0, ys_ - 0.2, xv + 1.0, ytop3, 'vref')
        grid_vias('Via2', xv - 1.0, yf - 0.2, xv + 1.0, yf + 0.2)
        yj1, yj2 = ytop3 - 1.6, VREF_Y[1] - 0.2
        D.box('M2', xv - 1.0, yj1, xv + 1.0, yj2); R.reserve(0, xv - 1.0, yj1, xv + 1.0, yj2, 'vref')
        grid_vias('Via2', xv - 1.0, yj1, xv + 1.0, ytop3)
        grid_vias('Via2', xv - 1.0, VREF_Y[0], xv + 1.0, yj2)
        blk.pin('vref', [(1, xv, y) for y in gpts(ys_ + 0.8, ytop3 - 0.4)], 'm4')
    # vrefl
    lf = m2_strap('xref_xmsfl_s0', 2, 'vrefl')
    ls = m2_strap('xref_xmibl_s0', 0, 'vrefl')
    for (a, b, y) in (lf, ls):
        D.box('M3', a - 0.2, y - 0.2, b + 0.2, y + 0.2); R.reserve(1, a - 0.2, y - 0.2, b + 0.2, y + 0.2, 'vrefl')
        for x in gpts(a, b):
            D.sq('Via2', x, y, VIA)
    xl4 = gnear(lf[0] + 16.8)
    assert xl4 - 0.8 > gceil(W / 2 + 26.0) + 0.4, xl4            # east of the vdda strap
    D.box('M4', xl4 - 1.0, lf[2] - 0.2, xl4 + 1.0, VREFL_Y[1]); R.reserve(2, xl4 - 1.0, lf[2] - 0.2, xl4 + 1.0, VREFL_Y[1], 'vrefl')
    grid_vias('Via3', xl4 - 1.0, lf[2] - 0.2, xl4 + 1.0, lf[2] + 0.2)
    D.box('M4', ls[0] - 0.2, ls[2] - 0.6, xl4 + 1.0, ls[2] + 0.6); R.reserve(2, ls[0] - 0.2, ls[2] - 0.6, xl4 + 1.0, ls[2] + 0.6, 'vrefl')
    for x in gpts(ls[0], ls[1]):
        D.sq('Via3', x, ls[2], VIA)
    blk.pin('vrefl', [(2, xl4, y) for y in gpts(lf[2] + 0.8, VREFL_Y[0] - 0.4)], 'm4')
    # layout B3 (2026-10-27): vrefl bus to the slice vrefl pins. In B2 the router crossed under the vref bus with
    # 0.40 um wires and single cuts (20-22 Ohm from the vrefl decoupling to the slice pins, vref 1.6 Ohm). B3: per pin
    # a Metal2 jumper (2.0 um) from inside the vrefl bus under the vref bus and a Metal3 stub (2.0 um) in the gap of the
    # vdd Metal3 strap up to the slice edge; Via2 at grid nodes at both ends
    vl_pins = []
    for x0 in SX:
        for (net, x) in SLICE_SOUTH:
            if net != 'vrefl':
                continue
            X = round(x0 + x, 4)
            ys1, ys2 = VREF_Y[1] + 0.4, SY + 0.4
            yj1, yj2 = VREFL_Y[0] + 0.2, ys1 + 1.8
            D.box('M3', X - 1.0, ys1, X + 1.0, ys2); R.reserve(1, X - 1.0, ys1, X + 1.0, ys2, 'vrefl')
            D.box('M2', X - 1.0, yj1, X + 1.0, yj2); R.reserve(0, X - 1.0, yj1, X + 1.0, yj2, 'vrefl')
            grid_vias('Via2', X - 1.0, VREFL_Y[0], X + 1.0, VREFL_Y[1])
            grid_vias('Via2', X - 1.0, ys1, X + 1.0, yj2)
            vl_pins.append(X)
    blk.stats['buffer_straps'] = dict(vrefl_pin_jumpers=vl_pins, vref_verticals=VX, vrefl_vertical=xl4, follower_rails=fol, sink_rails=snk, vrefl=[lf, ls])
    # comparator biases: rppd segments (west), diodes
    res = sorted([d for d in top_devs if d['kind'] == 'rppd'], key=lambda d: (d['orig'], d['seg']))
    groups = [dict(slots=[40.0], cols=[[d] for d in res if d['orig'] == 'xcbias_xrb']),
              dict(slots=[40.0], cols=[[d] for d in res if d['orig'] == 'xcbiasn_xrb'])]
    xe, ytop = resistor_array(blk, groups, 8.0, 6.4)
    tb1, _ = blk.mrow([dict(x0=gceil(xe + 2.4), devs=[by['xcbiasn_xmbd']], bulk='vss', gap=0.6)], 8.0, 'n')
    # layout B (dev3 antenna Ant.b 209.6 > 200 at the W 0.2 um vbn diode gate): no Metal3 in a band above the bias
    # diodes, so the vbn / vbp risers change to Metal4 after about 10 um of Metal3
    R.block_area([1], gfloor(xe + 1.6), 19.6, gceil(xe + 16.0), 23.6)
    tb2, _ = blk.mrow([dict(x0=gceil(xe + 2.4), devs=[by['xcbias_xmbd']], bulk='vdd', gap=0.6)], gceil(tb1 + 3.2), 'p')
    # ---- clock generator (north-west) -----------------------------------------------------------------------------
    ck = lambda n: by['xckg_' + n]
    cn = [ck('xnd0'), ck('xnd1'), ck('xnd2'), ck('xnd3'), ck('xnd4'), ck('xna'), ck('xnb'), ck('xni')]
    cp_ = [ck('xpd0'), ck('xpd1'), ck('xpd2'), ck('xpd3'), ck('xpd4'), ck('xpa'), ck('xpb'), ck('xpi')]
    tk1, _ = blk.mrow([dict(x0=CKG_X0, devs=cn, bulk='vss', gap=0.4)], 175.2, 'n')
    wk = blk.seg_w(cn, 0.4)
    tk2, ek2 = blk.mrow([dict(x0=gceil(CKG_X0 + wk + 2.4), devs=cp_, bulk='vdd', gap=0.4)], 175.2, 'p')
    for k in range(5):
        d = ck('cd%d' % k)
        mx = gceil(CKG_X0 + 1.6) + k * 7.2     # 7.2 pitch: TopMetal1 tab islands 1.64 um clear of the next plate
        blk.mim_rect(d['name'], d['w'], d['l'], mx, 175.2, d['nets'][0], d['nets'][1], tab='E')
    log('clkgen (B5) top %.2f %.2f, x %.2f - %.2f, MIM x end %.2f' % (tk1, tk2, CKG_X0, ek2[0][1], gceil(CKG_X0 + 1.6) + 4 * 7.2 + 5))
    assert ek2[0][1] + 0.6 < VDD_RISER_X[0], ek2
    # ---- long input pairs (hand-drawn), north channel shields -------------------------------------------------------
    long_pairs(blk)
    # layout B4 (D21): north keep-out for the SAR sub-macro row (free nodes only; pin stubs are reserved below)
    # layout B5: no north keep-out (B4 kept y >= 171.6 free for a SAR row inside the box)
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
            R.unblock(1, xg, 0.8)
            if net not in FEED_X:
                blk.pin(net, [(1, xg, 0.8)], 'm3')
        elif net in ('ain_sin_p', 'ain_sin_n', 'ain_isb_p', 'ain_isb_n'):
            pass       # straight Metal3 stubs to the slice edge pins (drawn below)
        elif net == 'ibias':
            pass
    # reserve the edge pin boxes and the straight input stubs (drawn after routing) for their nets
    for (net, side, x, y) in bp:
        if side == 'N':
            pass        # layout B5: north pins belong to the macro
        elif side == 'W':
            R.reserve(1, 0.0, y - 0.2, 1.0, y + 0.2, net)
        elif side == 'E':
            R.reserve(1, W - 1.0, y - 0.2, W, y + 0.2, net)
        elif side == 'S':
            hw = SUPPLY_PIN_HW if net in SUPPLY_PINS else 0.2
            R.reserve(1, min(x, gnear(x)) - hw, 0.0, max(x, gnear(x)) + hw, 1.0, net)
    for net, y in (('ain_sin_p', 110.0), ('ain_sin_n', 114.0)):
        R.reserve(1, 0.0, y - 0.2, SX[0] + 0.2, y + 0.6, net)
    for net, y in (('ain_isb_p', 130.0), ('ain_isb_n', 134.0)):
        R.reserve(1, SX[1] + WS - 0.2, y - 0.2, W, y + 0.6, net)
    b5_sar_connect(blk)
    # guard ring as vss at a few nodes next to the south vss pin
    blk.pin('vss', [(0, x, 0.8) for x in gpts(146.0, 154.0)], 'm1')
    # ---- route ------------------------------------------------------------------------------------------------------
    TOP_PAIRS = []
    R.halo_cost, R.halo_only = 40, set(B5_CLOCKS)
    ok = route_pairs(blk, B5_CLOCKS + ['vref', 'vrefl'], TOP_PAIRS, 'r1_adc')
    blk.stats.update(route_ok=ok, route_failed=R.failed)
    blk.draw_routes()
    # pins: Metal3 boxes, pin shapes, labels
    for (net, side, x, y) in bp:
        L = 'M3'
        if side == 'S':
            xg = gnear(x)       # pin at the checklist x, jog at y 0.6-1.0 to the router node (xg, 0.8)
            hw = SUPPLY_PIN_HW if net in SUPPLY_PINS else 0.2
            D.box(L, x - hw, 0.0, x + hw, 1.0); D.box('M3pin', x - hw, 0.0, x + hw, 1.0)
            D.label('M3txt', x, 0.5, net, 0.3)
            if abs(xg - x) > 1e-6:
                D.box(L, min(x, xg) - 0.2, 0.6, max(x, xg) + 0.2, 1.0)
        elif side == 'N':
            pass        # layout B5: drawn by b5_north_pins() on the macro pins
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
    b5_draw(blk)
    D.boundary(0, 0, W, HB5)
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
    # layout B: west verticals n at x 1.0, p at x 1.8 between Metal4 vss shields at x 0.2 and 2.6 (0.5 um spaces on
    # both sides of both lines); ibias moves to Metal2 (layout A: the p line ran next to ibias and vdd, 8.25 fF imbalance)
    for net, yp, xv, yh, xg, yend in (('ain_cos_p', 130.0, 1.8, 167.2, 220.8, 110.4), ('ain_cos_n', 134.0, 1.0, 168.0, 221.6, 114.4)):
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
    # ibias: west pin (0, 165) -> x 2.4 down to y 42.4 on Metal2 (router pin there)
    seg('M3', 0.0, 165.0, 2.4, 165.0, 'ibias'); via(2.4, 165.0, 0, 1, 'ibias')
    seg('M2', 2.4, 165.0, 2.4, 42.4, 'ibias')
    blk.pin('ibias', [(0, 2.4, 42.4)], 'm2')
    # COS / ISA shields: Metal4 at x 0.2 and 2.6 along the west COS verticals, joined to the channel shields; Metal3 at
    # x 222.4 (COS n side) and 216.8 (ISA n side) in the middle gap
    for x in (0.2, 2.6):
        D.box('M4', x - 0.15, 127.6, x + 0.15, 171.4)
        R.reserve(2, x - 0.15, 127.6, x + 0.15, 171.4, 'vss')
    for y in (166.4, 168.8, 171.2):
        via(2.6, y, 0, 2, 'vss')
    seg('M3', 222.4, 166.4, 222.4, 115.2, 'vss'); via(222.4, 166.4, 0, 1, 'vss')
    seg('M3', 216.8, 166.4, 216.8, 135.2, 'vss'); via(216.8, 166.4, 0, 1, 'vss')
    # shields: Metal2 in the channel (vss), Metal3 in the gap
    for y, xa, xb in ((166.4, 2.4, 436.8), (168.8, 2.4, 436.8), (171.2, 2.4, 436.8)):
        seg('M2', xa, y, xb, y, 'vss')
        D.box('M2', xa - 0.15, y - 0.2, xb + 0.15, y + 0.2)     # layout B: 0.40 um, no notch at the via pads (dev2 M2.b)
    for x in (219.2, 220.0):
        seg('M3', x, 166.4, x, 117.6, 'vss'); via(x, 166.4, 0, 1, 'vss')
    blk.pin('vss', [(0, 3.2, 166.4), (0, 436.0, 168.8), (0, 3.2, 171.2)], 'm2')
    # layout B4 (2026-10-27): ain_cos pair environment (B3 extraction, cap_breakdown.py: p 4.9 fF above n, from (a) the
    # Metal4 shield at x 0.2 without a via (floating: n saw no Metal4 sidewall to vss, p saw 3.7 fF), (b) a widened
    # top-level vdd Metal4 wire over the channel at y 166.2-167.4 (over p only, 1.0 fF overlap), (c) a widened vss Metal3
    # wire under the p Metal4 vertical at x 1.4-2.6 (1.7 fF))
    seg('M2', 0.2, 171.2, 2.4, 171.2, 'vss')
    D.box('M2', 0.05, 171.0, 2.4, 171.4)
    via(0.2, 171.2, 0, 2, 'vss')
    def block_free(l, x1, y1, x2, y2):
        for gx in gpts(x1, x2):
            for gy in gpts(y1, y2):
                i, j = R.ij(gx, gy)
                if R.inside(i, j) and R.res[l, i, j] == FREE:
                    R.res[l, i, j] = BLOCK
    block_free(2, 2.4, 165.6, 436.8, 172.0)        # no Metal4 over the north channel (both pairs see the same)
    block_free(1, 0.0, 127.6, 3.2, 148.8)          # no Metal3 under the west COS verticals (except the pin stubs and
    block_free(1, 0.0, 151.2, 3.2, 172.0)          # the vcm2 pin track at y 150, which crosses both lines once)
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
    # layout B5: the SAR macro as a cell reference (not flattened) at (0, H), R0
    import hashlib
    sgds = os.path.join(os.environ['G1_RESULTS_ROOT'], 'r1_adc_sar', 'release-t2j-h', 'r1_adc_sar.gds')
    assert hashlib.sha256(open(sgds, 'rb').read()).hexdigest() == SAR_GDS_SHA, 'r1_adc_sar.gds hash'
    sl2 = pya.Layout(); sl2.read(sgds)
    names = set(c.name for c in ly.each_cell())
    clash = [c.name for c in sl2.each_cell() if c.name in names]
    assert not clash, clash
    mc = ly.create_cell('r1_adc_sar')
    mc.copy_tree(sl2.top_cell())
    topc = ly.cell('r1_adc')
    topc.insert(pya.DCellInstArray(mc.cell_index(), pya.DTrans(0.0, H)))
    log('B5: r1_adc_sar placed at (0, %.2f), cells copied %d' % (H, sl2.cells()))
    import importlib
    importlib.reload(NLM)
    NLM.write_cdl()
    ly.write(OUT)
    rr = os.environ.get('G1_RESULTS_ROOT')
    log('wrote', (OUT.replace(rr, '<G1_RESULTS_ROOT>') if rr else OUT).replace('/work/', '<repo>/'))
    meta = dict(box=[W, HB5], analog_box=[W, H], slice=dict(origins=[[x, SY] for x in SX], size=[WS, HS], stats=sl.stats, edge=sl.edge),
                top=dict(stats=top.stats), log=LOG,
                ports=dict(slice=sl.ports, top=top.ports))
    json.dump(meta, open(os.path.join(HERE, 'r1_adc_layout.json'), 'w'), indent=1, default=str)


main()
