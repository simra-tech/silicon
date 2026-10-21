#!/usr/bin/env python3
"""T2 2026-10-21: reference noise of option 3c at the CDAC, from sim/r5/tb_refbuf5_noise.cir runs.
Method of sim/r4/post_refnoise4.py, for both outputs of r1_refbuf5 (vref: MSB array, vrefl: LSB array):
  S_out(f) = |H_out(f)|^2 * k^2 S_bgr(f) + S_buf,out(f)
  H_out : ac transfer vbgi -> vref / vrefl (Thevenin Rs 190 kOhm, 10 pF input filter, buffer)
  S_bgr : r1_bgr open-circuit noise density (decade table of ../r1_bgr/sim/results/summary-20261021.json, run
          bgr-noise-20261021-b, log-log interpolated; tt27 or ss125), scaled by k so that its 10 Hz - 10 MHz rms equals
          the published total. The table holds the bandgap's own roll-off (1 pF); applying H on top counts the source
          pole twice above about 0.8 MHz, so the band above 1 MHz is slightly low (as in revision 4).
  S_buf : ngspice noise of the buffer (Rs noiseless).
Integrated 10 Hz - 10 MHz and 10 Hz - 100 kHz. Criterion 110 uV rms (0.25 LSB) at each output. The LSB-array noise
reaches the comparator through the bridge (attenuated); judging vrefl on the same 110 uV is conservative.
usage: post_refnoise5.py OUT.json run_id:tt|ss ..."""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
root = os.environ["G1_RESULTS_ROOT"]
B = json.load(open(os.path.join(BLOCK, "..", "r1_bgr", "sim", "results", "summary-20261021.json")))["noise"]


def bgr_density(f, case):
    t = B[case]["density_nV_rtHz"]
    fx = np.array(sorted(float(k) for k in t))
    dx = np.array([t[k] for k in sorted(t, key=float)]) * 1e-9
    return np.exp(np.interp(np.log(f), np.log(fx), np.log(dx)))


def rms(f, s2, f1, f2):
    m = (f >= f1) & (f <= f2)
    return 1e6 * float(np.sqrt(np.trapz(s2[m], f[m])))


out = {"label": "simulated (sim/r5/tb_refbuf5_noise.cir: op + ac + noise) + r1_bgr spectrum (bgr-noise-20261021-b), "
                "sim/r5/post_refnoise5.py", "target_uV": 110.0, "source_model": "Rs 190 kOhm (noiseless) + r1_reffilt5 10 pF",
       "runs": {}}
for arg in sys.argv[2:]:
    rid, case = arg.split(":")
    d = os.path.join(root, "r1_adc", rid)
    ac = np.loadtxt(os.path.join(d, "ac.txt"))
    f = ac[:, 0]
    cb = {"tt": "tt27", "ss": "ss125"}[case]
    k = B[cb]["rms_10_10M_uV"] / rms(f, bgr_density(f, cb) ** 2, 10, 1e7)
    op = open(os.path.join(d, "op.txt")).read().split()
    opd = {op[i]: float(op[i + 1]) for i in range(1, len(op) - 1, 2)}
    r = {"corner_bgr_density": cb, "bgr_density_scale": round(k, 4), "vbg_V": opd["vbg"], "vref_V": opd["vref"],
         "vrefl_V": opd["vrefl"], "idda_mA": -opd["idda"] * 1e3}
    for col, node in ((1, "vref"), (3, "vrefl")):
        h = ac[:, col]
        nz = np.loadtxt(os.path.join(d, "noise_%s.txt" % node))
        sb = np.interp(f, nz[:, 0], nz[:, 1]) ** 2
        sg = (k * h * bgr_density(f, cb)) ** 2
        st = sg + sb
        i3 = np.argmax(h < h[0] / np.sqrt(2)) if np.any(h < h[0] / np.sqrt(2)) else None
        r[node] = {"h_dc": float(h[0]), "f_3dB_Hz": float(f[i3]) if i3 else None,
                   "bgr_uV_10_10M": rms(f, sg, 10, 1e7), "buffer_uV_10_10M": rms(f, sb, 10, 1e7),
                   "total_uV_10_10M": rms(f, st, 10, 1e7), "total_uV_10_100k": rms(f, st, 10, 1e5),
                   "pass_110uV": rms(f, st, 10, 1e7) <= 110.0}
    out["runs"][rid] = r
    print(rid, cb, " ".join("%s: H0 %.3f f3dB %s bgr %.1f buf %.1f total %.1f (10-100k %.1f) uV" % (
        n, r[n]["h_dc"], ("%.3g" % r[n]["f_3dB_Hz"]) if r[n]["f_3dB_Hz"] else "-", r[n]["bgr_uV_10_10M"],
        r[n]["buffer_uV_10_10M"], r[n]["total_uV_10_10M"], r[n]["total_uV_10_100k"]) for n in ("vref", "vrefl")))
json.dump(out, open(sys.argv[1], "w"), indent=1)
