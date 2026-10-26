#!/usr/bin/env python3
"""Revision F (track T3): reduce a 'var:' campaign (results/<run-id>.json) per variant and job.
  python3 revf_reduce.py <run-id> [--json]
Per stb job: worst PM and GM per loop (dm1 cm1 dm2 cm2) over the gain codes, with the RHP flag count; per ac job: f_c min
over steps and output CM range; per op job: output CM and differential output (x1, x32); per settle job: error at the
last sample (mV)."""
import json, sys, collections
rid = sys.argv[1]
res = json.load(open('results/%s.json' % rid))
out = collections.OrderedDict()
for j in res:
    vn, tag = j['name'].split('__', 1)
    d = out.setdefault(vn, collections.OrderedDict())
    rows = j['rows']
    if j['rc'] != 0 or not rows:
        d[tag] = 'FAILED rc=%s' % j['rc']
        continue
    st = [r for r in rows if r['tag'] == 'STBROW']
    if st:
        e = {}
        for lp in ('dm1', 'cm1', 'dm2', 'cm2'):
            rr = [r for r in st if r['loop'] == lp]
            if not rr:
                continue
            pm = [r['pm_deg'] for r in rr if r['pm_deg'] is not None]
            gm = [r['gm_db'] for r in rr if r['gm_db'] is not None]
            e[lp] = '%s/%s%s' % (min(pm) if pm else None, min(gm) if gm else None,
                                 '' if all(r['pm_valid'] for r in rr) else '*%d' % sum(1 for r in rr if not r['pm_valid']))
        d[tag] = e
        continue
    ac = [r for r in rows if r['tag'] == 'ACROW']
    if ac:
        f3 = [min(r['fs3'], r['fc3']) / 1e6 for r in ac if not isinstance(r['fs3'], str)]
        oc = [r['ocms'] for r in rows if r['tag'] == 'OPROW']
        d[tag] = dict(fc_min_MHz=round(min(f3), 4), ocm=[round(min(oc), 4), round(max(oc), 4)])
        continue
    op = [r for r in rows if r['tag'] == 'OPROW']
    if op:
        d[tag] = {('x%d' % 2 ** int(r['code'])): dict(ocm=round(r['ocms'], 4), odiff_mV=round(1e3 * r['odiff'], 2)) for r in op}
        continue
    s = [r for r in rows if r['tag'] == 'STROW']
    if s:
        d[tag] = dict(err_mV=round(1e3 * s[-1]['err_s'], 4) if not isinstance(s[-1]['err_s'], str) else None)
        continue
    nz = [r for r in rows if r['tag'] == 'NZROW']
    if nz:
        d[tag] = {('x%d' % 2 ** int(r['code'])): dict(in_uV=round(r['in_rms'] * 1e6, 2), out_uV=round(r['onoise_rms'] * 1e6, 1)) for r in nz}
        continue
    th = [r for r in rows if r['tag'] == 'THDROW']
    if th:
        d[tag] = dict(thd_pct=max(r['thd_percent'] for r in th))
if '--json' in sys.argv:
    print(json.dumps(out, indent=1))
else:
    for vn, d in out.items():
        print('==', vn)
        for t, v in d.items():
            print('   %-28s %s' % (t, v))
