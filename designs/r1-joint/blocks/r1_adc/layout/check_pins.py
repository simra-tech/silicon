"""Pin check of r1_adc.gds against the floor-plan checklist (r1_adc_netlist.py NORTH/WEST/EAST/SOUTH) and the
top-level ports of r1_adc_lvs.cdl. The PDK LVS ignores top-port mismatches, so this check is separate.
  flow/run.sh klayout -b -r check_pins.py -rd gds=<gds>      (exit 1 on any mismatch)
Bus bits: labels use [k] (checklist), the CDL uses <k>; the check maps <k> to [k].
A checklist pin passes if a Metal3 pin shape (30/2) with a Metal3 label (30/25) of that name touches the box edge and
its centre is within 0.05 um of the checklist coordinate (x for north/south, y for west/east)."""
import os, sys, pya
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import r1_adc_netlist as NLM
gds = globals().get('gds', os.path.join(HERE, 'r1_adc.gds'))
ly = pya.Layout(); ly.read(gds); top = ly.top_cell(); dbu = ly.dbu
bb = top.dbbox(); W, H = bb.width(), bb.height()
pin = ly.layer(30, 2)
rp = pya.Region(top.begin_shapes_rec(pin)).merged()
boxes = [p.bbox() for p in rp.each()]
labels = {}      # Metal3 labels (30/25) for the checklist pins; any text layer (datatype 25) for the other ports
other = set()
for li in ly.layer_indexes():
    info = ly.get_info(li)
    if info.datatype != 25:
        continue
    it = top.begin_shapes_rec(li)
    while not it.at_end():
        s = it.shape()
        if s.is_text():
            t = s.text.transformed(it.trans())
            if info.layer == 30 and it.cell_index() == top.cell_index():
                labels.setdefault(t.string, []).append(pya.Point(t.x, t.y))
            other.add(t.string)
        it.next()
bad = []
print('box %.3f x %.3f um, origin (%.3f, %.3f)' % (W, H, bb.left, bb.bottom))
for side, lst in (('N', NLM.NORTH), ('W', NLM.WEST), ('E', NLM.EAST), ('S', NLM.SOUTH)):
    for n, c in lst:
        hit = None
        for p in labels.get(n, []):
            for b in boxes:
                if b.contains(p): hit = b; break
            if hit: break
        if hit is None:
            bad.append(n); print('  %-14s %s %7.2f  NO PIN SHAPE WITH LABEL' % (n, side, c)); continue
        x0, y0, x1, y1 = [v * dbu for v in (hit.left, hit.bottom, hit.right, hit.top)]
        cx, cy = (x0 + x1) / 2 - bb.left, (y0 + y1) / 2 - bb.bottom
        edge = {'N': abs(y1 - bb.top) < 0.01, 'S': abs(y0 - bb.bottom) < 0.01,
                'W': abs(x0 - bb.left) < 0.01, 'E': abs(x1 - bb.right) < 0.01}[side]
        pos = cx if side in 'NS' else cy
        ok = edge and abs(pos - c) <= 0.05
        if not ok: bad.append(n)
        print('  %-14s %s %7.2f  found %7.3f  rect (%.2f %.2f %.2f %.2f) %s' % (n, side, c, pos, x0, y0, x1, y1, 'ok' if ok else 'FAIL'))
cdl = [l.split()[2:] for l in open(os.path.join(HERE, 'r1_adc_lvs.cdl')) if l.lower().startswith('.subckt r1_adc ')][0]
edge_names = [n for lst in (NLM.NORTH, NLM.WEST, NLM.EAST, NLM.SOUTH) for n, _ in lst]
norm = lambda n: n.replace('<', '[').replace('>', ']')      # the CDL writes bus bits as <k>
cdl = [norm(n) for n in cdl]
miss = [n for n in edge_names if n not in cdl]
nolab = [n for n in cdl if n not in labels and n not in other]
print('CDL top ports %d; checklist pins missing from CDL: %s; CDL ports without a label: %s' % (len(cdl), miss, nolab))
ok = not bad and not miss and not nolab
print('PIN CHECK:', 'PASS (%d checklist pins)' % len(edge_names) if ok else 'FAIL %s' % (bad + miss + nolab))
sys.exit(0 if ok else 1)
