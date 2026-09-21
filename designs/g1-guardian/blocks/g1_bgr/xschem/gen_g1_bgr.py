"""Generate g1_bgr.sch / g1_bgr.sym (G1 bandgap reference, 3.3 V, npn13G2 PTAT core)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from schgen import write_sch, write_sym

HVP = "sg13g2_pr/sg13_hv_pmos.sym"
HVN = "sg13g2_pr/sg13_hv_nmos.sym"
NPN = "sg13g2_pr/npn13G2.sym"
RPPD = "sg13g2_pr/rppd.sym"
RHIGH = "sg13g2_pr/rhigh.sym"

MIR = dict(w="10u", l="4u", ng=1, m=1, mm_ok=1, model="sg13_hv_pmos", spiceprefix="X")
def pm(name, d, g, s, b="vdd", **kw):
    p = dict(MIR); p.update(kw)
    return (HVP, name, {"D": d, "G": g, "S": s, "B": b}, p)
def casc(name, d, s):
    # cascode with its body tied to its own source (separate n-well): no body effect, so the
    # mirror device below it sees VDS = I_PTAT * RB exactly
    return pm(name, d, "pcasc", s, b=s)
def nm(name, d, g, s, w, l):
    return (HVN, name, {"D": d, "G": g, "S": s, "B": "vss"}, dict(w=w, l=l, ng=1, m=1, mm_ok=1, model="sg13_hv_nmos", spiceprefix="X"))
def q(name, c, b, e):
    return (NPN, name, {"C": c, "B": b, "E": e, "S": "vss"}, dict(model="npn13G2", spiceprefix="X", Nx=1, mm_ok=1))
def r(name, p, m, w, l, model="rppd"):
    sym = RPPD if model == "rppd" else RHIGH
    return (sym, name, {"P": p, "M": m}, dict(w=w, l=l, model=model, body="sub!", spiceprefix="X", b=0, m=1, mm_ok=1))

R1_L = "51.5u"    # 13.4 kOhm: dVBE(300 K) / 4 uA
R2_L = os.environ.get("G1_BGR_R2L", "315u")   # ~82 kOhm: zero-TC tap found by sweep (sim/results)
RB_L = "500u"     # 130 kOhm PMOS cascode bias drop (I_PTAT * RB ~ 0.54 V at 300 K)
RX_L = "192u"     # 50 kOhm: lifts the NMOS cascode gate by ~0.2 V (PTAT) above 2 VBE

inst = [
    # cascoded PMOS mirror: gate rail pbias, cascode rail pcasc
    pm("MP1", "d1", "pbias", "vdd"), casc("MC1", "n1", "d1"),
    pm("MP2", "d2", "pbias", "vdd"), casc("MC2", "pbias", "d2"),
    r("RB", "pbias", "pcasc", "1u", RB_L),
    # NMOS cascodes hold both HBT collectors near VBE (VCB ~ 0): keeps npn13G2 (BVCEO ~ 1.7 V)
    # out of avalanche and makes the two collector voltages equal
    nm("MNC1", "n1", "vb2", "vbe", "20u", "1u"), nm("MNC2", "pcasc", "vb2", "c2", "20u", "1u"),
    # cascode gate bias vb2 = 2 VBE + I_PTAT * RX from its own mirror leg
    pm("MP5", "d5", "pbias", "vdd"), casc("MC5", "vb2", "d5"),
    r("RX", "vb2", "vd1", "1u", RX_L),
    q("QD1", "vd1", "vd1", "vd2"), q("QD2", "vd2", "vd2", "vss"),
    # PTAT cell: Q1 (1 unit, diode) vs Q2 (8 parallel units) with R1 in the Q2 emitter
    q("Q1", "vbe", "vbe", "vss"),
    q("Q1B", "vbe", "b1b", "vss"),      # optional second unit for the 1:4 ratio test mode
] + [q(f"Q2{c}", "c2", "vbe", "dvbe") for c in "ABCDEFGH"] + [
    r("R1", "dvbe", "vss", "1u", R1_L),
    # VREF branch: I_PTAT copy into R2 + diode-connected unit HBT
    pm("MP3", "d3", "pbias", "vdd"), casc("MC3", "vref", "d3"),
    r("R2", "vref", "vbe3", "1u", R2_L),
    q("Q3", "vbe3", "vbe3", "vss"),
    # I_PTAT output leg (DAC strings / monitor)
    pm("MP4", "d4", "pbias", "vdd"), casc("MC4", "iptat", "d4"),
    # start-up: full mirror copy into RDET; kick pulls pbias down until current flows
    pm("MPS", "det", "pbias", "vdd"),
    r("RDET", "det", "vss", "0.5u", "735u", model="rhigh"),
    nm("MNI", "kick", "det", "vss", "1u", "0.5u"),
    pm("MPI", "kick", "det", "vdd", w="2u", l="0.5u"),
    nm("MKFB", "pbias", "kick", "vss", "1u", "4u"),
    # ratio test mode: r4=1 connects Q1B in parallel with Q1 (ratio 8:2 = 4), r4=0 grounds its base
    nm("MSW1", "vbe", "r4", "b1b", "2u", "0.5u"),
    nm("MSW2", "b1b", "r4n", "vss", "1u", "0.5u"),
    nm("MNI2", "r4n", "r4", "vss", "1u", "0.5u"),
    pm("MPI2", "r4n", "r4", "vdd", w="2u", l="0.5u"),
]
ports = [("vdd", "inout"), ("vss", "inout"), ("r4", "in"), ("vref", "out"), ("iptat", "out"),
         ("pbias", "out"), ("pcasc", "out"), ("vbe", "out"), ("dvbe", "out")]
here = os.path.dirname(os.path.abspath(__file__))
write_sch(os.path.join(here, "g1_bgr.sch"), "G1_BGR: op-amp-less cascoded self-biased npn13G2 bandgap, 3.3 V", ports, inst)
write_sym(os.path.join(here, "g1_bgr.sym"), "g1_bgr", ports)
