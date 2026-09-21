#!/usr/bin/env python3
"""Generate MANUAL_GLOBAL_PLACEMENTS for the three G1_SEU TMR chain copies.

First separation method (run6): one vertical third of the core per copy.
Superseded by tmr_spread.py (run7, the macro of record); kept because the run6
evidence in ../reports/librelane_run6/ was produced with it. See ../README.md,
"TMR copy separation", for why it was replaced (density imbalance, 230 um vote
nets, 81 max-slew violations).

LibreLane 3.1.0.dev2 has no placement-region variable, so the copies are
separated with a floorplan hint: every chain flop of copy a/b/c is given a
global-placement seed in its own vertical band (west / centre / east third of
the core), which Odb.ManualGlobalPlacement applies after global placement and
before legalisation. Detailed placement then keeps each flop near its seed.

The synthesised netlist names flops _NNNN_; the copy is identified from the
net on the flop's Q pin: u_core.u_seu.q<a|b|c>[i] for the chains and
u_core.u_seu.u_<reg>.q<a|b|c>[i] for the TMR control registers (yosys keeps
the copies because their flops carry the 'keep' attribute).

Usage: tmr_columns.py <netlist.nl.v> <out.yaml> [core_x0 core_y0 core_x1 core_y1]
The YAML is included from config.yaml through the 'meta' section or pasted in.
"""
import re
import sys

nl, out = sys.argv[1], sys.argv[2]
core = [float(v) for v in sys.argv[3:7]] if len(sys.argv) >= 7 else [8.0, 8.0, 352.0, 352.0]
x0, y0, x1, y1 = core

text = open(nl).read()
# one instance per statement: "cell name ( .PIN(net), ... );"
inst_re = re.compile(r"\b(sg13g2_\w+)\s+(\S+)\s*\((.*?)\)\s*;", re.S)
q_re = re.compile(r"\.Q\(\s*([^)]+?)\s*\)")
copies = {"a": [], "b": [], "c": []}
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
        copies[mm.group(2)].append((mm.group(1) or "", int(mm.group(3)), name))

n = {k: len(v) for k, v in copies.items()}
if len(set(n.values())) != 1 or n["a"] == 0:
    sys.exit(f"copy sizes differ or empty: {n}")
stages = n["a"]

# three bands: west, centre, east; inside each band a serpentine of rows
band_w = (x1 - x0) / 3.0
site_h = 3.78          # sg13g2 row height (um)
flop_w = 12.96         # sg13g2_dfrbpq_1 width (um), used only for spacing the seeds
margin = 6.0
rows = int((y1 - y0 - 2 * margin) // (site_h * 2))   # every second row keeps the bands sparse
lines = ["MANUAL_GLOBAL_PLACEMENTS:"]
for k, bx in zip("abc", range(3)):
    bx0 = x0 + bx * band_w + margin
    bx1 = x0 + (bx + 1) * band_w - margin
    per_row = max(1, int((bx1 - bx0) // (flop_w * 1.5)))
    for stage, (_reg, _bit, name) in enumerate(sorted(copies[k])):
        r = stage // per_row
        c = stage % per_row
        if r % 2:
            c = per_row - 1 - c
        x = bx0 + c * (bx1 - bx0) / per_row
        y = y0 + margin + (r % rows) * site_h * 2
        lines.append(f"  {name}:")
        lines.append(f"    location: [{x:.2f}, {y:.2f}]")
        lines.append(f"    orientation: N")
open(out, "w").write("\n".join(lines) + "\n")
print(f"{stages} stages per copy, {3 * stages} flops seeded; bands {band_w:.1f} um wide, {rows} rows used")
