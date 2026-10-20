#!/usr/bin/env python3
"""Post-process tb_cmp2_tran: per variant and common mode, integration and decision times (third clock cycle,
clk rises at 2 ns + 2 T). t_int: dip/din mean from 0 to 0.6 V (first-stage integration window used in the noise
integral); t_dec: |outp - outn| > 0.6 V. Energy per decision from the VDD current over the 2nd cycle / number of
comparators is not separable per instance here and is reported for the whole deck only."""
import json
import sys
import numpy as np
sys.path.insert(0, __file__.rsplit("/", 1)[0])
sys.path.insert(0, __file__.rsplit("/", 2)[0])
from rawread import read
from cmp_variants import VARIANTS

raw, out = sys.argv[1], sys.argv[2]
d, names = read(raw)
t = d["time"]
res = {}
for v in VARIANTS:
    for tag, cm in (("h", 0.6), ("m", 0.35), ("l", 0.1)):
        n = (v + tag).lower()
        dip, din = d["v(x%s.dip)" % n], d["v(x%s.din)" % n]
        op, on = d["v(op%s)" % n], d["v(on%s)" % n]
        m = (t > 2e-9 + 2 * 33.333e-9) & (t < 19e-9 + 2 * 33.333e-9)
        tt, avg, dif = t[m], 0.5 * (dip + din)[m], (op - on)[m]
        def cross(x, th):
            i = np.argmax(x > th)
            return float(tt[i] - 2e-9 - 2 * 33.333e-9) if x[i] > th else None
        res["%s_cm%.1f" % (v, cm)] = {"t_int_0p6V_ns": None if cross(avg, 0.6) is None else cross(avg, 0.6) * 1e9,
                                      "t_int_0p8V_ns": None if cross(avg, 0.8) is None else cross(avg, 0.8) * 1e9,
                                      "t_dec_ns": None if cross(np.abs(dif), 0.6) is None else cross(np.abs(dif), 0.6) * 1e9,
                                      "decision_correct": None if cross(np.abs(dif), 0.6) is None else bool(dif[np.argmax(np.abs(dif) > 0.6)] > 0)}
m = (t > 35.33e-9) & (t < 68.67e-9)
res["deck_vdd_energy_pJ_per_cycle_all"] = float(-np.trapz(d["i(vdd)"][m], t[m]) * 1.2 * 1e12)
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res, indent=1))
