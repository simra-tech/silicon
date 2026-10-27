# diagnostic (layout B4): list the shapes of a layer in a box, with the cell name. klayout -b -r probe_shapes.py -rd gds=<gds>
import pya
ly = pya.Layout(); ly.read(gds)
top = ly.top_cell()
def shapes(l, d, box):
    li = ly.find_layer(l, d)
    out = []
    it = top.begin_shapes_rec_overlapping(li, pya.DBox(*box))
    while not it.at_end():
        b = it.shape().dbbox().transformed(it.dtrans())
        out.append((it.cell().name, round(b.left,3), round(b.bottom,3), round(b.right,3), round(b.top,3)))
        it.next()
    return out
for name, l, box in ((n_, (int(a_), 0), tuple(float(v) for v in b_.split(','))) for n_, a_, b_ in [q.split(':') for q in probes.split(';')]):
    s = shapes(l[0], l[1], box)
    print(name, len(s))
    for x in s[:40]: print('  ', x)
