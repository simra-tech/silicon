# SPDX-License-Identifier: Apache-2.0
# Coverage of the 800 x 800 um windows (step 100 um) per metal layer of a filled r1_top, drawn + filler datatypes
# (like rules M1Fil.h...M5Fil.h: "Metalx and Metalx:filler coverage"). klayout -b -r probe_window_minmax.py -rd g=<gds> -rd out=<json>
import pya, json
ly = pya.Layout(); ly.read(g); top = ly.cell('r1_top'); dbu = ly.dbu
die = top.bbox(); W = 800000; step = 100000
res = {}
for l, n in ((8, 'Metal1'), (10, 'Metal2'), (30, 'Metal3'), (50, 'Metal4'), (67, 'Metal5')):
    r = pya.Region()
    for d in (0, 22):
        li = ly.find_layer(l, d)
        if li is not None:
            r += pya.Region(top.begin_shapes_rec(li))
    r = r.merged()
    vals = []
    x = die.left
    while x + W <= die.right:
        y = die.bottom
        while y + W <= die.top:
            w = pya.Box(x, y, x + W, y + W)
            vals.append(((r & pya.Region(w)).area() / (W * W) * 100, x * dbu, y * dbu))
            y += step
        x += step
    lo, hi = min(vals), max(vals)
    res[n] = {'min_pct': round(lo[0], 2), 'min_at_um': [lo[1], lo[2]], 'max_pct': round(hi[0], 2), 'max_at_um': [hi[1], hi[2]],
              'windows': len(vals), 'global_pct': round(r.area() / (die.width() * die.height()) * 100, 2)}
    print(n, res[n])
json.dump(res, open(out, 'w'), indent=1)
