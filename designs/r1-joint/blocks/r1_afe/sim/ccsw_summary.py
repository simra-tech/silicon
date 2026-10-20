#!/usr/bin/env python3
"""Worst PM per variant/loop and worst f3 per variant for the ccsw* development sweeps. Usage: python3 ccsw_summary.py <run-id>"""
import json, sys
agg = {}
for j in json.load(open('results/%s.json' % sys.argv[1])):
    v = j['name'].split('_')[1]
    for r in j['rows']:
        if r['tag'] == 'STBROW':
            k = (v, r['loop']); pm = r['pm_deg'] if r['pm_deg'] is not None else 999
            if k not in agg or pm < agg[k][0]:
                agg[k] = (pm, r['gm_db'], j['name'], 2 ** r['code'])
        if r['tag'] == 'ACROW' and not isinstance(r.get('fs3'), str) and not isinstance(r.get('fc3'), str):
            k = (v, 'f3'); f = min(r['fs3'], r['fc3']) / 1e6
            if k not in agg or f < agg[k][0]:
                agg[k] = (round(f, 3), r['pks'], j['name'], 2 ** int(r['code']))
for k in sorted(agg):
    print(k, agg[k])
