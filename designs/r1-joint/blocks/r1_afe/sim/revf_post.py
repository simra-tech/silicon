#!/usr/bin/env python3
"""Revision F / layout E3 (track T3): reduce post-layout 'var:' campaigns (specs/make_post_e3.py) against the closure criteria.
  python3 revf_post.py <run-id> [<run-id> ...] [--json out.json]
Criteria: every loop PM >= 63 deg and GM >= 10 dB (rows with pm_valid false are listed, not counted), f_c >= 1.0 MHz,
pole matching |f3 sine/cosine - 1| <= 1 %, output CM 0.600 +- 0.030 V, noise x32 input-referred at ss <= 35 uV,
settling non-linear residual <= 0.25 LSB (linear fit over the input levels per corner and gain), THD <= 0.1 %."""
import json, math, sys, collections
LSB = 1.8 / 4096
args = [a for a in sys.argv[1:] if not a.startswith('--')]
outp = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
if outp in args:
    args.remove(outp)
res = []
for rid in args:
    res += json.load(open('results/%s.json' % rid))
R = collections.OrderedDict(loops=collections.OrderedDict(), fc=collections.OrderedDict(), ocm=collections.OrderedDict(),
                            pole=collections.OrderedDict(), noise=None, settle=collections.OrderedDict(), thd=None, failed=[],
                            invalid=[])
st_pts = collections.defaultdict(list)
for j in res:
    tag = j['name'].split('__', 1)[1]
    rows = j['rows']
    if j['rc'] != 0 or not rows:
        R['failed'].append(tag)
        continue
    st = [r for r in rows if r['tag'] == 'STBROW']
    if st:
        e = {}
        for lp in ('dm1', 'cm1', 'dm2', 'cm2'):
            rr = [r for r in st if r['loop'] == lp]
            ok = [r for r in rr if r['pm_valid']]
            for r in rr:
                if not r['pm_valid']:
                    R['invalid'].append('%s %s x%d pm=%s' % (tag, lp, 2 ** int(r['code']), r['pm_deg']))
            pm = [r['pm_deg'] for r in ok if r['pm_deg'] is not None]
            gm = [r['gm_db'] for r in rr if r['gm_db'] is not None]
            e[lp] = (min(pm) if pm else None, min(gm) if gm else None)
        R['loops'][tag] = e
        continue
    ac = [r for r in rows if r['tag'] == 'ACROW']
    if ac and j.get('mismatch'):
        d = [100 * (r['fs3'] / r['fc3'] - 1) for r in ac if not isinstance(r['fs3'], str)]
        R['pole'].setdefault(j['corner'], []).extend(d)
        continue
    if ac:
        f3 = [min(r['fs3'], r['fc3']) / 1e6 for r in ac if not isinstance(r['fs3'], str)]
        R['fc'][tag] = round(min(f3), 4)
        oc = [r['ocms'] for r in rows if r['tag'] == 'OPROW'] + [r['ocmc'] for r in rows if r['tag'] == 'OPROW']
        if oc:
            R['ocm'][tag] = (round(min(oc), 4), round(max(oc), 4))
        continue
    op = [r for r in rows if r['tag'] == 'OPROW']
    if op:
        oc = [r['ocms'] for r in op] + [r['ocmc'] for r in op]
        R['ocm'][tag] = (round(min(oc), 4), round(max(oc), 4))
        continue
    nz = [r for r in rows if r['tag'] == 'NZROW']
    if nz:
        R['noise'] = {('x%d' % 2 ** int(r['code'])): round(r['in_rms'] * 1e6, 2) for r in nz}
        continue
    th = [r['thd_percent'] for r in rows if r['tag'] == 'THDROW']
    if th:
        R['thd'] = max(R['thd'] or 0, max(th))
        continue
    s = [r for r in rows if r['tag'] == 'STROW']
    if s and not isinstance(s[-1]['err_s'], str):
        tg_ = tag.split('_')
        if tg_[1] == 'vrst06':      # revision F1: settling with a 0.6 V CDAC top-plate reset (information)
            tg_ = [tg_[0], tg_[2] + '-vrst06'] + tg_[3:]
        _, k, g, lv = tg_
        x = {'p100': 1, 'm100': -1, 'p50': 0.5, 'm50': -0.5, 'p25': 0.25}[lv]
        st_pts[(k, g)].append((x, s[-1]['err_s'], s[-1]['err_c']))
for (k, g), pts in sorted(st_pts.items()):
    out = {}
    for ch, ix in (('s', 1), ('c', 2)):
        if len(pts) < 3:
            continue
        n = len(pts); mx = sum(p[0] for p in pts) / n; my = sum(p[ix] for p in pts) / n
        b = sum((p[0] - mx) * (p[ix] - my) for p in pts) / sum((p[0] - mx) ** 2 for p in pts)
        a = my - b * mx
        out[ch] = dict(offset_mV=round(1e3 * a, 4), resid_lsb=round(max(abs(p[ix] - a - b * p[0]) for p in pts) / LSB, 4),
                       total_lsb=round(max(abs(p[ix]) for p in pts) / LSB, 3), n=n)
    R['settle']['%s_%s' % (k, g)] = out
R['pole'] = {k: dict(worst_pct=round(max(abs(x) for x in v), 4), n=len(v)) for k, v in R['pole'].items()}
# verdicts
V = collections.OrderedDict()
pm = [(t, lp, v[0]) for t, e in R['loops'].items() for lp, v in e.items() if v[0] is not None]
gm = [(t, lp, v[1]) for t, e in R['loops'].items() for lp, v in e.items() if v[1] is not None]
if pm:
    w = min(pm, key=lambda q: q[2]); V['PM >= 63'] = ('passed' if w[2] >= 63 else 'failed', '%.2f (%s %s)' % (w[2], w[0], w[1]))
    V['PM fails'] = ['%s %s %.2f' % q for q in pm if q[2] < 63]
if gm:
    w = min(gm, key=lambda q: q[2]); V['GM >= 10'] = ('passed' if w[2] >= 10 else 'failed', '%.2f (%s %s)' % (w[2], w[0], w[1]))
    V['GM fails'] = ['%s %s %.2f' % q for q in gm if q[2] < 10]
if R['fc']:
    w = min(R['fc'].items(), key=lambda q: q[1]); V['f_c >= 1.0'] = ('passed' if w[1] >= 1.0 else 'failed', '%.4f MHz (%s)' % (w[1], w[0]))
if R['ocm']:
    lo = min(R['ocm'].items(), key=lambda q: q[1][0]); hi = max(R['ocm'].items(), key=lambda q: q[1][1])
    V['OCM 0.57-0.63'] = ('passed' if lo[1][0] >= 0.57 and hi[1][1] <= 0.63 else 'failed', '%.4f (%s) .. %.4f (%s)' % (lo[1][0], lo[0], hi[1][1], hi[0]))
if R['pole']:
    w = max(v['worst_pct'] for v in R['pole'].values()); V['pole <= 1 %'] = ('passed' if w <= 1 else 'failed', R['pole'])
if R['noise']:
    V['noise x32 ss <= 35'] = ('passed' if R['noise'].get('x32', 99) <= 35 else 'failed', R['noise'])
if R['settle']:
    w = max(v['resid_lsb'] for d in R['settle'].values() for v in d.values())
    V['settle resid <= 0.25 LSB'] = ('passed' if w <= 0.25 else 'failed', w)
if R['thd'] is not None:
    V['THD <= 0.1 %'] = ('passed' if R['thd'] <= 0.1 else 'failed', R['thd'])
R['verdict'] = V
if outp:
    json.dump(R, open(outp, 'w'), indent=1)
for k in ('loops', 'fc', 'ocm', 'pole', 'noise', 'settle', 'thd', 'failed', 'invalid'):
    v = R[k]
    if isinstance(v, dict) and k == 'loops':
        print('loops (PM/GM):')
        for t, e in v.items():
            print('  %-28s %s' % (t, '  '.join('%s %s/%s' % (lp, *x) for lp, x in e.items())))
    else:
        print(k, v)
print('VERDICT')
for k, v in V.items():
    print('  %-26s %s' % (k, v))
