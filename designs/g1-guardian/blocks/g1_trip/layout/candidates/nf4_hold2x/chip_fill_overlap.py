import pya
ly = pya.Layout(); ly.read(cand); top = ly.top_cell()
nf = pya.Region()
for l in (50, 67, 126, 134):
    li = ly.find_layer(l, 23)
    nf += pya.Region(top.shapes(li))
base = pya.Layout(); base.read(orig); bt = base.top_cell()
nf0 = pya.Region()
for l in (50, 67, 126, 134):
    li = base.find_layer(l, 23)
    if li is not None: nf0 += pya.Region(bt.shapes(li))
def L(lay, cell, l, d):
    li = lay.find_layer(l, d)
    return pya.Region() if li is None else pya.Region(cell.begin_shapes_rec(li))
newm = ((L(ly, top, 67, 0) - L(base, bt, 67, 0)) + (L(ly, top, 126, 0) - L(base, bt, 126, 0))).merged()
print('new Metal5+TopMetal1 area um2', newm.area()*1e-6)
new_nf = newm.sized(1500).merged()
print('new no-fill area um2', new_nf.area()*1e-6, [str(p.bbox().transformed(pya.CplxTrans(0.001))) for p in new_nf.each()])
pl = pya.Layout(); pl.read(parent); pt = pl.cell('placed_core_NOT_CONNECTED_FULLCHIP')
off = pya.Trans(pya.Vector(-771000, -736000))
box = pya.Region(pya.Box(0,0,229000,207000))
for l, d in ((50,22),(67,22),(126,22),(134,22),(50,0),(67,0),(126,0),(134,0)):
    li = pl.find_layer(l, d)
    if li is None: continue
    r = pya.Region(pt.begin_shapes_rec(li)).transformed(off) & box
    # exclude the macro's own shapes (the macro instance sits in pt)
    mi = [i for i in pt.each_inst() if pl.cell(i.cell_index).name == '__rz_port_text_033_retained_g1_trip'][0]
    own = pya.Region(pl.cell(mi.cell_index).begin_shapes_rec(li)).transformed(mi.cplx_trans).transformed(off)
    r = r - own
    ov = r & new_nf
    print('parent %d/%d over macro: %.1f um2; inside the new no-fill boxes: %.1f um2 (%d shapes)' % (l, d, r.area()*1e-6, ov.area()*1e-6, ov.count()))
