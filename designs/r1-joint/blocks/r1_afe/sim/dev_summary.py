#!/usr/bin/env python3
"""Revision-D development sweeps (campaign dev:<kind>:<variants>): per-variant summary on stdout.
Usage (block sim/ dir, host python3): python3 dev_summary.py <run-id>  (reads results/<run-id>.json and the
settling/noise rows; LSB = 1.8 V / 4096, D16)."""
import json, re, sys
LSB = 1.8 / 4096
res = json.load(open('results/%s.json' % sys.argv[1]))
V = {}
for j in res:
    m = re.match(r'^(.*?)_(ac|stb|st|noise)_(.*)$', j['name'])
    vn, kind = m.group(1), m.group(2)
    d = V.setdefault(vn, {})
    for r in j['rows']:
        if r['tag'] == 'OPROW':
            d.setdefault('ocm', []).append(r['ocms']); d.setdefault('idd', []).append(r['idd'] * 1e3)
        elif r['tag'] == 'ACROW':
            d.setdefault('f3', []).append((min(r['fs3'], r['fc3']) / 1e6, j['name'], int(r['code'])))
            d.setdefault('gain', {}).setdefault(j['corner'], {})[int(r['code'])] = 10 ** (r['gs0'] / 20)
        elif r['tag'] == 'STBROW':
            pm = r['pm_deg'] if r['pm_deg'] is not None else 999
            key = r['loop'] + '_x%d' % 2 ** int(r['code'])
            cur = d.setdefault('stb', {}).get(key)
            if cur is None or pm < cur[0]:
                d['stb'][key] = (pm, r['gm_db'], round((r['f_unity'] or 0) / 1e6, 1), m.group(3))
        elif r['tag'] == 'STROW':
            d.setdefault('st', {})[j['name']] = r
        elif r['tag'] == 'NZROW' and int(r['code']) in (0, 5):
            d.setdefault('nz', {})['%s_x%d' % (j['corner'], 2 ** int(r['code']))] = (
                round(r['in_rms'] * 1e6, 2), round(r['onoise_rms'] * 1e6, 1), round(r['onoise_rms'] / LSB, 3))
    if j['rc'] != 0 or not j['rows']:
        d.setdefault('failed', []).append(j['name'])
for vn, d in V.items():
    print('==', vn)
    if 'ocm' in d:
        print('  ocm %.4f-%.4f V   idd %.2f-%.2f mA' % (min(d['ocm']), max(d['ocm']), min(d['idd']), max(d['idd'])))
    if 'f3' in d:
        f = min(d['f3']); print('  f3 min %.3f MHz (%s code %d)' % f)
        for c, g in d['gain'].items():
            print('  gain %s x1 %.4f x32 %.3f' % (c, g.get(0, 0), g.get(5, 0)))
    for k in sorted(d.get('stb', {})):
        print('  %-9s PM %6.1f GM %s fu %s MHz  (%s)' % ((k,) + d['stb'][k]))
    if 'st' in d:
        for n, r in sorted(d['st'].items()):
            r2 = [x for x in res if x['name'] == n][0]['rows']
            last = [x for x in r2 if x['tag'] == 'STROW'][-1]
            print('  %-28s vout0 %+.4f err %+.3f LSB (cos %+.3f)' % (n, last['vout0'], last['err_s'] / LSB, last['err_c'] / LSB))
    for k, v in sorted(d.get('nz', {}).items()):
        print('  noise %s in %s uV, out %s uV = %s LSB' % ((k,) + v))
    if d.get('failed'):
        print('  FAILED JOBS', d['failed'])
