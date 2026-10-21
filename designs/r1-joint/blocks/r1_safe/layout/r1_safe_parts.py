#!/usr/bin/env python3
"""r1_safe layout parts: tree multiplexer (r1s_mux), threshold string (r1s_string), level shifter (r1s_ls).

Conventions (um; database unit 1 nm). Tap track i of the shared string is a Metal3 line at y = 0.48*i in the
band frame (track 0 at y = 0). All parts are built in that frame.

Multiplexer r1s_mux (one 256:1 thick-NMOS tree, netlist r1_safe_mux, 510 sg13_hv_nmos w 0.5 l 0.45):
  8 columns at pitch CP = 2.7 um, one per tree level k (column k holds 2**(7-k) switch pairs). A switch pair is two
  nmosHV PCells sharing the middle diffusion: L diffusion (even input) | gate A = bb_k | M (output) | gate B = b_k |
  R diffusion (odd input). Gates A and B of a column are two continuous vertical GatPoly lines (the select buses of
  level k), contacted once at the top (y = Y_PC). Pair of column k, centre yc: L input at yc-0.24, R input at
  yc+0.24, output (Metal2) at yc-0.24 to the gap track x_g(k+1). Column 0: L and R are via stacks to tap tracks
  2j and 2j+1 (yc = 0.96 j + 0.24). Column k >= 1: Metal2 gap track x_g(k) = cx(k) - 0.40 carries the outputs of
  the two children to the L input (Metal1 stub) and the R input (Metal2 at yc + 0.24).
"""
from r1_safe_lib import Draw, T, pya, um  # noqa: F401

CP = 2.7            # column pitch
MUX_PITCH = 23.6    # mux pitch in the band (8 columns + output gap + shared p-tap)
TRK = 0.48          # tap track pitch
Y_PC = 123.0        # gate poly contact row (band frame)
NLEV = 8


def mux_geometry():
    """strip centres per column and output y; returns ys[k] = list of yc, outs[k] = list of output y"""
    ys, outs = [], []
    ys.append([0.96 * j + 0.24 for j in range(128)])
    outs.append([y - 0.24 for y in ys[0]])
    for k in range(1, NLEV):
        yk = [round((outs[k - 1][2 * j] + outs[k - 1][2 * j + 1]) / 2, 3) for j in range(2 ** (7 - k))]
        ys.append(yk)
        outs.append([round(y - 0.24, 3) for y in yk])
    return ys, outs


def build_mux(ly):
    c = ly.create_cell('r1s_mux')
    D = Draw(ly, c)
    # switch pair leaf cell (two nmosHV sharing the middle diffusion), placed with its Activ lower-left at (cx, yc-0.25)
    pc = ly.create_cell('r1s_mxpair')
    PD = Draw(ly, pc)
    prm = {'w': '0.5u', 'l': '0.45u', 'ng': 1}
    PD.pcell('nmosHV', prm, T(0, 0))
    PD.pcell('nmosHV', prm, T(0.83, 0))
    PD.clean()
    ys, outs = mux_geometry()
    ylo = min(min(v) for v in ys) - 0.25
    for k in range(NLEV):
        cx = k * CP
        xL, xM, xR = cx + 0.15, cx + 0.98, cx + 1.81
        xg_in = cx - 0.40
        xg_out = cx + CP - 0.40
        for j, yc in enumerate(ys[k]):
            c.insert(pya.CellInstArray(pc.cell_index(), T(cx, yc - 0.25)))
            # output: Via1 on M, Metal2 to the next gap track
            D.via('Via1', xM, yc - 0.24, lo='s', hi=None)
            D.hw('M2', xM - 0.045, xg_out, yc - 0.24)
            if k == 0:
                # tap stacks; Metal2 pads 0.50 x 0.30 (area >= Mn.d 0.144), extended away from the gap tracks
                D.via('Via1', xL, yc - 0.24, lo='s', hi=None)
                D.box('M2', cx + 0.0, yc - 0.39, cx + 0.50, yc - 0.09)
                D.via('Via2', xL, yc - 0.24, lo=None, hi='t')
                D.via('Via1', xR, yc + 0.24, lo='s', hi=None)
                D.box('M2', cx + 1.46, yc + 0.09, cx + 1.96, yc + 0.39)
                D.via('Via2', xR, yc + 0.24, lo=None, hi='t')
            else:
                a, b = outs[k - 1][2 * j], outs[k - 1][2 * j + 1]
                # L: Metal1 stub from the gap track to the L diffusion, Via1 at the gap track
                D.box('M1', xg_in - 0.15, yc - 0.39, cx + 0.23, yc - 0.09)
                D.via('Via1', xg_in, yc - 0.24, lo=None, hi='v')
                D.vw('M2', xg_in, a, yc - 0.24)
                # R: Metal1 pad on the R diffusion, Metal2 to the gap track, then up to the upper child
                D.via('Via1', xR, yc + 0.24, lo='s', hi=None)
                D.hw('M2', xg_in, xR + 0.045, yc + 0.24)
                D.vw('M2', xg_in, yc + 0.24, b)
        # gate lines (select buses of level k): bb_k on gate A, b_k on gate B
        ytop = Y_PC + 0.15
        y0 = min(ys[k]) - 0.43
        D.box('GatPoly', cx + 0.34, y0, cx + 0.79, ytop)
        D.box('GatPoly', cx + 1.17, y0, cx + 1.62, ytop)
        for gx in (cx + 0.565, cx + 1.395):
            D.cont(gx, Y_PC)
            D.via('Via1', gx, Y_PC, lo='s', hi='v')
    # output of column 7: Metal2 down to the cell bottom
    x_out = (NLEV - 1) * CP + CP - 0.40
    y7 = outs[NLEV - 1][0]
    D.vw('M2', x_out, -1.5, y7)
    # thick-oxide region and the substrate ties at both sides (shared with the neighbour mux)
    D.box('TGO', -1.9, ylo - 1.2, MUX_PITCH - 1.9, Y_PC + 0.6)
    for xt in (-1.6, MUX_PITCH - 1.6):
        D.ptap(xt, ylo - 0.8, xt + 0.36, Y_PC + 0.3)
    meta = {'x_out': x_out, 'y_out_bottom': -1.5, 'gate_x': [[k * CP + 0.565, k * CP + 1.395] for k in range(NLEV)],
            'y_pc': Y_PC, 'ylo': ylo, 'tap_x': [-1.6, MUX_PITCH - 1.6], 'y7': y7}
    return c, meta


# ----------------------------------------------------------------------------------------------------------------
# Threshold string r1s_string: 252 rppd units (w 2, l 7.7) in 51 rows of 5 (row 50: 2 units), serpentine, rows at
# pitch 2.4 um (5 tap tracks per row), bodies along x (PCell rotated 90 deg). Node n (tap Tn) sits on head h_i of
# row n // 5 and lands on tap track n by a Via1/Via2 stack. Dummy rows below row 0 and above row 50, short dummy
# strips (l 2 um) at both ends of every row, dummies in the three empty slots of row 50. Dummies are GatPoly with
# pSD/SalBlock/EXTBlock but without the RES/PolyRes recognition layers (not devices).
UL, UW = 7.7, 2.0
UP = UL + 0.56          # unit pitch along a row (shared heads)
RP = 2.4                # row pitch
NROW = 51


def string_geometry(X1=3.97):
    hx = [X1 + UP * i - 0.28 for i in range(6)]
    return X1, hx


def node_head(n, hx):
    r, i = n // 5, n % 5
    return r, (hx[i] if r % 2 == 0 else hx[5 - i])


def build_string(ly, X1=3.97):
    c = ly.create_cell('r1s_string')
    D = Draw(ly, c)
    X1, hx = string_geometry(X1)

    def dummy(x1, x2, yb):
        D.box('GatPoly', x1, yb, x2, yb + UW)
        D.box('SalBlock', x1 + 0.43, yb - 0.2, x2 - 0.43, yb + UW + 0.2)
        D.box('pSD', x1 - 0.18, yb - 0.18, x2 + 0.18, yb + UW + 0.18)
        D.box('ExtBlock', x1 - 0.18, yb - 0.18, x2 + 0.18, yb + UW + 0.18)

    xl_d = (X1 - 0.93 - 2.86, X1 - 0.93)
    xr_d = (X1 + 4 * UP + 8.13 + 0.5, X1 + 4 * UP + 8.13 + 0.5 + 2.86)
    units = []
    for r in range(-1, NROW + 1):
        yb = RP * r - 0.02
        if r < 0 or r >= NROW:
            dummy(xl_d[0], xr_d[1], yb)
            continue
        dummy(*xl_d, yb)
        dummy(*xr_d, yb)
        nreal = 5 if r < NROW - 1 else 252 - 5 * (NROW - 1)
        for s in range(5):
            us = X1 + UP * s
            if s < nreal:
                D.pcell('rppd', {'w': '2u', 'l': '7.7u', 'b': 0, 'ps': '0.18u', 'Calculate': 'R'}, T(us + UL, yb, 90))
            unit = 5 * r + (s if r % 2 == 0 else 4 - s)
            if s < nreal or (r % 2 == 1):
                pass
            units.append(unit) if s < nreal else None
        if nreal < 5:
            x0 = X1 + UP * (nreal - 1) + 8.13 + 0.5
            dummy(x0, X1 + 4 * UP + 8.13, yb)
        # jumpers to the next row
        if r < NROW - 1:
            hj = hx[5] if r % 2 == 0 else hx[0]
            D.box('M1', hj - 0.15, yb + 1.0, hj + 0.15, yb + RP + 1.0)
    # one pSD and one EXTBlock region over the whole array (rows at 2.4 um pitch would leave 0.04 um slits)
    D.box('pSD', xl_d[0] - 0.18, RP * -1 - 0.2, xr_d[1] + 0.18, RP * NROW - 0.02 + UW + 0.2)
    D.box('ExtBlock', xl_d[0] - 0.18, RP * -1 - 0.2, xr_d[1] + 0.18, RP * NROW - 0.02 + UW + 0.2)
    D.clean()
    # tap via stacks: node n on track n (Metal2 pad 0.50 x 0.30); mux inputs 253-255 are T252: one Metal2 bar at
    # the T252 head carries Via2 to tracks 252..255
    stacks = {}
    for n in range(253):
        r, x = node_head(n, hx)
        y = TRK * n
        D.box('M1', x - 0.15, y - 0.15, x + 0.15, y + 0.15)
        D.via('Via1', x, y, lo='s', hi=None)
        if n < 252:
            D.box('M2', x - 0.25, y - 0.15, x + 0.25, y + 0.15)
        D.via('Via2', x, y, lo=None, hi='t')
        stacks[n] = (x, y)
    x252 = stacks[252][0]
    D.box('M2', x252 - 0.15, TRK * 252 - 0.15, x252 + 0.15, TRK * 255 + 0.15)
    for n in (253, 254, 255):
        D.via('Via2', x252, TRK * n, lo=None, hi='t')
        stacks[n] = (x252, TRK * n)
    meta = {'X1': X1, 'hx': hx, 'stacks': stacks, 'x_left': xl_d[0] - 0.18, 'x_right': xr_d[1] + 0.18,
            'y_bot': RP * -1 - 0.02 - 0.18, 'y_top': RP * NROW - 0.02 + UW + 0.18}
    return c, meta


# ----------------------------------------------------------------------------------------------------------------
# Level shifter r1s_ls (netlist r1_safe_ls: in vdd vdda vss out outb), 5.9 x 14.1 um, abutting in rows.
# Bottom to top: vss rail + p-tap | NMOS (pair1 MN1/MN2 w4, pair2 MB1N/MB2N w1, shared vss) | vdda NWell (pair3
# MP1/MP2 w0.6, pair4 MB1P/MB2P w2, shared vdda) + vdda tie | LV NMOS MIN | vdd NWell (LV PMOS MIP) + vdd tie.
# out (b) and outb (bb) leave as Via1/Via2 stacks with Metal3 pads at y 1.75 (x 5.11 / 3.45). `in` is a Metal2 line
# at x 0.915 over the full height. MIN source goes to a Metal3 vss rail at y 10.50..10.80.
LS_W, LS_H = 5.9, 14.1
LS_OUTB_X, LS_OUT_X, LS_OUT_Y, LS_IN_X = 3.45, 5.11, 1.75, 0.915


def build_ls(ly):
    c = ly.create_cell('r1s_ls')
    D = Draw(ly, c)
    W = LS_W
    nh = {'l': '0.45u', 'ng': 1}
    for x0 in (0.35, 1.18):
        D.pcell('nmosHV', dict(nh, w='4u'), T(x0, 1.25))
    for x0 in (3.30, 4.13):
        D.pcell('nmosHV', dict(nh, w='1u'), T(x0, 1.25))
    for x0 in (0.30, 1.18):
        D.pcell('pmosHV', {'w': '0.6u', 'l': '0.5u', 'ng': 1}, T(x0, 6.6))
    for x0 in (3.25, 4.13):
        D.pcell('pmosHV', {'w': '2u', 'l': '0.5u', 'ng': 1}, T(x0, 6.6))
    D.pcell('nmos', {'w': '0.5u', 'l': '0.13u', 'ng': 1}, T(0.51, 10.40))
    D.pcell('pmos', {'w': '1u', 'l': '0.13u', 'ng': 1}, T(0.51, 12.14))
    D.clean()
    # rails and ties (each cell draws its piece; abutting pieces merge)
    D.box('Activ', 0, 0.05, W, 0.35)
    D.box('pSD', -0.03, 0.02, W + 0.03, 0.38)
    D.cont_row(0.07, W - 0.07, 0.20)
    D.box('M1', 0, 0.0, W, 0.40)                       # vss
    D.box('Activ', 0, 9.05, W, 9.41)
    D.cont_row(0.07, W - 0.07, 9.23)
    D.box('M1', 0, 9.03, W, 9.43)                      # vdda
    D.box('Activ', 0, 13.50, W, 13.86)
    D.cont_row(0.07, W - 0.07, 13.68)
    D.box('M1', 0, 13.48, W, 13.88)                    # vdd
    D.box('M3', 0, 10.50, W, 10.80)                    # vss (Metal3, for MIN)
    D.box('NWell', 0, 5.98, W, 10.03)
    D.box('NWell', 0, 11.83, W, LS_H)
    D.box('TGO', 0, 0.70, W, 10.03)
    # NMOS sources to vss
    D.box('M1', 1.25, 0.40, 1.41, 1.25)
    D.box('M1', 4.20, 0.40, 4.36, 1.25)
    # pair1 gates: in (A) and inb (B), contacted below the pair
    D.box('GatPoly', 0.69, 0.85, 1.14, 1.25)
    D.box('GatPoly', 1.52, 0.85, 1.97, 1.25)
    for gx in (0.915, 1.745):
        D.cont(gx, 1.0)
        D.via('Via1', gx, 1.0, lo='s', hi='v')
    D.vw('M2', 0.915, 1.0, LS_H - 0.10)                 # in
    D.vw('M2', 1.745, 1.0, 12.64)                      # inb
    # a and b between pair1 and pair3
    D.box('M1', 0.37, 5.25, 0.58, 6.6)
    D.box('M1', 2.08, 5.25, 2.29, 6.6)
    # pair3 gates: A = b (contact low), B = a (contact high)
    D.box('GatPoly', 0.64, 5.65, 1.14, 6.6)
    D.cont(0.94, 5.80)
    D.box('M1', 0.79, 5.65, 1.09, 5.95)
    D.box('M1', 0.79, 5.70, 2.29, 5.90)
    D.box('GatPoly', 1.52, 6.15, 2.02, 6.6)
    D.cont(1.72, 6.30)
    D.box('M1', 1.57, 6.15, 1.87, 6.45)
    D.box('M1', 0.37, 6.20, 1.87, 6.40)
    # pair2/pair4 shared gates: A = b, B = outb
    D.box('GatPoly', 3.64, 2.25, 4.09, 6.6)
    D.box('GatPoly', 4.47, 2.25, 4.92, 6.6)
    D.box('M1', 3.32, 2.25, 3.53, 6.6)                 # outb
    D.box('M1', 5.03, 2.25, 5.24, 6.6)                 # out
    D.cont(4.67, 3.6)
    D.box('M1', 4.52, 3.45, 4.82, 3.75)
    D.box('M1', 3.32, 3.50, 4.82, 3.70)
    D.cont(3.89, 3.0)
    D.via('Via1', 3.89, 3.0, lo='s', hi=None)
    D.hw('M2', 2.6 - 0.045, 3.89 + 0.045, 3.0)
    D.box('M1', 2.08, 2.85, 2.75, 3.15)
    D.via('Via1', 2.6, 3.0, lo=None, hi=None)
    # PMOS sources to vdda
    D.box('M1', 1.25, 7.2, 1.41, 9.03)
    D.box('M1', 4.20, 8.6, 4.36, 9.03)
    # LV inverter: MIN (10.40..10.90), MIP (12.14..13.14), common gate contacted between them
    D.box('GatPoly', 0.85, 10.90, 0.98, 12.14)
    D.box('GatPoly', 0.765, 11.35, 1.065, 11.65)
    D.cont(0.915, 11.50)
    D.via('Via1', 0.915, 11.50, lo='s', hi='v')
    D.box('M1', 1.09, 10.50, 1.895, 10.80)             # MIN drain -> inb
    D.via('Via1', 1.745, 10.65, lo=None, hi='v')
    D.box('M1', 1.09, 12.49, 1.895, 12.79)             # MIP drain -> inb
    D.via('Via1', 1.745, 12.64, lo=None, hi='v')
    D.box('M1', 0.15, 10.50, 0.74, 10.80)              # MIN source -> vss (Metal3)
    D.via('Via1', 0.30, 10.65, lo=None, hi=None)
    D.box('M2', 0.15, 10.40, 0.45, 10.90)
    D.via('Via2', 0.30, 10.65, lo=None, hi=None)
    D.box('M1', 0.58, 13.14, 0.74, 13.48)              # MIP source -> vdd
    # outputs: stacks to Metal3 pads
    for x in (LS_OUTB_X, LS_OUT_X):
        D.via('Via1', x, LS_OUT_Y, lo='s', hi=None)
        D.box('M2', x - 0.15, LS_OUT_Y - 0.25, x + 0.15, LS_OUT_Y + 0.25)
        D.via('Via2', x, LS_OUT_Y, lo=None, hi=None)
        D.box('M3', x - 0.25, LS_OUT_Y - 0.15, x + 0.25, LS_OUT_Y + 0.15)
    return c
