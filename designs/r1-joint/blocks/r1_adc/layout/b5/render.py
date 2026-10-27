# render a window of a GDS to PNG with selected layers (KLayout batch LayoutView)
import pya
lv = pya.LayoutView()
lv.load_layout(gds, True)
lv.max_hier()
lv.clear_layers()
cols = {'8/0': 0x808080, '10/0': 0x0000ff, '30/0': 0x00b000, '50/0': 0xff0000, '67/0': 0xff00ff, '126/0': 0xffa500, '36/0': 0x00ffff, '1/0': 0x40ff40, '5/0': 0xb00000, '189/4': 0x000000}
for ln in layers.split(','):
    p = pya.LayerPropertiesNode(); p.source = ln + '@1'
    p.fill_color = cols.get(ln, 0x777777); p.frame_color = cols.get(ln, 0x777777); p.dither_pattern = 5 if ln not in ('126/0','67/0') else 9
    lv.insert_layer(lv.end_layers(), p)
lv.set_config('background-color', '#ffffff')
x0, y0, x1, y1 = [float(v) for v in win.split(',')]
lv.zoom_box(pya.DBox(x0, y0, x1, y1))
lv.save_image(out, int(px), int(int(px) * (y1 - y0) / (x1 - x0)))
print('ok', out)
