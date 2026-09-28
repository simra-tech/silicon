#!/usr/bin/env python3
"""Independent cross-check of supply_mesh_solve.py: effective resistance from the bondpads to each sink group,
extracted with KLayout's own R network extractor (klayout.pex.RNetExtractor, KLayout >= 0.30.2) on the same
geometry JSON (supply_geometry.py). Every bondpad ball area is one polygon port, all pads tied together; the
landing boxes of one sink group are polygon ports tied together (equipotential sink). The port-to-port network is
reduced with scipy; R_eff(group) = resistance between the tied pads and the tied group with all other ports open.
Output: JSON with R_eff per group for the typ sheet/via values of supply_mesh_solve.py.
"""
import argparse, collections, json
from pathlib import Path
import numpy as np
import klayout.db as kdb
import klayout.pex as kp
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--geom', required=True, type=Path); ap.add_argument('--out', required=True, type=Path)
ap.add_argument('--algorithm', default='SquareCounting', choices=('SquareCounting', 'Tesselation'))
ap.add_argument('--max-area', type=float, default=4.0, help='Tesselation max triangle area, um^2')
ap.add_argument('--source-group', default=None)
a = ap.parse_args()
RS = dict(Metal1=0.110, Metal2=0.088, Metal3=0.088, Metal4=0.088, Metal5=0.088, TopMetal1=0.018, TopMetal2=0.011)
RV = dict(Via1=9.0, Via2=9.0, Via3=9.0, Via4=9.0, TopVia1=2.2, TopVia2=1.1)
CUT = dict(Via1=0.19, Via2=0.19, Via3=0.19, Via4=0.19, TopVia1=0.42, TopVia2=0.9)
VIAS = [('Via1', 'Metal1', 'Metal2'), ('Via2', 'Metal2', 'Metal3'), ('Via3', 'Metal3', 'Metal4'), ('Via4', 'Metal4', 'Metal5'),
        ('TopVia1', 'Metal5', 'TopMetal1'), ('TopVia2', 'TopMetal1', 'TopMetal2')]
dbu = 0.001; um = lambda v: int(round(v / dbu))
G = json.loads(a.geom.read_text())
LID = {n: i for i, n in enumerate(list(RS) + list(RV))}
tech = kp.RExtractorTech()
for n, r in RS.items():
    c = kp.RExtractorTechConductor(); c.layer = LID[n]; c.resistance = r
    if a.algorithm == 'Tesselation':
        c.algorithm = kp.RExtractorTechConductor.Tesselation; c.triangulation_max_area = a.max_area
    tech.add_conductor(c)
for v, lo, hi in VIAS:
    t = kp.RExtractorTechVia(); t.cut_layer = LID[v]; t.bottom_conductor = LID[lo]; t.top_conductor = LID[hi]
    t.resistance = RV[v] * CUT[v] ** 2; t.merge_distance = 0; tech.add_via(t)
geo = {}
for n in RS:
    reg = kdb.Region()
    for x1, y1, x2, y2, o in G['layers'].get(n, []): reg.insert(kdb.Box(um(x1), um(y1), um(x2), um(y2)))
    geo[LID[n]] = reg.merged()
for v, lo, hi in VIAS:
    reg = kdb.Region()
    for x, y, k, o in G['vias'].get(v, []):
        h = CUT[v] * k ** 0.5 / 2
        reg.insert(kdb.Box(um(x - h), um(y - h), um(x + h), um(y + h)))
    geo[LID[v]] = reg
ports = collections.defaultdict(list); names = []
for p in G['ports']:
    grp = 'PADS' if p['kind'] == 'pad' else p['group']
    if a.source_group and grp == a.source_group: grp = 'PADS'
    if a.source_group and p['kind'] == 'pad': continue
    x1, y1, x2, y2 = p['box']
    poly = kdb.Polygon(kdb.Box(um(x1), um(y1), um(x2), um(y2)))
    inside = geo[LID[p['layer']]] & kdb.Region(poly)
    if inside.is_empty(): continue
    ports[LID[p['layer']]].append(kdb.Polygon(inside.bbox()))
    names.append((LID[p['layer']], len(ports[LID[p['layer']]]) - 1, grp))
grp_of = {(l, i): g for l, i, g in names}
ex = kp.RNetExtractor(dbu)
net = ex.extract(tech, geo, {}, dict(ports))
# node index: ports merged per group; internal nodes kept
idx = {}; node_grp = {}
def key(nd):
    if str(nd.type()) == 'PolygonPort':
        return 'G:' + grp_of[(nd.layer(), nd.port_index())]
    return 'N:%d' % nd.object_id()
for nd in net.each_node():
    k = key(nd)
    if k not in idx: idx[k] = len(idx)
n = len(idx)
Gm = np.zeros((n, n))
for e in net.each_element():
    i, j = idx[key(e.a())], idx[key(e.b())]
    if i == j or e.resistance() <= 0: continue
    g = 1.0 / e.resistance(); Gm[i, i] += g; Gm[j, j] += g; Gm[i, j] -= g; Gm[j, i] -= g
res = {}
if 'G:PADS' not in idx: raise SystemExit('no pad port')
p0 = idx['G:PADS']; keep = [i for i in range(n) if i != p0]
Gr = Gm[np.ix_(keep, keep)]
for k, i in idx.items():
    if not k.startswith('G:') or k == 'G:PADS': continue
    b = np.zeros(len(keep)); b[keep.index(i)] = 1.0
    try:
        x = np.linalg.solve(Gr, b); res[k[2:]] = float(x[keep.index(i)])
    except np.linalg.LinAlgError:
        res[k[2:]] = None
a.out.write_text(json.dumps(dict(net=G['net'], algorithm=a.algorithm, nodes=n, elements=net.num_elements(), R_eff_ohm=res), indent=1) + '\n')
print(G['net'], a.algorithm, 'nodes', n, 'R_eff', {k: round(v, 4) if v else v for k, v in res.items()})
