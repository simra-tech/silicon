#!/usr/bin/env python3
"""Generate tb_safe_mc3.cir: full-path transient mismatch MC, r1_isense channel -> r1_safe revision 3 (shared 252-unit
string, OC and NEG comparators r1_safe_cmp), mm_ok=1 on every device, with the calibration search of r1_ctrl run
inside each sample and the found codes applied.
REDUCED FIXTURE (deliberate): the 256:1 muxes and code level shifters are replaced by ideal tap switches (S elements,
Ron 2 kOhm) on the taps the search and the operating codes can select. The muxes carry no DC current into the
comparator gates, so they add no mismatch; their dynamics are in tb_safe_cmp3 and tb_safe_joint3 (full netlist).
The full-mux version ran at about 55 s per simulated us (development run dev-mc3-smoke, stopped).
Per sample (one `reset` = one draw; both transients use the same draw):
  tran 1 (calibration): 0-2.05 us r1_isense AZ; Vsh = 0 (zero current) throughout. OC cell code c0 = 14, NEG cell
    code c0 = 49 (thr_neg 14). From 2.5 us the calibration code k steps every DW ns: ascending over K0..K1 (output of
    each comparator starts tripped; first code whose dwell ends with the output low = k_rel), then descending K1..K0
    (first code whose dwell ends with the output high = k_trip). Both comparators search at the same time.
    k_cal = 32 + round((k_rel + k_trip)/2 - k_ideal), k_ideal = 36.31 (OC) / 27.69 (NEG) (ratio constants).
  tran 2 (operation, codes applied): AZ again; OC at thr THR_OC, NEG at thr THR_NEG (cell 63 - THR_NEG), both with
    their k_cal. Slow shunt ramps +-3 mV around each threshold (centre = mean of trip and release points, shunt
    referred) and 10 % overdrive steps from zero current (delays).
IDEAL SOURCES (this step only): VREF 1.05 V, VCM 0.6 V, IBIAS 5 uA PTAT, AZ phases. Load 2 pF per sense output."""
import os, json, math
VREF, G = 1.05, 14.0
STEP = VREF / 252
THR_OC, THR_NEG = int(os.environ.get("R1_THR_OC", "54")), int(os.environ.get("R1_THR_NEG", "9"))
DW = float(os.environ.get("R1_DW", "200e-9"))
WIN = int(os.environ.get("R1_WIN", "8"))
T0 = 2.5e-6
vsh = lambda c: VREF * (1 / 26 + (2 * c - 63) / 882)
Tc = lambda c, k: (2 * c - 63) / 63 * VREF + (k - 32) * STEP
VCAL = -G * VREF / 26
CMP = {"oc": {"c0": 14, "vcal": VCAL}, "ng": {"c0": 49, "vcal": -VCAL}}
for k, v in CMP.items():
    v["kid"] = 32 + (v["vcal"] - Tc(v["c0"], 32)) / STEP
    v["K0"] = max(0, int(round(v["kid"])) - WIN); v["K1"] = min(63, int(round(v["kid"])) + WIN)
def npn(c, k):
    d = k - 32
    return min(252, max(0, 4 * c - ((-d) // 2))), min(252, max(0, 4 * (63 - c) - (d // 2)))
taps = " ".join("t%d" % k for k in range(253))
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
Ibi vdda ibi dc {5u*(@@TEMP@@+273.15)/300.15}
Io vdda ibias_o dc {5u*(@@TEMP@@+273.15)/300.15}
In vdda ibias_n dc {5u*(@@TEMP@@+273.15)/300.15}
Cbo ibias_o 0 100f
Cbn ibias_n 0 100f
Vaz az 0 pwl(0 @@VDD@@ 2.05u @@VDD@@ 2.051u 0)
Vazh azh 0 pwl(0 @@VDD@@ 2.0u @@VDD@@ 2.001u 0)
Visn isn 0 dc 0
Vsh isp isn dc 0
XIS isp isn outp outn vref vcm ibi az azh vdda vdd 0 r1_isense_ch
CLP outp 0 2p
CLN outn 0 2p
XSTR vref %s 0 r1_safe_string""" % taps)
# tap-switch controls: for each comparator and side, the set of taps used by the search and by the operating code
VDD_TOKEN = "@@VDD@@"
nsteps = {}
OPC = {"oc": THR_OC, "ng": 63 - THR_NEG}           # operating cell codes
cand = {}
for name, v in CMP.items():
    seq = list(range(v["K0"], v["K1"] + 1)) + list(range(v["K1"], v["K0"] - 1, -1)); nsteps[name] = seq
    for side in "pn":
        st = set()
        for k in range(v["K0"] - 2, v["K1"] + 3):
            st.add(npn(v["c0"], k)[0 if side == "p" else 1])
            st.add(npn(OPC[name], k)[0 if side == "p" else 1])
        cand[(name, side)] = sorted(st)
TCAL = T0 + len(nsteps["oc"]) * DW + 0.2e-6
w(".model swi sw vt=0.5 vh=0.1 ron=2k roff=1e13")
for name, v in CMP.items():
    seq = nsteps[name]
    for side in "pn":
        idx = 0 if side == "p" else 1
        for tap in cand[(name, side)]:
            pts = []; prev = None
            for j, k in enumerate(seq):
                on = 1 if npn(v["c0"], k)[idx] == tap else 0
                t = T0 + j * DW
                if j == 0: pts.append("0 %d" % on)
                elif on != prev:
                    # break before make: switches turn off at t, on at t + 2 ns
                    pts.append("%.7g %d %.7g %d" % ((t, prev, t + 1e-9, on) if on == 0 else (t + 1e-9, prev, t + 2e-9, on)))
                prev = on
            w("Vc%s%s%d c%s%s%d 0 pwl(%s)" % (name, side, tap, name, side, tap, " ".join(pts)))
            w("S%s%s%d ref%s_%s t%d c%s%s%d 0 swi" % (name, side, tap, side, name, tap, name, side, tap))
w("Cr1 refp_oc 0 50f\nCr2 refn_oc 0 50f\nCr3 refp_ng 0 50f\nCr4 refn_ng 0 50f")
w("* comparators (r1_safe_cmp of the netlist of record); NEG: inputs swapped")
w("XOC outp outn refp_oc refn_oc oc ibias_o vdda vdd 0 r1_safe_cmp")
w("XNG outn outp refp_ng refn_ng ng ibias_n vdda vdd 0 r1_safe_cmp")
w("CL1 oc 0 10f\nCL2 ng 0 10f")
# operation stimulus
to, tn = vsh(THR_OC), vsh(THR_NEG); D = 2e-3
op = [(0, 0), (2.3e-6, 0), (2.4e-6, to - D), (2.6e-6, to - D), (5.6e-6, to + D), (8.6e-6, to - D), (8.8e-6, tn + D), (9e-6, tn + D),
      (12e-6, tn - D), (15e-6, tn + D), (15.2e-6, 0), (15.5e-6, 0), (15.501e-6, 1.1 * to), (17e-6, 1.1 * to), (17.001e-6, 0),
      (18e-6, 0), (18.001e-6, 1.1 * tn), (19.5e-6, 1.1 * tn), (19.501e-6, 0), (20e-6, 0)]
w(".control\nset wr_singlescale\nset wr_vecnames\nsetseed @@SEED@@\nlet half = @@VDD@@/2\nlet i = 0")
w("while i < @@N@@\n  reset")
w("  alter vsh dc = 0")
w("  tran 1n %.6g 0 2n" % TCAL)
# find k_rel / k_trip: sample each output at the end of each dwell
for name in ("oc", "ng"):
    seq = nsteps[name]; n_up = len(seq) // 2
    w("  let %s_krel = -1" % name); w("  let %s_ktrip = -1" % name)
    w("  let j = 0")
    w("  while j < %d" % len(seq))
    w("    let ts = %.6g + (j + 1)*%.6g - 2n" % (T0, DW))
    w("    meas tran vv find v(%s) at=$&ts" % name)
    w("    if j < %d" % n_up)
    w("      if (%s_krel < 0) & (vv < half)" % name)
    w("        let %s_krel = %d + j" % (name, seq[0]))
    w("      end")
    w("    else")
    w("      if (%s_ktrip < 0) & (vv > half)" % name)
    w("        let %s_ktrip = %d - (j - %d)" % (name, seq[n_up], n_up))
    w("      end")
    w("    end")
    w("    let j = j + 1")
    w("  end")
    w("  let %s_kc = 32 + floor((%s_krel + %s_ktrip)/2 - %.6f + 0.5)" % (name, name, name, CMP[name]["kid"]))
    w("  if %s_kc > 63\n    let %s_kc = 63\n  end\n  if %s_kc < 0\n    let %s_kc = 0\n  end" % (name, name, name, name))
    c = THR_OC if name == "oc" else 63 - THR_NEG
    w("  let dd = %s_kc - 32" % name)
    w("  let np = %d + (0 - floor((0 - dd)/2))" % (4 * c))
    w("  let nn = %d - floor(dd/2)" % (4 * (63 - c)))
    w("  if np > 252\n    let np = 252\n  end\n  if np < 0\n    let np = 0\n  end\n  if nn > 252\n    let nn = 252\n  end\n  if nn < 0\n    let nn = 0\n  end")
    for side, var in (("p", "np"), ("n", "nn")):
        for tap in cand[(name, side)]:
            w("  let cv = 1 - abs(%s - %d)" % (var, tap))
            w("  if cv < 0\n    let cv = 0\n  end")
            w("  alter vc%s%s%d pwl = [ 0 $&cv 1 $&cv ]" % (name, side, tap))
w('  echo "CAL3" $&i "seed=@@SEED@@ oc_krel=" $&oc_krel " oc_ktrip=" $&oc_ktrip " oc_kc=" $&oc_kc " ng_krel=" $&ng_krel " ng_ktrip=" $&ng_ktrip " ng_kc=" $&ng_kc')
w("  alter vsh pwl = [ %s ]" % " ".join("%.6g %.6g" % p for p in op))
w("  tran 1n 20u 0 2n")
w("  meas tran oc_t find v(isp) when v(oc)=half rise=1 from=2.6u to=5.6u")
w("  meas tran oc_r find v(isp) when v(oc)=half fall=1 from=5.6u to=8.6u")
w("  meas tran ng_t find v(isp) when v(ng)=half rise=1 from=9u to=12u")
w("  meas tran ng_r find v(isp) when v(ng)=half fall=1 from=12u to=15u")
w("  meas tran oc_d when v(oc)=half rise=1 from=15.501u to=17u")
w("  meas tran ng_d when v(ng)=half rise=1 from=18.001u to=19.5u")
w("  let oc_err = ((oc_t + oc_r)/2 - %.9f)*1e6" % to)
w("  let ng_err = ((ng_t + ng_r)/2 - %.9f)*1e6" % tn)
w("  let oc_h = (oc_t - oc_r)*1e6\n  let ng_h = (ng_r - ng_t)*1e6")
w("  let oc_dl = (oc_d - 15.501u)*1e9\n  let ng_dl = (ng_d - 18.001u)*1e9")
w('  echo "MC3" $&i "seed=@@SEED@@ oc_err_uV=" $&oc_err " ng_err_uV=" $&ng_err " oc_hyst_uV=" $&oc_h " ng_hyst_uV=" $&ng_h " oc_dly_ns=" $&oc_dl " ng_dly_ns=" $&ng_dl')
w("  set idx = $&i")
w("  wrdata @@OUT@@_op_$idx v(isp) v(outp) v(outn) v(oc) v(ng)")
w("  let i = i + 1\nend\n.endc\n.end")
here = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(here, "tb_safe_mc3.cir"), "w").write("\n".join(L) + "\n")
json.dump({"THR_OC": THR_OC, "THR_NEG": THR_NEG, "vsh_oc_V": to, "vsh_neg_V": tn, "DW": DW, "T0": T0, "TCAL": TCAL,
           "cmp": CMP, "op_pwl": op, "candidates": {"%s_%s" % k: v for k, v in cand.items()}, "LSB_shunt_V": 2 * VREF / 63 / G}, open(os.path.join(here, "tb_safe_mc3.json"), "w"), indent=1)
print("ok", CMP, TCAL, to, tn)
