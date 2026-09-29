#!/usr/bin/env python3
"""Pin-to-pin resistor networks of the top-level routing (every labelled net of the
top-interconnect view, the supply nets included), with KLayout's own R extractor
(klayout.pex.RNetExtractor, the engine kpex --mode RC calls; square counting on the
wires, per-cut via R), and the effective resistance between the pins of each net.

Why not kpex --mode RC on the view: the view LVSDB of make_view_lvsdb.py has no circuit
pins or devices, so kpex has no ports to anchor a network on. Here the ports are the
black-box pin shapes of prepare_top_interconnect.py (block macros, level shifters, IO
cells, tie cells, antenna cells). Pin shapes of decap/fill/filler/corner cells are not
ports (their nodes stay internal and are eliminated). Conductor sheet R and via R per cut
are the kpex ihp-sg13g2 tables, converted exactly as kpex's r_extractor does (via: R_cut *
cut_width^2 in ohm*um^2). The network is simplified by KLayout (series/parallel and
internal-node elimination). No rule deck, tech file or model is modified.

Output JSON per view net: ports (name = <CDL instance or cell@xy>:<pin label>), nodes,
resistors, and the effective resistance from a reference port to every other port with
all other ports open (reference = the port of the net's driver instance when one of the
DRIVER instances is on the net, else the first port by name). CDL identity comes from
prepare.json (net fragments '__fragN' keep their suffix)."""
import sys, json, math, collections, hashlib, argparse, time
from pathlib import Path
import klayout.db as kdb
import klayout.pex as klp
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('view'); ap.add_argument('prepare'); ap.add_argument('tech'); ap.add_argument('out')
ap.add_argument('--nets', default='', help='comma list: only these view nets (debug)')
a = ap.parse_args()
t0 = time.time()
T = json.load(open(a.tech))
RS = {r['layer_name']: r['resistance'] / 1000.0 for r in T['process_parasitics']['resistance']['layers']}    # ohm/sq
RV = {v['via_name']: v['resistance'] / 1000.0 for v in T['process_parasitics']['resistance']['vias']}        # ohm/cut
CW = {'Via1': 0.19, 'Via2': 0.19, 'Via3': 0.19, 'Via4': 0.19, 'TopVia1': 0.42, 'TopVia2': 0.9}                 # tech process_stack contact widths (um)
METALS = {8: 'Metal1', 10: 'Metal2', 30: 'Metal3', 50: 'Metal4', 67: 'Metal5', 126: 'TopMetal1', 134: 'TopMetal2'}
VIAS = {19: ('Via1', 8, 10), 29: ('Via2', 10, 30), 49: ('Via3', 30, 50), 66: ('Via4', 50, 67), 125: ('TopVia1', 67, 126), 133: ('TopVia2', 126, 134)}
NOPORT = ('decap', 'fill_', 'Filler', 'Corner')
DRIVER = ('Xi_core_u_digital', 'Xi_core_u_bgr', 'Xi_core_u_sense', 'Xi_core_u_trip', 'Xi_core_u_osc', 'Xi_core_u_gate',
          'Xi_core_u_t2f', 'Xi_core_u_digital_1', 'Xi_core_u_ls_mode', 'Xi_core_u_ls_r4', 'Xi_core_u_ls_en')
v = kdb.Layout(); v.read(a.view); vt = v.cell('g1_chip_top'); dbu = v.dbu
l2n = kdb.LayoutToNetlist(kdb.RecursiveShapeIterator(v, vt, []))
L = {}
for l in METALS:
    L[l] = l2n.make_layer(v.layer(l, 0), 'm%d' % l); l2n.connect(L[l]); l2n.connect(L[l], l2n.make_text_layer(v.layer(l, 25), 't%d' % l))
for l, (n, lo, hi) in VIAS.items():
    L[l] = l2n.make_layer(v.layer(l, 0), 'v%d' % l); l2n.connect(L[l]); l2n.connect(L[l], L[lo]); l2n.connect(L[l], L[hi])
l2n.extract_netlist()
circ = l2n.netlist().top_circuit()
P = json.load(open(a.prepare))
cellmap = P['cellmap']
def inst_name(inst):
    c = inst.split('@')[0]
    return cellmap.get(inst) or cellmap.get(c) or inst
# ports: black-box pin shapes, assigned to the view net under them
ports = collections.defaultdict(list)   # net name -> [(port name, layer, polygon)]
unassigned = 0
for p in P['pins']:
    if any(s in p['inst'] for s in NOPORT):
        continue
    x1, y1, x2, y2 = [float(t) for t in p['bbox_um'].strip('()').replace(';', ',').split(',')]
    box = kdb.DBox(x1, y1, x2, y2).to_itype(dbu)
    n = l2n.probe_net(L[p['layer']], kdb.DPoint((x1 + x2) / 2, (y1 + y2) / 2))
    if not n or not n.name:
        unassigned += 1
        continue
    ports[n.name].append(('%s:%s' % (inst_name(p['inst']), '/'.join(p['labels'])), p['layer'], kdb.Polygon(box)))
tech = klp.RExtractorTech(); tech.skip_simplify = False
for l, ln in METALS.items():
    c = klp.RExtractorTechConductor(); c.layer = l; c.algorithm = klp.Algorithm.SquareCounting; c.resistance = RS[ln]
    c.triangulation_min_b = 0.5; c.triangulation_max_area = 50.0; tech.add_conductor(c)
for l, (vn, lo, hi) in VIAS.items():
    x = klp.RExtractorTechVia(); x.cut_layer = l; x.bottom_conductor = lo; x.top_conductor = hi
    x.resistance = RV[vn] * CW[vn] ** 2; x.merge_distance = 0; tech.add_via(x)
only = set(s for s in a.nets.split(',') if s)
res = collections.OrderedDict()
for net in circ.each_net():
    name = net.name
    if not name or (only and name not in only):
        continue
    regions = {}
    for l in list(METALS) + list(VIAS):
        r = l2n.shapes_of_net(net, L[l], True)
        if not r.is_empty():
            regions[l] = r
    pl = ports.get(name, [])
    if not pl:
        res[name] = dict(ports=[], note='no port on this net'); continue
    pp = collections.defaultdict(list); pidx = collections.defaultdict(list)
    for i, (pn, ly, poly) in enumerate(pl):
        pp[ly].append(poly); pidx[ly].append(pn)
    t1 = time.time()
    rn = klp.RNetExtractor(dbu).extract(tech, regions, {}, dict(pp))
    nodes, idx = [], {}
    for nd in rn.each_node():
        if nd.type() == klp.RNode.PolygonPort:
            nm = pidx[nd.layer()][nd.port_index()]
        else:
            nm = None
        b = nd.location()
        idx[nd.object_id()] = len(nodes)
        nodes.append(dict(port=nm, layer=METALS.get(nd.layer(), VIAS.get(nd.layer(), ('?',))[0]),
                          xy_um=[round((b.left + b.right) / 2, 3), round((b.bottom + b.top) / 2, 3)]))
    els = [[idx[e.a().object_id()], idx[e.b().object_id()], e.resistance()] for e in rn.each_element()]
    # port nodes with the same port name (one pin drawn as several shapes / layers) are one node
    pnames = sorted(set(n['port'] for n in nodes if n['port']))
    # effective R from the reference port (Laplacian solve, other ports open)
    eff, ref = {}, None
    if len(pnames) > 1 and els:
        import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla
        uf = list(range(len(nodes)))
        def f(i):
            while uf[i] != i:
                uf[i] = uf[uf[i]]; i = uf[i]
            return i
        first = {}
        for i, n in enumerate(nodes):
            if n['port']:
                if n['port'] in first: uf[f(i)] = f(first[n['port']])
                else: first[n['port']] = i
        roots = sorted(set(f(i) for i in range(len(nodes)))); rid = {r: k for k, r in enumerate(roots)}
        N = len(roots)
        drv = [p for p in pnames if p.split(':')[0] in DRIVER]
        ref = drv[0] if drv else pnames[0]
        rr = rid[f(first[ref])]
        I, J, V = [], [], []
        for x, y, r in els:
            x, y = rid[f(x)], rid[f(y)]
            if x == y: continue
            g = 1.0 / max(r, 1e-9)
            I += [x, y, x, y]; J += [x, y, y, x]; V += [g, g, -g, -g]
        G = sp.csr_matrix((V, (I, J)), shape=(N, N)).tolil()
        keep = [k for k in range(N) if k != rr]
        Gr = G[keep, :][:, keep].tocsc()
        # connectivity: ports not connected to ref get no value
        ncomp, lab = sp.csgraph.connected_components(G.tocsr(), directed=False)
        for p in pnames:
            k = rid[f(first[p])]
            if p == ref: continue
            if lab[k] != lab[rr]:
                eff[p] = None; continue
            sub = [q for q in keep if lab[q] == lab[rr]]
            pos = {q: m for m, q in enumerate(sub)}
            Gs = G[sub, :][:, sub].tocsc()
            b = np.zeros(len(sub)); b[pos[k]] = 1.0
            vv = sla.spsolve(Gs, b)
            eff[p] = round(float(vv[pos[k]]), 3)
    res[name] = collections.OrderedDict(ports=pnames, reference_port=ref, n_nodes=len(nodes), n_resistors=len(els),
        sum_R_ohm=round(sum(e[2] for e in els), 3), effective_R_ohm=eff, extract_s=round(time.time() - t1, 2),
        nodes=nodes, resistors=[[x, y, round(r, 6)] for x, y, r in els])
    print('%-28s ports %4d nodes %6d R %6d  %.1f s' % (name, len(pnames), len(nodes), len(els), time.time() - t1), flush=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
out = collections.OrderedDict(inputs={Path(p).name: sha(p) for p in (a.view, a.prepare, a.tech)}, script_sha256=sha(__file__),
    klayout=kdb.__version__ if hasattr(kdb, '__version__') else '', sheet_ohm_per_sq=RS, via_ohm_per_cut=RV, via_cut_width_um=CW,
    unassigned_pin_shapes=unassigned, wall_s=round(time.time() - t0, 1), nets=res)
Path(a.out).write_text(json.dumps(out) + '\n'); print(len(res), 'nets; wall %.1f s' % (time.time() - t0))
