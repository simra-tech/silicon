#!/usr/bin/env python3
"""Write the PEX input GDS: a copy of the layout without the cmim capacitor layers.

kpex 0.3.12 (KLayout-PEX) has no capacitance model for the SG13G2 MIM layer (its sg13g2 technology
lists the computed layer `cmim_top` with original layer `<TODO>`) and its 2.5D engine stops with
`KeyError: '<TODO>'` on any layout that contains a `cmim`.  For the extraction the MIM (36/0), Vmim
(129/0), TopVia1 (125/0), TopMetal1 (126/0), Metal5 (67/0) and Via4 (66/0) layers are removed: in
G1_TRIP and G1_OSC they are used only by the capacitors and their plate tabs (each plate's stack
ends on a Metal3 pad that stays in the netlist).  The capacitors are re-inserted as the schematic
`cap_cmim` devices by make_pex_netlist.py; what is lost is the parasitic capacitance of the plates
to the wiring underneath them.  G1_TRIP also loses ThickGateOx (44/0): with it present kpex's
technology maps a computed layer to `<TODO>` and stops the same way; the 3.3 V devices then extract
as sg13_lv_* and get their sg13_hv_* model back in make_pex_netlist.py (all L = 0.45 um devices).
The cell hierarchy is flattened (see below).

If a file <in>_pexlabels.txt exists next to the input (lines: `net layer/datatype x y`), its
labels are added so that kpex names those nets (G1_OSC: the trim-capacitor bottom-plate nets).

  klayout -b -r pex_input.py -rd gds=<in.gds> -rd out=<out.gds>
"""
import os
import pya

ly = pya.Layout()
ly.read(gds)
# flatten the cell hierarchy: kpex 0.3.12 extracts the parasitics on the flattened layout but keeps
# the device netlist hierarchical, so with sub-cells the capacitors would attach to nets that do not
# exist in the device netlist
top = ly.top_cell()
top.flatten(-1, True)
lab = gds.replace('.gds', '_pexlabels.txt')
if os.path.exists(lab):
    top = ly.top_cell()
    for line in open(lab):
        net, ld, x, y = line.split()
        l, d = [int(v) for v in ld.split('/')]
        t = pya.Text(net, pya.Trans(pya.Point(int(float(x) * 1000), int(float(y) * 1000))))
        top.shapes(ly.layer(l, d)).insert(t)
for l, d in ((36, 0), (129, 0), (125, 0), (126, 0), (67, 0), (66, 0), (126, 2), (126, 25), (67, 2), (67, 25), (44, 0)):
    li = ly.find_layer(l, d)
    if li is not None:
        for c in ly.each_cell():
            c.shapes(li).clear()
# the metal/active fill (datatype 22) and the no-fill markers (datatype 23, NoMetFiller 160/0): kpex's
# SG13G2 technology maps the drawing and pin datatypes only, so the fill is not extracted either way;
# it is removed here to keep the PEX input small (fill is floating metal, see the README)
for li in list(ly.layer_indexes()):
    info = ly.get_info(li)
    if info.datatype in (22, 23) or (info.layer, info.datatype) in ((160, 0), (39, 0), (189, 4)):
        for c in ly.each_cell():
            c.shapes(li).clear()
ly.write(out)
print('wrote', out)
