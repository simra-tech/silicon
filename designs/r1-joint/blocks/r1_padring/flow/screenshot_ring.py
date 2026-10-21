# PNG of the ring. klayout -b -r flow/screenshot_ring.py -rd g=<gds> -rd png=<png> [-rd w=700]  (700 px gives < 300 kB)
import pya, os
lv = pya.LayoutView(); lv.load_layout(g, True)
lyp = os.environ['PDK_ROOT'] + '/' + os.environ['PDK'] + '/libs.tech/klayout/tech/sg13g2.lyp'
if os.path.exists(lyp): lv.load_layer_props(lyp)
lv.max_hier(); lv.zoom_fit()
W = int(globals().get('w', 700)); lv.save_image(png, W, W)
print('saved', png, os.path.getsize(png))
