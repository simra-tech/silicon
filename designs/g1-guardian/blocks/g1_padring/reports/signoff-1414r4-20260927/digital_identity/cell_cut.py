# Write one cell with its sub-hierarchy from a GDS to a new GDS (no timestamps, no context info), for byte comparison.
#   klayout -b -r cell_cut.py -rd src=<gds> -rd cell=<cell> -rd out=<gds>
import pya
ly = pya.Layout(); ly.read(src)
c = ly.cell(cell); assert c is not None
o = pya.SaveLayoutOptions(); o.format = 'GDS2'; o.gds2_write_timestamps = False; o.write_context_info = False
o.clear_cells(); o.add_cell(c.cell_index())
ly.write(out, o)
