#!/usr/bin/env python3
"""T2j: pin check of a hardened r1_adc_sar: every pin of flow/pins.json is in the final DEF on Metal2 at the
planned x (+-0.005 um) on the planned edge, no extra signal pins; writes a text report.
usage: check_pins.py <final def> <pins.json> <out.txt>"""
import json, re, sys

deff, pj, out = sys.argv[1:4]
s = open(deff).read()
dbu = int(re.search(r"UNITS DISTANCE MICRONS (\d+)", s).group(1))
die = [int(x) / dbu for x in re.search(r"DIEAREA \( (-?\d+) (-?\d+) \) \( (-?\d+) (-?\d+) \)", s).groups()]
blk = s[s.index("\nPINS"):s.index("END PINS")]
got = {}
for ent in re.split(r"\n\s*- ", blk)[1:]:
    m = re.match(r"(\S+) \+ NET (\S+).*?LAYER (\S+) \( (-?\d+) (-?\d+) \) \( (-?\d+) (-?\d+) \).*?PLACED \( (-?\d+) (-?\d+) \) (\w+)", ent, re.S)
    if not m:
        continue
    name = m.group(1).replace("\\", "")
    got[name] = {"layer": m.group(3), "x": int(m.group(8)) / dbu, "y": int(m.group(9)) / dbu}
want = json.load(open(pj))["pins"]
lines, bad = [], 0
for p in want:
    g = got.get(p["net"])
    edge_ok = g is not None and (abs(g["y"] - die[3]) < 1.0 if p["edge"] == "N" else abs(g["y"] - die[1]) < 1.0)
    ok = g is not None and g["layer"] == "Metal2" and abs(g["x"] - p["x"]) < 0.005 and edge_ok
    bad += 0 if ok else 1
    lines.append("%-16s %s want x %8.3f got %s %s" % (p["net"], p["edge"], p["x"],
                 "%8.3f y %7.3f %s" % (g["x"], g["y"], g["layer"]) if g else "missing", "ok" if ok else "FAIL"))
extra = sorted(set(got) - set(p["net"] for p in want) - {"VDD", "VSS"})
bad += len(extra)
hdr = ["# pin check (tools/check_pins.py): %d planned pins, %d in DEF, extra %s; die %s" % (len(want), len(got), extra or "none", die),
       "# result: %s (%d failures)" % ("passed" if bad == 0 else "FAILED", bad)]
open(out, "w").write("\n".join(hdr + lines) + "\n")
print(hdr[1])
