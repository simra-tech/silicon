import pya, json, os, collections
G = '/work/designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r3.gds'
OUT = '${BULK}/redteam-20260927/physical/p5'; os.makedirs(OUT, exist_ok=True)
ly = pya.Layout(); ly.read(G); top = ly.cell('g1_chip_top'); dbu = ly.dbu
res = {}
def flat(l, d):
    li = ly.find_layer(l, d)
    return pya.Region() if li is None else pya.Region(top.begin_shapes_rec(li)).merged()
mim = flat(36, 0); res['mim_total_um2'] = mim.area() * dbu * dbu; res['mim_count'] = mim.count()
res['mim_max_single_um2'] = max((p.area() * dbu * dbu for p in mim.each()), default=0)
res['top_texts_63'] = [(s.text_string, s.text.x * dbu, s.text.y * dbu) for s in top.shapes(ly.find_layer(63, 0)).each(pya.Shapes.STexts)]
res['top_cells'] = [c.name for c in ly.top_cells()]
res['bbox_um'] = str(top.dbbox())
es = flat(39, 4); res['edgeseal_boundary'] = [str(p) for p in es.each()][:3]
# everything (all layers) outside the die box
die = pya.Region(pya.Box(0, 0, 1414000, 1414000)); outside = {}
for li in ly.layer_indexes():
    r = pya.Region(top.begin_shapes_rec(li))
    o = r - die
    if not o.is_empty(): outside[str(ly.get_info(li))] = o.area() * dbu * dbu
res['area_outside_die'] = outside
# IO cell instances in the top
cnt = collections.Counter(ly.cell(i.cell_index).name for i in top.each_inst())
res['top_instances'] = {k: v for k, v in cnt.items() if 'IOPad' in k or 'Corner' in k or 'Filler' in k or 'bondpad' in k}
json.dump(res, open(OUT + '/misc.json', 'w'), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
