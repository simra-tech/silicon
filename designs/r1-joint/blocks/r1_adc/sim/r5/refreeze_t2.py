#!/usr/bin/env python3
"""T2 2026-10-21: regenerate the revision-5 library with the r1_refbuf5 bias pin and renew the campaign freeze.
Checks that the new schematic/r1_adc_r5.spice differs from the committed one only inside r1_refbuf5 (port list, the
removed internal Ibias, comment lines) and the same for r1_adc_r5_mm.spice; then writes sim/r5/FROZEN_NETLIST_SHA256.txt
with the new hashes (the previous freeze is kept as a comment). Exit 1 on any other difference."""
import difflib
import hashlib
import os
import subprocess
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
subprocess.check_call([sys.executable, os.path.join(BLOCK, "schematic", "gen_r1_adc_r5.py")])
ok = True
for n in ("r1_adc_r5.spice", "r1_adc_r5_mm.spice"):
    rel = os.path.relpath(os.path.join(BLOCK, "schematic", n), subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=BLOCK).decode().strip())
    old = subprocess.check_output(["git", "show", "HEAD:" + rel], cwd=BLOCK).decode().splitlines()
    new = open(os.path.join(BLOCK, "schematic", n)).read().splitlines()
    d = [l for l in difflib.unified_diff(old, new, lineterm="", n=0) if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    allowed = all(l[1:].startswith("*") or l[1:].startswith(".subckt r1_refbuf5 ") or l[1:].startswith("Ibias vdda nb 5u") for l in d)
    print(n, "changed lines:", len(d), "only r1_refbuf5 port / Ibias / comments:", allowed)
    for l in d:
        print("   ", l[:140])
    ok &= allowed
if not ok:
    sys.exit(1)
fz = os.path.join(HERE, "FROZEN_NETLIST_SHA256.txt")
prev = [l.rstrip("\n") for l in open(fz)]
with open(fz, "w") as f:
    for n in ("r1_adc_r5.spice", "r1_adc_r5_mm.spice"):
        f.write("%s  schematic/%s\n" % (hashlib.sha256(open(os.path.join(BLOCK, "schematic", n), "rb").read()).hexdigest(), n))
    f.write("# renewed 2026-10-21 by T2 (sim/r5/refreeze_t2.py): r1_refbuf5 bias pin nb (coordinator, r1_bias track); "
            "only the r1_refbuf5 port list, its internal Ibias and comments differ from the previous freeze:\n")
    for l in prev:
        f.write("#   previous: " + l.lstrip("# ") + "\n")
print(open(fz).read())
