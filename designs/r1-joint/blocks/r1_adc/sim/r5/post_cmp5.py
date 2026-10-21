#!/usr/bin/env python3
"""Revision 5: post-process the decision-0 comparator decks (sim/r5/tb_cmp5n_mem, tb_cmp5n_noise), all corners.
Copy of sim/r4/post_cmp4.py with the revision-5 CMs (0.70 / 0.60 / 0.50 V), the NMOS-input variants and the noise
window from the decision time at CM 0.6 V (the CM where this comparator works). Original header below.

Per corner: reset width of r1_cmp4_clkgen (mclk low after each clk30 rising edge, at 0.6 V).
Per variant, corner and CM: decision time t_dec of every tick from the start of evaluation (mclk rise) to
|outp - outn| > 0.6 V; correctness (+30 mV ticks -> outp high, -ASM ticks -> outp low, i.e. the memory test);
margin to the strobe (stb at the next clk30 edge - 0.6 ns). Supply current of the variant (3 comparators + bias).
Noise (method A of revision 2): quasi-static first-stage PSD at CM 0.1 V integrated with the sinc^2 window of an
integrator of length T_int = t_dec(CM 0.1 V, small input, median) - 1 ns.
usage: post_cmp4.py <set> <suffix> OUT.json
revision 5 usage: post_cmp5.py <suffix> OUT.json [set]"""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from rawread import read
os.environ.setdefault("CMP5_SET", sys.argv[3] if len(sys.argv) > 3 else "b")
from gen_cmp5_decks import VARIANTS, T, NT, CMS

SX, out = sys.argv[1], sys.argv[2]
SET = "n"
root = os.path.join(os.environ["G1_RESULTS_ROOT"], "r1_adc")
Tn = T * 1e-9
res = {"label": "simulated (tb_cmp4_mem: clkgen clock, alternating +30 mV / -0.2 mV; tb_cmp4_noise: quasi-static PSD) "
                "+ derived noise integration window", "target_uV": 60.0, "set": SET, "corners": {}}


def cross(t, x, th, rising, t0):
    m = t > t0
    tt, xx = t[m], x[m]
    i = np.nonzero((xx[:-1] < th) & (xx[1:] >= th))[0] if rising else np.nonzero((xx[:-1] > th) & (xx[1:] <= th))[0]
    if not i.size:
        return None
    j = i[0]
    return float(tt[j] + (th - xx[j]) * (tt[j + 1] - tt[j]) / (xx[j + 1] - xx[j]))


for c in ("tt27", "ss125", "ffm40"):
    d, _ = read(os.path.join(root, "r5-cmpn-mem-%s%s" % (c, SX), "mem.raw"))
    t = d["time"]
    edges = [2e-9 + k * Tn for k in range(1, NT)]
    rw, es = [], []
    for e in edges:
        f = cross(t, d["v(mclk)"], 0.6, False, e - 1e-9)
        r = cross(t, d["v(mclk)"], 0.6, True, e)
        rw.append((r - f) * 1e9)
        es.append(r)
    C = {"reset_width_ns": [round(x, 3) for x in rw], "eval_window_to_strobe_ns": round(Tn * 1e9 - 0.6 - np.mean(rw), 2)}
    for v in VARIANTS:
        V = {}
        for cm, tag in CMS:
            n = (v + tag).lower()
            dif = d["v(op%s)" % n] - d["v(on%s)" % n]
            td, ok = [], []
            for k in range(1, NT - 1):          # tick k: eval from es[k-1] to the edge edges[k]
                t0, tdead = es[k - 1], edges[k] - 0.6e-9
                m = (t > t0) & (t < tdead)
                x = dif[m]
                hit = np.nonzero(np.abs(x) > 0.6)[0]
                big = (k % 2 == 0)               # input +30 mV in tick k even (Vd starts at +30 mV)
                if hit.size:
                    td.append(float((t[m][hit[0]] - t0) * 1e9))
                    ok.append(bool((x[hit[0]] > 0) == big))
                else:
                    td.append(None)
                    ok.append(False)
            small = [x for i, x in enumerate(td) if (i + 1) % 2 == 1]
            V["cm%.2f" % cm] = {"t_dec_ns": [None if x is None else round(x, 2) for x in td],
                                "correct": "%d/%d" % (sum(ok), len(ok)),
                                "t_dec_small_max_ns": None if None in small else round(max(small), 2),
                                "margin_to_strobe_ns": None if None in td else round(C["eval_window_to_strobe_ns"] - max(td), 2)}
        m2 = (t > edges[1]) & (t < edges[-1])
        V["supply_uA_3cmp_plus_bias"] = round(float(-np.mean(d["i(v_%s)" % v.lower()][m2]) * 1e6), 1)
        a = np.loadtxt(os.path.join(root, "r5-cmpn-noise-%s%s" % (c, SX), "noise_%s.txt" % v), skiprows=1)
        f, vn = a[:, 0], a[:, 1]
        sm = [x for i, x in enumerate(V["cm0.60"]["t_dec_ns"]) if (i + 1) % 2 == 1 and x is not None]
        if sm:
            Ti = (float(np.median(sm)) - 1.0) * 1e-9
            V["noise_T_int_ns"] = round(Ti * 1e9, 2)
            V["noise_uV"] = round(float(np.sqrt(np.trapz(vn ** 2 * np.sinc(f * Ti) ** 2, f))) * 1e6, 1)
            V["white_nV_rtHz_100MHz"] = round(float(np.interp(1e8, f, vn) * 1e9), 2)
        C[v] = V
    res["corners"][c] = C
json.dump(res, open(out, "w"), indent=1)
for c in res["corners"]:
    C = res["corners"][c]
    print(c, "reset %.2f-%.2f ns, eval to strobe %.2f ns" % (min(C["reset_width_ns"]), max(C["reset_width_ns"]), C["eval_window_to_strobe_ns"]))
    for v in VARIANTS:
        V = C[v]
        print("  %-5s noise %5s uV  Tint %5s  I %6.1f uA | " % (V.get("noise_uV"), V.get("noise_uV") and "", V.get("noise_T_int_ns"), V["supply_uA_3cmp_plus_bias"])
              if False else "  %-5s noise %5s uV Tint %5s ns I %6.1f uA |" % (v, V.get("noise_uV"), V.get("noise_T_int_ns"), V["supply_uA_3cmp_plus_bias"]),
              " ".join("cm%s %s small-max %s margin %s" % (k[2:], V[k]["correct"], V[k]["t_dec_small_max_ns"], V[k]["margin_to_strobe_ns"])
                       for k in ("cm0.70", "cm0.60", "cm0.50")))
