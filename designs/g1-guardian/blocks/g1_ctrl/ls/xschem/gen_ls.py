"""Generate the g1_ls cell schematics (xschem 3.4.8RC format).

  g1_ls_up   1.2 V -> 3.3 V level shifter, no static current path:
             LV inverter (in -> inb, on vdd) drives two thick-oxide NMOS pull-downs;
             a cross-coupled thick-oxide PMOS pair on vdda holds the complementary
             nodes n / nb; an HV inverter from nb gives the full-swing output
             (out follows in). Structure of the PDK IO cell sg13g2_LevelUp
             (libs.ref/sg13g2_io/spice/sg13g2_io.spi); pull-downs widened from
             1.9 to 3.8 um so the LV-driven NMOS wins the contention against the
             keeper at vdd = 1.08 V, vdda = 3.63 V, mos_ss, -40 C (see ../sim).
Run: python3 gen_ls.py ; netlist with netlist.sh (inside the container).
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
VDD, VDDA, VSS = "vdd", "vdda", "vss"

# device sizes (um) -- single source of truth for schematic, layout and README
SIZES = {
    "MPI": ("sg13_lv_pmos", "2u",   "0.13u"),   # LV inverter
    "MNI": ("sg13_lv_nmos", "1u",   "0.13u"),
    "MN1": ("sg13_hv_nmos", "3.8u", "0.45u"),   # pull-down of nb (gate = in)
    "MN2": ("sg13_hv_nmos", "3.8u", "0.45u"),   # pull-down of n  (gate = inb)
    "MP1": ("sg13_hv_pmos", "0.3u", "0.45u"),   # keeper of nb (gate = n)
    "MP2": ("sg13_hv_pmos", "0.3u", "0.45u"),   # keeper of n  (gate = nb)
    "MPO": ("sg13_hv_pmos", "3.9u", "0.45u"),   # HV output inverter
    "MNO": ("sg13_hv_nmos", "1.9u", "0.45u"),
}

# ------------------------------------------------------------------ drawing --
# Readable sheet (2026-09-25): signal flow left to right, vdd/vdda rails on top, vss rail at
# the bottom.  Device attributes, instance order and port order are those of the original
# label-per-pin sheet, so the xschem netlist is unchanged (proof in
# designs/g1-guardian/review/schematics-readability-20260925).
s = Sheet("g1_ls_up")
m = lambda n: SIZES[n]
YP, YN, YTOP, YBOT = -300, -150, -390, -70          # PMOS row, NMOS row, supply rails
mpi = s.mos("MPI", m("MPI")[0], 200, YP, m("MPI")[1], m("MPI")[2], D="inb", G="in", S=VDD, B=VDD)
mni = s.mos("MNI", m("MNI")[0], 200, YN, m("MNI")[1], m("MNI")[2], D="inb", G="in", S=VSS, B=VSS)
mn1 = s.mos("MN1", m("MN1")[0], 440, YN, m("MN1")[1], m("MN1")[2], D="nb", G="in", S=VSS, B=VSS)
mn2 = s.mos("MN2", m("MN2")[0], 640, YN, m("MN2")[1], m("MN2")[2], D="n", G="inb", S=VSS, B=VSS)
mp1 = s.mos("MP1", m("MP1")[0], 440, YP, m("MP1")[1], m("MP1")[2], D="nb", G="n", S=VDDA, B=VDDA)
mp2 = s.mos("MP2", m("MP2")[0], 640, YP, m("MP2")[1], m("MP2")[2], D="n", G="nb", S=VDDA, B=VDDA)
mpo = s.mos("MPO", m("MPO")[0], 900, YP, m("MPO")[1], m("MPO")[2], D="out", G="nb", S=VDDA, B=VDDA)
mno = s.mos("MNO", m("MNO")[0], 900, YN, m("MNO")[1], m("MNO")[2], D="out", G="nb", S=VSS, B=VSS)
for d in (mpi, mni, mn1, mn2, mp1, mp2, mpo, mno):          # bodies tied to sources
    s.wire(d["B"], d["S"])
# input and LV inverter
s.port("in", (60, -225), "in")
s.wire((60, -225), (180, -225)); s.wire(mpi["G"], mni["G"])
s.wire(mpi["D"], mni["D"]); s.wire((220, -225), (300, -225)); s.lab((300, -225), "inb", "r")
s.stub(mn1["G"], "in", -40)
s.stub(mn2["G"], "inb", -40)
# pull-downs and cross-coupled keepers
s.wire(mp1["D"], mn1["D"]); s.wire(mp2["D"], mn2["D"])
s.wire((460, -245), (590, -245), (590, -300), mp2["G"])       # nb -> MP2 gate
s.wire((660, -205), (400, -205), (400, -300), mp1["G"])       # n -> MP1 gate (crosses nb once)
s.lab((460, -225), "nb", "l"); s.lab((660, -225), "n", "r")
# output inverter
s.wire(mpo["G"], mno["G"]); s.stub((880, -225), "nb", -40)
s.wire(mpo["D"], mno["D"]); s.wire((920, -225), (1040, -225))
s.port("out", (1040, -225), "out")
# supplies
s.wire(mpi["S"], (220, YTOP)); s.lab((220, YTOP), VDD, "l")
s.wire(mp1["S"], (460, YTOP), (920, YTOP)); s.wire(mp2["S"], (660, YTOP)); s.wire(mpo["S"], (920, YTOP))
s.lab((460, YTOP), VDDA, "l")
s.wire(mni["S"], (220, YBOT), (920, YBOT))
for d in (mn1, mn2, mno):
    s.wire(d["S"], (d["S"][0], YBOT))
s.lab((220, YBOT), VSS, "l")
s.port(VDD, (60, 40), "inout"); s.port(VDDA, (60, 70), "inout"); s.port(VSS, (60, 100), "inout")
s.frame(130, -430, 330, -40, "LV inverter (vdd 1.2 V)")
s.frame(350, -430, 760, -40, "pull-downs + cross-coupled keeper (vdda 3.3 V)")
s.frame(780, -430, 1080, -40, "HV output inverter")
s.text("in=1: MN1 pulls nb low, MP2 pulls n to vdda, MPO drives out high. No DC path in either state.\n"
       "MN1/MN2 widened to 3.8 um so the LV-driven pull-down wins at vdd 1.08 V, vdda 3.63 V, mos_ss, -40 C.\n"
       "Used 3x on the chip (t2f_en, t2f_mode, bgr_r4): static register bits, no timing requirement.", 140, 10)
s.title_block(130, -700, "g1_ls_up", "1.2 V to 3.3 V level shifter (no static current)",
              "sim/netlist/g1_ls_up.spice sha256 5567c807 (flattened device/connectivity comparison)",
              "baseline, 3 instances retained_g1_ls_up; layout g1_ls_up.gds 85de277c, LVS reference g1_ls_up.cdl 3465d0a6",
              width=1100)
s.write("g1_ls_up.sch")
write_symbol("g1_ls_up.sym", "g1_ls_up", ["in", "out", VDD, VDDA, VSS], {"in": "in", "out": "out"},
             label="1.2 V -> 3.3 V")
print("wrote g1_ls_up.sch/.sym")
