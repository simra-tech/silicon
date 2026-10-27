# SPDX-License-Identifier: Apache-2.0
"""r1_top try g, filled-chip extraction (track T11b): per-net table, unfilled against filled.

  python3 fill_report.py <cfill.json> <full-chip kpex dir> <checks.json unfilled> <checks.json filled> [<cfill 20 um
      margin json>] > table.md

R: largest pin-to-pin effective resistance of the net (top_checks.py (c), typ sheet; the fill is floating metal and
does not change R). C: total C of the net in the full-chip kpex (unfilled) and with the fill correction of
fill_net.py (filled). Pairs: delta C P - N and the P-N coupling, unfilled and filled.
"""
import csv
import json
import os
import sys
from collections import defaultdict

CF = json.load(open(sys.argv[1]))
K = sys.argv[2]
CU = json.load(open(sys.argv[3]))
CFd = json.load(open(sys.argv[4]))
M20 = json.load(open(sys.argv[5])) if len(sys.argv) > 5 else None
fpair = defaultdict(float)
f = [x for x in os.listdir(K) if x.endswith("_k25d_pex_netlist.csv")][0]
for row in csv.reader(open(os.path.join(K, f)), delimiter=";"):
    if row and row[0].startswith("C"):
        fpair[tuple(sorted((row[1], row[2])))] += float(row[3])
dpair = {tuple(sorted((a, b))): d for a, b, d in CF["pair_delta_fF"]}
RU = {r["net"]: r for r in CU["c_all_nets"]}
RF = {r["net"]: r for r in CFd["c_all_nets"]}
print("| Net | Group | R typ (Ω), unfilled = filled | C unfilled (fF) | C filled (fF) | Delta (fF) | Delta (%) | C in the filled netlist (fF) |")
print("| --- | --- | --- | --- | --- | --- | --- | --- |")
for s in CF["sensitive_nets"]:
    e = CF["nets"][s]
    ru, rf = RU[s]["R_ohm"], RF[s]["R_ohm"]
    assert abs(ru - rf) < 1e-6, s
    print("| `%s` | %s | %.1f | %.2f | %.2f | %+.2f | %+.1f | %.2f |" % (
        s, e["band"], ru, e["C_full_chip_fF"], e["C_filled_fF"], e["delta_fF"], 100 * e["delta_fF"] / e["C_full_chip_fF"],
        RF[s]["C_fF"]))
print()
print("| Pair | ΔR P−N (Ω) | ΔC P−N unfilled (fF) | ΔC P−N filled (fF) | C P–N unfilled (fF) | C P–N filled (fF) |")
print("| --- | --- | --- | --- | --- | --- |")
for p in ("AFE_SOUTS", "AFE_SOUTC", "ISN_OUTA", "ISN_OUTB"):
    a, b = p + "_P", p + "_N"
    k = tuple(sorted((a, b)))
    print("| `%s` | %.2f | %.2f | %.2f | %.2f | %.2f |" % (
        p, RU[a]["R_ohm"] - RU[b]["R_ohm"], RU[a]["C_fF"] - RU[b]["C_fF"], RF[a]["C_fF"] - RF[b]["C_fF"], fpair[k],
        fpair[k] + dpair.get(k, 0.0)))
if M20:
    print()
    print("| Net | Delta, 10 µm band (fF) | Delta, 20 µm band (fF) | Difference (%) |")
    print("| --- | --- | --- | --- |")
    for s, e in sorted(M20["nets"].items()):
        if "clk20" in e and "delta_fF" in e:
            d10, d20 = e["delta_fF"], e["clk20"]["delta_fF"]
            print("| `%s` | %.2f | %.2f | %+.2f |" % (s, d10, d20, 100 * (d20 - d10) / d10))
