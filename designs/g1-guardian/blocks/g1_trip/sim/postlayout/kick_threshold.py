#!/usr/bin/env python3
"""Bracket the effective trip point of the soft or hard path with the strobe-train bench.

Host-side driver (runs each ngspice in the pinned container through flow/run.sh):
  python3 kick_threshold.py worker <cpu> <outdir> <queue file>
  python3 kick_threshold.py table <outdir>
Queue lines: "<tag> <mos> <vdd> <temp> <soft|hard> <hard code> <soft code> [guess]" (tag old|nf4, or a
make_variant.py netlist <variants dir>/g1_trip_<tag>.spice with KT_VARIANTS=<variants dir>). With a guess the
coarse search starts there and steps outwards by 4, 8, 16, ... LSB until it brackets, then bisects. Each worker
claims a line (mkdir lock) and brackets it. A run is 0.8 us (4 strobes of each comparator); the decisions
of strobes k = 1..3 (the first is skipped) are read 50 ns after the edge; the run "trips" when at least 2
of 3 are high, and "mixed" when the 3 are not identical. Coarse underdrives (LSB of VREF/530 below the DC
threshold): hard 8, 12, 16, 24, 32, 48 (then 64, 96) upward until the first no-trip, with 1 known to trip
from the 21-strobe runs (checked downward if 8 does not trip); soft 0, then 2, 4, 8, 16 or -2, -4, -8, -16.
Then bisection to 1 LSB: the effective trip point is "code - N", N the largest underdrive that trips
(threshold between N and N+1 LSB below the DC code value). Shunt-referred: 1 LSB = 0.196 mV.
"""
import json
import os
import subprocess
import sys
import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), *['..'] * 6))
NET = {'old': 'postlayout/g1_trip_pex.spice', 'nf4': 'postlayout/g1_trip_nf4_pex.spice'}


def run(cpu, out, c, ud):
    tag, mos, vdd, temp, cond, hc, sc = c
    env = dict(os.environ, G1_CPUSET=str(cpu), G1_CPUS='1', G1_CONTAINER_ENGINE='podman',
               G1_RESULTS_ROOT=os.environ['BULK'], G1_WORKDIR='designs/g1-guardian/blocks/g1_trip/sim')
    net = NET.get(tag) or os.path.join(os.environ['KT_VARIANTS'], 'g1_trip_%s.spice' % tag)
    subprocess.run(['timeout', '7200', 'flow/run.sh', 'bash', 'postlayout/run_kick_train.sh', net, tag, mos, vdd,
                    temp, cond, out, str(ud), '0.8u', hc, sc], cwd=REPO, env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    name = 'kick_%s_%s_%sV_%sC' % (tag, mos, vdd, temp)
    if hc != '254': name += '_h' + hc
    if sc != '153': name += '_s' + sc
    if str(ud) != '1': name += '_ud%s' % ud
    name += '_' + cond
    d = np.loadtxt(os.path.join(out, name + '.dat'))
    t = d[:, 0]
    q = d[:, 9] if cond == 'soft' else d[:, 11]
    t0 = 20e-9 if cond == 'soft' else 120e-9
    hi = [bool(np.interp(t0 + k * 200e-9 + 50e-9, t, q) > float(vdd) / 2) for k in (1, 2, 3)]
    rec = dict(cond=c, ud=ud, high=hi, trip=sum(hi) >= 2, mixed=len(set(hi)) > 1)
    with open(os.path.join(out, 'results.jsonl'), 'a') as f:
        f.write(json.dumps(rec) + '\n')
    return rec['trip']


def bracket(cpu, out, c, guess=None):
    res = {}
    def T(u):
        if u not in res: res[u] = run(cpu, out, c, u)
        return res[u]
    lo = hi = None
    if guess is not None:
        step = 4
        if T(guess):
            lo = guess
            while hi is None and lo + step <= 160:
                if T(lo + step): lo += step
                else: hi = lo + step
                step *= 2
        else:
            hi = guess
            while lo is None and hi - step >= -40:
                if T(hi - step): lo = hi - step
                else: hi -= step
                step *= 2
    elif c[4] == 'hard':
        up, down = [8, 12, 16, 24, 32, 48, 64, 96], [4, 1, -4, -16]
        first = up[0]
    else:
        up, down = [2, 4, 8, 16], [-2, -4, -8, -16]
        first = 0
    if guess is not None:
        pass
    elif T(first):
        lo = first
        for u in (up if c[4] == 'soft' else up[1:]):
            if T(u): lo = u
            else: hi = u; break
    else:
        hi = first
        for u in down:
            if T(u): lo = u; break
            hi = u
    if lo is None or hi is None:
        return dict(cond=c, N=None, lo=lo, hi=hi, runs=res)
    while hi - lo > 1:
        m = (lo + hi) // 2
        if T(m): lo = m
        else: hi = m
    return dict(cond=c, N=lo, runs={str(k): v for k, v in sorted(res.items())})


def worker(cpu, out, queue):
    for i, line in enumerate(open(queue)):
        c = line.split()
        if len(c) not in (7, 8): continue
        guess = int(c[7]) if len(c) == 8 else None
        c = c[:7]
        try:
            os.mkdir(os.path.join(out, 'claim_%02d' % i))
        except FileExistsError:
            continue
        r = bracket(cpu, out, c, guess)
        with open(os.path.join(out, 'brackets.jsonl'), 'a') as f:
            f.write(json.dumps(r) + '\n')


def table(out):
    rows = [json.loads(l) for l in open(os.path.join(out, 'brackets.jsonl'))]
    mixed = {}
    for l in open(os.path.join(out, 'results.jsonl')):
        r = json.loads(l)
        if r['mixed']: mixed.setdefault(tuple(r['cond']), []).append(r['ud'])
    for r in sorted(rows, key=lambda r: (r['cond'][4], r['cond'][5], r['cond'][0], r['cond'][1])):
        tag, mos, vdd, temp, cond, hc, sc = r['cond']
        code = int(hc if cond == 'hard' else sc)
        n = r['N']
        s = 'n/a' if n is None else 'code %d - %d LSB (%+.2f mV shunt)' % (code, n, -n * 0.1962)
        print('%-4s %-4s code %3d %-6s %5sV %4sC  trip point %s  runs %s  mixed at %s'
              % (cond, tag, code, mos, vdd, temp, s, r['runs'], mixed.get(tuple(r['cond']), [])))


if __name__ == '__main__':
    if sys.argv[1] == 'worker':
        worker(int(sys.argv[2]), sys.argv[3], sys.argv[4])
    else:
        table(sys.argv[2])
