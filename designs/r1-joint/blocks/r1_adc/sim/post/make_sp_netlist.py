#!/usr/bin/env python3
"""make_sp_netlist.py <in.spice> <out.spice> <op run id> [--per-port]: R2-4 base-run netlist for RC netlists (2026-10-26, H12).

In the subckt r1_adc_lay_pr only, the vref / vrefl pins of Xslice_a / Xslice_b are disconnected from the reference
wiring and driven by ideal DC sources (to node 0) at the slice-port values of the buffer OP run (op.txt of <op run id>,
vectors v(xadc.xl.vref__p8/p9), v(xadc.xl.vrefl__p2/p4)). The buffer, its wiring and all supply / ground networks stay as
extracted, so the static supply and ground currents match the buffer run; the slices see a reference without settling
error. Run with --ref lay (normal buffer bias and bandgap) as the base run of post_post.py ref.
Layout B (2026-10-26): each slice has several vref / vrefl port nodes (3 / 2 south pins). Every vref__p<k> / vrefl__p<k>
token on an Xslice line gets its own ideal source (option --per-port) at v(xadc.xl.<token>) of the op run (the op run must print all of
them, --probe-extra). Layout A netlists keep the old behaviour (one source per net and slice, vectors as above)."""
import os, re, sys
src, out, oprun = sys.argv[1:4]
op = {}
for ln in open(os.path.join(os.environ['G1_RESULTS_ROOT'], 'r1_adc', oprun, 'op.txt')):
    m = re.match(r'\s*(\S+)\s*=\s*(\S+)', ln)
    if m:
        op[m.group(1)] = float(m.group(2))
PER_PORT = '--per-port' in sys.argv[4:]
val = {} if PER_PORT else {'a': (op['v(xadc.xl.vref__p8)'], op['v(xadc.xl.vrefl__p2)']), 'b': (op['v(xadc.xl.vref__p9)'], op['v(xadc.xl.vrefl__p4)'])}
L = open(src).read().split('\n')
inpr, done = False, []
for i, ln in enumerate(L):
    if ln.startswith('.subckt r1_adc_lay_pr '):
        inpr = True
    elif ln.startswith('.ends'):
        inpr = False
    elif inpr and re.match(r'Xslice_[ab] ', ln):
        sl = ln[7]
        t = ln.split(' ')
        n = 0
        for j, x in enumerate(t):
            if re.fullmatch(r'vref__p\d+', x):
                t[j] = 'sp_vref_' + sl; n += 1
            elif re.fullmatch(r'vrefl__p\d+', x):
                t[j] = 'sp_vrefl_' + sl; n += 1
        if PER_PORT:
            t = ln.split(' '); srcs = []
            for j, x in enumerate(t):
                if re.fullmatch(r'vrefl?__p\d+', x):
                    t[j] = 'sp_%s_%s' % (x, sl)
                    srcs.append('Vsp_%s_%s sp_%s_%s 0 DC %.6f' % (x, sl, x, sl, op['v(xadc.xl.%s)' % x]))
            L[i] = '\n'.join([' '.join(t)] + srcs)
            print(sl, srcs)
        else:
            assert n == 3, (sl, n)
            L[i] = ' '.join(t) + '\nVsp_vref_%s sp_vref_%s 0 DC %.6f\nVsp_vrefl_%s sp_vrefl_%s 0 DC %.6f' % (
                sl, sl, val[sl][0], sl, sl, val[sl][1])
        done.append(sl)
assert sorted(done) == ['a', 'b'], done
hdr = '* %s: %s with ideal slice references from op run %s (sim/post/make_sp_netlist.py)' % (os.path.basename(out), os.path.basename(src), oprun)
open(out, 'w').write(hdr + '\n' + '\n'.join(L))
print(out, val)
