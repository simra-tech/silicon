#!/usr/bin/env python3
"""Pin check for r1_bias (method of blocks/r1_t2f/layout/check_pins.py, reading the GDS instead of a LEF).

  flow/run.sh python3 designs/r1-joint/blocks/r1_bias/layout/check_pins.py <gds> <cdl> <subckt>

For every port of the top subcircuit of the LVS CDL: a Metal3 pin shape (30/2) with a Metal3 label (30/25) of the
same name must exist and touch the prBoundary (189/4). Prints the edge(s) of every pin and the metal layers used.
Needed because the PDK LVS runs with IGNORE_TOP_PORTS_MISMATCH, so a missing or misnamed pin is not an LVS error.
Exit status 1 on any mismatch.
"""
import sys

try:
    import klayout.db as pya
except ImportError:
    import pya

gds, cdl, sub = sys.argv[1:4]
ly = pya.Layout()
ly.read(gds)
top = ly.top_cell()
DBU = ly.dbu


def li(l, d):
    return ly.find_layer(l, d)


bnd = pya.Region(top.begin_shapes_rec(li(189, 4))).bbox()
W, H = bnd.width() * DBU, bnd.height() * DBU
pins = pya.Region(top.begin_shapes_rec(li(30, 2))).merged()
labels = {}
for s in top.shapes(li(30, 25)).each():
    if s.is_text():
        labels.setdefault(s.text_string, []).append(s.text.trans.disp)
ports = [l.split()[2:] for l in open(cdl) if l.startswith('.subckt ' + sub + ' ')][0]
print('macro %s: %.2f x %.2f um, area %.5f mm2' % (sub, W, H, W * H * 1e-6))
bad = []
for p in ports:
    pts = labels.get(p, [])
    found = []
    for pt in pts:
        for poly in pins.each():
            if poly.inside(pt) or poly.bbox().contains(pt):
                b = poly.bbox()
                e = ''.join(c for c, f in (('W', b.left <= bnd.left), ('E', b.right >= bnd.right),
                                          ('S', b.bottom <= bnd.bottom), ('N', b.top >= bnd.top)) if f)
                found.append((e or 'interior', (b.left * DBU, b.bottom * DBU, b.right * DBU, b.top * DBU)))
    edges = sorted({f[0] for f in found})
    ok = bool(found) and all(e != 'interior' for e in edges)
    print('  pin %-11s Metal3  edges %-10s %s' % (p, ','.join(edges) or '-', 'ok' if ok else 'MISSING OR NOT ON THE BOUNDARY'))
    if not ok:
        bad.append(p)
extra = sorted(set(labels) - set(ports))
used = []
for name, (l, d) in (('Metal1', (8, 0)), ('Metal2', (10, 0)), ('Metal3', (30, 0)), ('Metal4', (50, 0)),
                     ('Metal5', (67, 0)), ('TopMetal1', (126, 0)), ('TopMetal2', (134, 0))):
    i = li(l, d)
    if i is not None and not pya.Region(top.begin_shapes_rec(i)).is_empty():
        used.append(name)
print('metal layers used:', ' '.join(used))
mim = li(36, 0)
if mim is not None:
    mr = pya.Region(top.begin_shapes_rec(mim)).merged()
    m5 = pya.Region(top.begin_shapes_rec(li(67, 0))).merged()
    print('Metal5 outside the MIM bottom-plate margins and TopVia1 islands: %.2f um2 (plates and islands only)' % (
        (m5 - mr.sized(int(0.6 / DBU))).area() * DBU * DBU))
print('labels without a CDL port:', extra if extra else 'none')
print('PIN CHECK:', 'all %d CDL ports have a Metal3 pin on the boundary' % len(ports) if not bad else 'FAILED %s' % bad)
sys.exit(1 if bad else 0)
