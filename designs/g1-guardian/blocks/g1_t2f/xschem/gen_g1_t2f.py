"""Generate g1_t2f.sch / g1_t2f.sym: temperature-to-frequency converter, revision 2.

I_PTAT (PMOS legs on the bandgap's pbias/pcasc rails) alternately charges two cmim
capacitors; two HBT-input comparators against a threshold and a NAND RS latch steer
the current (en=0 holds the latch in q=0 and both capacitors discharged). mode=0: threshold = VREF (f proportional to I_PTAT / VREF, PTAT).
mode=1: threshold = I_PTAT * R_REF (f = 1 / (2 R_REF C), temperature independent to
first order; the ratio of the two readings cancels C, threshold and comparator delay).

Revision 2 (2026-09-19): collector cascodes in the comparators. Revision 1 ran the comparator
HBTs at V_CE = 2.2 V (diode side, on) and up to 3.3 V (mirror side, off) against the 1.6 V vce_max
of the npn13G2 model card; the avalanche base current of the on-side HBT loaded the threshold node
and gave -9.3 C/V supply sensitivity. Now every HBT collector is the source of an HV NMOS common-gate
device (MCA/MCB) whose gate rail vcg = vth + |V_GS| comes from a PMOS source follower (MSF, body
tied to source, own n-well) on the threshold node, biased by one more I_PTAT mirror leg (MPF). The
collector therefore sits at vth + (|V_GS,MSF| - V_GS,MC), i.e. V_CE = V_BE + about 0.3 V in both
modes and at every temperature; the follower gate loads vth only capacitively. Small NMOS bleeders
(MBA/MBB, gates on nbias, about 0.2 uA) keep each cascode conducting while its HBT is off, so the
off-state collector cannot float above vcg - V_GS(0.2 uA); they cancel at the mirror load (both
sides carry the same extra current). MPF has no pcasc cascode: at 3.0 V and 175 C in REF mode
(vth = 2 I_PTAT R_REF = 1.54 V, vcg = 2.45 V) there is only 0.55 V of headroom, and the follower's
current only sets |V_GS,MSF|.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "g1_bgr", "xschem"))
from schgen import write_sch, write_sym

HVP, HVN = "sg13g2_pr/sg13_hv_pmos.sym", "sg13g2_pr/sg13_hv_nmos.sym"
LVP, LVN = "sg13g2_pr/sg13_lv_pmos.sym", "sg13g2_pr/sg13_lv_nmos.sym"
NPN, RPPD, CMIM = "sg13g2_pr/npn13G2.sym", "sg13g2_pr/rppd.sym", "sg13g2_pr/cap_cmim.sym"

def mos(sym, model, name, d, g, s, b, w, l, m=1):
    return (sym, name, {"D": d, "G": g, "S": s, "B": b}, dict(w=w, l=l, ng=1, m=m, mm_ok=1, model=model, spiceprefix="X"))
def hp(name, d, g, s, w="2u", l="0.5u", m=1, b="vdd"): return mos(HVP, "sg13_hv_pmos", name, d, g, s, b, w, l, m)
def hn(name, d, g, s, w="1u", l="0.5u", m=1): return mos(HVN, "sg13_hv_nmos", name, d, g, s, "vss", w, l, m)
def lp(name, d, g, s, w, l): return mos(LVP, "sg13_lv_pmos", name, d, g, s, "vdd12", w, l)
def ln(name, d, g, s, w, l): return mos(LVN, "sg13_lv_nmos", name, d, g, s, "vss", w, l)
def q(name, c, b, e):
    return (NPN, name, {"C": c, "B": b, "E": e, "S": "vss"}, dict(model="npn13G2", spiceprefix="X", Nx=1, mm_ok=1))
def r(name, p, m, w, l):
    return (RPPD, name, {"P": p, "M": m}, dict(w=w, l=l, model="rppd", body="sub!", spiceprefix="X", b=0, m=1, mm_ok=1))
def cap(name, a, b, w, l):
    return (CMIM, name, {"c0": a, "c1": b}, dict(model="cap_cmim", w=w, l=l, m=1, mm_ok=1, spiceprefix="X"))
def inv(name, out, inp, wn="1u", wp="2u", l="0.5u"):
    return [hn(name + "N", out, inp, "vss", wn, l), hp(name + "P", out, inp, "vdd", wp, l)]
def nand2(name, out, a, b):
    return [hp(name + "PA", out, a, "vdd"), hp(name + "PB", out, b, "vdd"),
            hn(name + "NA", out, a, name + "_i", "2u"), hn(name + "NB", name + "_i", b, "vss", "2u")]
def nand3(name, out, a, b, c):
    return [hp(name + "PA", out, a, "vdd"), hp(name + "PB", out, b, "vdd"), hp(name + "PC", out, c, "vdd"),
            hn(name + "NA", out, a, name + "_i", "3u"), hn(name + "NB", name + "_i", b, name + "_j", "3u"), hn(name + "NC", name + "_j", c, "vss", "3u")]

# revision 2 sizes (environment overrides are for the sizing sweeps in build/, not for the frozen file)
CASC_W, CASC_L = os.environ.get("T2F_CASC_W", "4u"), os.environ.get("T2F_CASC_L", "1u")      # MCA/MCB collector cascodes
BLEED_W, BLEED_L = os.environ.get("T2F_BLEED_W", "0.5u"), os.environ.get("T2F_BLEED_L", "2u")  # MBA/MBB bleeders on nbias (~0.25 uA)
SF_W, SF_L = os.environ.get("T2F_SF_W", "2u"), os.environ.get("T2F_SF_L", "2u")               # MSF source follower

def comparator(k, cap_net, out_sn):
    # HBT differential pair on an 8 uA PTAT tail (constant gm, nearly constant delay); HV NMOS collector
    # cascodes MCA/MCB (gate rail vcg = vth + |V_GS,MSF|) hold both collectors at vth + ~0.3 V; NMOS bleeders
    # MBA/MBB (nbias, ~0.2 uA) keep the off-side cascode conducting; PMOS mirror load MLA/MLB above the
    # cascodes; the single-ended output ob drives two HV inverters. out_sn is low while cap > vth.
    return [q(f"QA{k}", f"ca{k}", "vth", f"tail{k}"), q(f"QB{k}", f"cb{k}", cap_net, f"tail{k}"),
            hn(f"MCA{k}", f"oa{k}", "vcg", f"ca{k}", CASC_W, CASC_L), hn(f"MCB{k}", f"ob{k}", "vcg", f"cb{k}", CASC_W, CASC_L),
            hn(f"MBA{k}", f"ca{k}", "nbias", "vss", BLEED_W, BLEED_L), hn(f"MBB{k}", f"cb{k}", "nbias", "vss", BLEED_W, BLEED_L),
            hp(f"MLA{k}", f"oa{k}", f"oa{k}", "vdd", "4u", "1u"), hp(f"MLB{k}", f"ob{k}", f"oa{k}", "vdd", "4u", "1u"),
            hn(f"MT{k}", f"tail{k}", "nbias", "vss", "20u", "2u")] + \
           inv(f"IC{k}A", f"c{k}", f"ob{k}") + inv(f"IC{k}B", out_sn, f"c{k}", "2u", "4u")

C_WL = "28u"          # 2 x 1.18 pF cmim: t_half = C * VREF / I_PTAT ~ 300 ns at 27 C
RREF_N, RREF_UNIT = 10, "24.5u"   # R_REF = 10 x rppd 0.5/24.5 in series (126 kOhm plus the 20 heads); one unit per layout PCell,
                                  # so LVS compares the serpentine one-to-one (--no_series_res). V_R = 2 I_PTAT R_REF ~ VREF at 27 C.
def rref():
    nodes = ["vr"] + [f"vr_{i}" for i in range(1, RREF_N)] + ["vss"]
    return [r(f"RREF{i + 1}", nodes[i], nodes[i + 1], "0.5u", RREF_UNIT) for i in range(RREF_N)]

inst = [
    # PTAT current legs on the bandgap mirror rails
    hp("MPO", "do", "pbias", "vdd", "10u", "4u"), hp("MCO", "isrc", "pcasc", "do", "10u", "4u", b="do"),
    hp("MPR", "dr", "pbias", "vdd", "10u", "4u", 2), hp("MCR", "vr", "pcasc", "dr", "10u", "4u", 2, b="dr"),
] + rref() + [
    hp("MPB", "db", "pbias", "vdd", "10u", "4u"), hp("MCB", "nbias", "pcasc", "db", "10u", "4u", b="db"),
    hn("MNB", "nbias", "nbias", "vss", "10u", "2u"),
    # cascode gate rail: I_PTAT (MPF, no cascode: headroom) into the PMOS source follower MSF on vth
    hp("MPF", "vcg", "pbias", "vdd", "10u", "4u"),
    hp("MSF", "vss", "vth", "vcg", SF_W, SF_L, b="vcg"),
    # threshold select: mode=0 -> VREF, mode=1 -> I_PTAT * R_REF
    hn("MX1", "vref", "moden", "vth", "4u"), hn("MX2", "vr", "mode", "vth", "4u"),
] + inv("IM", "moden", "mode") + comparator(1, "cap1", "sn") + comparator(2, "cap2", "rn") + \
    nand2("NQ", "q", "sn", "qn") + nand3("NQN", "qn", "rn", "q", "en") + \
    nand2("ND1", "d1g", "qn", "en") + nand2("ND2", "d2g", "q", "en") + [
    # current steering and discharge
    hp("SW1", "cap1", "d1g", "isrc", "4u"), hn("D1", "cap1", "d1g", "vss", "4u"),
    hp("SW2", "cap2", "d2g", "isrc", "4u"), hn("D2", "cap2", "d2g", "vss", "4u"),
    cap("C1", "cap1", "vss", C_WL, C_WL), cap("C2", "cap2", "vss", C_WL, C_WL),
] + inv("IA", "a", "d2g") + [
    # 3.3 V -> 1.2 V level shift (HV NMOS pull-downs, cross-coupled LV PMOS) and output buffer
    hn("MLSA", "lsa", "a", "vss", "2u"), hn("MLSB", "lsb", "d2g", "vss", "2u"),
    lp("MLPA", "lsa", "lsb", "vdd12", "0.5u", "0.3u"), lp("MLPB", "lsb", "lsa", "vdd12", "0.5u", "0.3u"),
    ln("IO1N", "fon", "lsb", "vss", "0.5u", "0.13u"), lp("IO1P", "fon", "lsb", "vdd12", "1u", "0.13u"),
    ln("IO2N", "fout", "fon", "vss", "1u", "0.13u"), lp("IO2P", "fout", "fon", "vdd12", "2u", "0.13u"),
]
ports = [("vdd", "inout"), ("vdd12", "inout"), ("vss", "inout"), ("pbias", "in"), ("pcasc", "in"),
         ("vref", "in"), ("en", "in"), ("mode", "in"), ("fout", "out")]
here = os.path.dirname(os.path.abspath(__file__))
out_dir = os.environ.get("T2F_OUT_DIR", here)


# ------------------------------------------------------------------ drawing --
# Readable sheet (2026-09-25): the device list above (order, names, nets, parameters) is unchanged;
# only placement, wires and labels are new, so the xschem netlist is unchanged (proof in
# designs/g1-guardian/review/schematics-readability-20260925).  Signal flow left to right:
# PTAT legs and threshold select | current steering and timing capacitors | two HBT comparators |
# NAND RS latch | 3.3 V -> 1.2 V level shift and output buffer.
def _find_flow():
    d = here
    while not os.path.isdir(os.path.join(d, "flow", "schematic")):
        if os.path.dirname(d) == d:
            raise SystemExit("flow/schematic not found above " + here)
        d = os.path.dirname(d)
    return os.path.join(d, "flow", "schematic")


sys.path.insert(0, _find_flow())
from xsch_readable import Sheet  # noqa: E402

POS = {}


def at(name, x, y, rot=0, flip=0):
    POS[name] = (x, y, rot, flip)


def inv_at(name, x, y):                       # P above N, both unflipped
    at(name + "P", x, y - 120); at(name + "N", x, y)


def nand_at(name, n, x, y):                   # parallel PMOS row, series NMOS stack
    for i, k in enumerate("ABC"[:n]):
        at(name + "P" + k, x + 160 * i, y - 170)
        at(name + "N" + k, x, y + 110 * i)


# PTAT legs, threshold rail and select
at("MPO", 200, -800); at("MCO", 200, -690)
at("MPR", 400, -800); at("MCR", 400, -690)
for i in range(RREF_N):
    at("RREF%d" % (i + 1), 420, -580 + 80 * i)
at("MPB", 600, -800); at("MCB", 600, -690); at("MNB", 600, -380)
at("MPF", 800, -800); at("MSF", 800, -620)
at("MX1", 1000, -620); at("MX2", 1160, -620)
inv_at("IM", 1080, -300)
# comparators
CX = 1800
for k, cy in ((1, -420), (2, 200)):
    at("QA%d" % k, CX, cy); at("QB%d" % k, CX + 240, cy, flip=1)
    at("MCA%d" % k, CX + 40, cy - 120, flip=1); at("MCB%d" % k, CX + 200, cy - 120)
    at("MBA%d" % k, CX - 80, cy - 40); at("MBB%d" % k, CX + 300, cy - 40, flip=1)
    at("MLA%d" % k, CX + 40, cy - 240, flip=1); at("MLB%d" % k, CX + 200, cy - 240)
    at("MT%d" % k, CX + 100, cy + 120)
    inv_at("IC%dA" % k, CX + 420, cy - 100); inv_at("IC%dB" % k, CX + 600, cy - 100)
# latch
nand_at("NQ", 2, 2900, -500); nand_at("NQN", 3, 2900, 40)
nand_at("ND1", 2, 3500, -500); nand_at("ND2", 2, 3500, 40)
# steering switches and timing capacitors
at("SW1", 1400, -480); at("D1", 1400, -360); at("C1", 1540, -390)
at("SW2", 1400, 140); at("D2", 1400, 260); at("C2", 1540, 230)
# output: 3.3 V inverter, level shifter, 1.2 V buffer
inv_at("IA", 4000, -380)
at("MLSA", 4200, -380); at("MLSB", 4400, -380); at("MLPA", 4200, -510); at("MLPB", 4400, -510)
at("IO1P", 4600, -500); at("IO1N", 4600, -380); at("IO2P", 4780, -500); at("IO2N", 4780, -380)

from schgen import PINS  # noqa: E402
sch = Sheet("g1_t2f")
I = {}
for sym, name, pins, params in inst:
    x, y, rot, flip = POS[name]
    attrs = "name=%s %s" % (name, " ".join("%s=%s" % kv for kv in params.items()))
    I[name] = sch.place(sym, PINS[sym], name, x, y, attrs, pins, rot, flip)
W, L, SL, ST = sch.wire, sch.lab, sch.slab, sch.stub


def up(pt, net):
    ST(pt, net, 0, -20, "l")


def dn(pt, net):
    ST(pt, net, 0, 20, "l")


sch.body(*[d for n, d in I.items() if not n.startswith("Q") and "B" in d.pins and n[0] != "R" and n[0] != "C"])
# PTAT current legs: pbias mirror + pcasc cascode (cascode bodies on their own sources)
for m, c in (("MPO", "MCO"), ("MPR", "MCR"), ("MPB", "MCB")):
    W(I[m]["D"], I[c]["S"]); up(I[m]["S"], "vdd")
W(I["MPO"]["G"], (160, -800), (160, -840), (780, -840), (780, -800), I["MPF"]["G"])
for m in ("MPR", "MPB"):
    W(I[m]["G"], (I[m]["G"][0], -840))
L((160, -840), "pbias", "l")
W(I["MCO"]["G"], (170, -690), (170, -650), (560, -650), (580, -650)); W((580, -650), (580, -690), I["MCB"]["G"])
W(I["MCR"]["G"], (380, -650)); L((170, -650), "pcasc", "l")
W(I["MCO"]["D"], (220, -600)); L((220, -600), "isrc", "l")
W(I["MCR"]["D"], I["RREF1"]["P"]); L((420, -625), "vr", "r")
for i in range(1, RREF_N):
    a, b = I["RREF%d" % i]["M"], I["RREF%d" % (i + 1)]["P"]
    W(a, b); SL((a[0], (a[1] + b[1]) / 2), "vr_%d" % i)
dn(I["RREF%d" % RREF_N]["M"], "vss")
W(I["MCB"]["D"], I["MNB"]["D"]); W(I["MNB"]["G"], (580, -440), (620, -440)); L((620, -500), "nbias", "r"); dn(I["MNB"]["S"], "vss")
W(I["MPF"]["D"], I["MSF"]["S"]); L((820, -670), "vcg", "r"); up(I["MPF"]["S"], "vdd")
ST(I["MSF"]["G"], "vth", -30); dn(I["MSF"]["D"], "vss")
# threshold select: mode=0 -> vref, mode=1 -> vr = I_PTAT * R_REF
W(I["MX1"]["S"], (1020, -560), (1180, -560), I["MX2"]["S"]); W((1100, -560), (1100, -530)); L((1100, -530), "vth", "l")
up(I["MX1"]["D"], "vref"); up(I["MX2"]["D"], "vr"); ST(I["MX1"]["G"], "moden", -30); ST(I["MX2"]["G"], "mode", -30)
W(I["IMP"]["G"], I["IMN"]["G"]); W(I["IMP"]["D"], I["IMN"]["D"]); ST((1060, -360), "mode", -40)
W((1100, -360), (1180, -360)); L((1180, -360), "moden", "r"); up(I["IMP"]["S"], "vdd"); dn(I["IMN"]["S"], "vss")
# current steering: d_kg = 0 connects isrc to cap k, d_kg = 1 discharges it
for sw, dd, c, capn, g in (("SW1", "D1", "C1", "cap1", "d1g"), ("SW2", "D2", "C2", "cap2", "d2g")):
    W(I[sw]["G"], I[dd]["G"]); W(I[sw]["D"], I[dd]["D"]); ST((I[sw]["G"][0], I[sw]["G"][1] + 60), g, -40)
    yy = I[sw]["D"][1] + 30
    W((I[sw]["D"][0], yy), (I[c]["c0"][0], yy), I[c]["c0"]); sch.wlab((1500, yy), capn)
    up(I[sw]["S"], "isrc"); dn(I[dd]["S"], "vss"); dn(I[c]["c1"], "vss")
# comparators: HBT pair on an nbias tail, vcg collector cascodes, nbias bleeders, PMOS mirror, two inverters
for k, capn, outn in ((1, "cap1", "sn"), (2, "cap2", "rn")):
    qa, qb = I["QA%d" % k], I["QB%d" % k]
    cy = qa.origin[1]
    W(I["MLA%d" % k]["D"], I["MCA%d" % k]["D"]); W(I["MLB%d" % k]["D"], I["MCB%d" % k]["D"])
    W(I["MLA%d" % k]["G"], I["MLB%d" % k]["G"]); W((CX + 100, cy - 240), (CX + 100, cy - 190), (CX + 20, cy - 190))
    L((CX + 20, cy - 175), "oa%d" % k, "l")
    W(I["MCA%d" % k]["G"], I["MCB%d" % k]["G"]); sch.wlab((CX + 140, cy - 120), "vcg")
    W(I["MCA%d" % k]["S"], qa["C"]); W(I["MCB%d" % k]["S"], qb["C"])
    L((CX + 20, cy - 45), "ca%d" % k, "l"); L((CX + 220, cy - 45), "cb%d" % k, "r")
    W(I["MBA%d" % k]["D"], (CX - 60, cy - 60), (CX + 20, cy - 60)); W(I["MBB%d" % k]["D"], (CX + 280, cy - 60), (CX + 220, cy - 60))
    ST(I["MBA%d" % k]["G"], "nbias", -30); ST(I["MBB%d" % k]["G"], "nbias", 30)
    dn(I["MBA%d" % k]["S"], "vss"); dn(I["MBB%d" % k]["S"], "vss")
    W(qa["E"], (CX + 20, cy + 60), (CX + 220, cy + 60), qb["E"]); W(I["MT%d" % k]["D"], (CX + 120, cy + 60))
    sch.wlab((CX + 100, cy + 60), "tail%d" % k)
    ST(I["MT%d" % k]["G"], "nbias", -30); dn(I["MT%d" % k]["S"], "vss")
    ST(qa["B"], "vth", -30); ST(qb["B"], capn, 30)
    SL(qa["S"], "vss"); SL(qb["S"], "vss")
    up(I["MLA%d" % k]["S"], "vdd"); up(I["MLB%d" % k]["S"], "vdd")
    for nm, inp, outp in (("IC%dA" % k, "ob%d" % k, "c%d" % k), ("IC%dB" % k, "c%d" % k, outn)):
        P, N = I[nm + "P"], I[nm + "N"]
        W(P["G"], N["G"]); W(P["D"], N["D"]); up(P["S"], "vdd"); dn(N["S"], "vss")
    W((CX + 220, cy - 180), (CX + 400, cy - 180)); sch.wlab((CX + 330, cy - 180), "ob%d" % k)
    W((CX + 440, cy - 160), (CX + 580, cy - 160)); sch.wlab((CX + 540, cy - 160), "c%d" % k)
    W((CX + 620, cy - 160), (CX + 720, cy - 160)); sch.wlab((CX + 720, cy - 160), outn)


def nand_draw(name, n, out):
    P = [I[name + "P" + k] for k in "ABC"[:n]]
    N = [I[name + "N" + k] for k in "ABC"[:n]]
    y = P[0]["D"][1] + 45
    W(P[0]["D"], (P[0]["D"][0], y), (P[-1]["D"][0], y))
    for p in P[1:]:
        W(p["D"], (p["D"][0], y))
    W((P[0]["D"][0], y), N[0]["D"])
    for a, b in zip(N, N[1:]):
        W(a["S"], b["D"]); SL((a["S"][0], (a["S"][1] + b["D"][1]) / 2), a.pins["S"][1])
    W(P[0]["G"], N[0]["G"])
    for p in P:
        up(p["S"], "vdd")
    dn(N[-1]["S"], "vss")
    W((P[-1]["D"][0], y), (P[-1]["D"][0] + 100, y)); sch.wlab((P[-1]["D"][0] + 100, y), out)


nand_draw("NQ", 2, "q"); nand_draw("NQN", 3, "qn"); nand_draw("ND1", 2, "d1g"); nand_draw("ND2", 2, "d2g")
# output: a = !d2g (3.3 V), cross-coupled 1.2 V PMOS level shifter, two 1.2 V inverters
W(I["IAP"]["G"], I["IAN"]["G"]); W(I["IAP"]["D"], I["IAN"]["D"]); up(I["IAP"]["S"], "vdd"); dn(I["IAN"]["S"], "vss")
ST((3980, -440), "d2g", -40); W((4020, -440), (4100, -440), (4100, -380), I["MLSA"]["G"]); sch.wlab((4080, -440), "a")
W(I["MLPA"]["D"], I["MLSA"]["D"]); W(I["MLPB"]["D"], I["MLSB"]["D"])
W((4220, -470), (4350, -470), (4350, -510), I["MLPB"]["G"]); W((4420, -430), (4160, -430), (4160, -510), I["MLPA"]["G"])
L((4220, -455), "lsa", "l"); L((4420, -455), "lsb", "r")
ST(I["MLSB"]["G"], "d2g", -30); dn(I["MLSA"]["S"], "vss"); dn(I["MLSB"]["S"], "vss")
up(I["MLPA"]["S"], "vdd12"); up(I["MLPB"]["S"], "vdd12")
for a, b in (("IO1P", "IO1N"), ("IO2P", "IO2N")):
    W(I[a]["G"], I[b]["G"]); W(I[a]["D"], I[b]["D"]); up(I[a]["S"], "vdd12"); dn(I[b]["S"], "vss")
W((4420, -450), (4500, -450), (4500, -440), (4580, -440))
W((4620, -440), (4760, -440)); sch.wlab((4720, -440), "fon")
W((4800, -440), (4950, -440))
# ports (original order)
for i, (name, d) in enumerate(ports):
    if name == "fout":
        sch.port("fout", (4950, -440), "out")
    else:
        sch.port(name, (100, -1100 + 30 * i), d)
sch.frame(140, -880, 1260, 450, "PTAT legs (pbias/pcasc from G1_BGR), R_REF, cascode gate rail vcg, threshold select")
sch.frame(1300, -560, 1640, 380, "current steering + timing caps")
sch.frame(1680, -700, 2560, 420, "comparators: npn13G2 pair, collector cascodes, PMOS mirror")
sch.frame(2800, -720, 3900, 420, "NAND RS latch + steering drive")
sch.frame(3940, -620, 4880, -300, "3.3 V -> 1.2 V and output buffer")
sch.text("mode=0: vth = VREF, f proportional to I_PTAT / VREF (PTAT).  mode=1: vth = 2 I_PTAT R_REF, f = 1/(2 R_REF C), temperature-independent to first order.\n"
         "Simulated (not measured), chip BGR586: 1.507 MHz at 25 C, 4.909 kHz/C slope (block); chip netlists 1.518 MHz at 27 C, 1.997 MHz at 125 C (README.md).\n"
         "Revision 2: collector cascodes MCA/MCB keep V_CE = V_BE + ~0.3 V (npn13G2 vce_max 1.6 V); bleeders MBA/MBB keep the off cascode conducting.", 140, 520)
sch.title_block(140, -1500, "g1_t2f", "temperature-to-frequency converter, revision 2 (I_PTAT relaxation oscillator, cascoded HBT comparators)",
                "g1_t2f.spice sha256 8011b761 (flattened device/connectivity comparison)",
                "baseline (not rev1) = layout/g1_t2f.gds c2ae89a9, LVS reference layout/g1_t2f_lvs.cdl ce4d82b7", width=2400)
sch.write(os.path.join(out_dir, "g1_t2f.sch"))
write_sym(os.path.join(out_dir, "g1_t2f.sym"), "g1_t2f", ports)
