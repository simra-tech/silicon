# Layout E8 (track T3l): render a region of one cell to PNG (KLayout batch, LayoutView without GUI).
#   flow/run.sh klayout -b -r layout/tools/render_region.py -rd gds=<gds> -rd cell=r1_afe_ch -rd box=x1,y1,x2,y2 -rd layers=8/0,10/0,30/0,50/0 -rd out=<png> [-rd px=2000]
import pya
ly = pya.Layout(); ly.read(gds)
c = ly.cell(cell)
x1, y1, x2, y2 = [float(v) for v in box.split(',')]
lv = pya.LayoutView()
lv.load_layout(gds, True)
lv.max_hier()
cv = lv.cellview(0); cv.cell = lv.cellview(0).layout().cell(cell)
cols = [0xff0000, 0x00a000, 0x0000ff, 0xff00ff, 0x00c0c0, 0xc08000, 0x808080, 0x000000]
for i, L in enumerate(layers.split(',')):
    l, d = [int(v) for v in L.split('/')]
    p = pya.LayerPropertiesNode(); p.source = '%d/%d@1' % (l, d)
    p.fill_color = cols[i % len(cols)]; p.frame_color = cols[i % len(cols)]; p.dither_pattern = 5 if i else 1; p.transparent = False
    lv.insert_layer(lv.end_layers(), p)
lv.zoom_box(pya.DBox(x1, y1, x2, y2))
w = int(globals().get('px', '2000')); h = int(w * (y2 - y1) / (x2 - x1))
lv.save_image(out, w, h)
print('wrote', out)
