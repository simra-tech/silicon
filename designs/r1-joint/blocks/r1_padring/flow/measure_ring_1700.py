# Geometry checks of the 1700 um ring: die/EdgeSeal, IO row continuity (corners, IO cells, fillers abut on every side),
# cell order and orientation against the 1414 ring, core window (IO row inner edge and core power ring inner edge).
#   klayout -b -r flow/measure_ring_1700.py -rd g=<gds> -rd out=<json> [-rd ref=<1414 gds>]
import pya, json, hashlib
DBU = 0.001
ly = pya.Layout(); ly.read(g); T, = ly.top_cells(); res = {'gds': g, 'sha256': hashlib.sha256(open(g, 'rb').read()).hexdigest(), 'top': T.name}
res['bbox_um'] = [T.bbox().p1.x * DBU, T.bbox().p1.y * DBU, T.bbox().p2.x * DBU, T.bbox().p2.y * DBU]
li = ly.find_layer(39, 4); es = [s.bbox() for s in T.shapes(li).each()]
res['edgeseal_39_4_um'] = [[b.left * DBU, b.bottom * DBU, b.right * DBU, b.top * DBU] for b in es]
NOM = {'Corner': 180000, 'Filler4000': 20000, 'Filler2000': 10000, 'Filler400': 2000, 'Filler200': 1000}
def nominal(name):
    if 'IOPad' in name: return 80000
    for k, v in NOM.items():
        if name.endswith(k): return v
    return None
sides = {'S': [], 'N': [], 'W': [], 'E': []}
io = []
for inst in T.each_inst():
    n = inst.cell.name; w = nominal(n)
    if w is None: continue
    t = inst.trans; x, y = t.disp.x, t.disp.y; bb = inst.bbox()
    # along-side start and across extent (nominal, from the instance bbox: 0.62 um overhang along the side only)
    ymid, xmid = bb.center().y, bb.center().x
    if 'Corner' in n:
        s = ('S' if ymid < 850000 else 'N'); sides[s].append((bb.left if xmid < 850000 else bb.right - 180000, 180000, n)); sides['W' if xmid < 850000 else 'E'].append((bb.bottom if ymid < 850000 else bb.top - 180000, 180000, n)); continue
    if ymid < 321000 and 141000 <= ymid: s, a, c = 'S', x, (bb.bottom, bb.top)
    elif ymid > 1379000 and ymid <= 1559000: s, a, c = 'N', x, (bb.bottom, bb.top)
    elif xmid < 321000: s, a, c = 'W', y, (bb.left, bb.right)
    else: s, a, c = 'E', y, (bb.left, bb.right)
    sides[s].append((a, w, n)); 
    if 'IOPad' in n: io.append((s, a, n, t.to_s(), c))
res['row'] = {}
ok_all = True
for s, lst in sides.items():
    lst.sort(); pos = lst[0][0]; gaps = 0; ov = 0
    for a, w, n in lst:
        if a > pos: gaps += 1
        if a < pos: ov += 1
        pos = a + w
    first, last = lst[0][0], pos
    ok = gaps == 0 and ov == 0 and first == 141000 and last == 1559000
    ok_all &= ok
    res['row'][s] = dict(count=len(lst), start_um=first * DBU, end_um=last * DBU, gaps=gaps, overlaps=ov, continuous=ok)
res['row_continuous_all'] = ok_all
iocells = {}
for s, a, n, ts, c in sorted(io):
    iocells.setdefault(s, []).append((a * DBU, n.replace('retained_fullchip_sg13g2_', ''), ts))
res['io_cells'] = iocells
res['io_cell_inner_edge_um'] = {'S': max(c[1] for s, a, n, t, c in io if s == 'S') * DBU, 'W': max(c[1] for s, a, n, t, c in io if s == 'W') * DBU,
                                'N': min(c[0] for s, a, n, t, c in io if s == 'N') * DBU, 'E': min(c[0] for s, a, n, t, c in io if s == 'E') * DBU}
# core power ring from the top-level TopMetal1 (126/0) and TopMetal2 (134/0) shapes, not the seal ring, not fill
def pieces(l, d):
    li = ly.find_layer(l, d); out = []
    for s in T.shapes(li).each():
        b = s.bbox()
        if b.width() > 1400000: continue
        if max(b.width(), b.height()) >= 300000: out.append(b)
    return out
tm1 = pieces(126, 0); tm2 = pieces(134, 0)
res['ring_tm1_um'] = sorted([[b.left * DBU, b.bottom * DBU, b.right * DBU, b.top * DBU] for b in tm1])
res['ring_tm2_um'] = sorted([[b.left * DBU, b.bottom * DBU, b.right * DBU, b.top * DBU] for b in tm2])
cols = [b for b in tm1 if b.height() > b.width()]; rows = [b for b in tm2 if b.width() > b.height()]
mid = 850000
w_in = max(b.right for b in cols if b.center().x < mid) * DBU
e_in = min(b.left for b in cols if b.center().x > mid) * DBU
s_in = max(b.top for b in rows if b.center().y < mid) * DBU
n_in = min(b.bottom for b in rows if b.center().y > mid) * DBU
res['core_ring_inner_edge_um'] = {'W_x': w_in, 'E_x': e_in, 'S_y': s_in, 'N_y': n_in}
res['core_window_um'] = {'x0': w_in, 'x1': e_in, 'y0': s_in, 'y1': n_in, 'width': e_in - w_in, 'height': n_in - s_in,
                         'area_mm2': (e_in - w_in) * (n_in - s_in) / 1e6}
io_in = res['io_cell_inner_edge_um']
res['io_window_um'] = {'x0': io_in['W'], 'x1': io_in['E'], 'y0': io_in['S'], 'y1': io_in['N'], 'area_mm2': (io_in['E'] - io_in['W']) * (io_in['N'] - io_in['S']) / 1e6}
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('io_cells', 'ring_tm1_um', 'ring_tm2_um')}, indent=1))
