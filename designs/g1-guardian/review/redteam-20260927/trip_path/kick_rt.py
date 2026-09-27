#!/usr/bin/env python3
"""Red-team 2026-09-27 trip_path: bracket the effective hard/soft trip point of G1_TRIP on a (variant of the)
NF4 kpex netlist with the strobe-train bench, same criterion as blocks/g1_trip/sim/postlayout/kick_threshold.py
(4 strobes per comparator, strobes k=1..3 read 50 ns after the edge, trip = >=2 of 3 high; bisection to 1 LSB),
but with the strobe period, VDDA and resistor corner as parameters.
  python3 kick_rt.py worker <cpu> <outdir> <queue>     queue line: tag net mos vdd temp cond hc sc per_ns [vdda res guess]
  python3 kick_rt.py table <outdir>
Each ngspice run goes through flow/run.sh with G1_CPUSET=<cpu> (container, pinned)."""
import json, os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, *['..'] * 5))
TMPL = open(os.path.join(HERE, 'tb_kick_rt.cir.tmpl')).read()

def run(cpu, out, c, ud):
    tag, net, mos, vdd, temp, cond, hc, sc, per, vdda, res = c
    per = float(per)
    name = 'k_%s_%s_%sV_%sC_%s_h%s_s%s_p%g_a%s_%s_ud%s' % (tag, mos, vdd, temp, cond, hc, sc, per, vdda, res, ud)
    bits = []
    for b in range(8):
        bits.append('Vs%d s%d 0 dc %s' % (b, b, '{VDD}' if (int(sc) >> b) & 1 else '0'))
        bits.append('Vh%d h%d 0 dc %s' % (b, b, '{VDD}' if (int(hc) >> b) & 1 else '0'))
    tstop = 20 + 4 * per + 10
    deck = (TMPL.replace('@@VDD@@', vdd).replace('@@PER@@', '%g' % per).replace('@@MOS@@', mos)
            .replace('@@RES@@', res).replace('@@TEMP@@', temp).replace('@@NET@@', net).replace('@@VDDA@@', vdda)
            .replace('@@BITS@@', '\n'.join(bits)).replace('@@COND@@', cond).replace('@@UD@@', str(ud))
            .replace('@@TSTOP@@', '%gn' % tstop).replace('@@OUT@@', os.path.join(out, name + '.dat')))
    open(os.path.join(out, name + '.cir'), 'w').write(deck)
    env = dict(os.environ, G1_CPUSET=str(cpu), G1_CPUS='1', G1_CONTAINER_ENGINE='podman',
               G1_RESULTS_ROOT=os.environ['BULK'], G1_WORKDIR='designs/g1-guardian/blocks/g1_trip/sim')
    with open(os.path.join(out, name + '.log'), 'w') as lf:
        subprocess.run(['timeout', '3600', 'flow/run.sh', 'ngspice', '-b', os.path.join(out, name + '.cir')],
                       cwd=REPO, env=env, stdout=lf, stderr=subprocess.STDOUT)
    try:
        d = np.loadtxt(os.path.join(out, name + '.dat'))
    except Exception:
        rec = dict(cond=c, ud=ud, error=True)
        open(os.path.join(out, 'results.jsonl'), 'a').write(json.dumps(rec) + '\n')
        return None
    t = d[:, 0]
    q = d[:, 9] if cond == 'soft' else d[:, 11]
    soft_first = (cond == 'soft') != ('swap' in tag)
    t0 = 20e-9 if soft_first else 20e-9 + per * 0.5e-9
    hi = [bool(np.interp(t0 + k * per * 1e-9 + min(50e-9, per * 0.4e-9), t, q) > float(vdd) / 2) for k in (1, 2, 3)]
    rec = dict(cond=c, ud=ud, high=hi, trip=sum(hi) >= 2, mixed=len(set(hi)) > 1)
    open(os.path.join(out, 'results.jsonl'), 'a').write(json.dumps(rec) + '\n')
    return rec['trip']

def bracket(cpu, out, c, guess):
    res = {}
    def T(u):
        if u not in res: res[u] = run(cpu, out, c, u)
        return res[u]
    lo = hi = None
    step = 4
    r = T(guess)
    if r is None: return dict(cond=c, N=None, error=True, runs=res)
    if r:
        lo = guess
        while hi is None and lo + step <= 200:
            r = T(lo + step)
            if r is None: return dict(cond=c, N=None, error=True, runs=res)
            if r: lo += step
            else: hi = lo + step
            step *= 2
    else:
        hi = guess
        while lo is None and hi - step >= -60:
            r = T(hi - step)
            if r is None: return dict(cond=c, N=None, error=True, runs=res)
            if r: lo = hi - step
            else: hi -= step
            step *= 2
    if lo is None or hi is None: return dict(cond=c, N=None, lo=lo, hi=hi, runs=res)
    while hi - lo > 1:
        m = (lo + hi) // 2
        r = T(m)
        if r is None: return dict(cond=c, N=None, error=True, runs=res)
        if r: lo = m
        else: hi = m
    return dict(cond=c, N=lo, runs={str(k): v for k, v in sorted(res.items())})

def worker(cpu, out, queue):
    for i, line in enumerate(open(queue)):
        c = line.split()
        if not c or c[0].startswith('#'): continue
        c += ['3.3', 'res_typ', '40'][len(c) - 9:] if len(c) < 12 else []
        guess = int(c[11]); c = c[:11]
        try: os.mkdir(os.path.join(out, 'claim_%03d' % i))
        except FileExistsError: continue
        r = bracket(cpu, out, c, guess)
        open(os.path.join(out, 'brackets.jsonl'), 'a').write(json.dumps(r) + '\n')

def points(cpu, out, queue):
    # queue line: tag net mos vdd temp cond hc sc per vdda res ud   (one run per line)
    for i, line in enumerate(open(queue)):
        c = line.split()
        if not c or c[0].startswith('#'): continue
        try: os.mkdir(os.path.join(out, 'pclaim_%03d' % i))
        except FileExistsError: continue
        run(cpu, out, c[:11], int(c[11]))

def ptable(out):
    rows = {}
    for l in open(os.path.join(out, 'results.jsonl')):
        r = json.loads(l)
        k = tuple(r['cond'][:1] + r['cond'][2:])
        rows.setdefault(k, []).append((r['ud'], 'ERR' if r.get('error') else ('T' if r['trip'] else 'n') + ('*' if r['mixed'] else '')))
    for k in sorted(rows):
        print(' '.join(k), ' '.join('%s:%s' % x for x in sorted(rows[k])))

def table(out):
    for l in open(os.path.join(out, 'brackets.jsonl')):
        r = json.loads(l)
        tag, net, mos, vdd, temp, cond, hc, sc, per, vdda, res = r['cond']
        code = int(hc if cond == 'hard' else sc)
        n = r['N']
        s = 'n/a' if n is None else '%3d - %3d LSB (%+.2f mV shunt)' % (code, n, -n * 0.1962)
        print('%-10s %-4s %-6s %5sV %4sC per %4sns vdda %s %s  %s  runs %s' % (tag, cond, mos, vdd, temp, per, vdda, res, s, r.get('runs')))

if __name__ == '__main__':
    if sys.argv[1] == 'worker': worker(int(sys.argv[2]), sys.argv[3], sys.argv[4])
    elif sys.argv[1] == 'points': points(int(sys.argv[2]), sys.argv[3], sys.argv[4])
    elif sys.argv[1] == 'ptable': ptable(sys.argv[2])
    else: table(sys.argv[2])
