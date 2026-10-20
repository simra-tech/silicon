#!/usr/bin/env python3
"""Generate tb_safe_cmp3.cir (revision 3: 8-bit summed DAC codes). Corner template for run_deck.py: threshold vs code
(calibration code k = 32, i.e. no correction), hysteresis, delay at 10 % overdrive."""
import json, os
VREF, VCMS, G, VPED = 1.05, 0.57, 14.0, 1.05 / 26
CODES = [int(x) for x in os.environ.get("R1_CODES", "4,14,32,59").split(",")]
TR = 6e-6       # half period of the triangle
DLY = 3e-6      # channel-b ramp delay (switching events never coincide)
SPAN = 0.025    # +-25 mV of Vod around the ideal threshold
vth = lambda c: (2 * c - 63) / 63.0 * VREF
here = os.path.dirname(os.path.abspath(__file__))
L = []
w = L.append
w("""* r1_safe comparator deck: threshold accuracy vs code (slow triangle on Vod around the ideal threshold), hysteresis,
* and propagation delay at 10 %% overdrive (overdrive = 10 %% of the threshold's distance from the zero-current
* output, in shunt terms). Inputs are ideal differential sense outputs: OUTx = %.2f V +- Vod/2 (r1_isense CM).
* Channel a: OC code c (its NEG parked at code 0); channel b: NEG code c (its OC parked at code 63), ramp delayed by 3 us,
* so no two comparators switch at the same time (simultaneous switching on shared taps: see README open issues).
* IDEAL REFERENCE SOURCES (this step only): VREF 1.05 V (r1_bgr, buffered), IBIAS 5 uA PTAT per comparator.
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib @@MOS@@
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib @@MOS@@
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib @@RES@@
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib @@CAP@@
.temp @@TEMP@@
.include /work/designs/r1-joint/blocks/r1_safe/schematic/r1_safe.spice
* revision 3: each comparator takes summed 8-bit codes nP/nN (cell code c, cal code k = 32 here)
.option gmin=1e-12 method=trap
* trap with a 2 ns (thresholds) / 1 ns (delays) maximum step: gear with 10 ns steps aborted at comparator
* transitions in the full four-comparator block (development runs dev-solver-v1..v9, dev-one-01)
Vdda vdda 0 dc @@VDDA@@
Vdd vdd 0 dc @@VDD@@
Vref vref 0 dc %.3f
Vcms vcms 0 dc %.3f
Ioa vdda ibias_oa dc {5u*(@@TEMP@@+273.15)/300.15}
Ina vdda ibias_na dc {5u*(@@TEMP@@+273.15)/300.15}
Iob vdda ibias_ob dc {5u*(@@TEMP@@+273.15)/300.15}
Inb vdda ibias_nb dc {5u*(@@TEMP@@+273.15)/300.15}
* bias-line capacitance (routing to r1_bgr), 100 fF each
Cba ibias_oa 0 100f
Cbb ibias_na 0 100f
Cbc ibias_ob 0 100f
Cbd ibias_nb 0 100f
Vvoda voda 0 dc 0
Vvodb vodb 0 dc 0
Eap outa_p vcms voda 0 0.5
Ean outa_n vcms voda 0 -0.5
Ebp outb_p vcms vodb 0 0.5
Ebn outb_n vcms vodb 0 -0.5""" % (VCMS, VREF, VCMS))
CMPS = ("oa", "na", "ob", "nb")
for cm in CMPS:
    for side in "pn":
        for i in range(8):
            w("V%s%s%d %s_%s%d 0 dc 0" % (cm, side, i, cm, side, i))
ports = " ".join(" ".join("%s_%s%d" % (cm, side, i) for i in range(8)) for cm in CMPS for side in "pn")
w("XDUT outa_p outa_n outb_p outb_n vref %s oc_a neg_a oc_b neg_b ibias_oa ibias_na ibias_ob ibias_nb vdda vdd 0 r1_safe_an" % ports)
w("CLa1 oc_a 0 10f\nCLa2 neg_a 0 10f\nCLb1 oc_b 0 10f\nCLb2 neg_b 0 10f")
w(".control\nset wr_singlescale\nset wr_vecnames")
def npn(c, k=32):
    d = k - 32
    return min(252, max(0, 4 * c - ((-d) // 2))), min(252, max(0, 4 * (63 - c) - (d // 2)))
def setcmp(cm, c, k=32):
    """cm in oa/na/ob/nb; c = cell code (OC: thr code; NEG: 63 - thr code)"""
    nP, nN = npn(c, k)
    for side, n in (("p", nP), ("n", nN)):
        for i in range(8):
            w("alter V%s%s%d dc = %s" % (cm, side, i, "@@VDD@@" if (n >> i) & 1 else "0"))
def setcodes(ca_, cb_):
    setcmp("oa", ca_); setcmp("na", 63 - ca_); setcmp("ob", cb_); setcmp("nb", 63 - cb_)
for c in CODES:
    setcmp("oa", c); setcmp("na", 63 - 0); setcmp("ob", 63); setcmp("nb", 63 - c)
    va = vth(c)
    w("alter Vvoda pwl = [ 0 %.5f %.6g %.5f %.6g %.5f %.6g %.5f ]" % (va - SPAN, TR, va + SPAN, 2 * TR, va - SPAN, 2 * TR + DLY, va - SPAN))
    w("alter Vvodb pwl = [ 0 %.5f %.6g %.5f %.6g %.5f %.6g %.5f ]" % (va - SPAN, DLY, va - SPAN, DLY + TR, va + SPAN, DLY + 2 * TR, va - SPAN))
    w("tran 2n %.6g 0 2n" % (2 * TR + DLY))
    w("wrdata @@OUT@@_thr_c%02d.txt v(voda) v(vodb) v(oc_a) v(neg_a) v(oc_b) v(neg_b) i(vdda) i(vdd)" % c)
# delay part: OC code 55 on both channels, NEG code 8
cOC, cNG = 55, 8
setcodes(cOC, cOC)
setcmp("na", 63 - cNG); setcmp("nb", 63 - cNG)
v0 = -G * VPED                       # zero shunt current
th_oc, th_ng = vth(cOC), vth(cNG)
od_oc = 0.1 * (th_oc - v0)           # 10 % of the threshold distance from zero current
od_ng = 0.1 * (v0 - th_ng)
# channel a: big steps (zero current -> threshold + 10 %); channel b: small steps around the OC threshold (+-1 LSB)
lsb = 2 * VREF / 63
pa = [(0, v0), (2e-6, v0), (2.001e-6, th_oc + od_oc), (5e-6, th_oc + od_oc), (5.001e-6, v0), (8e-6, v0),
      (8.001e-6, th_ng - od_ng), (11e-6, th_ng - od_ng), (11.001e-6, v0), (14e-6, v0)]
pb = [(0, th_oc - lsb), (3e-6, th_oc - lsb), (3.001e-6, th_oc + lsb), (6e-6, th_oc + lsb), (6.001e-6, th_oc - lsb), (9e-6, th_oc - lsb),
      (9.001e-6, th_ng + lsb), (12e-6, th_ng + lsb), (12.001e-6, th_ng - lsb), (14e-6, th_ng - lsb)]
# channel-b steps are 1 us after the channel-a steps: no two comparators switch together
w("alter Vvoda pwl = [ %s ]" % " ".join("%.6g %.5f" % p for p in pa))
w("alter Vvodb pwl = [ %s ]" % " ".join("%.6g %.5f" % p for p in pb))
w("tran 1n 14u 0 1n")
w("wrdata @@OUT@@_delay.txt v(voda) v(vodb) v(oc_a) v(neg_a) v(oc_b) v(neg_b) i(vdda) i(vdd)")
w(".endc\n.end")
open(os.path.join(here, "tb_safe_cmp3.cir"), "w").write("\n".join(L) + "\n")
json.dump({"codes": CODES, "TR": TR, "DLY": DLY, "SPAN": SPAN, "VREF": VREF, "G": G, "VPED": VPED, "delay_codes": {"oc": cOC, "neg": cNG},
           "od_oc_V": od_oc, "od_ng_V": od_ng, "lsb_V": lsb, "v0": v0},
          open(os.path.join(here, "tb_safe_cmp3.json"), "w"), indent=1)
print("ok", od_oc, od_ng)
