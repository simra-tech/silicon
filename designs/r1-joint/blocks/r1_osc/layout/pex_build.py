#!/usr/bin/env python3
"""Build the r1_osc post-layout netlist (RC) from the layout. KLayout batch script, run in the pinned container:

  flow/run.sh klayout -b -r designs/r1-joint/blocks/r1_osc/layout/pex_build.py \
      -rd kpexdir=<kpex 2.5D CC run dir>/r1_osc_pexin__r1_osc -rd gds=<r1_osc_pexin.gds> \
      -rd meta=<r1_osc_layout_meta.json> -rd out=<run dir>

Method: the r1_bgr method (blocks/r1_bgr/layout/pex_build.py), adapted to r1_osc.
  1. Devices, nets and terminal geometry from the LVS database that kpex wrote on the PEX input (pex_input.py: the
     layout without the MIM layers; devices not combined, every layout device with its layout parameters).
  2. Capacitance: kpex 0.3.12 2.5D CC (coupling and ground capacitance between nets, VSUBS -> vss), lumped at the
     net's main node.
  3. Resistance: per net a KLayout RNetExtractor network (klayout.pex, square counting) over Metal1..Metal4 and
     Via1..Via3, sg13g2_typ.itf typical values (Metal1 0.110, Metal2-4 0.088 Ohm/sq, Via1-3 9 Ohm per cut). Every
     device terminal on Metal1 is a polygon port (MOS source/drain strip, resistor head). Vertex ports: each pin
     label (Metal3) and each MIM landing point (Metal4, the Via4 position from the generator meta `caps`).
     Gates, MOS bulk, rppd body and the dpantenna carry no DC current and connect to the net's main node.
  4. The 13 MIM devices (cap_cmim, as in the netlist of record: units of one bit lumped with m = 2^k, CF, CTH) are
     inserted between their landing ports. The Metal5 / TopMetal1 plate joins have no resistance in the netlist.
  5. Every net's main node carries the net name (pins: the pin label point; nets with MIM: the first MIM landing
     point; others: the first device terminal), so the decks can probe x1.va, x1.vth, x1.ca, x1.rstb ...
Not modelled: contact resistance (Cont), Activ / GatPoly wiring resistance, substrate resistance, the plate
capacitance of the MIM plates to the wiring below (MIM layers removed for kpex, see pex_input.py).
Outputs in <out>: r1_osc_pex.spice (full RC), r1_osc_pex_c.spice (wiring R shorted: devices + C),
r1_osc_pex_dev.spice (layout devices with their AS/AD/PS/PD and the MIM only: no wiring R, no wiring C),
r1_osc_pex_rnets.json, pex_build.log.
"""
import json
import os

import pya
import klayout.pex as kp

KDIR = kpexdir   # noqa: F821  (-rd)
GDS = gds        # noqa: F821
OUT = out        # noqa: F821
META = json.load(open(meta))   # noqa: F821
os.makedirs(OUT, exist_ok=True)
log = open(os.path.join(OUT, 'pex_build.log'), 'w')


def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    log.write(s + '\n')


lvs = pya.LayoutVsSchematic()
lvs.read(os.path.join(KDIR, 'r1_osc.lvsdb.gz'))
nl = lvs.netlist()
top = [c for c in nl.each_circuit() if c.name == 'r1_osc'][0]
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

ly = pya.Layout()
ly.read(GDS)
tc = ly.top_cell()
PINPT = {}
for s in tc.shapes(ly.layer(30, 25)).each():
    if s.is_text():
        PINPT.setdefault(s.text_string, s.text.trans.disp)
PIN_ORDER = ['en', 'trim0', 'trim1', 'trim2', 'trim3', 'trim4', 'osc_clk', 'vdd', 'vss']
assert all(p in PINPT for p in PIN_ORDER), PINPT.keys()


def lname(n):     # generator net name -> layout (PEX input) net name
    if n.startswith('XCA.b'):
        return 'ba' + n[-1]
    if n.startswith('XCB.b'):
        return 'bb' + n[-1]
    return n


CAPPT = {}        # net -> list of (x, y) um on Metal4
for name, w, l, m, tn, tp, bn, bp in META['caps']:
    for n, p in ((tn, tp), (bn, bp)):
        lst = CAPPT.setdefault(lname(n), [])
        if tuple(p) not in [tuple(q) for q in lst]:
            lst.append(tuple(p))


def nname(n):
    return n.replace('$', 'n').replace('.', '_')


DEV = list(top.each_device())
NETS = {n.expanded_name(): n for n in top.each_net()}
ports = {}
termport = {}
NO_PORT = {'sg13_lv_pmos': ('G', 'B'), 'sg13_lv_nmos': ('G', 'B'), 'rppd': ('rppd_sub',), 'dpantenna': ('A', 'C')}
m1cache = {}


def net_m1(netname):
    if netname not in m1cache:
        m1cache[netname] = lvs.shapes_of_net(NETS[netname], LAY[1], True).merged()
    return m1cache[netname]


nmiss = 0
for d in DEV:
    cls = d.device_class()
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
        if cls.name == 'rppd':
            bb = bb.enlarged(0, 700)
        cand = (net_m1(nn) & pya.Region(bb)).merged()
        polys = sorted(cand.each(), key=lambda p: -p.area())
        if not polys:
            nmiss += 1
            P('no Metal1 port for', d.expanded_name(), cls.name, t.name, nn)
            continue
        dc = pya.Region(polys[0]).decompose_convex()
        pieces = [x.polygon if hasattr(x, 'polygon') else x for x in (dc.each() if hasattr(dc, 'each') else dc)]
        pp = sorted(pieces, key=lambda p: -p.area())[0]
        lst = ports.setdefault(nn, [])
        for i, q in enumerate(lst):
            if q == pp:
                termport[(d.id(), t.id())] = (nn, i)
                break
        else:
            lst.append(pp)
            termport[(d.id(), t.id())] = (nn, len(lst) - 1)
P('devices', len(DEV), 'nets', len(NETS), 'terminal ports', len(termport), 'terminals without Metal1 port', nmiss)

RNET = {}
STAT = dict(open=0, neg=0, neg_min=0.0, floor=0)
lines_r = []
mainnode = {}
capnode = {}      # (net, (x, y)) -> node name
nshort = 0
for nn, net in NETS.items():
    vports = {}
    vlist = []    # (layer, index, kind, key)
    if nn in PIN_ORDER:
        vports[3] = [PINPT[nn]]
        vlist.append((3, 0, 'pin', None))
    if nn in CAPPT:
        vports[4] = [pya.Point(int(round(x * 1000)), int(round(y * 1000))) for x, y in CAPPT[nn]]
        for i, p in enumerate(CAPPT[nn]):
            vlist.append((4, i, 'cap', p))
    pp = ports.get(nn, [])
    if not pp and not vports:
        mainnode[nn] = nname(nn)
        continue
    geo = {k: lvs.shapes_of_net(net, LAY[k], True).merged() for k in LAY}
    ex = kp.RNetExtractor(DBU)
    rn = ex.extract(tech, geo, vports, {1: pp})
    base = nname(nn)
    vname = {}
    for j, (lay, i, kind, key) in enumerate(vlist):
        vname[(lay, i)] = base if j == 0 else '%s__v%d_%d' % (base, lay, i)
    names = {}
    k_int = 0
    for node in rn.each_node():
        ty = node.type().to_s()
        if ty == 'VertexPort':
            names[node.object_id()] = vname[(node.layer(), node.port_index())]
        elif ty == 'PolygonPort':
            i = node.port_index()
            names[node.object_id()] = base if (not vlist and i == 0) else '%s__p%d' % (base, i)
        else:
            names[node.object_id()] = '%s__i%d' % (base, k_int)
            k_int += 1
    main = base
    par = {}

    def f(x):
        while par.get(x, x) != x:
            x = par[x]
        return x
    els = []
    for e in rn.each_element():
        a, b = names[e.a().object_id()], names[e.b().object_id()]
        r0 = e.resistance()
        if r0 != r0 or r0 > 1e12:
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
    want = [(base if (not vlist and i == 0) else '%s__p%d' % (base, i)) for i in range(len(pp))] + list(vname.values())
    for w in want:
        if w not in present or f(w) != f(main):
            els.append((w, main, 1e-3))
            par[f(w)] = f(main)
            nshort += 1
            P('tie', nn, w, '-> main (not connected through Metal1-4)')
    mainnode[nn] = main
    for (lay, i, kind, key) in vlist:
        if kind == 'cap':
            capnode[(nn, tuple(key))] = vname[(lay, i)]
    RNET[nn] = dict(main=main, elements=[[a, b, r] for a, b, r in els], ports=want)
    for a, b, r in els:
        lines_r.append('R%d %s %s %.6g' % (len(lines_r) + 1, a, b, r))
P('resistors', len(lines_r), 'island ties', nshort, 'element stats', STAT)


def tnode(d, t):
    net = d.net_for_terminal(t.id())
    nn = net.expanded_name()
    if (d.id(), t.id()) in termport:
        n2, i = termport[(d.id(), t.id())]
        if not CAPPT.get(n2) and n2 not in PIN_ORDER and i == 0:
            return nname(n2)
        return '%s__p%d' % (nname(n2), i)
    return mainnode.get(nn, nname(nn))


lines_d = []
cnt = {}
for d in DEV:
    cls = d.device_class()
    T = {t.name: t for t in cls.terminal_definitions()}
    par = lambda k: d.parameter(k)
    cnt[cls.name] = cnt.get(cls.name, 0) + 1
    if cls.name in ('sg13_lv_pmos', 'sg13_lv_nmos'):
        lines_d.append('XM%d %s %s %s %s %s w=%gu l=%gu as=%gp ad=%gp ps=%gu pd=%gu ng=1 m=1' % (
            d.id(), tnode(d, T['D']), tnode(d, T['G']), tnode(d, T['S']), tnode(d, T['B']), cls.name,
            par('W'), par('L'), par('AS'), par('AD'), par('PS'), par('PD')))
    elif cls.name == 'rppd':
        lines_d.append('XR%d %s %s %s rppd w=%gu l=%gu m=1 b=0' % (d.id(), tnode(d, T['rppd_1']), tnode(d, T['rppd_2']),
                                                                tnode(d, T['rppd_sub']), par('w'), par('l')))
    elif cls.name == 'dpantenna':
        assert abs(par('A') - 0.6084) < 1e-6
        lines_d.append('XD%d %s %s dpantenna l=0.78u w=0.78u' % (d.id(), tnode(d, T['A']), tnode(d, T['C'])))
    else:
        raise SystemExit('unhandled device class ' + cls.name)
for name, w, l, m, tn, tp, bn, bp in META['caps']:
    a, b = capnode[(lname(tn), tuple(tp))], capnode[(lname(bn), tuple(bp))]
    lines_d.append('XC_%s %s %s cap_cmim w=%gu l=%gu m=%d' % (name.replace('.', '_'), a, b, w, l, m))
    cnt['cap_cmim'] = cnt.get('cap_cmim', 0) + 1
P('device lines', cnt)

lines_c = []
ctot = 0.0
UNIT = {'a': 1e-18, 'f': 1e-15, 'p': 1e-12}
CNET = {}
for line in open(os.path.join(KDIR, 'r1_osc_k25d_pex_netlist.spice')):
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
    CNET[a] = CNET.get(a, 0.0) + val
    CNET[b] = CNET.get(b, 0.0) + val
P('capacitors', len(lines_c), 'total %.1f fF' % (ctot * 1e15))
P('per-net total C (fF):', json.dumps({k: round(v * 1e15, 2) for k, v in sorted(CNET.items())}))

hdr = ['* r1_osc post-layout netlist (RC), written by layout/pex_build.py',
       '* devices: KLayout LVS (PDK deck, via kpex) on the layout without MIM layers, not combined; 13 cap_cmim',
       '* re-inserted at their Via4 landing points; C: kpex 0.3.12 2.5D CC; R: KLayout RNetExtractor, Metal1..Metal4',
       '* + Via1..Via3, sg13g2_typ.itf values; device terminals on Metal1 are separate nodes.',
       '.subckt r1_osc ' + ' '.join(PIN_ORDER)]
with open(os.path.join(OUT, 'r1_osc_pex.spice'), 'w') as fh:
    fh.write('\n'.join(hdr + lines_d + lines_r + lines_c + ['.ends']) + '\n')
lines_r0 = ['R%d %s %s 1e-4' % (i + 1, l.split()[1], l.split()[2]) for i, l in enumerate(lines_r)]
with open(os.path.join(OUT, 'r1_osc_pex_c.spice'), 'w') as fh:
    fh.write('\n'.join(hdr + lines_d + lines_r0 + lines_c + ['.ends']) + '\n')
with open(os.path.join(OUT, 'r1_osc_pex_dev.spice'), 'w') as fh:     # layout devices only (wiring R and C removed)
    fh.write('\n'.join(hdr + lines_d + lines_r0 + ['.ends']) + '\n')
json.dump(dict(rnets=RNET, mainnode=mainnode, capnode={'%s|%s' % k: v for k, v in capnode.items()},
               cnet_fF={k: v * 1e15 for k, v in CNET.items()}),
          open(os.path.join(OUT, 'r1_osc_pex_rnets.json'), 'w'))
P('wrote', os.path.join(OUT, 'r1_osc_pex.spice'))
log.close()
