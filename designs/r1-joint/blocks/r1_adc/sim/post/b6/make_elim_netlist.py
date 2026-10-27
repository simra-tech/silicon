#!/usr/bin/env python3
"""T2l (layout B6, 2026-10-27): elimination variants of a merged post-layout RC netlist for the top-plate offset.
Diagnostic netlists only (not design netlists). Two operations on the slice subcircuit r1_adc_slice_post:

  --cut NETS      every extracted coupling capacitor (Cp*) between top_p / top_n and a net in NETS is moved to gnd on
                  both nets (same total load on both nets, no coupling). NETS: comma list of net names (the net of a
                  node is its name without the __p<k> / __i<k> suffix).
  --cut-all       the same for every net except gnd.
  --victims V     comma list of victim nets instead of top_p,top_n (T2l dev3 diagnostics; the moved-coupling print
                  then gives the first victim / all others)
  --balance PAIRS for each pair P:N (comma list) add one capacitor to gnd on the side with the smaller total extracted
                  capacitance so both totals are equal (tests a load imbalance, e.g. lsb_p:lsb_n, op:on).

usage: make_elim_netlist.py IN.spice OUT.spice [--cut a,b] [--cut-all] [--balance p:n,...]
Prints the moved couplings per net (fF, top_p / top_n) and the added balance capacitors.
"""
import collections, re, sys

src, out = sys.argv[1], sys.argv[2]
opt = sys.argv[3:]
cut, cutall, bal, VICT = set(), False, [], ("top_p", "top_n")
for i, o in enumerate(opt):
    if o == "--cut":
        cut = set(opt[i + 1].split(","))
    if o == "--cut-all":
        cutall = True
    if o == "--victims":
        VICT = tuple(opt[i + 1].split(","))
    if o == "--balance":
        bal = [tuple(p.split(":")) for p in opt[i + 1].split(",")]
net = lambda n: re.sub(r"__[pi]\d+$", "", n)
fv = lambda s: float(s.replace("f", "e-15")) if s.endswith("f") else float(s)
txt = open(src).read()
m = re.search(r"^\.subckt r1_adc_slice_post.*?^\.ends", txt, re.S | re.M)
body = m.group(0).split("\n")
tot = collections.defaultdict(float)
for ln in body:
    if re.match(r"C\w+ ", ln):
        t = ln.split()
        try:
            v = fv(t[3])
        except ValueError:
            continue
        tot[net(t[1])] += v
        tot[net(t[2])] += v
moved = collections.defaultdict(lambda: [0.0, 0.0])
new = []
for ln in body:
    if re.match(r"Cp\d+ ", ln):
        t = ln.split()
        a, b = net(t[1]), net(t[2])
        for x, y, nx, ny in ((a, b, t[1], t[2]), (b, a, t[2], t[1])):
            if x in VICT and y not in VICT and y != "gnd" and (cutall or y in cut):
                moved[y][0 if x == VICT[0] else 1] += fv(t[3])
                new.append("%s %s gnd %s" % (t[0], nx, t[3]))
                new.append("%sx %s gnd %s" % (t[0], ny, t[3]))
                break
        else:
            new.append(ln)
        continue
    if ln.startswith(".ends"):
        for k, (p, n) in enumerate(bal):
            d = tot[p] - tot[n]
            side = n if d > 0 else p
            new.append("Cbal%d %s gnd %.6gf" % (k, side, abs(d) * 1e15))
            print("balance %s/%s: %.3f / %.3f fF, +%.3f fF on %s" % (p, n, tot[p] * 1e15, tot[n] * 1e15, abs(d) * 1e15, side))
    new.append(ln)
for k, (p, n) in sorted(moved.items()):
    print("cut %-10s top_p %.3f fF top_n %.3f fF diff %+.3f" % (k, p * 1e15, n * 1e15, (p - n) * 1e15))
dp = sum(v[0] for v in moved.values()); dn = sum(v[1] for v in moved.values())
hdr = ("* T2l diagnostic (not a design netlist): %s with %s. Written by sim/post/b6/make_elim_netlist.py.\n"
       "* moved couplings: top_p %.3f fF, top_n %.3f fF (diff %+.3f fF)\n" % (
           src.split("/")[-1], " ".join(opt), dp * 1e15, dn * 1e15, (dp - dn) * 1e15))
open(out, "w").write(hdr + txt[:m.start()] + "\n".join(new) + txt[m.end():])
print(hdr.strip())
