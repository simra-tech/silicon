# KLayout script: write a flattened copy of a GDS with one top cell (same geometry) for LVS and PEX tools.
# usage: klayout -b -r flatten_gds.py -rd src=<in.gds> -rd dst=<out.gds> [-rd top=r1_safe]
import pya
ly = pya.Layout()
ly.read(src)  # noqa: F821
name = globals().get('top', 'r1_safe')
t = ly.cell(name)
t.flatten(-1, True)
for c in list(ly.top_cells()):
    if c.name != name:
        ly.delete_cell_rec(c.cell_index())
ly.cleanup()
ly.write(dst)  # noqa: F821
print('flat', dst, 'cells', ly.cells(), 'top', [c.name for c in ly.top_cells()])
