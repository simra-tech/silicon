#!/usr/bin/env python3
"""Worst phase margin (and its gain margin) per variant and loop over the jobs of results/<run-id>.json.
Variant = second '_' field of the job name. Usage: python3 stb_worst.py <run-id>"""
import json, sys
agg = {}
for j in json.load(open('results/%s.json' % sys.argv[1])):
    v = j['name'].split('_')[1]
    for r in j['rows']:
        if r['tag'] != 'STBROW':
            continue
        k = (v, r['loop'])
        pm = r['pm_deg'] if r['pm_deg'] is not None else 999
        if k not in agg or pm < agg[k][0]:
            agg[k] = (pm, r['gm_db'], j['name'], 'x%d' % 2 ** r['code'])
for k in sorted(agg):
    print('%-6s %-6s PM %7.2f  GM %s  at %s %s' % (k + agg[k]))
