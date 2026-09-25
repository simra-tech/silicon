#!/usr/bin/env python3
"""List the pin interface of a g1_digital macro cell in a GDS: pin shapes
(<layer>/2), pin labels (<layer>/25) and the power-stripe drawing shapes on
TopMetal1/TopMetal2, in the cell's own coordinates (nm).

Usage (inside the pinned container):
  extract_macro_pins.py <gds> <cell> <out.json>
The JSON is the input of compare_macro_pins.py.
"""
import json
import sys

import klayout.db as db

# IHP SG13G2 layer numbers (drawing, pin, text)
METALS = {'Metal1': 8, 'Metal2': 10, 'Metal3': 30, 'Metal4': 50, 'Metal5': 67,
          'TopMetal1': 126, 'TopMetal2': 134}


def extract(gds, cellname):
    ly = db.Layout()
    ly.read(gds)
    cell = ly.cell(cellname)
    if cell is None:
        raise SystemExit('cell %s not in %s' % (cellname, gds))
    out = {'gds': gds, 'cell': cellname, 'dbu_um': ly.dbu,
           'bbox_nm': list(map(int, str(cell.bbox()).strip('()').replace(';', ',').split(','))),
           'pins': [], 'labels': [], 'top_metal_drawing': {}}
    for name, num in METALS.items():
        for dt, key in ((2, 'pins'), (25, 'labels')):
            li = ly.find_layer(num, dt)
            if li is None:
                continue
            for s in cell.shapes(li).each():   # top level of the macro cell only
                if key == 'labels' and s.is_text():
                    t = s.text
                    out[key].append({'layer': name, 'text': t.string, 'x': t.x, 'y': t.y})
                elif key == 'pins' and not s.is_text():
                    b = s.bbox()
                    out[key].append({'layer': name, 'box': [b.left, b.bottom, b.right, b.top]})
        if name in ('TopMetal1', 'TopMetal2'):
            li = ly.find_layer(num, 0)
            reg = db.Region(cell.begin_shapes_rec(li)) if li is not None else db.Region()
            reg.merge()
            out['top_metal_drawing'][name] = sorted(
                [[p.bbox().left, p.bbox().bottom, p.bbox().right, p.bbox().top] for p in reg.each()])
    out['pins'].sort(key=lambda p: (p['layer'], p['box']))
    out['labels'].sort(key=lambda p: (p['layer'], p['text'], p['x'], p['y']))
    # attach the label(s) that fall inside each pin shape
    for p in out['pins']:
        x0, y0, x1, y1 = p['box']
        p['labels'] = sorted(l['text'] for l in out['labels'] if l['layer'] == p['layer']
                             and x0 <= l['x'] <= x1 and y0 <= l['y'] <= y1)
    return out


if __name__ == '__main__':
    gds, cellname, dst = sys.argv[1:4]
    res = extract(gds, cellname)
    with open(dst, 'w') as f:
        json.dump(res, f, indent=1)
    print('%s: %d pin shapes, %d labels, bbox %s' % (cellname, len(res['pins']), len(res['labels']), res['bbox_nm']))
