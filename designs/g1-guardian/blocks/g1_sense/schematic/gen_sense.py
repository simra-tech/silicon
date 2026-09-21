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
from xsch import Sch, Sym

# ---------------------------------------------------------------- OTA ------
VDD, VSS = "vdd", "vss"
s = Sch("g1_ota: 3.3 V PMOS-input folded-cascode + CS output stage; vbn = NMOS bias gate (1.25 uA/um of hv nmos L=1u)")
# bias generator column (the 10 uA reference diode MBI lives in g1_sense and drives vbn)
s.mos("MB2", "sg13_hv_nmos", 200, -200, "8u", "1u", D="vbp", G="vbn", S=VSS, B=VSS, ng=2)
s.mos("MB3", "sg13_hv_pmos", 200, -400, "16u", "1u", D="vbp", G="vbp", S=VDD, B=VDD, ng=4)
s.mos("MB5", "sg13_hv_pmos", 300, -400, "16u", "1u", D="vbnc", G="vbp", S=VDD, B=VDD, ng=4)
s.mos("MB4", "sg13_hv_nmos", 300, -200, "1.6u", "1u", D="vbnc", G="vbnc", S=VSS, B=VSS, ng=1)      # Sooch W/5 -> nmos cascode gate
s.mos("MB6", "sg13_hv_nmos", 400, -200, "8u", "1u", D="vbpc", G="vbn", S=VSS, B=VSS, ng=2)
s.mos("MB7", "sg13_hv_pmos", 400, -400, "3.2u", "1u", D="vbpc", G="vbpc", S=VDD, B=VDD, ng=1)     # Sooch W/5 -> pmos cascode gate
# core
s.mos("MT", "sg13_hv_pmos", 600, -500, "128u", "1u", D="tail", G="vbp", S=VDD, B=VDD, ng=16)       # 80 uA tail
s.mos("M1", "sg13_hv_pmos", 550, -350, "96u", "2u", D="fn", G="inn", S="tail", B=VDD, ng=16)        # inn -> mirror side (stage 2 inverts)
s.mos("M2", "sg13_hv_pmos", 700, -350, "96u", "2u", D="fp", G="inp", S="tail", B=VDD, ng=16)
s.mos("M3", "sg13_hv_nmos", 550, -100, "80u", "1u", D="fn", G="vbn", S=VSS, B=VSS, ng=10)        # 100 uA sources
s.mos("M4", "sg13_hv_nmos", 700, -100, "80u", "1u", D="fp", G="vbn", S=VSS, B=VSS, ng=10)
s.mos("M13", "sg13_hv_nmos", 550, -200, "48u", "1u", D="mir", G="vbnc", S="fn", B=VSS, ng=6)       # nmos cascodes (60 uA)
s.mos("M16", "sg13_hv_nmos", 700, -200, "48u", "1u", D="out1", G="vbnc", S="fp", B=VSS, ng=6)
s.mos("M14", "sg13_hv_pmos", 900, -500, "96u", "1u", D="pc1", G="mir", S=VDD, B=VDD, ng=12)        # pmos sources 60 uA, mirror gate = mir
s.mos("M11", "sg13_hv_pmos", 1050, -500, "96u", "1u", D="pc2", G="mir", S=VDD, B=VDD, ng=12)
s.mos("M15", "sg13_hv_pmos", 900, -400, "96u", "1u", D="mir", G="vbpc", S="pc1", B=VDD, ng=12)     # pmos cascodes
s.mos("M12", "sg13_hv_pmos", 1050, -400, "96u", "1u", D="out1", G="vbpc", S="pc2", B=VDD, ng=12)
# second stage: PMOS common source, 120 uA NMOS load, Miller Cc 0.8 pF with nulling resistor 1.7 kOhm
# PMOS common source: its gate (out1) balances near vbp, i.e. near the mirror node, so the
# finite-gain systematic offset of stage 1 is small; NMOS current-source load from the ibias diode.
s.mos("M20", "sg13_hv_pmos", 1250, -500, "192u", "1u", D="out", G="out1", S=VDD, B=VDD, ng=24)
s.mos("M21", "sg13_hv_nmos", 1250, -300, "96u", "1u", D="out", G="vbn", S=VSS, B=VSS, ng=12)
s.res("RZ", 1150, -200, "1u", "6.2u", P="out1", M="cz")
s.cap("CC", 1250, -150, "23u", "23u", c0="cz", c1="out")
s.ports(1500, -500, ins=("inp", "inn", "vbn"), outs=("out",), ios=(VDD, VSS))
s.text("Currents with vbn from an 8u/1u diode at 10 uA equivalent: tail 80uA, PMOS sources 60uA, NMOS sources 100uA; stage 2 120uA class A; two-stage Miller compensated (Cc 0.8 pF, Rz 1.7 kOhm).", 100, -650)
s.text("inn on M1 (mirror side), inp on M2: stage-1 output out1 falls when inp rises, stage 2 inverts -> out rises. ibias: 10 uA sunk into MB1 diode.", 100, -600)
s.write("g1_ota.sch")
OTA_PINS = ["inp", "inn", "vbn", "out", VDD, VSS]
Sym.write("g1_ota.sym", "g1_ota", OTA_PINS, {"inp": "in", "inn": "in", "vbn": "in", "out": "out"})

# ------------------------------------------------------------- SENSE -------
# unit resistor 10 kOhm: rppd w=2u l=76.7u (R = 70e-6/w + 260*l/w -> 35 + 130*76.7 = 10.0 k)
RW, RL = "2u", "76.7u"
t = Sch("g1_sense: difference amplifier gain 20, pedestal VPED = 51/53 VREF (1.0008 V at VREF 1.04), ISENSE = VPED + 20*(SENSE_P-SENSE_N)")

def chain(sch, prefix, x, y, n, a, b):
    """n series unit resistors from net a to net b, placed downwards."""
    prev = a
    for i in range(n):
        nxt = b if i == n - 1 else "%s_%d" % (prefix, i)
        sch.res("%s%d" % (prefix, i), x, y + 80 * i, RW, RL, P=prev, M=nxt)
        prev = nxt

chain(t, "R1N", 100, -1800, 1, "sense_n", "vn")          # R1 on inverting side
chain(t, "R2N", 200, -1800, 20, "vn", "isense")          # R2 feedback, 20 units
chain(t, "R1P", 400, -1800, 1, "sense_p", "vp")          # R1 non-inverting side
chain(t, "R2P", 500, -1800, 20, "vp", "vped")            # R2 to pedestal
chain(t, "RD1", 700, -1800, 2, "vref_buf", "vped_ref")   # pedestal divider from the buffered VREF: 2 units up, 51 down -> 51/53 VREF
chain(t, "RD2", 800, -1800, 51, "vped_ref", VSS)
# bias diode: G1_BGR iptat (4.13 uA at 27 C, PTAT) into a 3.3u/1u hv nmos diode = same density as the 8u/10uA design point
t.mos("MBI", "sg13_hv_nmos", 1000, -1800, "3.3u", "1u", D="iptat", G="iptat", S=VSS, B=VSS, ng=1)
# main OTA, pedestal buffer, VREF buffer (the bandgap output is unbuffered, ~88 kOhm)
t.inst("XOTA", "g1_ota.sym", OTA_PINS, 1100, -1500, {"inp": "vp", "inn": "vn", "vbn": "iptat", "out": "isense", VDD: VDD, VSS: VSS})
t.inst("XBUF", "g1_ota.sym", OTA_PINS, 1100, -1200, {"inp": "vped_ref", "inn": "vped", "vbn": "iptat", "out": "vped", VDD: VDD, VSS: VSS})
t.inst("XREF", "g1_ota.sym", OTA_PINS, 1100, -900, {"inp": "vref", "inn": "vref_buf", "vbn": "iptat", "out": "vref_buf", VDD: VDD, VSS: VSS})
t.ports(1400, -1500, ins=("sense_p", "sense_n", "vref", "iptat"), outs=("isense", "vped", "vref_buf"), ios=(VDD, VSS))
t.text("iptat: 4.13 uA PTAT from G1_BGR into MBI; all three OTAs run at ~350 uA each (PTAT). vref_buf feeds the G1_TRIP DAC strings.", 100, -1900)
t.write("g1_sense.sch")
SENSE_PINS = ["sense_p", "sense_n", "vref", "iptat", "isense", "vped", "vref_buf", VDD, VSS]
Sym.write("g1_sense.sym", "g1_sense", SENSE_PINS)
print("wrote g1_ota.sch/.sym g1_sense.sch/.sym")
