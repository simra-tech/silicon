#!/usr/bin/env python3
"""Per-layer breakdown of the kpex 2.5D report (rdb) for chosen nets (layout B4 diagnostic of the ain_cos pair).
Reads the flat category paths "'type'.'k=v'...'#n: value fF'" (each item once).
usage: cap_breakdown.py <kpex report .rdb.gz> net1 [net2 ...]"""
import gzip, re, sys
from collections import defaultdict
f, nets = sys.argv[1], set(sys.argv[2:])
seen = set()
S = defaultdict(float)
pat = re.compile(r"<category>('[^<]*?'#\d+:?[^']*? [0-9.eE+-]+ fF')")
for line in gzip.open(f, 'rt', errors='replace'):
    for m in pat.finditer(line):
        s = m.group(1)
        if s in seen:
            continue
        seen.add(s)
        parts = re.findall(r"'([^']*)'", s)
        typ = parts[0]
        v = float(re.search(r'([0-9.eE+-]+) fF$', parts[-1]).group(1))
        kv = dict(x.split('=', 1) for x in parts[1:-1] if '=' in x)
        pair = [x.replace('\\342\\200\\223', '–') for x in parts[1:-1] if '\\342\\200\\223' in x or ' – ' in x]
        if 'inside_net' in kv:
            a, b, la, lb = kv['inside_net'], kv.get('outside_net'), kv.get('inside_layer'), kv.get('outside_layer')
        elif 'inside' in kv:
            a, b, la, lb = kv['inside'], kv['outside'], kv['layer'], kv['layer']
        elif 'net1' in kv:
            a, b, la, lb = kv['net1'], kv['net2'], kv.get('layer1', kv.get('layer')), kv.get('layer2', kv.get('layer'))
        elif pair:
            a, b = [x.strip() for x in pair[0].split('–')]
            la = kv.get('top_layer') or kv.get('layer'); lb = kv.get('bot_layer') or kv.get('layer')
        else:
            print('unparsed', s[:200]); continue
        for n1, n2, l1, l2 in ((a, b, la, lb), (b, a, lb, la)):
            if n1 in nets:
                S[(n1, typ[:14], l1, l2, n2)] += v
for k in sorted(S, key=lambda k: (k[4], k[0], -S[k])):
    if S[k] >= 0.1:
        print('%-10s %-14s %-8s %-8s %-10s %7.3f' % (k + (S[k],)))
tot = defaultdict(float)
for k, v in S.items():
    tot[(k[0], k[4])] += v
print('totals'); [print(' ', k, round(v, 3)) for k, v in sorted(tot.items()) if v > 0.1]
