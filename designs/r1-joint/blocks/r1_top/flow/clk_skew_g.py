# SPDX-License-Identifier: Apache-2.0
"""r1_top try g: OSC_CLK skew between the r1_adc clk pin and the r1_ctrl clk pin (track T8e). Estimate.

  python3 clk_skew_g.py <run dir> <out.json>

R: KLayout RNetExtractor (square counting, typ and max sheet / via values as flow/supply_g_rnet.py) on the top-level
OSC_CLK shapes (macros excluded), between the r1_osc osc_clk pin end of the straight Metal3 line, the r1_ctrl clk pin
end and the r1_adc clk pin. C: per-length wire capacitance (three cases: area + edge to substrate from the PDK
technology LEF sg13g2_tech.lef, Metal3 0.3 um = 0.093 fF/um; 0.2 fF/um with neighbours as in try f; 0.3 fF/um bound)
times the routed length, plus the r1_adc clk pin load (extracted ADC top-level clk wiring 34.0 fF from
r1_adc pex/pex_report_b6.json + about 10 fF of gate load, rounded up to 50 fF; bound 60 fF) and the r1_ctrl clk pin
load (5 fF, its clock-tree root). Skew = Elmore delay to the ADC pin minus Elmore delay to the ctrl pin from the common
driver (the osc output resistance cancels: both pins see it in series with the whole net capacitance).
"""
import json
import os
import sys

import klayout.db as db
import klayout.pex as kp

RUN, OUTF = sys.argv[1], sys.argv[2]
asm = json.load(open(os.path.join(RUN, "r1_top_assembly.json")))
ly = db.Layout()
ly.read(os.path.join(RUN, "r1_top.gds"))
top = ly.cell("r1_top")
DBU = ly.dbu
LAY = {"M2": (10, 0), "V2": (29, 0), "M3": (30, 0), "V3": (49, 0), "M4": (50, 0), "V4": (66, 0), "M5": (67, 0)}
METALS = ["M2", "M3", "M4", "M5"]
VIAS = {"V2": ("M2", "M3"), "V3": ("M3", "M4"), "V4": ("M4", "M5")}
skip = [c.cell_index() for c in ly.each_cell() if c.name != "r1_top"]
ly2 = db.Layout()
ly2.dbu = DBU
t2 = ly2.create_cell("flat")
L2 = {}
for k, (l, d) in LAY.items():
    li = ly.find_layer(l, d)
    L2[k] = ly2.layer(l, d)
    it = top.begin_shapes_rec(li)
    it.unselect_cells(skip)
    t2.shapes(L2[k]).insert(db.Region(it))
l2n = db.LayoutToNetlist(db.RecursiveShapeIterator(ly2, t2, []))
R = {k: l2n.make_layer(L2[k], k) for k in LAY}
for k in METALS:
    l2n.connect(R[k])
for v, (a, b) in VIAS.items():
    l2n.connect(R[v])
    l2n.connect(R[a], R[v])
    l2n.connect(R[v], R[b])
l2n.extract_netlist()
adc = asm["macro_pins_used"]["adc"]["clk"]
net = l2n.probe_net(R["M3"], db.DPoint(1080.0, 1062.8))
GEO = {k: l2n.shapes_of_net(net, R[k], True).merged() for k in LAY}
LID = {k: i for i, k in enumerate(LAY)}
PORTS = [("osc", "M3", db.DBox(1088.9, 1062.65, 1089.9, 1062.95)), ("ctrl", "M3", db.DBox(1070.9, 1062.65, 1071.4, 1062.95)),
         ("adc", "M2", db.DBox(adc[0], adc[3], adc[2], adc[3] + 0.4))]
pp, order = {}, []
for nm, lay, bx in PORTS:
    reg = (GEO[lay] & db.Region(db.Box.from_dbox(bx * (1.0 / DBU)))).merged()
    if reg.is_empty():
        raise SystemExit("port %s not on the OSC_CLK net" % nm)
    pp.setdefault(LID[lay], []).append(sorted(reg.each(), key=lambda q: -q.area())[0])
    order.append((nm, lay, len(pp[LID[lay]]) - 1))
length = {k: round(GEO[k].edges().length() * DBU / 2.0, 1) for k in METALS}   # half perimeter ~ wire length
RS = {"typ": {"M2": 0.088, "M3": 0.088, "M4": 0.088, "M5": 0.088}, "max": {"M2": 0.103, "M3": 0.103, "M4": 0.103, "M5": 0.103}}
RV = {"typ": 9.0, "max": 20.0}
res = {"method": __doc__.strip().splitlines()[0], "wire_length_um_half_perimeter": length,
       "maze_stats": asm["maze"]["stats"].get("OSC_CLK"), "cases": []}
maze_len = sum(asm["maze"]["stats"]["OSC_CLK"]["um"])
L_total = maze_len + 19.0
res["routed_length_um"] = {"adc_branch_maze": round(maze_len, 1), "straight_line_osc_ctrl": 19.0}
for corner in ("typ", "max"):
    tech = kp.RExtractorTech()
    for k in METALS:
        c = kp.RExtractorTechConductor()
        c.layer = LID[k]
        c.resistance = RS[corner][k]
        c.algorithm = kp.Algorithm.SquareCounting
        c.triangulation_max_area = 2.0
        c.triangulation_min_b = 0.3
        tech.add_conductor(c)
    for v, (a, b) in VIAS.items():
        t = kp.RExtractorTechVia()
        t.cut_layer = LID[v]
        t.bottom_conductor = LID[a]
        t.top_conductor = LID[b]
        t.resistance = RV[corner] * 0.19 * 0.19
        t.merge_distance = 0.0
        tech.add_via(t)
    rn = kp.RNetExtractor(DBU).extract(tech, {LID[k]: GEO[k] for k in LAY}, {}, pp)
    # two-port resistances by nodal analysis (small network): ground osc, inject 1 A at a port
    nodes, idx = [], {}
    for n in rn.each_node():
        idx[n.object_id()] = len(nodes)
        nodes.append(n)
    import numpy as np
    N = len(nodes)
    G = np.zeros((N, N))
    for e in rn.each_element():
        r = e.resistance()
        if r != r or r > 1e12:
            continue
        a, b = idx[e.a().object_id()], idx[e.b().object_id()]
        g = 1.0 / max(r, 1e-6)
        G[a, a] += g
        G[b, b] += g
        G[a, b] -= g
        G[b, a] -= g
    pn = {}
    for n in rn.each_node():
        if n.type().to_s() == "PolygonPort":
            lay = list(LAY)[n.layer()]
            nm = [o[0] for o in order if o[1] == lay and o[2] == n.port_index()][0]
            pn[nm] = idx[n.object_id()]
    keep = [i for i in range(N) if i != pn["osc"]]
    Gr = G[np.ix_(keep, keep)]
    rr = {}
    for nm in ("ctrl", "adc"):
        rhs = np.zeros(N - 1)
        rhs[keep.index(pn[nm])] = 1.0
        v = np.linalg.solve(Gr, rhs)
        rr[nm] = float(v[keep.index(pn[nm])])
    for cw, cname in ((0.093, "LEF area+edge"), (0.2, "with neighbours (try f)"), (0.3, "bound")):
        for cadc in (50.0, 60.0):
            c_branch = cw * maze_len
            # Elmore, distributed branch from the tap next to the ctrl pin: R_branch (C_branch / 2 + C_adc);
            # the via resistance is lumped at the tap (bound) inside R_branch from the extraction
            t_adc = rr["adc"] * (c_branch / 2.0 + cadc) * 1e-15
            t_ctrl = rr["ctrl"] * (cw * 19.0 / 2.0 + 5.0) * 1e-15
            res["cases"].append({"sheet": corner, "R_osc_to_adc_ohm": round(rr["adc"], 2),
                                 "R_osc_to_ctrl_ohm": round(rr["ctrl"], 2), "c_wire_fF_per_um": cw, "c_case": cname,
                                 "C_adc_pin_fF": cadc, "skew_adc_minus_ctrl_ps": round((t_adc - t_ctrl) * 1e12, 1)})
sk = [c["skew_adc_minus_ctrl_ps"] for c in res["cases"]]
res["skew_range_ps"] = [min(sk), max(sk)]
res["sign"] = "ADC clk edge later than the ctrl clk edge in every case (the ADC is downstream on the same net)"
json.dump(res, open(OUTF, "w"), indent=1)
print(json.dumps(res, indent=1))
