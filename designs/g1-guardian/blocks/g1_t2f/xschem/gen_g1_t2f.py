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
write_sch(os.path.join(out_dir, "g1_t2f.sch"), "G1_T2F rev 2: I_PTAT relaxation oscillator, VREF or I_PTAT*R threshold, cascoded HBT comparators, 1.2 V output", ports, inst)
write_sym(os.path.join(out_dir, "g1_t2f.sym"), "g1_t2f", ports)
