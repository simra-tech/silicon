# SPDX-License-Identifier: Apache-2.0
# fill_top.sh step 1 (KLayout batch): prepare the r1_top chip GDS for the stock PDK filler (track T8).
#   klayout -b -r fill_top_pre.py -rd src=<r1_top.gds> -rd dst=<prefill.gds> -rd out=<exclusions.json> [-rd ring_depth=0] [-rd thru=r1_ctrl_top:10] [-rd halo=1.0]
# The PDK filler macros fill every place inside the sealring hole (EdgeSeal 39/0 holes) that is free of drawn metal, of
# the layer's own no-fill shapes (<layer>/23) and of NoMetFiller (160/0). This step draws temporary no-fill shapes on
# the nine fill layers (Activ, GatPoly, Metal1-5, TopMetal1-2) in one temporary cell T8_TMP_NOFILL:
#   1. every macro and standard-cell instance of the top cell (bounding box + halo), except the pad ring instance;
#      this includes the ADC placeholder r1_adc_ph (the ADC macro brings its own fill later);
#      Option thru=<cell>:<layer>[,<layer>...][;<cell>:...] (layer = GDS layer number of the fill layer) lets the chip
#      filler fill over that instance on those layers only (the macro is not edited; the fill is top-cell shapes);
#   2. the pad ring band: the die minus a core window inset by ring_depth um on every side (IO cells, corner cells,
#      IO fillers, bond pads);
#   3. every bond opening (Passiv 9/0 polygon narrower than 200 um) plus 10 um.
# Unreferenced PDK fill pattern cells of an earlier fill run are deleted so that the filler creates clean cell names.
# fill_top_post.py removes the temporary cell again.
import pya, json
src, dst, out = globals()['src'], globals()['dst'], globals()['out']
RING_DEPTH = float(globals().get('ring_depth', 0.0))
HALO = float(globals().get('halo', 1.0))
THRU = {}
for item in str(globals().get('thru', '')).split(';'):
    if item:
        c, ls = item.split(':')
        THRU[c] = {int(v) for v in ls.split(',')}
NOFILL = [(1, 23), (5, 23), (8, 23), (10, 23), (30, 23), (50, 23), (67, 23), (126, 23), (134, 23)]
ly = pya.Layout()
ly.read(src)
dbu = ly.dbu
top = ly.cell('r1_top')
# unreferenced pattern cells of an earlier filler run (other than the top)
orphans = [c.cell_index() for c in ly.each_cell() if c.cell_index() != top.cell_index() and c.parent_cells() == 0]
names = sorted(ly.cell(i).name for i in orphans)
for i in orphans:
    ly.delete_cell(i)
um = lambda v: int(round(v / dbu))
die = top.bbox()
excl = pya.Region()
thru_boxes = {}   # layer -> region of instance boxes that stay fillable on that layer
rep = {'thru': {k: sorted(v) for k, v in THRU.items()}, 'ring_depth_um': RING_DEPTH, 'halo_um': HALO, 'deleted_orphan_cells': names, 'instances': []}
for inst in top.each_inst():
    if inst.cell.name == 'r1_padring':
        continue
    b = inst.bbox().enlarged(um(HALO), um(HALO))
    excl.insert(b)
    for l in THRU.get(inst.cell.name, ()):
        thru_boxes.setdefault(l, pya.Region()).insert(b)
    rep['instances'].append({'cell': inst.cell.name, 'bbox_um': [round(v, 3) for v in (inst.bbox().left * dbu, inst.bbox().bottom * dbu, inst.bbox().right * dbu, inst.bbox().top * dbu)]})
band = pya.Region(die) - pya.Region(die.enlarged(-um(RING_DEPTH), -um(RING_DEPTH)))
li9 = ly.find_layer(9, 0)
ops = pya.Region()
if li9 is not None:
    for p in pya.Region(top.begin_shapes_rec(li9)).merged().each():
        if p.bbox().width() < um(200):
            ops.insert(p)
ops = ops.sized(um(10.0))
rep['bond_openings'] = ops.count()
excl_all = (excl + band + ops).merged()
tmp = ly.create_cell('T8_TMP_NOFILL')
for l, d in NOFILL:
    li = ly.layer(l, d)
    e = excl_all
    if l in thru_boxes:
        e = (excl_all - thru_boxes[l].merged()) + ((band + ops).merged() & thru_boxes[l].merged())
        e = e.merged()
    tmp.shapes(li).insert(e)
excl = excl_all
top.insert(pya.CellInstArray(tmp.cell_index(), pya.Trans()))
rep['excluded_area_um2'] = round(excl.area() * dbu * dbu, 1)
rep['die_um'] = [die.width() * dbu, die.height() * dbu]
ly.write(dst)
json.dump(rep, open(out, 'w'), indent=1)
print('fill_top_pre: deleted %d orphan cells, excluded area %.0f um2 (%d instances, %d bond openings), wrote %s' % (len(names), rep['excluded_area_um2'], len(rep['instances']), rep['bond_openings'], dst))
