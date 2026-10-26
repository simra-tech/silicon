# SPDX-License-Identifier: Apache-2.0
# fill_top.sh step 3 (KLayout batch): remove the temporary no-fill cell, prove that fill is the only change, count fill.
#   klayout -b -r fill_top_post.py -rd orig=<r1_top.gds> -rd filled=<filler output> -rd dst=<final gds> -rd out=<fill_counts.json>
# Gate (all must hold, else exit 1): every layer/datatype except the nine fill layers (datatype 22) has an empty XOR
# against the original; no original shape is removed from a fill layer; the instance list of the top cell is unchanged
# apart from the added fill instances; texts are unchanged; die box unchanged.
import pya, json, sys, collections
orig, filled, dst, out = globals()['orig'], globals()['filled'], globals()['dst'], globals()['out']
FILL_CELLS = ['Act_FILL_CELL', 'GatP_FILL_CELL', 'Met1_S_FILL_CELL', 'Met1_M_FILL_CELL', 'Met2_S_FILL_CELL', 'Met2_M_FILL_CELL',
              'Met3_S_FILL_CELL', 'Met3_M_FILL_CELL', 'Met4_S_FILL_CELL', 'Met4_M_FILL_CELL', 'Met5_S_FILL_CELL', 'Met5_M_FILL_CELL',
              'TM1_FILL_CELL', 'TM2_FILL_CELL']
LAYER_NAMES = {(1, 22): 'Activ', (5, 22): 'GatPoly', (8, 22): 'Metal1', (10, 22): 'Metal2', (30, 22): 'Metal3', (50, 22): 'Metal4',
               (67, 22): 'Metal5', (126, 22): 'TopMetal1', (134, 22): 'TopMetal2'}
a = pya.Layout(); a.read(orig); ta = a.cell('r1_top')
b = pya.Layout(); b.read(filled); tb = b.cell('r1_top')
dbu = b.dbu
for ci in list(b.each_cell()):
    if ci.name == 'T8_TMP_NOFILL':
        for inst in list(tb.each_inst()):
            if inst.cell_index == ci.cell_index():
                inst.delete()
        b.delete_cell(ci.cell_index())
# orphan pattern cells left by the filler: none expected
orph = [c.name for c in b.each_cell() if c.cell_index() != tb.cell_index() and c.parent_cells() == 0]
res = {'orphan_cells_after': orph, 'layers_changed_outside_fill': [], 'fill_layers_removed': []}
def reg(ly, top, l, d):
    li = ly.find_layer(l, d)
    return pya.Region() if li is None else pya.Region(top.begin_shapes_rec(li))
keys = sorted({(i.layer, i.datatype) for i in a.layer_infos()} | {(i.layer, i.datatype) for i in b.layer_infos()})
for k in keys:
    ra, rb = reg(a, ta, *k), reg(b, tb, *k)
    if k in LAYER_NAMES:
        if not (ra - rb).is_empty():
            res['fill_layers_removed'].append(list(k))
    elif not (ra ^ rb).is_empty():
        res['layers_changed_outside_fill'].append(list(k))
def texts(ly, top):
    t = collections.Counter()
    for li in ly.layer_indexes():
        i = top.begin_shapes_rec(li)
        i.shape_flags = pya.Shapes.STexts
        while not i.at_end():
            s = i.shape().text
            p = i.trans() * pya.Point(s.x, s.y)
            t[(ly.get_info(li).to_s(), s.string, p.x, p.y)] += 1
            i.next()
    return t
res['texts_equal'] = texts(a, ta) == texts(b, tb)
ia = collections.Counter((i.cell.name, str(i.trans)) for i in ta.each_inst())
ib = collections.Counter((i.cell.name, str(i.trans)) for i in tb.each_inst() if i.cell.name not in FILL_CELLS)
res['original_instances_kept'] = not (ia - ib) and not (ib - ia)
res['die_equal'] = ta.bbox() == tb.bbox()
cnt = {}
for name in FILL_CELLS:
    c = b.cell(name) if b.has_cell(name) else None
    if c is None:
        cnt[name] = {'placements': 0, 'rectangles': 0}
        continue
    pl = 0
    for inst in tb.each_inst():
        if inst.cell_index == c.cell_index():
            pl += (inst.na * inst.nb) if inst.is_regular_array() else 1
    cnt[name] = {'placements': pl, 'rectangles': pl}
res['cells'] = cnt
layers = {}
for (l, d), nm in LAYER_NAMES.items():
    li = b.find_layer(l, d)
    # fill of the top-level filler only: shapes of the fill pattern cells times their placements
    n, area = 0, 0
    for name in FILL_CELLS:
        c = b.cell(name) if b.has_cell(name) else None
        if c is None or li is None:
            continue
        s = c.shapes(li)
        if s.size() == 0:
            continue
        per = sum(sh.polygon.area() if sh.is_polygon() else sh.box.area() for sh in s.each())
        n += s.size() * cnt[name]['placements']
        area += per * cnt[name]['placements']
    flat = pya.Region(tb.shapes(li)) if li is not None else pya.Region()   # supplementary flat fill in the top cell
    layers[nm] = {'rectangles': n + flat.count(), 'area_um2': round((area + flat.area()) * dbu * dbu, 1),
                  'pdk_cell_rectangles': n, 'supplementary_flat_rectangles': flat.count()}
res['layers'] = layers
res['gate_passed'] = (not res['layers_changed_outside_fill'] and not res['fill_layers_removed'] and res['texts_equal']
                      and res['original_instances_kept'] and res['die_equal'] and not orph)
b.write(dst)
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps(res, indent=1))
print('fill_top_post: gate', 'PASSED' if res['gate_passed'] else 'FAILED', dst)
if not res['gate_passed']:
    sys.exit(1)
