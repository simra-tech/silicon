#!/usr/bin/env python3
"""Flatten the channel cell r1_isense_ch of r1_isense.gds for kpex (KLayout batch), after r1_afe/pex/pex_prepare.py:
  klayout -b -r pex_prepare.py -rd gds=<in> -rd out=<flat.gds> [-rd nomim=1]
With nomim=1 the MIM (36/0) and Vmim (129/0) layers and the TopMetal1 plate inside the MIM are removed (kpex 0.3.12
has no MIM model; the plate capacitance is in the cap_cmim model and the MIM devices are added from the netlist)."""
import pya
gds = globals()['gds']; out = globals()['out']; nomim = globals().get('nomim', '1') == '1'
ly = pya.Layout(); ly.read(gds)
for c in list(ly.each_cell()):
    if c.name == 'r1_isense':
        ly.delete_cell(c.cell_index())
ch = ly.cell('r1_isense_ch')
ch.flatten(-1, True)
if nomim:
    li_m = ly.find_layer(36, 0); li_t = ly.find_layer(126, 0)
    mim = pya.Region(ch.shapes(li_m)).merged()
    tm1 = pya.Region(ch.shapes(li_t)) - mim
    ch.shapes(li_t).clear(); ch.shapes(li_t).insert(tm1)
    for (l, d) in ((36, 0), (129, 0)):
        li = ly.find_layer(l, d)
        if li is not None:
            ch.shapes(li).clear()
ly.write(out)
print('pex_prepare: channel flattened (nomim=%s), wrote %s' % (nomim, out))
