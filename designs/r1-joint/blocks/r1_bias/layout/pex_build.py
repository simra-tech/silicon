#!/usr/bin/env python3
"""Build the r1_bias post-layout netlist (RC) from the layout. KLayout batch script, run in the pinned container:

  flow/run.sh klayout -b -r designs/r1-joint/blocks/r1_bias/layout/pex_build.py \
      -rd kpexdir=<kpex 2.5D CC run dir>/r1_bias_pexin__r1_bias -rd gds=<r1_bias_pexin.gds> \
      -rd meta=<r1_bias_layout_meta.json> -rd out=<run dir>

Method of r1_bgr (blocks/r1_bgr/layout/pex_build.py) with the MIM handling of r1_osc (blocks/r1_osc/layout):
  1. Devices, nets and terminal geometry from the LVS database that kpex wrote on the PEX input (pex_input.py: the
     layout without the MIM layers; devices not combined, every layout device with its layout parameters). kpex is
     given the LVS CDL without the cap_cmim lines, so the comparison matches and the cross-reference names every
     layout net with its schematic net; the main node of every net carries the hierarchical name of the netlist of
     record (meta `hier`: xpor_xca_tail -> xpor.xca.tail), so that the decks can probe xbias.xpor.gooda as before.
  2. Capacitance: kpex 0.3.12 2.5D CC (coupling and ground capacitance between nets, VSUBS -> vss), lumped at the
     net's main node.
  3. Resistance: per net a KLayout RNetExtractor network (klayout.pex, square counting) over Metal1..Metal4 and
     Via1..Via3, sg13g2_typ.itf typical values (Metal1 0.110, Metal2-4 0.088 Ohm/sq, Via1-3 9 Ohm per cut). Every
     device terminal on Metal1 is a polygon port (MOS source/drain strip, HBT emitter/collector/base bars, resistor
     head; the gates on pbias and pcasc also get a port at their gate-tab pad, for the gate-bus resistance per
     leg). Vertex ports: each pin label (Metal3) and each MIM landing point (Metal4, meta `caps`). Gates, MOS bulk,
     the HBT and resistor substrate terminals carry no DC current and connect to the net's main node (except the
     pbias/pcasc gates above).
  4. The MIM devices (4 in 1d, 6 in revision 2) (cap_cmim) are inserted between their landing ports.
Not modelled: contact resistance (Cont, EmWind), Activ / GatPoly wiring resistance, substrate resistance, the plate
capacitance of the MIM plates to the wiring below (MIM layers removed for kpex).
Outputs in <out>: r1_bias_pex.spice (full RC), r1_bias_pex_c.spice (wiring R set to 10 mOhm: devices + MIM + C;
1e-4 Ohm made the operating point fail, run post-op-20261021-dev1),
r1_bias_pex_dev.spice (layout devices + MIM only: no wiring R, no wiring C), r1_bias_pex_rnets.json, pex_build.log.
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
lvs.read(os.path.join(KDIR, 'r1_bias_pexin.lvsdb.gz') if os.path.exists(os.path.join(KDIR, 'r1_bias_pexin.lvsdb.gz'))
         else [os.path.join(KDIR, f) for f in os.listdir(KDIR) if f.endswith('.lvsdb.gz')][0])
nl = lvs.netlist()
top = [c for c in nl.each_circuit() if c.name.lower() == 'r1_bias'][0]
DBU = 0.001

# layout net -> schematic net name (cross-reference of the kpex LVS run)
L2S = {}
xr = lvs.xref()
nmatch = nother = 0
for cp in xr.each_circuit_pair():
    if not cp.first() or cp.first().name.lower() != 'r1_bias':
        continue
    P('kpex LVS circuit pair status:', cp.status())
    for npair in xr.each_net_pair(cp):
        a, b = npair.first(), npair.second()
        if a and b:
            L2S[a.expanded_name()] = b.expanded_name().lower()
            nmatch += 1
        else:
            nother += 1
P('net pairs named from the cross-reference', nmatch, 'unpaired', nother)
HIER = META['hier']


def sname(lay_net):
    s = L2S.get(lay_net, lay_net)
    return HIER.get(s, s)


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
PIN_ORDER = ['vdda', 'vdd', 'vss', 'pbias', 'pcasc', 'ib_afe_s1', 'ib_afe_s2', 'ib_afe_c1', 'ib_afe_c2', 'ib_is_a',
             'ib_is_b', 'ib_sf_oa', 'ib_sf_na', 'ib_sf_ob', 'ib_sf_nb', 'ib_adc_ref', 'por_n', 'vref', 'vref_b']
assert all(p in PINPT for p in PIN_ORDER), PINPT.keys()
NETS = {n.expanded_name(): n for n in top.each_net()}
assert all(p in NETS for p in PIN_ORDER), [p for p in PIN_ORDER if p not in NETS]

# MIM landing points: probe the layout net on Metal4 at each point
CAPPT = {}        # layout net -> list of (x, y) um on Metal4
CAPS = []
for c in META['caps']:
    ends = []
    for key in ('top', 'bot'):
        x, y = c[key]
        n = lvs.probe_net(LAY[4], pya.DPoint(x, y))
        if n is None:
            raise SystemExit('no Metal4 net at the %s landing of %s' % (key, c['name']))
        nn = n.expanded_name()
        ends.append((nn, (x, y)))
        lst = CAPPT.setdefault(nn, [])
        if (x, y) not in lst:
            lst.append((x, y))
    CAPS.append((c['name'], c['w'], c['l'], ends[0], ends[1]))
    P('cap', c['name'], 'top', sname(ends[0][0]), 'bottom', sname(ends[1][0]))


def nname(n):
    return n.replace('$', 'n')


DEV = list(top.each_device())
ports = {}
termport = {}
NO_PORT = {'sg13_hv_pmos': ('G', 'B'), 'sg13_hv_nmos': ('G', 'B'), 'sg13_lv_pmos': ('G', 'B'), 'sg13_lv_nmos': ('G', 'B'),
           'npn13G2': ('S',), 'rppd': ('rppd_sub',), 'rhigh': ('rhigh_sub',)}
m1cache = {}


def net_m1(netname):
    if netname not in m1cache:
        m1cache[netname] = lvs.shapes_of_net(NETS[netname], LAY[1], True).merged()
    return m1cache[netname]


nmiss = 0
for d in DEV:
    cls = d.device_class()
    tn = {t.name: d.net_for_terminal(t.id()) for t in cls.terminal_definitions()}
    if len({(n.expanded_name() if n else None) for n in tn.values()}) == 1:
        continue
    for t in cls.terminal_definitions():
        net = d.net_for_terminal(t.id())
        if net is None:
            continue
        gate_port = t.name == 'G' and net.expanded_name() in ('pbias', 'pcasc')
        if t.name in NO_PORT.get(cls.name, ()) and not gate_port:
            continue
        nn = net.expanded_name()
        tref = [tr for tr in net.each_terminal() if tr.device().id() == d.id() and tr.terminal_id() == t.id()][0]
        sh = lvs.shapes_of_terminal(tref)
        reg = pya.Region()
        for k, r in sh.items():
            reg += r
        bb = reg.bbox()
        if cls.name in ('rppd', 'rhigh'):
            bb = bb.enlarged(0, 700)
        if gate_port:                            # the gate tab Metal1 pad is 0.45-0.95 um below the Activ
            bb = bb.enlarged(0, 1000)
        cand = (net_m1(nn) & pya.Region(bb)).merged()
        polys = sorted(cand.each(), key=lambda p: -p.area())
        if not polys:
            nmiss += 1
            P('no Metal1 port for', d.expanded_name(), cls.name, t.name, sname(nn))
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
capnode = {}
nshort = 0
for nn, net in NETS.items():
    vports = {}
    vlist = []
    if nn in PIN_ORDER:
        vports[3] = [PINPT[nn]]
        vlist.append((3, 0, 'pin', None))
    if nn in CAPPT:
        vports[4] = [pya.Point(int(round(x * 1000)), int(round(y * 1000))) for x, y in CAPPT[nn]]
        for i, p in enumerate(CAPPT[nn]):
            vlist.append((4, i, 'cap', p))
    pp = ports.get(nn, [])
    base = nname(sname(nn))
    if not pp and not vports:
        mainnode[nn] = base
        continue
    geo = {k: lvs.shapes_of_net(net, LAY[k], True).merged() for k in LAY}
    ex = kp.RNetExtractor(DBU)
    rn = ex.extract(tech, geo, vports, {1: pp})
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
            P('tie', base, w, '-> main (not connected through Metal1-4)')
    mainnode[nn] = main
    for (lay, i, kind, key) in vlist:
        if kind == 'cap':
            capnode[(nn, tuple(key))] = vname[(lay, i)]
    RNET[base] = dict(main=main, elements=[[a, b, r] for a, b, r in els], ports=want)
    for a, b, r in els:
        lines_r.append('R%d %s %s %.6g' % (len(lines_r) + 1, a, b, r))
P('resistors', len(lines_r), 'island ties', nshort, 'element stats', STAT)


def tnode(d, t):
    net = d.net_for_terminal(t.id())
    nn = net.expanded_name()
    if (d.id(), t.id()) in termport:
        n2, i = termport[(d.id(), t.id())]
        if not CAPPT.get(n2) and n2 not in PIN_ORDER and i == 0:
            return nname(sname(n2))
        return '%s__p%d' % (nname(sname(n2)), i)
    return mainnode.get(nn, nname(sname(nn)))


lines_d = []
cnt = {}
dmap = {}
for d in DEV:
    cls = d.device_class()
    T = {t.name: t for t in cls.terminal_definitions()}
    par = lambda k: d.parameter(k)
    cnt[cls.name] = cnt.get(cls.name, 0) + 1
    if cls.name.startswith('sg13_'):
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
    dmap[str(d.id())] = dict(cls=cls.name, pos=[d.trans.disp.x * DBU, d.trans.disp.y * DBU],
                             t={t.name: [sname(d.net_for_terminal(t.id()).expanded_name()), tnode(d, t)]
                                for t in cls.terminal_definitions()},
                             W=par('W') if cls.name.startswith('sg13_') else None)
for name, w, l, (tn, tp), (bn, bp) in CAPS:
    a, b = capnode[(tn, tuple(tp))], capnode[(bn, tuple(bp))]
    lines_d.append('XC_%s %s %s cap_cmim w=%gu l=%gu m=1' % (name.replace('.', '_'), a, b, w, l))
    cnt['cap_cmim'] = cnt.get('cap_cmim', 0) + 1
P('device lines', cnt)

lines_c = []
ctot = 0.0
UNIT = {'a': 1e-18, 'f': 1e-15, 'p': 1e-12}
CNET = {}
cfile = [f for f in os.listdir(KDIR) if f.endswith('_k25d_pex_netlist.spice')][0]
for line in open(os.path.join(KDIR, cfile)):
    if not line.startswith('Cext'):
        continue
    f = line.split()
    a, b, v = f[1].replace('\\', ''), f[2].replace('\\', ''), f[3]
    val = float(v[:-1]) * UNIT[v[-1]] if v[-1] in UNIT else float(v)
    a = 'vss' if a == 'VSUBS' else a
    b = 'vss' if b == 'VSUBS' else b
    if a == b:
        continue
    na, nb = mainnode.get(a, nname(sname(a))), mainnode.get(b, nname(sname(b)))
    lines_c.append('C%d %s %s %.6g' % (len(lines_c) + 1, na, nb, val))
    ctot += val
    CNET[na] = CNET.get(na, 0.0) + val
    CNET[nb] = CNET.get(nb, 0.0) + val
P('capacitors', len(lines_c), 'total %.1f fF' % (ctot * 1e15))
P('per-net total C (fF):', json.dumps({k: round(v * 1e15, 2) for k, v in sorted(CNET.items())}))

hdr = ['* r1_bias post-layout netlist (RC), written by layout/pex_build.py',
       '* devices: KLayout LVS (PDK deck, via kpex) on the layout without MIM layers, not combined; the cap_cmim',
       '* re-inserted at their Via4 landing points; C: kpex 0.3.12 2.5D CC; R: KLayout RNetExtractor, Metal1..Metal4',
       '* + Via1..Via3, sg13g2_typ.itf values; device terminals on Metal1 are separate nodes. Main nodes carry the',
       '* hierarchical names of the netlist of record (xpor.gooda, xl_ib_afe_s1.d).',
       '.subckt r1_bias ' + ' '.join(PIN_ORDER)]
with open(os.path.join(OUT, 'r1_bias_pex.spice'), 'w') as fh:
    fh.write('\n'.join(hdr + lines_d + lines_r + lines_c + ['.ends']) + '\n')
lines_r0 = ['R%d %s %s 1e-2' % (i + 1, l.split()[1], l.split()[2]) for i, l in enumerate(lines_r)]
with open(os.path.join(OUT, 'r1_bias_pex_c.spice'), 'w') as fh:
    fh.write('\n'.join(hdr + lines_d + lines_r0 + lines_c + ['.ends']) + '\n')
with open(os.path.join(OUT, 'r1_bias_pex_dev.spice'), 'w') as fh:
    fh.write('\n'.join(hdr + lines_d + lines_r0 + ['.ends']) + '\n')
json.dump(dict(rnets=RNET, mainnode={k: v for k, v in mainnode.items()}, devices=dmap,
               capnode={'%s|%s' % (k[0], k[1]): v for k, v in capnode.items()},
               cnet_fF={k: v * 1e15 for k, v in CNET.items()}),
          open(os.path.join(OUT, 'r1_bias_pex_rnets.json'), 'w'))
P('wrote', os.path.join(OUT, 'r1_bias_pex.spice'))
log.close()
