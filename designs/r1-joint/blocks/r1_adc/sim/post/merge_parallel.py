#!/usr/bin/env python3
"""Merge identical parallel device instances of a post-layout netlist into one instance with m = count (T2 harness,
2026-10-26). Exact: the instances have the same subcircuit scope, the same nodes in the same order and the same
parameters (except m); a PDK MOS passes m to PSP 'mult', cap_cmim / rppd are multiplied as subcircuits. Why: each PDK
cap_cmim is R 55 mOhm + C; the ~830 unit MIMs of the CDAC (one instance each) make ngspice 14 to more than 28 x slower
than the netlist of record (runs post-fc-tt-lay0, post-dbg-speed). The pex builder (pex/pex_build.py) ties all units of a
CDAC bit to one collector node and one top-plate node, so the units merge in the RC and the C-only netlist alike.
Only X lines are merged (a merged group gets m = sum; an unmerged line is written unchanged); R / C parasitic elements and the order of the other lines are kept. The first instance name
of a group is kept. usage: merge_parallel.py <in.spice> <out.spice>   (prints and writes <out>_merge.json)
"""
import hashlib, json, os, re, sys
src, dst = sys.argv[1], sys.argv[2]
L = open(src).read().splitlines()
# join continuation lines
J = []
for l in L:
    if l.startswith('+') and J:
        J[-1] += ' ' + l[1:].strip()
    else:
        J.append(l)
out, groups, sub = [], {}, None
nin = nout = 0
for l in J:
    t = l.split()
    if t and t[0].lower() == '.subckt':
        sub = t[1]
    if t and t[0][0] in 'Xx' and sub is not None:
        nin += 1
        nodes = [x for x in t[1:] if '=' not in x]
        par = [x for x in t[1:] if '=' in x]
        m = 1
        rest = []
        for x in par:
            k, v = x.split('=', 1)
            if k.lower() == 'm':
                m = int(float(v))
            else:
                rest.append(x)
        key = (sub, tuple(nodes), tuple(rest))
        if key in groups:
            groups[key]['m'] += m
            groups[key]['n'] += 1
            continue
        groups[key] = {'idx': len(out), 'name': t[0], 'nodes': nodes, 'rest': rest, 'm': m, 'n': 1, 'line': l}
        out.append(None)
        continue
    out.append(l)
for g in groups.values():
    # a group of one keeps its line unchanged. Fix 2026-10-26 (found by the layout lead): the first version wrote m=1 on
    # every instance, also on Xslice_a / Xslice_b; in ngspice 46 an m on a subcircuit instance overrides the m of the
    # devices inside, so every merged CDAC MIM became m=1 (runs post-isa-tt-rc-s, post-isa-tt-cm: gain 1.40, codes at
    # the rails).
    out[g['idx']] = g['line'] if g['n'] == 1 else '%s %s %s m=%d' % (g['name'], ' '.join(g['nodes']), ' '.join(g['rest']), g['m'])
    nout += 1
hdr = '* merged by sim/post/merge_parallel.py from %s (sha256 %s): %d -> %d device instances (identical parallel devices as m = count)' % (
    os.path.relpath(src), hashlib.sha256(open(src, 'rb').read()).hexdigest()[:16], nin, nout)
open(dst, 'w').write('\n'.join([hdr] + out) + '\n')
rep = {'source': os.path.relpath(src), 'source_sha256': hashlib.sha256(open(src, 'rb').read()).hexdigest(),
       'out': os.path.relpath(dst), 'out_sha256': hashlib.sha256(open(dst, 'rb').read()).hexdigest(),
       'instances_in': nin, 'instances_out': nout, 'groups_merged': sum(1 for g in groups.values() if g['n'] > 1)}
json.dump(rep, open(dst.replace('.spice', '_merge.json'), 'w'), indent=1)
print(json.dumps(rep))
