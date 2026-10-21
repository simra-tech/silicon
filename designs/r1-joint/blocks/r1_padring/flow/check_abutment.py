# IO-row rail continuity check: for every pair of abutting row cells (corner, IO cell, IO filler) on every side,
# compare the cross-section of each layer on both sides of the common boundary. A shape that reaches the boundary
# from one cell but has no partner from the other cell is a break.
#   klayout -b -r flow/check_abutment.py -rd gds=<ring gds> -rd out=<json>
import pya, json, collections
ly = pya.Layout(); ly.read(gds); T = ly.top_cell(); DIE = T.bbox().right
LAY = {'Activ': (1, 0), 'Metal1': (8, 0), 'Metal2': (10, 0), 'Metal3': (30, 0), 'Metal4': (50, 0), 'Metal5': (67, 0),
       'TopMetal1': (126, 0), 'TopMetal2': (134, 0)}
PRB = ly.find_layer(189, 4)
def outline(i):
    c = i.cell; r = pya.Region(pya.RecursiveShapeIterator(ly, c, PRB)) if PRB is not None else pya.Region()
    b = r.bbox() if not r.is_empty() else c.bbox()
    return b.transformed(i.cplx_trans)
row = [i for i in T.each_inst() if 'sg13g2_' in i.cell.name and ('IOPad' in i.cell.name or 'Filler' in i.cell.name or 'Corner' in i.cell.name)]
def side(b):
    if b.bottom == 141000 and b.top == 321000 and b.right <= DIE - 141000: return 'S'
    if b.top == DIE - 141000 and b.bottom == DIE - 321000: return 'N'
    if b.left == 141000 and b.right == 321000: return 'W'
    if b.right == DIE - 141000 and b.left == DIE - 321000: return 'E'
    return None
sides = collections.defaultdict(list)
for i in row:
    b = outline(i)   # prBoundary 189/4 of the cell
    if 'Corner' in i.cell.name:
        # a corner belongs to two sides
        for s in 'SNWE':
            ok = {'S': b.bottom == 141000, 'N': b.top == DIE - 141000, 'W': b.left == 141000, 'E': b.right == DIE - 141000}[s]
            if ok: sides[s].append(i)
    else:
        s = side(b)
        assert s, (i.cell.name, b.to_s())
        sides[s].append(i)
def flat(inst, li):
    r = pya.Region()
    it = pya.RecursiveShapeIterator(ly, inst.cell, li); it.global_trans = pya.ICplxTrans(inst.trans) if False else pya.ICplxTrans()
    r = pya.Region(it); r.transform(inst.cplx_trans)
    return r.merged()
rep = {'gds': gds, 'pairs': 0, 'breaks': [], 'per_layer_breaks': {k: 0 for k in LAY}, 'gaps_or_overlaps': []}
for s in 'SNWE':
    horiz = s in 'SN'
    key = (lambda i: outline(i).left) if horiz else (lambda i: outline(i).bottom)
    cells = sorted(sides[s], key=key)
    for a, b in zip(cells, cells[1:]):
        ba, bb = outline(a), outline(b)
        ea = ba.right if horiz else ba.top; sb = bb.left if horiz else bb.bottom
        if ea != sb: rep['gaps_or_overlaps'].append([s, a.cell.name, b.cell.name, ea / 1000, sb / 1000]); continue
        rep['pairs'] += 1; c = ea
        lo, hi = (141000, 321000) if s in 'SW' else (DIE - 321000, DIE - 141000)
        wa = pya.Box(c - 10, lo, c, hi) if horiz else pya.Box(lo, c - 10, hi, c)
        wb = pya.Box(c, lo, c + 10, hi) if horiz else pya.Box(lo, c, hi, c + 10)
        for name, (l, d) in LAY.items():
            li = ly.find_layer(l, d)
            if li is None: continue
            ra = flat(a, li) & pya.Region(wa); rb = flat(b, li) & pya.Region(wb)
            # project onto the across axis
            pa = pya.Region([pya.Box(0, x.bottom, 1, x.top) if horiz else pya.Box(x.left, 0, x.right, 1) for x in (p.bbox() for p in ra.each_merged())]).merged()
            pb = pya.Region([pya.Box(0, x.bottom, 1, x.top) if horiz else pya.Box(x.left, 0, x.right, 1) for x in (p.bbox() for p in rb.each_merged())]).merged()
            diff = (pa ^ pb)
            if not diff.is_empty():
                rep['per_layer_breaks'][name] += 1
                rep['breaks'].append([s, a.cell.name, b.cell.name, c / 1000, name,
                                      [[(x.bottom if horiz else x.left) / 1000, (x.top if horiz else x.right) / 1000] for x in (p.bbox() for p in diff.each())][:6]])
rep['cells_per_side'] = {s: len(v) for s, v in sides.items()}
rep['break_cell_pairs'] = collections.Counter('%s|%s' % (x[1].replace('retained_fullchip_', ''), x[2].replace('retained_fullchip_', '')) for x in rep['breaks'])
json.dump(rep, open(out, 'w'), indent=1, default=str)
print(json.dumps({k: rep[k] for k in ('pairs', 'per_layer_breaks', 'gaps_or_overlaps', 'cells_per_side', 'break_cell_pairs')}, indent=1, default=str))
