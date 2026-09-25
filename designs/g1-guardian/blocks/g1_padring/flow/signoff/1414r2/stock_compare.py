"""Compare every chip cell whose name (minus a trailing $N suffix, and minus a retained_/retained_fullchip_ prefix,
reported separately) exists in a PDK libs.ref GDS against that PDK cell: per-layer XOR of the recursive
shapes in cell coordinates on the union of layers, plus a flattened text comparison. Also compares the listed
renamed cells against their stock origin.
klayout -b -r stock_compare.py -rd g=<chip.gds> -rd out=<json> [-rd renamed=new:stock,...]"""
import pya, json, re, glob, hashlib, collections
ly = pya.Layout(); ly.read(g)
try: renamed
except NameError: renamed = 'g1_LevelDown_polyres:sg13g2_LevelDown'
REN = dict(p.split(':') for p in renamed.split(',') if p)
refs = {}
for f in sorted(glob.glob('/foss/pdks/ihp-sg13g2/libs.ref/*/gds/*.gds')):
    r = pya.Layout(); r.read(f); refs[f] = r
def R(lay, cell, l, d):
    li = lay.find_layer(l, d)
    return pya.Region() if li is None else pya.Region(cell.begin_shapes_rec(li))
def texts(lay, cell):
    out = collections.Counter()
    for li in lay.layer_indexes():
        it = cell.begin_shapes_rec(li); it.shape_flags = pya.Shapes.STexts
        while not it.at_end():
            t = it.shape().text.transformed(it.trans()); out[(str(lay.get_info(li)), t.string, t.x, t.y)] += 1; it.next()
    return out
def compare(c, base):
    hits = [(f, r) for f, r in refs.items() if r.has_cell(base)]
    f, rl = hits[0]; rc = rl.cell(base); dbu = ly.dbu; diffs = {}
    infos = {(i.layer, i.datatype) for i in ly.layer_infos()} | {(i.layer, i.datatype) for i in rl.layer_infos()}
    for l, d in sorted(infos):
        a = R(ly, c, l, d); b = R(rl, rc, l, d); x = a ^ b
        if not x.is_empty():
            diffs[f'{l}/{d}'] = dict(xor_um2=round(x.area() * dbu * dbu, 4), chip_um2=round(a.area() * dbu * dbu, 4), ref_um2=round(b.area() * dbu * dbu, 4))
    A, B = texts(ly, c), texts(rl, rc)
    return dict(ref=base, ref_lib=f.split('/libs.ref/')[1], libs_with_name=len(hits), identical=not diffs and A == B, layer_diffs=diffs,
                text_only_chip=sum((A - B).values()), text_only_ref=sum((B - A).values()), bbox=[str(c.bbox()), str(rc.bbox())])
stock, derived, prefixed, ren = {}, {}, {}, {}
for c in ly.each_cell():
    n = c.name
    if any(r.has_cell(n) for r in refs.values()): stock[n] = compare(c, n); continue
    base = re.sub(r'(\$\d+)+$', '', n)
    if base != n and any(r.has_cell(base) for r in refs.values()): derived[n] = compare(c, base); continue
    pb = re.sub(r'(\$\d+)+$', '', re.sub(r'^(retained_fullchip_|retained_)', '', n))
    if pb != n and any(r.has_cell(pb) for r in refs.values()): prefixed[n] = compare(c, pb)
for new, old in REN.items():
    if ly.has_cell(new): ren[new] = compare(ly.cell(new), old)
res = dict(gds=g, sha256=hashlib.sha256(open(g, 'rb').read()).hexdigest(), ref_libs=list(refs),
           exact_stock_named=len(stock), exact_stock_named_differing={k: v for k, v in stock.items() if not v['identical']},
           dollar_suffix_named=len(derived), dollar_suffix_differing={k: v for k, v in derived.items() if not v['identical']},
           prefixed_informational={k: v['layer_diffs'] or 'identical' for k, v in prefixed.items()},
           renamed_vs_stock=ren, exact_stock_names=sorted(stock), dollar_names=sorted(derived))
open(out, 'w').write(json.dumps(res, indent=1) + '\n')
print(json.dumps({k: res[k] for k in ['sha256', 'exact_stock_named', 'exact_stock_named_differing', 'dollar_suffix_named', 'dollar_suffix_differing', 'prefixed_informational', 'renamed_vs_stock']}, indent=1))
