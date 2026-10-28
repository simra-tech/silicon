#!/usr/bin/env python3
"""Layout E8 (track T3l): x32 / x1 output offset table (mV) from the OPROW rows of one or more result files.
  python3 sim/ofs_table.py results/<run>.json [...]   -> one line per variant and job tag (x32 odiff, x1 odiff)"""
import json, sys, collections
T = collections.OrderedDict()
for f in sys.argv[1:]:
    for j in json.load(open(f)):
        v, _, tag = j['name'].rpartition('__')
        r = {int(x['code']): x for x in j.get('rows', []) if x.get('tag') == 'OPROW'}
        T[(v, tag)] = (r[5]['odiff'] * 1e3 if 5 in r else None, r[0]['odiff'] * 1e3 if 0 in r else None, j.get('rc'))
for (v, tag), (a, b, rc) in T.items():
    print('%-6s %-30s x32 %8s  x1 %8s  rc %s' % (v, tag, '%.2f' % a if a is not None else '-', '%.2f' % b if b is not None else '-', rc))
