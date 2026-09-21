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
from xsch import Sch, Sym
VDD, VDDA, VSS = "vdd", "vdda", "vss"

def lv_inv(name, pins=("a", "y", VDD, VSS)):
    s = Sch("%s: LV inverter" % name)
    s.mos("MP", "sg13_lv_pmos", 100, -200, "2u", "0.13u", D="y", G="a", S=VDD, B=VDD)
    s.mos("MN", "sg13_lv_nmos", 100, -100, "1u", "0.13u", D="y", G="a", S=VSS, B=VSS)
    s.ports(300, -200, ins=("a",), outs=("y",), ios=(VDD, VSS)); s.write(name + ".sch")
    Sym.write(name + ".sym", name, list(pins), {"a": "in", "y": "out"})
    return list(pins)
LVINV = lv_inv("g1_lv_inv")

s = Sch("g1_lv_nand2")
s.mos("MP1", "sg13_lv_pmos", 100, -300, "2u", "0.13u", D="y", G="a", S=VDD, B=VDD)
s.mos("MP2", "sg13_lv_pmos", 200, -300, "2u", "0.13u", D="y", G="b", S=VDD, B=VDD)
s.mos("MN1", "sg13_lv_nmos", 100, -200, "2u", "0.13u", D="y", G="a", S="m", B=VSS)
s.mos("MN2", "sg13_lv_nmos", 100, -100, "2u", "0.13u", D="m", G="b", S=VSS, B=VSS)
s.ports(400, -300, ins=("a", "b"), outs=("y",), ios=(VDD, VSS)); s.write("g1_lv_nand2.sch")
LVNAND = ["a", "b", "y", VDD, VSS]; Sym.write("g1_lv_nand2.sym", "g1_lv_nand2", LVNAND, {"a": "in", "b": "in", "y": "out"})

s = Sch("g1_hv_inv: 3.3 V inverter")
s.mos("MP", "sg13_hv_pmos", 100, -200, "3.9u", "0.45u", D="y", G="a", S=VDDA, B=VDDA)
s.mos("MN", "sg13_hv_nmos", 100, -100, "1.9u", "0.45u", D="y", G="a", S=VSS, B=VSS)
s.ports(300, -200, ins=("a",), outs=("y",), ios=(VDDA, VSS)); s.write("g1_hv_inv.sch")
HVINV = ["a", "y", VDDA, VSS]; Sym.write("g1_hv_inv.sym", "g1_hv_inv", HVINV, {"a": "in", "y": "out"})

s = Sch("g1_hv_nor2: 3.3 V NOR2")
s.mos("MP1", "sg13_hv_pmos", 100, -400, "7.8u", "0.45u", D="m", G="a", S=VDDA, B=VDDA)
s.mos("MP2", "sg13_hv_pmos", 100, -300, "7.8u", "0.45u", D="y", G="b", S="m", B=VDDA)
s.mos("MN1", "sg13_hv_nmos", 100, -200, "1.9u", "0.45u", D="y", G="a", S=VSS, B=VSS)
s.mos("MN2", "sg13_hv_nmos", 200, -200, "1.9u", "0.45u", D="y", G="b", S=VSS, B=VSS)
s.ports(400, -400, ins=("a", "b"), outs=("y",), ios=(VDDA, VSS)); s.write("g1_hv_nor2.sch")
HVNOR = ["a", "b", "y", VDDA, VSS]; Sym.write("g1_hv_nor2.sym", "g1_hv_nor2", HVNOR, {"a": "in", "b": "in", "y": "out"})

s = Sch("g1_lvlup: 1.2 V in -> 3.3 V out (y = a level); cross-coupled hv PMOS pair")
s.inst("XI", "g1_lv_inv.sym", LVINV, 100, -300, {"a": "a", "y": "ab", VDD: VDD, VSS: VSS})
s.mos("MN1", "sg13_hv_nmos", 300, -200, "1.9u", "0.45u", D="nb", G="a", S=VSS, B=VSS)    # a=1 pulls nb low
s.mos("MN2", "sg13_hv_nmos", 400, -200, "1.9u", "0.45u", D="n", G="ab", S=VSS, B=VSS)
s.mos("MP1", "sg13_hv_pmos", 300, -300, "0.3u", "0.45u", D="nb", G="n", S=VDDA, B=VDDA)
s.mos("MP2", "sg13_hv_pmos", 400, -300, "0.3u", "0.45u", D="n", G="nb", S=VDDA, B=VDDA)
s.inst("XO", "g1_hv_inv.sym", HVINV, 600, -300, {"a": "nb", "y": "y", VDDA: VDDA, VSS: VSS})
s.ports(800, -300, ins=("a",), outs=("y",), ios=(VDD, VDDA, VSS)); s.write("g1_lvlup.sch")
LVLUP = ["a", "y", VDD, VDDA, VSS]; Sym.write("g1_lvlup.sym", "g1_lvlup", LVLUP, {"a": "in", "y": "out"})

s = Sch("g1_lvldn: 3.3 V a/ab -> 1.2 V y (= a level); hv NMOS pull-downs, cross-coupled lv PMOS")
s.mos("MN1", "sg13_hv_nmos", 100, -200, "2u", "0.45u", D="yb", G="a", S=VSS, B=VSS)
s.mos("MN2", "sg13_hv_nmos", 200, -200, "2u", "0.45u", D="y", G="ab", S=VSS, B=VSS)
s.mos("MP1", "sg13_lv_pmos", 100, -300, "1u", "0.13u", D="y", G="yb", S=VDD, B=VDD)
s.mos("MP2", "sg13_lv_pmos", 200, -300, "1u", "0.13u", D="yb", G="y", S=VDD, B=VDD)
s.ports(400, -300, ins=("a", "ab"), outs=("y",), ios=(VDD, VSS)); s.write("g1_lvldn.sch")
LVLDN = ["a", "ab", "y", VDD, VSS]; Sym.write("g1_lvldn.sym", "g1_lvldn", LVLDN, {"a": "in", "ab": "in", "y": "out"})

# ------------------------------------------------------------------ top -----
s = Sch("g1_gate: HV SR latch (reset dominant), set = trip_d | (hard_cmp & fast_en), reset = !en | clr_d")
# LV: fast path AND
s.inst("XNA", "g1_lv_nand2.sym", LVNAND, 100, -600, {"a": "hard_cmp", "b": "fast_en", "y": "fast_n", VDD: VDD, VSS: VSS})
s.inst("XIA", "g1_lv_inv.sym", LVINV, 250, -600, {"a": "fast_n", "y": "fast", VDD: VDD, VSS: VSS})
# level up: fast, trip_d, clr_d, en
for i, (a, y) in enumerate((("fast", "fast_h"), ("trip_d", "trip_h"), ("clr_d", "clr_h"), ("en_core", "en_h"))):
    s.inst("XU%d" % i, "g1_lvlup.sym", LVLUP, 500, -700 + 120 * i, {"a": a, "y": y, VDD: VDD, VDDA: VDDA, VSS: VSS})
# set = fast_h | trip_h ; reset = !en_h | clr_h
s.inst("XN1", "g1_hv_nor2.sym", HVNOR, 800, -700, {"a": "fast_h", "b": "trip_h", "y": "set_n", VDDA: VDDA, VSS: VSS})
s.inst("XI1", "g1_hv_inv.sym", HVINV, 950, -700, {"a": "set_n", "y": "set", VDDA: VDDA, VSS: VSS})
s.inst("XI2", "g1_hv_inv.sym", HVINV, 800, -500, {"a": "en_h", "y": "en_hn", VDDA: VDDA, VSS: VSS})
s.inst("XN2", "g1_hv_nor2.sym", HVNOR, 950, -500, {"a": "en_hn", "b": "clr_h", "y": "rst_n", VDDA: VDDA, VSS: VSS})
s.inst("XI3", "g1_hv_inv.sym", HVINV, 1100, -500, {"a": "rst_n", "y": "rst", VDDA: VDDA, VSS: VSS})
# latch: q = NOR(rst, qb) ; qb = NOR(set, q)     (rst=1 forces q=0)
s.inst("XL1", "g1_hv_nor2.sym", HVNOR, 1300, -700, {"a": "rst", "b": "qb", "y": "q", VDDA: VDDA, VSS: VSS})
s.inst("XL2", "g1_hv_nor2.sym", HVNOR, 1300, -500, {"a": "set", "b": "q", "y": "qb", VDDA: VDDA, VSS: VSS})
# gate_h = en_h & !q = NOR(en_hn, q) ; complement for the level-down
s.inst("XG", "g1_hv_nor2.sym", HVNOR, 1550, -700, {"a": "en_hn", "b": "q", "y": "gate_h", VDDA: VDDA, VSS: VSS})
s.inst("XGI", "g1_hv_inv.sym", HVINV, 1700, -700, {"a": "gate_h", "y": "gate_hn", VDDA: VDDA, VSS: VSS})
# level down to the 1.2 V pad inputs and to the digital macro
s.inst("XD1", "g1_lvldn.sym", LVLDN, 1950, -700, {"a": "gate_h", "ab": "gate_hn", "y": "gate_core", VDD: VDD, VSS: VSS})
s.inst("XD2", "g1_lvldn.sym", LVLDN, 1950, -550, {"a": "qb", "ab": "q", "y": "fault_core", VDD: VDD, VSS: VSS})
s.inst("XD3", "g1_lvldn.sym", LVLDN, 1950, -400, {"a": "q", "ab": "qb", "y": "tripped", VDD: VDD, VSS: VSS})
s.ports(2250, -800, ins=("trip_d", "clr_d", "fast_en", "hard_cmp", "en_core"), outs=("gate_core", "fault_core", "tripped"), ios=(VDD, VDDA, VSS))
s.text("q (tripped) held in 3.3 V logic; fault_core = !q ; gate_core = en & !q. Power-up: en_core=0 forces gate_core=0.", 100, -900)
s.write("g1_gate.sch")
GATE = ["trip_d", "clr_d", "fast_en", "hard_cmp", "en_core", "gate_core", "fault_core", "tripped", VDD, VDDA, VSS]
Sym.write("g1_gate.sym", "g1_gate", GATE)
print("wrote g1_gate cells")
