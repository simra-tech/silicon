#!/usr/bin/env python3
"""T2o (D28 item 3): regeneration time after the strobe against the input, from the gen_regen.py runs.
Strobe = 50 % rising crossing of the ideal clock (16.69 ns). r1_cmp4 (a, b): regenerated when min(outp, outn) < VDD/2;
r1_cmp5n (c, d): when max(outp, outn) > VDD/2. Output JSON: per run, vd -> t_reg - t_strobe (ns; null = not by 33.3 ns
after the strobe) and the sign check (outp side = sign of vd).
usage: post_regen.py OUT.json run_id [run_id ...]"""
import json, os, sys
import numpy as np
root = os.environ["G1_RESULTS_ROOT"]
out, rids = sys.argv[1], sys.argv[2:]
res = {}
for rid in rids:
    d = os.path.join(root, "r1_adc", rid)
    vd = [float(x) for x in open(os.path.join(d, "vd.txt")).read().split()]
    A = np.loadtxt(os.path.join(d, "regen.txt"), skiprows=1)
    t, ck = A[:, 0], A[:, 1]
    vdd = ck.max()
    def cross(y, th, t0, rising):
        m = t >= t0
        tt, yy = t[m], y[m]
        idx = np.nonzero(yy >= th)[0] if rising else np.nonzero(yy <= th)[0]
        if not idx.size:
            return None
        i = idx[0]
        if i == 0:
            return float(tt[0])
        return float(tt[i - 1] + (th - yy[i - 1]) * (tt[i] - tt[i - 1]) / (yy[i] - yy[i - 1]))
    ts = cross(ck, vdd / 2, 10e-9, True)
    tend = ts + 33.0e-9
    r4, r5 = {}, {}
    for i, v in enumerate(vd):
        a, b, c, dd = A[:, 2 + 4 * i], A[:, 3 + 4 * i], A[:, 4 + 4 * i], A[:, 5 + 4 * i]
        tr = cross(np.minimum(a, b), vdd / 2, ts, False)
        win = None
        if tr is not None and tr < tend:
            win = 'p' if np.interp(tr + 1e-9, t, a) > np.interp(tr + 1e-9, t, b) else 'n'
        r4['%.3g' % v] = dict(t_ns=None if (tr is None or tr > tend) else round((tr - ts) * 1e9, 3), out_high=win)
        tr = cross(np.maximum(c, dd), vdd / 2, ts, True)
        win = None
        if tr is not None and tr < tend:
            win = 'p' if np.interp(tr + 1e-9, t, c) > np.interp(tr + 1e-9, t, dd) else 'n'
        r5['%.3g' % v] = dict(t_ns=None if (tr is None or tr > tend) else round((tr - ts) * 1e9, 3), out_high=win)
    res[rid] = dict(strobe_ns=round(ts * 1e9, 3), vdd=round(float(vdd), 3), r1_cmp4=r4, r1_cmp5n=r5)
    print(rid, 'strobe %.2f ns' % (ts * 1e9))
    for nm, r in (('cmp4', r4), ('cmp5n', r5)):
        print('  %-6s' % nm, ' '.join('%s:%s' % (k, r[k]['t_ns']) for k in r))
json.dump({"tool": "sim/post/b9/post_regen.py", "label": "simulated, schematic comparator cells (netlist of record), ideal clock",
           "runs": res}, open(out, "w"), indent=1)
