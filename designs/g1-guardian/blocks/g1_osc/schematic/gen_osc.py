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

VDD, VSS = "vdd", "vss"
LP, LN = "0.13u", "0.13u"
# Readable sheets (2026-09-25): signal flow left to right, supplies on rails, bodies tied to
# sources along the symbol (small b:<net> tag otherwise).  Device attributes, instance order and
# port order are those of the original label-per-pin generator, so the xschem netlists are
# unchanged (designs/g1-guardian/review/schematics-readability-20260925).
# Timing resistors RA/RB.  The chip of record carries R0.95 (owner decision 2026-09-24): 0.95 x 117 um =
# 111.15 um, laid out as two 55.575 um segments; the chip CDL has one rppd 1u/111.15u per branch.  This is
# the default.  G1_OSC_VARIANT=baseline draws the earlier 117 um block, whose netlist is
# sim/netlist/g1_osc.spice (43a16205); the two variants differ only in the XRA and XRB lines.
OSC_VARIANT = os.environ.get("G1_OSC_VARIANT", "r095")
if OSC_VARIANT not in ("r095", "baseline"):
    raise SystemExit("G1_OSC_VARIANT must be r095 or baseline")
RA_L = "117u" if OSC_VARIANT == "baseline" else "111.15u"
if OSC_VARIANT == "baseline":
    REF = "sim/netlist/g1_osc.spice sha256 43a16205"
    VARIANT = ("baseline 117 um block (NOT on the chip; the chip carries R0.95, RA/RB l=111.15u); "
               "sub-cells = layout/g1_osc_lvs.cdl 8a8fa94a")
else:
    REF = "sim/netlist/g1_osc.spice sha256 43a16205 except XRA/XRB l=111.15u (R0.95); sub-cells identical"
    VARIANT = ("R0.95 (this sheet): RA/RB rppd 1u/111.15u = chip CDL g1_osc RRA/RRB (canonical CDL 126acd51 lineage); "
               "sub-cells = layout/g1_osc_lvs.cdl 8a8fa94a")


def title(s, cell, what, ref=None, y=-600, width=900):
    s.title_block(100, y, cell, what, ref or ("the %s subcircuit in %s" % (cell, REF)), VARIANT, width=width)


def rails(s, vdd_pts, vss_pts, ytop, ybot, x0=100):
    """vdd rail at ytop and vss rail at ybot, each ending in its port at x0 (call in port order)."""
    s.wire(*([(x0, ytop)] + [(max(p[0] for p in vdd_pts), ytop)]))
    for p in vdd_pts:
        s.wire(p, (p[0], ytop))
    s.port(VDD, (x0, ytop), "inout", flip=1)
    s.wire(*([(x0, ybot)] + [(max(p[0] for p in vss_pts), ybot)]))
    for p in vss_pts:
        s.wire(p, (p[0], ybot))
    s.port(VSS, (x0, ybot), "inout", flip=1)


# ------------------------------------------------------------- gates --------
def gate_inv(name):
    s = Sheet(name)
    mp = s.mos("MP", "sg13_lv_pmos", 200, -300, "1u", LP, D="y", G="a", S=VDD, B=VDD)
    mn = s.mos("MN", "sg13_lv_nmos", 200, -150, "0.5u", LN, D="y", G="a", S=VSS, B=VSS)
    s.body(mp, mn)
    s.wire(mp["G"], mn["G"]); s.wire(mp["D"], mn["D"])
    s.port("a", (80, -225), "in"); s.wire((80, -225), (180, -225))
    s.wire((220, -225), (360, -225)); s.port("y", (360, -225), "out")
    rails(s, [mp["S"]], [mn["S"]], -380, -70)
    title(s, name, "1.2 V inverter", y=-540)
    s.write(name + ".sch")
    pins = ["a", "y", VDD, VSS]
    write_symbol(name + ".sym", name, pins, {"a": "in", "y": "out"}, shape="inv")
    return pins


def gate_nor(name, n):
    s = Sheet(name)
    ins = ["a%d" % i for i in range(n)]
    y0 = -200 - 110 * n                               # PMOS series stack, top to bottom
    prev = VDD
    mps = []
    for i, a in enumerate(ins):
        nxt = "y" if i == n - 1 else "p%d" % i
        mps.append(s.mos("MP%d" % i, "sg13_lv_pmos", 200, y0 + 110 * i, "%gu" % (1.0 * n), LP, D=nxt, G=a, S=prev, B=VDD))
        prev = nxt
    mns = []
    for i, a in enumerate(ins):                       # NMOS parallel
        mns.append(s.mos("MN%d" % i, "sg13_lv_nmos", 200 + 180 * i, -100, "0.5u", LN, D="y", G=a, S=VSS, B=VSS))
    s.body(*(mps + mns))
    for i in range(n - 1):
        s.wire(mps[i]["D"], mps[i + 1]["S"])
        s.lab((220, mps[i]["D"][1] + 20), "p%d" % i, "r")
    s.wire(mps[-1]["D"], mns[0]["D"])
    s.wire((220, -170), (220 + 180 * (n - 1), -170))
    for m in mns[1:]:
        s.wire(m["D"], (m["D"][0], -170))
    for i, a in enumerate(ins):
        s.port(a, (60, mps[i]["G"][1]), "in"); s.wire((60, mps[i]["G"][1]), mps[i]["G"])
        s.stub(mns[i]["G"], a, -40)
    xo = 220 + 180 * (n - 1) + 120
    s.wire((220 + 180 * (n - 1), -170), (xo, -170)); s.port("y", (xo, -170), "out")
    rails(s, [mps[0]["S"]], [m["S"] for m in mns], y0 - 70, -30)
    title(s, name, "1.2 V %d-input NOR" % n, y=y0 - 330)
    s.write(name + ".sch")
    pins = ins + ["y", VDD, VSS]
    write_symbol(name + ".sym", name, pins, dict([(a, "in") for a in ins] + [("y", "out")]), shape="nor")
    return pins


def gate_nand2(name):
    s = Sheet(name)
    mp0 = s.mos("MP0", "sg13_lv_pmos", 200, -300, "1u", LP, D="y", G="a0", S=VDD, B=VDD)
    mp1 = s.mos("MP1", "sg13_lv_pmos", 380, -300, "1u", LP, D="y", G="a1", S=VDD, B=VDD)
    mn0 = s.mos("MN0", "sg13_lv_nmos", 200, -150, "1u", LN, D="y", G="a0", S="n0", B=VSS)
    mn1 = s.mos("MN1", "sg13_lv_nmos", 200, -40, "1u", LN, D="n0", G="a1", S=VSS, B=VSS)
    s.body(mp0, mp1, mn0, mn1)
    s.wire(mp0["G"], mn0["G"])
    s.wire(mp0["D"], (220, -225), (400, -225), mp1["D"]); s.wire((220, -225), mn0["D"])
    s.wire(mn0["S"], mn1["D"]); s.lab((220, -95), "n0", "r")
    s.port("a0", (60, -225), "in"); s.wire((60, -225), (180, -225))
    s.port("a1", (60, -40), "in"); s.wire((60, -40), mn1["G"])
    s.stub(mp1["G"], "a1", -40)
    s.wire((400, -225), (500, -225)); s.port("y", (500, -225), "out")
    rails(s, [mp0["S"], mp1["S"]], [mn1["S"]], -380, 40)
    title(s, name, "1.2 V 2-input NAND", y=-540)
    s.write(name + ".sch")
    pins = ["a0", "a1", "y", VDD, VSS]
    write_symbol(name + ".sym", name, pins, {"a0": "in", "a1": "in", "y": "out"}, shape="nand")
    return pins


INV = gate_inv("g1_osc_inv")
NOR2 = gate_nor("g1_osc_nor2", 2)
NOR3 = gate_nor("g1_osc_nor3", 3)
NAND2 = gate_nand2("g1_osc_nand2")

# --------------------------------------------------------- comparator -------
s = Sheet("g1_osc_cmp")
mt = s.mos("MT", "sg13_lv_nmos", 300, -130, "2u", "0.5u", D="tail", G="vbn", S=VSS, B=VSS)
m1 = s.mos("M1", "sg13_lv_nmos", 200, -250, "4u", "0.3u", D="d1", G="inp", S="tail", B=VSS)
m2 = s.mos("M2", "sg13_lv_nmos", 440, -250, "4u", "0.3u", D="o1", G="inn", S="tail", B=VSS, flip=1)
m3 = s.mos("M3", "sg13_lv_pmos", 240, -400, "2u", "0.3u", D="d1", G="d1", S=VDD, B=VDD, flip=1)   # mirror input
m4 = s.mos("M4", "sg13_lv_pmos", 400, -400, "2u", "0.3u", D="o1", G="d1", S=VDD, B=VDD)            # mirror output -> o1
xi1 = s.inst("XI1", "g1_osc_inv.sym", 620, -320, {"a": "o1", "y": "o2", VDD: VDD, VSS: VSS})
xi2 = s.inst("XI2", "g1_osc_inv.sym", 800, -320, {"a": "o2", "y": "out", VDD: VDD, VSS: VSS})
s.body(mt, m1, m2, m3, m4)
s.wire(m3["D"], m1["D"]); s.wire(m4["D"], m2["D"])
s.wire(m3["G"], m4["G"]); s.wire((320, -400), (320, -340), (220, -340)); s.lab((220, -310), "d1", "l")
s.wire(m1["S"], (220, -190), (420, -190), m2["S"]); s.wire((320, -190), mt["D"]); s.wlab((300, -190), "tail")
s.port("inp", (60, -250), "in"); s.wire((60, -250), m1["G"])
s.port("inn", (60, -200), "in"); s.stub(m2["G"], "inn", 40)
s.port("vbn", (60, -130), "in"); s.wire((60, -130), mt["G"])
s.wire((420, -320), xi1["a"]); s.wlab((540, -320), "o1")
s.wire(xi1["y"], xi2["a"]); s.wlab((730, -320), "o2")
s.port("out", (960, -320), "out"); s.wire(xi2["y"], (960, -320))
s.supplies(xi1); s.supplies(xi2)
rails(s, [m3["S"], m4["S"]], [mt["S"]], -470, -60)
s.frame(150, -500, 500, -40, "5-T NMOS-input stage, PMOS mirror")
s.frame(540, -500, 900, -40, "output inverters")
s.text("out = 1 when inp > inn; tail from the vbn mirror gate (about 20 uA, MBD in g1_osc)", 150, 0)
title(s, "g1_osc_cmp", "continuous-time comparator", "sim/netlist/g1_osc_cmp.spice sha256 ad2ce6b3", y=-720, width=1000)
s.write("g1_osc_cmp.sch")
CMP = ["inp", "inn", "vbn", "out", VDD, VSS]
write_symbol("g1_osc_cmp.sym", "g1_osc_cmp", CMP, {"inp": "in", "inn": "in", "vbn": "in", "out": "out"},
             shape="amp", left=["inp", "inn"], right=["out"], top=[VDD], bottom=["vbn", VSS])

# ------------------------------------------------------ capacitor bank -------
# cmim ~1.5 fF/um^2: fixed 1.50 pF (31.65 x 31.65; was 1.43 pF / 30.9 x 30.9 in revision 3, raised 5 % so that
# trim code 15 reaches 10 MHz at the mos_ff/res_bcs/cap_bcs corner), trim LSB 100 fF (8.16 x 8.16) x 1,2,4,8
s = Sheet("g1_osc_cbank")
cf = s.cap("CF", 160, -300, "31.65u", "31.65u", c0="top", c1=VSS)
cts, mss = [], []
for b, side in enumerate(("8.16u", "11.55u", "16.33u", "23.09u")):
    x = 380 + 220 * b
    cts.append(s.cap("CT%d" % b, x, -300, side, side, c0="top", c1="b%d" % b))
    mss.append(s.mos("MS%d" % b, "sg13_lv_nmos", x - 20, -180, "4u", LN, D="b%d" % b, G="t%d" % b, S=VSS, B=VSS))
s.body(*mss)
s.wire(cf["c0"], (160, -400), (cts[-1]["c0"][0], -400))
for c, m in zip(cts, mss):
    s.wire(c["c0"], (c["c0"][0], -400)); s.wire(c["c1"], m["D"]); s.lab((c["c1"][0], -240), c.pins["c1"][1], "r")
for b in range(4):
    s.port("t%d" % b, (60, -140 + 25 * b), "in")
for b, m in enumerate(mss):
    s.stub(m["G"], "t%d" % b, -40)
s.port("top", (100, -400), "inout", flip=1); s.wire((100, -400), (160, -400))
s.wire(cf["c1"], (160, -80), (mss[-1]["S"][0], -80))
for m in mss:
    s.wire(m["S"], (m["S"][0], -80))
s.port(VSS, (100, -80), "inout", flip=1); s.wire((100, -80), (160, -80))
s.text("C(top) = 1.50 pF + 100 fF x code (cmim ~1.5 fF/um^2); a trim cap counts when its NMOS switch is on (t_b = 1)", 100, 0)
title(s, "g1_osc_cbank", "timing capacitor: fixed 1.50 pF + 4-bit binary trim", y=-620)
s.write("g1_osc_cbank.sch")
CB = ["t0", "t1", "t2", "t3", "top", VSS]
write_symbol("g1_osc_cbank.sym", "g1_osc_cbank", CB, {"t0": "in", "t1": "in", "t2": "in", "t3": "in"},
             left=["t0", "t1", "t2", "t3"], right=[], top=["top"], bottom=[VSS], label="1.5 pF + trim")

# ---------------------------------------------------------------- top -------
RW, RL = "1u", RA_L         # rppd R = 70 + 260*l[um] Ohm for w = 1 um: 30.3 k (117u) / 28.97 k (111.15u)
s = Sheet("g1_osc")
ra = s.res("RA", 200, -800, RW, RL, P=VDD, M="va")
rb = s.res("RB", 200, -420, RW, RL, P=VDD, M="vb")
tr = {"t0": "trim0", "t1": "trim1", "t2": "trim2", "t3": "trim3"}
xca = s.inst("XCA", "g1_osc_cbank.sym", 320, -620, dict(tr, top="va", vss=VSS))
xcb = s.inst("XCB", "g1_osc_cbank.sym", 320, -240, dict(tr, top="vb", vss=VSS))
mra = s.mos("MRA", "sg13_lv_nmos", 480, -640, "4u", LN, D="va", G="rsta", S=VSS, B=VSS)      # discharge A when rsta=1
mrb = s.mos("MRB", "sg13_lv_nmos", 480, -260, "4u", LN, D="vb", G="rstb", S=VSS, B=VSS)
# threshold divider VDD/2 (2 x 100 k rppd, 1 pF hold) and bias branch (35 k into an NMOS diode, ~20 uA)
rt1 = s.res("RT1", 700, -620, "1u", "384.3u", P=VDD, M="vth")
rt2 = s.res("RT2", 700, -460, "1u", "384.3u", P="vth", M=VSS)
cth = s.cap("CTH", 800, -460, "26u", "26u", c0="vth", c1=VSS)     # 1 pF: absorbs comparator kickback on the threshold node
# antenna diode on vth (revision 5, 2026-09-19): the node carries only gates (M2 of both comparators),
# poly resistors and the 26 um cmim top plate, so the chip-level antenna check flagged it (Ant.b,
# cumulative metal / gate area 283 > 200 without a diode).  p+/n-well diode dpantenna 0.78 x 0.78 um,
# anode vth, cathode = the n-well on vdd: reverse-biased (vth = vdd/2), fA-class leakage, 0.5 fF.
# (dantenna, the n+/substrate variant, was tried first: its model (rs 219 kOhm with tt 700 ns) stalls
# the ngspice transient of this circuit; the p+ model has tt = 1 ps and runs.)
dant = s.diode("DANT", 900, -460, "0.78u", "0.78u", anode="vth", cathode=VDD, model="dpantenna", rot=2)
rbias = s.res("RBIAS", 860, -230, "1u", "134.3u", P=VDD, M="vbn")
mbd = s.mos("MBD", "sg13_lv_nmos", 880, -110, "2u", "0.5u", D="vbn", G="vbn", S=VSS, B=VSS, flip=1)
xcmpa = s.inst("XCMPA", "g1_osc_cmp.sym", 1150, -720, {"inp": "va", "inn": "vth", "vbn": "vbn", "out": "ca", VDD: VDD, VSS: VSS})
xcmpb = s.inst("XCMPB", "g1_osc_cmp.sym", 1150, -340, {"inp": "vb", "inn": "vth", "vbn": "vbn", "out": "cb", VDD: VDD, VSS: VSS})
# latch: q = NOR3(ca, en_n, qb) ; qb = NOR2(cb, q) ; rsta = qb ; rstb = NAND2(qb, en) = q | en_n
xen = s.inst("XEN", "g1_osc_inv.sym", 1400, -900, {"a": "en", "y": "en_n", VDD: VDD, VSS: VSS})
xnq = s.inst("XNQ", "g1_osc_nor3.sym", 1450, -720, {"a0": "ca", "a1": "en_n", "a2": "qb", "y": "q", VDD: VDD, VSS: VSS})
xnqb = s.inst("XNQB", "g1_osc_nor2.sym", 1450, -470, {"a0": "cb", "a1": "q", "y": "qb", VDD: VDD, VSS: VSS})
xrstb = s.inst("XRSTB", "g1_osc_nand2.sym", 1450, -260, {"a0": "qb", "a1": "en", "y": "rstb", VDD: VDD, VSS: VSS})
xrsta = s.inst("XRSTA", "g1_osc_inv.sym", 1720, -900, {"a": "q", "y": "rsta", VDD: VDD, VSS: VSS})      # rsta = ~q (= qb, buffered)
xb1 = s.inst("XB1", "g1_osc_inv.sym", 1720, -720, {"a": "q", "y": "qn_b", VDD: VDD, VSS: VSS})
xb2 = s.inst("XB2", "g1_osc_inv.sym", 1880, -720, {"a": "qn_b", "y": "osc_clk", VDD: VDD, VSS: VSS})
s.body(mra, mrb, mbd)
for x in (xca, xcb, xcmpa, xcmpb, xen, xnq, xnqb, xrstb, xrsta, xb1, xb2):
    s.supplies(x)
# RC branches A and B
for r, x, m, cmp, net, y in ((ra, xca, mra, xcmpa, "va", -730), (rb, xcb, mrb, xcmpb, "vb", -350)):
    s.stub(r["P"], VDD, 0, -20)
    s.wire(r["M"], (200, y), (m["D"][0], y), m["D"]); s.wire(x["top"], (x["top"][0], y))
    s.wire((m["D"][0], y), (1040, y), (1040, cmp["inp"][1]), cmp["inp"]); s.wlab((620, y), net)
    for t in ("t0", "t1", "t2", "t3"):
        s.stub(x[t], tr[t], -30)
s.stub(mra["G"], "rsta", -40); s.stub(mrb["G"], "rstb", -40)
s.stub(mra["S"], VSS, 0, 20); s.stub(mrb["S"], VSS, 0, 20)
# threshold vdd/2, antenna diode, bias
s.stub(rt1["P"], VDD, 0, -20); s.wire(rt1["M"], rt2["P"]); s.stub(rt2["M"], VSS, 0, 20)
s.wire((700, -540), (900, -540), dant["d0"]); s.wire((800, -540), cth["c0"]); s.stub(cth["c1"], VSS, 0, 20)
s.stub(dant["d1"], VDD, 0, 20)
s.wire((900, -540), (1000, -540), (1000, xcmpa["inn"][1]), xcmpa["inn"]); s.wire((1000, -540), (1000, xcmpb["inn"][1]), xcmpb["inn"])
s.wlab((990, -540), "vth")
s.stub(rbias["P"], VDD, 0, -20); s.wire(rbias["M"], mbd["D"]); s.wire(mbd["G"], (900, -170), (860, -170)); s.wire((900, -170), (960, -170))
s.stub(mbd["S"], VSS, 0, 20); s.wlab((960, -170), "vbn")
# comparator outputs into the latch
s.wire(xcmpa["out"], (1300, -720), (1300, -740), xnq["a0"]); s.wlab((1300, -720), "ca")
s.wire(xcmpb["out"], (1300, -340), (1300, -480), xnqb["a0"]); s.wlab((1290, -340), "cb")
s.port("en", (1260, -900), "in"); s.wire((1260, -900), xen["a"])
s.wire(xen["y"], (1520, -900)); s.wlab((1520, -900), "en_n"); s.stub(xnq["a1"], "en_n", -40)
s.stub(xnq["a2"], "qb", -40); s.stub(xnqb["a1"], "q", -40)
s.stub(xrstb["a0"], "qb", -40); s.stub(xrstb["a1"], "en", -40)
s.wire(xnq["y"], (1600, -720), (1600, -900), xrsta["a"]); s.wire((1600, -720), xb1["a"]); s.wlab((1560, -720), "q")
s.wire(xnqb["y"], (1600, -470)); s.wlab((1600, -470), "qb")
s.wire(xrstb["y"], (1600, -260)); s.wlab((1600, -260), "rstb")
s.wire(xrsta["y"], (1840, -900)); s.wlab((1840, -900), "rsta")
s.wire(xb1["y"], xb2["a"]); s.wlab((1805, -720), "qn_b")
for i in range(4):
    s.port("trim%d" % i, (100, -1000 + 25 * i), "in")
s.port("osc_clk", (2060, -720), "out"); s.wire(xb2["y"], (2060, -720))
s.port(VDD, (100, -890), "inout"); s.port(VSS, (100, -865), "inout")
s.frame(140, -900, 580, -120, "RC timing branches A / B (4-bit trim)")
s.frame(620, -700, 980, -40, "threshold vdd/2 + bias")
s.frame(1020, -900, 1250, -120, "comparators")
s.frame(1300, -1010, 2000, -120, "SR latch, reset switches, clock out")
s.text("q=1: A charges through RA (rsta=0), B held at 0 (rstb=1). va > vdd/2 -> ca=1 -> q=0, B charges. en=0 -> q=0, both banks held, osc_clk=0.\n"
       "Half period = R C ln2 + comparator/latch delay; threshold is a fixed fraction of vdd, so f is first-order independent of vdd.\n"
       "Simulated (not measured): R0.95 chip variant, trim 8, tt/1.2 V/27 C with clock-tree load: 9.436 MHz (block); chip netlists 9.443-9.483 MHz.\n"
       "Baseline 117 um block (G1_OSC_VARIANT=baseline): 9.919 MHz schematic, 8.994 MHz post-layout at trim 8 (history, not on the chip). See ../README.md.", 140, 10)
title(s, "g1_osc", "1.2 V ping-pong RC relaxation oscillator, about 10 MHz, 4-bit trim", REF, y=-1300, width=1800)
s.write("g1_osc.sch")
write_symbol("g1_osc.sym", "g1_osc", ["en", "trim0", "trim1", "trim2", "trim3", "osc_clk", VDD, VSS],
             {"en": "in", "trim0": "in", "trim1": "in", "trim2": "in", "trim3": "in", "osc_clk": "out"})
print("wrote g1_osc cells")
