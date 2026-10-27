"""layout-B diagnosis: dump the polygons (boxes) of selected nets of one circuit of an .lvsdb to JSON.
klayout -b -r dev/net_dump.py -rd db=<lvsdb> -rd circuit=<name> -rd nets=a,b,c -rd out=<json>"""
import json, pya
l2n = pya.LayoutVsSchematic(); l2n.read(globals()['db'])
nl = l2n.netlist(); c = nl.circuit_by_name(globals()['circuit'])
want = globals()['nets'].split(',')
dbu = l2n.internal_layout().dbu
res = {}
for x in c.each_net():
    nm = x.expanded_name()
    if nm not in want:
        continue
    d = {}
    for ln in l2n.layer_names():
        li = l2n.layer_by_name(ln)
        r = l2n.shapes_of_net(x, li, False)
        bx = []
        for p in r.each():
            for q in pya.Region(p).decompose_trapezoids_to_region().each():
                b = q.bbox().to_dtype(dbu); bx.append([round(b.left, 3), round(b.bottom, 3), round(b.right, 3), round(b.top, 3)])
        if bx:
            d[ln] = bx      # derived lvsdb layer names (l10 Metal1 ... l20 TopMetal1, see plot_nets.py)
    res[nm] = d
json.dump(res, open(globals()['out'], 'w'))
print({k: {l: len(v) for l, v in d.items()} for k, d in res.items()})
