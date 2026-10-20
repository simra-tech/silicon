#!/usr/bin/env python3
"""Post-process tb_cmp3_tran (revision 3): per variant and common mode the decision time t_dec (|outp - outn| >
0.6 V, measured from the start of evaluation of the 3rd decision period), correctness, bias voltage and the
average supply current of the variant (three comparators of the variant + its bias) over periods 2-3.
usage: post_cmp3_tran.py <bulk dir> OUT.json"""
import json
import os
import sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rawread import read
from gen_cmp3_decks import VARIANTS

H = 1e-6 / 60.0
d, names = read(os.path.join(sys.argv[1], "cmp_tran.raw"))
t = d["time"]
t3 = 1e-9 + 2 * H
res = {"strobe_after_eval_start_ns": 13.0, "eval_ns": 13.5}
for v in VARIANTS:
    r = {}
    for tag, cm in (("h", 0.6), ("m", 0.35), ("l", 0.1)):
        n = (v + tag).lower()
        op, on = d["v(op%s)" % n], d["v(on%s)" % n]
        m = (t > t3) & (t < t3 + 13.5e-9)
        dif = (op - on)[m]
        i = np.argmax(np.abs(dif) > 0.6)
        ok = np.abs(dif[i]) > 0.6
        r["cm%.2f" % cm] = {"t_dec_ns": float(t[m][i] - t3) * 1e9 if ok else None,
                            "correct": bool(dif[i] > 0) if ok else None}
    m2 = (t > 1e-9 + H) & (t < 1e-9 + 3 * H)
    r["vbp_V"] = float(np.mean(d["v(vbp%s)" % v.lower()][m2]))
    r["supply_uA_3cmp_plus_bias"] = float(-np.mean(d["i(v_%s)" % v.lower()][m2]) * 1e6)
    r["t_dec_max_ns"] = max(x["t_dec_ns"] or 99 for k, x in r.items() if k.startswith("cm"))
    res[v] = r
json.dump(res, open(sys.argv[2], "w"), indent=1)
for v in VARIANTS:
    r = res[v]
    print(v, VARIANTS[v], "tdec", [None if r[c]["t_dec_ns"] is None else round(r[c]["t_dec_ns"], 2) for c in ("cm0.60", "cm0.35", "cm0.10")],
          "ok", [r[c]["correct"] for c in ("cm0.60", "cm0.35", "cm0.10")], "vbp %.3f I %.0f uA" % (r["vbp_V"], r["supply_uA_3cmp_plus_bias"]))
