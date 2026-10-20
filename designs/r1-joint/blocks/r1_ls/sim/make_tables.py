#!/usr/bin/env python3
"""Markdown tables from results/<run-id>.json (host python 3.6). Usage: python3 make_tables.py <run-id>"""
import json, sys
d = json.load(open("results/%s.json" % sys.argv[1]))
order = ["tt_27C_3p3_1p2", "ss_125C_3p0_1p08", "ff_m40C_3p6_1p32", "ss_m40C_3p6_1p08_stress"]
names = {"tt_27C_3p3_1p2": "tt, 27 C, 3.3 / 1.2 V", "ss_125C_3p0_1p08": "ss, 125 C, 3.0 / 1.08 V", "ff_m40C_3p6_1p32": "ff, -40 C, 3.6 / 1.32 V", "ss_m40C_3p6_1p08_stress": "ss, -40 C, 3.6 / 1.08 V (stress)"}
print("| Cell | Corner | rise delay (ps) | fall delay (ps) | rise-fall skew (ps) | 10-90 rise (ps) | 90-10 fall (ps) | pulse width change at 30 MHz (ps) | duty distortion (% of period) | levels low / high (V) |")
print("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
for cell in ("g1_ls_up", "g1_lvlup", "g1_lvldn"):
    for c in order:
        r = d["%s/%s" % (cell, c)]
        w = (r["hout_ns"] - r["hin_ns"]) * 1e3
        print("| `%s` | %s | %.0f | %.0f | %.0f | %.0f | %.0f | %+.0f | %+.2f | %.1e / %.4g |" % (
            cell, names[c], r["tr_ps"], r["tf_ps"], r["tr_ps"] - r["tf_ps"], r["tr1090_ps"], r["tf9010_ps"], w, w / 33333.0 * 100.0, r["vlo"], r["vhi"]))
print()
print("| Cell | Corner | static I(3.3 V domain), in low / high (pA) | static I(1.2 V domain), in low / high (pA) | peak I(3.3 V) rising edge (uA) | peak I(3.3 V) falling edge (uA) | peak I(1.2 V) rising edge (uA) |")
print("| --- | --- | --- | --- | ---: | ---: | ---: |")
for cell in ("g1_ls_up", "g1_lvlup", "g1_lvldn"):
    for c in order:
        r = d["%s/%s" % (cell, c)]
        s0, s1 = r["static"]["in=0"], r["static"]["in=1"]
        a = ("n/a (no 3.3 V supply pin)" if cell == "g1_lvldn" else "%.1f / %.1f" % (s0["ivdda_A"] * 1e12, s1["ivdda_A"] * 1e12))
        print("| `%s` | %s | %s | %.1f / %.1f | %s | %s | %.1f |" % (cell, names[c], a, s0["ivdd_A"] * 1e12, s1["ivdd_A"] * 1e12,
              ("n/a" if cell == "g1_lvldn" else "%.0f" % r["iapk_uA"]), ("n/a" if cell == "g1_lvldn" else "%.0f" % r["iapkf_uA"]), r["icpk_uA"]))
