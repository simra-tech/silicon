"""Generate the G1_OSC schematics (xschem): 1.2 V ping-pong RC relaxation oscillator, ~10 MHz.

Cells
  g1_osc_inv / g1_osc_nor2 / g1_osc_nor3 / g1_osc_nand2   LV logic gates
  g1_osc_cmp        continuous-time comparator: 5-T NMOS-input pair, PMOS mirror, two inverters
  g1_osc_cbank      timing capacitor: fixed cmim + 4-bit binary-weighted cmim trim (NMOS switches to vss)
  g1_osc            top: two RC branches (rppd R from vdd), two capacitor banks, two comparators
                    against a VDD/2 rppd divider, SR latch, enable

Operation: Q=1 -> bank A charges through RA toward VDD, bank B is held at 0 by its reset switch.
When VA crosses VDD/2 the comparator A output resets the latch (Q=0): A is discharged, B charges.
Half period = R*C*ln2 + comparator/latch delay; first-order independent of VDD because the
threshold is a fixed fraction of VDD.  en=0 forces Q=0 and holds both banks discharged.
Run: python3 gen_osc.py ; netlist with netlist.sh.
"""
from xsch import Sch, Sym

VDD, VSS = "vdd", "vss"
LP, LN = "0.13u", "0.13u"

# ------------------------------------------------------------- gates --------
def gate_inv(name):
    s = Sch(name + ": LV inverter")
    s.mos("MP", "sg13_lv_pmos", 100, -200, "1u", LP, D="y", G="a", S=VDD, B=VDD)
    s.mos("MN", "sg13_lv_nmos", 100, -100, "0.5u", LN, D="y", G="a", S=VSS, B=VSS)
    s.ports(300, -200, ins=("a",), outs=("y",), ios=(VDD, VSS))
    s.write(name + ".sch")
    pins = ["a", "y", VDD, VSS]
    Sym.write(name + ".sym", name, pins, {"a": "in", "y": "out"})
    return pins

def gate_nor(name, n):
    s = Sch(name + ": LV %d-input NOR" % n)
    ins = ["a%d" % i for i in range(n)]
    prev = VDD
    for i, a in enumerate(ins):                       # PMOS series stack
        nxt = "y" if i == n - 1 else "p%d" % i
        s.mos("MP%d" % i, "sg13_lv_pmos", 100 + 100 * i, -300, "%gu" % (1.0 * n), LP, D=nxt, G=a, S=prev, B=VDD)
        prev = nxt
    for i, a in enumerate(ins):                       # NMOS parallel
        s.mos("MN%d" % i, "sg13_lv_nmos", 100 + 100 * i, -100, "0.5u", LN, D="y", G=a, S=VSS, B=VSS)
    s.ports(600, -300, ins=tuple(ins), outs=("y",), ios=(VDD, VSS))
    s.write(name + ".sch")
    pins = ins + ["y", VDD, VSS]
    Sym.write(name + ".sym", name, pins, dict([(a, "in") for a in ins] + [("y", "out")]))
    return pins

def gate_nand2(name):
    s = Sch(name + ": LV 2-input NAND")
    s.mos("MP0", "sg13_lv_pmos", 100, -300, "1u", LP, D="y", G="a0", S=VDD, B=VDD)
    s.mos("MP1", "sg13_lv_pmos", 200, -300, "1u", LP, D="y", G="a1", S=VDD, B=VDD)
    s.mos("MN0", "sg13_lv_nmos", 100, -100, "1u", LN, D="y", G="a0", S="n0", B=VSS)
    s.mos("MN1", "sg13_lv_nmos", 200, -100, "1u", LN, D="n0", G="a1", S=VSS, B=VSS)
    s.ports(400, -300, ins=("a0", "a1"), outs=("y",), ios=(VDD, VSS))
    s.write(name + ".sch")
    pins = ["a0", "a1", "y", VDD, VSS]
    Sym.write(name + ".sym", name, pins, {"a0": "in", "a1": "in", "y": "out"})
    return pins

INV = gate_inv("g1_osc_inv")
NOR2 = gate_nor("g1_osc_nor2", 2)
NOR3 = gate_nor("g1_osc_nor3", 3)
NAND2 = gate_nand2("g1_osc_nand2")

# --------------------------------------------------------- comparator -------
s = Sch("g1_osc_cmp: 5-T comparator, out=1 when inp>inn; vbn = tail mirror gate (about 20 uA)")
s.mos("MT", "sg13_lv_nmos", 300, -100, "2u", "0.5u", D="tail", G="vbn", S=VSS, B=VSS)
s.mos("M1", "sg13_lv_nmos", 200, -200, "4u", "0.3u", D="d1", G="inp", S="tail", B=VSS)
s.mos("M2", "sg13_lv_nmos", 400, -200, "4u", "0.3u", D="o1", G="inn", S="tail", B=VSS)
s.mos("M3", "sg13_lv_pmos", 200, -350, "2u", "0.3u", D="d1", G="d1", S=VDD, B=VDD)   # mirror input
s.mos("M4", "sg13_lv_pmos", 400, -350, "2u", "0.3u", D="o1", G="d1", S=VDD, B=VDD)   # mirror output -> o1
s.inst("XI1", "g1_osc_inv.sym", INV, 650, -250, {"a": "o1", "y": "o2", VDD: VDD, VSS: VSS})
s.inst("XI2", "g1_osc_inv.sym", INV, 850, -250, {"a": "o2", "y": "out", VDD: VDD, VSS: VSS})
s.ports(1100, -350, ins=("inp", "inn", "vbn"), outs=("out",), ios=(VDD, VSS))
s.write("g1_osc_cmp.sch")
CMP = ["inp", "inn", "vbn", "out", VDD, VSS]
Sym.write("g1_osc_cmp.sym", "g1_osc_cmp", CMP, {"inp": "in", "inn": "in", "vbn": "in", "out": "out"})

# ------------------------------------------------------ capacitor bank -------
# cmim ~1.5 fF/um^2: fixed 1.50 pF (31.65 x 31.65; was 1.43 pF / 30.9 x 30.9 in revision 3, raised 5 % so that
# trim code 15 reaches 10 MHz at the mos_ff/res_bcs/cap_bcs corner), trim LSB 100 fF (8.16 x 8.16) x 1,2,4,8
s = Sch("g1_osc_cbank: fixed 1.50 pF + 4-bit trim (100 fF LSB, binary weighted), C = 1.50 pF + 100 fF * code")
s.cap("CF", 100, -200, "31.65u", "31.65u", c0="top", c1=VSS)
for b, side in enumerate(("8.16u", "11.55u", "16.33u", "23.09u")):
    s.cap("CT%d" % b, 300 + 150 * b, -300, side, side, c0="top", c1="b%d" % b)
    s.mos("MS%d" % b, "sg13_lv_nmos", 300 + 150 * b, -150, "4u", LN, D="b%d" % b, G="t%d" % b, S=VSS, B=VSS)
s.ports(1000, -300, ins=("t0", "t1", "t2", "t3"), ios=("top", VSS))
s.write("g1_osc_cbank.sch")
CB = ["t0", "t1", "t2", "t3", "top", VSS]
Sym.write("g1_osc_cbank.sym", "g1_osc_cbank", CB, {"t0": "in", "t1": "in", "t2": "in", "t3": "in"})

# ---------------------------------------------------------------- top -------
RW, RL = "1u", "117u"        # rppd R = 70 + 260*l[um] Ohm for w = 1 um
s = Sch("g1_osc: ping-pong RC relaxation oscillator, f ~ 1/(2 R C ln2), threshold VDD/2, en, 4-bit trim")
s.res("RA", 100, -900, RW, RL, P=VDD, M="va")
s.res("RB", 200, -900, RW, RL, P=VDD, M="vb")
s.inst("XCA", "g1_osc_cbank.sym", CB, 400, -900, {"t0": "trim0", "t1": "trim1", "t2": "trim2", "t3": "trim3", "top": "va", VSS: VSS})
s.inst("XCB", "g1_osc_cbank.sym", CB, 400, -600, {"t0": "trim0", "t1": "trim1", "t2": "trim2", "t3": "trim3", "top": "vb", VSS: VSS})
s.mos("MRA", "sg13_lv_nmos", 600, -900, "4u", LN, D="va", G="rsta", S=VSS, B=VSS)      # discharge A when rsta=1
s.mos("MRB", "sg13_lv_nmos", 600, -600, "4u", LN, D="vb", G="rstb", S=VSS, B=VSS)
# threshold divider VDD/2 (2 x 100 k rppd, 1 pF hold) and bias branch (35 k into an NMOS diode, ~20 uA)
s.res("RT1", 800, -900, "1u", "384.3u", P=VDD, M="vth")
s.res("RT2", 800, -700, "1u", "384.3u", P="vth", M=VSS)
s.cap("CTH", 800, -500, "26u", "26u", c0="vth", c1=VSS)     # 1 pF: absorbs comparator kickback on the threshold node
# antenna diode on vth (revision 5, 2026-09-19): the node carries only gates (M2 of both comparators),
# poly resistors and the 26 um cmim top plate, so the chip-level antenna check flagged it (Ant.b,
# cumulative metal / gate area 283 > 200 without a diode).  p+/n-well diode dpantenna 0.78 x 0.78 um,
# anode vth, cathode = the n-well on vdd: reverse-biased (vth = vdd/2), fA-class leakage, 0.5 fF.
# (dantenna, the n+/substrate variant, was tried first: its model (rs 219 kOhm with tt 700 ns) stalls
# the ngspice transient of this circuit; the p+ model has tt = 1 ps and runs.)
s.diode("DANT", 800, -300, "0.78u", "0.78u", anode="vth", cathode=VDD, model="dpantenna")
s.res("RBIAS", 950, -900, "1u", "134.3u", P=VDD, M="vbn")
s.mos("MBD", "sg13_lv_nmos", 950, -700, "2u", "0.5u", D="vbn", G="vbn", S=VSS, B=VSS)
s.inst("XCMPA", "g1_osc_cmp.sym", CMP, 1200, -900, {"inp": "va", "inn": "vth", "vbn": "vbn", "out": "ca", VDD: VDD, VSS: VSS})
s.inst("XCMPB", "g1_osc_cmp.sym", CMP, 1200, -600, {"inp": "vb", "inn": "vth", "vbn": "vbn", "out": "cb", VDD: VDD, VSS: VSS})
# latch: q = NOR3(ca, en_n, qb) ; qb = NOR2(cb, q) ; rsta = qb ; rstb = NAND2(qb, en) = q | en_n
s.inst("XEN", "g1_osc_inv.sym", INV, 1500, -1000, {"a": "en", "y": "en_n", VDD: VDD, VSS: VSS})
s.inst("XNQ", "g1_osc_nor3.sym", NOR3, 1500, -800, {"a0": "ca", "a1": "en_n", "a2": "qb", "y": "q", VDD: VDD, VSS: VSS})
s.inst("XNQB", "g1_osc_nor2.sym", NOR2, 1500, -550, {"a0": "cb", "a1": "q", "y": "qb", VDD: VDD, VSS: VSS})
s.inst("XRSTB", "g1_osc_nand2.sym", NAND2, 1500, -300, {"a0": "qb", "a1": "en", "y": "rstb", VDD: VDD, VSS: VSS})
s.inst("XRSTA", "g1_osc_inv.sym", INV, 1750, -1000, {"a": "q", "y": "rsta", VDD: VDD, VSS: VSS})      # rsta = ~q (= qb, buffered)
s.inst("XB1", "g1_osc_inv.sym", INV, 1750, -800, {"a": "q", "y": "qn_b", VDD: VDD, VSS: VSS})
s.inst("XB2", "g1_osc_inv.sym", INV, 1750, -600, {"a": "qn_b", "y": "osc_clk", VDD: VDD, VSS: VSS})
s.ports(2000, -1000, ins=("en", "trim0", "trim1", "trim2", "trim3"), outs=("osc_clk",), ios=(VDD, VSS))
s.text("q=1: A charges (rsta=0), B held (rstb=1). va > vdd/2 -> ca=1 -> q=0. en=0 -> q=0, both banks held, osc_clk=0.", 100, -1100)
s.write("g1_osc.sch")
Sym.write("g1_osc.sym", "g1_osc", ["en", "trim0", "trim1", "trim2", "trim3", "osc_clk", VDD, VSS],
          {"en": "in", "trim0": "in", "trim1": "in", "trim2": "in", "trim3": "in", "osc_clk": "out"})
print("wrote g1_osc cells")
