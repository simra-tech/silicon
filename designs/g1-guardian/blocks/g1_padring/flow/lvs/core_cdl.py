#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Core-only CDL from the assembled chip CDL: the top subcircuit without the
IO ring cells (sg13g2_IOPad*, sg13g2_Filler*, sg13g2_Corner) and bondpads.
The nets the pads drove (p2c/c2p/padres/padbare terminals) remain as ports
of the core subcircuit, named after the pad nets, so the core-only GDS
(core_only_gds.py labels the same nets at the pad terminals) can be compared.

  python3 core_cdl.py <chip.cdl> <out_core.cdl>
"""
import re
import sys

src, out = sys.argv[1], sys.argv[2]
text = open(src).read()
a = text.index(".SUBCKT g1_chip_top")
b = text.index(".ENDS", a)
top = text[a:b].splitlines()
hdr = top[0].split()
body = top[1:]
ring_re = re.compile(r"/ (sg13g2_IOPad\w+|sg13g2_Filler\d+|sg13g2_Corner|bondpad_70x70\w*)\s*$")
kept, dropped = [], {}
pad_nets = set()
for ln in body:
    m = ring_re.search(ln)
    if m:
        dropped[m.group(1)] = dropped.get(m.group(1), 0) + 1
        toks = ln.split()
        # nets on the pad's core-side terminals: whatever is not a supply/pad port
        for n in toks[1:-2]:
            if n not in ("VDD", "VSS", "IOVDD", "IOVSS") and not n.startswith("_nc"):
                pad_nets.add(n)
        continue
    kept.append(ln)
used = set()
for ln in kept:
    used.update(ln.split()[1:-2])
ports = [p for p in hdr[2:] if p in used or p in ("VDD", "VSS", "VDDA")]
# pad-driven internal nets that are now dangling from the core's point of view: make them ports
extra = sorted(n for n in pad_nets if n in used and n not in ports)
core_ports = ports + extra
with open(out, "w") as f:
    f.write(text[:a])
    f.write(".SUBCKT g1_core " + " ".join(core_ports) + "\n")
    f.write("\n".join(kept) + "\n.ENDS\n")
print("dropped ring instances:", dropped)
print("core ports:", core_ports)
