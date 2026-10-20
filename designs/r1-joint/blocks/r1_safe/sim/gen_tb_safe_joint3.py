#!/usr/bin/env python3
"""Generate tb_safe_joint3.cir: joint path r1_isense (both channels, real outputs) -> r1_safe_an (revision 3), nominal
devices, corner template for run_deck.py. Questions: threshold centre and delay through the real sense output, and
simultaneous switching of all four comparators on the shared string.
Timeline (both channels, shunt-referred input Vsh = ISP - ISN):
  0-2.05 us     r1_isense auto-zero, Vsh = 0 (comparator outputs invalid, blanked by r1_ctrl)
  3-13 us       SIMULTANEOUS: both channels ramp Vsh_th -3 mV -> +3 mV -> -3 mV (5 us per side); OC_a, OC_b trip and
                NEG_a, NEG_b release at the same crossing (all four at code THR, calibration code k = 32)
  14-26.5 us    STAGGERED: the same ramp, channel b delayed by 2.5 us (reference without coincident switching)
  27 us         both channels step 0 -> Vsh_th + 10 % (of Vsh_th) together; 29 us back to 0
  31-37 us      CROSS-CHANNEL: channel b holds Vsh_th - 1 mV (31-34 us, below its trip point) then Vsh_th + 1 mV
                (34-37 us, above), while channel a steps 0 -> Vsh_th + 10 % at 31.5 / 34.5 us and back at 32.5 / 35.5 us;
                any transition of oc_b / neg_b in these windows is kickback through the shared string taps
  Optional reference decoupling (R1_CREF = cmim side in um, 0 = none) on every comparator reference node.
PATH FIXTURE (deliberate): the codes are static in this deck, so each 256:1 mux is represented by its conducting
path (8 series thick NMOS switches w 0.5 l 0.45, gates at VDDA) plus one off switch (gate at 0) per level from the
sibling tap, i.e. the real reference-path impedance and junction loading at 1/30 of the device count. String and
comparators are the netlist of record; no code level shifters (static codes). The full-netlist version ran at about
8 min per simulated us (dev-joint3-fullmux, stopped).
IDEAL SOURCES (this step only): VREF 1.05 V (shared by r1_isense pedestal arms and the r1_safe string), VCM 0.6 V,
IBIAS 5 uA PTAT per r1_isense channel and per comparator, AZ phases.  Load: 2 pF per sense output (ADC T/H)."""
import os, json
VREF, G = 1.05, 14.0
THR = int(os.environ.get("R1_THR", "44"))
CREF = float(os.environ.get("R1_CREF", "0"))
OUTNAME = os.environ.get("R1_OUT", "tb_safe_joint3.cir")
vsh = lambda c: VREF * (1 / 26 + (2 * c - 63) / 882)
TH = vsh(THR); D = 3e-3
def npn(c, k=32):
    d = k - 32
    return min(252, max(0, 4 * c - ((-d) // 2))), min(252, max(0, 4 * (63 - c) - (d // 2)))
L = []; w = L.append
w("* " + __doc__.replace("\n", "\n* "))
w(""".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib @@MOS@@
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib @@MOS@@
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib @@RES@@
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib @@CAP@@
.temp @@TEMP@@
.include /work/designs/r1-joint/blocks/r1_isense/schematic/r1_isense.spice
.include /work/designs/r1-joint/blocks/r1_safe/schematic/r1_safe.spice
.option gmin=1e-12 method=gear reltol=1e-4 abstol=1e-12 vntol=1e-7
Vdda vdda 0 dc @@VDDA@@
Vdd vdd 0 dc @@VDD@@
Vref vref 0 dc 1.05
Vcm vcm 0 dc 0.6
Iba vdda iba dc {5u*(@@TEMP@@+273.15)/300.15}
Ibb vdda ibb dc {5u*(@@TEMP@@+273.15)/300.15}
Ioa vdda ibias_oa dc {5u*(@@TEMP@@+273.15)/300.15}
Ina vdda ibias_na dc {5u*(@@TEMP@@+273.15)/300.15}
Iob vdda ibias_ob dc {5u*(@@TEMP@@+273.15)/300.15}
Inb vdda ibias_nb dc {5u*(@@TEMP@@+273.15)/300.15}
Cba ibias_oa 0 100f
Cbb ibias_na 0 100f
Cbc ibias_ob 0 100f
Cbd ibias_nb 0 100f
Vaz az 0 pwl(0 @@VDD@@ 2.05u @@VDD@@ 2.051u 0)
Vazh azh 0 pwl(0 @@VDD@@ 2.0u @@VDD@@ 2.001u 0)
Vna isa_n 0 dc 0
Vnb isb_n 0 dc 0""")
lo, hi, h = TH - D, TH + D, TH * 1.1
pa = [(0, 0), (2.5e-6, 0), (3e-6, lo), (8e-6, hi), (13e-6, lo), (14e-6, lo), (19e-6, hi), (24e-6, lo), (26.5e-6, lo), (26.6e-6, 0),
      (27e-6, 0), (27.001e-6, h), (29e-6, h), (29.001e-6, 0), (31e-6, 0), (31.5e-6, 0), (31.501e-6, h), (32.5e-6, h), (32.501e-6, 0),
      (34.5e-6, 0), (34.501e-6, h), (35.5e-6, h), (35.501e-6, 0), (37e-6, 0)]
pb = [(0, 0), (2.5e-6, 0), (3e-6, lo), (8e-6, hi), (13e-6, lo), (16.5e-6, lo), (21.5e-6, hi), (26.5e-6, lo), (26.6e-6, 0),
      (27e-6, 0), (27.001e-6, h), (29e-6, h), (29.001e-6, 0), (30e-6, 0), (31e-6, TH - 1e-3), (34e-6, TH - 1e-3), (34.3e-6, TH + 1e-3), (37e-6, TH + 1e-3)]
w("Vpa isa_p isa_n pwl(%s)" % " ".join("%.6g %.6g" % p for p in pa))
w("Vpb isb_p isb_n pwl(%s)" % " ".join("%.6g %.6g" % p for p in pb))
w("XIS isa_p isa_n isb_p isb_n outa_p outa_n outb_p outb_n vref vcm iba ibb az azh az azh vdda vdd 0 r1_isense")
w("CLap outa_p 0 2p\nCLan outa_n 0 2p\nCLbp outb_p 0 2p\nCLbn outb_n 0 2p")
taps = " ".join("t%d" % k for k in range(253))
w("XSTR vref %s 0 r1_safe_string" % taps)
def path(n, out, pre):
    cur = "t%d" % n
    for lev in range(8):
        nxt = out if lev == 7 else "%s_l%d" % (pre, lev)
        sib = "t%d" % min(252, n ^ (1 << lev))
        w("X%s_on%d %s vdda %s 0 sg13_hv_nmos w=0.5u l=0.45u ng=1 m=1 mm_ok=1" % (pre, lev, cur, nxt))
        w("X%s_off%d %s 0 %s 0 sg13_hv_nmos w=0.5u l=0.45u ng=1 m=1 mm_ok=1" % (pre, lev, sib, nxt))
        cur = nxt
for cm, c, inp, inn, out in (("oa", THR, "outa_p", "outa_n", "oc_a"), ("na", 63 - THR, "outa_n", "outa_p", "neg_a"),
                             ("ob", THR, "outb_p", "outb_n", "oc_b"), ("nb", 63 - THR, "outb_n", "outb_p", "neg_b")):
    nP, nN = npn(c)
    w("* %s: cell code %d, k = 32: REFP = T%d, REFN = T%d" % (cm, c, nP, nN))
    path(nP, "refp_" + cm, "mp" + cm); path(nN, "refn_" + cm, "mn" + cm)
    if CREF > 0:
        w("XCRP%s refp_%s 0 cap_cmim w=%gu l=%gu m=1 mm_ok=1" % (cm, cm, CREF, CREF))
        w("XCRN%s refn_%s 0 cap_cmim w=%gu l=%gu m=1 mm_ok=1" % (cm, cm, CREF, CREF))
    w("X%s %s %s refp_%s refn_%s %s ibias_%s vdda vdd 0 r1_safe_cmp" % (cm.upper(), inp, inn, cm, cm, out, cm))
w("CL1 oc_a 0 10f\nCL2 neg_a 0 10f\nCL3 oc_b 0 10f\nCL4 neg_b 0 10f")
w(""".control
set wr_singlescale
set wr_vecnames
tran 1n 37u 0 1n
wrdata @@OUT@@_joint.txt v(isa_p) v(isb_p) v(outa_p) v(outa_n) v(outb_p) v(outb_n) v(oc_a) v(neg_a) v(oc_b) v(neg_b) v(t176) v(t76) i(vdda) i(vdd)
.endc
.end""")
here = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(here, OUTNAME), "w").write("\n".join(L) + "\n")
json.dump({"THR": THR, "CREF_um": CREF, "vsh_th_V": TH, "D_V": D, "step_V": h, "pa": pa, "pb": pb, "G": G, "VREF": VREF}, open(os.path.join(here, OUTNAME.replace(".cir", ".json")), "w"), indent=1)
print("ok", TH, npn(THR), npn(63 - THR))
