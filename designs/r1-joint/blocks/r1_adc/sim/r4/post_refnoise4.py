#!/usr/bin/env python3
"""Reference noise seen by the CDAC (revision 4, coordinator request 2026-10-21), from tb_refbuf4_noise.cir runs.

S_vref(f) = |H(f)|^2 * S_bgr(f) + S_buf(f)
  H      : ac transfer vbgi -> vref of the run (Thevenin source Rs, input filter, buffer)
  S_bgr  : r1_bgr open-circuit vref noise density, log-log interpolation of the decade table in
           ../r1_bgr/sim/results/summary-20261021.json (run bgr-noise-20261021-b; tt27 or ss125 by corner). The
           table already contains the bandgap roll-off with 1 pF; applying H on top counts the source pole twice
           above about 0.8 MHz (the band above 1 MHz is then slightly low; noted in the README).
           The decade table is scaled so that its 10 Hz - 10 MHz rms equals the published total (158.1 / 188.5 uV).
  S_buf  : ngspice noise of the buffer, divider and filter at vref (Rs noiseless).
Integrated 10 Hz - 10 MHz and 10 Hz - 100 kHz. Target 110 uV rms (0.25 LSB, coordinator).
usage: post_refnoise4.py OUT.json run_id[:tt|ss] ...
"""
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


out = {"label": "simulated (tb_refbuf4_noise.cir: ac + noise) + r1_bgr spectrum (bgr-noise-20261021-b), post_refnoise4.py",
       "target_uV": 110.0, "runs": {}}
for arg in sys.argv[2:]:
    rid, case = (arg.split(":") + ["tt"])[:2]
    d = os.path.join(root, "r1_adc", rid)
    ac = np.loadtxt(os.path.join(d, "ac.txt"))
    nz = np.loadtxt(os.path.join(d, "noise.txt"))
    f, h = ac[:, 0], ac[:, 1]
    sb = np.interp(f, nz[:, 0], nz[:, 1]) ** 2
    case_b = {"tt": "tt27", "ss": "ss125"}[case]
    # the decade table under-reads the published rms (onoise_total); scale the density so that the unfiltered
    # 10 Hz - 10 MHz rms equals the r1_bgr value (factor recorded per run)
    k = B[case_b]["rms_10_10M_uV"] / rms(f, bgr_density(f, case_b) ** 2, 10, 1e7)
    sg = (k * h * bgr_density(f, case_b)) ** 2
    op = open(os.path.join(d, "op.txt")).read().split()
    opd = {op[i]: float(op[i + 1]) for i in range(1, len(op) - 1, 2)}
    st = sg + sb
    r = {"corner": case_b, "vbg_V": opd["vbg"], "vref_V": opd["vref"], "ibg_A": opd["ibg"], "idda_mA": -opd["idda"] * 1e3,
         "h_dc": float(h[0]), "f_3dB_Hz": float(f[np.argmax(h < h[0] / np.sqrt(2))]) if np.any(h < h[0] / np.sqrt(2)) else None,
         "bgr_uV_10_10M": rms(f, sg, 10, 1e7), "buffer_uV_10_10M": rms(f, sb, 10, 1e7),
         "total_uV_10_10M": rms(f, st, 10, 1e7), "total_uV_10_100k": rms(f, st, 10, 1e5),
         "bgr_density_scale": round(k, 4)}
    r["pass_110uV"] = r["total_uV_10_10M"] <= 110.0
    out["runs"][rid] = r
    print("%-26s %s vref %.4f H0 %.3f f3dB %s bgr %.1f buf %.1f total %.1f (10-100k %.1f) uV" % (
        rid, case, r["vref_V"], r["h_dc"], ("%.3g" % r["f_3dB_Hz"]) if r["f_3dB_Hz"] else "-", r["bgr_uV_10_10M"],
        r["buffer_uV_10_10M"], r["total_uV_10_10M"], r["total_uV_10_100k"]))
json.dump(out, open(sys.argv[1], "w"), indent=1)
