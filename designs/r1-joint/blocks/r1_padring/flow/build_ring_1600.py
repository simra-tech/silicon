# Build the R1 1600 um pad ring (revision b, empty core) from the 1414 um ring of revision a (before fill).
#   klayout -b -r flow/build_ring_1600.py -rd src=<r1_padring_nofill.gds of ring-20261020-a> \
#           -rd io_gds=<PDK sg13g2_io.gds> -rd out=<ring gds> -rd report=<json>
# Method: the ring is stretched by 186 um at the die centre line (coordinates >= 707 um move by +186 um).
# The 24 IO cells keep their order, type and orientation; pitch 112 -> 140 um, row centred (pad centres
# 450, 590, 730, 870, 1010, 1150 um). Corners, seal ring layers, core power ring and TopVia2 array are mapped
# vertex by vertex. Bondpad cells, bridge shapes, pad squares and pad labels are moved with their pad.
# All IO fillers are deleted and written again so that every gap is filled with PDK filler cells.
import pya, json, hashlib
DBU = 0.001
ly = pya.Layout(); ly.read(src)
T = ly.top_cell()
assert abs(ly.dbu - DBU) < 1e-12 and T.bbox() == pya.Box(0, 0, 1414000, 1414000), T.bbox().to_s()
um = lambda v: int(round(v / DBU))
STRETCH, MID, PITCH0, PITCH1, ORG0, ORG1 = um(186), um(707), um(112), um(140), um(355), um(410)
DIE1 = 1414000 + STRETCH
f = lambda c: c if c < MID else c + STRETCH
# --- pad geometry
def cell_origin_new(i): return ORG1 + PITCH1 * i           # along-side coordinate of IO cell origin, pad index i = 0..5
def centre_new(n):
    i = (n - 1) % 6; a = cell_origin_new(i) + um(40)
    if n <= 6: return (a, um(101))
    if n <= 12: return (DIE1 - um(101), a)
    if n <= 18: return (a, DIE1 - um(101))
    return (um(101), a)
def centre_old(n):
    i = (n - 1) % 6; a = ORG0 + PITCH0 * i + um(40)
    if n <= 6: return (a, um(101))
    if n <= 12: return (1414000 - um(101), a)
    if n <= 18: return (a, 1414000 - um(101))
    return (um(101), a)
def pad_of(x, y):
    """pad number whose old pad zone contains the point (x, y): zone = 180 um deep strip, 112 um wide slot"""
    for n in range(1, 25):
        cx, cy = centre_old(n)
        if n <= 6 or 13 <= n <= 18:
            if abs(x - cx) <= PITCH0 // 2 and abs(y - cy) <= um(90): return n
        else:
            if abs(y - cy) <= PITCH0 // 2 and abs(x - cx) <= um(90): return n
    return None
def delta(n):
    ox, oy = centre_old(n); nx, ny = centre_new(n); return (nx - ox, ny - oy)

PINS = [(1,'VDD'),(2,'VSS'),(3,'IOVDD'),(4,'IOVSS'),(5,'VSS'),(6,'IOVSS'),(7,'VDDA'),(8,'ISA_P'),(9,'ISA_N'),(10,'ISB_P'),(11,'ISB_N'),
        (12,'FAULT_N'),(13,'GATE_A'),(14,'GATE_B'),(15,'GATE_C'),(16,'CS_N'),(17,'MA_SCLK'),(18,'SLO_SDO'),(19,'SDI'),(20,'EN_STO_IN'),
        (21,'SIN_P'),(22,'SIN_N'),(23,'COS_P'),(24,'COS_N')]
rep = {'src': src, 'moved': {}, 'removed': {}}
byname = {c.name: c for c in ly.each_cell()}
# PDK IO filler of 1 um (needed for the odd 89 um gap between a corner and the first IO cell)
iol = pya.Layout(); iol.read(io_gds)
# The copy gets the prefix of the G1 ring copies. A cell named sg13g2_Filler200 makes the PDK LVS add a circuit pair (try 1, 13 NoMatch).
f200 = ly.create_cell('retained_fullchip_sg13g2_Filler200'); f200.copy_tree(iol.cell('sg13g2_Filler200'))
rep['filler200'] = 'copy of PDK sg13g2_io.gds cell sg13g2_Filler200, named retained_fullchip_sg13g2_Filler200 like the other IO filler copies'
fill_cells = {w: byname['retained_fullchip_sg13g2_Filler%d' % k] for w, k in ((20000, 4000), (10000, 2000), (2000, 400))}
fill_cells[1000] = f200
# orientation of the fillers per side (taken from the 1414 ring)
side_trans = {}
for inst in list(T.each_inst()):
    n = inst.cell.name
    if 'sg13g2_Filler' in n:
        t = inst.trans; x, y = t.disp.x, t.disp.y
        s = 'S' if y == 141000 else 'N' if y == 1273000 else 'W' if x == 141000 else 'E'
        side_trans[s] = t.dup(); inst.delete()
assert sorted(side_trans) == ['E', 'N', 'S', 'W'], side_trans
rep['filler_orient'] = {k: v.to_s() for k, v in side_trans.items()}

# --- move IO cells, bondpads, corners
for inst in list(T.each_inst()):
    n = inst.cell.name; t = inst.trans; x, y = t.disp.x, t.disp.y
    if n.startswith('retained_fullchip_sg13g2_IOPad'):
        if y == 141000: nd = (cell_origin_new((x - ORG0) // PITCH0), 141000)
        elif x == 1273000: nd = (1273000 + STRETCH, cell_origin_new((y - ORG0) // PITCH0))
        elif y == 1273000: nd = (cell_origin_new((x - ORG0) // PITCH0), 1273000 + STRETCH)
        else: nd = (141000, cell_origin_new((y - ORG0) // PITCH0))
        assert (x - ORG0) % PITCH0 == 0 or (y - ORG0) % PITCH0 == 0
    elif n.startswith('retained_fullchip_bondpad'):
        bb = inst.bbox(); cx, cy = bb.center().x, bb.center().y
        p = pad_of(cx, cy); assert p, (n, t.to_s()); dx, dy = delta(p); nd = (x + dx, y + dy)
    elif n.startswith('retained_fullchip_sg13g2_Corner'):
        nd = (f(x), f(y))
    elif n in ('new_signal_routes', 'bondpad_outward_5um_retained_metal'):
        continue
    else:
        raise SystemExit('unexpected instance ' + n)
    nt = t.dup(); nt.disp = pya.Vector(nd[0], nd[1]); inst.trans = nt
    rep['moved'][n] = rep['moved'].get(n, 0) + 1

# --- new IO fillers: gaps between corner / IO cells / corner on every side, widths 20, 10, 2, 1 um
def tile(a0, a1):
    gap = a1 - a0
    n20, r = divmod(gap, 20000); n10, r = divmod(r, 10000); n2, r = divmod(r, 2000); n1, r = divmod(r, 1000)
    assert r == 0, gap
    seq = [20000] * n20 + [10000] * n10 + [2000] * n2 + [1000] * n1
    if n1 and len(seq) > 2: seq.remove(1000); seq.insert(len(seq) // 2, 1000)   # 1 um piece in the middle of the run
    out = []; a = a0
    for w in seq: out.append((a, w)); a += w
    assert a == a1
    return out
nfill = {}
for s in 'SNWE':
    base = side_trans[s]
    cross = 141000 if s in 'SW' else 1273000 + STRETCH
    spans = [(141000 + 180000, cell_origin_new(0))] + [(cell_origin_new(i) + 80000, cell_origin_new(i + 1)) for i in range(5)] \
            + [(cell_origin_new(5) + 80000, DIE1 - 141000 - 180000)]
    for a0, a1 in spans:
        for a, w in tile(a0, a1):
            c = fill_cells[w]; tt = base.dup()
            tt.disp = pya.Vector(a, cross) if s in 'SN' else pya.Vector(cross, a)
            T.insert(pya.CellInstArray(c.cell_index(), tt))
            nfill[c.name] = nfill.get(c.name, 0) + 1
rep['fillers'] = nfill

# --- vertex map of top shapes (stretch), labels and registration text
def mpoly(p):
    h = pya.Polygon([pya.Point(f(q.x), f(q.y)) for q in p.each_point_hull()])
    for k in range(p.holes()): h.insert_hole([pya.Point(f(q.x), f(q.y)) for q in p.each_point_hole(k)])
    return h
cnt = {}
for li in list(ly.layer_indexes()):
    info = ly.get_info(li); key = '%d/%d' % (info.layer, info.datatype); sh = T.shapes(li)
    for s in list(sh.each()):
        if s.is_text():
            if key == '63/0':
                nt = s.text.dup(); nt.string = nt.string.replace('x=1414.0', 'x=1600.0').replace('y=1414.0', 'y=1600.0').replace('1.999396', '2.560000')
                tr = nt.trans.dup(); tr.disp = pya.Vector(f(nt.x), f(nt.y)); nt.trans = tr
                sh.erase(s); sh.insert(nt)
            else: sh.erase(s)
            continue
        if s.is_box(): nb = pya.Box(f(s.box.left), f(s.box.bottom), f(s.box.right), f(s.box.top)); sh.erase(s); sh.insert(nb)
        else: np_ = mpoly(s.polygon); sh.erase(s); sh.insert(np_)
        cnt[key] = cnt.get(key, 0) + 1
rep['top_mapped'] = cnt
# labels: one per net on the first pad of the net
lbl = T.shapes(ly.layer(134, 25)); seen = set()
for n, net in PINS:
    if net in seen: continue
    seen.add(net); x, y = centre_new(n); lbl.insert(pya.Text(net, pya.Trans(x, y)))
rep['top_labels'] = len(seen)

# --- pad-bound shapes of new_signal_routes and of the bondpad bridge cell: translate with the pad
def move_cell(c):
    k = {}
    for li in list(ly.layer_indexes()):
        info = ly.get_info(li); key = '%d/%d' % (info.layer, info.datatype); sh = c.shapes(li)
        for s in list(sh.each()):
            if s.is_text(): sh.erase(s); continue
            b = s.bbox()
            if key == '189/4': # boundary
                sh.erase(s); sh.insert(pya.Box(f(b.left), f(b.bottom), f(b.right), f(b.top))); continue
            p = pad_of(b.center().x, b.center().y); assert p, (c.name, key, b.to_s())
            dx, dy = delta(p); s.transform(pya.Trans(dx, dy)); k[key] = k.get(key, 0) + 1
    return k
rep['nsr_moved'] = move_cell(byname['new_signal_routes'])
rep['bridge_moved'] = move_cell(byname['bondpad_outward_5um_retained_metal'])
nl = byname['new_signal_routes'].shapes(ly.layer(134, 25))
for n, net in PINS:
    x, y = centre_new(n); nl.insert(pya.Text(net, pya.Trans(x, y)))
rep['cells'] = ly.cells()
T.name = 'r1_padring'
for _ in range(20):
    orphans = [c for c in ly.each_cell() if c.cell_index() != T.cell_index() and c.parent_cells() == 0]
    if not orphans: break
    for c in orphans: ly.delete_cell(c.cell_index())
rep['cells'] = ly.cells(); rep['top'] = T.name
rep['bbox_um'] = [T.bbox().p1.x * DBU, T.bbox().p1.y * DBU, T.bbox().p2.x * DBU, T.bbox().p2.y * DBU]
opt = pya.SaveLayoutOptions(); opt.format = 'GDS2'; opt.gds2_write_timestamps = False; opt.gds2_write_cell_properties = False
ly.write(out, opt)
rep['out'] = out; rep['out_sha256'] = hashlib.sha256(open(out, 'rb').read()).hexdigest()
json.dump(rep, open(report, 'w'), indent=1, sort_keys=True, default=str)
print(json.dumps(rep, indent=1, default=str))
