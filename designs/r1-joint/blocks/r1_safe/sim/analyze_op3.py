#!/usr/bin/env python3
"""Collect tb_safe_op3: block supply currents per corner (IDDA includes the four 5 uA bias inputs)."""
import sys, os, json, glob
rdir, tdir = sys.argv[1], sys.argv[2]
res = {}
for f in sorted(glob.glob(os.path.join(rdir, "*.log"))):
    for line in open(f, errors="replace"):
        if line.startswith("OP3"):
            p = line.replace("=", " = ").split(); g = lambda k: float(p[p.index(k) + 2])
            c = p[p.index("corner") + 2]
            res[c] = {k: g(k) for k in ("idda_uA", "idd_uA", "iref_uA", "oc_a", "neg_a")}
            # the deck adds 4 x 5 uA PTAT to -i(vdda), but the bias sources already hang on the vdda node: remove the double count
            T = {"tt": 27, "ss": 125, "ff": -40, "ss_cold": -40, "ff_hot": 125}[c]
            res[c]["idda_deck_value_uA"] = res[c]["idda_uA"]; res[c]["idda_uA"] -= 4 * 5 * (T + 273.15) / 300.15
summ = {"result": res, "criterion": "report (no limit specified): static supply currents; IDDA = -i(vdda), which includes the four 5 uA PTAT bias inputs (the deck line adds them a second time; corrected here)",
        "disposition": "report: IDDA %s uA, IDD %s uA, VREF load %s uA" % ("/".join("%.0f" % v["idda_uA"] for v in res.values()), "/".join("%.2f" % v["idd_uA"] for v in res.values()), "/".join("%.2f" % v["iref_uA"] for v in res.values()))}
json.dump(summ, open(os.path.join(tdir, "summary.json"), "w"), indent=1); print(summ["disposition"], list(res))
