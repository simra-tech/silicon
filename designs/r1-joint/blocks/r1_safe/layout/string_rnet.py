#!/usr/bin/env python3
"""Extract the metal resistance networks of the r1_safe reference-string nets. KLayout batch script (pinned container):

  flow/run.sh klayout -b -r designs/r1-joint/blocks/r1_safe/layout/string_rnet.py \
      -rd lvsdb=<flat LVS run>/r1_safe_flat.lvsdb -rd gds=<r1_safe_flat.gds> -rd out=<run dir>

Input: a flat LVS database of r1_safe (PDK deck, flat GDS copy, netlists match). Method as r1_bgr/layout/pex_build.py:
KLayout RNetExtractor (klayout.pex, square counting) over Metal1..Metal4 and Via1..Via3 with the PDK typical values
(sg13g2_typ.itf: Metal1 0.110, Metal2-4 0.088 Ohm/sq, Via1-3 9 Ohm per 0.19 um cut). Nets: string nodes t1..t251,
vref (string top) and vss (string bottom). Ports per net:
  - every rppd terminal on the net (Metal1 head next to the terminal): role 'res', with the schematic device name;
  - every hv_nmos source/drain on the net (column-0 multiplexer inputs): role 'tap';
  - the pin label (vref, vss): role 'pin'.
Output: <out>/string_rnet.json (per net: elements [a, b, ohm], ports {node: [role, info]}), string_rnet.log.
Not modelled: contact resistance (inside the rppd model head), Activ/GatPoly wiring, substrate.
"""
import json
import os

import pya
import klayout.pex as kp

OUT = out          # noqa: F821  (-rd)
os.makedirs(OUT, exist_ok=True)
log = open(os.path.join(OUT, 'string_rnet.log'), 'w')


def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    log.write(s + '\n')


lvs = pya.LayoutVsSchematic()
lvs.read(lvsdb)    # noqa: F821
nl = lvs.netlist()
top = [c for c in nl.each_circuit() if c.name.lower() in ('r1_safe', 'r1_safe_flat')][0]
DBU = 0.001
COND = {1: ('metal1_con', 0.110), 2: ('metal2_con', 0.088), 3: ('metal3_con', 0.088), 4: ('metal4_con', 0.088)}
VIAS = {11: ('via1_drw', 1, 2), 12: ('via2_drw', 2, 3), 13: ('via3_drw', 3, 4)}
RVIA = 9.0 * 0.19 * 0.19
GDSL = {1: (8, 0), 2: (10, 0), 3: (30, 0), 4: (50, 0), 11: (19, 0), 12: (29, 0), 13: (49, 0)}
LAY = {}     # filled after the nets are known: the PDK deck database has no layer names, so map by geometry
tech = kp.RExtractorTech()
for k, (_, rs) in COND.items():
    c = kp.RExtractorTechConductor()
    c.layer, c.resistance, c.algorithm = k, rs, kp.Algorithm.SquareCounting
    c.triangulation_max_area, c.triangulation_min_b = 4.0, 0.3
    tech.add_conductor(c)
for k, (_, b, t) in VIAS.items():
    v = kp.RExtractorTechVia()
    v.cut_layer, v.bottom_conductor, v.top_conductor, v.resistance, v.merge_distance = k, b, t, RVIA, 0.0
    tech.add_via(v)

# schematic names of layout nets and devices
xref = lvs.xref()
NETNAME, DEVNAME = {}, {}
for cp in xref.each_circuit_pair():
    for np_ in xref.each_net_pair(cp):
        if np_.first() and np_.second():
            NETNAME[np_.first().cluster_id] = np_.second().name
    for dp in xref.each_device_pair(cp):
        if dp.first() and dp.second():
            DEVNAME[dp.first().id()] = dp.second().name
WANT = ['t%d' % n for n in range(1, 252)] + ['vref', 'vss']
NETS = {}
for n in top.each_net():
    s = NETNAME.get(n.cluster_id)
    if s and s.lower() in WANT:
        NETS[s.lower()] = n
P('string nets found', len(NETS), 'of', len(WANT))

# map database layers to GDS layers: for the vss net, a database layer is 'k' if its shapes cover the largest area
# inside GDS layer k (each conductor/cut layer of the deck is the drawn layer or a subset of it)
_ly0 = pya.Layout()
_ly0.read(gds)     # noqa: F821
_tc = _ly0.top_cell()
_G = {k: pya.Region(_tc.begin_shapes_rec(_ly0.layer(*v))).merged() for k, v in GDSL.items()}
_cand = {}
for i in lvs.layer_indexes():
    try:
        r = lvs.shapes_of_net(NETS['vss'], lvs.layer_by_index(i), True)
    except Exception:
        continue
    a = r.area()
    if a == 0:
        continue
    for k, g in _G.items():
        if (r - g).area() == 0:
            _cand.setdefault(k, []).append((a, -i, i))
_best, _used = {}, set()
for k in (1, 11, 2, 12, 3, 13, 4):       # stack order; each database layer is used once
    c = sorted([x for x in _cand.get(k, []) if x[2] not in _used], reverse=True)
    if c:
        _best[k] = (c[0][0], c[0][2])
        _used.add(c[0][2])
LAY = {k: lvs.layer_by_index(v[1]) for k, v in _best.items()}
P('layer map', {k: v[1] for k, v in _best.items()})

ly = pya.Layout()
ly.read(gds)       # noqa: F821
PINPT = {}
for s in ly.top_cell().shapes(ly.layer(30, 25)).each():
    if s.is_text():       # reference point: the west-most label of the name (the west edge pin of vref and vss)
        d = s.text.trans.disp
        if s.text_string not in PINPT or d.x < PINPT[s.text_string].x:
            PINPT[s.text_string] = d

m1cache = {}


def net_m1(nn):
    if nn not in m1cache:
        m1cache[nn] = lvs.shapes_of_net(NETS[nn], LAY[1], True).merged()
    return m1cache[nn]


ports, roles = {}, {}
CLSNET = {id(v): k for k, v in NETS.items()}
nmiss = 0
for d in top.each_device():
    cls = d.device_class()
    if cls.name not in ('rppd', 'sg13_hv_nmos'):
        continue
    for t in cls.terminal_definitions():
        if t.name not in ('rppd_1', 'rppd_2', 'S', 'D'):
            continue
        net = d.net_for_terminal(t.id())
        nn = NETNAME.get(net.cluster_id, '').lower() if net else ''
        if nn not in NETS:
            continue
        tref = [tr for tr in net.each_terminal() if tr.device().id() == d.id() and tr.terminal_id() == t.id()][0]
        reg = pya.Region()
        for k, r in lvs.shapes_of_terminal(tref).items():
            reg += r
        bb = reg.bbox().enlarged(700, 700) if cls.name == 'rppd' else reg.bbox()
        polys = sorted((net_m1(nn) & pya.Region(bb)).merged().each(), key=lambda p: -p.area())
        if not polys:
            nmiss += 1
            P('no Metal1 port for', DEVNAME.get(d.id()), t.name, nn)
            continue
        dc = pya.Region(polys[0]).decompose_convex()
        pieces = [x.polygon if hasattr(x, 'polygon') else x for x in (dc.each() if hasattr(dc, 'each') else dc)]
        pp = sorted(pieces, key=lambda p: -p.area())[0]
        lst = ports.setdefault(nn, [])
        role = ('res', '%s:%s' % (DEVNAME.get(d.id()), t.name)) if cls.name == 'rppd' else ('tap', DEVNAME.get(d.id()))
        for i, q in enumerate(lst):
            if q == pp:
                roles[(nn, i)].append(role)
                break
        else:
            lst.append(pp)
            roles[(nn, len(lst) - 1)] = [role]
P('terminal ports', sum(len(v) for v in ports.values()), 'missing', nmiss)

RES = {}
for nn, net in NETS.items():
    vports = {3: [PINPT[nn]]} if nn in ('vref', 'vss') and nn in PINPT else {}
    geo = {k: lvs.shapes_of_net(net, LAY[k], True).merged() for k in LAY}
    rn = kp.RNetExtractor(DBU).extract(tech, geo, vports, {1: ports.get(nn, [])})
    names, k_int, pr = {}, 0, {}
    for node in rn.each_node():
        ty = node.type().to_s()
        if ty == 'VertexPort':
            names[node.object_id()] = nn + '__pin'
            pr[nn + '__pin'] = [['pin', nn]]
        elif ty == 'PolygonPort':
            nm = '%s__p%d' % (nn, node.port_index())
            names[node.object_id()] = nm
            pr[nm] = roles[(nn, node.port_index())]
        else:
            names[node.object_id()] = '%s__i%d' % (nn, k_int)
            k_int += 1
    els = []
    for e in rn.each_element():
        r = e.resistance()
        if r != r or r > 1e12:
            continue
        els.append([names[e.a().object_id()], names[e.b().object_id()], max(r, 1e-4)])
    RES[nn] = dict(elements=els, ports=pr)
P('nets extracted', len(RES), 'elements', sum(len(v['elements']) for v in RES.values()))
json.dump(RES, open(os.path.join(OUT, 'string_rnet.json'), 'w'))
