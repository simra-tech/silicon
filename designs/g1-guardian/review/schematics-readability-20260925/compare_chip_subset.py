#!/usr/bin/env python3
"""Compare the xschem netlist of the chip interconnect sheet with the top subcircuit of the chip CDL.

usage: compare_chip_subset.py CHIP.cdl SHEET.spice [--json OUT]

The sheet draws only macro, tie, pad-cell and bond-pad instances (black boxes).  Every instance of the
sheet must exist in the CDL top subcircuit with the same name, cell and ordered nets; every CDL
instance of a drawn cell type must be on the sheet; the port lists must be equal.  CDL instances of
other cell types (fill, decap, antenna, IO corner/filler) are counted and reported as not drawn.
"""
import collections
import hashlib
import json
import re
import sys


def cdl_top(path):
    txt = open(path).read().replace("\n+", " ")
    top = re.search(r"^\.SUBCKT g1_chip_top .*?^\.ENDS", txt, re.M | re.S | re.I).group(0).splitlines()
    insts = {}
    for line in top[1:]:
        t = line.split()
        if not t or t[0].startswith(".") or t[0].startswith("*"):
            continue
        cell = t[t.index("/") + 1] if "/" in t else t[-1]
        nets = t[1:t.index("/")] if "/" in t else t[1:-1]
        insts[t[0]] = (cell, tuple(nets))
    return top[0].split()[2:], insts


def sheet_top(path):
    lines, cur = [], None
    for raw in open(path).read().splitlines():
        if raw.startswith("+") and lines:
            lines[-1] += " " + raw[1:]
        else:
            lines.append(raw)
    ports, insts, inside = None, {}, False
    for line in lines:
        t = line.split()
        if not t:
            continue
        if t[0].lower() == ".subckt" and t[1] == "g1_chip_top":
            ports, inside = t[2:], True
        elif t[0].lower().startswith(".ends"):
            inside = False
        elif inside and not t[0].startswith("*"):
            insts[t[0]] = (t[-1], tuple(t[1:-1]))
    return ports, insts


cdl, sheet = sys.argv[1], sys.argv[2]
cp, ci = cdl_top(cdl)
sp, si = sheet_top(sheet)
drawn = set(c for c, _ in si.values())
diffs = []
if cp != sp:
    diffs.append("ports differ: %s vs %s" % (cp, sp))
for k in sorted(set(si) | set(n for n, (c, _) in ci.items() if c in drawn)):
    if si.get(k) != ci.get(k):
        diffs.append("%s: cdl %s sheet %s" % (k, ci.get(k), si.get(k)))
skipped = collections.Counter(c for n, (c, _) in ci.items() if c not in drawn)
res = {"cdl_sha256": hashlib.sha256(open(cdl, "rb").read()).hexdigest(),
       "sheet_netlist_sha256": hashlib.sha256(open(sheet, "rb").read()).hexdigest(),
       "compared_instances": len(si), "differences": diffs, "not_drawn": dict(skipped),
       "result": "identical (drawn subset)" if not diffs else "DIFFERENT"}
if "--json" in sys.argv:
    json.dump(res, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
print("g1_chip_top %s: %d instances compared, %d differences, not drawn %s" % (res["result"], len(si), len(diffs), dict(skipped)))
sys.exit(0 if not diffs else 1)
