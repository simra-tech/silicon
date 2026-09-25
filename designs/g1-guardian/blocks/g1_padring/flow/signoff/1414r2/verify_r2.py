"""Prove r2 differs from r1 only in the two 63/0 registration texts and the listed cell renames.
(1) cell count and names equal modulo RENAME; every cell's direct shapes (all layers; top 63/0 texts reported
    separately) and instance lists (child by mapped name) identical; (2) deep per-layer XOR of the flattened top
    on every layer; (3) flattened text lists per layer; (4) recursive instance-tree walk (mapped names).
klayout -b -r verify_r2.py -rd a=<r1.gds> -rd b=<r2.gds> -rd out=<json> [-rd rename=old:new,...]"""
import pya, json, hashlib, re, collections
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
try: rename
except NameError: rename = 'sg13g2_LevelDown:g1_LevelDown_polyres'
RENAME = dict(p.split(':') for p in rename.split(',') if p)
la = pya.Layout(); la.read(a); lb = pya.Layout(); lb.read(b)
ta, = la.top_cells(); tb, = lb.top_cells()
res = dict(r1=a, r1_sha256=sha(a), r2=b, r2_sha256=sha(b), tops=[ta.name, tb.name], dbu_equal=la.dbu == lb.dbu,
           cell_count=[la.cells(), lb.cells()], rename=RENAME,
           libname=[la.meta_info_value('libname'), lb.meta_info_value('libname')])
def mapn(n): return RENAME.get(n, n)
def direct(ly, c, skip_top_text=False):
    d = {}
    for i in ly.layer_indexes():
        info = ly.get_info(i); sh = c.shapes(i)
        if sh.is_empty(): continue
        items = sorted(str(s) for s in sh.each() if not (skip_top_text and info.layer == 63 and info.datatype == 0 and s.is_text()))
        if items: d[info.to_s()] = items
    return d
def insts(ly, c, m): return sorted((m(i.cell.name), re.sub(r'^#\d+ ', '', str(i.cell_inst))) for i in c.each_inst())
ha = {mapn(c.name): (direct(la, c, c.cell_index() == ta.cell_index()), insts(la, c, mapn)) for c in la.each_cell()}
hb = {c.name: (direct(lb, c, c.cell_index() == tb.cell_index()), insts(lb, c, lambda n: n)) for c in lb.each_cell()}
res['cell_names_equal_modulo_rename'] = sorted(ha) == sorted(hb)
res['renamed_present'] = {o: [la.has_cell(o), lb.has_cell(o), la.has_cell(n), lb.has_cell(n)] for o, n in RENAME.items()}
res['hier_diff_cells'] = [k for k in ha if ha[k] != hb.get(k)]
# recursive instance tree (paths by mapped names) counts
def tree(ly, top, m):
    cnt = collections.Counter(); it = top.begin_instances_rec()
    while not it.at_end():
        path = tuple(m(ly.cell(e.cell_inst().cell_index).name) for e in it.path()) + (m(ly.cell(it.inst_cell().cell_index()).name),)
        cnt[(path[-1], str(it.trans() * it.inst_trans()))] += 1; it.next()
    return cnt
tra, trb = tree(la, ta, mapn), tree(lb, tb, lambda n: n)
res['recursive_instances'] = [sum(tra.values()), sum(trb.values())]
res['recursive_instance_tree_equal'] = tra == trb
# deep XOR per layer and flattened texts
infos = {(i.layer, i.datatype) for i in la.layer_infos()} | {(i.layer, i.datatype) for i in lb.layer_infos()}
dss = pya.DeepShapeStore(); dss.threads = 4
xor = {}; text_diff = {}; nonempty = 0
for L, D in sorted(infos):
    info = pya.LayerInfo(L, D); ia = la.find_layer(info); ib = lb.find_layer(info)
    ra = pya.Region(ta.begin_shapes_rec(ia), dss) if ia is not None else pya.Region()
    rb = pya.Region(tb.begin_shapes_rec(ib), dss) if ib is not None else pya.Region()
    n = (ra ^ rb).count()
    if not ra.is_empty() or not rb.is_empty(): nonempty += 1
    if n: xor[f'{L}/{D}'] = n
    def tx(ly, t, i):
        out = collections.Counter()
        if i is None: return out
        it = t.begin_shapes_rec(i); it.shape_flags = pya.Shapes.STexts
        while not it.at_end():
            x = it.shape().text.transformed(it.trans()); out[(x.string, str(x.trans), x.size, x.font, int(x.halign), int(x.valign))] += 1; it.next()
        return out
    A, B = tx(la, ta, ia), tx(lb, tb, ib)
    if A != B: text_diff[f'{L}/{D}'] = dict(only_r1=[list(k) for k in (A - B)], only_r2=[list(k) for k in (B - A)], n=[sum(A.values()), sum(B.values())])
res.update(layers_compared=len(infos), layers_with_content=nonempty, xor_nonempty_layers=xor, text_diff_layers=text_diff,
           top_bbox=[str(ta.bbox()), str(tb.bbox())])
td = text_diff.get('63/0', {})
res['only_63_0_texts_differ'] = set(text_diff) <= {'63/0'} and len(td.get('only_r1', [])) == 2 and len(td.get('only_r2', [])) == 2 \
    and sorted(k[1:] for k in td['only_r1']) == sorted(k[1:] for k in td['only_r2'])
res['metadata_only_change'] = (res['dbu_equal'] and res['cell_names_equal_modulo_rename'] and not res['hier_diff_cells']
                               and not xor and res['only_63_0_texts_differ'] and ta.bbox() == tb.bbox()
                               and la.cells() == lb.cells() and res['recursive_instance_tree_equal'])
open(out, 'w').write(json.dumps(res, indent=2) + '\n'); print(json.dumps(res, indent=1))
