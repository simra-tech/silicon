#!/usr/bin/env python3
"""Derive a top-interconnect-only extraction view of the G1 chip.

Kept, flattened into one cell: the top cell's own non-fill shapes and the
routing-only child cells (new_signal_routes and its via cells, the outward
bondpad metal, the BGR supply overlay, the bondpads). Every other child
instance (the block macros, level shifters, IO cells, corner/filler IO cells,
standard cells) is replaced by its own pin shapes only (<layer>/2 moved to
<layer>/0); nothing else inside those cells is kept. Fill (datatype 22) must
already be stripped from the input. A metal/via connectivity pass then maps
every pin to a connected cluster and, through the canonical CDL top subckt,
to its CDL net; one label per cluster carries that name. Opens (one CDL net on
several clusters) and shorts (one cluster on several CDL nets) are reported.
"""
import argparse, hashlib, json, re, collections
from pathlib import Path
import klayout.db as kdb
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input', required=True, type=Path); ap.add_argument('--cdl', required=True, type=Path)
ap.add_argument('--output', required=True, type=Path); ap.add_argument('--report', required=True, type=Path)
a = ap.parse_args()
if a.output.exists() or a.report.exists(): ap.error('refusing to overwrite')
ROUTING = ('new_signal_routes', 'bondpad_outward_5um_retained_metal', 'bgr_supply_additive_context_candidate',
           'retained_fullchip_bondpad_70x70_tm1')
METALS = [(8, 'Metal1'), (10, 'Metal2'), (30, 'Metal3'), (50, 'Metal4'), (67, 'Metal5'), (126, 'TopMetal1'), (134, 'TopMetal2')]
VIAS = [(19, 8, 10), (29, 10, 30), (49, 30, 50), (66, 50, 67), (125, 67, 126), (133, 126, 134)]
TEXT_DT = 25
ly = kdb.Layout(); ly.read(str(a.input)); top = ly.cell('g1_chip_top')
out = kdb.Layout(); out.dbu = ly.dbu; otop = out.create_cell('g1_chip_top')
def olayer(l, d): return out.layer(l, d)
# ---- routing: top own shapes + routing cells (recursive), no texts, no fill
kept = collections.Counter()
for li in ly.layer_indices():
    info = ly.get_info(li)
    if info.datatype in (22, 23, TEXT_DT) or info.layer in (63, 189): continue
    dst = otop.shapes(olayer(info.layer, info.datatype))
    for s in top.shapes(li).each():
        if not s.is_text(): dst.insert(s); kept['top_own:'+info.to_s()] += 1
for inst in top.each_inst():
    if inst.cell.name not in ROUTING: continue
    for li in ly.layer_indices():
        info = ly.get_info(li)
        if info.datatype in (22, 23, TEXT_DT) or info.layer in (63, 189): continue
        it = inst.cell.begin_shapes_rec(li)
        dst = otop.shapes(olayer(info.layer, info.datatype))
        while not it.at_end():
            if not it.shape().is_text():
                dst.insert(it.shape().polygon.transformed(inst.cplx_trans * it.trans())); kept[inst.cell.name+':'+info.to_s()] += 1
            it.next()
# ---- black boxes: pin shapes only
pins = []   # (inst_key, cellname, label, layer, polygon(top coords))
bbcount = collections.Counter()
for idx, inst in enumerate(top.each_inst()):
    c = inst.cell
    if c.name in ROUTING: continue
    arr = [inst.trans] if not inst.is_regular_array() else [inst.cplx_trans * 0 for _ in []]
    assert not inst.is_regular_array()
    key = '%s@%.3f,%.3f' % (c.name, inst.trans.disp.x*ly.dbu, inst.trans.disp.y*ly.dbu)
    for m, _ in METALS:
        pl = ly.find_layer(m, 2); tl = ly.find_layer(m, TEXT_DT)
        if pl is None: continue
        texts = [s.text for s in c.shapes(tl).each() if s.is_text()] if tl is not None else []
        for s in c.shapes(pl).each():
            if s.is_text(): continue
            poly = s.polygon
            lab = [t.string for t in texts if poly.inside(t.trans.disp) or poly.bbox().contains(t.trans.disp)]
            tp = poly.transformed(inst.cplx_trans)
            otop.shapes(olayer(m, 0)).insert(tp); bbcount[c.name] += 1
            pins.append(dict(inst=key, cell=c.name, labels=sorted(set(lab)), layer=m, poly=tp, bbox_um=str(tp.bbox().to_dtype(ly.dbu))))
# ---- connectivity
l2n = kdb.LayoutToNetlist(kdb.RecursiveShapeIterator(out, otop, []))
regs = {}
for m, n in METALS: regs[m] = l2n.make_layer(olayer(m, 0), n); l2n.connect(regs[m])
for v, lo, hi in VIAS:
    regs[v] = l2n.make_layer(olayer(v, 0), 'v%d' % v); l2n.connect(regs[v]); l2n.connect(regs[v], regs[lo]); l2n.connect(regs[v], regs[hi])
l2n.extract_netlist()
nl = l2n.netlist(); ctop = nl.circuit_by_name('g1_chip_top')
def cluster_of(p):
    # probe at a point inside the polygon
    b = p['poly'].bbox(); pt = kdb.DPoint(b.center().x*ly.dbu, b.center().y*ly.dbu)
    if not p['poly'].inside(b.center()):
        for e in p['poly'].each_edge():
            pt = kdb.DPoint((e.p1.x+e.p2.x)/2*ly.dbu, (e.p1.y+e.p2.y)/2*ly.dbu); break
    n = l2n.probe_net(regs[p['layer']], pt)
    return n.cluster_id if n else None
# ---- CDL port mapping
cdl = a.cdl.read_text().replace('\n+', ' ')
ports = {}
for m in re.finditer(r'^\.subckt\s+(\S+)\s+(.*)$', cdl, re.M | re.I): ports[m[1].lower()] = m[2].split()
body = re.search(r'^\.SUBCKT g1_chip_top .*?^\.ENDS', cdl, re.M | re.S | re.I)[0]
insts = {}
for line in body.splitlines()[1:]:
    t = line.split()
    if not t or not t[0].startswith('X') or '/' not in t: continue
    k = t.index('/'); insts[t[0]] = (t[k+1], t[1:k])
# GDS instance -> CDL instance
CELLMAP = {'__rz_port_text_000_retained_g1_digital': 'Xi_core_u_digital', '__rz_port_text_030_g1_sense_candidate': 'Xi_core_u_sense',
  '__rz_port_text_031_g1_bgr_candidate': 'Xi_core_u_bgr', '__rz_port_text_032_retained_g1_osc': 'Xi_core_u_osc',
  '__rz_port_text_033_retained_g1_trip': 'Xi_core_u_trip', '__rz_port_text_037_retained_g1_t2f': 'Xi_core_u_t2f',
  'retained_g1_gate': 'Xi_core_u_gate', 'retained_g1_dose_macro': 'Xi_core_u_dose', 'retained_g1_dut_macro': 'Xi_core_u_dut',
  'retained_fullchip_sg13g2_tiehi': 'Xi_core_u_digital_1'}
# pads: nearest top-level pad label (134/25 in new_signal_routes)
padlabels = []
nsr = ly.cell('new_signal_routes'); tl = ly.find_layer(134, TEXT_DT)
for s in nsr.shapes(tl).each():
    if s.is_text(): padlabels.append((s.text.string, s.text.trans.disp))
padinst = {k: v for k, v in insts.items() if k.startswith('Xpad')}
for inst in top.each_inst():
    if 'IOPad' in inst.cell.name:
        cb = inst.bbox().center()
        best = min(padlabels, key=lambda t: (t[1]-cb).length())
        cands = [k for k in padinst if k.lower().endswith('_'+best[0].lower())]
        key = '%s@%.3f,%.3f' % (inst.cell.name, inst.trans.disp.x*ly.dbu, inst.trans.disp.y*ly.dbu)
        CELLMAP[key] = cands[0] if len(cands) == 1 else None
def cdl_net(p):
    ci = CELLMAP.get(p['inst']) or CELLMAP.get(p['cell'])
    if ci is None: return None
    sub, nets = insts[ci]; pl = [x.lower() for x in ports[sub.lower()]]
    for lab in p['labels']:
        if lab.lower() in pl: return nets[pl.index(lab.lower())]
    return None
# level shifters: identify by what their 'in' pin cluster carries
clusters = collections.defaultdict(list)
for p in pins:
    p['cluster'] = cluster_of(p); clusters[p['cluster']].append(p)
for p in pins:
    p['cdl'] = cdl_net(p)
ls = [k for k, v in insts.items() if v[0] == 'g1_ls_up']
for p in pins:
    if p['cell'] == 'retained_g1_ls_up' and 'in' in p['labels']:
        drv = {q['cdl'] for q in clusters[p['cluster']] if q['cdl']}
        for k in ls:
            if insts[k][1][0] in drv: CELLMAP[p['inst']] = k
for p in pins: p['cdl'] = cdl_net(p)
# antenna diodes: pin A takes the cluster's name (they are not identified individually)
by_cluster = {}
for cid, ps in clusters.items():
    names = sorted({p['cdl'] for p in ps if p['cdl']})
    by_cluster[cid] = names
shorts = {str(c): n for c, n in by_cluster.items() if len(n) > 1}
net_clusters = collections.defaultdict(set)
for c, n in by_cluster.items():
    for x in n: net_clusters[x].add(c)
opens = {n: len(c) for n, c in net_clusters.items() if len(c) > 1}
# labels: one per cluster with a unique CDL name
labelled = {}
for cid, names in by_cluster.items():
    if len(names) != 1 or cid is None: continue
    p = max(clusters[cid], key=lambda q: q['poly'].area())
    nm = names[0]
    if nm in labelled: nm = nm + '__frag%d' % sum(1 for k in labelled if k.startswith(nm))
    b = p['poly'].bbox()
    otop.shapes(olayer(p['layer'], TEXT_DT)).insert(kdb.Text(nm, kdb.Trans(b.center())))
    labelled[nm] = dict(cluster=cid, layer=p['layer'], at_um=[b.center().x*ly.dbu, b.center().y*ly.dbu])
# one isolated substrate tap (Activ/pSD/Cont/Metal1) so the kpex LVS deck has a device and keeps the
# circuit (a device-free layout yields an empty LVSDB); its M1 island is 20 um from any M1 shape
m1all = kdb.Region(otop.begin_shapes_rec(olayer(8, 0)))
um = lambda v: int(round(v/ly.dbu))
tap_at = None
for x, y in [(700, 1000), (1000, 700), (400, 400), (1000, 1000), (700, 700)]:
    probe = kdb.Box(um(x-20), um(y-20), um(x+20), um(y+20))
    if (m1all & kdb.Region(probe)).is_empty(): tap_at = (x, y); break
if tap_at:
    x, y = tap_at
    otop.shapes(olayer(1, 0)).insert(kdb.Box(um(x-1), um(y-1), um(x+1), um(y+1)))
    otop.shapes(olayer(14, 0)).insert(kdb.Box(um(x-1.5), um(y-1.5), um(x+1.5), um(y+1.5)))
    otop.shapes(olayer(6, 0)).insert(kdb.Box(um(x-0.08), um(y-0.08), um(x+0.08), um(y+0.08)))
    otop.shapes(olayer(8, 0)).insert(kdb.Box(um(x-0.5), um(y-0.5), um(x+0.5), um(y+0.5)))
    otop.shapes(olayer(8, TEXT_DT)).insert(kdb.Text('dummy_tap', kdb.Trans(kdb.Point(um(x), um(y)))))
opts = kdb.SaveLayoutOptions(); opts.write_context_info = False
out.write(str(a.output), opts)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rep = dict(input=str(a.input), input_sha256=sha(a.input), cdl=str(a.cdl), cdl_sha256=sha(a.cdl), output=str(a.output),
  output_sha256=sha(a.output), script_sha256=sha(Path(__file__)), klayout=kdb.__version__,
  routing_cells=ROUTING, kept_shapes=dict(kept), blackbox_pin_shapes=dict(bbcount),
  cellmap={k: v for k, v in CELLMAP.items()},
  pins=[dict(inst=p['inst'], labels=p['labels'], layer=p['layer'], bbox_um=p['bbox_um'], cluster=p['cluster'], cdl=p['cdl']) for p in pins],
  dummy_tap_um=tap_at, cluster_names={str(k): v for k, v in by_cluster.items()}, shorts=shorts, opens=opens, labels=labelled)
a.report.write_text(json.dumps(rep, indent=1)+'\n')
print('pins', len(pins), 'clusters', len(clusters), 'labelled', len(labelled))
print('shorts', json.dumps(shorts)); print('opens', json.dumps(opens))
print('unmapped pins', sum(1 for p in pins if p['cdl'] is None))
