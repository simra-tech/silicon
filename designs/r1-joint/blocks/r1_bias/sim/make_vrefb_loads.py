#!/usr/bin/env python3
"""Write sim/r1_vrefb_loads.spice: the vref_b consumer loads (revision 2, D20), copied unchanged from the neighbour
netlists of record (sha256 in the header). Run from any directory: python3 make_vrefb_loads.py
  - r1_safe_string: the whole subckt of r1_safe/schematic/r1_safe.spice (252 rppd units of 1 kOhm, taps t0..t252);
  - ld_isped: one r1_isense pedestal arm (XRPB1..XRPB26 and the switch XSPB of r1_isense_ch), pins vref azb sb vss;
    sb is the amplifier summing node (held by the deck), azb the auto-zero complement (high = pedestal on).
r1_t2f is not copied: the decks instantiate the whole r1_t2f netlist with its vref pin on vref_b.
"""
import hashlib, os
HERE = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.dirname(os.path.dirname(HERE))
SAFE = os.path.join(R1, "r1_safe", "schematic", "r1_safe.spice")
ISN = os.path.join(R1, "r1_isense", "schematic", "r1_isense.spice")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def subckt(path, name):
    out, on = [], False
    for l in open(path):
        if l.lower().startswith(".subckt %s " % name):
            on = True
        if on:
            out.append(l.rstrip("\n"))
        if on and l.lower().startswith(".ends"):
            return out
    raise KeyError(name)


s = ["* r1_bias revision 2 vref_b consumer loads (T9, 2026-10-26), written by make_vrefb_loads.py. Do not edit.",
     "* Sources (sha256 at the time of copy):",
     "*   r1_safe   schematic/r1_safe.spice   %s (rev 3): subckt r1_safe_string unchanged" % sha(SAFE),
     "*   r1_isense schematic/r1_isense.spice %s (rev 2): XRPB1..26 and XSPB of r1_isense_ch unchanged" % sha(ISN), ""]
s += subckt(SAFE, "r1_safe_string") + [""]
ch = subckt(ISN, "r1_isense_ch")
arm = [l for l in ch if l.split() and (l.split()[0].startswith("XRPB") or l.split()[0] == "XSPB")]
assert len(arm) == 27, len(arm)
s += ["* one r1_isense pedestal arm: 26 rppd units (104 kOhm) from vref to the switch XSPB into the summing node sb",
      ".subckt ld_isped vref azb sb vss"] + arm + [".ends ld_isped", ""]
open(os.path.join(HERE, "r1_vrefb_loads.spice"), "w").write("\n".join(s) + "\n")
print("wrote r1_vrefb_loads.spice", sha(os.path.join(HERE, "r1_vrefb_loads.spice")))
