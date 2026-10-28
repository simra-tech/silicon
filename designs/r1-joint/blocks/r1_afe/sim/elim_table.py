#!/usr/bin/env python3
"""Layout E8 (track T3l): x32 output offset (mV) per variant and job of an elimination run, and the term of each
eliminated group (BASE - variant).  python3 sim/elim_table.py results/<run>.json [code]"""
import json, sys, collections
code = int(sys.argv[2]) if len(sys.argv) > 2 else 5
T = collections.OrderedDict()
for j in json.load(open(sys.argv[1])):
    v, _, tag = j['name'].rpartition('__')
    r = {int(x['code']): x for x in j.get('rows', []) if x.get('tag') == 'OPROW' and isinstance(x.get('odiff'), float)}
    T.setdefault(v, collections.OrderedDict())[tag] = r[code]['odiff'] * 1e3 if code in r else None
tags = list(T['BASE'])
short = lambda t: t.replace('op_', '').replace('_ib10.14', '').replace('ib11.81_', '').replace('ib9.00_', '')
f = lambda x: '%13.2f' % x if x is not None else '%13s' % '-'
print('%-6s' % 'x%d' % 2 ** code + ''.join('%13s' % short(t) for t in tags))
for v in T:
    print('%-6s' % v + ''.join(f(T[v].get(t)) for t in tags))
print('term (BASE - variant)')
for v in T:
    if v != 'BASE':
        print('%-6s' % v + ''.join(f(T['BASE'][t] - T[v][t] if T[v].get(t) is not None and T['BASE'][t] is not None else None) for t in tags))
