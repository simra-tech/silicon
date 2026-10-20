#!/usr/bin/env python3
"""post_vref_load.py <tb.raw> <out.json>: charge drawn from the ideal VREF per bit cycle (Python 3.6).

Integrates -i(vref) of a tb_quick-type run (two slices, frames 1..8) per 33.3 ns cycle. Gives the per-frame
charge, the largest charge in one conversion cycle and the decoupling capacitance that would hold the droop
below 0.25 LSB (568 uV LSB) without any buffer action (simulated charge; the capacitance is derived)."""
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rawread
d, var = rawread.read(sys.argv[1], ["time", "i(vref)", "i(vdd)"])
t = d["time"]; i = -d["i(vref)"]; idd = -d["i(vdd)"]
T = 1 / 30e6; t0 = 0.25e-6; lsb = 568e-6
q = np.concatenate([[0], np.cumsum(0.5 * (i[1:] + i[:-1]) * np.diff(t))])
qd = np.concatenate([[0], np.cumsum(0.5 * (idd[1:] + idd[:-1]) * np.diff(t))])
Q = lambda a, b: np.interp(b, t, q) - np.interp(a, t, q)
rows = np.array([[Q(t0 + f * 1e-6 + k * T, t0 + f * 1e-6 + (k + 1) * T) for k in range(30)] for f in range(1, 9)])
qmax = float(np.abs(rows[:, :24]).max())
out = {"label": "simulated charge with ideal VREF and 400-ohm ideal drivers; decap figure derived",
       "frames": 8, "vref_charge_per_frame_pC": [round(x * 1e12, 3) for x in rows.sum(1)],
       "vref_avg_current_uA": float(rows.sum(1).mean() * 1e12),
       "max_charge_one_conversion_cycle_pC": qmax * 1e12,
       "decap_for_0p25lsb_droop_without_buffer_pF": qmax / (0.25 * lsb) * 1e12,
       "vdd_charge_per_frame_pC_comparators_bootstrap_buffers": float((np.interp(9.25e-6, t, qd) - np.interp(1.25e-6, t, qd)) / 8 * 1e12)}
json.dump(out, open(sys.argv[2], "w"), indent=1)
print(json.dumps(out, indent=1))
