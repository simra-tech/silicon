"""Generate the G1_TRIP schematics (xschem):
  g1_inv, g1_tg      LV inverter and transmission gate cells
  g1_cmp             StrongARM latch + inverter buffers + NOR SR latch (1.2 V), with
                     neutralisation dummies on the input pair
  g1_dac8            8-bit resistor-string DAC: 530 rppd units from the buffered VREF, taps 255..510
                     (0.5004 V .. 1.0008 V for VREF = 1.04 V, LSB = VREF/530 = 1.962 mV), binary
                     tree of 510 thick-oxide NMOS switches whose gates are driven at 3.3 V
                     by 8 level shifters (g1_tlvlup) and 8 hv inverters: LV switches leaked
                     8 LSB at 27 C / 53 LSB at 175 C into the 4 uA string (first version)
  g1_cond            ISENSE conditioning: 2:1 rppd divider (same 10 k unit as G1_SENSE)
                     + 1 pF cmim hold capacitor
  g1_trip            top: cond + two DACs + two comparators (soft on cmp_clk, hard on its inverse)
Run: python3 gen_trip.py ; netlist with netlist.sh.
Comparator device sizes start from 2AMLogic/sg13g2-comparator design/comparator.spice
(Apache-2.0, commit in designs/g1-guardian/SOURCES.md); tail bias branch removed (clocked tail only).
"""
from xsch import Sch, Sym

VDD, VSS = "vdd", "vss"

# ------------------------------------------------------------- cells --------
s = Sch("g1_inv: LV inverter")
s.mos("MP", "sg13_lv_pmos", 100, -200, "1u", "0.13u", D="y", G="a", S=VDD, B=VDD)
s.mos("MN", "sg13_lv_nmos", 100, -100, "0.5u", "0.13u", D="y", G="a", S=VSS, B=VSS)
s.ports(300, -200, ins=("a",), outs=("y",), ios=(VDD, VSS))
s.write("g1_inv.sch")
INV = ["a", "y", VDD, VSS]
Sym.write("g1_inv.sym", "g1_inv", INV, {"a": "in", "y": "out"})

s = Sch("g1_tg: LV transmission gate, on when en=1 (enb=0)")
s.mos("MN", "sg13_lv_nmos", 100, -200, "1u", "0.13u", D="a", G="en", S="b", B=VSS)
s.mos("MP", "sg13_lv_pmos", 100, -100, "2u", "0.13u", D="b", G="enb", S="a", B=VDD)
s.ports(300, -200, ins=("en", "enb"), ios=("a", "b", VDD, VSS))
s.write("g1_tg.sch")
TG = ["en", "enb", "a", "b", VDD, VSS]
Sym.write("g1_tg.sym", "g1_tg", TG, {"en": "in", "enb": "in"})

s = Sch("g1_thv_inv: 3.3 V inverter (DAC switch drive)")
s.mos("MP", "sg13_hv_pmos", 100, -200, "3.9u", "0.45u", D="y", G="a", S="vdda", B="vdda")
s.mos("MN", "sg13_hv_nmos", 100, -100, "1.9u", "0.45u", D="y", G="a", S=VSS, B=VSS)
s.ports(300, -200, ins=("a",), outs=("y",), ios=("vdda", VSS)); s.write("g1_thv_inv.sch")
THVINV = ["a", "y", "vdda", VSS]; Sym.write("g1_thv_inv.sym", "g1_thv_inv", THVINV, {"a": "in", "y": "out"})

s = Sch("g1_tlvlup: 1.2 V code bit -> 3.3 V y and yb (structure of sg13g2_LevelUp)")
s.inst("XI", "g1_inv.sym", INV, 100, -300, {"a": "a", "y": "ab", VDD: VDD, VSS: VSS})
s.mos("MN1", "sg13_hv_nmos", 300, -200, "1.9u", "0.45u", D="nb", G="a", S=VSS, B=VSS)
s.mos("MN2", "sg13_hv_nmos", 400, -200, "1.9u", "0.45u", D="n", G="ab", S=VSS, B=VSS)
s.mos("MP1", "sg13_hv_pmos", 300, -300, "0.3u", "0.45u", D="nb", G="n", S="vdda", B="vdda")
s.mos("MP2", "sg13_hv_pmos", 400, -300, "0.3u", "0.45u", D="n", G="nb", S="vdda", B="vdda")
s.inst("XO", "g1_thv_inv.sym", THVINV, 600, -300, {"a": "nb", "y": "y", "vdda": "vdda", VSS: VSS})
s.inst("XOB", "g1_thv_inv.sym", THVINV, 600, -200, {"a": "y", "y": "yb", "vdda": "vdda", VSS: VSS})
s.ports(800, -300, ins=("a",), outs=("y", "yb"), ios=(VDD, "vdda", VSS)); s.write("g1_tlvlup.sch")
TLVLUP = ["a", "y", "yb", VDD, "vdda", VSS]; Sym.write("g1_tlvlup.sym", "g1_tlvlup", TLVLUP, {"a": "in", "y": "out", "yb": "out"})

# ---------------------------------------------------------- comparator ------
s = Sch("g1_cmp: StrongARM latch, 1.2 V; q=1 when inp>inn, held by SR latch between strobes")
s.mos("MTAIL", "sg13_lv_nmos", 400, -100, "16u", "0.13u", D="tail", G="clk", S=VSS, B=VSS)
s.mos("M1", "sg13_lv_nmos", 300, -200, "12u", "0.34u", D="xp", G="inp", S="tail", B=VSS)
s.mos("M2", "sg13_lv_nmos", 500, -200, "12u", "0.34u", D="xq", G="inn", S="tail", B=VSS)
# neutralisation dummies: gate on one input, source/drain shorted to the opposite drain
s.mos("MD1", "sg13_lv_nmos", 200, -200, "6u", "0.13u", D="xq", G="inp", S="xq", B=VSS)
s.mos("MD2", "sg13_lv_nmos", 600, -200, "6u", "0.13u", D="xp", G="inn", S="xp", B=VSS)
s.mos("M3", "sg13_lv_nmos", 300, -300, "3u", "0.13u", D="xn", G="yn", S="xp", B=VSS)
s.mos("M4", "sg13_lv_nmos", 500, -300, "3u", "0.13u", D="yn", G="xn", S="xq", B=VSS)
s.mos("M5", "sg13_lv_pmos", 300, -400, "3u", "0.13u", D="xn", G="yn", S=VDD, B=VDD)
s.mos("M6", "sg13_lv_pmos", 500, -400, "3u", "0.13u", D="yn", G="xn", S=VDD, B=VDD)
s.mos("M7", "sg13_lv_pmos", 200, -400, "6u", "0.13u", D="xn", G="clk", S=VDD, B=VDD)
s.mos("M8", "sg13_lv_pmos", 600, -400, "6u", "0.13u", D="yn", G="clk", S=VDD, B=VDD)
s.mos("M9", "sg13_lv_pmos", 200, -300, "3u", "0.13u", D="xp", G="clk", S=VDD, B=VDD)
s.mos("M10", "sg13_lv_pmos", 600, -300, "3u", "0.13u", D="xq", G="clk", S=VDD, B=VDD)
# inverter buffers, skewed to a low threshold (~0.35 V) so the common-mode dip of X/Y during the
# amplification phase (to about VDD-|Vthp|) does not reach the SR latch; only a full regeneration does
s.mos("MIAP", "sg13_lv_pmos", 800, -400, "1u", "0.13u", D="xnb", G="xn", S=VDD, B=VDD)
s.mos("MIAN", "sg13_lv_nmos", 800, -300, "4u", "0.13u", D="xnb", G="xn", S=VSS, B=VSS)
s.mos("MIBP", "sg13_lv_pmos", 900, -400, "1u", "0.13u", D="ynb", G="yn", S=VDD, B=VDD)
s.mos("MIBN", "sg13_lv_nmos", 900, -300, "4u", "0.13u", D="ynb", G="yn", S=VSS, B=VSS)
# NOR SR latch: qb = NOR(xnb, q) ; q = NOR(ynb, qb)
s.mos("MNAP1", "sg13_lv_pmos", 1100, -500, "4u", "0.13u", D="na", G="xnb", S=VDD, B=VDD)
s.mos("MNAP2", "sg13_lv_pmos", 1100, -400, "4u", "0.13u", D="qb", G="q", S="na", B=VDD)
s.mos("MNAN1", "sg13_lv_nmos", 1100, -300, "1.5u", "0.13u", D="qb", G="xnb", S=VSS, B=VSS)
s.mos("MNAN2", "sg13_lv_nmos", 1100, -200, "1.5u", "0.13u", D="qb", G="q", S=VSS, B=VSS)
s.mos("MNBP1", "sg13_lv_pmos", 1250, -500, "4u", "0.13u", D="nb", G="ynb", S=VDD, B=VDD)
s.mos("MNBP2", "sg13_lv_pmos", 1250, -400, "4u", "0.13u", D="q", G="qb", S="nb", B=VDD)
s.mos("MNBN1", "sg13_lv_nmos", 1250, -300, "1.5u", "0.13u", D="q", G="ynb", S=VSS, B=VSS)
s.mos("MNBN2", "sg13_lv_nmos", 1250, -200, "1.5u", "0.13u", D="q", G="qb", S=VSS, B=VSS)
s.ports(1500, -500, ins=("inp", "inn", "clk"), outs=("q", "qb"), ios=(VDD, VSS))
s.write("g1_cmp.sch")
CMP = ["inp", "inn", "clk", "q", "qb", VDD, VSS]
Sym.write("g1_cmp.sym", "g1_cmp", CMP, {"inp": "in", "inn": "in", "clk": "in", "q": "out", "qb": "out"})

# ---------------------------------------------------------------- DAC -------
UW, UL = "4u", "1.2u"          # unit rppd ~95.5 Ohm (70e-6/w + 260*l/w); 530 units = 50.6 kOhm, 20.5 uA from the buffered VREF (1.04 V)
NUNIT = 530                    # 255 below tap0 (0.5 V), 255 between tap0 and tap255, 20 above (VREF = 1.04 V)
s = Sch("g1_dac8: 8-bit rppd string DAC from VREF, taps 255..510 of 530, hv-NMOS binary tree driven at 3.3 V")
prev = VSS
for i in range(NUNIT):
    # top of unit i is (i+1) units above ground: tap k = 255+k units -> unit index i = 254+k
    nxt = "vref" if i == NUNIT - 1 else ("t%d" % (i - 254) if 254 <= i <= 509 else "s%d" % i)
    s.res("RU%d" % i, 100 + 60 * (i % 40), -3000 + 80 * (i // 40), UW, UL, P=nxt, M=prev)
    prev = nxt
# code level shifters: dh = 3.3 V copy of d, dhn its complement
for b in range(8):
    s.inst("XLU%d" % b, "g1_tlvlup.sym", TLVLUP, 100 + 150 * b, -3200, {"a": "d%d" % b, "y": "dh%d" % b, "yb": "dhn%d" % b, VDD: VDD, "vdda": "vdda", VSS: VSS})
# mux tree: level b combines pairs of level b-1 nodes; d_b = 1 selects the odd (higher) input
nodes = ["t%d" % k for k in range(256)]
y0 = -1600
for b in range(8):
    nxt = []
    for k in range(len(nodes) // 2):
        o = "out" if b == 7 else "m%d_%d" % (b, k)
        x = 100 + 100 * (k % 32)
        y = y0 + 80 * (k // 32) + 400 * b
        s.mos("MS%d_%da" % (b, k), "sg13_hv_nmos", x, y, "2u", "0.45u", D=nodes[2 * k], G="dhn%d" % b, S=o, B=VSS)
        s.mos("MS%d_%db" % (b, k), "sg13_hv_nmos", x + 50, y, "2u", "0.45u", D=nodes[2 * k + 1], G="dh%d" % b, S=o, B=VSS)
        nxt.append(o)
    nodes = nxt
s.ports(4200, -3000, ins=("vref",) + tuple("d%d" % b for b in range(8)), outs=("out",), ios=(VDD, "vdda", VSS))
s.text("out = VREF*(255+code)/530 ; code 0 -> 0.5004 V, 255 -> 1.0008 V at VREF=1.04 V; LSB 1.962 mV", 100, -3300)
s.write("g1_dac8.sch")
DAC = ["vref"] + ["d%d" % b for b in range(8)] + ["out", VDD, "vdda", VSS]
Sym.write("g1_dac8.sym", "g1_dac8", DAC, {"out": "out"})

# --------------------------------------------------------------- cond -------
RW, RL = "2u", "76.7u"   # 10 k unit shared with G1_SENSE
s = Sch("g1_cond: isense_cmp = ISENSE/2 (5+5 units of 10 k), 1 pF hold")
prev = "isense"
for i in range(10):
    nxt = VSS if i == 9 else ("icmp" if i == 4 else "c%d" % i)
    s.res("RC%d" % i, 100 + 80 * i, -300, RW, RL, P=prev, M=nxt)
    prev = nxt
s.cap("CH", 1000, -300, "26u", "26u", c0="icmp", c1=VSS)
s.ports(1200, -300, ins=("isense",), outs=("icmp",), ios=(VSS,))
s.write("g1_cond.sch")
COND = ["isense", "icmp", VSS]
Sym.write("g1_cond.sym", "g1_cond", COND, {"isense": "in", "icmp": "out"})

# ---------------------------------------------------------------- top -------
s = Sch("g1_trip: conditioning + 2 x DAC + 2 x StrongARM; soft strobed on cmp_clk rising, hard on its inverse")
s.inst("XCOND", "g1_cond.sym", COND, 200, -600, {"isense": "isense", "icmp": "icmp", VSS: VSS})
soft = {"vref": "vref", "out": "vth_soft", VDD: VDD, "vdda": "vdda", VSS: VSS}
hard = {"vref": "vref", "out": "vth_hard", VDD: VDD, "vdda": "vdda", VSS: VSS}
for b in range(8):
    soft["d%d" % b] = "soft%d" % b
    hard["d%d" % b] = "hard%d" % b
s.inst("XDACS", "g1_dac8.sym", DAC, 500, -700, soft)
s.inst("XDACH", "g1_dac8.sym", DAC, 500, -400, hard)
s.cap("CHS", 700, -700, "26u", "26u", c0="vth_soft", c1=VSS)
s.cap("CHH", 700, -400, "26u", "26u", c0="vth_hard", c1=VSS)
s.inst("XCLKI", "g1_inv.sym", INV, 800, -200, {"a": "cmp_clk", "y": "cmp_clk_n", VDD: VDD, VSS: VSS})
s.inst("XCS", "g1_cmp.sym", CMP, 1000, -700, {"inp": "icmp", "inn": "vth_soft", "clk": "cmp_clk", "q": "cmp_soft", "qb": "cmp_soft_n", VDD: VDD, VSS: VSS})
s.inst("XCH", "g1_cmp.sym", CMP, 1000, -400, {"inp": "icmp", "inn": "vth_hard", "clk": "cmp_clk_n", "q": "cmp_hard", "qb": "cmp_hard_n", VDD: VDD, VSS: VSS})
ins = ("isense", "vref", "cmp_clk") + tuple("soft%d" % b for b in range(8)) + tuple("hard%d" % b for b in range(8))
s.ports(1300, -800, ins=ins, outs=("cmp_soft", "cmp_hard"), ios=(VDD, "vdda", VSS))
s.text("vref = buffered VREF from G1_SENSE. cmp_x = 1 while ISENSE/2 > VREF*(255+code)/530, i.e. shunt voltage > code*0.1962 mV*(VREF/1.04)", 200, -900)
s.write("g1_trip.sch")
TRIP = list(ins) + ["cmp_soft", "cmp_hard", VDD, "vdda", VSS]
Sym.write("g1_trip.sym", "g1_trip", TRIP)
print("wrote g1_inv g1_tg g1_cmp g1_dac8 g1_cond g1_trip")
