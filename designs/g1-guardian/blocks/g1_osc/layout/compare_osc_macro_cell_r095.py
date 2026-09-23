"""Read-only recursive OSC-cell comparison inside a full-chip GDS."""
import hashlib
import json
import pya

baseline = globals()['baseline']
chip = globals()['chip']
out = globals()['out']
cellname = globals().get('cellname', 'g1_osc')
chipcell = globals().get('chipcell', '__rz_port_text_032_retained_g1_osc')


def load(path, name):
    ly = pya.Layout()
    ly.read(path)
    cell = ly.cell(name)
    assert cell is not None, (path, name, [c.name for c in ly.each_cell() if 'osc' in c.name.lower()], ly.top_cell().name)
    assert abs(ly.dbu - 0.001) < 1e-12, (path, ly.dbu)
    return ly, cell


def text_inventory(cell, li):
    it = cell.begin_shapes_rec(li)
    ans = []
    while not it.at_end():
        shape = it.shape()
        if shape.is_text():
            t = shape.text.transformed(it.trans())
            ans.append((t.string, str(t.trans)))
        it.next()
    return sorted(ans)


la, ca = load(baseline, cellname)
lb, cb = load(chip, chipcell)
layers = sorted(set((la.get_info(li).layer, la.get_info(li).datatype) for li in la.layer_indexes()) |
                set((lb.get_info(li).layer, lb.get_info(li).datatype) for li in lb.layer_indexes()))
rows = []
for l, d in layers:
    ia, ib = la.find_layer(l, d), lb.find_layer(l, d)
    ra = pya.Region(ca.begin_shapes_rec(ia)) if ia is not None else pya.Region()
    rb = pya.Region(cb.begin_shapes_rec(ib)) if ib is not None else pya.Region()
    xor = ra ^ rb
    ta = text_inventory(ca, ia) if ia is not None else []
    tb = text_inventory(cb, ib) if ib is not None else []
    if not xor.is_empty() or ta != tb:
        rows.append({'layer': '%d/%d' % (l, d), 'nontext_xor_shapes': xor.count(),
                     'baseline_text': ta, 'chip_text': tb})
report = {'baseline_sha256': hashlib.sha256(open(baseline, 'rb').read()).hexdigest(),
          'chip_sha256': hashlib.sha256(open(chip, 'rb').read()).hexdigest(),
          'baseline_cell': cellname, 'chip_cell': chipcell,
          'baseline_bbox': str(ca.bbox()), 'chip_bbox': str(cb.bbox()),
          'layer_differences': rows, 'same_recursive_geometry_and_text': not rows}
open(out, 'w').write(json.dumps(report, indent=2) + '\n')
print(json.dumps({'same': not rows, 'changed_layers': [(x['layer'], x['nontext_xor_shapes'],
       len(x['baseline_text']), len(x['chip_text'])) for x in rows]}))
