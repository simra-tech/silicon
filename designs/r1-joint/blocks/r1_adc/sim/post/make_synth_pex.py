#!/usr/bin/env python3
"""Synthetic parasitic files for the run-time estimate of the post-layout runs (T2 harness, 2026-10-26). NOT an
extraction: random capacitors on the real net names of layout/r1_adc_netlist.py, so that make_sim_netlist.py --pex-slice /
--pex-top builds a netlist of the expected size (about 10^4 capacitors; option: dangling RC ladders as a stand-in
for reduced RC networks). Written to sim/post/scratch/ (regenerable test input, not evidence, not for commit).
usage: make_synth_pex.py <tag> <C per slice> <C top> <R ladders per slice> <R ladders top> [ladder length 10]
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(BLOCK, 'layout'))
import r1_adc_netlist as N   # noqa: E402
tag, ncs, nct, nrs, nrt = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
klad = int(sys.argv[6]) if len(sys.argv) > 6 else 10
rng = np.random.RandomState(7)
sl = sorted(set(N.SLICE_PORTS) | set(n for d in N.slice_devices(N.NDUMMY) for n in d['nets']))
tp = sorted(set(n for d in N.top_devices() for n in d['nets']) | {'vref', 'vrefl', 'vdd', 'vss', 'vdda'})
os.makedirs(os.path.join(HERE, 'scratch'), exist_ok=True)


def write(fn, nets, gnd, nc, nr):
    L = ['* synthetic parasitics (make_synth_pex.py, seed 7): %d C, %d RC ladders of %d' % (nc, nr, klad)]
    for k in range(nc):
        a = nets[rng.randint(len(nets))]
        b = gnd if rng.rand() < 0.6 else nets[rng.randint(len(nets))]
        L.append('C%d %s %s %.3gf' % (k, a, 'VSUBS' if b == gnd else b, float(np.exp(rng.normal(np.log(0.15), 0.8)))))
    for j in range(nr):
        a = nets[rng.randint(len(nets))]
        prev = a
        for i in range(klad):
            n = 'lad%d_%d' % (j, i)
            L.append('Rl%d_%d %s %s %.3g' % (j, i, prev, n, float(rng.uniform(1, 20))))
            L.append('Cl%d_%d %s VSUBS %.3gf' % (j, i, n, 0.1))
            prev = n
    open(fn, 'w').write('\n'.join(L) + '\n')
    return fn


fs = write(os.path.join(HERE, 'scratch', 'synth_%s_slice.spice' % tag), sl, 'gnd', ncs, nrs)
ft = write(os.path.join(HERE, 'scratch', 'synth_%s_top.spice' % tag), tp, 'vss', nct, nrt)
print(os.path.relpath(fs, BLOCK), os.path.relpath(ft, BLOCK))
