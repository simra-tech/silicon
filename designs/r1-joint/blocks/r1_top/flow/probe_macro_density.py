# Per-instance density (drawn + fill datatype 22) of the top-cell instances, per fill layer. klayout -b -r probe_macro_density.py -rd g=<gds>
import klayout.db as db
ly = db.Layout(); ly.read(g); top = ly.cell('r1_top'); dbu = ly.dbu
L = {'Activ': 1, 'GatPoly': 5, 'Metal1': 8, 'Metal2': 10, 'Metal3': 30, 'Metal4': 50, 'Metal5': 67, 'TM1': 126, 'TM2': 134}
def reg(cell, l):
    r = db.Region()
    for d in (0, 22):
        li = ly.find_layer(l, d)
        if li is not None:
            r += db.Region(cell.begin_shapes_rec(li))
    return r.merged()
print('%-14s %9s ' % ('instance', 'area um2') + ' '.join('%7s' % k for k in L))
for inst in top.each_inst():
    n = inst.cell.name
    if n.startswith('sg13g2') or n in ('r1_padring', 'r1_ls'):
        continue
    b = inst.bbox(); box = db.Region(b)
    out = []
    for k, l in L.items():
        r = db.Region(inst.cell.begin_shapes_rec(ly.find_layer(l, 0))) if False else None
    # instance contents placed in top coordinates
    tmp = db.Region()
    row = []
    for k, l in L.items():
        r = db.Region()
        for d in (0, 22):
            li = ly.find_layer(l, d)
            if li is not None:
                r += db.Region(top.begin_shapes_rec(li)) & box if False else db.Region(inst.cell.begin_shapes_rec(li)).transformed(inst.trans)
        row.append(r.merged().area() / box.area() * 100)
    print('%-14s %9.0f ' % (n, box.area() * dbu * dbu) + ' '.join('%6.1f%%' % v for v in row))
