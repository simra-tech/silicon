"""Print the shapes of one extracted net (from a .lvsdb) inside a window, per layer. For short and open hunting.
klayout -b -r tools/net_shapes.py -rd db=<lvsdb> -rd circuit=<name> -rd net=<layout net name> [-rd win=x1,y1,x2,y2] [-rd n=40]"""
import pya
l2n = pya.LayoutVsSchematic(); l2n.read(globals()['db'])
nl = l2n.netlist(); c = nl.circuit_by_name(globals()['circuit'])
want = globals()['net']; n = int(globals().get('n', '40'))
win = [float(v) for v in globals().get('win', '-1e9,-1e9,1e9,1e9').split(',')]
W = pya.DBox(*win)
net = None
for x in c.each_net():
    if x.expanded_name() == want or x.name == want: net = x; break
if net is None: raise SystemExit('no net %s' % want)
dbu = l2n.internal_layout().dbu
for ln in l2n.layer_names():
    li = l2n.layer_by_name(ln)
    r = l2n.shapes_of_net(net, li, True)
    k = 0
    for p in r.each():
        b = p.bbox().to_dtype(dbu)
        if b.overlaps(W) or b.inside(W):
            if k < n: print('%-12s (%.2f %.2f %.2f %.2f)' % (ln, b.left, b.bottom, b.right, b.top))
            k += 1
    if k: print('  %s: %d shapes in window' % (ln, k))
