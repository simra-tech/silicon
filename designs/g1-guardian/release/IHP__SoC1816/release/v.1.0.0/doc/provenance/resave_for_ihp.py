# KLayout batch script: rename the single top cell and re-save a GDS with the save
# options shown in IHP Open-Silicon-MPW fig/klayout_save.png (IP-development-steps.md,
# "Acceptance criteria" item 5) and set by March-2026/submitted-tmp/conv2sub.pv.
# No geometry is touched.
# Usage: klayout -b -r resave_for_ihp.py -rd input_file=<in.gds> -rd output_file=<out.gds> -rd newtop=<name>
import pya

ly = pya.Layout()
ly.read(input_file)
tops = ly.top_cells()
assert len(tops) == 1, "expected exactly one top cell, found %d" % len(tops)
assert not ly.has_cell(newtop), "a cell named %s already exists" % newtop
old = tops[0].name
tops[0].name = newtop

o = pya.SaveLayoutOptions()
o.format = "GDS2"
o.select_all_layers()                 # Layers to save: all layers
o.dbu = 0.001                         # Database unit 0.001 um
o.scale_factor = 1.0                  # Scaling factor 1.0
o.no_empty_cells = False              # "Don't write empty cells": unchecked
o.keep_instances = False              # "Keep instances for dropped cells": unchecked
o.write_context_info = False          # "Store PCell and library context information": unchecked
o.gds2_libname = "LIB"                # Library name LIB
o.gds2_max_cellname_length = 32000    # Max. cell name length 32000
o.gds2_max_vertex_count = 8000        # Max. vertices 8000
o.gds2_multi_xy_records = False       # Multi-XY record mode: unchecked
o.gds2_write_cell_properties = False  # Write cell properties: unchecked
o.gds2_write_file_properties = False  # Write layout properties: unchecked
o.gds2_resolve_skew_arrays = False    # Resolve skew arrays: unchecked
o.gds2_no_zero_length_paths = True    # Eliminate zero-length paths: checked
o.gds2_write_timestamps = True        # Write current time to time stamps: checked
if output_file.endswith(".gz"):
    o.compression_level = 1
ly.write(output_file, o)
print("renamed top cell %s -> %s; wrote %s" % (old, newtop, output_file))
