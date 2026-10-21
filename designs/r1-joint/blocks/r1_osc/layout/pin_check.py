#!/usr/bin/env python3
"""Pin check of an r1_osc GDS (KLayout batch): every port of the netlist of record has exactly one Metal3 pin
shape (layer 30/2) with a Metal3 label (30/25) inside it, the pin touches the prBoundary (189/4) edge, and every
signal pin (all but vdd, vss) is on the west edge (S7 floorplan constraint, 2026-10-21).
  flow/run.sh klayout -b -r designs/r1-joint/blocks/r1_osc/layout/pin_check.py -rd gds=<gds> [-rd ref=<other gds>]
With ref: also prints whether the pin names, layers and boundary size match the reference GDS."""
import pya


def pins(path):
    ly = pya.Layout()
    ly.read(path)
    top = ly.top_cell()
    bnd = pya.Region(top.begin_shapes_rec(ly.layer(189, 4))).bbox()
    pr = pya.Region(top.begin_shapes_rec(ly.layer(30, 2)))
    out = {}
    it = top.begin_shapes_rec(ly.layer(30, 25))
    while not it.at_end():
        sh = it.shape()
        if sh.is_text():
            p = it.trans() * sh.text.trans.disp
            hit = [b for b in pr.each() if b.bbox().contains(pya.Point(p.x, p.y))]
            out.setdefault(sh.text.string, []).extend(b.bbox() for b in hit)
        it.next()
    return ly, bnd, out


PORTS = ['en', 'trim0', 'trim1', 'trim2', 'trim3', 'trim4', 'osc_clk', 'vdd', 'vss']
ly, bnd, P = pins(gds)   # noqa: F821
ok = True
for n in PORTS:
    bb = P.get(n, [])
    edge = bool(bb) and any(b.left == bnd.left or b.right == bnd.right or b.bottom == bnd.bottom or b.top == bnd.top for b in bb)
    west = bool(bb) and bb[0].left == bnd.left
    good = len(bb) == 1 and edge and (west or n in ('vdd', 'vss'))   # S7: every signal pin on the west edge
    ok &= good
    print('pin %-8s shapes %d at edge %s %s' % (n, len(bb), edge, 'ok' if good else 'FAIL'))
extra = sorted(set(P) - set(PORTS))
print('extra Metal3 pin labels:', extra)
ok &= not extra
print('boundary %.3f x %.3f um' % (bnd.width() * ly.dbu, bnd.height() * ly.dbu))
try:
    _, bnd2, P2 = pins(ref)  # noqa: F821
    print('reference boundary %.3f x %.3f um; same pin names: %s' % (bnd2.width() * ly.dbu, bnd2.height() * ly.dbu, sorted(P2) == sorted(P)))
    for n in PORTS:
        side = lambda b, B: [s for s, v in (('W', b.left == B.left), ('E', b.right == B.right), ('S', b.bottom == B.bottom), ('N', b.top == B.top)) if v]
        print('  %-8s side %s (reference %s)' % (n, side(P[n][0], bnd), side(P2[n][0], bnd2)))
except NameError:
    pass
print('PIN CHECK', 'passed' if ok else 'failed')
