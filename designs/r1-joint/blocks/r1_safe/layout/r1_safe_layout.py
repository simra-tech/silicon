#!/usr/bin/env python3
"""r1_safe (analog part, revision 3) layout generator. KLayout batch Python, PDK commit 8437402, KLayout 0.30.9.

  G1_WORKDIR=designs/r1-joint/blocks/r1_safe/layout flow/run.sh klayout -b -r r1_safe_layout.py -rd out=<dir> [-rd cmp=0]
Writes <dir>/r1_safe.gds, <dir>/r1_safe_lvs.cdl (via make_cdl.py), <dir>/r1_safe_layout_meta.json, <dir>/r1_safe.lef.
With cmp=0 the four comparators are left out (development check of string + multiplexers + level shifters).

Floorplan (bottom to top): pin strip with the sense-input buses | four comparators r1s_cmp (identical copies, side by
side) | channel C (multiplexer outputs to REFP/REFN) | band: threshold string r1s_string (west) + eight 256:1
multiplexers r1s_mux (OCa P, OCa N, NGa P, NGa N, OCb P, OCb N, NGb P, NGb N) on 256 Metal3 tap tracks | channel A
(select lines: gate contacts -> Metal3 tracks) | level-shifter row A (levels 0..3) | row B (levels 4..7) | code pins.
Supplies: Metal4 trunks vss, vdda, vdd on the west and east edges, Metal3 pins at both edges. p+ guard ring (vss)
around the block. Metal1..Metal4 only.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '/work/designs/r1-joint/blocks/r1_safe/layout'
sys.path.insert(0, HERE)
sys.path.insert(0, '/work/designs/r1-joint/blocks/r1_safe/layout')
from r1_safe_lib import Draw, pya, place, write_gds, um  # noqa: E402
import r1_safe_parts as P  # noqa: E402

OUT = globals().get('out', HERE)
WITH_CMP = str(globals().get('cmp', '1')) == '1'
os.makedirs(OUT, exist_ok=True)

ly = pya.Layout()
ly.dbu = 0.001
top = ly.create_cell('r1_safe')
D = Draw(ly, top)
mux, MM = P.build_mux(ly)
strc, SM = P.build_string(ly)
lsc = P.build_ls(ly)
CM = None
if WITH_CMP:
    import r1_safe_cmp_cell as C  # noqa: E402
    cmpc = C.build_cmp(ly)
    CM = json.load(open(os.path.join(HERE, 'r1_safe_cmp_cell_meta.json')))
    WC, HC = CM['W'], CM['H']
else:
    WC, HC = 59.0, 0.0

# ------------------------------------------------------------------------------------------------ geometry
TR = {'vss': (1.1, 1.8), 'vdda': (2.2, 2.9), 'vdd': (3.3, 4.0)}      # Metal4 trunks (west); east mirrored
LM = 4.6
XS = LM
XM0 = XS + SM['x_right'] + 2.5 + 1.6
MUXX = [XM0 + P.MUX_PITCH * m for m in range(8)]
X_LAST_TAP = MUXX[7] + MM['tap_x'][1] + 0.36
W = round(X_LAST_TAP + LM - 0.2, 2)
TRE = {k: (W - b, W - a) for k, (a, b) in TR.items()}
YC0 = 7.0                                 # comparator row bottom
NCT = 8                                   # channel C tracks
YCT0 = YC0 + HC + 1.2                     # first channel C track
YVB = YCT0 + NCT * 0.48 + 0.5             # vss Metal1 bus (mux taps), centre
YB = YVB + 0.4 + 2.62 + 0.6               # band frame origin (string dummy row bottom at YB - 2.62)
YCA = YB + P.Y_PC + 0.55                  # first channel A track
YA = YB + P.Y_PC + 8.4                    # level-shifter row A origin
YBR = YA + P.LS_H + 0.7                   # row B origin
H = round(YBR + P.LS_H + 2.0, 2)
XC0 = round((W - 4 * WC) / 2, 2)

# ------------------------------------------------------------------------------------------------ band
place(top, strc, XS, YB)
for x in MUXX:
    place(top, mux, x, YB)
# tap tracks (Metal3 0.24 wide) from the string head to the last multiplexer's column-0 R pad
x_end = MUXX[7] + 1.81 + 0.15
for n in range(256):
    xs = XS + SM['stacks'][n][0]
    D.box('M3', xs - 0.15, YB + P.TRK * n - 0.12, x_end, YB + P.TRK * n + 0.12)
# vref: track 253 (= T252) extended west to the block edge (pin); vss: track 0 extended west to the vss trunk
D.box('M3', 0, YB + P.TRK * 253 - 0.12, XS + SM['stacks'][253][0], YB + P.TRK * 253 + 0.12)
D.pin('M3', 0, YB + P.TRK * 253 - 0.12, 1.0, YB + P.TRK * 253 + 0.12, 'vref')
D.box('M3', TR['vss'][0], YB - 0.12, XS + SM['stacks'][0][0], YB + 0.12)
BUSY_Y = [YB, YB + P.TRK * 253]

# ------------------------------------------------------------------------------------------------ supplies
def trunk_stack(x, y, w=0.6):
    """Via1+Via2+Via3 at (x, y) from Metal1 to the Metal4 trunk"""
    D.via('Via1', x, y, lo='s', hi=None)
    D.sq('M2', x, y, 0.42)
    D.via('Via2', x, y, lo=None, hi=None)
    D.sq('M3', x, y, 0.42)
    D.via('Via3', x, y, lo=None, hi=None)
    BUSY_Y.append(y)


def m3_trunk_via(x, y):
    D.via('Via3', x, y, lo='s', hi=None)
    BUSY_Y.append(y)


YT0, YT1 = 1.2, H - 1.2
for net in TR:
    for (a, b) in (TR[net], TRE[net]):
        D.box('M4', a, YT0, b, YT1)
# guard ring (p+, vss): Activ 0.36 wide at 0.40 from the edge, Metal1 over it
GR = (0.40, 0.40, W - 0.40, H - 0.40)
g = 0.36
for (x1, y1, x2, y2) in ((GR[0], GR[1], GR[2], GR[1] + g), (GR[0], GR[3] - g, GR[2], GR[3]),
                         (GR[0], GR[1], GR[0] + g, GR[3]), (GR[2] - g, GR[1], GR[2], GR[3])):
    D.box('Activ', x1, y1, x2, y2)
    D.box('M1', x1, y1, x2, y2)
D.box('pSD', GR[0] - 0.03, GR[1] - 0.03, GR[2] + 0.03, GR[1] + g + 0.03)
D.box('pSD', GR[0] - 0.03, GR[3] - g - 0.03, GR[2] + 0.03, GR[3] + 0.03)
D.box('pSD', GR[0] - 0.03, GR[1] - 0.03, GR[0] + g + 0.03, GR[3] + 0.03)
D.box('pSD', GR[2] - g - 0.03, GR[1] - 0.03, GR[2] + 0.03, GR[3] + 0.03)
D.cont_row(GR[0] + 0.07, GR[2] - 0.07, GR[1] + g / 2)
D.cont_row(GR[0] + 0.07, GR[2] - 0.07, GR[3] - g / 2)
D.cont_col(GR[1] + 0.5, GR[3] - 0.5, GR[0] + g / 2)
D.cont_col(GR[1] + 0.5, GR[3] - 0.5, GR[2] - g / 2)
xv_w, xv_e = sum(TR['vss']) / 2, sum(TRE['vss']) / 2
m3_trunk_via(xv_w, YB)                    # string bottom (track 0) to the vss trunk
# supply pins (Metal3) on both edges
for net, yp in (('vss', 4.0), ('vdda', 4.8), ('vdd', 5.6)):
    for (a, b), xe0, xe1 in ((TR[net], 0.0, 1.0), (TRE[net], W - 1.0, W)):
        x = (a + b) / 2
        D.box('M3', min(xe0, x), yp - 0.2, max(xe1, x), yp + 0.2)
        D.pin('M3', xe0, yp - 0.2, xe1, yp + 0.2, net)
        m3_trunk_via(x, yp)

# vss bus under the band (Metal1) for the multiplexer substrate ties
D.box('M1', TR['vss'][0], YVB - 0.2, TRE['vss'][1], YVB + 0.2)
for xw in (xv_w, xv_e):
    trunk_stack(xw, YVB)
for x in MUXX:
    for xt in MM['tap_x']:
        D.box('M1', x + xt, YVB, x + xt + 0.36, YB + MM['ylo'] - 0.6)

# ------------------------------------------------------------------------------------------------ level shifters
THR = ['oa', 'na', 'ob', 'nb']          # pin prefixes of XOCa, XNGa, XOCb, XNGb
LSX0 = -1.0                             # LS column 0 relative to the multiplexer origin
pins_top = []
for row, y0 in (('A', YA), ('B', YBR)):
    xa, xb = MUXX[0] + LSX0, MUXX[7] + LSX0 + 4 * P.LS_W
    for m, x in enumerate(MUXX):
        for i in range(4):
            place(top, lsc, x + LSX0 + P.LS_W * i, y0)
    # row-wide wells, thick oxide; rails extended to the trunks
    D.box('NWell', xa - 1.0, y0 + 5.98, xb + 1.0, y0 + 10.03)
    D.box('NWell', xa - 1.0, y0 + 11.83, xb + 1.0, y0 + P.LS_H)
    D.box('TGO', xa - 1.0, y0 + 0.70, xb + 1.0, y0 + 10.03)
    for net, (r0, r1), lay in (('vss', (0.0, 0.40), 'M1'), ('vdda', (9.03, 9.43), 'M1'), ('vdd', (13.48, 13.88), 'M1'),
                               ('vss', (10.50, 10.80), 'M3')):
        xw, xe = sum(TR[net]) / 2, sum(TRE[net]) / 2
        yc = y0 + (r0 + r1) / 2
        D.box(lay, xw - 0.3, y0 + r0, xa, y0 + r1)
        D.box(lay, xb, y0 + r0, xe + 0.3, y0 + r1)
        for xt in (xw, xe):
            if lay == 'M1':
                trunk_stack(xt, yc)
            else:
                m3_trunk_via(xt, yc)

# select lines: level k of mux m -> LS (row A if k < 4 else B), column i = k % 4
# LS outputs: row A Metal4 at outb 3.45 / out 5.11; row B jogged on Metal3 to 2.6 / 4.3, then Metal4 down.
GATE = MM['gate_x']
for m, x in enumerate(MUXX):
    thr, side = THR[m // 2], ('p' if m % 2 == 0 else 'n')
    for k in range(8):
        i = k % 4
        lx = x + LSX0 + P.LS_W * i
        y0 = YA if k < 4 else YBR
        for q_off, (gx, lsx, lsx_b) in enumerate(((GATE[k][0], P.LS_OUTB_X, 2.6), (GATE[k][1], P.LS_OUT_X, 4.3))):
            q = 2 * k + q_off
            yt = YCA + 0.48 * q
            xg = x + gx
            if k < 4:
                xm = lx + lsx
            else:
                xm = lx + lsx_b
                D.box('M3', min(xm, lx + lsx) - 0.15, y0 + P.LS_OUT_Y - 0.15, max(xm, lx + lsx) + 0.15, y0 + P.LS_OUT_Y + 0.15)
            D.via('Via3', xm, y0 + P.LS_OUT_Y, lo='s', hi=None)
            D.box('M4', xm - 0.15, yt - 0.15, xm + 0.15, y0 + P.LS_OUT_Y + 0.15)
            D.via('Via3', xm, yt, lo='t', hi=None)
            D.vw('M2', xg, YB + P.Y_PC, yt)
            D.via('Via2', xg, yt, lo='v', hi='t')
            xa_, xb_ = min(xg, xm) - 0.15, max(xg, xm) + 0.15
            if xb_ - xa_ < 0.65:
                xb_ = xa_ + 0.65
            D.box('M3', xa_, yt - 0.12, xb_, yt + 0.12)
        # code input pin
        name = '%s_%s%d' % (thr, side, k)
        if k >= 4:
            xi = lx + P.LS_IN_X
            D.vw('M2', xi, y0 + P.LS_H - 0.2, H - 0.8)
            D.via('Via2', xi, H - 0.8, lo='v', hi='v')
            D.box('M3', xi - 0.15, H - 0.95, xi + 0.15, H)
            D.pin('M3', xi - 0.15, H - 0.95, xi + 0.15, H, name)
        else:
            xi, xj = lx + P.LS_IN_X, lx + 0.25
            yj = y0 + P.LS_H + 0.35
            D.vw('M2', xi, y0 + P.LS_H - 0.2, yj)
            D.via('Via2', xi, yj, lo='v', hi='s')
            D.box('M3', xj - 0.15, yj - 0.15, xi + 0.15, yj + 0.15)
            D.via('Via3', xj, yj, lo='s', hi=None)
            D.box('M4', xj - 0.15, yj - 0.15, xj + 0.15, H - 0.6)
            D.via('Via3', xj, H - 0.8, lo=None, hi=None)
            D.box('M3', xj - 0.15, H - 0.95, xj + 0.15, H)
            D.pin('M3', xj - 0.15, H - 0.95, xj + 0.15, H, name)
        pins_top.append(name)

# ------------------------------------------------------------------------------------------------ comparators
REFS = []          # (mux index, comparator index, 'refp'/'refn')
for m in range(8):
    REFS.append((m, m // 2, 'refp' if m % 2 == 0 else 'refn'))
if WITH_CMP:
    for c in range(4):
        place(top, cmpc, XC0 + WC * c, YC0)
    # channel C: multiplexer outputs (Metal2 down to the track) -> Metal3 track -> Metal4 drop -> comparator pin
    used = []
    for m, c, pn in REFS:
        xo = MUXX[m] + MM['x_out']
        r = CM['pins'][pn]
        xp = XC0 + WC * c + (r[0] + r[2]) / 2
        span = (min(xo, xp) - 0.5, max(xo, xp) + 0.5)
        t = 0
        while any(tt == t and not (span[1] < s0 or span[0] > s1) for tt, s0, s1 in used):
            t += 1
        used.append((t, span[0], span[1]))
        yt = YCT0 + 0.48 * t
        D.vw('M2', xo, yt, YB + MM['y_out_bottom'])
        D.via('Via2', xo, yt, lo='v', hi='t')
        D.box('M3', min(xo, xp) - 0.15, yt - 0.12, max(xo, xp) + 0.15, yt + 0.12)
        D.via('Via3', xp, yt, lo='t', hi=None)
        D.box('M4', xp - 0.15, YC0 + HC - 0.5, xp + 0.15, yt + 0.15)
        D.via('Via3', xp, YC0 + HC - 0.4, lo=None, hi=None)
    assert max(u[0] for u in used) < NCT
    # supply rails of the comparator row to the trunks
    for net, (r0, r1) in CM['rails'].items():
        xw, xe = sum(TR[net]) / 2, sum(TRE[net]) / 2
        D.box('M3', xw - 0.3, YC0 + r0, XC0, YC0 + r1)
        D.box('M3', XC0 + 4 * WC, YC0 + r0, xe + 0.3, YC0 + r1)
        for xt in (xw, xe):
            m3_trunk_via(xt, YC0 + (r0 + r1) / 2)
    # bottom pins: out and ibias straight down; inp/inn joined per channel (outX_p on Metal4, outX_n on Metal2)
    OUTN = ['oc_a', 'neg_a', 'oc_b', 'neg_b']
    IBN = ['ibias_oa', 'ibias_na', 'ibias_ob', 'ibias_nb']
    for c in range(4):
        for pn, name in (('out', OUTN[c]), ('ibias', IBN[c])):
            r = CM['pins'][pn]
            x1, x2 = XC0 + WC * c + r[0], XC0 + WC * c + r[2]
            D.box('M3', x1, 0.0, x2, YC0 + r[3])
            D.pin('M3', x1, 0.0, x2, 1.0, name)
    for ch, (c0, c1) in (('a', (0, 1)), ('b', (2, 3))):
        # outX_p: comp c0.inp and comp c1.inn ; outX_n: comp c0.inn and comp c1.inp
        for net, members, lay, yb in (('out%s_p' % ch, ((c0, 'inp'), (c1, 'inn')), 'M4', 3.2),
                                      ('out%s_n' % ch, ((c0, 'inn'), (c1, 'inp')), 'M2', 2.4)):
            xs = []
            for c, pn in members:
                r = CM['pins'][pn]
                xp = XC0 + WC * c + (r[0] + r[2]) / 2
                xs.append(xp)
                D.box('M3', xp - 0.15, yb - 0.15, xp + 0.15, YC0 + r[3])
                if lay == 'M4':
                    D.via('Via3', xp, yb, lo=None, hi='s')
                else:
                    D.via('Via2', xp, yb, lo='s', hi=None)
            D.box(lay, min(xs) - 0.15, yb - 0.15, max(xs) + 0.15, yb + 0.15)
            # pin stub: outX_p (Metal4) between inp and inn of the first comparator (clear of its ibias pin);
            # outX_n (Metal2) west of the inn pin
            xpin = min(xs) + 1.6 if lay == 'M4' else min(xs) - 1.2
            D.box(lay, min(xpin, min(xs)) - 0.15, yb - 0.15, max(xpin, min(xs)), yb + 0.15)
            if lay == 'M4':
                D.via('Via3', xpin, yb, lo='s', hi=None)
            else:
                D.via('Via2', xpin, yb, lo='s', hi='s')
            D.box('M3', xpin - 0.15, 0.0, xpin + 0.15, yb + 0.15)
            D.pin('M3', xpin - 0.15, 0.0, xpin + 0.15, 1.0, net)
else:
    for m, c, pn in REFS:
        xo = MUXX[m] + MM['x_out']
        D.label('M2txt', xo, YB + MM['y_out_bottom'] + 0.1, '%s_%s' % (['OCa', 'NGa', 'OCb', 'NGb'][c], pn))

# ring -> vss trunks (west and east), about every 20 um, clear of the other trunk vias
yy = 3.0
while yy < H - 3.0:
    if all(abs(yy - b) > 1.5 for b in BUSY_Y):
        for xr, xt in ((GR[0], xv_w), (GR[2], xv_e)):
            D.box('M1', min(xr, xt) - 0.15, yy - 0.15, max(xr, xt) + 0.15, yy + 0.15)
            trunk_stack(xt, yy)
        yy += 20.0
    else:
        yy += 0.5
D.box('prBoundary', 0, 0, W, H)
gds = os.path.join(OUT, 'r1_safe.gds')
write_gds(ly, gds)
meta = {'W': W, 'H': H, 'area_um2': round(W * H, 1), 'with_cmp': WITH_CMP, 'YB': YB, 'XS': XS, 'MUXX': MUXX,
        'YC0': YC0, 'HC': HC, 'XC0': XC0, 'WC': WC, 'pins_top': pins_top}
json.dump(meta, open(os.path.join(OUT, 'r1_safe_layout_meta.json'), 'w'), indent=1)
# LEF abstract: size and the first Metal3 shape of every pin (pins with several shapes keep all rects)
LN = {'M3': 'Metal3', 'M2': 'Metal2', 'M4': 'Metal4'}
with open(os.path.join(OUT, 'r1_safe.lef'), 'w') as f:
    f.write('VERSION 5.7 ;\nMACRO r1_safe\n  CLASS BLOCK ;\n  ORIGIN 0 0 ;\n  SIZE %.3f BY %.3f ;\n' % (W, H))
    seen = {}
    for (n, lay, x1, y1, x2, y2) in D.pins:
        seen.setdefault(n, []).append((lay, x1, y1, x2, y2))
    for n, rs in seen.items():
        use = ' USE POWER ;' if n in ('vdda', 'vdd') else (' USE GROUND ;' if n == 'vss' else '')
        f.write('  PIN %s\n    DIRECTION INOUT ;%s\n    PORT\n' % (n, use))
        for (lay, x1, y1, x2, y2) in rs:
            f.write('      LAYER %s ;\n        RECT %.3f %.3f %.3f %.3f ;\n' % (LN[lay], x1, y1, x2, y2))
        f.write('    END\n  END %s\n' % n)
    f.write('END r1_safe\nEND LIBRARY\n')
print('r1_safe layout', W, 'x', H, '=', round(W * H), 'um2', 'cmp' if WITH_CMP else 'no-cmp')
