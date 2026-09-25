"""Prove renamed GDS is geometrically identical to source.
(1) hierarchical: every cell (top matched by role) has identical direct shapes, texts, properties-free
    instance lists; (2) deep-mode per-layer XOR of the whole flattened top is empty; (3) flattened texts equal.
klayout -b -r verify_rename.py -rd a=<src.gds> -rd b=<renamed.gds> -rd out=<json>"""
import pya, json, hashlib, re
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
la = pya.Layout(); la.read(a); lb = pya.Layout(); lb.read(b)
ta, = la.top_cells(); tb, = lb.top_cells()
res = dict(src=a, src_sha256=sha(a), dst=b, dst_sha256=sha(b), src_top=ta.name, dst_top=tb.name,
           dbu_equal=la.dbu == lb.dbu, cell_count=[la.cells(), lb.cells()])
def nm(c, top): return '<TOP>' if c.cell_index() == top.cell_index() else c.name
def direct(ly, c):
    return {ly.get_info(i).to_s(): sorted(str(s) for s in c.shapes(i).each()) for i in ly.layer_indexes() if not c.shapes(i).is_empty()}
# cell indices are renumbered by the writer; instances are compared by child-cell name
def insts(ly, c, top): return sorted((nm(i.cell, top), re.sub(r'^#\d+ ', '', str(i.cell_inst))) for i in c.each_inst())
ha = {nm(c, ta): (direct(la, c), insts(la, c, ta)) for c in la.each_cell()}
hb = {nm(c, tb): (direct(lb, c), insts(lb, c, tb)) for c in lb.each_cell()}
res['cell_names_equal_except_top'] = sorted(ha) == sorted(hb)
res['hier_diff_cells'] = [k for k in ha if ha[k] != hb.get(k)]
# deep XOR per layer
infos = {(i.layer, i.datatype) for i in la.layer_infos()} | {(i.layer, i.datatype) for i in lb.layer_infos()}
dss = pya.DeepShapeStore(); dss.threads = 4
xor = {}; text_diff = {}; shape_layers = 0
for L, D in sorted(infos):
    info = pya.LayerInfo(L, D); ia = la.find_layer(info); ib = lb.find_layer(info)
    ra = pya.Region(ta.begin_shapes_rec(ia), dss) if ia is not None else pya.Region()
    rb = pya.Region(tb.begin_shapes_rec(ib), dss) if ib is not None else pya.Region()
    x = ra ^ rb; n = x.count()
    if not ra.is_empty(): shape_layers += 1
    if n: xor[f'{L}/{D}'] = n
    txa = sorted(str(t) for t in pya.Texts(ta.begin_shapes_rec(ia))) if ia is not None else []
    txb = sorted(str(t) for t in pya.Texts(tb.begin_shapes_rec(ib))) if ib is not None else []
    if txa != txb: text_diff[f'{L}/{D}'] = [len(txa), len(txb)]
res.update(layers_compared=len(infos), layers_with_shapes=shape_layers, xor_nonempty_layers=xor, text_diff_layers=text_diff,
           top_bbox=[str(ta.bbox()), str(tb.bbox())])
res['identical_geometry'] = (res['dbu_equal'] and res['cell_names_equal_except_top'] and not res['hier_diff_cells']
                             and not xor and not text_diff and ta.bbox() == tb.bbox())
open(out, 'w').write(json.dumps(res, indent=2) + '\n'); print(json.dumps(res))
