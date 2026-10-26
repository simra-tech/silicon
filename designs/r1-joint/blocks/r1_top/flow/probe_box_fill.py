# Fill placed by the chip filler inside one instance box. klayout -b -r probe_box_fill.py -rd g=<gds> -rd cell=<instance cell>
import klayout.db as db
ly = db.Layout(); ly.read(g); top = ly.cell('r1_top'); dbu = ly.dbu
box = [i.bbox() for i in top.each_inst() if i.cell.name == cell][0]
bx = db.Region(box)
names = {1: 'Activ', 5: 'GatPoly', 8: 'Metal1', 10: 'Metal2', 30: 'Metal3', 50: 'Metal4', 67: 'Metal5', 126: 'TopMetal1', 134: 'TopMetal2'}
for l, n in names.items():
    li = ly.find_layer(l, 22)
    fill = db.Region(top.shapes(li)) if li is not None else db.Region()
    # top-cell shapes only are chip fill; fill cells are placed as instances in the top cell
    allf = db.Region(top.begin_shapes_rec(li)) if li is not None else db.Region()
    li0 = ly.find_layer(l, 0)
    drawn = db.Region(top.begin_shapes_rec(li0)) if li0 is not None else db.Region()
    print('%-9s in box: drawn %5.1f %%  fill(all) %5.1f %%' % (n, (drawn & bx).area() / bx.area() * 100, (allf & bx).area() / bx.area() * 100))
