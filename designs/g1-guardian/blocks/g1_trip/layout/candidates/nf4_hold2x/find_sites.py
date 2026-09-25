import pya
ly = pya.Layout(); ly.read(macro); top = ly.top_cell(); dbu = ly.dbu
box = pya.Region(top.bbox())
def R(cell, l, d, lay=ly):
    li = lay.find_layer(l, d)
    return pya.Region() if li is None else pya.Region(cell.begin_shapes_rec(li))
blk = R(top,67,0) + R(top,126,0) + R(top,36,0) + R(top,66,0) + R(top,125,0)
pl = pya.Layout(); pl.read(parent); ptop = pl.cell('placed_core_NOT_CONNECTED_FULLCHIP')
off = pya.Trans(pya.Vector(-771000, -736000))
for (l,d) in ((67,0),(126,0),(36,0),(66,0),(125,0)):
    li = pl.find_layer(l,d)
    if li is None: continue
    blk += (pya.Region(ptop.shapes(li)).transformed(off) & box)
    for inst in ptop.each_inst():
        if pl.cell(inst.cell_index).name == '__rz_port_text_033_retained_g1_trip': continue
        if not inst.bbox().overlaps(pya.Box(771000,736000,1000000,943000)): continue
        blk += (pya.Region(pl.cell(inst.cell_index).begin_shapes_rec(li)).transformed(inst.cplx_trans).transformed(off) & box)
blk.merge()
print('parent TM1 over macro:', [str(p.bbox().transformed(pya.CplxTrans(dbu))) for p in (blk).each()][:40])
cmps = []
for inst in top.each_inst():
    n = ly.cell(inst.cell_index).name
    if n in ('g1_cmp','g1_cmp_regenpair4'): cmps.append(inst.bbox().enlarged(3000,3000))
keep = blk.sized(int(2.1/dbu))   # MIM(26) + M5 0.6 + 1.5 spacing to other upper-metal shapes
for c in cmps: keep += pya.Region(c)
keep += pya.Region(pya.Box(0, int(201.5/dbu)-1500, int(229/dbu), int(207/dbu)))   # IOVDD/VDD bar zone
keep.merge()
caps = {'CHS': (97.5,158.5), 'CHH': (162.5,158.5), 'CH': (59.06,163.0)}
sites = []
y = 3.5
while y + 26 <= 196:
    x = 3.5
    while x + 26 <= 225.5:
        sq = pya.Region(pya.Box(int(x/dbu), int(y/dbu), int((x+26)/dbu), int((y+26)/dbu)))
        if (sq & keep).is_empty(): sites.append((x, y))
        x += 0.5
    y += 0.5
print('free sites', len(sites))
for n, (cx, cy) in caps.items():
    best = sorted(sites, key=lambda s: abs(s[0]-cx) + abs(s[1]-cy))[:5]
    print(n, 'nearest free 26x26 MIM origins:', best)
