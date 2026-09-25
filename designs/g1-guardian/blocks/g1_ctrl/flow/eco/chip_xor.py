#!/usr/bin/env python3
"""Per-layer XOR of two chip GDS files, split into outside / inside a macro box.

  chip_xor.py <reference.gds> <candidate.gds> <x0,y0,x1,y1 um> <out.json>

For every layer: number of XOR polygons and XOR area outside the box and inside it,
on the flattened top cell; flattened text records (string, position) outside the box
compared as sets. Used to prove that outside the digital macro only fill layers
changed (swap + GatPoly fill regeneration).
"""
import collections
import hashlib
import json
import sys

import klayout.db as db


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


ref_p, cand_p, box_s, out_p = sys.argv[1:5]
x0, y0, x1, y1 = (int(round(float(v) * 1000)) for v in box_s.split(','))
box = db.Region(db.Box(x0, y0, x1, y1))
la, lb = db.Layout(), db.Layout()
la.read(ref_p); lb.read(cand_p)
ta, = la.top_cells(); tb, = lb.top_cells()
infos = {(i.layer, i.datatype) for i in la.layer_infos()} | {(i.layer, i.datatype) for i in lb.layer_infos()}


def reg(ly, top, ld):
    li = ly.find_layer(*ld)
    return db.Region() if li is None else db.Region(top.begin_shapes_rec(li)).merged()


def txt(ly, top, ld):
    li = ly.find_layer(*ld)
    out = collections.Counter()
    if li is None:
        return out
    it = top.begin_shapes_rec(li)
    while not it.at_end():
        if it.shape().is_text():
            t = it.shape().text.transformed(it.trans())
            inside = x0 <= t.x <= x1 and y0 <= t.y <= y1
            out[(t.string, t.x, t.y, inside)] += 1
        it.next()
    return out


res = {'reference': ref_p, 'reference_sha256': sha(ref_p), 'candidate': cand_p, 'candidate_sha256': sha(cand_p),
       'box_um': box_s, 'layers': {}}
for ld in sorted(infos):
    x = reg(la, ta, ld) ^ reg(lb, tb, ld)
    xo, xi = x - box, x & box
    ca, cb = txt(la, ta, ld), txt(lb, tb, ld)
    to = sum(((ca - cb) + (cb - ca)).values())
    t_out = sum(v for k, v in ((ca - cb) + (cb - ca)).items() if not k[3])
    if x.is_empty() and not to:
        continue
    res['layers']['%d/%d' % ld] = dict(outside_polygons=xo.count(), outside_um2=round(xo.area() * 1e-6, 4),
                                       inside_polygons=xi.count(), inside_um2=round(xi.area() * 1e-6, 4),
                                       text_diffs_outside=t_out, text_diffs_inside=to - t_out)
res['layers_changed_outside'] = sorted(k for k, v in res['layers'].items()
                                       if v['outside_polygons'] or v['text_diffs_outside'])
res['layers_changed_inside'] = sorted(k for k, v in res['layers'].items()
                                      if v['inside_polygons'] or v['text_diffs_inside'])
json.dump(res, open(out_p, 'w'), indent=1)
print(json.dumps({k: res[k] for k in ('layers_changed_outside', 'layers_changed_inside')}))
print(json.dumps(res['layers'].get('5/22')))
