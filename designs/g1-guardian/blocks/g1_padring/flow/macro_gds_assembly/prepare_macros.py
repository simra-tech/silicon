# SPDX-License-Identifier: Apache-2.0
"""Assembly views of the macro GDS files (KLayout batch):

  klayout -b -rd out_dir=<dir> -rd strip_hi_fill=<comma list of macro names or ''> -r prepare_macros.py

For every macro of record a copy is written to <out_dir>/<macro>.gds with
  1. layer 189/0 (prBoundary drawing) removed from every cell -- the PDK density
     deck takes ANY 189/0 polygon as the chip area, so a macro boundary on 189/0
     makes the chip-level density check evaluate the maximum-density rules over
     the macro footprint (assembly 2026-09-19: "Using prBoundary (189/0) for chip
     area: 54340 um^2"); the macro boundary stays on 189/4;
  2. for the macros named in strip_hi_fill: the PDK fill cells on Metal4,
     Metal5, TopMetal1, TopMetal2 (Met4_*, Met5_*, TM1_*, TM2_*) and bare fill
     shapes (datatype 22) on those layers removed, and a no-fill rectangle
     (datatype 23) over the macro added where none exists -- the chip PDN
     stripes, the VDDA straps and the via stacks onto the Metal3 supply bars
     land on those layers (234 DRC markers with the fill in place). The plan of
     record is fill up to Metal3 inside the macros, Metal4 and above by the
     chip filler, which honours the macros' no-fill shapes.
Nothing else changes. These files are derived views for the assembly, not
views of record; the block directories hold the originals.
"""
import pya

MACROS = {
    "g1_digital":    "designs/g1-guardian/blocks/g1_ctrl/layout/g1_digital.gds",
    "g1_sense":      "designs/g1-guardian/blocks/g1_sense/layout/g1_sense_filled.gds",
    "g1_trip":       "designs/g1-guardian/blocks/g1_trip/layout/g1_trip.gds",
    "g1_gate":       "designs/g1-guardian/blocks/g1_gate/layout/g1_gate_filled.gds",
    "g1_osc":        "designs/g1-guardian/blocks/g1_osc/layout/g1_osc.gds",
    "g1_t2f":        "designs/g1-guardian/blocks/g1_t2f/layout/g1_t2f.gds",
    "g1_bgr":        "designs/g1-guardian/blocks/g1_bgr/layout/g1_bgr.gds",
    "g1_dose_macro": "designs/g1-guardian/blocks/g1_dose/layout/g1_dose_macro.gds",
    "g1_dut_macro":  "designs/g1-guardian/blocks/g1_dut/layout/g1_dut_macro.gds",
    "g1_ls_up":      "designs/g1-guardian/blocks/g1_ctrl/ls/layout/g1_ls_up.gds",
}
HI = {50: "Met4_", 67: "Met5_", 126: "TM1_", 134: "TM2_"}
out_dir = globals()["out_dir"]
strip = set(x for x in globals().get("strip_hi_fill", "").split(",") if x)

for name, path in MACROS.items():
    ly = pya.Layout(); ly.read("/work/" + path)
    top = ly.cell(name) or ly.top_cells()[0]
    # 1. prBoundary drawing
    n189 = 0
    l0 = ly.find_layer(189, 0)
    if l0 is not None:
        for c in ly.each_cell():
            n189 += c.shapes(l0).size(); c.shapes(l0).clear()
    l4 = ly.layer(189, 4)
    if pya.Region(top.begin_shapes_rec(l4)).count() == 0:
        top.shapes(l4).insert(top.bbox())
    # 2. upper-metal fill
    n_inst = 0
    if name in strip:
        kill = tuple(HI.values())
        for c in list(ly.each_cell()):
            for inst in list(c.each_inst()):
                if inst.cell.name.startswith(kill):
                    c.erase(inst); n_inst += 1
        for l in HI:
            li = ly.find_layer(l, 22)
            if li is not None:
                for c in ly.each_cell(): c.shapes(li).clear()
            nf = ly.layer(l, 23)
            if pya.Region(top.begin_shapes_rec(nf)).count() == 0:
                top.shapes(nf).insert(top.bbox())
        for c in list(ly.each_cell()):
            if c.name.startswith(kill) and c.parent_cells() == 0 and c != top:
                ly.delete_cell(c.cell_index())
    ly.write(f"{out_dir}/{name}.gds")
    print(f"{name:14s} <- {path.split('/')[-1]:24s} 189/0 removed: {n189:3d}   upper-metal fill cells removed: {n_inst}")
