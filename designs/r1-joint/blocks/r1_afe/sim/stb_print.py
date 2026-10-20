#!/usr/bin/env python3
"""Print the loop-gain rows (STBROW) of results/<run-id>.json. Usage: python3 stb_print.py <run-id>"""
import json, sys
for j in json.load(open('results/%s.json' % sys.argv[1])):
    print('==', j['name'], 'rc', j['rc'], '%ss' % j['seconds'], j['errors'][:2])
    for r in j['rows']:
        if r['tag'] == 'STBROW':
            print('  x%-2d %-6s Tdc=%6.1f dB fu=%-9s PM=%-7s GM=%-7s f180=%s' % (
                2 ** r['code'], r['loop'], r['t_dc_db'], '%.3g' % r['f_unity'] if r['f_unity'] else '-',
                r['pm_deg'], r['gm_db'], '%.3g' % r['f_180'] if r['f_180'] else '-'))
