# SPDX-License-Identifier: Apache-2.0
"""Circuit-by-circuit summary of a KLayout LVS database.

  klayout -b -rd db=<x.lvsdb> -r xref_summary.py

One line per circuit pair with its status; for pairs that are not a match,
the unmatched nets, devices, pins and subcircuits (first 25 of each) and the
comparer's own message where the database carries one.
"""
import pya

lvs = pya.LayoutVsSchematic()
lvs.read(globals()["db"])
x = lvs.xref()
X = pya.NetlistCrossReference
stat = {X.Match: "Match", X.MatchWithWarning: "MatchWarn", X.Mismatch: "MISMATCH",
        X.NoMatch: "NOMATCH", X.Skipped: "Skipped", X.None_: "None"}
ok = (X.Match, X.MatchWithWarning)
totals = {}
for cp in x.each_circuit_pair():
    a, b = cp.first(), cp.second()
    name = (a.name if a else "-") + " | " + (b.name if b else "-")
    st = stat.get(cp.status(), str(cp.status()))
    totals[st] = totals.get(st, 0) + 1
    if st.startswith("Match"):
        pins = len(list(x.each_pin_pair(cp))); nets = len(list(x.each_net_pair(cp)))
        devs = len(list(x.each_device_pair(cp))); subs = len(list(x.each_subcircuit_pair(cp)))
        print(f"{st:10s} {name}  (pins {pins}, nets {nets}, devices {devs}, subcircuits {subs})")
        continue
    print(f"{st:10s} {name}")
    bad = {
        "net": [((n.first().expanded_name() if n.first() else "-"), (n.second().expanded_name() if n.second() else "-"), stat.get(n.status(), "?"))
                for n in x.each_net_pair(cp) if n.status() not in ok],
        "dev": [((d.first().expanded_name() if d.first() else "-"), (d.second().expanded_name() if d.second() else "-"), stat.get(d.status(), "?"))
                for d in x.each_device_pair(cp) if d.status() not in ok],
        "pin": [((p.first().name() if p.first() else "-"), (p.second().name() if p.second() else "-"), stat.get(p.status(), "?"))
                for p in x.each_pin_pair(cp) if p.status() not in ok],
        "sub": [((s.first().expanded_name() if s.first() else "-"), (s.second().expanded_name() if s.second() else "-"), stat.get(s.status(), "?"))
                for s in x.each_subcircuit_pair(cp) if s.status() not in ok],
    }
    print("   unmatched: nets %d devices %d pins %d subcircuits %d" % tuple(len(bad[k]) for k in ("net", "dev", "pin", "sub")))
    for k in ("net", "dev", "pin", "sub"):
        for t in bad[k][:25]:
            print("     ", k, t)
print("totals:", ", ".join(f"{k} {v}" for k, v in sorted(totals.items())))
