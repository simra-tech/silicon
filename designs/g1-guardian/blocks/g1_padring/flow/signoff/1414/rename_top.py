"""Rename top cell placed_core_NOT_CONNECTED_FULLCHIP -> g1_chip_top; no geometry change.
Run in the pinned container: klayout -b -r rename_top.py -rd src=<in.gds> -rd dst=<out.gds>"""
import pya, hashlib
SRC_SHA = '60730627d24e1fb6b880138edc3e50fdd7c14624bb2dfbbc631e084b7415eca1'
OLD, NEW = 'placed_core_NOT_CONNECTED_FULLCHIP', 'g1_chip_top'
assert hashlib.sha256(open(src, 'rb').read()).hexdigest() == SRC_SHA
ly = pya.Layout(); ly.read(src)
tops = list(ly.top_cells()); assert len(tops) == 1 and tops[0].name == OLD, [t.name for t in tops]
assert not ly.has_cell(NEW), 'target name already used'
tops[0].name = NEW
opt = pya.SaveLayoutOptions(); opt.format = 'GDS2'; opt.gds2_write_timestamps = False  # deterministic bytes
ly.write(dst, opt)
print('wrote', dst, 'cells', ly.cells(), 'dbu', ly.dbu)
