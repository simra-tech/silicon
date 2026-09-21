#!/usr/bin/env python3
"""G1_T2F layout generator: temperature-to-frequency converter (relaxation oscillator on two cmim
capacitors, I_PTAT from the bandgap rails, HBT-input comparators, 1.2 V output stage).
Every device is a PDK PCell; the frozen schematic is ../xschem/g1_t2f.spice.

Run inside the pinned container (KLayout 0.30.9, PDK commit 8437402), from the repository root:
  G1_WORKDIR=designs/g1-guardian/blocks/g1_t2f/layout flow/run.sh klayout -b -r g1_t2f_layout.py
Writes g1_t2f.gds (top cell g1_t2f) and g1_t2f.lef next to this script and prints the macro size.

Floorplan (um, origin at the lower-left corner of the macro, boundary W x H):
  y   3..33   C1, C2: two 28 x 28 cmim (bottom plates Metal5 merged, vss; TopMetal1 top plates with a
              tab to a TopVia1 island at the top edge)           | RREF: 10 rppd 0.5 x 24.5 segments
  y  34..50   switch row (HV CMOS row): SW1/D1, SW2/D2 over the capacitor tabs, threshold mux MX1/MX2,
              mode inverter IM
  y  50..55   analog channel (Metal3): vref vth vr nbias isrc cap1 cap2 d1g
  y  54..82   comparator block: tails MT1 MNB MT2, HBT row (dummy QA1 QB1 QB2 QA2 dummy, pitch 6.3,
              merged p+ rings), loads MLA1 MLB1 MLB2 MLA2  | mirror block: cascodes MCO MCR MCB (own
              n-wells) under mirrors MPO MPR MPB
  y  80..84   logic channel (Metal3)
  y  84..97   HV logic row: IC1A IC1B NQ NQN ND1 ND2 IA MLS IC2A IC2B | 1.2 V output: MLPA/B IO1 IO2
Wires: Metal1 inside cells and for rails, Metal2 vertical stubs, Metal3 horizontal tracks; the
capacitors use Metal5/TopMetal1 by construction. Pins: vss (Metal3, west edge), vdd (Metal3, east
edge), pbias pcasc vref mode (Metal2, east edge), en fout (Metal2, north edge), vdd12 (Metal3, north).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t2f_lib import pya, Draw, Mos, Hbt, Row, g, STUB_W, TRACK_W, TRACK_P

HERE = os.path.dirname(os.path.abspath(__file__))
ly = pya.Layout(); ly.dbu = 0.001
top = ly.create_cell('g1_t2f')
D = Draw(ly, top)

W, H = 92.0, 100.4
PINS = {}       # name -> list of (layer, x1, y1, x2, y2) for the LEF
DEBUG_LABELS = os.environ.get('T2F_DEBUG_LABELS', '1') == '1'   # internal net names (extra LVS ports, tolerated by the compare)


def dbg_label(layer, x, y, text):
    if DEBUG_LABELS:
        D.label(layer + 'txt', x, y, text)


def pin(layer, x1, y1, x2, y2, name):
    D.pin(layer, x1, y1, x2, y2, name)
    PINS.setdefault(name, []).append((layer, x1, y1, x2, y2))


# ============================================================ guard ring, vss / vdd buses
RING = (2.2, 2.2, W - 2.2, H - 2.2)
cx1, cy1, cx2, cy2 = D.guard_ring(*RING, w=0.40, m1w=0.60)      # p+ ring, Metal1 0.6 centred at 2.0 / W-2.0
D.label('M1txt', cx1, 30.0, 'vss')
VSS_X = 2.0                       # west vss stripe (Metal3, internal) and south vss bar (Metal3, the pin)
D.box('M3', 0.6, 0.6, 3.0, H - 3.4, 'vss')
D.box('M3', 0.0, 0.0, W, 2.6, 'vss')
pin('M3', 0.0, 0.0, W, 2.6, 'vss')
PINS['vss'].append(('M3', 0.6, 0.6, 3.0, H - 3.4))                      # west stripe, also pin geometry
for y in range(6, int(H) - 6, 8):
    D.via(VSS_X, y, 'M1', 'M3', pad=0.40, net='vss')
for x in range(10, int(W) - 5, 10):
    D.via(x, cy1, 'M1', 'M3', pad=0.40, net='vss')
VDD_X = 87.75                     # east vdd stripe (Metal2, internal) and north vdd bar (Metal3, the pin)
D.box('M2', 87.0, 44.0, 88.5, H - 1.0, 'vdd')
D.box('M3', 0.0, H - 2.6, W, H, 'vdd')
pin('M3', 0.0, H - 2.6, W, H, 'vdd')
for y in (H - 1.6, H - 2.2):
    D.via(VDD_X, y, 'M2', 'M3', pad=0.40, net='vdd')


def rail_to_vdd(y, x_from):
    """Metal1 rail extension from x_from east to the vdd stripe, Via1 there"""
    D.box('M1', x_from, y - 0.30, VDD_X + 0.30, y + 0.30)
    D.via(VDD_X, y, 'M1', 'M2', pad=0.40, net='vdd')


def rail_to_vss_west(y, x_to):
    D.box('M1', cx1 - 0.30, y - 0.30, x_to, y + 0.30)


def east_pin(name, y, x_from, lower):
    """Metal3 pin wire from x_from to the east edge at y; `lower` = layer of the source (Metal1 rail end
    or Metal3 track end, which then just continues)."""
    if lower == 'M1':
        D.via(x_from, y, 'M1', 'M3', pad=0.40, net=name)
    D.box('M3', x_from - 0.20, y - 0.25, W, y + 0.25, name)
    pin('M3', W - 1.6, y - 0.40, W, y + 0.40, name)
    PINS[name].append(('M3', x_from - 0.20, y - 0.25, W, y + 0.25))      # the whole wire is pin geometry


# ============================================================ capacitors C1, C2
CX = {1: 5.0, 2: 35.0}
CY0, CS = 4.0, 28.0
for k, x in CX.items():
    D.pcell('cmim', {'w': '28u', 'l': '28u', 'Calculate': 'C'}, x, CY0)
D.box('M5', CX[1] - 0.6, CY0 - 0.6, CX[2] + CS + 0.6, CY0 + CS + 0.6)      # merged bottom plates (vss)
D.box('M5', VSS_X - 0.5, 16.0, CX[1] - 0.6, 17.0)                          # strap to the vss bus
D.via(VSS_X, 16.5, 'M3', 'M5', pad=0.60, net='vss')
TAB = {1: CX[1] + 14.0, 2: CX[2] + 14.0}         # x of the top-plate tabs (19.0, 49.0)
CAPY = 34.3                                     # y of the TopVia1 islands / cap net entry on Metal3
for k, x in TAB.items():
    D.box('TM1', x - 1.0, CY0 + CS - 0.14, x + 1.0, CAPY + 1.1)            # tab out of the TopMetal1 plate
    D.via(x, CAPY, 'M3', 'TM1', pad=0.90, net=f'cap{k}')                   # M5 island 1.25 above the plate

# ============================================================ RREF: 10 x rppd 0.5/24.5 serpentine
RX, RY, RP, RL, RN = 70.0, 4.0, 1.4, 24.5, 10
for i in range(RN):
    D.pcell('rppd', {'w': '0.5u', 'l': '%gu' % RL, 'b': 0, 'Calculate': 'R'}, RX + i * RP, RY)
for i in range(0, RN, 2):            # top straps (0,1) (2,3) ...
    D.box('M1', RX + i * RP + 0.02, RY + RL + 0.13, RX + (i + 1) * RP + 0.48, RY + RL + 0.43)
for i in range(1, RN - 1, 2):        # bottom straps (1,2) (3,4) ...
    D.box('M1', RX + i * RP + 0.02, RY - 0.43, RX + (i + 1) * RP + 0.48, RY - 0.13)
VR_X = RX + 0.25                     # segment 0 bottom head = vr, riser on Metal2 to the vr track
D.box('M1', RX + 0.02, RY - 0.60, RX + 0.48, RY - 0.13)
D.via(VR_X, RY - 0.45, 'M1', 'M2', pad=0.30, pads={'M2': (STUB_W, 0.30)}, net='vr')
D.box('M1', RX + (RN - 1) * RP + 0.10, cy1, RX + (RN - 1) * RP + 0.40, RY - 0.13)   # last head to the vss ring
dbg_label('M1', RX + 0.25, RY + 12.0, 'vr')

# ============================================================ switch row (HV): SW1/D1, SW2/D2, MX1/MX2, IM
S = Row(D, TAB[1] - 1.03, 38.0, 4.0, 4.0, 'S')          # SWD1 output column exactly at the C1 tab x
S.place('SWD1', 1, 4.0, 4.0, ['vss', 'cap1'], ['isrc', 'cap1'], ['d1g'], 'cap1')
S.x = TAB[2] - 1.03
S.place('SWD2', 1, 4.0, 4.0, ['vss', 'cap2'], ['isrc', 'cap2'], ['d2g'], 'cap2')
S.x = 56.0
mx_n, _ = S.place('MX', 2, 8.0, None, ['vref', 'vth', 'vr'], None, ['moden', 'mode'])
S.x = 60.0
S.inv('IM', 'mode', 'moden')
S.finish()
rail_to_vss_west(S.vss_y, S.x1)
D.box('M1', S.x2, S.vss_y - 0.30, cx2 + 0.30, S.vss_y + 0.30)     # vss rail also east to the ring
rail_to_vdd(S.vdd_y, S.x2)
# lower channel: moden (k=0), mode (k=1) -> mode pin at the east edge
y_moden = S.stubs_to('moden', 0)
y_mode = S.stubs_to('mode', 1, x_ext=[84.0])
# capacitor nets: output column stubs straight down onto the TopVia1 island pads
for k in (1, 2):
    xo, yo, _ = S.pins[f'cap{k}'][0]
    D.stub(xo, yo, CAPY, f'cap{k}')
# analog channel above the switch row
CH = {'vref': 50.5, 'vth': 51.1, 'vr': 51.7, 'nbias': 52.3, 'isrc': 52.9, 'cap1': 53.5, 'cap2': 54.1, 'd1g': 54.7}
for net in ('vref', 'vth', 'vr'):                   # mux strips: stubs up from the strip pads
    for x, yp, lower in S.pins[net]:
        D.stub(x, yp, CH[net], net)
for net in ('isrc',):                                # switch sources (PMOS strips): up
    for x, yp, lower in S.pins[net]:
        D.stub(x, yp, CH[net], net)
for k in (1, 2):                                     # cap nets: same column continues up
    xo, yo, _ = S.pins[f'cap{k}'][0]
    D.stub(xo, yo, CH[f'cap{k}'], f'cap{k}', lower='M2')
xd1, yd1, _ = S.pins['d1g'][0]
D.stub(xd1, yd1, CH['d1g'], 'd1g')                   # d1g: gate up to the analog channel
xd2, yd2, _ = S.pins['d2g'][0]                       # d2g: gate straight up to the logic channel (later)

# ============================================================ comparator block
TY = 55.5                                            # tails Activ bottom
HY = 70.0                                            # HBT emitter centre line
LY = 75.8                                            # loads Activ bottom (nBuLay to n-well 2.2 um: NBL.d)
HX = [9.0 + 6.3 * i for i in range(6)]               # dummy QA1 QB1 QB2 QA2 dummy
Q = {}
Q['D1'] = Hbt(D, 'QD1', HX[0], HY, dummy=True)
Q['A1'] = Hbt(D, 'QA1', HX[1], HY)
Q['B1'] = Hbt(D, 'QB1', HX[2], HY)
Q['B2'] = Hbt(D, 'QB2', HX[3], HY)
Q['A2'] = Hbt(D, 'QA2', HX[4], HY)
Q['D2'] = Hbt(D, 'QD2', HX[5], HY, dummy=True)
D.label('M1txt', HX[0] - 2.9, HY, 'vss')
D.box('M1', cx1 - 0.30, HY - 2.88 - 0.15, HX[0] - 2.9, HY - 2.88 + 0.15)   # ring bottom rail to the vss ring
# emitter straps (tail1, tail2) on Metal2 between the pair emitters
for a, b, net in (('A1', 'B1', 'tail1'), ('B2', 'A2', 'tail2')):
    D.box('M2', Q[a].cx + 0.80, HY - 0.15, Q[b].cx - 0.80, HY + 0.15, net)
    dbg_label('M2', (Q[a].cx + Q[b].cx) / 2, HY, net)
# tails: MT1 under pair 1, MNB between, MT2 under pair 2 (Metal1 vss rail below, nbias gate rail above)
MT1 = Mos(D, 'MT1', 'nmosHV', 20, 2, 2, (Q['A1'].cx + Q['B1'].cx) / 2 - 2.53, TY)
MT2 = Mos(D, 'MT2', 'nmosHV', 20, 2, 2, (Q['B2'].cx + Q['A2'].cx) / 2 - 2.53, TY)
MNB = Mos(D, 'MNB', 'nmosHV', 10, 2, 1, (MT1.x2 + MT2.x - 2.68) / 2, TY)
T_VSS_Y = TY - 1.4
D.tap_strip(MT1.x - 0.6, MT2.x2 + 0.6, TY - 1.6, TY - 1.2, True, m1w=0.60)
rail_to_vss_west(T_VSS_Y, MT1.x - 0.6)
D.box('TGO', MT1.x - 0.6, TY - 0.52, MT2.x2 + 0.6, TY + 10.52)
for dev in (MT1, MNB, MT2):
    for j in range(0, dev.ng + 1, 2):
        dev.strip_to(j, T_VSS_Y)
    for i in range(dev.ng):
        dev.gate_pad(i, 'top')
NBIAS_Y = TY + 10 + 0.40
D.hwire('M1', MT1.gx(0), MT2.gx(1), NBIAS_Y, w=0.30)          # nbias rail over the gate pads
dbg_label('M1', MNB.gx(0), NBIAS_Y, 'nbias')
MNB.strip_to(1, NBIAS_Y)                                      # MNB diode: drain strip up to its gate rail
D.stub(MNB.sx(1), TY + 0.5, CH['nbias'], 'nbias')             # nbias down to the analog channel
for dev, net in ((MT1, 'tail1'), (MT2, 'tail2')):             # tail drains up to the emitter straps
    dev.strip_pad(1, TY + 9.6)
    D.via(dev.sx(1), TY + 9.6, 'M1', 'M2', pad=0.30, pads={'M2': (STUB_W, 0.30)}, net=net)
    D.box('M2', dev.sx(1) - STUB_W / 2, TY + 9.45, dev.sx(1) + STUB_W / 2, HY, net)
# bases: QA -> vth track, QB -> cap tracks
for q, net in (('A1', 'vth'), ('B1', 'cap1'), ('B2', 'cap2'), ('A2', 'vth')):
    D.stub(Q[q].b[0], Q[q].b[1], CH[net], net, lower='M2')
# loads MLA1 MLB1 MLB2 MLA2 (pmosHV 4/1), drain strip over the HBT centre line
LD = {}
for q, name in (('A1', 'MLA1'), ('B1', 'MLB1'), ('B2', 'MLB2'), ('A2', 'MLA2')):
    LD[name] = Mos(D, name, 'pmosHV', 4, 1, 1, Q[q].cx - 1.53, LY)
L_VDD_Y = LY + 4 + 1.4
LX1, LX2 = LD['MLA1'].x - 0.90, LD['MLA2'].x2 + 0.90
D.tap_strip(LX1, LX2, LY + 4 + 1.2, LY + 4 + 1.6, False, m1w=0.60)
D.box('NWell', LX1 - 0.30, LY - 0.62, LX2 + 0.30, LY + 4 + 2.0)
D.box('TGO', LX1 - 0.30, LY - 0.62, LX2 + 0.30, LY + 4 + 0.62)
D.box('pSD', LX1 + 0.42, LY - 0.40, LX2 - 0.42, LY + 4 + 0.40)
rail_to_vdd(L_VDD_Y, LX2)
for name, m in LD.items():
    m.strip_to(0, L_VDD_Y)
    gx, gy = m.gate_pad(0, 'bottom')
    if name.startswith('MLA'):                                # diode load: drain strip down to the gate pad
        m.strip_to(1, gy)
for a, b, net in (('MLA1', 'MLB1', 'oa1'), ('MLA2', 'MLB2', 'oa2')):        # a = diode load
    xs = (LD[a].gx(0), LD[b].gx(0), LD[a].sx(1))
    D.hwire('M1', min(xs), max(xs), LY - 0.40, w=0.30)
    dbg_label('M1', (LD[a].gx(0) + LD[b].gx(0)) / 2, LY - 0.40, net)
# collectors up to the load drains; ob1/ob2 continue up to the logic channel
for q, name, net, cont in (('A1', 'MLA1', 'oa1', False), ('B1', 'MLB1', 'ob1', True),
                           ('B2', 'MLB2', 'ob2', True), ('A2', 'MLA2', 'oa2', False)):
    m = LD[name]
    m.strip_pad(1, LY + 0.5)
    D.via(m.sx(1), LY + 0.5, 'M1', 'M2', pad=0.30, pads={'M2': (STUB_W, 0.30)}, net=net)
    D.box('M2', m.sx(1) - STUB_W / 2, Q[q].c[1], m.sx(1) + STUB_W / 2, LY + 0.65, net)

# ============================================================ mirror block
CY = TY                                              # cascode Activ bottom (same row as the tails)
MY = 68.5                                            # mirror Activ bottom
MCO = Mos(D, 'MCO', 'pmosHV', 10, 4, 1, 49.5, CY)
MCR = Mos(D, 'MCR', 'pmosHV', 20, 4, 2, 57.28, CY)
MCB = Mos(D, 'MCB', 'pmosHV', 10, 4, 1, 69.4, CY)
MPO = Mos(D, 'MPO', 'pmosHV', 10, 4, 1, 52.0, MY)
MPR = Mos(D, 'MPR', 'pmosHV', 20, 4, 2, 57.28, MY)
MPB = Mos(D, 'MPB', 'pmosHV', 10, 4, 1, 66.94, MY)
# cascodes: own n-well each (body = source), n-tap strip at the bottom of the well tied to the source strip
for dev, src, drains, net in ((MCO, 0, [1], 'isrc'), (MCR, 1, [0, 2], 'vr'), (MCB, 0, [1], 'nbias')):
    wx1, wx2 = dev.x - 0.62, dev.x2 + 0.62
    D.box('NWell', wx1, CY - 2.22, wx2, CY + 10.62)
    D.box('TGO', wx1, CY - 2.22, wx2, CY + 10.62)
    D.tap_strip(dev.x + 0.20, dev.x2 - 0.20, CY - 1.60, CY - 1.20, False, m1w=0.40)
    D.box('M1', min(dev.sx(src), dev.x + 0.20) - 0.08, CY - 1.60, max(dev.sx(src), dev.x + 0.20) + 0.08, CY - 1.20)
    dev.strip_to(src, CY - 1.40)
    for i in range(dev.ng):
        dev.gate_pad(i, 'top')
    dev.strip_pad(src, CY + 9.6)                                     # source: up to the link
    for j in drains:                                                 # drains: down to the analog channel
        D.stub(dev.sx(j), CY + 0.5, CH[net], net)
PCASC_Y = CY + 10 + 0.40
D.hwire('M1', MCO.gx(0), MCB.gx(0), PCASC_Y, w=0.30)
dbg_label('M1', MCR.gx(0), PCASC_Y, 'pcasc')
# mirrors: one n-well (vdd), sources up to the vdd rail, gates (pbias) on bottom pads
M_VDD_Y = MY + 10 + 1.4
MX1_, MX2_ = MPO.x - 0.90, MPB.x2 + 0.90
D.tap_strip(MX1_, MX2_, MY + 10 + 1.2, MY + 10 + 1.6, False, m1w=0.60)
D.box('NWell', MX1_ - 0.30, MY - 0.62, MX2_ + 0.30, MY + 10 + 2.0)
D.box('TGO', MX1_ - 0.30, MY - 0.62, MX2_ + 0.30, MY + 10 + 0.62)
D.box('pSD', MX1_ + 0.42, MY - 0.40, MX2_ - 0.42, MY + 10 + 0.40)
rail_to_vdd(M_VDD_Y, MX2_)
for dev in (MPO, MPR, MPB):
    for j in range(0, dev.ng + 1, 2):
        dev.strip_to(j, M_VDD_Y)
    for i in range(dev.ng):
        dev.gate_pad(i, 'bottom')
PBIAS_Y = MY - 0.40
D.hwire('M1', MPO.gx(0), MPB.gx(0), PBIAS_Y, w=0.30)
dbg_label('M1', MPR.gx(0), PBIAS_Y, 'pbias')
# links mirror drain -> cascode source: MPO/MCO and MPB/MCB via short Metal3 jogs, MPR/MCR straight
LNK = {'do': 66.6, 'db': 67.2}
for mir, cas, net in ((MPO, MCO, 'do'), (MPB, MCB, 'db')):
    mir.strip_pad(1, MY + 0.4)
    D.stub(mir.sx(1), MY + 0.4, LNK[net], net)
    D.stub(cas.sx(0), CY + 9.6, LNK[net], net)
    D.track(LNK[net], cas.sx(0), mir.sx(1), net)
MPR.strip_pad(1, MY + 0.4)
D.via(MPR.sx(1), MY + 0.4, 'M1', 'M2', pad=0.30, pads={'M2': (STUB_W, 0.30)}, net='dr')
D.via(MCR.sx(1), CY + 9.6, 'M1', 'M2', pad=0.30, pads={'M2': (STUB_W, 0.30)}, net='dr')
D.box('M2', MPR.sx(1) - STUB_W / 2, CY + 9.45, MPR.sx(1) + STUB_W / 2, MY + 0.55, 'dr')
dbg_label('M2', MPR.sx(1), (CY + 10 + MY) / 2, 'dr')
# pbias / pcasc rails east to the pins
for net, y in (('pbias', PBIAS_Y), ('pcasc', PCASC_Y)):
    D.box('M1', MPB.gx(0), y - 0.15, 84.0, y + 0.15)
    east_pin(net, y, 84.0, 'M1')

# ============================================================ analog channel tracks
D.track(CH['vref'], S.pins['vref'][0][0], 84.0, 'vref')
east_pin('vref', CH['vref'], 84.0, 'M3')
east_pin('mode', y_mode, 84.0, 'M3')
D.track(CH['vth'], Q['A1'].cx, S.pins['vth'][0][0], 'vth')
D.track(CH['vr'], MCR.sx(0), VR_X, 'vr')                        # MCR drains, mux, RREF riser
D.box('M2', VR_X - STUB_W / 2, RY - 0.60, VR_X + STUB_W / 2, CH['vr'] + 0.15, 'vr')
D.via(VR_X, CH['vr'], 'M2', 'M3', pad=0.30, pads={'M2': (STUB_W, 0.30)}, net='vr')
D.track(CH['nbias'], MNB.sx(1), MCB.sx(1), 'nbias')
D.track(CH['isrc'], S.pins['isrc'][0][0], MCO.sx(1), 'isrc')
D.track(CH['cap1'], S.pins['cap1'][0][0], Q['B1'].cx, 'cap1')
D.track(CH['cap2'], Q['B2'].cx, S.pins['cap2'][0][0], 'cap2')
FT_D1G = 12.0                                                   # d1g feedthrough column west of QA1
D.track(CH['d1g'], FT_D1G, xd1, 'd1g')
D.via(FT_D1G, CH['d1g'], 'M2', 'M3', pad=0.30, pads={'M2': (STUB_W, 0.30)}, net='d1g')

# ============================================================ HV logic row and 1.2 V output stage
# cell order leaves 0.6 um gaps at x = 21.6 (ob1 riser) and 27.9 (ob2 riser) and 18.94 (en riser)
L = Row(D, 13.02, 86.0, 3.0, 4.0, 'L')
L.inv('IC1A', 'ob1', 'c1')
L.inv('IC1B', 'c1', 'sn', 2.0, 4.0)
L.nand2('ND1', 'qn', 'en', 'd1g')
EN_X = L.x - 0.30
L.nand2('ND2', 'q', 'en', 'd2g')
L.x = Q['B1'].cx + 0.30
L.nand2('NQ', 'sn', 'qn', 'q')
L.nand3('NQN', 'rn', 'q', 'en', 'qn')
L.x = Q['B2'].cx + 0.20
L.inv('IA', 'd2g', 'a')
L.place('MLS', 2, 4.0, None, ['lsa', 'vss', 'lsb'], None, ['a', 'd2g'])
L.inv('IC2A', 'ob2', 'c2')
L.inv('IC2B', 'c2', 'rn', 2.0, 4.0)
L.finish()
rail_to_vss_west(L.vss_y, L.x1)
rail_to_vdd(L.vdd_y, L.x2)
# 1.2 V domain: LV row sharing the vss tap line. The 1.2 V PCells have their S/D strips only 0.34 um
# (l = 0.3) or 0.255 um (l = 0.13) from the gate, so no Metal1 strip may run through the gate-contact
# gap: drains are joined on Metal2 (Via1 inside each Activ) and the gate pads leave sideways on Metal1.
V = Row(D, 40.0, 86.0, 1.0, 2.0, 'V', l=0.13, hv=False)
MLP = Mos(D, 'MLP', 'pmos', 1.0, 0.3, 2, V.x, V.yp)          # MLPA (gate 0 = lsb, drain 0 = lsa), MLPB (gate 1 = lsa, drain 2 = lsb)
V.cells.append(('MLP', None, MLP))
MLP.strip_to(1, V.vdd_y)                                      # shared source to vdd12
for i in range(2):
    D.box('GatPoly', MLP.gx(i) - 0.15, V.y_gate - 0.18, MLP.gx(i) + 0.15, MLP.y - 0.17)
    MLP.gate_contact_at(i, V.y_gate)
M2P = {'M2': (STUB_W, 0.30)}
# lsb: gate 0 pad -> Metal1 in the gap (y_gate .. yc+0.3) east to x_b, Via1, Metal2 up over the Activ to drain 2
X_B = MLP.x2 + 0.40
D.box('M1', MLP.gx(0) - 0.10, V.y_gate, MLP.gx(0) + 0.10, V.yc + 0.45)
D.box('M1', MLP.gx(0) - 0.10, V.yc + 0.15, X_B + 0.15, V.yc + 0.45)
D.via(X_B, V.yc + 0.30, 'M1', 'M2', pad=0.30, pads=M2P, net='lsb')
D.box('M2', X_B - STUB_W / 2, V.yc + 0.15, X_B + STUB_W / 2, MLP.y2 + 0.55, 'lsb')
D.box('M2', MLP.sx(2) - STUB_W / 2, MLP.y2 + 0.25, X_B + STUB_W / 2, MLP.y2 + 0.55, 'lsb')
D.via(MLP.sx(2), MLP.y + 0.25, 'M1', 'M2', pad=0.30, pads=M2P, net='lsb')
D.box('M2', MLP.sx(2) - STUB_W / 2, MLP.y + 0.10, MLP.sx(2) + STUB_W / 2, MLP.y2 + 0.55, 'lsb')
X_LSB = MLP.sx(1)                                             # external lsb stub in the gap under the source column
V.add_pin('lsb', X_LSB, V.yc + 0.30)
# lsa: gate 1 pad -> Metal1 jog east to x_b at y_gate (Via1, stub down); drain 0 -> Metal2 up and west to x_a, stub down
D.box('M1', MLP.gx(1) - 0.10, V.y_gate - 0.10, X_B + 0.15, V.y_gate + 0.10)
V.add_pin('lsa', X_B, V.y_gate)
X_A = V.x0 - 0.80
D.via(MLP.sx(0), MLP.y + 0.25, 'M1', 'M2', pad=0.30, pads=M2P, net='lsa')
D.box('M2', MLP.sx(0) - STUB_W / 2, MLP.y + 0.10, MLP.sx(0) + STUB_W / 2, MLP.y2 + 0.55, 'lsa')
D.box('M2', X_A - STUB_W / 2, MLP.y2 + 0.25, MLP.sx(0) + STUB_W / 2, MLP.y2 + 0.55, 'lsa')
V.add_pin('lsa', X_A, MLP.y2 + 0.40, 'M2')


def lv_inv(name, x, wn, wp, gate_net, out_net):
    """1.2 V inverter: sources to the rails on Metal1, drains joined on Metal2 (Via1 inside each Activ),
    gate pad in the gap. Returns (n, p, x_out) with the output Metal2 vertical at x_out."""
    n = Mos(D, name + 'N', 'nmos', wn, 0.13, 1, x, V.yn)
    p = Mos(D, name + 'P', 'pmos', wp, 0.13, 1, x, V.yp)
    V.cells.append((name, n, p))
    n.strip_to(0, V.vss_y)
    p.strip_to(0, V.vdd_y)
    n.gate_bridge(0, p, pw=0.30)
    n.gate_contact_at(0, V.y_gate)
    xo = n.sx(1)
    D.via(xo, n.y + 0.25, 'M1', 'M2', pad=0.30, pads=M2P, net=out_net)
    D.via(xo, p.y + 0.50, 'M1', 'M2', pad=0.30, pads=M2P, net=out_net)
    D.box('M2', xo - STUB_W / 2, n.y + 0.10, xo + STUB_W / 2, p.y + 0.65, out_net)
    return n, p, xo


IO1N, IO1P, X_FON = lv_inv('IO1', 43.0, 0.5, 1.0, 'lsb', 'fon')
IO2N, IO2P, X_FOUT = lv_inv('IO2', 44.41, 1.0, 2.0, 'fon', 'fout')
V.x = IO2N.x2 + 0.6
V.finish()
D.box('M1', L.x2, L.vss_y - 0.30, cx2 + 0.30, L.vss_y + 0.30)          # shared vss rail east to the ring
# IO1 gate (lsb): Metal1 jog west into the cell gap, Via1, stub down (added to the lsb pins)
X_G1 = IO1N.x - 0.30
D.box('M1', X_G1 - 0.15, V.y_gate - 0.10, IO1N.gx(0), V.y_gate + 0.10)
V.add_pin('lsb', X_G1, V.y_gate)
# fon: IO1 output Metal2 vertical -> Metal2 at yc+0.3 east to the IO2 gate jog (Metal1 west from the gate pad)
X_G2 = IO2N.x - 0.30
D.box('M1', X_G2 - 0.15, V.y_gate - 0.10, IO2N.gx(0), V.y_gate + 0.10)
D.via(X_G2, V.y_gate, 'M1', 'M2', pad=0.30, pads=M2P, net='fon')
D.box('M2', X_G2 - STUB_W / 2, V.y_gate - 0.15, X_G2 + STUB_W / 2, V.yc + 0.45, 'fon')
D.box('M2', X_FON - STUB_W / 2, V.yc + 0.15, X_G2 + STUB_W / 2, V.yc + 0.45, 'fon')
dbg_label('M2', (X_FON + X_G2) / 2, V.yc + 0.30, 'fon')
# fout: IO2 output Metal2 vertical up to y = 94.5, then Metal3 to the east edge
Y_FOUT = 94.5
D.box('M2', X_FOUT - 0.20, IO2P.y + 0.35, X_FOUT + 0.20, Y_FOUT + 0.15, 'fout')
D.via(X_FOUT, Y_FOUT, 'M2', 'M3', pad=0.30, pads={'M2': (0.40, 0.30)}, net='fout')
east_pin('fout', Y_FOUT, X_FOUT, 'M3')
# vdd12: rail east end to a Metal3 pin at the east edge
VDD12_X = V.x2 + 1.0
D.box('M1', V.x2 - 0.30, V.vdd_y - 0.30, VDD12_X + 0.30, V.vdd_y + 0.30)
east_pin('vdd12', V.vdd_y, VDD12_X, 'M1')
dbg_label('M1', VDD12_X - 1.5, V.vdd_y, 'vdd12')

# ---- logic channel: greedy track allocation below the logic row
pins = {}
for row in (L, V):
    for net, lst in row.pins.items():
        pins.setdefault(net, []).extend(lst)
ext = {'ob1': [Q['B1'].cx], 'ob2': [Q['B2'].cx], 'd1g': [FT_D1G], 'd2g': [xd2], 'en': [EN_X]}
order = ['ob1', 'c1', 'sn', 'q', 'qn', 'rn', 'en', 'd1g', 'd2g', 'a', 'lsa', 'lsb', 'ob2', 'c2']
slots = []      # list of lists of (x1, x2)
TRK = {}
for net in order:
    xs = [x for x, _, _ in pins[net]] + ext.get(net, [])
    x1, x2 = min(xs) - 0.3, max(xs) + 0.3
    for k, occ in enumerate(slots):
        if all(x2 + 0.3 < a or x1 - 0.3 > b for a, b in occ):
            occ.append((x1, x2)); TRK[net] = k; break
    else:
        slots.append([(x1, x2)]); TRK[net] = len(slots) - 1
for net in order:
    y = L.track_y(TRK[net])
    for x, yp, lower in pins[net]:
        D.stub(x, yp, y, net, lower)
    xs = [x for x, _, _ in pins[net]] + ext.get(net, [])
    D.track(y, min(xs), max(xs), net)
# risers into the logic channel
for net, x, y_from in (('ob1', Q['B1'].cx, LY + 0.65), ('ob2', Q['B2'].cx, LY + 0.65), ('d1g', FT_D1G, CH['d1g']),
                       ('d2g', xd2, yd2)):
    y = L.track_y(TRK[net])
    D.box('M2', x - STUB_W / 2, y_from - 0.15, x + STUB_W / 2, y + 0.15, net)
    D.via(x, y, 'M2', 'M3', pad=0.30, pads={'M2': (STUB_W, 0.30)}, net=net)
D.via(xd2, yd2, 'M1', 'M2', pad=0.30, pads={'M2': (STUB_W, 0.30)}, net='d2g')
# en: Metal2 riser through the logic row up to y = 97.3, Metal3 to the east edge
y_en = L.track_y(TRK['en'])
Y_EN = 96.9
D.box('M2', EN_X - 0.20, y_en - 0.15, EN_X + 0.20, Y_EN + 0.15, 'en')
D.via(EN_X, y_en, 'M2', 'M3', pad=0.30, pads={'M2': (0.40, 0.30)}, net='en')
D.via(EN_X, Y_EN, 'M2', 'M3', pad=0.30, pads={'M2': (0.40, 0.30)}, net='en')
east_pin('en', Y_EN, EN_X, 'M3')
# vdd north bar down to the logic row vdd rail (Metal2 verticals) and the east stripe
for x in (10.0, 30.0, 60.0, 75.0):
    D.via(x, L.vdd_y, 'M1', 'M2', pad=0.40, net='vdd')
    D.box('M2', x - 0.30, L.vdd_y - 0.20, x + 0.30, H - 1.0, 'vdd')
    D.via(x, H - 1.6, 'M2', 'M3', pad=0.40, net='vdd')

# ============================================================ boundary, checks, output
D.box('prBoundary', 0, 0, W, H)
bad = D.check_overlaps()
print('self-check: %d Metal2/Metal3 proximity issues' % bad)
print('logic channel tracks used:', len(slots), {n: L.track_y(k) for n, k in TRK.items()})
gds = os.path.join(HERE, 'g1_t2f.gds')
ly.write(gds)
print('wrote', gds, 'bbox', top.dbbox(), 'macro %g x %g um' % (W, H))

# ---- LEF
LEFL = {'M1': 'Metal1', 'M2': 'Metal2', 'M3': 'Metal3', 'M4': 'Metal4', 'M5': 'Metal5', 'TM1': 'TopMetal1'}
USE = {'vdd': ('INOUT', 'POWER'), 'vdd12': ('INOUT', 'POWER'), 'vss': ('INOUT', 'GROUND'), 'fout': ('OUTPUT', 'SIGNAL')}
lef = ['VERSION 5.8 ;', 'BUSBITCHARS "[]" ;', 'DIVIDERCHAR "/" ;', 'UNITS', '  DATABASE MICRONS 1000 ;', 'END UNITS', '',
       'MACRO g1_t2f', '  CLASS BLOCK ;', '  ORIGIN 0 0 ;', '  FOREIGN g1_t2f 0 0 ;', '  SIZE %g BY %g ;' % (W, H), '  SYMMETRY X Y ;']
for name in ('vdd', 'vdd12', 'vss', 'pbias', 'pcasc', 'vref', 'en', 'mode', 'fout'):
    d, u = USE.get(name, ('INPUT', 'SIGNAL'))
    lef += ['  PIN %s' % name, '    DIRECTION %s ;' % d, '    USE %s ;' % u]
    for layer, x1, y1, x2, y2 in PINS[name]:
        lef += ['    PORT', '      LAYER %s ;' % LEFL[layer], '        RECT %g %g %g %g ;' % (x1, y1, x2, y2), '    END']
    lef += ['  END %s' % name]
lef += ['  OBS']
for m in ('Metal1', 'Metal2'):
    lef += ['    LAYER %s ;' % m, '      RECT 0 0 %g %g ;' % (W, H)]
lef += ['    LAYER Metal3 ;', '      RECT 3.4 3.0 89.9 %g ;' % (H - 3.0)]         # inside the pin bars / edge stubs
lef += ['    LAYER Metal4 ;', '      RECT 0 0 %g %g ;' % (CX[2] + CS + 3.0, CAPY + 2.5)]
lef += ['    LAYER Metal5 ;', '      RECT 0 0 %g %g ;' % (CX[2] + CS + 3.0, CAPY + 2.5)]
lef += ['    LAYER TopMetal1 ;', '      RECT 0 0 %g %g ;' % (CX[2] + CS + 3.0, CAPY + 2.5), '  END', 'END g1_t2f', '', 'END LIBRARY']
open(os.path.join(HERE, 'g1_t2f.lef'), 'w').write('\n'.join(lef) + '\n')
print('wrote', os.path.join(HERE, 'g1_t2f.lef'))
