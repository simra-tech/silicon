"""Dump all shapes (flattened) of a GDS inside a window.  klayout -b -r tools/dump_win.py -rd gds=<f> -rd win=x1,y1,x2,y2"""
import pya
ly = pya.Layout(); ly.read(globals()['gds']); top = ly.top_cell()
W = pya.DBox(*[float(v) for v in globals()['win'].split(',')])
for li in ly.layer_indexes():
    info = ly.get_info(li)
    it = top.begin_shapes_rec_touching(li, W)
    while not it.at_end():
        s = it.shape()
        if s.is_text():
            t = s.text.transformed(it.trans()); print('%d/%d text %s (%.3f %.3f)' % (info.layer, info.datatype, t.string, t.x * ly.dbu, t.y * ly.dbu))
        else:
            b = s.bbox().transformed(it.trans()).to_dtype(ly.dbu)
            print('%d/%d (%.3f %.3f %.3f %.3f) %s' % (info.layer, info.datatype, b.left, b.bottom, b.right, b.top, ly.cell(it.cell_index()).name[:16]))
        it.next()
