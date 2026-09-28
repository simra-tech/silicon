# Per-layer XOR of one cell (hierarchy flattened) between two GDS files, plus text and sub-cell tree comparison.
#   klayout -b -r cell_xor.py -rd a=<gds> -rd ca=<cell> -rd b=<gds> -rd cb=<cell> -rd out=<json>
import pya, json, hashlib
def sha(p):
    h = hashlib.sha256(); f = open(p, 'rb')
    for blk in iter(lambda: f.read(1 << 20), b''): h.update(blk)
    return h.hexdigest()
la = pya.Layout(); la.read(a); lb = pya.Layout(); lb.read(b)
A, B = la.cell(ca), lb.cell(cb)
assert A is not None and B is not None, 'cell missing'
assert la.dbu == lb.dbu
infos = {}
for li in la.layer_indexes(): infos[str(la.get_info(li))] = [li, None]
for lj in lb.layer_indexes(): infos.setdefault(str(lb.get_info(lj)), [None, None])[1] = lj
layers = {}; ndiff = 0
def texts(lay, c, li):
    s = []
    it = c.begin_shapes_rec(li)
    while not it.at_end():
        sh = it.shape()
        if sh.is_text():
            t = sh.text.transformed(it.trans())
            s.append((t.string, t.x, t.y))
        it.next()
    return sorted(s)
for k, (li, lj) in sorted(infos.items()):
    ra = pya.Region(A.begin_shapes_rec(li)) if li is not None else pya.Region()
    rb = pya.Region(B.begin_shapes_rec(lj)) if lj is not None else pya.Region()
    x = ra ^ rb
    ta = texts(la, A, li) if li is not None else []
    tb = texts(lb, B, lj) if lj is not None else []
    d = {'polys_a': ra.count(), 'polys_b': rb.count(), 'xor_polys': x.count(), 'xor_um2': round(x.area() * la.dbu * la.dbu, 6),
         'texts_a': len(ta), 'texts_b': len(tb), 'texts_equal': ta == tb}
    if ra.is_empty() and rb.is_empty() and not ta and not tb: continue
    layers[k] = d
    if d['xor_polys'] or not d['texts_equal']: ndiff += 1
def tree(lay, c):
    out = []
    for ci in c.each_child_cell(): pass
    s = set()
    for i in c.called_cells(): s.add(lay.cell(i).name)
    return sorted(s)
res = {'a': a, 'a_sha256': sha(a), 'cell_a': ca, 'b': b, 'b_sha256': sha(b), 'cell_b': cb,
       'bbox_a': str(A.dbbox()), 'bbox_b': str(B.dbbox()),
       'called_cells_a': len(tree(la, A)), 'called_cells_b': len(tree(lb, B)),
       'called_cell_names_equal': tree(la, A) == tree(lb, B),
       'layers_compared': len(layers), 'layers_differing': ndiff,
       'total_xor_polys': sum(v['xor_polys'] for v in layers.values()), 'layers': layers}
# placement of the cell in each file's top cell
for tag, lay, c in (('a', la, A), ('b', lb, B)):
    top = lay.top_cell(); pl = []
    if top.cell_index() != c.cell_index():
        for inst in top.each_inst():
            if inst.cell_index == c.cell_index(): pl.append(str(inst.dcplx_trans))
    res['placements_in_top_' + tag] = pl
open(out, 'w').write(json.dumps(res, indent=1))
print(json.dumps({k: v for k, v in res.items() if k != 'layers'}))
