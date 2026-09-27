#!/usr/bin/env python3
"""Block qualification 2026-09-27: mismatch-enabled copy of a post-layout g1_trip netlist and per-seed wrappers.
  python3 mm_netlist.py <in.spice> <outdir> <seed> [<seed> ...]
writes <outdir>/g1_trip_mm.spice: the input with ' mm_ok=1' appended to every MOS instance line (XM... sg13_{lv,hv}_{n,p}mos),
nothing else changed; and <outdir>/seed<N>.spice = '.option seed=<N>' + '.include <outdir>/g1_trip_mm.spice'.
With the PDK's mos_<corner>_mismatch libraries (cornerMOSlv.lib / cornerMOShv.lib) every device then draws its own
delvto / factuo / w / l from agauss() (sg13g2_mos{lv,hv}_mod_mismatch.lib); the draw is fixed by the seed option, which
ngspice reads before parameter evaluation (checked: same seed -> same draws, different seed -> different draws).
With the plain mos_<corner> libraries the flag is ignored (nominal devices)."""
import os, sys
src, out = sys.argv[1:3]
seeds = [int(s) for s in sys.argv[3:]]
os.makedirs(out, exist_ok=True)
n, lines = 0, []
for ln in open(src).read().split('\n'):
    t = ln.split()
    if t and t[0].startswith('XM') and len(t) > 5 and t[5] in ('sg13_lv_nmos', 'sg13_lv_pmos', 'sg13_hv_nmos', 'sg13_hv_pmos'):
        assert 'mm_ok' not in ln
        ln += ' mm_ok=1'; n += 1
    lines.append(ln)
mm = os.path.join(out, 'g1_trip_mm.spice')
open(mm, 'w').write('\n'.join(lines))
for s in seeds:
    open(os.path.join(out, 'seed%d.spice' % s), 'w').write('* mismatch seed %d\n.option seed=%d\n.include %s\n' % (s, s, mm))
print('flagged', n, 'MOS; wrote', mm, 'and', len(seeds), 'seed wrappers')
