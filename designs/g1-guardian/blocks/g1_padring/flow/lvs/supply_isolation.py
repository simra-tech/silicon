# SPDX-License-Identifier: Apache-2.0
"""Metal-only connectivity of the chip GDS: are the chip's pins on separate nets?

  klayout -b -rd gds=<chip.gds> [-rd top=g1_chip_top] -r supply_isolation.py

Extracts the connectivity of Metal1..TopMetal2 through the vias over the whole
hierarchy (no devices: a diode or a transistor does not connect), attaches the
top cell's texts (the DEF pin labels on the bondpads, <layer>/25) to the nets,
and lists every net that carries more than one distinct label: two chip pins on
one piece of metal, i.e. a short. Supply nets that must be distinct: VDD, VSS,
VDDA, IOVDD, IOVSS. Runs in a few minutes on the 1350 um chip.
"""
import pya

ly = pya.Layout(); ly.read(globals()["gds"])
top = ly.cell(globals().get("top", "g1_chip_top"))
metals = [("Metal1", 8), ("Metal2", 10), ("Metal3", 30), ("Metal4", 50), ("Metal5", 67), ("TopMetal1", 126), ("TopMetal2", 134)]
vias = [("Via1", 19, 0, 1), ("Via2", 29, 1, 2), ("Via3", 49, 2, 3), ("Via4", 66, 3, 4), ("TopVia1", 125, 4, 5), ("TopVia2", 133, 5, 6)]
l2n = pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly, top, []))
L = {}
for name, gl in metals:
    L[name] = l2n.make_layer(ly.layer(gl, 0), name)
    t = l2n.make_text_layer(ly.layer(gl, 25), name + "_txt")
    l2n.connect(L[name]); l2n.connect(L[name], t)
for name, gl, a, b in vias:
    v = l2n.make_layer(ly.layer(gl, 0), name)
    l2n.connect(v); l2n.connect(L[metals[a][0]], v); l2n.connect(L[metals[b][0]], v)
l2n.extract_netlist()
c = l2n.netlist().circuit_by_name(top.name)
labelled = []
for net in c.each_net():
    names = sorted(set(net.expanded_name().split(",")))
    if net.name:                       # nets without a label are anonymous ($n)
        labelled.append(names)
shorts = [n for n in labelled if len(n) > 1]
print(f"{top.name}: {len(labelled)} labelled nets, {len(shorts)} carrying more than one pin label")
for n in sorted(labelled):
    print("  net:", ",".join(n), "  <-- SHORT" if len(n) > 1 else "")
print("supply isolation:", "FAILED" if shorts else "passed")
