import pya, sys
lvs = pya.LayoutVsSchematic()
lvs.read(globals().get("db", "build/scratch/lvs1200/run_deep/g1_chip_top.lvsdb"))
x = lvs.xref()
stat = {pya.NetlistCrossReference.Match: "Match", pya.NetlistCrossReference.MatchWithWarning: "MatchWarn",
        pya.NetlistCrossReference.Mismatch: "MISMATCH", pya.NetlistCrossReference.NoMatch: "NOMATCH",
        pya.NetlistCrossReference.Skipped: "Skipped", pya.NetlistCrossReference.None_: "None"}
for cp in x.each_circuit_pair():
    a, b = cp.first(), cp.second()
    name = (a.name if a else "-") + " | " + (b.name if b else "-")
    st = stat.get(cp.status(), str(cp.status()))
    if st.startswith("Match") and "chip_top" not in name:
        print(f"{st:10s} {name}"); continue
    print(f"{st:10s} {name}")
    bad_nets = [(n.first().name if n.first() else "-", n.second().name if n.second() else "-", stat.get(n.status(), "?"))
                for n in x.each_net_pair(cp) if n.status() not in (pya.NetlistCrossReference.Match, pya.NetlistCrossReference.MatchWithWarning)]
    bad_dev = [((d.first().expanded_name() if d.first() else "-"), (d.second().expanded_name() if d.second() else "-"), stat.get(d.status(), "?"))
               for d in x.each_device_pair(cp) if d.status() not in (pya.NetlistCrossReference.Match, pya.NetlistCrossReference.MatchWithWarning)]
    bad_pins = [((p.first().name() if p.first() else "-"), (p.second().name() if p.second() else "-"), stat.get(p.status(), "?"))
                for p in x.each_pin_pair(cp) if p.status() not in (pya.NetlistCrossReference.Match, pya.NetlistCrossReference.MatchWithWarning)]
    bad_sub = [((s.first().expanded_name() if s.first() else "-"), (s.second().expanded_name() if s.second() else "-"), stat.get(s.status(), "?"))
               for s in x.each_subcircuit_pair(cp) if s.status() not in (pya.NetlistCrossReference.Match, pya.NetlistCrossReference.MatchWithWarning)]
    print(f"   nets {len(bad_nets)} devices {len(bad_dev)} pins {len(bad_pins)} subckts {len(bad_sub)}")
    for lab, lst in (("net", bad_nets), ("dev", bad_dev), ("pin", bad_pins), ("sub", bad_sub)):
        for t in lst[:25]: print("     ", lab, t)
