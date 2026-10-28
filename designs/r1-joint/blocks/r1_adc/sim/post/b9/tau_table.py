#!/usr/bin/env python3
"""T2o (D28 item 1): reference-path time-constant breakdown at the slice A port from the impedance runs
(gen_zref.py) and the B7 proxy waveforms; writes sim/post/b9/results/tau_breakdown.json.
usage: tau_table.py <zref run tt> <zref run ss>"""
import json, os, sys
import numpy as np
root = os.environ["G1_RESULTS_ROOT"]
out = {"label": "simulated (ngspice 46, B7 extraction = B6 PEX, small-signal at the buffer operating point; CDAC lines 0, "
                "comparators in reset, track switches open)", "runs": sys.argv[1:3], "corners": {}}
for rid, cn in zip(sys.argv[1:3], ("tt", "ss125")):
    d = os.path.join(root, "r1_adc", rid)
    Z = {t: np.loadtxt(os.path.join(d, "z_%s.txt" % t), skiprows=1) for t in ("l_main", "l_port", "m_main", "m_port")}
    f = Z["l_main"][:, 0]
    zl, zlp = Z["l_main"][:, 1], Z["l_port"][:, 3]
    r0 = float(zl[0])
    # single-pole fit of the vrefl main-node impedance between 10 and 100 MHz
    m = (f >= 1e7) & (f <= 1e8)
    fp = np.median(f[m] / np.sqrt(np.maximum((r0 / zl[m]) ** 2 - 1, 1e-12)))
    c = 1 / (2 * np.pi * r0 * fp)
    i3 = int(np.argmin(abs(f - 3e6)))
    zm = Z["m_main"][:, 5]
    out["corners"][cn] = {
        "vrefl_follower_output_ohm": round(r0, 1),
        "vrefl_wiring_main_to_slice_port_ohm": round(float(zlp[0] - zl[0]), 2),
        "vrefl_pole_MHz": round(fp / 1e6, 1), "vrefl_node_C_pF": round(c * 1e12, 2),
        "vrefl_tau_ns_smallsignal": round(r0 * c * 1e9, 2),
        "vref_closed_loop_ohm_1kHz": round(float(zm[0]), 2), "vref_peak_ohm": round(float(zm.max()), 1),
        "vref_peak_MHz": round(float(f[int(np.argmax(zm))]) / 1e6, 2),
        "vref_at_3MHz_main_port_ohm": [round(float(Z["m_main"][i3, 5]), 1), round(float(Z["m_port"][i3, 7]), 1)]}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "tau_breakdown.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
