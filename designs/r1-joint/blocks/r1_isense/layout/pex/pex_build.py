#!/usr/bin/env python3
"""Build the r1_isense_ch post-layout netlist (RC) from the layout (adapted from r1_bgr/layout/pex_build.py, track T7). KLayout batch script, run in the pinned container:

  flow/run.sh klayout -b -r designs/r1-joint/blocks/r1_isense_ch/layout/pex_build.py \
      -rd kpexdir=<kpex 2.5D CC run dir>/r1_isense_ch__r1_isense_ch -rd gds=<r1_isense_ch.gds> -rd out=<run dir>

Method (why: kpex 0.3.12 RC mode leaves every device on the unsplit net node, so device-to-device wiring resistance is
lost - the limitation G1 recorded; Magic finds the devices but leaves every npn13G2 emitter on an isolated node):
  1. Devices, nets and terminal geometry from the LVS database that kpex wrote (KLayout LVS with the PDK deck, devices
     not combined: every layout unit is one device with its layout parameters).
  2. Capacitance: kpex 2.5D CC (coupling and ground capacitance between nets, VSUBS -> vss), lumped at the net's main node.
  3. Resistance: for every net, a KLayout RNetExtractor network (klayout.pex, square counting) over Metal1..Metal4 and
     Via1..Via3 with the PDK typical values (sg13g2_typ.itf: Metal1 0.110, Metal2-4 0.088 Ohm/sq, Via1-3 9 Ohm per
     0.19 um cut). Every device terminal that lands on Metal1 is a polygon port (MOS source/drain strip, HBT emitter
     window, collector and base bars, resistor head) and gets its own node; pins are vertex ports at the pin label.
     Gates, MOS bulk and HBT substrate terminals carry no DC current and connect to the net's main node.
  4. Not modelled: contact (Cont, EmWind) resistance, Activ / GatPoly wiring resistance, substrate resistance.
Outputs in <out>: r1_isense_ch_pex.spice (subckt r1_isense_ch, pins as the netlist of record), r1_isense_ch_pex_rnets.json
(per-net network with port names, for the path-resistance report), pex_build.log.
"""
import json
import os

import pya
import klayout.pex as kp

KDIR = kpexdir   # noqa: F821  (-rd)
CDL = cdl        # noqa: F821  (LVS reference CDL, for the MIM devices)
GDS = gds        # noqa: F821
OUT = out        # noqa: F821
os.makedirs(OUT, exist_ok=True)
log = open(os.path.join(OUT, 'pex_build.log'), 'w')


def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    log.write(s + '\n')


lvs = pya.LayoutVsSchematic()
lvs.read(os.path.join(KDIR, 'r1_isense_ch.lvsdb.gz'))
nl = lvs.netlist()
top = [c for c in nl.each_circuit() if c.name == 'r1_isense_ch'][0]
DBU = 0.001

COND = {1: ('metal1_con', 0.110), 2: ('metal2_con', 0.088), 3: ('metal3_con', 0.088), 4: ('metal4_con', 0.088)}
VIAS = {11: ('via1_drw', 1, 2), 12: ('via2_drw', 2, 3), 13: ('via3_drw', 3, 4)}
RVIA = 9.0 * 0.19 * 0.19      # Ohm * um^2
LAY = {k: lvs.layer_by_name(v[0]) for k, v in COND.items()}
LAY.update({k: lvs.layer_by_name(v[0]) for k, v in VIAS.items()})

tech = kp.RExtractorTech()
for k, (_, rs) in COND.items():
    c = kp.RExtractorTechConductor()
    c.layer = k
    c.resistance = rs
    c.algorithm = kp.Algorithm.SquareCounting
    c.triangulation_max_area = 4.0
    c.triangulation_min_b = 0.3
    tech.add_conductor(c)
for k, (_, b, t) in VIAS.items():
    v = kp.RExtractorTechVia()
    v.cut_layer = k
    v.bottom_conductor = b
    v.top_conductor = t
    v.resistance = RVIA
    v.merge_distance = 0.0
    tech.add_via(v)

# pin label positions (Metal3 text 30/25 in the GDS)
ly = pya.Layout()
ly.read(GDS)
tc = ly.top_cell()
PINPT = {}   # net -> (conductor index, point): channel edge pins on Metal3, supply trunk labels on Metal4
for lay, k in ((30, 3), (50, 4)):
    for s in tc.shapes(ly.layer(lay, 25)).each():
        if s.is_text() and s.text_string in ('isp', 'isn', 'outp', 'outn', 'vref', 'vcm', 'ibias', 'az_lv', 'azh_lv', 'vdda', 'vdd', 'vss'):
            PINPT.setdefault(s.text_string, (k, s.text.trans.disp))
PIN_ORDER = ['isp', 'isn', 'outp', 'outn', 'vref', 'vcm', 'ibias', 'az_lv', 'azh_lv', 'vdda', 'vdd', 'vss']
# MIM devices (removed for kpex, no MIM model): taken from the netlist with their net names (layout labels)
import sys as _s
_s.path.insert(0, os.path.join(os.path.dirname(GDS), '.'))
CAPS = [l.split() for l in open(CDL) if l.startswith('Cx')]


def nname(n):
    return n.replace('$', 'n')


# ---------------------------------------------------------------------------------------------------------------
# ports per net
DEV = list(top.each_device())
NETS = {n.expanded_name(): n for n in top.each_net()}
ports = {}       # net -> list of Polygon (Metal1)
termport = {}    # (device id, terminal id) -> (net, port index) ; missing -> main node
NO_PORT = {'sg13_hv_pmos': ('G', 'B'), 'sg13_hv_nmos': ('G', 'B'), 'sg13_lv_pmos': ('G', 'B'), 'sg13_lv_nmos': ('G', 'B'),
           'npn13G2': ('S',), 'rppd': ('rppd_sub',),
           'rhigh': ('rhigh_sub',)}
m1cache = {}


def net_m1(netname):
    if netname not in m1cache:
        m1cache[netname] = lvs.shapes_of_net(NETS[netname], LAY[1], True).merged()
    return m1cache[netname]


nmiss = 0
for d in DEV:
    cls = d.device_class()
    tnets = {t.name: d.net_for_terminal(t.id()) for t in cls.terminal_definitions()}
    if len({(n.expanded_name() if n else None) for n in tnets.values()}) == 1:
        continue                                  # dummy: every terminal on one net
    for t in cls.terminal_definitions():
        net = d.net_for_terminal(t.id())
        if net is None or t.name in NO_PORT.get(cls.name, ()):
            continue
        nn = net.expanded_name()
        tref = [tr for tr in net.each_terminal() if tr.device().id() == d.id() and tr.terminal_id() == t.id()][0]
        sh = lvs.shapes_of_terminal(tref)
        reg = pya.Region()
        for k, r in sh.items():
            reg += r
        bb = reg.bbox()
        if cls.name in ('rppd', 'rhigh'):        # port line at the body end: take the head Metal1 next to it
            bb = bb.enlarged(0, 700)
        cand = (net_m1(nn) & pya.Region(bb)).merged()
        polys = sorted(cand.each(), key=lambda p: -p.area())
        if not polys:
            nmiss += 1
            P('no Metal1 port for', d.expanded_name(), cls.name, t.name, nn)
            continue
        # port polygon: the largest convex piece of the terminal's Metal1 (convex and inside the conductor)
        dc = pya.Region(polys[0]).decompose_convex()
        pieces = [x.polygon if hasattr(x, 'polygon') else x for x in (dc.each() if hasattr(dc, 'each') else dc)]
        pp = sorted(pieces, key=lambda p: -p.area())[0]
        lst = ports.setdefault(nn, [])
        for i, q in enumerate(lst):              # C=B devices: same Metal1 for both terminals -> same port
            if q == pp:
                termport[(d.id(), t.id())] = (nn, i)
                break
        else:
            lst.append(pp)
            termport[(d.id(), t.id())] = (nn, len(lst) - 1)
P('devices', len(DEV), 'nets', len(NETS), 'terminal ports', len(termport), 'terminals without Metal1 port', nmiss)

# ---------------------------------------------------------------------------------------------------------------
# R networks
RNET = {}
STAT = dict(open=0, neg=0, neg_min=0.0, floor=0)
lines_r = []
mainnode = {}
nshort = 0
for nn, net in NETS.items():
    vports = {}
    pin = nn if nn in PIN_ORDER else None
    if pin and pin in PINPT:
        vports = {PINPT[pin][0]: [PINPT[pin][1]]}
    pp = ports.get(nn, [])
    if not pp and not vports:
        mainnode[nn] = nname(nn)
        continue
    geo = {k: lvs.shapes_of_net(net, LAY[k], True).merged() for k in LAY}
    ex = kp.RNetExtractor(DBU)
    rn = ex.extract(tech, geo, vports, {1: pp})
    names = {}
    k_int = 0
    for node in rn.each_node():
        ty = node.type().to_s()
        if ty == 'VertexPort':
            names[node.object_id()] = nname(nn)                       # the pin
        elif ty == 'PolygonPort':
            names[node.object_id()] = '%s__p%d' % (nname(nn), node.port_index())
        else:
            names[node.object_id()] = '%s__i%d' % (nname(nn), k_int)
            k_int += 1
    if pin:
        main = nname(nn)
    else:
        main = '%s__p0' % nname(nn)
    # connectivity check: every port must reach the main node through the network
    par = {}

    def f(x):
        while par.get(x, x) != x:
            x = par[x]
        return x
    els = []
    for e in rn.each_element():
        a, b = names[e.a().object_id()], names[e.b().object_id()]
        r0 = e.resistance()
        if r0 != r0 or r0 > 1e12:                 # open (degenerate triangle): no element
            STAT['open'] += 1
            continue
        if r0 < 0:
            STAT['neg'] += 1
            STAT['neg_min'] = min(STAT['neg_min'], r0)
        elif r0 < 1e-4:
            STAT['floor'] += 1
        r = max(r0, 1e-4)
        els.append((a, b, r))
        par[f(a)] = f(b)
    present = set(names.values())
    want = ['%s__p%d' % (nname(nn), i) for i in range(len(pp))] + ([nname(nn)] if vports else [])
    for w in want:
        if w not in present or f(w) != f(main):
            els.append((w, main, 1e-3))              # island or missing port: tie to the main node (counted)
            par[f(w)] = f(main)
            nshort += 1
            P('tie', nn, w, '-> main (not connected through Metal1-4)')
    mainnode[nn] = main
    RNET[nn] = dict(main=main, elements=[[a, b, r] for a, b, r in els], ports=want)
    for a, b, r in els:
        lines_r.append('R%d %s %s %.6g' % (len(lines_r) + 1, a, b, r))
P('resistors', len(lines_r), 'island ties', nshort, 'element stats', STAT)

# ---------------------------------------------------------------------------------------------------------------
# devices


def tnode(d, t):
    net = d.net_for_terminal(t.id())
    nn = net.expanded_name()
    if (d.id(), t.id()) in termport:
        n2, i = termport[(d.id(), t.id())]
        return '%s__p%d' % (nname(n2), i)
    return mainnode.get(nn, nname(nn))


lines_d = []
cnt = {}
for d in DEV:
    cls = d.device_class()
    T = {t.name: t for t in cls.terminal_definitions()}
    par = lambda k: d.parameter(k)
    cnt[cls.name] = cnt.get(cls.name, 0) + 1
    if cls.name in ('sg13_hv_pmos', 'sg13_hv_nmos', 'sg13_lv_pmos', 'sg13_lv_nmos'):
        lines_d.append('XM%d %s %s %s %s %s w=%gu l=%gu as=%gp ad=%gp ps=%gu pd=%gu ng=1 m=1' % (
            d.id(), tnode(d, T['D']), tnode(d, T['G']), tnode(d, T['S']), tnode(d, T['B']), cls.name,
            par('W'), par('L'), par('AS'), par('AD'), par('PS'), par('PD')))
    elif cls.name == 'npn13G2':
        lines_d.append('XQ%d %s %s %s %s npn13G2 Nx=%d' % (d.id(), tnode(d, T['C']), tnode(d, T['B']), tnode(d, T['E']),
                                                         tnode(d, T['S']), int(par('Nx'))))
    elif cls.name in ('rppd', 'rhigh'):
        lines_d.append('XR%d %s %s %s %s w=%gu l=%gu m=1 b=0' % (d.id(), tnode(d, T[cls.name + '_1']), tnode(d, T[cls.name + '_2']),
                                                                 tnode(d, T[cls.name + '_sub']), cls.name, par('w'), par('l')))
    else:
        raise SystemExit('unhandled device class ' + cls.name)
for f in CAPS:
    lines_d.append('X%s %s %s cap_cmim %s %s m=1' % (f[0][1:], mainnode.get(f[1], nname(f[1])), mainnode.get(f[2], nname(f[2])), f[4], f[5]))
    cnt['cap_cmim'] = cnt.get('cap_cmim', 0) + 1
P('device lines', cnt)

# ---------------------------------------------------------------------------------------------------------------
# capacitances from kpex 2.5D CC
lines_c = []
ctot = 0.0
UNIT = {'a': 1e-18, 'f': 1e-15, 'p': 1e-12}
for line in open(os.path.join(KDIR, 'r1_isense_ch_k25d_pex_netlist.spice')):
    if not line.startswith('Cext'):
        continue
    f = line.split()
    a, b, v = f[1].replace('\\', ''), f[2].replace('\\', ''), f[3]
    val = float(v[:-1]) * UNIT[v[-1]] if v[-1] in UNIT else float(v)
    a = 'vss' if a == 'VSUBS' else a
    b = 'vss' if b == 'VSUBS' else b
    if a == b:
        continue
    na, nb = mainnode.get(a, nname(a)), mainnode.get(b, nname(b))
    lines_c.append('C%d %s %s %.6g' % (len(lines_c) + 1, na, nb, val))
    ctot += val
P('capacitors', len(lines_c), 'total %.1f fF' % (ctot * 1e15))

hdr = ['* r1_isense_ch post-layout netlist (RC), written by layout/pex_build.py',
       '* devices: KLayout LVS (PDK deck) on the layout, not combined; C: kpex 0.3.12 2.5D CC; R: KLayout RNetExtractor,',
       '* Metal1..Metal4 + Via1..Via3, sg13g2_typ.itf values; device terminals on Metal1 are separate nodes.',
       '.subckt r1_isense_ch ' + ' '.join(PIN_ORDER)]
with open(os.path.join(OUT, 'r1_isense_ch_pex.spice'), 'w') as fh:
    fh.write('\n'.join(hdr + lines_d + lines_r + lines_c + ['.ends']) + '\n')
# R-only (no C) and C-only (no R) variants for attribution
with open(os.path.join(OUT, 'r1_isense_ch_pex_r.spice'), 'w') as fh:
    fh.write('\n'.join(hdr + lines_d + lines_r + ['.ends']) + '\n')
lines_r0 = ['R%d %s %s 1e-4' % (i + 1, l.split()[1], l.split()[2]) for i, l in enumerate(lines_r)]
with open(os.path.join(OUT, 'r1_isense_ch_pex_c.spice'), 'w') as fh:
    fh.write('\n'.join(hdr + lines_d + lines_r0 + lines_c + ['.ends']) + '\n')
# device -> terminal -> node map for the path-resistance report
dmap = {}
for d in DEV:
    cls = d.device_class()
    dmap[str(d.id())] = dict(cls=cls.name, pos=[d.trans.disp.x * DBU, d.trans.disp.y * DBU],
                             t={t.name: [d.net_for_terminal(t.id()).expanded_name(), tnode(d, t)] for t in cls.terminal_definitions()})
json.dump(dict(rnets=RNET, devices=dmap, mainnode=mainnode), open(os.path.join(OUT, 'r1_isense_ch_pex_rnets.json'), 'w'))
P('wrote', os.path.join(OUT, 'r1_isense_ch_pex.spice'))
log.close()
