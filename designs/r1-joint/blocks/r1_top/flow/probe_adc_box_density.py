# SPDX-License-Identifier: Apache-2.0
# Metal3-5 coverage (drawn + filler) of a filled r1_top inside the r1_adc box (try g). klayout -b -r probe_adc_box_density.py -rd g=<gds> -rd out=<json>
import pya, json
ly = pya.Layout(); ly.read(g); top = ly.cell('r1_top'); dbu = ly.dbu
res = {}
for l, n in ((67, 'Metal5'), (50, 'Metal4'), (30, 'Metal3')):
    r = pya.Region()
    for d in (0, 22):
        li = ly.find_layer(l, d)
        if li is not None:
            r += pya.Region(top.begin_shapes_rec(li))
    r = r.merged()
    for nm, b in (("adc_box", (592.0, 376.0, 1031.0, 581.42)),):
        w = pya.Box(int(b[0]/dbu), int(b[1]/dbu), int(b[2]/dbu), int(b[3]/dbu))
        res["%s_%s" % (n, nm)] = round((r & pya.Region(w)).area() / w.area() * 100, 2)
print(json.dumps(res)); open(out, 'w').write(json.dumps(res, indent=1))
