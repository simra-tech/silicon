#!/usr/bin/env python3
"""Red-team 2026-09-27: simulation-only what-if on g1_trip_nf4_pex.spice ("non-overlapping reset"): each
comparator evaluates on the undelayed clock edge and resets D ns after the other comparator's evaluation edge.
Soft (NF4) clock devices (XM1110-1113, XM1226-1229) -> net soft_ck, hard (regenpair4) clock devices (XM1130-1133,
XM1239-1242) -> net hard_ck, both driven by ideal sources inside the subckt (0.2 ns edges; the extracted cmp_clk /
cmp_clk_n nets keep their parasitics and the clock inverter). Uses the testbench parameters VDD and PER:
  soft_ck: rises at 20n (with cmp_clk), falls at 20n+PER/2+D   (= OR(cmp_clk, cmp_clk delayed D))
  hard_ck: rises at 20n+PER/2 (cmp_clk falling), falls at 20n+PER+D (= NAND(cmp_clk, cmp_clk delayed D))
  python3 make_nov_variant.py <in> <out> <D ns> [softonly]
With "softonly" only the soft comparator is moved (to soft_ck); the hard comparator stays on the extracted
cmp_clk_n from the real clock inverter: the minimal fix "delay only the soft comparator's reset edge"."""
import sys
src, dst, d = sys.argv[1], sys.argv[2], float(sys.argv[3])
softonly = len(sys.argv) > 4 and sys.argv[4] == 'softonly'
soft = {'XM1110', 'XM1111', 'XM1112', 'XM1113', 'XM1226', 'XM1227', 'XM1228', 'XM1229'}
hard = {'XM1130', 'XM1131', 'XM1132', 'XM1133', 'XM1239', 'XM1240', 'XM1241', 'XM1242'}
lines = open(src).read().rstrip('\n').split('\n')
assert lines[-1] == '.ends'
out, n = [], 0
for ln in lines[:-1]:
    t = ln.split()
    if t and t[0] in soft:
        assert t[2] == 'cmp_clk'; t[2] = 'soft_ck'; ln = ' '.join(t); n += 1
    elif t and t[0] in hard and not softonly:
        assert t[2] == 'cmp_clk_n'; t[2] = 'hard_ck'; ln = ' '.join(t); n += 1
    out.append(ln)
assert n == (8 if softonly else 16)
out += ['* make_nov_variant.py D=%g ns' % d,
        'Vsoftck soft_ck vss pulse(0 {VDD} 20n 0.2n 0.2n {PER/2+%gn-0.2n} {PER})' % d,
        ] + ([] if softonly else ['Vhardck hard_ck vss pulse(0 {VDD} {20n+PER/2} 0.2n 0.2n {PER/2+%gn-0.2n} {PER})' % d]) + ['.ends']
open(dst, 'w').write('\n'.join(out) + '\n')
print('wrote', dst)
