#!/usr/bin/env python3
"""Per-net top-level routing geometry, wire resistance and an area/perimeter capacitance
cross-check for the labelled nets of the top-interconnect view.

Route shapes are the routing selection of prepare_top_interconnect.py (top cell's own
shapes + routing-only cells), taken unmerged from the fill-free chip; each shape is
assigned to the view net found under it. Wire R per shape = Rs * L/W (rectangle
equivalent from area and perimeter); vias are grouped by merged cut clusters (parallel
cuts), R = Rvia / n per cluster. The per-net sum is an upper bound of any pin-to-pin
path (all segments in series). Area/perimeter C uses the kpex ihp-sg13g2 substrate
table (field over substrate, no shielding, no coupling) as a cross-check only."""
import sys, json, math, collections, hashlib
from pathlib import Path
import klayout.db as kdb
nofill, view, tech, out = sys.argv[1:5]
T = json.load(open(tech))['process_parasitics']
RS = {r['layer_name']: r['resistance']/1000.0 for r in T['resistance']['layers']}       # ohm/sq
RV = {v['via_name']: v['resistance']/1000.0 for v in T['resistance']['vias']}           # ohm/cut
CS = {s['layer_name']: (s['area_capacitance'], s['perimeter_capacitance']) for s in T['capacitance']['substrates']}  # aF/um2, aF/um
METALS = {8: 'Metal1', 10: 'Metal2', 30: 'Metal3', 50: 'Metal4', 67: 'Metal5', 126: 'TopMetal1', 134: 'TopMetal2'}
VIAS = {19: ('Via1', 8, 10), 29: ('Via2', 10, 30), 49: ('Via3', 30, 50), 66: ('Via4', 50, 67), 125: ('TopVia1', 67, 126), 133: ('TopVia2', 126, 134)}
ROUTING = ('new_signal_routes', 'bondpad_outward_5um_retained_metal', 'bgr_supply_additive_context_candidate', 'retained_fullchip_bondpad_70x70_tm1')
src = kdb.Layout(); src.read(nofill); top = src.cell('g1_chip_top'); dbu = src.dbu
def route_shapes(l):
    li = src.find_layer(l, 0); res = []
    if li is None: return res
    for s in top.shapes(li).each():
        if not s.is_text(): res.append(s.polygon)
    for inst in top.each_inst():
        if inst.cell.name not in ROUTING: continue
        it = inst.cell.begin_shapes_rec(li)
        while not it.at_end():
            if not it.shape().is_text(): res.append(it.shape().polygon.transformed(inst.cplx_trans * it.trans()))
            it.next()
    return res
v = kdb.Layout(); v.read(view); vt = v.cell('g1_chip_top')
l2n = kdb.LayoutToNetlist(kdb.RecursiveShapeIterator(v, vt, []))
R = {}
for l in METALS:
    R[l] = l2n.make_layer(v.layer(l, 0), 'm%d' % l); l2n.connect(R[l]); l2n.connect(R[l], l2n.make_text_layer(v.layer(l, 25), 't%d' % l))
for l, (n, lo, hi) in VIAS.items():
    R[l] = l2n.make_layer(v.layer(l, 0), 'v%d' % l); l2n.connect(R[l]); l2n.connect(R[l], R[lo]); l2n.connect(R[l], R[hi])
l2n.extract_netlist()
def netname(layer, poly):
    b = poly.bbox(); c = b.center()
    if not poly.inside(c):
        e = next(poly.each_edge()); c = kdb.Point((e.p1.x+e.p2.x)//2, (e.p1.y+e.p2.y)//2)
    n = l2n.probe_net(R[layer], kdb.DPoint(c.x*dbu, c.y*dbu))
    return n.name if (n and n.name) else None
nets = collections.defaultdict(lambda: dict(layers={}, vias={}, R_wire_ohm=0.0, R_via_ohm=0.0, C_area_fF=0.0, C_perim_fF=0.0))
for l, lname in METALS.items():
    for p in route_shapes(l):
        n = netname(l, p)
        if not n: continue
        A = p.area()*dbu*dbu; P = p.perimeter()*dbu
        h = P/2.0; disc = max(h*h - 4*A, 0.0); W = (h - math.sqrt(disc))/2.0; L = h - W
        sq = L/W if W > 0 else 0.0
        d = nets[n]; e = d['layers'].setdefault(lname, dict(shapes=0, area_um2=0.0, perimeter_um=0.0, length_um=0.0, squares=0.0))
        e['shapes'] += 1; e['area_um2'] += A; e['perimeter_um'] += P; e['length_um'] += L; e['squares'] += sq
        d['R_wire_ohm'] += sq*RS[lname]
        ca, cp = CS[lname]; d['C_area_fF'] += A*ca/1000.0; d['C_perim_fF'] += P*cp/1000.0
for l, (vname, lo, hi) in VIAS.items():
    bynet = collections.defaultdict(list)
    for p in route_shapes(l):
        n = netname(lo, p) or netname(hi, p)
        if n: bynet[n].append(p)
    for n, cuts in bynet.items():
        reg = kdb.Region(cuts)
        for cl in reg.sized(200).merged().each():      # cuts within 0.4 um of each other form one parallel array
            k = reg.interacting(kdb.Region(cl)).count()
            d = nets[n]; e = d['vias'].setdefault(vname, dict(arrays=0, cuts=0))
            e['arrays'] += 1; e['cuts'] += k; d['R_via_ohm'] += RV[vname]/k
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
res = dict(inputs={p: sha(p) for p in (nofill, view, tech)}, script_sha256=sha(__file__), sheet_ohm_per_sq=RS, via_ohm_per_cut=RV,
           substrate_aF=CS, nets=nets)
Path(out).write_text(json.dumps(res, indent=1)+'\n'); print(len(nets), 'nets')
