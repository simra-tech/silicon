import pya
# Flatten a GDS for the kpex cross-check (KLayout batch Python, PDK container):
#   klayout -b -r flatten.py -rd src=<gds> -rd dst=<gds> [-rd strip=36/0,129/0]
# Lists the text objects of every child cell first (in this block they are the PDK PCells' cell-name texts on
# the TEXT 63/0 and HeatTrans 51/0 layers, not net labels, so nothing collides after flattening), flattens the
# top cell and optionally strips layers (not used for the block of record: the MIM device stays blackboxed).
ly = pya.Layout(); ly.read(src)
top = ly.top_cell()
for ci in ly.each_cell():
    if ci.cell_index() == top.cell_index():
        continue
    for li in ly.layer_indexes():
        texts = [s.text_string for s in ci.shapes(li).each() if s.is_text()]
        if texts:
            print("child", ci.name, "layer", ly.get_info(li).to_s(), "texts", len(texts), texts[:3])
try:
    strip_layers = [tuple(int(v) for v in t.split('/')) for t in strip.split(',')]
except NameError:
    strip_layers = []
top.flatten(-1, True)
for l, d in strip_layers:
    li = ly.find_layer(l, d)
    if li is not None:
        top.shapes(li).clear()
        print("stripped layer", l, d)
ly.write(dst)
print("wrote", dst)
