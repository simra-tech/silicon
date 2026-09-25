"""Generate the G1_GATE schematics (xschem).
  g1_lv_inv, g1_lv_nand2      1.2 V logic (sg13_lv_*)
  g1_hv_inv, g1_hv_nor2       3.3 V logic (sg13_hv_*), sizes from the PDK IO LevelUp cell
  g1_lvlup                    1.2 V -> 3.3 V level shifter (cross-coupled hv PMOS, structure of
                              sg13g2_LevelUp in libs.ref/sg13g2_io/spice/sg13g2_io.spi)
  g1_lvldn                    3.3 V -> 1.2 V level shifter (hv NMOS pull-downs driven by a and its
                              complement, cross-coupled lv PMOS load on vdd)
  g1_gate                     top: reset-dominant SR latch in the 3.3 V domain (thick-oxide devices,
                              large nodes: high critical charge), set by trip_d (digital) or by
                              hard_cmp & fast_en (analog fast path), cleared by en_core=0 or clr_d;
                              gate_core = en & !tripped, fault_core = !tripped, tripped -> digital.
                              All top-level ports are 1.2 V signals except vdda (3.3 V).
Run: python3 gen_gate.py ; netlist with netlist.sh
"""
import os
import sys


def _find_flow():
    d = os.path.dirname(os.path.abspath(__file__))
    while not os.path.isdir(os.path.join(d, "flow", "schematic")):
        if os.path.dirname(d) == d:
            raise SystemExit("flow/schematic not found above " + __file__)
        d = os.path.dirname(d)
    return os.path.join(d, "flow", "schematic")


sys.path.insert(0, _find_flow())
from xsch_readable import Sheet, write_symbol  # noqa: E402

VDD, VDDA, VSS = "vdd", "vdda", "vss"
# Readable sheets (2026-09-25): signal flow left to right, supplies on top/bottom rails, bodies
# tied to their sources by a wire along the symbol (small b:<net> tag otherwise).  Device
# attributes, instance order and port order are those of the original label-per-pin
# generator, so the xschem netlists are unchanged (designs/g1-guardian/review/
# schematics-readability-20260925).
REF = "sim/netlist/g1_gate.spice sha256 846a55e0"
VARIANT = "baseline (chip cell retained_g1_gate = layout/g1_gate.gds ddf2c44a; LVS reference layout/g1_gate.cdl 27548c03)"


def title(s, cell, what, ref=None, width=1000, y=-640):
    s.title_block(120, y, cell, what, ref or ("the %s subcircuit in %s" % (cell, REF)), VARIANT, width=width)


def inv_cell(name, what, pmodel, pw, pl, nmodel, nw, nl, vp):
    """Inverter: PMOS over NMOS, input left, output right, supply rails top and bottom."""
    s = Sheet(name)
    mp = s.mos("MP", pmodel, 200, -300, pw, pl, D="y", G="a", S=vp, B=vp)
    mn = s.mos("MN", nmodel, 200, -150, nw, nl, D="y", G="a", S=VSS, B=VSS)
    s.body(mp, mn)
    s.wire(mp["G"], mn["G"]); s.wire(mp["D"], mn["D"])
    s.port("a", (80, -225), "in"); s.wire((80, -225), (180, -225))
    s.wire((220, -225), (360, -225)); s.port("y", (360, -225), "out")
    s.wire(mp["S"], (220, -380), (100, -380)); s.port(vp, (100, -380), "inout", flip=1)
    s.wire(mn["S"], (220, -70), (100, -70)); s.port(VSS, (100, -70), "inout", flip=1)
    title(s, name, what, width=900, y=-560)
    s.write(name + ".sch")


def lv_inv(name, pins=("a", "y", VDD, VSS)):
    inv_cell(name, "1.2 V inverter", "sg13_lv_pmos", "2u", "0.13u", "sg13_lv_nmos", "1u", "0.13u", VDD)
    write_symbol(name + ".sym", name, list(pins), {"a": "in", "y": "out"}, shape="inv")
    return list(pins)


LVINV = lv_inv("g1_lv_inv")

# ------------------------------------------------------------- LV NAND2 -----
s = Sheet("g1_lv_nand2")
mp1 = s.mos("MP1", "sg13_lv_pmos", 200, -300, "2u", "0.13u", D="y", G="a", S=VDD, B=VDD)
mp2 = s.mos("MP2", "sg13_lv_pmos", 360, -300, "2u", "0.13u", D="y", G="b", S=VDD, B=VDD)
mn1 = s.mos("MN1", "sg13_lv_nmos", 200, -150, "2u", "0.13u", D="y", G="a", S="m", B=VSS)
mn2 = s.mos("MN2", "sg13_lv_nmos", 200, -40, "2u", "0.13u", D="m", G="b", S=VSS, B=VSS)
s.body(mp1, mp2, mn1, mn2)
s.wire(mp1["G"], mn1["G"])
s.wire(mp1["D"], (220, -225), (380, -225), mp2["D"]); s.wire((220, -225), mn1["D"])
s.wire(mn1["S"], mn2["D"]); s.wlab((220, -95), "m")
s.port("a", (60, -225), "in"); s.wire((60, -225), (180, -225))
s.port("b", (60, -40), "in"); s.wire((60, -40), mn2["G"])
s.stub(mp2["G"], "b", -40)
s.wire((380, -225), (480, -225)); s.port("y", (480, -225), "out")
s.wire(mp1["S"], (220, -380), (380, -380), mp2["S"]); s.wire((220, -380), (100, -380)); s.port(VDD, (100, -380), "inout", flip=1)
s.wire(mn2["S"], (220, 40), (100, 40)); s.port(VSS, (100, 40), "inout", flip=1)
title(s, "g1_lv_nand2", "1.2 V NAND2 (y = !(a b))", width=900, y=-580)
s.write("g1_lv_nand2.sch")
LVNAND = ["a", "b", "y", VDD, VSS]
write_symbol("g1_lv_nand2.sym", "g1_lv_nand2", LVNAND, {"a": "in", "b": "in", "y": "out"}, shape="nand")

# ---------------------------------------------------------------- HV INV ----
inv_cell("g1_hv_inv", "3.3 V inverter (thick oxide, sizes of the PDK IO LevelUp)", "sg13_hv_pmos", "3.9u", "0.45u",
         "sg13_hv_nmos", "1.9u", "0.45u", VDDA)
HVINV = ["a", "y", VDDA, VSS]
write_symbol("g1_hv_inv.sym", "g1_hv_inv", HVINV, {"a": "in", "y": "out"}, shape="inv")

# --------------------------------------------------------------- HV NOR2 ----
s = Sheet("g1_hv_nor2")
mp1 = s.mos("MP1", "sg13_hv_pmos", 200, -340, "7.8u", "0.45u", D="m", G="a", S=VDDA, B=VDDA)
mp2 = s.mos("MP2", "sg13_hv_pmos", 200, -240, "7.8u", "0.45u", D="y", G="b", S="m", B=VDDA)
mn1 = s.mos("MN1", "sg13_hv_nmos", 200, -100, "1.9u", "0.45u", D="y", G="a", S=VSS, B=VSS)
mn2 = s.mos("MN2", "sg13_hv_nmos", 380, -100, "1.9u", "0.45u", D="y", G="b", S=VSS, B=VSS)
s.body(mp1, mp2, mn1, mn2)
s.wire(mp1["D"], mp2["S"]); s.wlab((220, -290), "m")
s.wire(mp2["D"], mn1["D"]); s.wire((220, -170), (400, -170), mn2["D"])
s.wire((400, -170), (500, -170))
s.wire((160, -340), mp1["G"]); s.wire((160, -100), mn1["G"]); s.wire((160, -340), (160, -100))
s.port("a", (60, -300), "in"); s.wire((60, -300), (160, -300))
s.port("b", (60, -240), "in"); s.wire((60, -240), mp2["G"])
s.port("y", (500, -170), "out")
s.stub(mn2["G"], "b", -40)
s.wire(mp1["S"], (220, -400), (100, -400)); s.port(VDDA, (100, -400), "inout", flip=1)
s.wire(mn1["S"], (220, -30), (400, -30), mn2["S"]); s.wire((220, -30), (100, -30)); s.port(VSS, (100, -30), "inout", flip=1)
title(s, "g1_hv_nor2", "3.3 V NOR2 (y = !(a + b))", width=900, y=-600)
s.write("g1_hv_nor2.sch")
HVNOR = ["a", "b", "y", VDDA, VSS]
write_symbol("g1_hv_nor2.sym", "g1_hv_nor2", HVNOR, {"a": "in", "b": "in", "y": "out"}, shape="nor")

# ---------------------------------------------------------------- LVLUP -----
s = Sheet("g1_lvlup")
xi = s.inst("XI", "g1_lv_inv.sym", 200, -225, {"a": "a", "y": "ab", VDD: VDD, VSS: VSS})
mn1 = s.mos("MN1", "sg13_hv_nmos", 440, -150, "1.9u", "0.45u", D="nb", G="a", S=VSS, B=VSS)    # a=1 pulls nb low
mn2 = s.mos("MN2", "sg13_hv_nmos", 640, -150, "1.9u", "0.45u", D="n", G="ab", S=VSS, B=VSS)
mp1 = s.mos("MP1", "sg13_hv_pmos", 440, -300, "0.3u", "0.45u", D="nb", G="n", S=VDDA, B=VDDA)
mp2 = s.mos("MP2", "sg13_hv_pmos", 640, -300, "0.3u", "0.45u", D="n", G="nb", S=VDDA, B=VDDA)
xo = s.inst("XO", "g1_hv_inv.sym", 900, -225, {"a": "nb", "y": "y", VDDA: VDDA, VSS: VSS})
s.body(mn1, mn2, mp1, mp2)
s.port("a", (60, -225), "in"); s.wire((60, -225), xi["a"])
s.wire((110, -225), (110, -100), (400, -100), (400, -150), mn1["G"])
s.wire(xi["y"], (300, -225)); s.wlab((300, -225), "ab"); s.stub(mn2["G"], "ab", -40)
s.wire(mp1["D"], mn1["D"]); s.wire(mp2["D"], mn2["D"])
s.wire((460, -245), (590, -245), (590, -300), mp2["G"])
s.wire((660, -205), (400, -205), (400, -300), mp1["G"])
s.lab((460, -225), "nb", "l"); s.lab((660, -225), "n", "r")
s.stub(xo["a"], "nb", -40)
s.wire(xo["y"], (1060, -225)); s.port("y", (1060, -225), "out")
s.supplies(xi); s.supplies(xo)
s.wire(mp1["S"], (460, -380), (660, -380), mp2["S"]); s.lab((460, -380), VDDA, "l")
s.wire(mn1["S"], (460, -70), (660, -70), mn2["S"]); s.lab((460, -70), VSS, "l")
s.port(VDD, (60, 20), "inout"); s.port(VDDA, (60, 50), "inout"); s.port(VSS, (60, 80), "inout")
s.text("a=1: MN1 pulls nb low, MP2 pulls n to vdda, XO drives y = vdda.\nStructure of the PDK IO cell sg13g2_LevelUp.", 300, 0)
title(s, "g1_lvlup", "1.2 V to 3.3 V level shifter (y = a)", "sim/netlist/g1_lvlup.spice sha256 71af3cd8", width=1100, y=-620)
s.write("g1_lvlup.sch")
LVLUP = ["a", "y", VDD, VDDA, VSS]
write_symbol("g1_lvlup.sym", "g1_lvlup", LVLUP, {"a": "in", "y": "out"}, label="1.2 -> 3.3 V")

# ---------------------------------------------------------------- LVLDN -----
s = Sheet("g1_lvldn")
mn1 = s.mos("MN1", "sg13_hv_nmos", 300, -150, "2u", "0.45u", D="yb", G="a", S=VSS, B=VSS)
mn2 = s.mos("MN2", "sg13_hv_nmos", 500, -150, "2u", "0.45u", D="y", G="ab", S=VSS, B=VSS)
mp1 = s.mos("MP1", "sg13_lv_pmos", 500, -300, "1u", "0.13u", D="y", G="yb", S=VDD, B=VDD)
mp2 = s.mos("MP2", "sg13_lv_pmos", 300, -300, "1u", "0.13u", D="yb", G="y", S=VDD, B=VDD)
s.body(mn1, mn2, mp1, mp2)
s.wire(mp2["D"], mn1["D"]); s.wire(mp1["D"], mn2["D"])
s.wire((320, -245), (450, -245), (450, -300), mp1["G"])
s.wire((520, -205), (260, -205), (260, -300), mp2["G"])
s.lab((320, -225), "yb", "l")
s.port("a", (100, -150), "in"); s.wire((100, -150), mn1["G"])
s.port("ab", (100, -100), "in")
s.stub(mn2["G"], "ab", -40)
s.port("y", (640, -225), "out"); s.wire((520, -225), (640, -225))
s.wire(mp2["S"], (320, -380), (520, -380), mp1["S"]); s.wire((320, -380), (160, -380)); s.port(VDD, (160, -380), "inout", flip=1)
s.wire(mn1["S"], (320, -70), (520, -70), mn2["S"]); s.wire((320, -70), (160, -70)); s.port(VSS, (160, -70), "inout", flip=1)
s.text("a/ab: 3.3 V complementary inputs; thick-oxide pull-downs, cross-coupled 1.2 V PMOS load on vdd.", 160, -20)
title(s, "g1_lvldn", "3.3 V to 1.2 V level shifter (y = a)", "sim/netlist/g1_lvldn.spice sha256 d253d0a6", width=1000, y=-600)
s.write("g1_lvldn.sch")
LVLDN = ["a", "ab", "y", VDD, VSS]
write_symbol("g1_lvldn.sym", "g1_lvldn", LVLDN, {"a": "in", "ab": "in", "y": "out"}, label="3.3 -> 1.2 V")

# ------------------------------------------------------------------ top -----
s = Sheet("g1_gate")
xna = s.inst("XNA", "g1_lv_nand2.sym", 300, -700, {"a": "hard_cmp", "b": "fast_en", "y": "fast_n", VDD: VDD, VSS: VSS})
xia = s.inst("XIA", "g1_lv_inv.sym", 480, -700, {"a": "fast_n", "y": "fast", VDD: VDD, VSS: VSS})
xu = []
for i, (a, y) in enumerate((("fast", "fast_h"), ("trip_d", "trip_h"), ("clr_d", "clr_h"), ("en_core", "en_h"))):
    xu.append(s.inst("XU%d" % i, "g1_lvlup.sym", 700, -700 + 140 * i, {"a": a, "y": y, VDD: VDD, VDDA: VDDA, VSS: VSS}))
# set = fast_h | trip_h ; reset = !en_h | clr_h
xn1 = s.inst("XN1", "g1_hv_nor2.sym", 950, -630, {"a": "fast_h", "b": "trip_h", "y": "set_n", VDDA: VDDA, VSS: VSS})
xi1 = s.inst("XI1", "g1_hv_inv.sym", 1110, -630, {"a": "set_n", "y": "set", VDDA: VDDA, VSS: VSS})
xi2 = s.inst("XI2", "g1_hv_inv.sym", 950, -280, {"a": "en_h", "y": "en_hn", VDDA: VDDA, VSS: VSS})
xn2 = s.inst("XN2", "g1_hv_nor2.sym", 1110, -430, {"a": "en_hn", "b": "clr_h", "y": "rst_n", VDDA: VDDA, VSS: VSS})
xi3 = s.inst("XI3", "g1_hv_inv.sym", 1270, -430, {"a": "rst_n", "y": "rst", VDDA: VDDA, VSS: VSS})
# latch: q = NOR(rst, qb) ; qb = NOR(set, q)     (rst=1 forces q=0)
xl1 = s.inst("XL1", "g1_hv_nor2.sym", 1550, -420, {"a": "rst", "b": "qb", "y": "q", VDDA: VDDA, VSS: VSS})
xl2 = s.inst("XL2", "g1_hv_nor2.sym", 1550, -640, {"a": "set", "b": "q", "y": "qb", VDDA: VDDA, VSS: VSS})
# gate_h = en_h & !q = NOR(en_hn, q) ; complement for the level-down
xg = s.inst("XG", "g1_hv_nor2.sym", 1850, -700, {"a": "en_hn", "b": "q", "y": "gate_h", VDDA: VDDA, VSS: VSS})
xgi = s.inst("XGI", "g1_hv_inv.sym", 2010, -700, {"a": "gate_h", "y": "gate_hn", VDDA: VDDA, VSS: VSS})
# level down to the 1.2 V pad inputs and to the digital macro
xd1 = s.inst("XD1", "g1_lvldn.sym", 2300, -700, {"a": "gate_h", "ab": "gate_hn", "y": "gate_core", VDD: VDD, VSS: VSS})
xd2 = s.inst("XD2", "g1_lvldn.sym", 2300, -540, {"a": "qb", "ab": "q", "y": "fault_core", VDD: VDD, VSS: VSS})
xd3 = s.inst("XD3", "g1_lvldn.sym", 2300, -380, {"a": "q", "ab": "qb", "y": "tripped", VDD: VDD, VSS: VSS})
for x in [xna, xia] + xu + [xn1, xi1, xi2, xn2, xi3, xl1, xl2, xg, xgi, xd1, xd2, xd3]:
    s.supplies(x)
# inputs (original port order)
s.port("trip_d", (100, -560), "in"); s.wire((100, -560), xu[1]["a"])
s.port("clr_d", (100, -420), "in"); s.wire((100, -420), xu[2]["a"])
s.port("fast_en", (100, -670), "in"); s.wire((100, -670), (200, -670), (200, -690), xna["b"])
s.port("hard_cmp", (100, -740), "in"); s.wire((100, -740), (200, -740), (200, -710), xna["a"])
s.port("en_core", (100, -280), "in"); s.wire((100, -280), xu[3]["a"])
# fast path and level-up
s.wire(xna["y"], xia["a"]); s.wlab((410, -700), "fast_n")
s.wire(xia["y"], xu[0]["a"]); s.wlab((620, -700), "fast")
s.wire(xu[0]["y"], (830, -700), (830, -640), xn1["a"]); s.wlab((820, -700), "fast_h")
s.wire(xu[1]["y"], (850, -560), (850, -620), xn1["b"]); s.wlab((840, -560), "trip_h")
s.wire(xu[2]["y"], xn2["b"]); s.wlab((980, -420), "clr_h")
s.wire(xu[3]["y"], xi2["a"]); s.wlab((870, -280), "en_h")
# set / reset
s.wire(xn1["y"], xi1["a"]); s.wlab((1045, -630), "set_n")
s.wire(xi2["y"], (1090, -280)); s.wlab((1090, -280), "en_hn")
s.stub(xn2["a"], "en_hn", -40)
s.wire(xn2["y"], xi3["a"]); s.wlab((1205, -430), "rst_n")
s.wire(xi1["y"], (1400, -630), (1400, -650), xl2["a"]); s.wlab((1300, -630), "set")
s.wire(xi3["y"], xl1["a"]); s.wlab((1390, -430), "rst")
# cross-coupled NOR latch
s.wire(xl1["y"], (1640, -420), (1640, -530), (1460, -530), (1460, -630), xl2["b"])
s.wire(xl2["y"], (1680, -640), (1680, -320), (1440, -320), (1440, -410), xl1["b"])
s.wire((1640, -420), (1720, -420)); s.wlab((1720, -420), "q")
s.wire((1680, -640), (1720, -640)); s.wlab((1720, -640), "qb")
# gate output path
s.stub(xg["a"], "en_hn", -40); s.stub(xg["b"], "q", -40)
s.wire(xg["y"], xgi["a"])
s.wire((1930, -700), (1930, -760), (2200, -760), (2200, -710), xd1["a"]); s.wlab((2150, -760), "gate_h")
s.wire(xgi["y"], (2220, -700), (2220, -690), xd1["ab"]); s.wlab((2160, -700), "gate_hn")
s.stub(xd2["a"], "qb", -40); s.stub(xd2["ab"], "q", -40)
s.stub(xd3["a"], "q", -40); s.stub(xd3["ab"], "qb", -40)
# outputs and supplies
for d, net in ((xd1, "gate_core"), (xd2, "fault_core"), (xd3, "tripped")):
    s.wire(d["y"], (2480, d["y"][1])); s.port(net, (2480, d["y"][1]), "out")
s.port(VDD, (100, -120), "inout"); s.port(VDDA, (100, -90), "inout"); s.port(VSS, (100, -60), "inout")
s.frame(170, -800, 560, -620, "1.2 V fast-path AND")
s.frame(590, -800, 800, -220, "1.2 -> 3.3 V")
s.frame(860, -800, 1360, -220, "3.3 V set / reset")
s.frame(1380, -800, 1740, -300, "SR latch, reset dominant")
s.frame(1760, -800, 2440, -300, "gate enable + 3.3 -> 1.2 V")
s.text("set = trip_d | (hard_cmp & fast_en)     reset = !en_core | clr_d     q = tripped, held in 3.3 V thick-oxide logic\n"
       "gate_core = en_core & !q ; fault_core = !q ; power-up: en_core = 0 forces gate_core = 0\n"
       "Chip level (simulated, chip netlists tt/27 C): pad GATE < 1 V 1.345 us after a hard fault (g1_top RESULTS_20260925)", 170, -180)
title(s, "g1_gate", "latch-up guardian gate driver: 3.3 V SR latch between 1.2 V level shifters", REF, width=1800, y=-1020)
s.write("g1_gate.sch")
GATE = ["trip_d", "clr_d", "fast_en", "hard_cmp", "en_core", "gate_core", "fault_core", "tripped", VDD, VDDA, VSS]
write_symbol("g1_gate.sym", "g1_gate", GATE, dict([(p, "in") for p in GATE[:5]] + [(p, "out") for p in GATE[5:8]]))
print("wrote g1_gate cells")
