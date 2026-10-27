#!/usr/bin/env python3
"""make_diag_netlist.py <in.spice> <out.spice> [--no-c] [--r-nets n1,n2,...] [--r-scale-nets n1,..:k]
Diagnostic variants of a merged post-layout RC netlist (layout B track, 2026-10-26, step 1 of the layout-B brief):
  --no-c            drop every extracted parasitic capacitor (lines 'Cp<k> ...'); the comparator loads Cld_* stay
  --r-nets LIST     keep the extracted wiring resistors (lines 'Rw<k> ...' slice, 'Rt<k> ...' top) only on the nets in LIST; every other Rw is
                    set to 0.05 Ohm (the topology and the node names stay, so probes and the R2-4 base method still work)
  --tie V           value of the disabled resistors (default 0.05 Ohm; 1e-3 made the OP fail in run postb-diag-isa-tt-rsup)
  --r-scale S:k     multiply the Rw values of the nets in S (comma list) by k (what-if: 'gnd,vdd:0.02')
The net of a node is its name without the '__p<k>' / '__i<k>' suffix (pex_build.py naming). Devices are not changed."""
import re, sys
src, out = sys.argv[1], sys.argv[2]
opt = sys.argv[3:]
noc = '--no-c' in opt
rnets = None; scale = {}; tie = '0.05'
for i, o in enumerate(opt):
    if o == '--r-nets':
        rnets = set(opt[i + 1].split(','))
    if o == '--tie':
        tie = opt[i + 1]
    if o == '--r-scale':
        s, k = opt[i + 1].split(':')
        for n in s.split(','):
            scale[n] = float(k)
def net(n):
    return re.sub(r'__[pi]\d+$', '', n)
nc = nr = nk = 0
L = []
for ln in open(src).read().split('\n'):
    if noc and re.match(r'Cp\d+ ', ln):
        nc += 1; continue
    if re.match(r'R[wt]\d+ ', ln):
        t = ln.split()
        na, nb = net(t[1]), net(t[2])
        if rnets is not None and not (na in rnets or nb in rnets):
            t[3] = tie; nr += 1
        elif na in scale or nb in scale:
            t[3] = '%.6g' % (float(t[3]) * scale.get(na, scale.get(nb))); nk += 1
        ln = ' '.join(t)
    L.append(ln)
hdr = '* %s: diagnostic variant of %s (%s): %d C dropped, %d R set to %s Ohm, %d R scaled' % (
    out.split('/')[-1], src.split('/')[-1], ' '.join(opt), nc, nr, tie, nk)
open(out, 'w').write(hdr + '\n' + '\n'.join(L))
print(hdr)
