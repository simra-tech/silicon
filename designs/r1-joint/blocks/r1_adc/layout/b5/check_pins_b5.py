"""Pin check of r1_adc layout B5 (KLayout batch, pinned container, G1_WORKDIR=designs/r1-joint/blocks/r1_adc/layout):
  flow/run.sh klayout -b -r b5/check_pins_b5.py -rd gds=<gds> -rd out=<pin table .md>
Reads the top-cell pin labels (Metal2 / Metal3, datatype 25) and pin shapes (datatype 2), compares with the B5 pin list
(B4 checklist pins of r1_adc_netlist.py, north pins moved to the r1_adc_sar north pins, new pin cur_trk) and the box.
Checks: every pin present once on the box edge; supply pins >= 1.0 um wide; north pitch >= 1.6 um; x shift against B4."""
import os, sys, json
import pya
sys.path.insert(0, os.getcwd())
import r1_adc_netlist as N
gds = globals()['gds']; out = globals()['out']
ly = pya.Layout(); ly.read(gds); top = ly.cell('r1_adc')
W, H = 439.0, 205.42
bb = top.dbbox_per_layer(ly.layer(189, 4))
res = []
fails = []
labels = {}
for (l, nm) in ((10, 'Metal2'), (30, 'Metal3')):
    lt = ly.find_layer(l, 25); lp = ly.find_layer(l, 2)
    if lt is None:
        continue
    pins = pya.Region(top.shapes(lp)) if lp is not None else pya.Region()
    for s in top.shapes(lt).each():
        if not s.is_text():
            continue
        x, y = s.text.trans.disp.x * ly.dbu, s.text.trans.disp.y * ly.dbu
        hit = [p for p in pins.each() if p.bbox().contains(s.text.trans.disp)]
        if not hit:
            continue           # internal net label (sar_*, probes), not a pin
        b = hit[0].bbox().to_dtype(ly.dbu)
        labels.setdefault(s.text.string, []).append((nm, x, y, b))
b4 = {}
for side, lst in (('N', N.NORTH), ('W', N.WEST), ('E', N.EAST), ('S', N.SOUTH)):
    for n, c in lst:
        b4[n.replace('[', '<').replace(']', '>')] = (side, c)
sar = json.load(open('../sar/flow/pins.json'))['pins']
want = {}
for p in sar:
    if p['edge'] == 'N':
        want[p['net'].replace('[', '<').replace(']', '>')] = ('N', p['x'])
for n, (side, c) in b4.items():
    if side != 'N':
        want[n] = (side, c)
rows = []
for n, (side, c) in sorted(want.items(), key=lambda kv: ('NWES'.index(kv[1][0]), kv[1][1])):
    L = labels.get(n, [])
    if len(L) != 1:
        fails.append('%s: %d pin labels' % (n, len(L))); rows.append((n, side, c, None, None, None, None, None)); continue
    lay, x, y, b = L[0]
    pos = (b.center().x if side in 'NS' else b.center().y)
    edge_ok = {'N': abs(b.top - H) < 1e-3, 'S': abs(b.bottom) < 1e-3, 'W': abs(b.left) < 1e-3, 'E': abs(b.right - W) < 1e-3}[side]
    if not edge_ok:
        fails.append('%s not on the %s edge: %s' % (n, side, b))
    if abs(pos - c) > 1e-3:
        fails.append('%s at %.3f, want %.3f' % (n, pos, c))
    wid = b.width() if side in 'NS' else b.height()
    if n in ('vdd', 'vdda', 'vss', 'vref_in') and wid < 1.0 - 1e-6:
        fails.append('%s width %.2f < 1.0' % (n, wid))
    b4x = b4.get(n, (None, None))[1]
    rows.append((n, side, pos, lay, wid, b4x, None if b4x is None else round(pos - b4x, 3), '%.3f-%.3f' % ((b.bottom, b.top) if side in 'NS' else (b.left, b.right))))
extra = sorted(set(labels) - set(want))
if extra:
    fails.append('extra pin labels: %s' % extra)
nx = sorted(r[2] for r in rows if r[1] == 'N' and r[2] is not None)
pmin = min(b - a for a, b in zip(nx, nx[1:]))
if pmin < 1.6 - 1e-6:
    fails.append('north pitch %.2f < 1.6' % pmin)
box_ok = abs(bb.width() - W) < 1e-3 and abs(bb.height() - H) < 1e-3 and bb.left == 0 and bb.bottom == 0
if not box_ok:
    fails.append('box %s' % bb)
L = ['# r1_adc layout B5 pin table (written by layout/b5/check_pins_b5.py)', '',
     'Box (prBoundary 189/4): %.2f x %.2f um, origin (0, 0). Pins: %d (B4: 51, + `cur_trk`). North pitch min %.2f um.' % (bb.width(), bb.height(), len(rows), pmin),
     'Coordinates: macro frame (local), pin-shape centre along the edge. "B4" = layout B4 / checklist position.', '',
     '| Pin | Edge | Position (um) | Layer | Width (um) | B4 position (um) | Shift (um) | Span across the edge (um) |',
     '| --- | --- | --- | --- | --- | --- | --- | --- |']
for (n, side, pos, lay, wid, b4x, sh, span) in rows:
    L.append('| `%s` | %s | %s | %s | %s | %s | %s | %s |' % (n, side, '%.3f' % pos if pos is not None else 'missing', lay, '%.2f' % wid if wid else '-',
                                                     '%.2f' % b4x if b4x is not None else 'new', sh if sh is not None else '-', span))
L += ['', 'Result: **%s**' % ('passed' if not fails else 'failed'), ''] + ['- ' + f for f in fails]
open(out, 'w').write('\n'.join(L) + '\n')
print('\n'.join(L[-(len(fails) + 3):]))
