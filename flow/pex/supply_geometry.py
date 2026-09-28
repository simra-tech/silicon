#!/usr/bin/env python3
"""Geometry of the top-level supply and pad nets of the G1 chip for the IR-drop / EM analysis.

Input: the fill-free chip GDS (flow/pex/strip_fill.py) and the prepare.json report of
flow/pex/prepare_top_interconnect.py (pin -> CDL net map and one label point per cluster).

Kept, flattened into one cell, with an origin tag:
  route  the top cell's own shapes and the routing-only cells (as prepare_top_interconnect.py)
  io     every metal and via shape of the IO-ring cells (sg13g2 IO pads, corners, IO fillers):
         the ring rails, the supply-pad and analog-pad metal and their via stacks
  pin    only the pin shapes (<layer>/2) of every other cell (block macros, level shifters,
         standard cells); nothing else inside them
A metal/via connectivity pass with the prepare.json label points names the nets. For each
requested net the merged metal of each layer is cut into rectangles (horizontal trapezoid
decomposition; non-rectangular pieces are replaced by their bounding box and counted), the
net's metal is first split by origin (route > io > pin), and every via cut is
listed. Rectangles of different origins abut. Ports: the bond-ball area (40 x 40 um at the bondpad centre, TopMetal2) of every
bondpad on the net, and every pin shape of a block macro or IO cell on the net, grouped by
CDL instance. Output: one JSON per net.
"""
import argparse, collections, hashlib, json, re, time
from pathlib import Path
import klayout.db as kdb
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input', required=True, type=Path); ap.add_argument('--prepare', required=True, type=Path)
ap.add_argument('--nets', required=True, help='comma-separated CDL net names')
ap.add_argument('--outdir', required=True, type=Path)
a = ap.parse_args()
t0 = time.time()
ROUTING = ('new_signal_routes', 'bondpad_outward_5um_retained_metal', 'bgr_supply_additive_context_candidate',
           'retained_fullchip_bondpad_70x70_tm1')
IO_RE = re.compile(r'sg13g2_(IOPad|Corner|Filler)')
METALS = [(8, 'Metal1'), (10, 'Metal2'), (30, 'Metal3'), (50, 'Metal4'), (67, 'Metal5'), (126, 'TopMetal1'), (134, 'TopMetal2')]
VIAS = [(19, 'Via1', 8, 10), (29, 'Via2', 10, 30), (49, 'Via3', 30, 50), (66, 'Via4', 50, 67), (125, 'TopVia1', 67, 126), (133, 'TopVia2', 126, 134)]
CUT_AREA = {'Via1': 0.19**2, 'Via2': 0.19**2, 'Via3': 0.19**2, 'Via4': 0.19**2, 'TopVia1': 0.42**2, 'TopVia2': 0.9**2}
ORIGINS = ('route', 'io', 'pin')
TEXT_DT = 25
nets = a.nets.split(',')
prep = json.loads(a.prepare.read_text())
ly = kdb.Layout(); ly.read(str(a.input)); top = ly.cell('g1_chip_top'); dbu = ly.dbu
um = lambda v: int(round(v / dbu))
out = kdb.Layout(); out.dbu = dbu; otop = out.create_cell('g1_chip_top')
# per (layer, origin) flat regions
R = {(l, o): kdb.Region() for l in [m for m, _ in METALS] + [v[0] for v in VIAS] for o in ORIGINS}
def add_rec(cell, trans, origin, pins_only):
    for l in [m for m, _ in METALS] + [v[0] for v in VIAS]:
        for dt in ((2,) if pins_only else (0, 2)):
            li = ly.find_layer(l, dt)
            if li is None: continue
            it = cell.begin_shapes_rec(li)
            while not it.at_end():
                s = it.shape()
                if not s.is_text() and (s.is_polygon() or s.is_box() or s.is_path()):
                    R[(l, origin)].insert(s.polygon.transformed(trans * it.trans()))
                it.next()
counts = collections.Counter()
# top cell own shapes
for l in [m for m, _ in METALS] + [v[0] for v in VIAS]:
    for dt in (0, 2):
        li = ly.find_layer(l, dt)
        if li is None: continue
        for s in top.shapes(li).each():
            if not s.is_text() and (s.is_polygon() or s.is_box() or s.is_path()): R[(l, 'route')].insert(s.polygon)
for inst in top.each_inst():
    n = inst.cell.name
    if n in ROUTING: add_rec(inst.cell, inst.cplx_trans, 'route', False); counts['route:' + n] += 1
    elif IO_RE.search(n): add_rec(inst.cell, inst.cplx_trans, 'io', False); counts['io:' + n] += 1
    else: add_rec(inst.cell, inst.cplx_trans, 'pin', True); counts['pin:' + n] += 1
# full metal of the block macros (not in the view): where the net's metal overlaps it on the same layer,
# the block draws its current (landing areas; they contain the pin shapes)
STDCELL_RE = re.compile(r'decap|fill_|antenna|tiehi')
macro_metal = []    # (inst key, cell name, {layer: Region})
for inst in top.each_inst():
    n = inst.cell.name
    if n in ROUTING or IO_RE.search(n) or STDCELL_RE.search(n): continue
    mm = {}
    for m, _ in METALS:
        r = kdb.Region()
        for dt in (0, 2):
            li = ly.find_layer(m, dt)
            if li is not None: r.insert(kdb.Region(inst.cell.begin_shapes_rec(li)).transformed(inst.cplx_trans))
        mm[m] = r.merged()
    macro_metal.append(('%s@%.3f,%.3f' % (n, inst.trans.disp.x * dbu, inst.trans.disp.y * dbu), n, mm))
# combined conductor layers (datatype 0) for connectivity
for (l, o), r in R.items():
    r.merge(); otop.shapes(out.layer(l, 0)).insert(r)
# labels of the requested nets (prepare.json: one label point per named cluster, fragments suffixed __fragN)
lab_used = collections.Counter()
for nm, d in prep['labels'].items():
    base = nm.split('__frag')[0]
    if base in nets:
        otop.shapes(out.layer(d['layer'], TEXT_DT)).insert(kdb.Text(base, kdb.Trans(kdb.Point(um(d['at_um'][0]), um(d['at_um'][1])))))
        lab_used[base] += 1
l2n = kdb.LayoutToNetlist(kdb.RecursiveShapeIterator(out, otop, []))
L = {}
for m, n in METALS:
    L[m] = l2n.make_layer(out.layer(m, 0), n); l2n.connect(L[m]); l2n.connect(L[m], l2n.make_text_layer(out.layer(m, TEXT_DT), 't' + n))
for v, n, lo, hi in VIAS:
    L[v] = l2n.make_layer(out.layer(v, 0), n); l2n.connect(L[v]); l2n.connect(L[v], L[lo]); l2n.connect(L[v], L[hi])
l2n.extract_netlist()
ctop = l2n.netlist().circuit_by_name('g1_chip_top')
bynames = collections.defaultdict(list)
for n in ctop.each_net():
    if n.name: bynames[n.name].append(n)
# names on more than one label = a cluster carrying two requested names = short
shorts = [n.name for n in ctop.each_net() if n.name and ',' in n.name]
bondpads = [inst.bbox() for inst in top.each_inst() if inst.cell.name == 'retained_fullchip_bondpad_70x70_tm1']
a.outdir.mkdir(parents=True, exist_ok=True)
summary = dict(input=str(a.input), input_sha256=hashlib.sha256(a.input.read_bytes()).hexdigest(),
               prepare_sha256=hashlib.sha256(a.prepare.read_bytes()).hexdigest(),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), klayout=kdb.__version__,
               instances=dict(counts), labels_used=dict(lab_used), shorts=shorts, nets={})
def parts(reg, layer):
    """Split a net region of one layer into route / io / pin parts (route > io > pin)."""
    seen = kdb.Region(); res = []
    for o in ORIGINS:
        pr = (reg & R[(layer, o)]) - seen; seen += R[(layer, o)]; res.append((o, pr))
    return res
def rects_of(reg, layer):
    res, nonrect = [], 0
    for org, pr in parts(reg, layer):
        for p in pr.each():
            for t in p.decompose_trapezoids(kdb.Polygon.TD_htrapezoids):
                b = t.bbox()
                if t.num_points() != 4 or t.area() != b.area(): nonrect += 1
                res.append([b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu, org])
    return res, nonrect
for name in nets:
    ns = bynames.get(name, [])
    info = dict(l2n_nets=len(ns))
    if not ns:
        summary['nets'][name] = info; continue
    reg = {}
    for l in [m for m, _ in METALS] + [v[0] for v in VIAS]:
        r = kdb.Region()
        for n in ns: r += l2n.shapes_of_net(n, L[l], True)
        reg[l] = r.merged()
    layers, nonrect_total = {}, 0
    for m, mn in METALS:
        rs, nr = rects_of(reg[m], m); layers[mn] = rs; nonrect_total += nr
    vias = {}
    for v, vn, lo, hi in VIAS:
        lst = []
        for org, pr in parts(reg[v], v):
            for p in pr.each():
                c = p.bbox().center(); ar = p.area() * dbu * dbu
                lst.append([c.x * dbu, c.y * dbu, max(1, int(round(ar / CUT_AREA[vn]))), org])
        vias[vn] = lst
    ports = []
    for b in bondpads:
        c = b.center(); pb = kdb.Box(c.x - um(20), c.y - um(20), c.x + um(20), c.y + um(20))
        if not (reg[134] & kdb.Region(pb)).is_empty():
            ports.append(dict(kind='pad', group='bondpad@%.0f,%.0f' % (c.x * dbu, c.y * dbu), layer='TopMetal2',
                              box=[pb.left * dbu, pb.bottom * dbu, pb.right * dbu, pb.top * dbu]))
    cellmap = prep['cellmap']
    # IO cells: their supply pin shapes (the ring rails inside the cell) and pad pins
    for p in prep['pins']:
        if p['cdl'] != name: continue
        cellname = p['inst'].split('@')[0]
        if not IO_RE.search(cellname) or re.search(r'Filler|Corner', cellname): continue
        grp = cellmap.get(p['inst']) or cellmap.get(cellname) or p['inst']
        x1, y1, x2, y2 = map(float, re.findall(r'[-0-9.]+', p['bbox_um']))
        ports.append(dict(kind='sink', group=grp, cell=cellname, labels=p['labels'], layer=dict(METALS)[p['layer']], box=[x1, y1, x2, y2]))
    # block macros: landing areas of the net on the macro's own metal, cut into rectangles
    for key, cellname, mm in macro_metal:
        grp = cellmap.get(key) or cellmap.get(cellname) or key
        for m, mn in METALS:
            land = reg[m] & mm[m]
            for p in land.each():
                for t in p.decompose_trapezoids(kdb.Polygon.TD_htrapezoids):
                    b = t.bbox()
                    ports.append(dict(kind='sink', group=grp, cell=cellname, labels=['landing'], layer=mn,
                                      box=[b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu]))
    info.update(nonrect_pieces=nonrect_total, rects={k: len(v) for k, v in layers.items()},
                cuts={k: sum(c[2] for c in v) for k, v in vias.items()},
                area_um2={dict(METALS)[m]: {o: (reg[m] & R[(m, o)]).area() * dbu * dbu for o in ORIGINS} for m, _ in METALS},
                ports=collections.Counter(p['kind'] + ':' + p['group'] for p in ports))
    summary['nets'][name] = info
    (a.outdir / ('%s.json' % name)).write_text(json.dumps(dict(net=name, layers=layers, vias=vias, ports=ports)) + '\n')
summary['wall_s'] = round(time.time() - t0, 1)
(a.outdir / 'geometry_summary.json').write_text(json.dumps(summary, indent=1) + '\n')
print(json.dumps({k: dict(l2n_nets=v.get('l2n_nets'), rects=v.get('rects'), ports=len(v.get('ports', {}))) for k, v in summary['nets'].items()}, indent=1))
print('shorts', shorts, 'wall', summary['wall_s'])
