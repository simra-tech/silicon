#!/usr/bin/env python3
"""Generate MANUAL_GLOBAL_PLACEMENTS that spread the three copies of every
G1_SEU TMR stage apart, density-neutrally.

Second separation method (run7). The first one (tmr_columns.py, run6) seeded
each copy into its own vertical third of the core; that moved two thirds of the
SEU flops out of the region global placement had chosen for them, left the west
half-empty and the east overfull, and the legaliser then displaced five copy-c
flops by more than 100 um back next to copy b. It also made every vote net
about 230 um long (81 max-slew violations at the slow corner).

Here every stage's three flops stay where global placement put them, on
average: copy a is seeded DX to the west and DY south of the stage's centroid,
copy b at the centroid, copy c DX east and DY north. Copies of one stage are
therefore at least ~sqrt(DX^2 + DY^2) apart in two directions (so neither a
track along a row nor one along a column can cross two of them), the density
map is unchanged to first order, and a vote net spans about 2 DX.

Copy membership comes from the net on the flop's Q pin in the synthesised
netlist: u_core.u_seu.q<a|b|c>[i] (chains) and u_core.u_seu.u_<reg>.q<a|b|c>[i]
(TMR control registers). Positions come from the DEF written by the global
placement step (identical between runs of the same netlist and configuration).

Usage: tmr_spread.py <netlist.nl.v> <globalplacement.def> <out.yaml> [DX DY]
Defaults DX = 40 um, DY = 15.12 um (4 rows). Paste the YAML into the config.
"""
import re
import sys

nl, deff, out = sys.argv[1], sys.argv[2], sys.argv[3]
DX = float(sys.argv[4]) if len(sys.argv) > 4 else 40.0
DY = float(sys.argv[5]) if len(sys.argv) > 5 else 15.12
FLOP_W = 12.96          # sg13g2_dfrbpq_1 width (um)
MARGIN = 2.0

text = open(nl).read()
inst_re = re.compile(r"\b(sg13g2_\w+)\s+(\S+)\s*\((.*?)\)\s*;", re.S)
q_re = re.compile(r"\.Q\(\s*([^)]+?)\s*\)")
stages = {}                                   # (reg, bit) -> {copy: instance}
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
        stages.setdefault((mm.group(1) or "", int(mm.group(3))), {})[mm.group(2)] = name

d = open(deff).read()
# placement rows: "ROW <name> <site> x y <orient> DO n BY 1 STEP sx sy ;"
rows = [(int(x) / 1000.0, int(y) / 1000.0, int(n), int(sx) / 1000.0) for x, y, n, sx in
        re.findall(r"^ROW\s+\S+\s+\S+\s+(-?\d+)\s+(-?\d+)\s+\S+\s+DO\s+(\d+)\s+BY\s+1\s+STEP\s+(\d+)", d, re.M)]
x_lo = min(r[0] for r in rows); x_hi = max(r[0] + r[2] * r[3] for r in rows)
y_lo = min(r[1] for r in rows); y_hi = max(r[1] for r in rows)
comp_re = re.compile(r"^\s*-\s+(\S+)\s+\S+\s+.*?\+\s+(?:PLACED|FIXED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)", re.M)
pos = {m.group(1): (int(m.group(2)) / 1000.0, int(m.group(3)) / 1000.0) for m in comp_re.finditer(d)}

x_min, x_max = x_lo + MARGIN, x_hi - MARGIN - FLOP_W
y_min, y_max = y_lo, y_hi
lines = ["MANUAL_GLOBAL_PLACEMENTS:"]
n = 0
dmin = float("inf")
for key in sorted(stages):
    cp = stages[key]
    if set(cp) != {"a", "b", "c"}:
        sys.exit(f"stage {key} has copies {sorted(cp)}")
    if any(cp[k] not in pos for k in "abc"):
        sys.exit(f"stage {key}: instance missing from DEF")
    cx = sum(pos[cp[k]][0] for k in "abc") / 3.0
    cy = sum(pos[cp[k]][1] for k in "abc") / 3.0
    seeds = {"a": (cx - DX, cy - DY), "b": (cx, cy), "c": (cx + DX, cy + DY)}
    # keep all three inside the core by shifting the whole stage, not by clamping one copy
    shift_x = max(0.0, x_min - seeds["a"][0]) - max(0.0, seeds["c"][0] - x_max)
    shift_y = max(0.0, y_min - seeds["a"][1]) - max(0.0, seeds["c"][1] - y_max)
    for k in "abc":
        x, y = seeds[k]
        lines += [f"  {cp[k]}:", f"    location: [{x + shift_x:.2f}, {y + shift_y:.2f}]", "    orientation: N"]
        n += 1
    dmin = min(dmin, (DX ** 2 + DY ** 2) ** 0.5)
open(out, "w").write("\n".join(lines) + "\n")
print(f"{len(stages)} stages, {n} flops seeded; DX {DX} um, DY {DY} um, seeded copy-to-copy distance "
      f">= {dmin:.1f} um; core x {x_lo:.2f}..{x_hi:.2f}, rows y {y_lo:.2f}..{y_hi:.2f}")
