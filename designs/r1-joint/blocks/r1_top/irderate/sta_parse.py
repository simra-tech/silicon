# SPDX-License-Identifier: Apache-2.0
"""r1_top try g, ctrl IR derate (track T11b): summary of sta_derate.tcl reports.
  python3 sta_parse.py <report> [<report> ...] > summary.json
Per case: worst slack max / min, TNS, worst slack to flop D, to outputs, to latch D (with the borrow), hold."""
import json
import re
import sys

out = {}
for f in sys.argv[1:]:
    txt = open(f).read()
    for m in re.finditer(r"=== CASE (\S+) early (\S+) late (\S+)\n(.*?)=== END", txt, re.S):
        name, e, l, body = m.groups()
        r = {"report": f.split("/")[-1], "early": float(e), "late": float(l)}
        g = re.search(r"worst slack max (\S+)", body); r["wns_max"] = float(g.group(1))
        g = re.search(r"worst slack min (\S+)", body); r["wns_min"] = float(g.group(1))
        g = re.search(r"tns max (\S+)", body); r["tns_max"] = float(g.group(1)) if g else None
        parts = re.split(r"--- (setup to flop D|setup to outputs|setup to latch D|hold)\n", body)
        for k in range(1, len(parts), 2):
            key = {"setup to flop D": "setup_ff", "setup to outputs": "setup_out", "setup to latch D": "setup_latch",
                   "hold": "hold"}[parts[k]]
            s = re.search(r"(-?[0-9.]+)\s+slack \((MET|VIOLATED)\)", parts[k + 1])
            r[key] = float(s.group(1)) if s else None
            if key == "setup_latch":
                b = re.search(r"(-?[0-9.]+)\s+time borrowed from endpoint", parts[k + 1])
                r["latch_borrow"] = float(b.group(1)) if b else None
            if key in ("setup_ff", "hold"):
                sp = re.search(r"Startpoint: (\S+)", parts[k + 1]); ep = re.search(r"Endpoint: (\S+)", parts[k + 1])
                r[key + "_path"] = "%s -> %s" % (sp.group(1) if sp else "?", ep.group(1) if ep else "?")
        out["%s/%s" % (r["report"], name)] = r
print(json.dumps(out, indent=1))
