#!/usr/bin/env python3
"""Write the kpex input GDS for r1_osc: a copy of the layout without the MIM layers (KLayout batch script).

  flow/run.sh klayout -b -r designs/r1-joint/blocks/r1_osc/layout/pex_input.py -rd gds=<r1_osc.gds> \
      -rd meta=<r1_osc_layout_meta.json> -rd out=<pexin.gds>

kpex 0.3.12 has no model for the SG13G2 MIM layer: its 2.5D engine stops with KeyError '<TODO>' on any cmim
(G1 g1_osc finding, layout/pex_input.py there). MIM (36/0), Vmim (129/0), TopVia1 (125/0), TopMetal1 (126/*),
Metal5 (67/*) and Via4 (66/0) are removed. In r1_osc these layers carry only the MIM plates and their joins; every
plate connection lands on Metal4 through Via4, so every net keeps its Metal1-Metal4 part. pex_build.py inserts the
13 MIM devices again at the Via4 landing points (meta `caps`). The unnamed bank bottom-plate nets get Metal4 labels
(meta `pex_labels`: ba0..ba4, bb0..bb4) so that the extracted nets have names.
Lost by this method: the capacitance of the Metal5/TopMetal1 plates to the wiring below them and to the substrate.
"""
import json
import pya

ly = pya.Layout()
ly.read(gds)          # noqa: F821
top = ly.top_cell()
top.flatten(-1, True)
for l, d in ((36, 0), (129, 0), (125, 0), (126, 0), (126, 2), (126, 25), (67, 0), (67, 2), (67, 25), (66, 0)):
    li = ly.find_layer(l, d)
    if li is not None:
        top.shapes(li).clear()
m = json.load(open(meta))   # noqa: F821
for name, x, y in m['pex_labels']:
    t = pya.Text(name, pya.Trans(pya.Point(int(round(x * 1000)), int(round(y * 1000)))))
    top.shapes(ly.layer(50, 25)).insert(t)
ly.write(out)         # noqa: F821
print('wrote', out)
