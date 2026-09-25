"""Layer inventory of a tape-in GDS against the PDK KLayout layer properties.
klayout -b -r gds_inventory.py -rd gds=<file.gds> -rd lyp=<sg13g2.lyp> -rd out=<file.json>
Reports: top cell(s), DBU, bbox, per-layer flattened shape and text counts (computed
hierarchically: direct shapes x number of flat placements of each cell), layers absent
from the .lyp, text-purpose layers, which cells carry PolyRes 128/0, seal-ring layers,
Passiv 9/0 openings (merged, flat) and bondpad-cell placements."""
import pya, json, hashlib, re
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()
s = open(lyp).read()
names = {}
for p in re.findall(r'<properties>(.*?)</properties>', s, re.S):
    src = re.search(r'<source>([0-9]+/[0-9]+)', p); nm = re.search(r'<name>(.*?)</name>', p)
    if src: names[src.group(1)] = nm.group(1) if nm else ''
ly = pya.Layout(); ly.read(gds)
tops = ly.top_cells(); top = tops[0]
# flat placement count of every cell
cnt = {top.cell_index(): 1}
order = list(ly.each_cell_top_down())  # cell indices, parents before children
for ci in order:
    c = ly.cell(ci); n = cnt.get(ci, 0)
    if n == 0: continue
    for inst in c.each_inst():
        cnt[inst.cell_index] = cnt.get(inst.cell_index, 0) + n * inst.size()
layers = []
for li in ly.layer_indexes():
    info = ly.get_info(li); key = f'{info.layer}/{info.datatype}'
    shapes = texts = 0; cells_with = []
    for ci, n in cnt.items():
        sh = ly.cell(ci).shapes(li)
        if sh.is_empty(): continue
        t = sum(1 for _ in sh.each(pya.Shapes.STexts))
        shapes += n * (sh.size() - t); texts += n * t
        cells_with.append(ly.cell(ci).name)
    if shapes == 0 and texts == 0: continue
    nm = names.get(key)
    layers.append(dict(layer=key, name=nm, in_pdk_lyp=nm is not None, flat_shapes=shapes, flat_texts=texts,
                       n_cells=len(cells_with), cells=sorted(cells_with)))
layers.sort(key=lambda r: tuple(int(x) for x in r['layer'].split('/')))
def flat_region(key):
    L, D = map(int, key.split('/')); li = ly.find_layer(pya.LayerInfo(L, D))
    return pya.Region() if li is None else pya.Region(top.begin_shapes_rec(li))
passiv = flat_region('9/0').merged()
open_boxes = sorted(((round(p.bbox().width() * ly.dbu, 3), round(p.bbox().height() * ly.dbu, 3)) for p in passiv.each()))
res = dict(gds=gds, sha256=sha(gds), top_cells=[c.name for c in tops], dbu_um=ly.dbu,
           bbox_um=[round(v * ly.dbu, 3) for v in (top.bbox().left, top.bbox().bottom, top.bbox().right, top.bbox().top)],
           cell_count=ly.cells(), layers=layers,
           layers_not_in_lyp=[r['layer'] for r in layers if not r['in_pdk_lyp']],
           layers_with_texts=[r['layer'] for r in layers if r['flat_texts']],
           text_purpose_layers=[r['layer'] for r in layers if (r['name'] or '').endswith(('.label', '.text', '.pin'))],
           polyres_128_0=next((r for r in layers if r['layer'] == '128/0'), None),
           passiv_openings=dict(count=len(open_boxes), sizes_um=sorted(set(open_boxes))),
           bondpad_cells={ly.cell(ci).name: n for ci, n in cnt.items() if 'bondpad' in ly.cell(ci).name.lower()},
           sealring_cells={ly.cell(ci).name: n for ci, n in cnt.items() if 'seal' in ly.cell(ci).name.lower()},
           io_cells={ly.cell(ci).name: n for ci, n in cnt.items() if re.search(r'IOPad|Corner|Filler', ly.cell(ci).name)})
open(out, 'w').write(json.dumps(res, indent=1) + '\n')
print(json.dumps({k: v for k, v in res.items() if k != 'layers'}, indent=1))
