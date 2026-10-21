# Compare the IO cell order and orientation of two rings. klayout -b -r flow/compare_order.py -rd a=<gds a> -rd b=<gds b> -rd out=<json>
import pya, json
def slots(path):
    ly = pya.Layout(); ly.read(path); T, = ly.top_cells(); r = {}
    for inst in T.each_inst():
        n = inst.cell.name
        if 'IOPad' not in n: continue
        t = inst.trans; x, y = t.disp.x, t.disp.y; bb = inst.bbox(); c = bb.center()
        D = T.bbox().width(); dx, dy = c.x - D / 2, c.y - D / 2
        if abs(dy) >= abs(dx): key = ('S', c.x) if dy < 0 else ('N', c.x)
        else: key = ('W', c.y) if dx < 0 else ('E', c.y)
        r.setdefault(key[0], []).append((key[1], n.replace('retained_fullchip_sg13g2_', ''), t.angle, t.is_mirror()))
    pads = []
    for s in ('S', 'E', 'N', 'W'):
        pads += [(s, nm, ang, mir) for _, nm, ang, mir in sorted(r[s])]
    return pads
A, B = slots(a), slots(b)
res = {'pads_a': len(A), 'pads_b': len(B), 'identical_order_type_orientation': A == B, 'slots': [list(x) for x in B]}
json.dump(res, open(out, 'w'), indent=1); print(res['pads_a'], res['pads_b'], res['identical_order_type_orientation'])
