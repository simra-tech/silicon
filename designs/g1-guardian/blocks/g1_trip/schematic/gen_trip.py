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
from xsch_readable import Sheet, write_symbol, HDR, MOS_N  # noqa: E402

VDD, VSS = "vdd", "vss"
# Readable sheets (2026-09-25): signal flow left to right, supplies on rails, bodies tied to
# sources along the symbol (small b:<net> tag otherwise).  Device attributes, instance order and
# port order are those of the original label-per-pin generator, so the xschem netlists are
# unchanged (designs/g1-guardian/review/schematics-readability-20260925).
# Variant.  Default "chip": the sheets of the chip of record (TRIP regenpair4 + NF4, owner decision 2026-09-24):
# soft comparator g1_cmp with the NF4 input pair M1/M2 w=24u l=0.68u ng=4 (+ the drawn as/ad/ps/pd of the
# four-finger layout), hard comparator g1_cmp_regenpair4 (M3/M4 w=6u l=0.26u, M1/M2 12u/0.34u), rppd bodies on vss.
# The netlist is compared with the chip deck trip.spice (f5f0a90a).  G1_TRIP_VARIANT=baseline regenerates the
# historical 12u/0.34u sheets (both comparators g1_cmp, rppd body = symbol default sub!), whose netlists are
# ../sim/netlist/*.spice; they are kept in historical_12u034/.
TRIP_VARIANT = os.environ.get("G1_TRIP_VARIANT", "chip")
if TRIP_VARIANT not in ("chip", "baseline"):
    raise SystemExit("G1_TRIP_VARIANT must be chip or baseline")
CHIP = TRIP_VARIANT == "chip"
DECK = "sim/qualification/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/trip.spice sha256 f5f0a90a"
RBODY = "vss" if CHIP else None
if CHIP:
    VARIANT = ("chip of record (regenpair4 + NF4): soft g1_cmp M1/M2 24u/0.68u ng=4, hard g1_cmp_regenpair4 M3/M4 6u/0.26u; "
               "rppd bodies on vss as in the chip deck; layout/g1_trip_lvs.cdl 60a9ad6e + regenpair4/NF4 cell CDLs")
else:
    VARIANT = ("HISTORICAL 12u/0.34u comparators, NOT on the chip (chip-of-record sheets: ../, G1_TRIP_VARIANT=chip); "
               "netlists ../../sim/netlist/*.spice")


def ref(cell, hist):
    return ("the %s subcircuit in %s (chip deck)" % (cell, DECK)) if CHIP else hist


def title(s, cell, what, ref, y, width=1000):
    s.title_block(100, y, cell, what, ref, VARIANT, width=width)


def rails(s, top, bot, ytop, ybot, vtop=VDD, x0=100):
    for d in top:
        s.wire(d, (d[0], ytop))
    s.wire((x0, ytop), (max(p[0] for p in top), ytop)); s.port(vtop, (x0, ytop), "inout", flip=1)
    for d in bot:
        s.wire(d, (d[0], ybot))
    s.wire((x0, ybot), (max(p[0] for p in bot), ybot)); s.port(VSS, (x0, ybot), "inout", flip=1)


def inverter(name, what, pm, pw, pl, nm, nw, nl, vp, ref):
    s = Sheet(name)
    mp = s.mos("MP", pm, 200, -300, pw, pl, D="y", G="a", S=vp, B=vp)
    mn = s.mos("MN", nm, 200, -150, nw, nl, D="y", G="a", S=VSS, B=VSS)
    s.body(mp, mn)
    s.wire(mp["G"], mn["G"]); s.wire(mp["D"], mn["D"])
    s.port("a", (80, -225), "in"); s.wire((80, -225), (180, -225))
    s.wire((220, -225), (360, -225)); s.port("y", (360, -225), "out")
    rails(s, [mp["S"]], [mn["S"]], -380, -70, vp)
    title(s, name, what, ref, -560, 900)
    s.write(name + ".sch")


# ------------------------------------------------------------- cells --------
inverter("g1_inv", "1.2 V inverter", "sg13_lv_pmos", "1u", "0.13u", "sg13_lv_nmos", "0.5u", "0.13u", VDD,
         ref("g1_inv", "the g1_inv subcircuit in sim/netlist/g1_trip.spice sha256 6f265319"))
INV = ["a", "y", VDD, VSS]
write_symbol("g1_inv.sym", "g1_inv", INV, {"a": "in", "y": "out"}, shape="inv")

s = Sheet("g1_tg")
mn = s.mos("MN", "sg13_lv_nmos", 200, -200, "1u", "0.13u", D="a", G="en", S="b", B=VSS)
mp = s.mos("MP", "sg13_lv_pmos", 400, -200, "2u", "0.13u", D="b", G="enb", S="a", B=VDD)
s.body(mn, mp)
s.wire(mn["D"], (220, -270), (420, -270), mp["S"]); s.wire(mn["S"], (220, -130), (420, -130), mp["D"])
s.port("en", (80, -200), "in"); s.wire((80, -200), mn["G"])
s.port("enb", (80, -60), "in"); s.stub(mp["G"], "enb", -40)
s.port("a", (100, -270), "inout", flip=1); s.wire((100, -270), (220, -270))
s.port("b", (540, -130), "inout"); s.wire((420, -130), (540, -130))
s.port(VDD, (80, -30), "inout"); s.port(VSS, (80, 0), "inout")
title(s, "g1_tg", "1.2 V transmission gate, on when en=1 (enb=0)", "g1_tg netlisted standalone (no instance in g1_trip)", -480, 900)
s.write("g1_tg.sch")
TG = ["en", "enb", "a", "b", VDD, VSS]
write_symbol("g1_tg.sym", "g1_tg", TG, {"en": "in", "enb": "in"}, left=["en", "enb", "a"], right=["b"], top=[VDD], bottom=[VSS])

inverter("g1_thv_inv", "3.3 V inverter (DAC switch drive)", "sg13_hv_pmos", "3.9u", "0.45u", "sg13_hv_nmos", "1.9u", "0.45u",
         "vdda", ref("g1_thv_inv", "the g1_thv_inv subcircuit in sim/netlist/g1_tlvlup.spice sha256 5eac9e76"))
THVINV = ["a", "y", "vdda", VSS]
write_symbol("g1_thv_inv.sym", "g1_thv_inv", THVINV, {"a": "in", "y": "out"}, shape="inv")

s = Sheet("g1_tlvlup")
xi = s.inst("XI", "g1_inv.sym", 200, -225, {"a": "a", "y": "ab", VDD: VDD, VSS: VSS})
mn1 = s.mos("MN1", "sg13_hv_nmos", 440, -150, "1.9u", "0.45u", D="nb", G="a", S=VSS, B=VSS)
mn2 = s.mos("MN2", "sg13_hv_nmos", 640, -150, "1.9u", "0.45u", D="n", G="ab", S=VSS, B=VSS)
mp1 = s.mos("MP1", "sg13_hv_pmos", 440, -300, "0.3u", "0.45u", D="nb", G="n", S="vdda", B="vdda")
mp2 = s.mos("MP2", "sg13_hv_pmos", 640, -300, "0.3u", "0.45u", D="n", G="nb", S="vdda", B="vdda")
xo = s.inst("XO", "g1_thv_inv.sym", 900, -225, {"a": "nb", "y": "y", "vdda": "vdda", VSS: VSS})
xob = s.inst("XOB", "g1_thv_inv.sym", 1100, -225, {"a": "y", "y": "yb", "vdda": "vdda", VSS: VSS})
s.body(mn1, mn2, mp1, mp2)
s.port("a", (60, -225), "in"); s.wire((60, -225), xi["a"])
s.wire((110, -225), (110, -100), (400, -100), (400, -150), mn1["G"])
s.wire(xi["y"], (300, -225)); s.wlab((300, -225), "ab"); s.stub(mn2["G"], "ab", -40)
s.wire(mp1["D"], mn1["D"]); s.wire(mp2["D"], mn2["D"])
s.wire((460, -245), (590, -245), (590, -300), mp2["G"])
s.wire((660, -205), (400, -205), (400, -300), mp1["G"])
s.lab((460, -225), "nb", "l"); s.lab((660, -225), "n", "r")
s.stub(xo["a"], "nb", -40)
s.wire(xo["y"], xob["a"]); s.wire((1000, -225), (1000, -140), (1300, -140)); s.port("y", (1300, -140), "out")
s.wlab((1030, -225), "y")
s.wire(xob["y"], (1300, -225)); s.port("yb", (1300, -225), "out")
s.supplies(xi); s.supplies(xo); s.supplies(xob)
s.wire(mp1["S"], (460, -380), (660, -380), mp2["S"]); s.lab((460, -380), "vdda", "l")
s.wire(mn1["S"], (460, -70), (660, -70), mn2["S"]); s.lab((460, -70), VSS, "l")
s.port(VDD, (60, 20), "inout"); s.port("vdda", (60, 50), "inout"); s.port(VSS, (60, 80), "inout")
s.text("DAC code bit: 1.2 V a -> 3.3 V y (= a) and yb for the thick-oxide switch gates. Structure of sg13g2_LevelUp.", 300, 0)
title(s, "g1_tlvlup", "1.2 V code bit to 3.3 V y / yb", ref("g1_tlvlup", "sim/netlist/g1_tlvlup.spice sha256 5eac9e76"), -620, 1200)
s.write("g1_tlvlup.sch")
TLVLUP = ["a", "y", "yb", VDD, "vdda", VSS]
write_symbol("g1_tlvlup.sym", "g1_tlvlup", TLVLUP, {"a": "in", "y": "out", "yb": "out"}, label="1.2 -> 3.3 V")

# ---------------------------------------------------------- comparator ------
CMP = ["inp", "inn", "clk", "q", "qb", VDD, VSS]
GEOM_FMT = "@spiceprefix@name @pinlist @model w=@w l=@l ng=@ng m=@m mm_ok=@mm_ok as=@as ad=@ad ps=@ps pd=@pd"


def write_geom_nmos():
    """LV NMOS drawn like the PDK symbol, netlisted with the drain/source geometry the NF4 pair carries in
    the chip deck (as/ad/ps/pd of the four-finger layout).  Same model and pin order as sg13_lv_nmos."""
    ls = [(-20, 0, 5, 0), (5, -20, 5, 20), (10, -22, 10, 22), (10, -18, 20, -18), (20, -18, 20, -30),
          (10, 18, 20, 18), (20, 18, 20, 30), (10, 0, 20, 0), (14, 15, 20, 18), (14, 21, 20, 18)]
    out = [HDR.replace("K {}", 'K {type=nmos\nformat="%s"\ntemplate="name=M1 model=sg13_lv_nmos spiceprefix=X w=1u l=0.13u '
                       'ng=1 m=1 mm_ok=1 as=0 ad=0 ps=0 pd=0"}' % GEOM_FMT)]
    out += ["L 4 %s %s %s %s {}\n" % l for l in ls]
    out += ["T {@name} 25 -45 0 0 0.2 0.2 {}\n", "T {w=@w l=@l ng=@ng} 25 -28 0 0 0.18 0.18 {layer=13}\n",
            "T {as=@as ad=@ad ps=@ps pd=@pd} 25 -12 0 0 0.14 0.14 {layer=13}\n", "T {@model} 25 18 0 0 0.15 0.15 {layer=13}\n"]
    for p, (x, y) in MOS_N.items():
        out.append("B 5 %s %s %s %s {name=%s dir=inout}\n" % (x - 2.5, y - 2.5, x + 2.5, y + 2.5, p))
    open("g1_nmos_geom.sym", "w").write("".join(out))


def in_pair(s, name, x, y, m12, nets, flip=0):
    w, l, ng, geom = m12
    if geom is None:
        return s.mos(name, "sg13_lv_nmos", x, y, w, l, ng=ng, flip=flip, **nets)
    attrs = "name=%s model=sg13_lv_nmos w=%s l=%s ng=%d m=1 as=%s ad=%s ps=%s pd=%s" % ((name, w, l, ng) + geom)
    return s.place("g1_nmos_geom.sym", MOS_N, name, x, y, attrs, nets, flip=flip)


def cmp_sheet(cell, m12, m34, what, cref, note):
    s = Sheet(cell)
    mtail = s.mos("MTAIL", "sg13_lv_nmos", 550, -160, "16u", "0.13u", D="tail", G="clk", S=VSS, B=VSS)
    m1 = in_pair(s, "M1", 400, -300, m12, dict(D="xp", G="inp", S="tail", B=VSS))
    m2 = in_pair(s, "M2", 700, -300, m12, dict(D="xq", G="inn", S="tail", B=VSS), flip=1)
    # neutralisation dummies: gate on one input, source/drain shorted to the opposite drain
    md1 = s.mos("MD1", "sg13_lv_nmos", 950, -300, "6u", "0.13u", D="xq", G="inp", S="xq", B=VSS, flip=1)
    md2 = s.mos("MD2", "sg13_lv_nmos", 150, -300, "6u", "0.13u", D="xp", G="inn", S="xp", B=VSS)
    m3 = s.mos("M3", "sg13_lv_nmos", 400, -460, m34[0], m34[1], D="xn", G="yn", S="xp", B=VSS)
    m4 = s.mos("M4", "sg13_lv_nmos", 700, -460, m34[0], m34[1], D="yn", G="xn", S="xq", B=VSS, flip=1)
    m5 = s.mos("M5", "sg13_lv_pmos", 400, -600, "3u", "0.13u", D="xn", G="yn", S=VDD, B=VDD)
    m6 = s.mos("M6", "sg13_lv_pmos", 700, -600, "3u", "0.13u", D="yn", G="xn", S=VDD, B=VDD, flip=1)
    m7 = s.mos("M7", "sg13_lv_pmos", 150, -600, "6u", "0.13u", D="xn", G="clk", S=VDD, B=VDD)
    m8 = s.mos("M8", "sg13_lv_pmos", 950, -600, "6u", "0.13u", D="yn", G="clk", S=VDD, B=VDD, flip=1)
    m9 = s.mos("M9", "sg13_lv_pmos", 150, -460, "3u", "0.13u", D="xp", G="clk", S=VDD, B=VDD)
    m10 = s.mos("M10", "sg13_lv_pmos", 950, -460, "3u", "0.13u", D="xq", G="clk", S=VDD, B=VDD, flip=1)
    # inverter buffers, skewed to a low threshold (~0.35 V) so the common-mode dip of X/Y during the
    # amplification phase (to about VDD-|Vthp|) does not reach the SR latch; only a full regeneration does
    miap = s.mos("MIAP", "sg13_lv_pmos", 1200, -620, "1u", "0.13u", D="xnb", G="xn", S=VDD, B=VDD)
    mian = s.mos("MIAN", "sg13_lv_nmos", 1200, -500, "4u", "0.13u", D="xnb", G="xn", S=VSS, B=VSS)
    mibp = s.mos("MIBP", "sg13_lv_pmos", 1200, -340, "1u", "0.13u", D="ynb", G="yn", S=VDD, B=VDD)
    mibn = s.mos("MIBN", "sg13_lv_nmos", 1200, -220, "4u", "0.13u", D="ynb", G="yn", S=VSS, B=VSS)
    # NOR SR latch: qb = NOR(xnb, q) ; q = NOR(ynb, qb)
    mnap1 = s.mos("MNAP1", "sg13_lv_pmos", 1500, -640, "4u", "0.13u", D="na", G="xnb", S=VDD, B=VDD)
    mnap2 = s.mos("MNAP2", "sg13_lv_pmos", 1540, -540, "4u", "0.13u", D="qb", G="q", S="na", B=VDD, flip=1)
    mnan1 = s.mos("MNAN1", "sg13_lv_nmos", 1500, -380, "1.5u", "0.13u", D="qb", G="xnb", S=VSS, B=VSS)
    mnan2 = s.mos("MNAN2", "sg13_lv_nmos", 1680, -380, "1.5u", "0.13u", D="qb", G="q", S=VSS, B=VSS)
    mnbp1 = s.mos("MNBP1", "sg13_lv_pmos", 1950, -640, "4u", "0.13u", D="nb", G="ynb", S=VDD, B=VDD)
    mnbp2 = s.mos("MNBP2", "sg13_lv_pmos", 1990, -540, "4u", "0.13u", D="q", G="qb", S="nb", B=VDD, flip=1)
    mnbn1 = s.mos("MNBN1", "sg13_lv_nmos", 1950, -380, "1.5u", "0.13u", D="q", G="ynb", S=VSS, B=VSS)
    mnbn2 = s.mos("MNBN2", "sg13_lv_nmos", 2130, -380, "1.5u", "0.13u", D="q", G="qb", S=VSS, B=VSS)
    s.body(mtail, m1, m2, md1, md2, m3, m4, m5, m6, m7, m8, m9, m10, miap, mian, mibp, mibn,
           mnap1, mnap2, mnan1, mnan2, mnbp1, mnbp2, mnbn1, mnbn2)
    # StrongARM core: input pair, cross-coupled NMOS/PMOS, clocked tail
    s.wire(m5["D"], m3["D"]); s.wire(m3["S"], m1["D"]); s.wire(m6["D"], m4["D"]); s.wire(m4["S"], m2["D"])
    s.lab((420, -550), "xn", "r"); s.lab((680, -550), "yn", "l"); s.lab((420, -400), "xp", "r"); s.lab((680, -400), "xq", "l")
    s.wire(m5["G"], m3["G"]); s.wire(m6["G"], m4["G"])
    s.wire((380, -530), (680, -530)); s.wire((420, -510), (720, -510))
    s.wire(m1["S"], (420, -230), (680, -230), m2["S"]); s.wire(mtail["D"], (570, -230)); s.wlab((540, -230), "tail")
    s.port("inp", (60, -380), "in"); s.wire((60, -380), (300, -380), (300, -300), m1["G"])
    s.port("inn", (60, -110), "in")
    s.stub(m2["G"], "inn", 40)
    s.port("clk", (60, -160), "in"); s.wire((60, -160), mtail["G"])
    # precharge devices and dummies (connected by name)
    for d, net in ((m7, "xn"), (m9, "xp"), (m8, "yn"), (m10, "xq")):
        s.stub(d["D"], net, 0, 20); s.stub(d["G"], "clk", 30 if d["G"][0] > d.origin[0] else -30)
    for d in (m9, m10):
        s.stub(d["S"], VDD, 0, -20)
    s.stub(md1["G"], "inp", 30)
    s.stub(md2["G"], "inn", -30)
    s.stub(md2["D"], "xp", 0, -20); s.stub(md2["S"], "xp", 0, 20); s.stub(md1["D"], "xq", 0, -20); s.stub(md1["S"], "xq", 0, 20)
    # output buffers
    s.wire(miap["G"], mian["G"]); s.wire(miap["D"], mian["D"]); s.stub((1180, -560), "xn", -40)
    s.wire(mibp["G"], mibn["G"]); s.wire(mibp["D"], mibn["D"]); s.stub((1180, -280), "yn", -40)
    s.stub(mibp["S"], VDD, 0, -20); s.stub(mian["S"], VSS, 0, 20)
    # NOR SR latch A (qb) and B (q)
    s.wire((1220, -560), (1460, -560)); s.wlab((1330, -560), "xnb")
    s.wire(mnap1["G"], (1460, -640), (1460, -380), mnan1["G"])
    s.wire(mnap1["D"], mnap2["S"]); s.lab((1520, -590), "na", "l")
    s.wire(mnap2["D"], mnan1["D"]); s.wire((1520, -450), (1700, -450), mnan2["D"])
    s.stub(mnap2["G"], "q", 30); s.stub(mnan2["G"], "q", -30)
    s.wire((1220, -280), (1420, -280)); s.wlab((1420, -280), "ynb")
    s.stub(mnbp1["G"], "ynb", -40); s.stub(mnbn1["G"], "ynb", -40)
    s.wire(mnbp1["D"], mnbp2["S"]); s.lab((1970, -590), "nb", "l")
    s.wire(mnbp2["D"], mnbn1["D"]); s.wire((1970, -450), (2150, -450), mnbn2["D"])
    s.stub(mnbp2["G"], "qb", 30); s.stub(mnbn2["G"], "qb", -30)
    s.wire((1700, -450), (1800, -450)); s.wlab((1780, -450), "qb")
    s.wire((2150, -450), (2260, -450)); s.port("q", (2260, -450), "out")
    s.port("qb", (1800, -250), "out"); s.wire((1800, -450), (1800, -250))
    # supplies
    top = [m7["S"], m5["S"], m6["S"], m8["S"], miap["S"], mnap1["S"], mnbp1["S"]]
    bot = [mtail["S"], mibn["S"], mnan1["S"], mnan2["S"], mnbn1["S"], mnbn2["S"]]
    rails(s, top, bot, -700, -90)
    s.frame(90, -760, 1000, -110, "StrongARM latch: precharge (clk=0), evaluate (clk=1); dummies MD1/MD2 cancel input kickback")
    s.frame(1120, -760, 1330, -110, "skewed inverters")
    s.frame(1400, -760, 2230, -110, "NOR SR latch: holds q between strobes")
    s.text("q = 1 when inp > inn at the rising clk edge.  Core sizes from 2AMLogic sg13g2-comparator (Apache-2.0), tail bias branch removed.\n" + note, 90, -40)
    title(s, cell, what, cref, -960, 2000)
    s.write(cell + ".sch")
    write_symbol(cell + ".sym", cell, CMP, {"inp": "in", "inn": "in", "clk": "in", "q": "out", "qb": "out"},
                 shape="amp", left=["inn", "inp"], right=["q", "qb"], top=[VDD], bottom=["clk", VSS])


if CHIP:
    write_geom_nmos()
    cmp_sheet("g1_cmp", ("24u", "0.68u", 4, ("4.56p", "6.36p", "25.52u", "38.12u")), ("3u", "0.13u"),
              "1.2 V StrongARM comparator, soft path (NF4 input pair 24u/0.68u, 4 fingers)", ref("g1_cmp", ""),
              "NF4: M1/M2 w=24u l=0.68u ng=4 with the four-finger drain/source geometry (as/ad/ps/pd) of the layout.\n"
              "Simulated NF4 decision delay on the extraction, 1 mV overdrive: 0.859 ns tt/1.2 V/27 C (g1_trip/sim/postlayout/README.md).")
    cmp_sheet("g1_cmp_regenpair4", ("12u", "0.34u", 1, None), ("6u", "0.26u"),
              "1.2 V StrongARM comparator, hard path (regenerative pair M3/M4 6u/0.26u)", ref("g1_cmp_regenpair4", ""),
              "regenpair4: the regenerative NMOS pair M3/M4 is 6u/0.26u (baseline 3u/0.13u); input pair 12u/0.34u.\n"
              "Hard-comparator decision delay on the extraction: not run (g1_trip/README.md).")
else:
    cmp_sheet("g1_cmp", ("12u", "0.34u", 1, None), ("3u", "0.13u"),
              "1.2 V StrongARM comparator with NOR SR output latch (historical 12u/0.34u sizes)", "sim/netlist/g1_cmp.spice sha256 a31a1f15",
              "Historical sizes; on the chip the soft comparator is NF4 (24u/0.68u) and the hard one g1_cmp_regenpair4 (../).")

# ---------------------------------------------------------------- DAC -------
UW, UL = "4u", "1.2u"          # unit rppd ~95.5 Ohm (70e-6/w + 260*l/w); 530 units = 50.6 kOhm, 20.5 uA from the buffered VREF (1.04 V)
NUNIT = 530                    # 255 below tap0 (0.5 V), 255 between tap0 and tap255, 20 above (VREF = 1.04 V)
# The 1040-device DAC keeps the original placement grid (string rows of 40 units, level shifters on top,
# one row block per tree level); only the frame, the title block and group captions are added.
s = Sheet("g1_dac8")
prev = VSS
for i in range(NUNIT):
    # top of unit i is (i+1) units above ground: tap k = 255+k units -> unit index i = 254+k
    nxt = "vref" if i == NUNIT - 1 else ("t%d" % (i - 254) if 254 <= i <= 509 else "s%d" % i)
    s.res("RU%d" % i, 100 + 60 * (i % 40), -3000 + 80 * (i // 40), UW, UL, P=nxt, M=prev, body=RBODY)
    prev = nxt
# code level shifters: dh = 3.3 V copy of d, dhn its complement
for b in range(8):
    s.inst("XLU%d" % b, "g1_tlvlup.sym", 100 + 200 * b, -3250, {"a": "d%d" % b, "y": "dh%d" % b, "yb": "dhn%d" % b, VDD: VDD, "vdda": "vdda", VSS: VSS})
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
for i, p in enumerate(("vref",) + tuple("d%d" % b for b in range(8))):
    s.port(p, (3400, -3000 + 30 * i), "in")
s.port("out", (3400, -2700), "out")
for i, p in enumerate((VDD, "vdda", VSS)):
    s.port(p, (3400, -2640 + 30 * i), "inout")
s.frame(40, -3330, 1700, -3180, "8 code-bit level shifters: d_b (1.2 V) -> dh_b / dhn_b (3.3 V)")
s.frame(40, -3060, 2460, -1850, "resistor string: 530 x rppd 4u/1.2u from vref (top) to vss; taps t0..t255 = units 255..510")
s.frame(40, -1680, 3300, 1200, "binary tree of thick-oxide NMOS switches, level b (row block b) selected by dh_b / dhn_b")
s.text("out = VREF*(255+code)/530 ; code 0 -> 0.5004 V, 255 -> 1.0008 V at VREF=1.04 V; LSB 1.962 mV (VREF/530).\n"
       "Shunt-referred threshold = code x 0.1962 mV x (VREF/1.04 V) (gain 20, divider 1/2). With the BGR586 VREF 1.04546 V (simulated), code 200 = 39.45 mV.", 40, 1260)
s.title_block(40, -3700, "g1_dac8", "8-bit rppd string DAC from VREF with a 3.3 V-driven NMOS binary tree",
              ref("g1_dac8", "sim/netlist/g1_dac8.spice sha256 9f967559"), VARIANT, width=2400)
s.write("g1_dac8.sch")
DAC = ["vref"] + ["d%d" % b for b in range(8)] + ["out", VDD, "vdda", VSS]
write_symbol("g1_dac8.sym", "g1_dac8", DAC, {"vref": "in", "out": "out", "d0": "in", "d1": "in", "d2": "in", "d3": "in",
             "d4": "in", "d5": "in", "d6": "in", "d7": "in"}, label="8-bit string DAC")

# --------------------------------------------------------------- cond -------
RW, RL = "2u", "76.7u"   # 10 k unit shared with G1_SENSE
s = Sheet("g1_cond")
prev = "isense"
rs = []
for i in range(10):
    nxt = VSS if i == 9 else ("icmp" if i == 4 else "c%d" % i)
    rs.append(s.res("RC%d" % i, 300 + 130 * i, -300, RW, RL, P=prev, M=nxt, rot=3, body=RBODY))
    prev = nxt
ch = s.cap("CH", 1000, -180, "26u", "26u", c0="icmp", c1=VSS)
for i in range(9):
    s.wire(rs[i]["M"], rs[i + 1]["P"])
    if i != 4:
        s.slab(((rs[i]["M"][0] + rs[i + 1]["P"][0]) / 2, -300), "c%d" % i)
s.port("isense", (120, -300), "in"); s.wire((120, -300), rs[0]["P"])
s.wire((880, -300), (880, -400), (1600, -400)); s.port("icmp", (1600, -400), "out"); s.wlab((1000, -400), "icmp")
s.wire((880, -300), (880, -240), (1000, -240), ch["c0"])
s.wire(rs[9]["M"], (1640, -300), (1640, -100), (1000, -100), ch["c1"]); s.port(VSS, (120, -100), "inout", flip=1)
s.wire((120, -100), (1000, -100))
s.text("icmp = ISENSE / 2 (5 + 5 units of the 10 k SENSE unit rppd 2u/76.7u); CH 1 pF holds icmp against comparator kickback.\n"
       "ISENSE = 1.0 V pedestal + 20 x Vshunt (1.0 .. 2.0 V) -> icmp 0.5 .. 1.0 V, the DAC tap range.", 120, -20)
title(s, "g1_cond", "ISENSE conditioning: 2:1 divider + 1 pF hold", ref("g1_cond", "sim/netlist/g1_cond.spice sha256 ef8ed581"), -660, 1500)
s.write("g1_cond.sch")
COND = ["isense", "icmp", VSS]
write_symbol("g1_cond.sym", "g1_cond", COND, {"isense": "in", "icmp": "out"}, label="ISENSE / 2")

# ---------------------------------------------------------------- top -------
s = Sheet("g1_trip")
xcond = s.inst("XCOND", "g1_cond.sym", 300, -650, {"isense": "isense", "icmp": "icmp", VSS: VSS})
soft = {"vref": "vref", "out": "vth_soft", VDD: VDD, "vdda": "vdda", VSS: VSS}
hard = {"vref": "vref", "out": "vth_hard", VDD: VDD, "vdda": "vdda", VSS: VSS}
for b in range(8):
    soft["d%d" % b] = "soft%d" % b
    hard["d%d" % b] = "hard%d" % b
xdacs = s.inst("XDACS", "g1_dac8.sym", 700, -1000, soft)
xdach = s.inst("XDACH", "g1_dac8.sym", 700, -350, hard)
chs = s.cap("CHS", 870, -920, "26u", "26u", c0="vth_soft", c1=VSS)
chh = s.cap("CHH", 870, -270, "26u", "26u", c0="vth_hard", c1=VSS)
xclki = s.inst("XCLKI", "g1_inv.sym", 900, -120, {"a": "cmp_clk", "y": "cmp_clk_n", VDD: VDD, VSS: VSS})
xcs = s.inst("XCS", "g1_cmp.sym", 1150, -980, {"inp": "icmp", "inn": "vth_soft", "clk": "cmp_clk", "q": "cmp_soft", "qb": "cmp_soft_n", VDD: VDD, VSS: VSS})
xch = s.inst("XCH", "g1_cmp_regenpair4.sym" if CHIP else "g1_cmp.sym", 1150, -330, {"inp": "icmp", "inn": "vth_hard", "clk": "cmp_clk_n", "q": "cmp_hard", "qb": "cmp_hard_n", VDD: VDD, VSS: VSS})
for x in (xcond, xdacs, xdach, xclki, xcs, xch):
    s.supplies(x)
ins = ("isense", "vref", "cmp_clk") + tuple("soft%d" % b for b in range(8)) + tuple("hard%d" % b for b in range(8))
s.port("isense", (100, -650), "in"); s.wire((100, -650), xcond["isense"])
s.port("vref", (100, -1200), "in")
s.stub(xdacs["vref"], "vref", -40); s.stub(xdach["vref"], "vref", -40)
s.port("cmp_clk", (100, -120), "in"); s.wire((100, -120), xclki["a"])
for b in range(8):
    s.port("soft%d" % b, (100, xdacs["d%d" % b][1]), "in"); s.wire((100, xdacs["d%d" % b][1]), xdacs["d%d" % b])
for b in range(8):
    s.port("hard%d" % b, (100, xdach["d%d" % b][1]), "in"); s.wire((100, xdach["d%d" % b][1]), xdach["d%d" % b])
# thresholds with their hold capacitors, comparators
s.wire(xdacs["out"], (950, -1000), (950, xcs["inn"][1]), xcs["inn"]); s.wire((870, -1000), chs["c0"]); s.stub(chs["c1"], VSS, 0, 20)
s.wlab((940, -1000), "vth_soft")
s.wire(xdach["out"], (950, -350), (950, xch["inn"][1]), xch["inn"]); s.wire((870, -350), chh["c0"]); s.stub(chh["c1"], VSS, 0, 20)
s.wlab((940, -350), "vth_hard")
s.wire(xcond["icmp"], (1000, -650), (1000, xcs["inp"][1]), xcs["inp"]); s.wlab((600, -650), "icmp")
s.stub(xch["inp"], "icmp", -40)
s.wire(xclki["y"], (xch["clk"][0], -120), xch["clk"]); s.wlab((1100, -120), "cmp_clk_n")
s.wire(xcs["q"], (1400, xcs["q"][1])); s.stub(xcs["qb"], "cmp_soft_n", 40)
s.wire(xch["q"], (1400, xch["q"][1])); s.stub(xch["qb"], "cmp_hard_n", 40)
s.port("cmp_soft", (1400, xcs["q"][1]), "out"); s.port("cmp_hard", (1400, xch["q"][1]), "out")
s.port(VDD, (100, -60), "inout"); s.port("vdda", (100, -35), "inout"); s.port(VSS, (100, -10), "inout")
s.text("vref = buffered VREF from G1_SENSE (vref_buf). cmp_x = 1 while ISENSE/2 > VREF*(255+code)/530, i.e. shunt voltage > code x 0.1962 mV x (VREF/1.04 V).\n"
       "Soft comparator strobes on the rising edge of cmp_clk (osc_clk/2, about 4.7 MHz with the 9.44 MHz chip clock, simulated), hard on the falling edge.\n"
       "Chip (regenpair4 + NF4, simulated block bench): hard path trips 40-56 LSB below its code, soft within 1 LSB (sim/postlayout/README.md).", 100, 60)
title(s, "g1_trip", "shunt-current trip: ISENSE/2 against two 8-bit VREF string DACs, soft + hard StrongARM comparators",
      (DECK + " (chip deck)") if CHIP else "sim/netlist/g1_trip.spice sha256 6f265319", -1500, 2000)
s.write("g1_trip.sch")
TRIP = list(ins) + ["cmp_soft", "cmp_hard", VDD, "vdda", VSS]
write_symbol("g1_trip.sym", "g1_trip", TRIP, dict([(p, "in") for p in ins] + [("cmp_soft", "out"), ("cmp_hard", "out")]))
print("wrote g1_trip cells (%s)" % TRIP_VARIANT)
