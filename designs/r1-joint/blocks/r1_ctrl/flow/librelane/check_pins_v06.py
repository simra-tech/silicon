#!/usr/bin/env python3
"""Compare the pin positions of a finished run (final DEF) with the template table.
usage: check_pins_v06.py <final r1_ctrl_top.def> <pins_v06*.json>   prints one line per mismatch and a summary
SPDX-License-Identifier: Apache-2.0"""
import json, re, sys
d = open(sys.argv[1]).read(); tab = json.load(open(sys.argv[2]))
want = {p["net"]: (p["x"], p["y"], p["edge"]) for p in tab["pins"]}
got = {}
for m in re.finditer(r"- (\S+) \+ NET \S+(?:.*?)\+ PLACED \( (-?\d+) (-?\d+) \)", d, re.S):
    pass
for blk in re.split(r"\n\s*- ", d.split("PINS")[1].split("END PINS")[0]):
    n = blk.split()[0] if blk.split() else ""
    r = re.search(r"\+ LAYER (\S+) \( (-?\d+) (-?\d+) \) \( (-?\d+) (-?\d+) \)", blk)
    p = re.search(r"\+ PLACED \( (-?\d+) (-?\d+) \)", blk)
    if n and r and p:
        x0, y0, x1, y1 = [int(v) / 1000.0 for v in r.groups()[1:]]
        px, py = int(p.group(1)) / 1000.0, int(p.group(2)) / 1000.0
        got[n] = (round(px + (x0 + x1) / 2, 3), round(py + (y0 + y1) / 2, 3), r.group(1))
bad = 0
for n, (x, y, e) in want.items():
    g = got.get(n.replace("[", "\\[").replace("]", "\\]")) or got.get(n)
    if g is None: print("MISSING", n); bad += 1; continue
    if (abs(g[0] - x) if e in "NS" else abs(g[1] - y)) > 0.05:   # along-edge coordinate only
         print("MISMATCH", n, "want", (x, y), "got", g[:2]); bad += 1
print("pins in table %d, in DEF %d, mismatches %d" % (len(want), len(got), bad))
