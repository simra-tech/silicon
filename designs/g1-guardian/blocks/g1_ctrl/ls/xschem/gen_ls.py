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
from xsch import Sch, Sym
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

s = Sch("g1_ls_up: 1.2 V in -> 3.3 V out (out = in level); LV inverter, hv NMOS pull-downs, cross-coupled hv PMOS keeper, hv output inverter")
m = lambda n: SIZES[n]
s.mos("MPI", m("MPI")[0], 100, -300, m("MPI")[1], m("MPI")[2], D="inb", G="in", S=VDD, B=VDD)
s.mos("MNI", m("MNI")[0], 100, -200, m("MNI")[1], m("MNI")[2], D="inb", G="in", S=VSS, B=VSS)
s.mos("MN1", m("MN1")[0], 300, -200, m("MN1")[1], m("MN1")[2], D="nb", G="in",  S=VSS, B=VSS)
s.mos("MN2", m("MN2")[0], 400, -200, m("MN2")[1], m("MN2")[2], D="n",  G="inb", S=VSS, B=VSS)
s.mos("MP1", m("MP1")[0], 300, -300, m("MP1")[1], m("MP1")[2], D="nb", G="n",   S=VDDA, B=VDDA)
s.mos("MP2", m("MP2")[0], 400, -300, m("MP2")[1], m("MP2")[2], D="n",  G="nb",  S=VDDA, B=VDDA)
s.mos("MPO", m("MPO")[0], 600, -300, m("MPO")[1], m("MPO")[2], D="out", G="nb", S=VDDA, B=VDDA)
s.mos("MNO", m("MNO")[0], 600, -200, m("MNO")[1], m("MNO")[2], D="out", G="nb", S=VSS, B=VSS)
s.ports(800, -300, ins=("in",), outs=("out",), ios=(VDD, VDDA, VSS))
s.text("in=1: MN1 pulls nb low, MP2 pulls n to vdda, MPO drives out high. No DC path in either state.", 100, -420)
s.write("g1_ls_up.sch")
Sym.write("g1_ls_up.sym", "g1_ls_up", ["in", "out", VDD, VDDA, VSS], {"in": "in", "out": "out"})
print("wrote g1_ls_up.sch/.sym")
