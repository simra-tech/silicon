#!/usr/bin/env python3
"""R1_GATE layout: the on-chip gate path (three PWM channels into the c2p inputs of the sg13g2_IOPadOut30mA pads).
Descends from the G1 generator designs/g1-guardian/blocks/g1_gate/layout/g1_gate_layout.py (sha256 in README); the
cell generators, the row/track structure and the library g1_layout_lib.py are unchanged. Only the netlist part is new.

Two variants, both in the netlist of record ../schematic/r1_gate.spice (default `hv`, one GDS each):
  hv  r1_gate_hv  AND in the 3.3 V domain (G1 style, no latch): 4 x g1_lvlup (pwm_a/b/c, gate_en), 4 x hv_inv at their
                  outputs, 1 x hv_inv (en_hn), per channel hv_inv + hv_nor2 + hv_inv, 3 x g1_lvldn back to 1.2 V.
                  Rows, south to north: vss bar | 1.2 V NMOS | 1.2 V PMOS | Metal2 track band | 3.3 V PMOS | 3.3 V NMOS | vdda bar.
  lv  r1_gate_lv  AND in the 1.2 V core: 3 x g1_lv_nand2 + 3 x g1_lv_inv. No 3.3 V devices. The port `vdda` of the
                  netlist exists as a bare Metal3 bar (label vdda, no device) so the pin list equals the netlist.
Pins (Metal3): inputs pwm_a pwm_b pwm_c gate_en and vdd on the west edge, outputs gc_a gc_b gc_c on the east edge,
vss bar south, vdda bar north. p+ guard ring (vss).
Run (container, repository root):  G1_WORKDIR=designs/r1-joint/blocks/r1_gate/layout flow/run.sh klayout -b -r r1_gate_layout.py
  variant: -rd variant=lv (default hv). Writes r1_gate_<variant>.gds and r1_gate_<variant>.lef next to this script;
  fill_r1_gate.sh then adds the PDK fill in place (the GDS of record is the filled one).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from g1_layout_lib import *  # noqa


def write_lef(path, name, bbox, pins, obs_layers):
    """Minimal LEF (copy of write_lef in the G1 g1_sense_layout.py): MACRO CLASS BLOCK, pins [(name, use, layer, x1, y1, x2, y2)],
    OBS = the listed layers over the macro."""
    x1, y1, x2, y2 = bbox
    L = []
    L.append('VERSION 5.8 ;\nBUSBITCHARS "[]" ;\nDIVIDERCHAR "/" ;\n')
    L.append('MACRO %s\n  CLASS BLOCK ;\n  ORIGIN 0 0 ;\n  FOREIGN %s 0 0 ;\n  SIZE %.3f BY %.3f ;\n  SYMMETRY X Y ;\n' % (name, name, x2 - x1, y2 - y1))
    for (pn, use, layer, px1, py1, px2, py2) in pins:
        L.append('  PIN %s\n    DIRECTION INOUT ;\n    USE %s ;\n    PORT\n      LAYER %s ;\n        RECT %.3f %.3f %.3f %.3f ;\n    END\n  END %s\n'
                 % (pn, use, layer, px1 - x1, py1 - y1, px2 - x1, py2 - y1, pn))
    L.append('  OBS\n')
    for layer, (ox1, oy1, ox2, oy2) in obs_layers:
        L.append('    LAYER %s ;\n      RECT %.3f %.3f %.3f %.3f ;\n' % (layer, ox1 - x1, oy1 - y1, ox2 - x1, oy2 - y1))
    L.append('  END\nEND %s\nEND LIBRARY\n' % name)
    with open(path, 'w') as f:
        f.write(''.join(L))
    print('wrote', path)


TPITCH = 0.8                   # Metal2 track pitch in the band
VW = 0.30                      # Metal3 vertical width
EXTW = 0.30                    # Metal2 track width
STUB = 0.6                     # gate stub end: this far outside the cell's Activ, into the gap
GAP = 2.0                      # gap between cells (two stub verticals fit: 0.8 apart)
PINW, PINL = 0.5, 2.0
BARW = 3.0


def build_gate(ly, variant='hv'):
    HV = variant == 'hv'
    top = ly.create_cell('r1_gate_' + variant)
    D = Draw(ly, top)
    ports = []                                          # (net, x, y)
    def port(net, x, y):
        ports.append((net, x, y))

    # ------------------------------------------------------------------ y structure ------------
    YVSS = 3.0                                          # south bar centre (1.5..4.5)
    YLN = 8.5                                           # 1.2 V NMOS Activ bottom (heights 1 / 2)
    YLP = YLN + 2.0 + 0.8                                # 1.2 V PMOS Activ bottom (heights 1 / 2)
    YLV_GATE = YLP - 0.45                                # shared gate contact (1.2 V)
    YVDD = YLP + 2.0 + 1.03                              # vdd rail centre (0.5 wide)
    YB0 = YLP + 2.0 + 2.6                                # band bottom (first track)
    # the band height is fixed after track packing; provisional HV y's are set from NTRACK below

    # ------------------------------------------------------------------ helpers ---------------
    def src_rail(m, side, strips, y_rail_lo):
        """Metal1 source rail of device m on `side` at the absolute rail level (y_rail_lo..+0.5)."""
        lo = abs(y_rail_lo - m.edge(side))
        m.rail(side, strips, lo=lo, hi=lo + 0.5)

    def drain_pad(m, k):
        """via pad on strip k inside the Activ (finger centre) -> Metal2 pad; returns (x, y)."""
        return m.strip_pad(k, 'bot', -m.wf / 2)

    def gate_stub(m, k, side, xstub):
        """individual gate pad of finger k on `side` (0.30 wide Metal2 pad for the 0.51 um pitch of
        the 1.2 V devices) with a Metal2 stub from the pad edge to xstub; returns (xstub, y)."""
        padw = 0.30 if m.l < 0.2 else 0.40
        gx, yc = m.gate_pad(k, side, padw=padw)
        ra, rb = m.yd(side, Mos.GRAIL_LO), m.yd(side, Mos.GRAIL_HI)
        if xstub < gx:
            D.box('M2', xstub - 0.20, min(ra, rb), gx - padw / 2 + 0.01, max(ra, rb))
        else:
            D.box('M2', gx + padw / 2 - 0.01, min(ra, rb), xstub + 0.20, max(ra, rb))
        return (xstub, yc)

    def shared_gate(mp, mn, k, ycont, xstub):
        """poly bridge between the PMOS (below) and NMOS (above) fingers k, contact at ycont with
        Metal1 pad, Via1 and a Metal2 stub to xstub; returns (xstub, ycont)."""
        gx = mp.gx(k)
        D.box('GatPoly', gx - mp.l / 2, mp.y1, gx + mp.l / 2, mn.y0)
        D.box('GatPoly', gx - 0.15, ycont - 0.15, gx + 0.15, ycont + 0.15)
        D.sq('Cont', gx, ycont, CONT)
        D.box('M1', gx - 0.15, ycont - 0.17, gx + 0.15, ycont + 0.17)
        D.sq('Via1', gx, ycont, VIA)
        D.box('M2', gx - 0.15, ycont - 0.20, gx + 0.15, ycont + 0.20)
        if xstub < gx:
            D.box('M2', xstub - 0.20, ycont - 0.15, gx - 0.15, ycont + 0.15)
        else:
            D.box('M2', gx + 0.15, ycont - 0.15, xstub + 0.20, ycont + 0.15)
        return (xstub, ycont)

    # ------------------------------------------------------------------ 1.2 V row cells --------
    LV_N, LV_P = [], []
    def lv_inv(x0, a, y, vdd_rail_top):
        mp = Mos(D, 'pmos', 2, 0.13, 1, x0, YLP); mn = Mos(D, 'nmos', 1, 0.13, 1, x0, YLN)
        LV_P.append(mp); LV_N.append(mn)
        src_rail(mp, 'top', [0], YLP + 2.0 + Mos.RAIL_LO); src_rail(mn, 'bot', [0], YLN - Mos.RAIL_HI)
        x, yy = drain_pad(mp, 1); port(y, x, yy)
        x, yy = drain_pad(mn, 1); port(y, x, yy)
        port(a, *shared_gate(mn, mp, 0, YLV_GATE, x0 - STUB))
        return mp.x1

    def lv_nand2(x0, a, b, y):
        mp = Mos(D, 'pmos', 4, 0.13, 2, x0, YLP); mn = Mos(D, 'nmos', 4, 0.13, 2, x0, YLN)
        LV_P.append(mp); LV_N.append(mn)
        src_rail(mp, 'top', [1], YLP + 2.0 + Mos.RAIL_LO); src_rail(mn, 'bot', [2], YLN - Mos.RAIL_HI)
        for k in (0, 2):
            x, yy = drain_pad(mp, k); port(y, x, yy)
        x, yy = drain_pad(mn, 0); port(y, x, yy)
        port(a, *shared_gate(mn, mp, 0, YLV_GATE, x0 - STUB))
        port(b, *shared_gate(mn, mp, 1, YLV_GATE, mp.x1 + STUB))
        return mp.x1

    def lv_ppair(x0, y, yb):
        """lvldn cross-coupled LV PMOS: MP1 (y, gate yb), MP2 (yb, gate y); strips y | vdd | yb."""
        mp = Mos(D, 'pmos', 2, 0.13, 2, x0, YLP)
        LV_P.append(mp)
        src_rail(mp, 'top', [1], YLP + 2.0 + Mos.RAIL_LO)
        x, yy = drain_pad(mp, 0); port(y, x, yy)
        x, yy = drain_pad(mp, 2); port(yb, x, yy)
        port(yb, *gate_stub(mp, 0, 'bot', x0 - STUB))
        port(y, *gate_stub(mp, 1, 'bot', mp.x1 + STUB))
        return mp.x1

    # note: shared_gate(mn, mp, ...) for the 1.2 V row: the PMOS is above the NMOS -> pass (mn, mp)
    # so that the poly bridge runs from mn.y1 to mp.y0 (argument names are generic)

    # ------------------------------------------------------------------ 3.3 V row cells --------
    HV_N, HV_P = [], []
    def hv_inv(x0, a, y, YHP, YHN, YHV_GATE):
        mp = Mos(D, 'pmosHV', 3.9, 0.45, 1, x0, YHP); mn = Mos(D, 'nmosHV', 1.9, 0.45, 1, x0, YHN)
        HV_P.append(mp); HV_N.append(mn)
        src_rail(mp, 'bot', [0], YHP - Mos.RAIL_HI); src_rail(mn, 'top', [0], YHN + 2.0 + Mos.RAIL_LO)
        x, yy = drain_pad(mp, 1); port(y, x, yy)
        x, yy = drain_pad(mn, 1); port(y, x, yy)
        port(a, *shared_gate(mp, mn, 0, YHV_GATE, x0 - STUB))
        return mp.x1

    def hv_nor2(x0, a, b, y, YHP, YHN, YHV_GATE):
        mp = Mos(D, 'pmosHV', 15.6, 0.45, 2, x0, YHP); mn = Mos(D, 'nmosHV', 3.8, 0.45, 2, x0, YHN)
        HV_P.append(mp); HV_N.append(mn)
        src_rail(mp, 'bot', [0], YHP - Mos.RAIL_HI); src_rail(mn, 'top', [1], YHN + 2.0 + Mos.RAIL_LO)   # vdda | m | y ; y | vss | y
        x, yy = drain_pad(mp, 2); port(y, x, yy)
        for k in (0, 2):
            x, yy = drain_pad(mn, k); port(y, x, yy)
        port(a, *shared_gate(mp, mn, 0, YHV_GATE, x0 - STUB))
        port(b, *shared_gate(mp, mn, 1, YHV_GATE, mp.x1 + STUB))
        return mp.x1

    def hv_lvlup(x0, a, ab, nb, n, YHP, YHN):
        """pull-downs MN1 (nb, gate a) MN2 (n, gate ab) as one 2-finger nmosHV (nb | vss | n) at x0;
        cross-coupled pmosHV 0.3/0.45: MP1 (drain nb, gate n) west, MP2 (drain n, gate nb) east.
        Sources of the PMOS go down to the vdda rail, drains up into the middle region."""
        mn = Mos(D, 'nmosHV', 3.8, 0.45, 2, x0, YHN); HV_N.append(mn)
        src_rail(mn, 'top', [1], YHN + 2.0 + Mos.RAIL_LO)
        x, yy = drain_pad(mn, 0); port(nb, x, yy)
        x, yy = drain_pad(mn, 2); port(n, x, yy)
        port(a, *gate_stub(mn, 0, 'bot', x0 - 0.55))
        port(ab, *gate_stub(mn, 1, 'bot', mn.x1 + 0.55))
        def pmos(xp, dnet, gnet, xstub):
            mp = Mos(D, 'pmosHV', 0.3, 0.45, 1, xp, YHP); HV_P.append(mp)
            src_rail(mp, 'bot', [0], YHP - Mos.RAIL_HI)                # source -> vdda rail
            port(gnet, *gate_stub(mp, 0, 'bot', xstub))
            x = mp.sx(1); yt = mp.y1 + 0.75                            # drain up to a pad in the middle
            D.box('M1', x - 0.08, mp.y1, x + 0.08, yt)
            D.sq('M1', x, yt, 0.34); D.stack(x, yt, 'M1', 'M2')
            port(dnet, x, yt)
            return mp
        mp1 = pmos(x0 - 2.23, nb, n, x0 - 2.9)
        mp2 = pmos(x0 + 2.23, n, nb, x0 + 3.9)
        return (mp1.x0, mp2.x1 + 0.8)                                   # (x_min, x_max incl. stub)

    def hv_ndn(x0, a, ab, yb, y, YHN):
        """lvldn pull-downs MN1 (yb, gate a) MN2 (y, gate ab): 2-finger nmosHV 2/0.45 (yb | vss | y)."""
        mn = Mos(D, 'nmosHV', 4.0, 0.45, 2, x0, YHN); HV_N.append(mn)
        src_rail(mn, 'top', [1], YHN + 2.0 + Mos.RAIL_LO)
        x, yy = drain_pad(mn, 0); port(yb, x, yy)
        x, yy = drain_pad(mn, 2); port(y, x, yy)
        port(a, *gate_stub(mn, 0, 'bot', x0 - STUB))
        port(ab, *gate_stub(mn, 1, 'bot', mn.x1 + STUB))
        return mn.x1

    # ------------------------------------------------------------------ net list (r1_gate.spice) --
    CH = ['a', 'b', 'c']
    U = [('pwm_%s' % c, 'ab%d' % i, 'nb%d' % i, 'n%d' % i, 'p%s_h' % c) for i, c in enumerate(CH)] + \
        [('gate_en', 'ab3', 'nb3', 'n3', 'en_h')]
    DN = [('g%s_h' % c, 'g%s_hn' % c, 'yb%s' % c, 'gc_%s' % c) for c in CH]
    LV_OFF = {'nand2': [-STUB, 0.15, 1.17, 1.32 + STUB], 'inv': [-STUB, 0.66], 'ppair': [-STUB, 0.15, 1.17, 1.32 + STUB]}
    LV_W = {'nand2': 1.32, 'inv': 0.81, 'ppair': 1.32}

    def place_all(YHP, YHN, YHV_GATE):
        del ports[:]; del LV_N[:]; del LV_P[:]; del HV_N[:]; del HV_P[:]
        hv_anchor = {}
        hv_x1 = 0.0
        if HV:
            x = 6.0 + 3.05
            for i, (a, ab, nb, n, out) in enumerate(U):
                if i > 0:
                    x += 3.05
                xa, xb = hv_lvlup(x, a, ab, nb, n, YHP, YHN)
                hv_anchor['U%d' % i] = xa
                x = xb + GAP
                x = hv_inv(x, nb, out, YHP, YHN, YHV_GATE) + GAP
            x = hv_inv(x, 'en_h', 'en_hn', YHP, YHN, YHV_GATE) + GAP
            for c in CH:
                x = hv_inv(x, 'p%s_h' % c, 'p%s_hn' % c, YHP, YHN, YHV_GATE) + GAP
                x = hv_nor2(x, 'en_hn', 'p%s_hn' % c, 'g%s_h' % c, YHP, YHN, YHV_GATE) + GAP
                x = hv_inv(x, 'g%s_h' % c, 'g%s_hn' % c, YHP, YHN, YHV_GATE) + GAP
            for i, (a, ab, yb, out) in enumerate(DN):
                hv_anchor['D%d' % i] = x
                x = hv_ndn(x, a, ab, yb, out, YHN) + GAP
            hv_x1 = x - GAP
        hv_xs = sorted(px for net, px, py in ports)
        def free_x(xd, kind):
            xx = snap(xd)
            while True:
                if all(abs(xx + o - hx) >= 0.55 for o in LV_OFF[kind] for hx in hv_xs):
                    return xx
                xx = snap(xx + 0.05)
        # 1.2 V row
        x = free_x(6.0, 'nand2')
        if HV:
            for i, (a, ab, nb, n, out) in enumerate(U):
                x = free_x(max(x, hv_anchor['U%d' % i]), 'inv')
                x = lv_inv(x, a, ab, True) + GAP
            for i, (a, ab, yb, out) in enumerate(DN):
                x = free_x(max(x, hv_anchor['D%d' % i] - 1.0), 'ppair')
                x = lv_ppair(x, out, yb) + GAP
        else:
            for c in CH:
                x = free_x(x, 'nand2')
                x = lv_nand2(x, 'pwm_%s' % c, 'gate_en', 'n%s' % c) + GAP
                x = free_x(x, 'inv')
                x = lv_inv(x, 'n%s' % c, 'gc_%s' % c, True) + GAP
        lv_x1 = x - GAP
        return max(lv_x1, hv_x1), None

    INPUTS = ['pwm_a', 'pwm_b', 'pwm_c', 'gate_en']
    OUTPUTS = ['gc_a', 'gc_b', 'gc_c']

    def pack_tracks(ports, x_west, x_east):
        """greedy interval packing: returns {net: track index}; pin nets span to the edge."""
        nets = {}
        for net, x, y in ports:
            xs = nets.setdefault(net, [x, x])
            xs[0] = min(xs[0], x); xs[1] = max(xs[1], x)
        for net in INPUTS:
            nets[net][0] = x_west
        for net in OUTPUTS:
            nets[net][1] = x_east
        order = sorted(nets.items(), key=lambda kv: kv[1][0])
        tracks = []                                     # list of x_max per track
        assign = {}
        for net, (xa, xb) in order:
            for i, xe in enumerate(tracks):
                if xa > xe + 0.8:
                    tracks[i] = xb; assign[net] = i; break
            else:
                tracks.append(xb); assign[net] = len(tracks) - 1
        return assign, len(tracks)

    # pass 1: provisional geometry into a scratch cell to get the port x's
    scratch = ly.create_cell('scratch')
    D_real = D
    D = Draw(ly, scratch)
    XW, _ = place_all(100.0, 109.1, 108.48)
    X1, X2 = 0.0, XW + 6.0
    assign, NTRACK = pack_tracks(ports, X1, X2)
    ly.delete_cell(scratch.cell_index()); ly.cleanup()
    D = D_real
    # real y's
    YB1 = YB0 + (NTRACK - 1) * TPITCH                    # last track
    YHP = YB1 + 0.8 + 2.2                                # 3.3 V PMOS Activ bottom (n+ tie at -1.7, rail at -1.03)
    YHN = YHP + 7.8 + 1.3
    YHV_GATE = YHN - 0.62
    XW, _ = place_all(YHP, YHN, YHV_GATE)
    assign2, NTRACK2 = pack_tracks(ports, X1, X2)
    assert assign2 == assign and NTRACK2 == NTRACK
    def track_y(i):
        return YB0 + i * TPITCH

    # ------------------------------------------------------------------ verticals and tracks ----
    bynet = {}
    for net, x, y in ports:
        bynet.setdefault(net, []).append((x, y))
    # different-net ports must be >= 0.5 apart in x
    allx = sorted((x, net) for net, lst in bynet.items() for x, y in lst)
    for (xa, na), (xb, nb_) in zip(allx[:-1], allx[1:]):
        if na != nb_ and xb - xa < 0.50 - 1e-9:
            raise ValueError('ports too close: %s@%.3f %s@%.3f' % (na, xa, nb_, xb))
    for net, lst in bynet.items():
        yt = track_y(assign[net])
        xs = sorted(lst)
        # group ports closer than 0.6 in x into one vertical
        groups = []
        for x, y in xs:
            if groups and x - groups[-1][-1][0] < 0.6:
                groups[-1].append((x, y))
            else:
                groups.append([(x, y)])
        for g in groups:
            xa, xb = g[0][0], g[-1][0]
            ya = min(y for x, y in g); yb = max(y for x, y in g)
            lo, hi = min(ya, yt), max(yb, yt)
            D.box('M3', xa - VW / 2, lo - VW / 2, xb + VW / 2, hi + VW / 2)
            for x, y in g:
                D.sq('Via2', x, y, VIA)                  # port pad (Metal2, 0.40) -> Metal3
            xv = (xa + xb) / 2 if xb - xa < 0.2 else xa
            D.sq('M2', xv, yt, PAD); D.sq('Via2', xv, yt, VIA)
        xmin = min(x for x, y in lst); xmax = max(x for x, y in lst)
        if net in INPUTS:
            xmin = X1 + PINL - 0.5
        if net in OUTPUTS:
            xmax = X2 - PINL + 0.5
        D.hwire('M2', xmin, xmax, yt, EXTW)
    # pins
    for net in INPUTS + OUTPUTS:
        yt = track_y(assign[net])
        if net in INPUTS:
            xv, xa, xb = X1 + PINL - 0.5, X1, X1 + PINL
        else:
            xv, xa, xb = X2 - PINL + 0.5, X2 - PINL, X2
        D.sq('M2', xv, yt, PAD); D.sq('Via2', xv, yt, VIA)
        D.box('M3', xa, yt - PINW / 2, xb, yt + PINW / 2); D.box('M3pin', xa, yt - PINW / 2, xb, yt + PINW / 2)
        D.label('M3txt', (xa + xb) / 2, yt, net)

    # ------------------------------------------------------------------ rails, ties, wells ------
    xl = min(m.x0 for m in LV_N + LV_P + HV_N + HV_P) - 1.0
    xr = max(m.x1 for m in LV_N + LV_P + HV_N + HV_P) + 1.0
    # 1.2 V NMOS: vss rail (bottom) + p+ tie
    yr = YLN - Mos.RAIL_HI; D.box('M1', xl, yr, xr, YLN - Mos.RAIL_LO)
    D.tap_strip(xl, xr, YLN - 1.7, ptype=True)
    for xq in (xl + 1.0, (xl + xr) / 2, xr - 1.0):
        D.box('M1', xq - 0.15, YLN - 1.83, xq + 0.15, YLN - Mos.RAIL_LO)
    # 1.2 V PMOS: vdd rail (top of the 2 um envelope) + n+ tie + NWell / pSD cover
    ylp1 = YLP + 2.0
    D.box('M1', xl, ylp1 + Mos.RAIL_LO, xr, ylp1 + Mos.RAIL_HI)
    D.tap_strip(xl, xr, ylp1 + 1.7, ptype=False)
    for xq in (xl + 1.0, (xl + xr) / 2, xr - 1.0):
        D.box('M1', xq - 0.15, ylp1 + Mos.RAIL_HI, xq + 0.15, ylp1 + 1.83)
    D.box('NWell', xl - 0.5, YLP - 0.31, xr + 0.5, ylp1 + 2.3)
    D.box('pSD', xl - 0.18, YLP - 0.30, xr + 0.18, ylp1 + 0.30)
    if HV:
        # 3.3 V PMOS: vdda rail (bottom) + n+ tie + NWell / pSD; ThickGateOx over both 3.3 V rows
        D.box('M1', xl, YHP - Mos.RAIL_HI, xr, YHP - Mos.RAIL_LO)
        D.tap_strip(xl, xr, YHP - 1.7, ptype=False)
        for xq in (xl + 1.0, (xl + xr) / 2, xr - 1.0):
            D.box('M1', xq - 0.15, YHP - 1.83, xq + 0.15, YHP - Mos.RAIL_LO)
        yhp1 = YHP + 7.8
        D.box('NWell', xl - 0.5, YHP - 2.3, xr + 0.5, yhp1 + 0.62)
        D.box('pSD', xl - 0.18, YHP - 0.40, xr + 0.18, yhp1 + 0.40)
        yhn1 = YHN + 2.0
        D.box('TGO', xl - 0.3, YHP - 0.62, xr + 0.3, yhn1 + 0.52)
        # 3.3 V NMOS: vss rail (top) + p+ tie
        D.box('M1', xl, yhn1 + Mos.RAIL_LO, xr, yhn1 + Mos.RAIL_HI)
        D.tap_strip(xl, xr, yhn1 + 1.7, ptype=True)
        for xq in (xl + 1.0, (xl + xr) / 2, xr - 1.0):
            D.box('M1', xq - 0.15, yhn1 + Mos.RAIL_HI, xq + 0.15, yhn1 + 1.83)

    # ------------------------------------------------------------------ power ------------------
    if HV:
        Y2 = yhn1 + 1.7 + 0.15 + 1.5 + BARW + 1.5
    else:
        Y2 = YB1 + 0.8 + 2.0 + BARW + 1.5 + 1.5           # variant lv: the vdda bar is a bare pin, above the track band
    YVDDA = Y2 - 1.5 - BARW / 2
    D.box('M3', X1, YVSS - BARW / 2, X2, YVSS + BARW / 2); D.box('M3pin', X1, YVSS - BARW / 2, X2, YVSS + BARW / 2)
    D.box('M3', X1, YVDDA - BARW / 2, X2, YVDDA + BARW / 2); D.box('M3pin', X1, YVDDA - BARW / 2, X2, YVDDA + BARW / 2)
    D.label('M3txt', X2 / 2, YVSS, 'vss'); D.label('M3txt', X2 / 2, YVDDA, 'vdda')
    # 1.2 V vss rail -> south bar (stacks + Metal3 verticals)
    for xq in (xl + 0.5, (xl + xr) / 2 + 0.3, xr - 0.5):
        D.stack(xq, YLN - 1.03, 'M1', 'M3'); D.vwire('M3', xq, YVSS, YLN - 1.03, VW)
    if HV:
        # 3.3 V vss rail (north) -> south bar and vdda rail -> north bar: Metal3 verticals east of the cells
        xv1, xv2 = xr + 1.5, xr + 3.0
        D.box('M1', xr, yhn1 + Mos.RAIL_LO, xv1 + 0.3, yhn1 + Mos.RAIL_HI)
        D.stack(xv1, yhn1 + 1.03, 'M1', 'M3'); D.vwire('M3', xv1, YVSS, yhn1 + 1.03, 0.6)
        D.box('M1', xr, YHP - Mos.RAIL_HI, xv2 + 0.3, YHP - Mos.RAIL_LO)
        D.stack(xv2, YHP - 1.03, 'M1', 'M3'); D.vwire('M3', xv2, YHP - 1.03, YVDDA, 0.6)
    # vdd: 1.2 V PMOS rail -> west pin
    D.box('M1', X1 + PINL - 0.5, ylp1 + Mos.RAIL_LO, xl, ylp1 + Mos.RAIL_HI)
    D.stack(X1 + PINL - 0.5, ylp1 + 1.03, 'M1', 'M3')
    D.box('M3', X1, ylp1 + 1.03 - PINW / 2, X1 + PINL, ylp1 + 1.03 + PINW / 2)
    D.box('M3pin', X1, ylp1 + 1.03 - PINW / 2, X1 + PINL, ylp1 + 1.03 + PINW / 2)
    D.label('M3txt', X1 + PINL / 2, ylp1 + 1.03, 'vdd')
    # p+ guard ring (vss) inside the boundary, tied to the south bar
    Y1 = 0.0
    mr = D.tap_ring(X1 + 0.6, Y1 + 0.6, X2 - 0.6, Y2 - 0.6, 0.30, ptype=True)
    for xq in (X1 + 3.0, X2 - 3.0):
        D.sq('M1', xq, mr[1], 0.34); D.stack(xq, mr[1], 'M1', 'M3')
    D.boundary(X1, Y1, X2, Y2)
    return top, {'bbox': (X1, Y1, X2, Y2), 'ntrack': NTRACK, 'yvss': YVSS, 'yvdda': YVDDA}


if __name__ == '__main__':
    variant = globals().get('variant', 'hv')
    ly = pya.Layout(); ly.dbu = 0.001
    top, info = build_gate(ly, variant)
    name = 'r1_gate_' + variant
    write_gds(ly, os.path.join(HERE, name + '.gds'))
    x1, y1, x2, y2 = info['bbox']
    print('%s boundary %.2f x %.2f um, %d tracks' % (name, x2 - x1, y2 - y1, info['ntrack']), info['bbox'])
    pins = []
    lp = ly.layer(*LAYERS['M3pin']); lt = ly.layer(*LAYERS['M3txt'])
    texts = [(s.text_string, s.text_dtrans.disp) for s in top.shapes(lt).each() if s.is_text()]
    for s in top.shapes(lp).each():
        b = s.dbbox()
        for nm, p in texts:
            if b.contains(pya.DPoint(p.x, p.y)):
                use = 'POWER' if nm in ('vdd', 'vdda') else ('GROUND' if nm == 'vss' else 'SIGNAL')
                pins.append((nm, use, 'Metal3', b.left, b.bottom, b.right, b.top))
    yb1, yb2 = info['yvss'] + BARW / 2 + 0.5, info['yvdda'] - BARW / 2 - 0.5
    obs = [(ln, (x1, y1, x2, y2)) for ln in ('Metal1', 'Metal2')]
    obs += [(ln, (x1 + 2.5, yb1, x2 - 2.5, yb2)) for ln in ('Metal3',)]
    write_lef(os.path.join(HERE, name + '.lef'), name, info['bbox'], pins, obs)
