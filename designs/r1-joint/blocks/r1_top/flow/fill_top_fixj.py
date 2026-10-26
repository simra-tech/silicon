# SPDX-License-Identifier: Apache-2.0
# fill_top.sh step 2b (KLayout batch): remove the GatPoly filler rectangles that break rule GFil.j (track T8).
#   klayout -b -r fill_top_fixj.py -rd src=<filler output> -rd dst=<gds> -rd out=<json>
# GFil.j: GatPoly:filler must extend at least 0.18 um over an Activ:filler edge it crosses (maximal deck:
# Activ_filler.ext_enclosed(GatPoly_filler, 0.18)). With the stock grid the two filler grids are commensurate and no
# rectangle breaks the rule. With a narrower GatPoly gap (fill_top.sh, gatpoly_gap_um) a part of the rectangles ends
# 0 < d < 0.18 um beyond an Activ filler edge. This step finds them with the same check, flattens the chip-level
# GatPoly filler cell placements (GatP_FILL_CELL) into top-cell shapes on 5/22, and drops the offending rectangles.
# Macro cells are not touched. A second pass proves that the check is now empty.
import pya, json
src, dst, out = globals()['src'], globals()['dst'], globals()['out']
ly = pya.Layout(); ly.read(src); top = ly.cell('r1_top')
li_a, li_p = ly.layer(1, 22), ly.layer(5, 22)
# chip-level GatPoly filler = placements of GatP_FILL_CELL in the top cell
fill_cell = ly.cell('GatP_FILL_CELL')
chip = pya.Region()
placements = []
for inst in list(top.each_inst()):
    if inst.cell_index == fill_cell.cell_index():
        placements.append(inst)
base = pya.Region(fill_cell.shapes(li_p))
for inst in placements:
    if inst.is_regular_array():
        a, b = inst.a, inst.b
        for i in range(inst.na):
            for j in range(inst.nb):
                chip.insert(base.transformed(inst.trans * pya.Trans(a.x * i + b.x * j, a.y * i + b.y * j)))
    else:
        chip.insert(base.transformed(inst.trans))
chip_rects = [p for p in chip.each()]
poly_all = pya.Region(top.begin_shapes_rec(li_p))      # chip fill + macro fill, for the check
act_f = pya.Region(top.begin_shapes_rec(li_a))
bad_marks = act_f.enclosed_check(poly_all, 180)
bad_area = pya.Region()
for ep in bad_marks.each():
    bad_area.insert(ep.bbox().enlarged(10, 10))
bad_area = bad_area.sized(10)
chip_r = chip.dup()
dropr = chip_r.interacting(bad_area)
keepr = chip_r - dropr
for inst in placements:
    inst.delete()
top.shapes(li_p).insert(keepr)
if fill_cell.parent_cells() == 0:
    ly.delete_cell(fill_cell.cell_index())     # the pattern cell is no longer used
ly.write(dst)
rep = {'chip_poly_rectangles_before': chip_r.count(), 'violating_edge_pairs': bad_marks.count(),
       'rectangles_removed': dropr.count(), 'chip_poly_rectangles_after': keepr.count()}
# second pass
chk = ly.cell('r1_top')
poly2 = pya.Region(top.begin_shapes_rec(li_p))
rep['violating_edge_pairs_after'] = act_f.enclosed_check(poly2, 180).count()
json.dump(rep, open(out, 'w'), indent=1)
print(json.dumps(rep, indent=1))
