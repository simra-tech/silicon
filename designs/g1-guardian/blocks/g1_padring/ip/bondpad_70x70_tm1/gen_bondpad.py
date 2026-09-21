# SPDX-License-Identifier: Apache-2.0
"""Generate the 70 x 70 um square bondpad from the PDK's own 'bondpad' PCell
(SG13_dev library), flattened, with the lower-left corner at the origin so
that OpenROAD's place_bondpad offsets (PDK default 5.0, -70.0) apply.

Metal stack TopMetal1 + TopVia2 + TopMetal2 only (PCell bottomMetal 'TM1'),
matching the IO cell's TopMetal1/TopMetal2 'pad' stub. (Chosen while chasing
the PDK antenna markers on sg13g2_IOPadIn; those turned out to come from the
cell's vdd-tied gate and are the same with either stack, see ../../README.md.
The PCell default stack, Metal3 up, is equally valid.)

Run inside KLayout batch mode with the PDK technology loaded, e.g.
  KLAYOUT_PATH=$PDK_ROOT/$PDK/libs.tech/klayout \
  klayout -zz -nc -n sg13g2 -r gen_bondpad.py -rd output=gds/bondpad_70x70_tm1.gds

Same PCell call as libs.tech/klayout/tech/scripts/bondpad.py in the PDK
(diameter 70u, shape square, top metal TopMetal2, Passiv enclosure 2.1 um)
plus bottomMetal='TM1', the origin shift and the flattening. With the PCell
default bottomMetal='3' the result is polygon-identical to
iic-jku/ihp-sg13g2-ams-chip-template ip/sg13g2_ip__bondpad_70x70 (XOR = 0).
"""
# pylint: disable=import-error,undefined-variable
import pathlib
import sys
import pya

LIB = "SG13_dev"
PCELL = "bondpad"
DIAMETER = 70.0
SHAPE = "square"
BOTTOM_METAL = "TM1"   # PCell choice: '1'..'5' or 'TM1'
CELL_NAME = "bondpad_70x70_tm1"

try:
    output  # noqa: B018  (passed with -rd output=...)
except NameError:
    print("Missing output argument. Please define '-rd output=<path>'")
    sys.exit(1)

lib = pya.Library.library_by_name(LIB, "sg13g2")
if lib is None:
    raise RuntimeError("SG13_dev PCell library not found; run klayout with -n sg13g2")
decl = lib.layout().pcell_declaration(PCELL)

layout = pya.Layout(True)
layout.dbu = 0.001
top = layout.create_cell(CELL_NAME)
pcell = layout.add_pcell_variant(lib, decl.id(), {"diameter": f"{DIAMETER}u", "shape": SHAPE, "bottomMetal": BOTTOM_METAL})
top.insert(pya.CellInstArray(pcell, pya.Trans()))
top.flatten(True)

bbox = top.bbox()
shift = pya.Trans(pya.Vector(-bbox.left, -bbox.bottom))
for li in layout.layer_indexes():
    top.shapes(li).transform(shift)
bbox = top.bbox()
print(f"{CELL_NAME}: bbox {bbox.left/1000:.3f} {bbox.bottom/1000:.3f} {bbox.right/1000:.3f} {bbox.top/1000:.3f} um")

pathlib.Path(output).parent.mkdir(parents=True, exist_ok=True)
opts = pya.SaveLayoutOptions()
opts.write_context_info = False
layout.write(output, opts)
print(f"wrote {output}")
