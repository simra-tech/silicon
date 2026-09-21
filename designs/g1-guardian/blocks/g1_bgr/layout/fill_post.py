# fill_g1_bgr.sh step 3 (KLayout batch): remove the temporary EdgeSeal (39/0) and Metal4/5 no-fill rectangles that
# fill_pre.py added, give the PDK fill cells macro-specific names (no clash with the chip-level fill cells of the same
# name when the macro GDS is merged into the chip) and report the fill count per layer.
#   klayout -b -r fill_post.py -rd src=<filled gds> -rd dst=<final gds>
import pya
src, dst = globals()['src'], globals()['dst']
ly = pya.Layout()
ly.read(src)
top = ly.top_cell()
for lay in ((39, 0), (50, 23), (67, 23)):
    li = ly.find_layer(*lay)
    if li is not None:
        top.shapes(li).clear()
        ly.delete_layer(li)
for ci in ly.each_cell():
    if ci.cell_index() != top.cell_index() and 'FILL_CELL' in ci.name and not ci.name.startswith(top.name):
        ci.name = top.name + '_' + ci.name
for lay, name in ((1, 'Activ'), (5, 'GatPoly'), (8, 'Metal1'), (10, 'Metal2'), (30, 'Metal3'), (50, 'Metal4'), (67, 'Metal5'),
                  (126, 'TopMetal1'), (134, 'TopMetal2')):
    li = ly.find_layer(lay, 22)
    n = pya.Region(top.begin_shapes_rec(li)).count() if li is not None else 0
    print('fill_post: %-9s fill shapes %6d' % (name, n))
print('fill_post: cells', [c.name for c in ly.each_cell() if c.cell_index() != top.cell_index() and 'FILL' in c.name])
ly.write(dst)
print('fill_post: wrote', dst, top.dbbox())
