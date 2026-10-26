# probe: shapes of the nmos PCell at w 0.2 um, l 0.5 um
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import adc_lib, g1_layout_lib as G, pya
ly = pya.Layout(); ly.dbu = 0.001; c = ly.create_cell('t'); D = G.Draw(ly, c)
cell = D.pcell('nmos', {'w': '0.2u', 'l': '0.5u', 'ng': 1}, 0, 0)
for li in ly.layer_indexes():
    info = ly.get_info(li)
    for s in cell.begin_shapes_rec(li).each() if False else []:
        pass
    it = cell.begin_shapes_rec(li)
    while not it.at_end():
        b = it.shape().bbox().transformed(it.trans())
        print(info.layer, info.datatype, '(%.3f %.3f %.3f %.3f)' % (b.left/1000, b.bottom/1000, b.right/1000, b.top/1000))
        it.next()
