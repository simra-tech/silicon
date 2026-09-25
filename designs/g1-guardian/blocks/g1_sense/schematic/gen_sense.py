"""Generate the G1_SENSE schematics (xschem) : g1_ota (3.3 V PMOS-input folded cascode)
and g1_sense (difference amplifier, gain 20, VREF-derived pedestal, pedestal buffer, VREF buffer).
Revision B (2026-09-18 evening): VREF = 1.04 V and IPTAT = 4.13 uA from G1_BGR; pedestal 51/53 VREF.

Run:  python3 gen_sense.py        (then netlist with netlist.sh)

Sizing origin: IHP TO_Nov2024/BG OTA3C (recycling folded cascode, PMOS input,
sg13_hv_*). Kept: PMOS input pair at L=2u (width doubled to 96u for offset), hv devices at L=1u, cascoded output.
Changed (see README): the recycling NMOS diode mirrors are replaced by plain
current sources with a wide-swing (Sooch) cascode bias, because a diode node
at Vgs_n ~0.8 V would put the input pair in triode at the -0.1..+0.3 V input
common mode; bias current raised for >= 2 MHz closed-loop bandwidth at gain 20.
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

# Readable sheets (2026-09-25): signal flow left to right, supplies on rails, bodies tied to
# sources along the symbol (small b:<net> tag otherwise), resistor strings drawn as series
# columns.  Device attributes, instance order and port order are those of the original
# label-per-pin generator, so the xschem netlists are unchanged
# (designs/g1-guardian/review/schematics-readability-20260925).
VARIANT_OTA = ("chip cells XBUF/XREF use g1_ota (this sheet); the chip's main amplifier XOTA is "
               "g1_ota_main_candidate (comp45 + R100: M1/M2 w=384u, RRZ rppd 1u/100u, CC 45u x 23u), not drawn here")
VARIANT_SENSE = ("comp45 + R100 on the chip (XOTA = g1_ota_main_candidate); this sheet is revision B with XOTA = g1_ota. "
                 "Chip netlist of the block: native-reference CDL 696b43fd, layout 450a4906")

# ---------------------------------------------------------------- OTA ------
VDD, VSS = "vdd", "vss"
OTA_PINS = ["inp", "inn", "vbn", "out", VDD, VSS]
# device sizes (w, l, ng) of the revision-B OTA; the comp45 + R100 main amplifier overrides some of them
BASE = {"M1": ("96u", "2u", 16), "M2": ("96u", "2u", 16), "M3": ("80u", "1u", 10), "M4": ("80u", "1u", 10),
        "M14": ("96u", "1u", 12), "M11": ("96u", "1u", 12), "M15": ("96u", "1u", 12), "M12": ("96u", "1u", 12),
        "RZ": ("1u", "6.2u"), "CC": ("23u", "23u")}


def ota_sheet(cell="g1_ota", sizes=None, what="3.3 V PMOS-input folded-cascode OTA + CS output stage (SENSE buffers)",
              ref="sim/netlist/g1_ota.spice sha256 7f68bf0f", variant=None, out_dir=".", text_extra=""):
    z = dict(BASE)
    z.update(sizes or {})
    s = Sheet(cell)
    # bias generator column (the 10 uA reference diode MBI lives in g1_sense and drives vbn)
    mb2 = s.mos("MB2", "sg13_hv_nmos", 200, -190, "8u", "1u", D="vbp", G="vbn", S=VSS, B=VSS, ng=2)
    mb3 = s.mos("MB3", "sg13_hv_pmos", 200, -700, "16u", "1u", D="vbp", G="vbp", S=VDD, B=VDD, ng=4)
    mb5 = s.mos("MB5", "sg13_hv_pmos", 400, -700, "16u", "1u", D="vbnc", G="vbp", S=VDD, B=VDD, ng=4)
    mb4 = s.mos("MB4", "sg13_hv_nmos", 400, -190, "1.6u", "1u", D="vbnc", G="vbnc", S=VSS, B=VSS, ng=1)      # Sooch W/5 -> nmos cascode gate
    mb6 = s.mos("MB6", "sg13_hv_nmos", 600, -190, "8u", "1u", D="vbpc", G="vbn", S=VSS, B=VSS, ng=2)
    mb7 = s.mos("MB7", "sg13_hv_pmos", 600, -700, "3.2u", "1u", D="vbpc", G="vbpc", S=VDD, B=VDD, ng=1)     # Sooch W/5 -> pmos cascode gate
    # core
    mt = s.mos("MT", "sg13_hv_pmos", 1300, -700, "128u", "1u", D="tail", G="vbp", S=VDD, B=VDD, ng=16)       # 80 uA tail
    m1 = s.mos("M1", "sg13_hv_pmos", 1200, -520, z["M1"][0], z["M1"][1], D="fn", G="inn", S="tail", B=VDD, ng=z["M1"][2])        # inn -> mirror side (stage 2 inverts)
    m2 = s.mos("M2", "sg13_hv_pmos", 1440, -520, z["M2"][0], z["M2"][1], D="fp", G="inp", S="tail", B=VDD, ng=z["M2"][2], flip=1)
    m3 = s.mos("M3", "sg13_hv_nmos", 1000, -190, z["M3"][0], z["M3"][1], D="fn", G="vbn", S=VSS, B=VSS, ng=z["M3"][2])        # 100 uA sources
    m4 = s.mos("M4", "sg13_hv_nmos", 1640, -190, z["M4"][0], z["M4"][1], D="fp", G="vbn", S=VSS, B=VSS, ng=z["M4"][2], flip=1)
    m13 = s.mos("M13", "sg13_hv_nmos", 1000, -330, "48u", "1u", D="mir", G="vbnc", S="fn", B=VSS, ng=6)       # nmos cascodes (60 uA)
    m16 = s.mos("M16", "sg13_hv_nmos", 1640, -330, "48u", "1u", D="out1", G="vbnc", S="fp", B=VSS, ng=6, flip=1)
    m14 = s.mos("M14", "sg13_hv_pmos", 1000, -700, z["M14"][0], z["M14"][1], D="pc1", G="mir", S=VDD, B=VDD, ng=z["M14"][2])        # pmos sources 60 uA, mirror gate = mir
    m11 = s.mos("M11", "sg13_hv_pmos", 1640, -700, z["M11"][0], z["M11"][1], D="pc2", G="mir", S=VDD, B=VDD, ng=z["M11"][2], flip=1)
    m15 = s.mos("M15", "sg13_hv_pmos", 1000, -590, z["M15"][0], z["M15"][1], D="mir", G="vbpc", S="pc1", B=VDD, ng=z["M15"][2])     # pmos cascodes
    m12 = s.mos("M12", "sg13_hv_pmos", 1640, -590, z["M12"][0], z["M12"][1], D="out1", G="vbpc", S="pc2", B=VDD, ng=z["M12"][2], flip=1)
    # second stage: PMOS common source, 120 uA NMOS load, Miller Cc 0.8 pF with nulling resistor 1.7 kOhm
    m20 = s.mos("M20", "sg13_hv_pmos", 1900, -700, "192u", "1u", D="out", G="out1", S=VDD, B=VDD, ng=24)
    m21 = s.mos("M21", "sg13_hv_nmos", 1900, -190, "96u", "1u", D="out", G="vbn", S=VSS, B=VSS, ng=12)
    rz = s.res("RZ", 1700, -440, z["RZ"][0], z["RZ"][1], P="out1", M="cz", body="vss", rot=3)
    cc = s.cap("CC", 1800, -440, z["CC"][0], z["CC"][1], c0="cz", c1="out", rot=3)
    s.body(mb2, mb3, mb5, mb4, mb6, mb7, mt, m1, m2, m3, m4, m13, m16, m14, m11, m15, m12, m20, m21)
    # bias: Sooch wide-swing cascode bias from vbn
    s.wire(mb3["D"], mb2["D"]); s.wire(mb3["G"], (180, -650), (220, -650))
    s.wire((220, -650), (300, -650), (300, -700), mb5["G"]); s.wlab((300, -650), "vbp")
    s.wire(mb5["D"], mb4["D"]); s.wire(mb4["G"], (380, -250), (420, -250)); s.lab((420, -450), "vbnc", "r")
    s.wire(mb7["D"], mb6["D"]); s.wire(mb7["G"], (580, -650), (620, -650)); s.lab((620, -450), "vbpc", "r")
    s.stub(mb6["G"], "vbn", -30)
    # input pair and tail
    s.stub(mt["G"], "vbp", -30)
    s.wire(mt["D"], (1320, -610)); s.wire((1220, -610), (1420, -610)); s.wire((1220, -610), m1["S"]); s.wire((1420, -610), m2["S"])
    s.wlab((1300, -610), "tail")
    s.wire(m1["D"], (1220, -260), (1020, -260)); s.wire(m2["D"], (1420, -260), (1620, -260))
    # folded cascode branches
    s.wire(m14["D"], m15["S"]); s.lab((1020, -645), "pc1", "r")
    s.wire(m15["D"], m13["D"]); s.wire(m13["S"], m3["D"]); s.lab((1020, -240), "fn", "l")
    s.wire(m11["D"], m12["S"]); s.lab((1620, -645), "pc2", "l")
    s.wire(m12["D"], m16["D"]); s.wire(m16["S"], m4["D"]); s.lab((1620, -240), "fp", "r")
    s.wire(m14["G"], (900, -700), (900, -460), (1020, -460)); s.lab((1020, -420), "mir", "r")
    s.stub(m11["G"], "mir", 30)
    s.lab(m15["G"], "vbpc", "l"); s.stub(m12["G"], "vbpc", 30)
    s.stub(m13["G"], "vbnc", -30); s.stub(m16["G"], "vbnc", 30)
    s.stub(m3["G"], "vbn", -30); s.stub(m4["G"], "vbn", 30)
    # output stage and Miller compensation
    s.wire((1620, -500), (1800, -500), (1800, -700), m20["G"]); s.wlab((1780, -500), "out1")
    s.wire((1640, -500), (1640, -440), rz["P"]); s.wire(rz["M"], cc["c0"]); s.slab((1750, -440), "cz")
    s.wire(m20["D"], m21["D"]); s.wire(cc["c1"], (1920, -440))
    s.stub(m21["G"], "vbn", -30)
    # ports (original order) and rails
    s.port("inp", (1520, -520), "in", flip=1); s.wire(m2["G"], (1520, -520))
    s.port("inn", (1120, -520), "in"); s.wire((1120, -520), m1["G"])
    s.port("vbn", (100, -190), "in"); s.wire((100, -190), mb2["G"])
    s.port("out", (2060, -440), "out"); s.wire((1920, -440), (2060, -440))
    top = [mb3, mb5, mb7, mt, m14, m11, m20]
    for d in top:
        s.wire(d["S"], (d["S"][0], -790))
    s.wire((100, -790), (1920, -790)); s.port(VDD, (100, -790), "inout", flip=1)
    bot = [mb2, mb4, mb6, m3, m4, m21]
    for d in bot:
        s.wire(d["S"], (d["S"][0], -100))
    s.wire((100, -100), (1920, -100)); s.port(VSS, (100, -100), "inout", flip=1)
    s.frame(130, -770, 700, -120, "bias: Sooch wide-swing cascode (vbp, vbnc, vbpc from vbn)")
    s.frame(1130, -760, 1540, -400, "PMOS input pair + tail")
    s.frame(1680, -770, 2000, -120, "CS output stage + Miller RZ/CC")
    s.text(text_extra + "Folded cascode: left branch M14/M15/M13/M3 (mirror side, node mir), right branch M11/M12/M16/M4 (node out1).\n"
           "Design currents (generator, vbn from an 8u/1u diode at 10 uA equivalent): tail 80 uA, PMOS sources 60 uA, NMOS sources 100 uA,\n"
           "stage 2 120 uA class A; Cc 0.8 pF, Rz 1.7 kOhm.  inn on M1 (mirror side), inp on M2: out rises when inp rises.\n"
           "Bodies: wire to source where equal; b:<net> tag where the body is a rail but not the source.", 130, -40)
    s.title_block(130, -1060, cell, what, ref, variant or VARIANT_OTA, width=1800)
    s.write(os.path.join(out_dir, cell + ".sch"))
    write_symbol(os.path.join(out_dir, cell + ".sym"), cell, OTA_PINS, {"inp": "in", "inn": "in", "vbn": "in", "out": "out"},
                 shape="amp", left=["inn", "inp"], right=["out"], top=[VDD], bottom=["vbn", VSS])

# ------------------------------------------------------------- SENSE -------
# unit resistor 10 kOhm: rppd w=2u l=76.7u (R = 70e-6/w + 260*l/w -> 35 + 130*76.7 = 10.0 k)
RW, RL = "2u", "76.7u"
ROWS, DX, DY = 10, 170, 80


def chain(sch, prefix, x, y, n, a, b):
    """n series unit resistors from net a to net b in columns of ROWS (down, then up, ...).
    Returns the a-end and b-end points."""
    prev = a
    ends = []
    for i in range(n):
        col, row = divmod(i, ROWS)
        nxt = b if i == n - 1 else "%s_%d" % (prefix, i)
        xx = x + DX * col
        if col % 2 == 0:
            r = sch.res("%s%d" % (prefix, i), xx, y + DY * row, RW, RL, P=prev, M=nxt, body="vss")
        else:
            r = sch.res("%s%d" % (prefix, i), xx, y + DY * (ROWS - 1 - row), RW, RL, P=prev, M=nxt, body="vss", rot=2, flip=1)
        ends.append(r)
        prev = nxt
    for i in range(n - 1):
        m, p = ends[i]["M"], ends[i + 1]["P"]
        net = ends[i].pins["M"][1]
        if m[0] == p[0]:
            sch.wire(m, p); sch.slab((m[0], (m[1] + p[1]) / 2), net)
        else:
            yy = m[1] + (20 if (i // ROWS) % 2 == 0 else -20)
            sch.wire(m, (m[0], yy), (p[0], yy), p); sch.slab(((m[0] + p[0]) / 2, yy), net)
    return ends[0]["P"], ends[-1]["M"]


def unit(sch, name, x, y, a, b):
    """One unit resistor drawn horizontally (P left)."""
    return sch.res(name, x, y, RW, RL, P=a, M=b, body="vss", rot=3)




def sense_sheet(xota_cell="g1_ota", ref="sim/netlist/g1_sense.spice sha256 8880157b", variant=VARIANT_SENSE, out_dir="."):
    """Top sheet; XOTA uses the symbol xota_cell (g1_ota, or g1_ota_main_candidate for comp45 + R100)."""
    here = os.getcwd()
    os.chdir(out_dir)                       # symbols are read from the output directory
    t = Sheet("g1_sense")
    r1n = unit(t, "R1N0", 400, -1310, "sense_n", "vn")                  # R1 on inverting side
    r2n = chain(t, "R2N", 900, -2150, 20, "vn", "isense")               # R2 feedback, 20 units
    r1p = unit(t, "R1P0", 400, -1100, "sense_p", "vp")                  # R1 non-inverting side
    r2p = chain(t, "R2P", 560, -1000, 20, "vp", "vped")                 # R2 to pedestal
    rd1 = chain(t, "RD1", 1700, -560, 2, "vref_buf", "vped_ref")         # pedestal divider from the buffered VREF: 2 units up, 51 down
    rd2 = chain(t, "RD2", 1900, -560, 51, "vped_ref", VSS)
    # bias diode: G1_BGR iptat (4.13 uA at 27 C, PTAT) into a 3.3u/1u hv nmos diode = same density as the 8u/10uA design point
    mbi = t.mos("MBI", "sg13_hv_nmos", 300, -300, "3.3u", "1u", D="iptat", G="iptat", S=VSS, B=VSS, ng=1)
    # main OTA, pedestal buffer, VREF buffer (the bandgap output is unbuffered, ~88 kOhm)
    xota = t.inst("XOTA", xota_cell + ".sym", 1400, -1300, {"inp": "vp", "inn": "vn", "vbn": "iptat", "out": "isense", VDD: VDD, VSS: VSS})
    xbuf = t.inst("XBUF", "g1_ota.sym", 1300, -850, {"inp": "vped_ref", "inn": "vped", "vbn": "iptat", "out": "vped", VDD: VDD, VSS: VSS})
    xref = t.inst("XREF", "g1_ota.sym", 1300, -500, {"inp": "vref", "inn": "vref_buf", "vbn": "iptat", "out": "vref_buf", VDD: VDD, VSS: VSS})
    t.body(mbi)
    for x in (xota, xbuf, xref):
        t.supplies(x)
    # difference amplifier: ISENSE = VPED + 20 (SENSE_P - SENSE_N)
    t.port("sense_p", (100, -1100), "in"); t.wire((100, -1100), r1p["P"])
    t.port("sense_n", (100, -1310), "in"); t.wire((100, -1310), r1n["P"])
    t.wire(r1n["M"], xota["inn"]); t.wlab((600, -1310), "vn")
    t.wire((700, -1310), (700, -2220), (900, -2220), r2n[0])
    t.wire(r1p["M"], (1200, -1100), (1200, xota["inp"][1]), xota["inp"]); t.wlab((520, -1100), "vp")
    t.wire((560, -1100), r2p[0])
    t.wire(r2n[1], (r2n[1][0], -2220), (1600, -2220), (1600, -1300))
    t.wire(xota["out"], (1800, -1300)); t.wlab((1760, -1300), "isense")
    t.wire(r2p[1], (r2p[1][0], -1060), (1000, -1060)); t.wlab((1000, -1060), "vped")
    # reference buffer, pedestal divider and pedestal buffer
    t.port("vref", (1000, -490), "in"); t.wire((1000, -490), xref["inp"])
    t.wire(xref["out"], (1420, -500), (1420, -600), (1210, -600), (1210, -510), xref["inn"])
    t.wire((1420, -500), (1600, -500)); t.wlab((1560, -500), "vref_buf"); t.wire((1500, -500), (1500, -380))
    t.wire((1600, -500), (1600, -620), (1700, -620), rd1[0])
    t.wire(rd1[1], (1700, -420), (1850, -420), (1850, -620), (1900, -620), rd2[0]); t.wlab((1840, -420), "vped_ref")
    t.stub(rd2[1], VSS, 0, 20)
    t.stub(xbuf["inp"], "vped_ref", -40)
    t.wire(xbuf["out"], (1420, -850), (1420, -950), (1210, -950), (1210, -860), xbuf["inn"])
    t.wire((1420, -850), (1560, -850)); t.wlab((1560, -850), "vped")
    t.port("iptat", (100, -360), "in"); t.wire((100, -360), (320, -360), mbi["D"]); t.wire(mbi["G"], (280, -360))
    t.stub(mbi["S"], VSS, 0, 20)
    t.port("isense", (1900, -1300), "out"); t.wire((1800, -1300), (1900, -1300))
    t.port("vped", (1900, -850), "out"); t.wire((1560, -850), (1900, -850))
    t.port("vref_buf", (1500, -380), "out")
    t.port(VDD, (100, -200), "inout"); t.port(VSS, (100, -170), "inout")
    t.text("iptat: 4.13 uA PTAT from G1_BGR into MBI; the three OTAs run at about 350 uA each (PTAT).", 100, 40)
    t.title_block(100, -2560, "g1_sense", "low-side shunt amplifier: gain 20 difference amplifier + VREF-derived 1.0 V pedestal",
                  ref, variant, width=1900)
    t.write(os.path.join(".", "g1_sense.sch"))
    SENSE_PINS = ["sense_p", "sense_n", "vref", "iptat", "isense", "vped", "vref_buf", VDD, VSS]
    write_symbol(os.path.join(".", "g1_sense.sym"), "g1_sense", SENSE_PINS, dict([(p, "in") for p in SENSE_PINS[:4]] + [(p, "out") for p in SENSE_PINS[4:7]]))
    os.chdir(here)


if __name__ == "__main__":
    ota_sheet()
    sense_sheet()
    print("wrote g1_ota.sch/.sym g1_sense.sch/.sym")
