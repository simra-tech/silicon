# T2l (layout B6): Metal5 (67/0) area of r1_adc.gds by source: per child cell (flattened), and in the top cell split by
# overlap with MIM (36/0, i.e. MIM bottom plates) and by y band. Density = area / box area.
# usage: klayout -b -r m5_breakdown.py -rd gds=<gds>
import pya
ly = pya.Layout(); ly.read(gds)
top = ly.cell('r1_adc')
dbu = ly.dbu
m5 = ly.layer(67, 0); mim = ly.layer(36, 0); tm1 = ly.layer(126, 0)
box = top.bbox()
A = box.area() * dbu * dbu
allm5 = pya.Region(top.begin_shapes_rec(m5)).merged()
print('box %.2f x %.2f um, area %.1f um2; Metal5 total %.1f um2 = %.2f %%' % (box.width() * dbu, box.height() * dbu, A, allm5.area() * dbu * dbu, 100 * allm5.area() * dbu * dbu / A))
mimr = pya.Region(top.begin_shapes_rec(mim)).merged()
print('  over MIM (sized 0.6 um): %.1f um2' % ((allm5 & mimr.sized(600)).area() * dbu * dbu))
own = pya.Region(top.shapes(m5)).merged()
print('  top cell own shapes: %.1f um2' % (own.area() * dbu * dbu))
for inst in top.each_inst():
    c = inst.cell
    r = pya.Region(c.begin_shapes_rec(m5)).merged()
    print('  child %s (x%d placements): %.1f um2 each' % (c.name, 1, r.area() * dbu * dbu))
for y1, y2 in ((0, 54.4), (54.4, 165.6), (165.6, 182.3), (182.3, 205.42)):
    b = pya.Region(pya.Box(0, int(y1 / dbu), box.right, int(y2 / dbu)))
    print('  band y %.1f-%.1f: %.1f um2 (own %.1f)' % (y1, y2, (allm5 & b).area() * dbu * dbu, (own & b).area() * dbu * dbu))
