# Cut the TRIP macro subtree out of the full-chip GDS; rename the macro top and the integration-prefixed
# sub-cells back to their CDL subckt names. Geometry, layers and labels are copied unchanged.
import pya, re
src_ly = pya.Layout(); src_ly.read(src)
c = src_ly.cell(cell)
ly = pya.Layout(); ly.dbu = src_ly.dbu
top = ly.create_cell('g1_trip')
top.copy_tree(c)
ren = {'__rz_port_text_035_g1_cond': 'g1_cond', '__rz_port_text_034_g1_cmp': 'g1_cmp',
       '__rz_port_text_033_g1_cmp_regenpair4': 'g1_cmp_regenpair4'}
for x in ly.each_cell():
    if x.name in ren:
        print('rename', x.name, '->', ren[x.name]); x.name = ren[x.name]
print('tops', [t.name for t in ly.top_cells()], 'cells', sorted(x.name for x in ly.each_cell()))
ly.write(out)
