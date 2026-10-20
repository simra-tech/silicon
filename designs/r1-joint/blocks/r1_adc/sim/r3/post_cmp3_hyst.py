#!/usr/bin/env python3
"""Post-process tb_cmp3_hyst: per reset width and CM, the decision at the strobe (13.0 ns after the start of
evaluation) in every period with the small negative input (must be 0, i.e. outp low), and its decision time.
usage: post_cmp3_hyst.py <bulk dir> OUT.json"""
import json
import os
import sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from rawread import read
H = 1e-6 / 60
d, _ = read(os.path.join(sys.argv[1], "hyst.raw"))
t = d["time"]
res = {}
import os as _o
NAMES = ("2", "8", "16", "24") if _o.environ.get("HYST_SET", "c") == "c" else ("c16", "c24", "c32", "c32c", "c40b", "c40c")
for w in NAMES:
    for tag, cm in (("h", 0.6), ("m", 0.35), ("l", 0.1)):
        n = "w%s%s" % (w, tag)
        dif = d["v(op%s)" % n] - d["v(on%s)" % n]
        ok, td = [], []
        for k in range(1, 12, 2):
            t0 = k * H + 1e-9
            m = (t > t0) & (t < t0 + 13.0e-9)
            x = dif[m]
            i = np.argmax(np.abs(x) > 0.6)
            res_ok = bool(np.abs(x[i]) > 0.6 and x[i] < 0)
            ok.append(res_ok)
            td.append(float((t[m][i] - t0) * 1e9) if np.abs(x[i]) > 0.6 else None)
        res["%s_cm%.2f" % (w, cm)] = {"correct_small_after_big": "%d/%d" % (sum(ok), len(ok)), "t_dec_ns": td}
json.dump(res, open(sys.argv[2], "w"), indent=1)
for k, v in res.items():
    print(k, v["correct_small_after_big"], [None if x is None else round(x, 2) for x in v["t_dec_ns"]])
