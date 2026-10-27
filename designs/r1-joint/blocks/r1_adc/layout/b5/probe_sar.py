# probe the r1_adc_sar release GDS: top cell, bbox, layers, shapes near the north / south edges
import pya, sys
ly = pya.Layout(); ly.read(gds)
top = ly.top_cell()
print('top', top.name, 'bbox', top.dbbox(), 'cells', ly.cells())
for li in ly.layer_indexes():
    info = ly.get_info(li)
    r = pya.Region(top.begin_shapes_rec(li))
    if r.is_empty(): continue
    n = r.count()
    bb = r.bbox()
    # shapes in the top 1 um and bottom 1 um bands
    N = r & pya.Region(pya.Box(0, int((23.12-1.0)*1000), 439000, 23120))
    S = r & pya.Region(pya.Box(0, 0, 439000, 1000))
    print(info, n, 'bbox', bb.to_dtype(0.001), 'northband', N.count(), 'southband', S.count())
# texts
for li in ly.layer_indexes():
    it = top.begin_shapes_rec(li)
    k = 0
    while not it.at_end():
        s = it.shape()
        if s.is_text() and k < 3:
            print('text', ly.get_info(li), s.text_string, s.dbbox()); k += 1
        it.next()
