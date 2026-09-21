#!/usr/bin/env python3
"""G1_SENSE macro `g1_sense` (schematic ../schematic/g1_sense.sch, LVS netlist g1_sense.cdl).

Floorplan (origin = south-west corner of the macro boundary):
  west   three `g1_ota` cells stacked (XOTA bottom, XBUF middle, XREF top), all OTA pins on their
         east edges facing the routing channel; their Metal3 vdd/vss trunks are joined between
         the cells and end on the north (vdd) / south (vss) Metal3 power bars
  middle routing channel: Metal3 verticals (one per net), the bias diode MBI at its south end
  east   resistor array: 95 units of rppd 2 x 76.7 um, one PCell per schematic unit (so the LVS
         compares 1:1 with --no_series_res: the deck's series combiner would otherwise merge through
         the OTA-input nodes and hide their connections), 2.5 um column pitch, two meander rows of
         52 columns (poly dummy columns at both ends, merged pSD/SalBlock/EXTBlock covers per row):
           row 0 (south): [d d][RD2 a 13][R2N a 10][R1N][R1P][R2P a 10][RD2 b 13][d d]
           row 1 (north): [d d][RD2 c 13][R2P b 10][RD1 2][R2N b 10][RD2 d 12][d][d d]
         R2N and R2P each have one half west and one east of the centre, one in each row (2-D
         common centroid at chain level); R1N/R1P are the adjacent centre columns of row 0 and
         their SENSE_N/SENSE_P heads leave symmetrically on the south side. Chain ends are heads;
         Metal3 drops take them to Metal2 tracks in the gaps (south of row 0, between the rows,
         north of row 1) and on to the channel or the east edge.
  pins   Metal3: sense_p, sense_n on the east edge; vref, iptat, isense, vped, vref_buf on the west
         edge (Metal2 tracks in the gaps between the OTA cells); vdd bar on the north edge and vss bar
         on the south edge (Metal3, full width). p+ guard ring (vss) around the macro; the array has
         its own p+ ring. No-fill regions (NoFillerStack PCell + NoMetFiller) over the resistor array
         and, inside the OTA cell, over the input pair and the capacitor; boundary on 189/4 only
         (189/0 is the chip outline for the chip-level density deck and must not appear in a macro).
         The PDK filler is run on the finished GDS by layout/fill.sh (see there).
Run (container):  G1_WORKDIR=designs/g1-guardian/blocks/g1_sense/layout flow/run.sh klayout -b -r g1_sense_layout.py
writes layout/g1_sense.gds, layout/g1_sense.lef and build/g1_sense_lay/g1_sense.gds (top cell g1_sense).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from g1_layout_lib import *  # noqa
from g1_ota_layout import build_ota, EXTW, VERTW

RW, RL = 2.0, 76.7             # unit resistor body (w, l): one PCell per schematic unit (LVS 1:1, no series merge)
RPITCH = 2.5                   # column pitch
NCOL = 52                      # columns per row (incl. 2 dummies at each end)
HEAD = 0.43                    # head extension beyond the body (GatPoly/Metal1)
ROWGAP = 6.0                   # gap between the pSD covers of the two rows (Metal2 tracks)
TRACK = 0.6                    # Metal2 track pitch in the gaps
PINW, PINL = 1.0, 2.0          # macro pin width (Metal3) and depth into the macro
BARW = 3.0                     # vdd/vss Metal3 bars (north/south)


def build_sense(ly):
    top = ly.create_cell('g1_sense')
    D = Draw(ly, top)
    ota_cell, oi = build_ota(ly)
    ox1, oy1, ox2, oy2 = oi['bbox']                    # OTA boundary in its own coordinates
    OW, OH = ox2 - ox1, oy2 - oy1
    OGAP = 4.0

    # ------------------------------------------------------------------ placement ---------------
    # macro interior: x from 0; OTAs at x = OX (their boundary west edge), channel, array
    RING = 3.0                                          # margin from the boundary to the OTA cells
    OX = RING
    OY0 = RING + BARW + 3.0                             # bottom OTA's boundary south edge
    oy = [OY0 + k * (OH + OGAP) for k in range(3)]      # XOTA, XBUF, XREF
    for k in range(3):
        D.inst(ota_cell, OX - ox1, oy[k] - oy1)
    def opin(k, name):
        layer, px, py = oi['pins'][name]
        return (px - ox1 + OX, py - oy1 + oy[k])
    OTA_E = OX + OW                                     # east edge of the OTA cells
    CH_X0 = OTA_E + 0.5                                 # channel
    CH = {'vbn': 0.9, 'vn': 1.9, 'isense': 2.9, 'vp': 3.9, 'x2n': 4.9, 'x2p': 5.9, 'vped': 6.9,
          'vped_ref': 7.9, 'vref_buf': 8.9, 'vref': 9.9, 'vss': 10.9}
    CHX = {k: CH_X0 + v for k, v in CH.items()}
    AX0 = CH_X0 + 12.5                                  # array: first column's body x
    AY0 = OY0 + 4.0                                     # row 0 body y (gap-0 tracks below it)
    ROWPITCH = RL + 2 * 0.61 + ROWGAP
    def colx(c):
        return AX0 + c * RPITCH
    def rowy(r):
        return AY0 + r * ROWPITCH

    # ------------------------------------------------------------------ resistor array ---------
    def unit(c, r):
        D.pcell('rppd', {'Calculate': 'R', 'w': '%gu' % RW, 'l': '%gu' % RL, 'b': 0}, colx(c), rowy(r))
    def dummy(c, r):
        D.box('GatPoly', colx(c), rowy(r) + 0.25, colx(c) + RW, rowy(r) + RL - 0.25)   # inside SalBlock (Sal.c 0.2)
    def strap(c, r, side):   # join the heads of columns c and c+1 on `side`
        if side == 'top':
            y = rowy(r) + RL
            D.box('M1', colx(c) + 0.02, y + 0.13, colx(c + 1) + RW - 0.02, y + HEAD)
        else:
            y = rowy(r)
            D.box('M1', colx(c) + 0.02, y - HEAD, colx(c + 1) + RW - 0.02, y - 0.13)
    def chain(r, c0, n):
        """meander of n units from column c0 (straps alternate bot/top starting at the bottom).
        Returns ((c_first, side), (c_last, side)) of the two free heads."""
        for u in range(n):
            unit(c0 + u, r)
            if u > 0:
                strap(c0 + u - 1, r, 'bot' if (u - 1) % 2 == 0 else 'top')
        first = (c0, 'top')
        last = (c0 + n - 1, 'top' if n % 2 == 0 else 'bot')
        return (first, last)
    def covers(r, c_first, c_last):
        x1, x2 = colx(c_first), colx(c_last) + RW
        y1, y2 = rowy(r), rowy(r) + RL
        D.box('pSD', x1 - 0.18, y1 - 0.61, x2 + 0.18, y2 + 0.61)
        D.box('EXTBlock', x1 - 0.18, y1 - 0.61, x2 + 0.18, y2 + 0.61)
        D.box('SalBlock', x1 - 0.20, y1, x2 + 0.20, y2)
    # row 0 (south): [d d][RD2 a 13][R2N a 10][R1N][R1P][R2P a 10][RD2 b 13][d d]
    for c in (0, 1, 50, 51): dummy(c, 0)
    RD2a = chain(0, 2, 13); R2Na = chain(0, 15, 10); R1N = chain(0, 25, 1); R1P = chain(0, 26, 1)
    R2Pa = chain(0, 27, 10); RD2b = chain(0, 37, 13)
    # row 1 (north): [d d][RD2 c 13][R2P b 10][RD1 2][R2N b 10][RD2 d 12][d][d d]
    for c in (0, 1, 49, 50, 51): dummy(c, 1)
    RD2c = chain(1, 2, 13); R2Pb = chain(1, 15, 10); RD1 = chain(1, 25, 2); R2Nb = chain(1, 27, 10); RD2d = chain(1, 37, 12)
    for r in range(2):
        covers(r, 0, NCOL - 1)
    AX1 = colx(NCOL - 1) + RW                            # array east edge (bodies)
    AY1 = rowy(1) + RL

    # ------------------------------------------------------------------ gap tracks ----------------
    # gap g: 0 below row 0, 1 between the rows, 2 above row 1; track i counts away from row 0
    def gap_track(g, i):
        if g == 0:
            return rowy(0) - HEAD - 0.5 - i * TRACK
        if g == 1:
            return rowy(0) + RL + HEAD + 0.5 + i * TRACK
        return rowy(1) + RL + HEAD + 0.5 + i * TRACK
    def to_track(c, r, side, g, i):
        """head (top/bottom) of column c, row r -> Metal3 drop to track i of gap g; returns (x, y_track)."""
        x = colx(c) + RW / 2
        y = rowy(r) + RL + 0.28 if side == 'top' else rowy(r) - 0.28
        D.stack(x, y, 'M1', 'M3')
        yt = gap_track(g, i)
        D.vwire('M3', x, y, yt, EXTW)
        D.sq('M3', x, yt, PAD); D.sq('Via2', x, yt, VIA); D.sq('M2', x, yt, PAD)
        return (x, yt)
    def to_channel(net, x, y):
        """Metal2 horizontal from (x, y) west to the channel vertical of `net`, Via2 there."""
        xc = CHX[net]
        D.hwire('M2', xc, x, y, EXTW)
        D.sq('M2', xc, y, PAD); D.sq('Via2', xc, y, VIA); D.sq('M3', xc, y, PAD)
        return (xc, y)
    chan_y = {k: [] for k in CH}
    def reg(net, y):
        chan_y[net].append(y)
    def link(a, b):
        """two heads in the same gap joined by one track: a, b = (col, row, side, gap, track)"""
        x1, yt = to_track(*a); x2, _ = to_track(*b)
        D.hwire('M2', x1, x2, yt, EXTW)
        return (min(x1, x2), yt)
    # gap 0: sense_n (R1N bottom), sense_p (R1P bottom) east; RD2 a/b link
    xn, ytn = to_track(25, 0, 'bot', 0, 0); xp, ytp = to_track(26, 0, 'bot', 0, 1)
    link((14, 0, 'bot', 0, 2), (49, 0, 'bot', 0, 2))
    # gap 1: vn = R1N top + R2N a first; vp = R1P top + R2P a first; x2n = R2N a last; x2p = R2P a last;
    #        vped_ref = RD2 a first; RD2 b last (top) <-> RD2 c last (row 1 bottom)
    x, yt = link((25, 0, 'top', 1, 0), (15, 0, 'top', 1, 0)); reg('vn', to_channel('vn', x, yt)[1])
    x, yt = link((26, 0, 'top', 1, 1), (27, 0, 'top', 1, 1)); reg('vp', to_channel('vp', x, yt)[1])
    x, yt = to_track(24, 0, 'top', 1, 2); reg('x2n', to_channel('x2n', x, yt)[1])
    x, yt = to_track(36, 0, 'top', 1, 3); reg('x2p', to_channel('x2p', x, yt)[1])
    x, yt = to_track(2, 0, 'top', 1, 4); reg('vped_ref', to_channel('vped_ref', x, yt)[1])
    link((37, 0, 'top', 1, 5), (14, 1, 'bot', 1, 5))
    # gap 2: x2n = R2N b first; isense = R2N b last; x2p = R2P b first; vped = R2P b last;
    #        vref_buf = RD1 first; vped_ref = RD1 last; RD2 c first <-> RD2 d first; vss = RD2 d last
    x, yt = to_track(27, 1, 'top', 2, 0); reg('x2n', to_channel('x2n', x, yt)[1])
    x, yt = to_track(36, 1, 'top', 2, 1); reg('isense', to_channel('isense', x, yt)[1])
    x, yt = to_track(15, 1, 'top', 2, 2); reg('x2p', to_channel('x2p', x, yt)[1])
    x, yt = to_track(24, 1, 'top', 2, 3); reg('vped', to_channel('vped', x, yt)[1])
    x, yt = to_track(25, 1, 'top', 2, 4); reg('vref_buf', to_channel('vref_buf', x, yt)[1])
    x, yt = to_track(26, 1, 'top', 2, 5); reg('vped_ref', to_channel('vped_ref', x, yt)[1])
    link((2, 1, 'top', 2, 6), (37, 1, 'top', 2, 6))
    x, yt = to_track(48, 1, 'top', 2, 7); reg('vss', to_channel('vss', x, yt)[1])

    # ------------------------------------------------------------------ MBI (bias diode) -----------
    MBIX, MBIY = CH_X0 + 3.0, OY0 + 9.0                 # in the channel beside XOTA, clear of the gap-0 tracks
    MBI = Mos(D, 'nmosHV', 3.3, 1, 1, MBIX, MBIY)
    MBI.end_dummies()
    g = MBI.gate_bar('bot', m2=False)
    rMBI = MBI.rail('bot', [1], ext=(0.0, 0.0))
    D.box('M1', MBI.gx(0) - 0.15, MBI.yd('bot', Mos.GBAR_LO), MBI.gx(0) + 0.15, MBI.yd('bot', Mos.RAIL_HI))
    D.box('M1', MBI.gx(0) - 0.15, MBI.yd('bot', Mos.RAIL_LO), MBI.sx(1) + 0.20, MBI.yd('bot', Mos.RAIL_HI))
    tMBI = MBI.rail('top', [0])
    D.box('TGO', MBI.x0 - 0.27, MBI.y0 - 0.52, MBI.x1 + 0.27, MBI.y1 + 0.52)
    # iptat = drain/gate rail -> channel vbn vertical; source rail -> vss vertical
    xi, yi = MBI.sx(1), MBI.yd('bot', (Mos.RAIL_LO + Mos.RAIL_HI) / 2)
    D.stack(xi, yi, 'M1', 'M2'); reg('vbn', to_channel('vbn', xi, yi)[1])
    xs, ys = MBI.sx(0), MBI.yd('top', (Mos.RAIL_LO + Mos.RAIL_HI) / 2)
    D.stack(xs, ys, 'M1', 'M2'); D.hwire('M2', xs, CHX['vss'], ys, EXTW)
    D.sq('M2', CHX['vss'], ys, PAD); D.sq('Via2', CHX['vss'], ys, VIA); D.sq('M3', CHX['vss'], ys, PAD); reg('vss', ys)

    # ------------------------------------------------------------------ OTA pins -> channel ---------
    def ota_to_channel(k, pin, net):
        x, y = opin(k, pin)                                # pin centre 0.5 inside the OTA east edge
        xc = CHX[net]
        D.hwire('M2', x, xc, y, EXTW)
        D.sq('M2', xc, y, PAD); D.sq('Via2', xc, y, VIA); D.sq('M3', xc, y, PAD)
        reg(net, y)
    ota_to_channel(0, 'inn', 'vn'); ota_to_channel(0, 'inp', 'vp'); ota_to_channel(0, 'out', 'isense'); ota_to_channel(0, 'vbn', 'vbn')
    ota_to_channel(1, 'inn', 'vped'); ota_to_channel(1, 'inp', 'vped_ref'); ota_to_channel(1, 'out', 'vped'); ota_to_channel(1, 'vbn', 'vbn')
    ota_to_channel(2, 'inn', 'vref_buf'); ota_to_channel(2, 'inp', 'vref'); ota_to_channel(2, 'out', 'vref_buf'); ota_to_channel(2, 'vbn', 'vbn')

    # ------------------------------------------------------------------ macro extent ----------------
    X1, Y1 = 0.0, 0.0
    X2 = AX1 + 6.0 + RING
    Y2 = max(oy[2] + OH, gap_track(2, 7) + 1.5) + 3.0 + BARW + RING

    # ------------------------------------------------------------------ west pins via OTA gaps ------
    # tracks: south of XOTA (iptat), gap XOTA/XBUF (isense), gap XBUF/XREF (vped, vref_buf), north of XREF (vref)
    WPINS = {}
    def west_pin(net, y, label=None):
        label = net if label is None else label
        xc = CHX[net]
        D.sq('M2', xc, y, PAD); D.sq('Via2', xc, y, VIA); D.sq('M3', xc, y, PAD)
        D.hwire('M2', X1 + PINL - 0.5, xc, y, EXTW)
        D.sq('M2', X1 + PINL - 0.5, y, PAD); D.sq('Via2', X1 + PINL - 0.5, y, VIA)
        D.box('M3', X1, y - PINW / 2, X1 + PINL, y + PINW / 2)
        D.box('M3pin', X1, y - PINW / 2, X1 + PINL, y + PINW / 2)
        D.label('M3txt', X1 + PINL / 2, y, label)
        reg(net, y)
        WPINS[label] = y
    west_pin('vbn', OY0 - 1.5, 'iptat')                  # iptat (the channel net vbn is the MBI diode = iptat)
    west_pin('isense', oy[0] + OH + OGAP / 2)
    west_pin('vped', oy[1] + OH + OGAP / 2 - 1.0)
    west_pin('vref_buf', oy[1] + OH + OGAP / 2 + 1.0)
    west_pin('vref', oy[2] + OH + 1.5)

    # ------------------------------------------------------------------ east pins (sense_p/n) -------
    def east_pin(net, x, y, xr, ypin):
        """track wire (x, y) east to a Metal3 riser at xr, up to ypin, Metal3 pin on the east edge."""
        D.hwire('M2', x, xr, y, EXTW)
        D.sq('M2', xr, y, PAD); D.sq('Via2', xr, y, VIA); D.sq('M3', xr, y, PAD)
        D.vwire('M3', xr, y, ypin, VERTW)
        D.box('M3', xr - VERTW / 2, ypin - PINW / 2, X2, ypin + PINW / 2)
        D.box('M3pin', X2 - PINL, ypin - PINW / 2, X2, ypin + PINW / 2)
        D.label('M3txt', X2 - PINL / 2, ypin, net)
    east_pin('sense_n', xn, ytn, AX1 + 4.2, AY0 + 6.0); east_pin('sense_p', xp, ytp, AX1 + 3.0, AY0 + 12.0)

    # ------------------------------------------------------------------ power ----------------------
    YVSS = Y1 + RING + BARW / 2                          # south bar centre
    YVDD = Y2 - RING - BARW / 2                          # north bar centre
    D.box('M3', X1, YVSS - BARW / 2, X2, YVSS + BARW / 2); D.box('M3pin', X1, YVSS - BARW / 2, X2, YVSS + BARW / 2)
    D.box('M3', X1, YVDD - BARW / 2, X2, YVDD + BARW / 2); D.box('M3pin', X1, YVDD - BARW / 2, X2, YVDD + BARW / 2)
    D.label('M3txt', X2 / 2, YVSS, 'vss'); D.label('M3txt', X2 / 2, YVDD, 'vdd')
    # OTA trunks: join between the cells; vss trunks to the south bar, vdd trunks to the north bar
    _, xvl, xvr = oi['pins']['vdd']; _, xsl, xsr = oi['pins']['vss']
    for xt in (xvl, xvr):
        x = xt - ox1 + OX
        D.box('M3', x - 0.6, oy[0], x + 0.6, YVDD)              # bottom cell south edge .. north bar
    for xt in (xsl, xsr):
        x = xt - ox1 + OX
        D.box('M3', x - 0.6, YVSS, x + 0.6, oy[2] + OH)
    reg('vss', YVSS)
    # array p+ ring (vss) around the four rows, tied to the vss channel vertical and the south bar
    ar = D.tap_ring(AX0 - 1.2, gap_track(0, 2) - 1.0, AX1 + 1.2, gap_track(2, 7) + 1.0, 0.30, ptype=True)
    xr = ar[0]                                            # ring west side centre line
    for yq in (rowy(0) + RL / 2, rowy(1) + RL / 2):          # mid-row heights: no gap tracks there
        D.sq('M1', xr, yq, 0.34); D.stack(xr, yq, 'M1', 'M2'); D.hwire('M2', CHX['vss'], xr, yq, EXTW)
        D.sq('M2', CHX['vss'], yq, PAD); D.sq('Via2', CHX['vss'], yq, VIA); D.sq('M3', CHX['vss'], yq, PAD)
        reg('vss', yq)
    # macro p+ ring (vss) just inside the boundary, tied to the south bar at both ends
    mr = D.tap_ring(X1 + 1.0, Y1 + 1.0, X2 - 1.0, Y2 - 1.0, 0.30, ptype=True)
    for xq in (X1 + 8.0, X2 - 8.0):
        D.sq('M1', xq, mr[1], 0.34); D.stack(xq, mr[1], 'M1', 'M3')
    # channel verticals (all y's registered above)
    for net, ys in chan_y.items():
        if len(ys) >= 2:
            D.vwire('M3', CHX[net], min(ys), max(ys), VERTW)
    # no fill over the resistor array (both rows, 3 um margin; the OTA cell carries its own)
    D.nofill(colx(0) - 3.0, rowy(0) - 3.0, colx(NCOL - 1) + RW + 3.0, rowy(1) + RL + 3.0)
    D.boundary(X1, Y1, X2, Y2)
    info = {'bbox': (X1, Y1, X2, Y2), 'pins_w': WPINS, 'yvss': YVSS, 'yvdd': YVDD}
    return top, info


def write_lef(path, name, bbox, pins, obs_layers):
    """Minimal LEF: MACRO with CLASS BLOCK, pins as given [(name, use, layer, x1, y1, x2, y2)],
    OBS = the whole macro on the listed layers."""
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


if __name__ == '__main__':
    ly = pya.Layout(); ly.dbu = 0.001
    top, info = build_sense(ly)
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, '..', '..', '..', '..', '..', 'build', 'g1_sense_lay')
    write_gds(ly, os.path.join(out, 'g1_sense.gds'))
    write_gds(ly, os.path.join(here, 'g1_sense.gds'))
    x1, y1, x2, y2 = info['bbox']
    print('g1_sense boundary %.2f x %.2f um' % (x2 - x1, y2 - y1), info['bbox'])
    # LEF from the pin shapes on the M3pin layer
    pins = []
    lp = ly.layer(*LAYERS['M3pin']); lt = ly.layer(*LAYERS['M3txt'])
    texts = [(s.text_string, s.text_dtrans.disp) for s in top.shapes(lt).each() if s.is_text()]
    for s in top.shapes(lp).each():
        b = s.dbbox()
        for nm, p in texts:
            if b.contains(pya.DPoint(p.x, p.y)):
                use = 'POWER' if nm == 'vdd' else ('GROUND' if nm == 'vss' else 'SIGNAL')
                pins.append((nm, use, 'Metal3', b.left, b.bottom, b.right, b.top))
    OBS_IN = 2.5                                          # keep the router off the interior only
    yb1, yb2 = info['yvss'] + BARW / 2 + 0.5, info['yvdd'] - BARW / 2 - 0.5
    obs = [(ln, (x1, y1, x2, y2)) for ln in ('Metal1', 'Metal2')]
    obs += [(ln, (x1 + OBS_IN, yb1, x2 - OBS_IN, yb2)) for ln in ('Metal3', 'Metal4', 'Metal5')]
    # TopMetal1: only the capacitor plates (their bboxes)
    ltm = ly.layer(*LAYERS['TM1'])
    r = pya.Region(top.begin_shapes_rec(ltm)); r.merge()
    for p in r.each():
        b = p.bbox().to_dtype(0.001)
        obs.append(('TopMetal1', (b.left - 1.0, b.bottom - 1.0, b.right + 1.0, b.top + 1.0)))
    write_lef(os.path.join(here, 'g1_sense.lef'), 'g1_sense', info['bbox'], pins, obs)
