#!/usr/bin/env python3
"""G1_SENSE OTA cell `g1_ota` (schematic ../schematic/g1_ota.sch, netlist ../sim/netlist/g1_ota.spice,
LVS netlist g1_ota.cdl). Regenerated layout: the source OTA (TO_Nov2024/BG) came as schematics only.

All signal pins (inn, inp, vbn, out) are Metal2 stubs on the east edge.
Four device rows, bottom to top, all fingers 8 um (input pair 6 um), gates L = 1 um (pair 2 um):
  N    MB4 | MB2 | MB6 | M3 | M13 | M16 | M4 | M21        nmosHV   bias diodes, NMOS sources/cascodes, stage-2 load
  P-A  M14 | M15 | M12 | M11                              pmosHV   PMOS current sources (outer) and cascodes (inner)
  P-B  M1/M2 interdigitated, 32 x 6 um, pairs ABBAABBAABBAABBA (1-D common centroid, poly dummies at both ends)
  P-C  MB7 | MB5 | MB3 | MT | M20                         pmosHV   bias mirrors, tail source, stage-2 PMOS
Mirror-symmetric pairs (M3/M4, M13/M16, M14/M11, M15/M12) sit symmetrically about the row centre with
identical neighbours; every device row has poly dummies in the gaps and at the ends.

Metal use: Metal1 = device source/drain rails (0.78..1.28 um outside the Activ) and gate pads;
Metal2 = gate rails (0.14..0.52) and horizontal exit wires at fixed levels; Metal3 = vertical nets in
the two side channels (left: fn, mir, vbp, vbpc, vbnc; right: fp, out1, out) and the tail bus;
Metal4 = vdd/vss bars over the row power rails; Metal3 trunks 1.2 um on both sides carry vdd/vss.
Miller capacitor: cmim 23 x 23 um (Metal5 bottom plate = out, TopMetal1 top plate = cz) over rows
P-A/P-B; nulling resistor RZ (rppd 1 x 6.2 um) in the right channel over the substrate.
Guard: n+ ring inside the NWell around the three PMOS rows plus n+ strips between them (LU.a);
p+ substrate ring around the cell (LU.b, both 20 um). Nets are labelled on the metal text layers.
No-fill (NoFillerStack + NoMetFiller) over the input pair row and the capacitor; boundary on 189/4 only (189/0 is the chip outline for the density deck).

Run (container):  G1_WORKDIR=designs/g1-guardian/blocks/g1_sense/layout flow/run.sh klayout -b -r g1_ota_layout.py
writes build/g1_sense_lay/g1_ota.gds (top cell g1_ota) for the stand-alone DRC/LVS.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from g1_layout_lib import *  # noqa

EXTW = 0.30                    # Metal2 exit wire width
VERTW = 0.40                   # Metal3 vertical width
TRUNKW = 1.2                   # Metal3 power trunk width
BARW = 1.0                     # Metal4 power bar width
RAILC = (Mos.RAIL_LO + Mos.RAIL_HI) / 2      # 1.03: via position on a Metal1 rail
GATEC = (Mos.GRAIL_LO + Mos.GRAIL_HI) / 2    # 0.33: Metal2 gate rail centre


def build_ota(ly, name='g1_ota'):
    """Returns (cell, info). info['pins'] maps pin -> (layer, x, y) of the pin shape centre on the cell
    boundary; info['bbox'] = (x1, y1, x2, y2) of the cell boundary (prBoundary)."""
    cell = ly.create_cell(name)
    D = Draw(ly, cell)

    # ------------------------------------------------------------------ rows and x positions ---
    N_SPEC = [(1.6, 1, 1), (8, 1, 1), (8, 1, 1), (80, 1, 10), (48, 1, 6), (48, 1, 6), (80, 1, 10), (96, 1, 12)]
    PA_SPEC = [(96, 1, 12), (96, 1, 12), (96, 1, 12), (96, 1, 12)]
    PC_SPEC = [(3.2, 1, 1), (16, 1, 2), (16, 1, 2), (128, 1, 16), (192, 1, 24)]
    GAP = 1.40
    W = row_width(N_SPEC, GAP)                       # widest row sets the cell width
    def off(spec):
        return snap((W - row_width(spec, GAP)) / 2)
    Y = {'N': 0.0, 'PA': 13.6, 'PB': 25.0, 'PC': 34.8}
    n = row(D, 'nmosHV', N_SPEC, 0.0, Y['N'], GAP);      MB4, MB2, MB6, M3, M13, M16, M4, M21 = n
    pa = row(D, 'pmosHV', PA_SPEC, off(PA_SPEC), Y['PA'], GAP); M14, M15, M12, M11 = pa
    PAIRX = snap((W - (32 * 2.38 + 0.30)) / 2)
    PAIR = Mos(D, 'pmosHV', 192, 2, 32, PAIRX, Y['PB']); PAIR.end_dummies()
    pc = row(D, 'pmosHV', PC_SPEC, off(PC_SPEC), Y['PC'], GAP); MB7, MB5, MB3, MT, M20 = pc
    cover_row(D, n, 'nmosHV'); cover_row(D, pa, 'pmosHV'); cover_row(D, [PAIR], 'pmosHV'); cover_row(D, pc, 'pmosHV')

    # side channels: Metal3 verticals (x), trunks, rings
    XFN, XMIR, XVBP, XVBPC, XVBNC = -1.3, -2.2, -3.1, -4.0, -4.9
    XVSS_L, XVDD_L = -6.4, -8.2
    XFP, XOUT1, XOUT = W + 1.3, W + 2.2, W + 3.1
    XVSS_R, XVDD_R = W + 4.6, W + 6.4
    XRZ = W + 7.5                                   # RZ body x (1 um wide)
    NR_X1, NR_X2 = -2.3, W + 2.3                    # n+ ring inner box (Activ ring 0.3 outside)
    XL, XR = -9.9, W + 9.5                          # p+ ring inner box
    YB, YT = -4.2, Y['PC'] + 8 + 3.0
    BX1, BY1, BX2, BY2 = XL - 0.6, YB - 0.6, XR + 0.6, YT + 0.6   # cell boundary

    # ------------------------------------------------------------------ helpers -----------------
    def rail_via(m, side, k, hi='M2'):
        """Via on the Metal1 rail of device m (`side`) at strip k -> (x, y) of the Metal2 pad."""
        x, y = m.sx(k), m.yd(side, RAILC)
        D.stack(x, y, 'M1', hi)
        return (x, y)

    def exit_wire(m, side, k, level, xto):
        """Rail via at strip k, Metal2 vertical to `level` (d outside the Activ), Metal2 horizontal to xto.
        Returns (xto, y) of the wire end (a Via2 pad is placed there for the Metal3 vertical)."""
        x, y0 = rail_via(m, side, k)
        y = m.yd(side, level)
        if abs(y - y0) > 1e-9:
            D.vwire('M2', x, y0, y, EXTW)
        D.hwire('M2', x, xto, y, EXTW)
        D.sq('M2', xto, y, PAD); D.sq('Via2', xto, y, VIA); D.sq('M3', xto, y, PAD)
        return (xto, y)

    def gate_exit(rail, side_x, xto, y=None):
        """Extend a Metal2 gate rail (box tuple) horizontally to xto and drop a Via2 there."""
        yc = (rail[2] + rail[3]) / 2 if y is None else y
        xa = rail[0] if side_x < 0 else rail[1]
        D.hwire('M2', xa, xto, yc, rail[3] - rail[2])
        D.sq('M2', xto, yc, PAD); D.sq('Via2', xto, yc, VIA); D.sq('M3', xto, yc, PAD)
        return (xto, yc)

    def bridge_m1(ra, rb):
        D.box('M1', ra[1], ra[2], rb[0], ra[3])

    def bridge_m2(ga, gb):
        D.box('M2', ga[1], ga[2], gb[0], ga[3])

    def diode(m, k, side, strip=None):
        """Metal1 bridge from the gate pad of finger k to the rail on the same side (gate = drain);
        the rail is extended sideways to the gate x (strip = the drain strip, default k + 1)."""
        g = m.gx(k)
        strip = k + 1 if strip is None else strip
        D.box('M1', g - 0.15, m.yd(side, Mos.GBAR_LO), g + 0.15, m.yd(side, Mos.RAIL_HI))
        D.box('M1', g - 0.15, m.yd(side, Mos.RAIL_LO), m.sx(strip) + 0.20, m.yd(side, Mos.RAIL_HI))

    def strip_to_gate_rail(m, side, k):
        """Join strip k (which has a rail extension on `side`) to the Metal2 gate rail level."""
        ya, yb = m.yd(side, Mos.GRAIL_LO), m.yd(side, Mos.GRAIL_HI)
        m.strip_pad(k, side, GATEC, m2box=(min(ya, yb), max(ya, yb)))

    # ------------------------------------------------------------------ row N ------------------
    # gates: vbn on MB2 MB6 M3 M4 M21 (bottom bar); vbnc on M13 M16 (top bar); MB4 diode (vbnc)
    gMB4 = MB4.gate_bar('bot', m2=False); diode(MB4, 0, 'bot')
    gMB2 = MB2.gate_bar('bot'); gMB6 = MB6.gate_bar('bot'); gM3 = M3.gate_bar('bot')
    gM4 = M4.gate_bar('bot'); gM21 = M21.gate_bar('bot')
    gM13 = M13.gate_bar('top'); gM16 = M16.gate_bar('top')
    # vbn rail continuous from MB2 to M21 (passes under M13/M16 whose gates are on top)
    D.box('M2', gMB2[0], gMB2[2], gM21[1], gMB2[3])
    bridge_m2(gM13, gM16)
    # bottom rails (drains)
    rMB4 = MB4.rail('bot', [1]); rMB2 = MB2.rail('bot', [1]); rMB6 = MB6.rail('bot', [1])
    rM3 = M3.rail('bot', M3.strips(1)); rM13 = M13.rail('bot', M13.strips(0))
    rM16 = M16.rail('bot', M16.strips(0)); rM4 = M4.rail('bot', M4.strips(1)); rM21 = M21.rail('bot', M21.strips(1))
    bridge_m1(rM3, rM13); bridge_m1(rM16, rM4)                      # fn, fp
    # top rails: vss (MB4 strip 0 reaches up to the 8 um level), mir (M13), out1 (M16)
    tMB4 = MB4.rail('top', [0], lo=8 - 1.6 + Mos.RAIL_LO, hi=8 - 1.6 + Mos.RAIL_HI)
    tMB2 = MB2.rail('top', [0]); tMB6 = MB6.rail('top', [0]); tM3 = M3.rail('top', M3.strips(0))
    tM13 = M13.rail('top', M13.strips(1)); tM16 = M16.rail('top', M16.strips(1))
    tM4 = M4.rail('top', M4.strips(0)); tM21 = M21.rail('top', M21.strips(0))
    bridge_m1(tMB4, tMB2); bridge_m1(tMB2, tMB6); bridge_m1(tMB6, tM3); bridge_m1(tM4, tM21)
    # vss Metal4 bar over the top rails (1.0 wide from the rail bottom), stacks on the vss segments
    yv = Y['N'] + 8 + RAILC
    D.box('M4', XVSS_L - TRUNKW / 2, yv - 0.25, XVSS_R + TRUNKW / 2, yv + 0.75)
    for m, ks in ((M3, (0, 2, 4, 6, 8, 10)), (M4, (0, 2, 4, 6, 8, 10)), (M21, (0, 4, 8, 12)), (MB2, (0,)), (MB6, (0,))):
        for k in ks:
            D.stack(m.sx(k), yv, 'M1', 'M4')
    # exits, bottom (levels 1.7/2.3/2.9/3.5 leftwards: vbnc vbp vbpc fn; rightwards: out 1.7, fp 2.3)
    e_vbnc_n = exit_wire(MB4, 'bot', 1, 1.7, XVBNC)
    e_vbp_n = exit_wire(MB2, 'bot', 1, 2.3, XVBP)
    e_vbpc_n = exit_wire(MB6, 'bot', 1, 2.9, XVBPC)
    e_fn_n = exit_wire(M3, 'bot', 1, 3.5, XFN)
    e_out_n = exit_wire(M21, 'bot', 11, 1.7, XOUT)
    e_fp_n = exit_wire(M4, 'bot', 9, 2.3, XFP)
    # exits, top: mir (M13) left and out1 (M16) right at level 2.3; vbnc gate rail left; vbn pin left
    e_mir_n = exit_wire(M13, 'top', 1, 2.3, XMIR)
    e_out1_n = exit_wire(M16, 'top', 5, 2.3, XOUT1)
    e_vbnc_t = gate_exit(gM13, -1, XVBNC)
    yvbn = (gMB2[2] + gMB2[3]) / 2
    D.hwire('M2', gM21[1], BX2, yvbn, gMB2[3] - gMB2[2])                        # vbn rail -> east edge
    vbn_pin = ('M2', BX2 - 0.5, yvbn)

    # ------------------------------------------------------------------ row P-A ----------------
    gM14 = M14.gate_bar('bot'); gM11 = M11.gate_bar('bot')          # mir
    gM15 = M15.gate_bar('top'); gM12 = M12.gate_bar('top')          # vbpc
    D.box('M2', gM14[0], gM14[2], gM11[1], gM14[3]); bridge_m2(gM15, gM12)
    rM14 = M14.rail('bot', M14.strips(0)); rM15 = M15.rail('bot', M15.strips(1))   # vdd, mir
    rM12 = M12.rail('bot', M12.strips(1)); rM11 = M11.rail('bot', M11.strips(0))   # out1, vdd
    tM14 = M14.rail('top', M14.strips(1)); tM15 = M15.rail('top', M15.strips(0))   # pc1
    tM12 = M12.rail('top', M12.strips(0)); tM11 = M11.rail('top', M11.strips(1))   # pc2
    bridge_m1(tM14, tM15); bridge_m1(tM12, tM11)
    strip_to_gate_rail(M15, 'bot', 5)                               # mir drain -> mir gate rail
    e_mir_a = gate_exit(gM14, -1, XMIR)
    e_vbpc_a = gate_exit(gM15, -1, XVBPC)
    e_out1_a = exit_wire(M12, 'bot', 11, 1.7, XOUT1)
    # vdd rails of M14 / M11 straight to the trunks on Metal2 at the rail level
    x, y = rail_via(M14, 'bot', 0); D.hwire('M2', x, XVDD_L, y, EXTW); D.stack(XVDD_L, y, 'M2', 'M3')
    x, y = rail_via(M11, 'bot', 12); D.hwire('M2', x, XVDD_R, y, EXTW); D.stack(XVDD_R, y, 'M2', 'M3')

    # ------------------------------------------------------------------ row P-B (pair) ---------
    m = PAIR
    pattern = 'ABBAABBAABBAABBA'
    A_g = [f for f in range(32) if pattern[f // 2] == 'A']
    B_g = [f for f in range(32) if pattern[f // 2] == 'B']
    A_d = [2 * j + 1 for j in range(16) if pattern[j] == 'A']
    B_d = [2 * j + 1 for j in range(16) if pattern[j] == 'B']
    for f in A_g:
        m.gate_pad(f, 'bot')
    for f in B_g:
        m.gate_pad(f, 'top')
    ya, yb = m.yd('bot', Mos.GRAIL_LO), m.yd('bot', Mos.GRAIL_HI)
    D.box('M2', m.gx(A_g[0]) - 0.20, min(ya, yb), BX2, max(ya, yb))            # inn rail -> east edge
    inn_pin = ('M2', BX2 - 0.5, (ya + yb) / 2)
    ya, yb = m.yd('top', Mos.GRAIL_LO), m.yd('top', Mos.GRAIL_HI)
    D.box('M2', m.gx(B_g[0]) - 0.20, min(ya, yb), BX2, max(ya, yb))            # inp rail -> east edge
    inp_pin = ('M2', BX2 - 0.5, (ya + yb) / 2)
    rfn = m.rail('bot', A_d); rfp = m.rail('top', B_d)
    x, y = rail_via(m, 'bot', A_d[0]); D.hwire('M2', x, XFN, y, EXTW); D.sq('M2', XFN, y, PAD); D.sq('Via2', XFN, y, VIA); D.sq('M3', XFN, y, PAD)
    e_fn_b = (XFN, y)
    x, y = rail_via(m, 'top', B_d[-1]); D.hwire('M2', x, XFP, y, EXTW); D.sq('M2', XFP, y, PAD); D.sq('Via2', XFP, y, VIA); D.sq('M3', XFP, y, PAD)
    e_fp_b = (XFP, y)
    # tail: even strips -> pads inside the Activ (top end) -> Metal3 verticals -> Metal3 tail bus
    ytail = m.yd('top', 1.9)
    for k in m.strips(0):
        x, y = m.strip_pad(k, 'top', -0.35, hi='M3')
        D.vwire('M3', x, y, ytail, 0.30)
    D.hwire('M3', m.sx(0), m.sx(32), ytail, VERTW)

    # ------------------------------------------------------------------ row P-C ----------------
    gMB7 = MB7.gate_bar('bot', m2=False); diode(MB7, 0, 'bot')      # vbpc diode
    gMB5 = MB5.gate_bar('bot'); gMB3 = MB3.gate_bar('bot'); gMT = MT.gate_bar('bot')   # vbp
    gM20 = M20.gate_bar('bot')                                      # out1
    bridge_m2(gMB5, gMB3); bridge_m2(gMB3, gMT)
    rMB7 = MB7.rail('bot', [1]); rMB5 = MB5.rail('bot', [1]); rMB3 = MB3.rail('bot', [1])
    rMT = MT.rail('bot', MT.strips(1)); rM20 = M20.rail('bot', M20.strips(1))
    strip_to_gate_rail(MB3, 'bot', 1)                               # vbp diode
    # vdd: all sources on top; MB7 strip 0 reaches up from its 3.2 um Activ
    tMB7 = MB7.rail('top', [0], lo=8 - 3.2 + Mos.RAIL_LO, hi=8 - 3.2 + Mos.RAIL_HI)
    tMB5 = MB5.rail('top', [0, 2]); tMB3 = MB3.rail('top', [0, 2])
    tMT = MT.rail('top', MT.strips(0)); tM20 = M20.rail('top', M20.strips(0))
    bridge_m1(tMB7, tMB5); bridge_m1(tMB5, tMB3); bridge_m1(tMB3, tMT); bridge_m1(tMT, tM20)
    yd_ = Y['PC'] + 8 + RAILC
    D.box('M4', XVDD_L - TRUNKW / 2, yd_ - 0.25, XVDD_R + TRUNKW / 2, yd_ + 0.75)
    for mm, ks in ((MT, (0, 4, 8, 12, 16)), (M20, (0, 4, 8, 12, 16, 20, 24)), (MB5, (0,)), (MB3, (2,))):
        for k in ks:
            D.stack(mm.sx(k), yd_, 'M1', 'M4')
    e_vbpc_c = exit_wire(MB7, 'bot', 1, RAILC, XVBPC)
    e_vbnc_c = exit_wire(MB5, 'bot', 1, 1.7, XVBNC)
    e_vbp_c = gate_exit(gMB5, -1, XVBP)
    e_out_c = exit_wire(M20, 'bot', 23, 1.7, XOUT)
    e_out1_c = gate_exit(gM20, +1, XOUT1)
    # tail: Metal3 verticals from the tail bus up to MT's drain rail
    for k in (3, 7, 11, 15):
        x, y = rail_via(MT, 'bot', k, hi='M3')
        D.vwire('M3', x, ytail, y, 0.30)

    # ------------------------------------------------------------------ Metal3 verticals -------
    def vert(x, ys):
        D.vwire('M3', x, min(ys), max(ys), VERTW)
    vert(XVBNC, (e_vbnc_n[1], e_vbnc_t[1], e_vbnc_c[1]))
    vert(XVBP, (e_vbp_n[1], e_vbp_c[1]))
    vert(XVBPC, (e_vbpc_n[1], e_vbpc_a[1], e_vbpc_c[1]))
    vert(XMIR, (e_mir_n[1], e_mir_a[1]))
    vert(XFN, (e_fn_n[1], e_fn_b[1]))
    vert(XFP, (e_fp_n[1], e_fp_b[1]))
    vert(XOUT1, (e_out1_n[1], e_out1_a[1], e_out1_c[1]))
    vert(XOUT, (e_out_n[1], e_out_c[1]))

    # ------------------------------------------------------------------ RZ and CC --------------
    YRZ = 26.0
    D.pcell('rppd', {'Calculate': 'R', 'w': '1u', 'l': '6.2u'}, XRZ, YRZ)
    xrz = XRZ + 0.5
    ylo, yhi = YRZ - 0.28, YRZ + 6.2 + 0.28               # Metal1 head centres
    D.sq('M1', xrz, ylo, 0.34); D.sq('M1', xrz, yhi, 0.34)
    D.stack(xrz, ylo, 'M1', 'M2'); D.hwire('M2', xrz, XOUT1, ylo, EXTW)
    D.sq('M2', XOUT1, ylo, PAD); D.sq('Via2', XOUT1, ylo, VIA); D.sq('M3', XOUT1, ylo, PAD)
    D.stack(xrz, yhi, 'M1', 'TM1')                          # cz up to TopMetal1
    # capacitor over rows P-A/P-B: bottom plate Metal5 = out, top plate TopMetal1 = cz
    CX0, CY0 = snap(W / 2 - 11.5), 12.4
    D.pcell('cmim', {'Calculate': 'C', 'w': '23u', 'l': '23u'}, CX0, CY0)
    D.box('TM1', CX0 + 23 - 0.16 - 0.5, yhi - 1.0, xrz + 0.85, yhi + 1.0)     # top plate tab (2.0 wide)
    YTAB = CY0 + 4.0
    D.box('M5', CX0 + 23 + 0.6 - 0.5, YTAB - 0.6, XOUT + 0.6, YTAB + 0.6)     # bottom plate tab
    D.stack(XOUT, YTAB, 'M3', 'M5')

    # ------------------------------------------------------------------ power -----------------
    for xt in (XVSS_L, XVSS_R, XVDD_L, XVDD_R):
        D.box('M3', xt - TRUNKW / 2, BY1, xt + TRUNKW / 2, BY2)
    for xt in (XVSS_L, XVSS_R):                             # vss bar <-> trunks
        D.via_fill(xt - TRUNKW / 2 + 0.1, yv - 0.25 + 0.1, xt + TRUNKW / 2 - 0.1, yv + 0.75 - 0.1, 'M3', 'M4')
    for xt in (XVDD_L, XVDD_R):
        D.via_fill(xt - TRUNKW / 2 + 0.1, yd_ - 0.25 + 0.1, xt + TRUNKW / 2 - 0.1, yd_ + 0.75 - 0.1, 'M3', 'M4')

    # ------------------------------------------------------------------ wells, taps, rings -------
    NRY1, NRY2 = Y['PA'] - 1.85, Y['PC'] + 8 + 1.85           # n+ ring inner box y
    NWE = 0.30 + 0.30                                         # NWell beyond the ring inner box (NW.e 0.24)
    D.box('NWell', NR_X1 - NWE, NRY1 - NWE, NR_X2 + NWE, NRY2 + NWE)
    nr = D.tap_ring(NR_X1, NRY1, NR_X2, NRY2, 0.30, ptype=False)
    D.tap_strip(NR_X1 - 0.30, NR_X2 + 0.30, Y['PA'] + 8 + 1.7, ptype=False, inset=0.6)
    D.tap_strip(NR_X1 - 0.30, NR_X2 + 0.30, Y['PB'] + 6 + 1.7, ptype=False, inset=0.6)
    # n+ ring -> vdd trunks with Metal2 stubs at a free height (row P-A) and Metal1 pads on the ring
    for xr_, xt in ((nr[0], XVDD_L), (nr[2], XVDD_R)):
        yq = Y['PA'] + 4.0
        D.sq('M1', xr_, yq, 0.34); D.stack(xr_, yq, 'M1', 'M2'); D.hwire('M2', xr_, xt, yq, EXTW); D.stack(xt, yq, 'M2', 'M3')
    # p+ substrate ring, tied to the vss trunks where they cross its top and bottom sides
    pr = D.tap_ring(XL, YB, XR, YT, 0.30, ptype=True)
    for xt in (XVSS_L, XVSS_R):
        for yq in (pr[1], pr[3]):
            D.sq('M1', xt, yq, 0.34); D.stack(xt, yq, 'M1', 'M3')

    # ------------------------------------------------------------------ pins, labels, boundary --
    YOUTPIN = 20.0                                          # out pin on Metal2 (crosses the Metal3 trunks)
    D.sq('M3', XOUT, YOUTPIN, PAD); D.sq('Via2', XOUT, YOUTPIN, VIA)
    D.hwire('M2', XOUT, BX2, YOUTPIN, EXTW)
    out_pin = ('M2', BX2 - 0.5, YOUTPIN)
    for (layer, x, y), nm in ((inn_pin, 'inn'), (inp_pin, 'inp'), (vbn_pin, 'vbn'), (out_pin, 'out')):
        D.label(layer + 'txt', x - 1.5, y, nm)                       # labels 2 um inside the east edge
    D.label('M3txt', XVDD_L, Y['PB'], 'vdd'); D.label('M3txt', XVSS_L, Y['PB'], 'vss')
    # no fill over the input pair row (3 um margin, full cell width) and over the Miller capacitor
    D.nofill(BX1, Y['PB'] - 3.0, BX2, Y['PB'] + 6 + 3.0)
    D.nofill(CX0 - 3.0, CY0 - 3.0, CX0 + 23 + 3.0, CY0 + 23 + 3.0)
    D.boundary(BX1, BY1, BX2, BY2)
    info = {'pins': {'inn': inn_pin, 'inp': inp_pin, 'vbn': vbn_pin, 'out': out_pin,
                     'vdd': ('M3', XVDD_L, XVDD_R), 'vss': ('M3', XVSS_L, XVSS_R),
                     'vdd_bar_y': yd_, 'vss_bar_y': yv},
            'bbox': (BX1, BY1, BX2, BY2), 'W': W}
    return cell, info


if __name__ == '__main__':
    ly = pya.Layout(); ly.dbu = 0.001
    cell, info = build_ota(ly)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'build', 'g1_sense_lay')
    write_gds(ly, os.path.join(out, 'g1_ota.gds'))
    print('bbox', cell.dbbox(), 'boundary', info['bbox'], 'W', info['W'])
