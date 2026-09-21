#!/usr/bin/env python3
"""Measure the physical separation of the G1_SEU TMR copies in a placed design.

Reads the final netlist (copy membership of every flop from the net on its Q
pin: u_core.u_seu.q<a|b|c>[i] for the chain stages, u_core.u_seu.u_<reg>.q<a|b|c>[i]
for the redundant control registers) and the final DEF (placement), and reports
for every stage the smallest distance between two of its three copies. The
criterion used in the README: every stage >= 20 um, i.e. more than an order of
magnitude above the charge-collection radius of a single ion strike in a
130 nm bulk process, so one particle cannot upset two copies of one stage.

Usage: tmr_check.py <final.nl.v> <final.def>
"""
import math
import re
import sys

nl, deff = sys.argv[1], sys.argv[2]
text = open(nl).read()
inst_re = re.compile(r"\b(sg13g2_\w+)\s+(\S+)\s*\((.*?)\)\s*;", re.S)
q_re = re.compile(r"\.Q\(\s*([^)]+?)\s*\)")
stages = {}
for m in inst_re.finditer(text):
    cell, name, pins = m.groups()
    if not cell.startswith("sg13g2_dfrbpq"):
        continue
    q = q_re.search(pins)
    if not q:
        continue
    net = q.group(1).replace("\\", "").strip()
    mm = re.match(r"u_core\.u_seu\.(u_\w+\.)?q([abc])\[(\d+)\]", net)
    if mm:
        stages.setdefault((mm.group(1) or "chain.", int(mm.group(3))), {})[mm.group(2)] = name

d = open(deff).read()
comp_re = re.compile(r"^\s*-\s+(\S+)\s+\S+\s+.*?\+\s+(?:PLACED|FIXED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)", re.M)
pos = {m.group(1): (int(m.group(2)) / 1000.0, int(m.group(3)) / 1000.0) for m in comp_re.finditer(d)}

rows = []
for key in sorted(stages):
    cp = stages[key]
    if set(cp) != {"a", "b", "c"} or any(cp[k] not in pos for k in "abc"):
        sys.exit(f"stage {key}: copies {sorted(cp)} / missing placement")
    p = {k: pos[cp[k]] for k in "abc"}
    dmin = min(math.dist(p["a"], p["b"]), math.dist(p["b"], p["c"]), math.dist(p["a"], p["c"]))
    rows.append((key, dmin, p))

n_chain = sum(1 for k, _, _ in rows if k[0] == "chain.")
dm = [r[1] for r in rows]
dm_sorted = sorted(dm)
print(f"# TMR copy separation: {len(rows)} stages ({n_chain} chain stages, {len(rows) - n_chain} control-register bits), "
      f"{3 * len(rows)} flops, all placed")
print(f"# min distance between two copies of one stage: min {dm_sorted[0]:.1f} um, "
      f"median {dm_sorted[len(dm_sorted) // 2]:.1f} um, max {dm_sorted[-1]:.1f} um")
for thr in (5, 10, 20, 40):
    print(f"# stages with a copy pair closer than {thr:2d} um: {sum(1 for v in dm if v < thr)}")
print("# stage  min_pair_um  a(x,y)  b(x,y)  c(x,y)")
for (reg, bit), dmin, p in rows:
    print(f"{reg}{bit:<4d} {dmin:7.1f}   " + "  ".join(f"({p[k][0]:.1f},{p[k][1]:.1f})" for k in "abc"))
