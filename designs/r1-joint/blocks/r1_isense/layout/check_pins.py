"""Pin check of r1_isense.gds (KLayout batch): every Metal3 pin shape (30/2) of the top cell with its label (30/25) must
touch the cell boundary (prBoundary 189/4), and the set of pin names must equal the ports of the top subcircuit of the
LVS CDL (the PDK LVS ignores top-port mismatches by default, so a missing label is not an LVS error).
  klayout -b -r check_pins.py -rd gds=<gds> -rd cdl=<cdl>          (after t2f/layout/check_pins.py, LEF-free form)"""
import pya
gds = globals()['gds']; cdl = globals()['cdl']
ly = pya.Layout(); ly.read(gds)
top = ly.cell('r1_isense')
bnd = pya.Region(top.begin_shapes_rec(ly.layer(189, 4))).bbox()
pinr = pya.Region(top.shapes(ly.layer(30, 2)))
labels = {}
for s in top.shapes(ly.layer(30, 25)).each():
    if s.is_text():
        labels.setdefault(s.text_string, []).append(s.text.trans.disp)
pins = {}
for p in pinr.each():
    b = p.bbox()
    names = [n for n, pts in labels.items() if any(b.contains(q) for q in pts)]
    for n in names:
        pins.setdefault(n, []).append(b)
ports = [l.split()[2:] for l in open(cdl) if l.startswith('.subckt r1_isense ')][0]
dbu = ly.dbu
print('macro r1_isense: %.3f x %.3f um, area %.2f um2' % (bnd.width() * dbu, bnd.height() * dbu, bnd.width() * bnd.height() * dbu * dbu))
bad = []
for n in sorted(pins):
    for b in pins[n]:
        e = ''.join(c for c, f in (('W', b.left <= bnd.left), ('E', b.right >= bnd.right), ('S', b.bottom <= bnd.bottom), ('N', b.top >= bnd.top)) if f) or 'interior'
        if e == 'interior':
            bad.append(n)
        print('  pin %-8s Metal3 rect (%.2f %.2f %.2f %.2f) edge %s' % (n, b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu, e))
ok = sorted(ports) == sorted(pins) and not bad
print('PIN CHECK:', 'pins equal CDL ports' if ok else 'MISMATCH ports=%s pins=%s interior=%s' % (sorted(ports), sorted(pins), bad))
