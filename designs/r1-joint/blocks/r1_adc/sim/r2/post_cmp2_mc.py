#!/usr/bin/env python3
"""Post-process tb_cmp2_offset_mc: per copy, the input at which the decision changes from low to high.
Decision of cycle n read 15 ns after the evaluation start (the SAR strobe instant, 0.45 T); the input of cycle n is
the ramp value at the evaluation start. Offset = mid-point between the last 'low' and the first 'high' input
(resolution = ramp step). usage: post_cmp2_mc.py <offset.raw> OUT.json VR NC VCM"""
import json
import sys
import numpy as np
sys.path.insert(0, __file__.rsplit("/", 2)[0])
from rawread import read
raw, out, vr, nc, vcm = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
d, names = read(raw)
t = d["time"]
T = 33.3333e-9
n = np.arange(nc)
ts = 2e-9 + n * T + 15e-9
vin = -vr + 2 * vr * (2e-9 + n * T) / (nc * T)
offs = []
flips = []
for i in range(30):
    o = np.interp(ts, t, d["v(op%d)" % i]) > 0.6
    o[:2] = False   # the first two cycles start from the initial condition, not from a decision
    k = int(np.argmax(o)) if o.any() else None
    if k is None or k == 0:
        offs.append(np.nan)
        continue
    offs.append(0.5 * (vin[k - 1] + vin[k]))
    flips.append(int(np.sum(np.diff(o[k - 5:k + 5].astype(int)) != 0)) if k > 5 else 0)
offs = np.array(offs)
res = {"label": "simulated (mos_tt_mismatch, mmos=1, 30 copies, no noise)", "input_cm_V": vcm, "ramp_step_uV": 2 * vr / nc * 1e6,
       "offset_mV": [None if np.isnan(x) else round(x * 1e3, 4) for x in offs],
       "mean_mV": float(np.nanmean(offs) * 1e3), "sigma_mV": float(np.nanstd(offs, ddof=1) * 1e3),
       "max_abs_mV": float(np.nanmax(np.abs(offs)) * 1e3), "copies_resolved": int(np.sum(~np.isnan(offs)))}
json.dump(res, open(out, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "offset_mV"}, indent=1))
