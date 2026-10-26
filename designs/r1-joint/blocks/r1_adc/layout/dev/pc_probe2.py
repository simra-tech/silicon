# probe: which MOS PCell parameter sets fall back to minimum width
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import adc_lib, g1_layout_lib as G, pya
ly = pya.Layout(); ly.dbu = 0.001; c = ly.create_cell('t'); D = G.Draw(ly, c)
for kind, w, l, ng in [('pmos', 20, 0.13, 1), ('nmos', 16, 0.13, 1), ('pmos', 80, 4, 4), ('nmos', 30, 4, 2), ('pmos', 10, 0.13, 1), ('pmos', 12, 0.13, 1), ('pmos', 48, 0.3, 4), ('nmos', 6, 0.13, 2), ('pmos', 20, 0.13, 2)]:
    cell = D.pcell(kind, {'w': '%gu' % w, 'l': '%gu' % l, 'ng': ng}, 0, 0)
    b = pya.Region(cell.begin_shapes_rec(ly.layer(1, 0))).bbox()
    print(kind, w, l, ng, 'Activ bbox h=%.3f w=%.3f' % (b.height() * 0.001, b.width() * 0.001))
