#!/usr/bin/env python3
"""Post-process tb_refbuf_pulse: VREF error at the comparator decision instants (cycle start + 2 ns, i.e. the
start of evaluation after the previous bit cycle's switching) relative to the quiescent level before the train.
Code error estimate at full scale: e_k [LSB] = dV(t_k) / VREF * 2048 * f, f = 1 (all P-side capacitors still at
VREF, all N-side at ground: the full-scale worst case). Decisions 0-4 (top array) are covered by the +31 LSB
redundancy; decisions 5-12 must stay below ~0.25 LSB. usage: post_refbuf.py <refbuf.raw> OUT.json"""
import json
import sys
import numpy as np
sys.path.insert(0, __file__.rsplit("/", 2)[0])
from rawread import read
d, _ = read(sys.argv[1], ["time", "v(vref)", "i(vdda)"])
t, v = d["time"], d["v(vref)"]
T = 1 / 30e6
t0 = 4e-6                                    # second frame of the train (first one sets the pattern history)
v0 = np.interp(2.9e-6, t, v)
res = {"label": "simulated (r1_refbuf alone, current-pulse CDAC model)", "vref_quiescent_V": float(v0),
       "ivdda_quiescent_uA": float(-np.interp(2.9e-6, t, d["i(vdda)"]) * 1e6),
       "max_droop_mV": float((v0 - v[(t > t0) & (t < t0 + 1e-6)].min()) * 1e3)}
for sl, off in (("A", 0), ("B", 13)):
    rows = []
    for k in range(13):
        tk = t0 + (k + off) * T + 2e-9
        dv = float(np.interp(tk, t, v) - v0)
        rows.append({"decision": k, "dV_uV": round(dv * 1e6, 1), "code_error_fullscale_lsb": round(abs(dv) / v0 * 2048, 3)})
    res["slice_" + sl] = rows
    res["slice_%s_max_err_decisions_5_12_lsb" % sl] = max(r["code_error_fullscale_lsb"] for r in rows[5:])
    res["slice_%s_max_err_decisions_0_4_lsb" % sl] = max(r["code_error_fullscale_lsb"] for r in rows[:5])
json.dump(res, open(sys.argv[2], "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if not k.startswith("slice_") or "max" in k}, indent=1))
