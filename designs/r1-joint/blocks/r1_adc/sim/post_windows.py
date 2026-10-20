#!/usr/bin/env python3
"""post_windows.py <tag> <out.json>: DNL in the static windows of run_windows.sh (Python 3.6).
Each window: codes c-12 .. c+12 at 0.25 LSB per frame; DNL by histogram over the codes fully inside the window,
normalised to the ideal 4 hits per code (LSB 568 uV of the tt transitions, 142 uV per frame)."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from post_adc import load_codes
B = os.path.join(os.environ["G1_RESULTS_ROOT"], "r1_adc")
tag, out = sys.argv[1], sys.argv[2]
res = {"label": "simulated", "tag": tag, "hits_per_lsb_nominal": 4.0, "windows": []}
for c in (512, 1024, 1536, 1984, 2048):
    p = os.path.join(B, "win-%s-c%d" % (tag, c), "codes.txt")
    if not os.path.exists(p):
        p = os.path.join(B, "win-%s-c%dr-merged.txt" % (tag, c))
    if not os.path.exists(p):
        res["windows"].append({"centre": c, "status": "not run"})
        continue
    f, a, _ = load_codes(p)
    h = np.bincount(a, minlength=4096)
    lo, hi = a.min() + 1, a.max() - 1
    hh = h[lo:hi + 1].astype(float)
    dnl_nom = hh / 4.0 - 1
    dnl_avg = hh / hh.mean() - 1
    w = int(np.argmax(np.abs(dnl_avg)))
    res["windows"].append({"centre": c, "frames": int(len(a)), "codes": [int(lo), int(hi)],
                           "hits_per_code_mean": float(hh.mean()),
                           "dnl_min": float(dnl_avg.min()), "dnl_max": float(dnl_avg.max()),
                           "worst_code": int(lo + w), "missing_codes": int(np.sum(hh == 0)),
                           "hits": {str(int(lo + i)): int(x) for i, x in enumerate(hh)}})
json.dump(res, open(out, "w"), indent=1)
for wdw in res["windows"]:
    print(tag, wdw.get("centre"), {k: v for k, v in wdw.items() if k not in ("hits",)})
