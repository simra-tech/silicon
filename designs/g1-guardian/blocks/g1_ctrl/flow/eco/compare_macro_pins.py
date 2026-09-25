#!/usr/bin/env python3
"""Compare two pin lists written by extract_macro_pins.py.

Usage: compare_macro_pins.py <reference.json> <candidate.json> [out.json]
Reports pin shapes (layer + box) present in only one side, labels present in
only one side, and TopMetal1/TopMetal2 drawing (power stripes) differences.
Exit 0 only if pin shapes are identical and the candidate's TopMetal1/2
drawing lies inside the reference's (swap-compatible); label
differences are reported separately (the chip cell has its unconnected-pin
labels removed by the port-text normalisation).
"""
import json
import sys


def key_pin(p):
    return (p['layer'], tuple(p['box']))


def key_lab(l):
    return (l['layer'], l['text'], l['x'], l['y'])


ref, cand = (json.load(open(f)) for f in sys.argv[1:3])
res = {'reference': sys.argv[1], 'candidate': sys.argv[2]}
rp, cp = {key_pin(p) for p in ref['pins']}, {key_pin(p) for p in cand['pins']}
rl, cl = {key_lab(l) for l in ref['labels']}, {key_lab(l) for l in cand['labels']}
res['bbox_equal'] = ref['bbox_nm'] == cand['bbox_nm']
res['pin_shapes_ref'], res['pin_shapes_cand'] = len(rp), len(cp)
res['pin_shapes_only_ref'] = sorted(rp - cp)
res['pin_shapes_only_cand'] = sorted(cp - rp)
res['labels_only_ref'] = sorted(rl - cl)
res['labels_only_cand'] = sorted(cl - rl)
res['top_metal_equal'] = {k: ref['top_metal_drawing'].get(k) == cand['top_metal_drawing'].get(k)
                          for k in ('TopMetal1', 'TopMetal2')}
def inside(b, boxes):
    return any(r[0] <= b[0] and r[1] <= b[1] and b[2] <= r[2] and b[3] <= r[3] for r in boxes)


# TopMetal drawing of the candidate must lie inside the reference's: the chip's TopMetal1
# stripes and TopMetal fill are drawn around the reference macro's TopMetal shapes
res['top_metal_subset'] = {k: all(inside(b, ref['top_metal_drawing'].get(k, []))
                                  for b in cand['top_metal_drawing'].get(k, []))
                           for k in ('TopMetal1', 'TopMetal2')}
res['pins_identical'] = (res['bbox_equal'] and not res['pin_shapes_only_ref']
                         and not res['pin_shapes_only_cand'])
res['swap_compatible'] = res['pins_identical'] and all(res['top_metal_subset'].values())
res['labels_identical'] = not res['labels_only_ref'] and not res['labels_only_cand']
if len(sys.argv) > 3:
    json.dump(res, open(sys.argv[3], 'w'), indent=1)
print(json.dumps({k: (v if not isinstance(v, list) else (len(v), v[:8])) for k, v in res.items()}, indent=1))
sys.exit(0 if res['swap_compatible'] else 1)
