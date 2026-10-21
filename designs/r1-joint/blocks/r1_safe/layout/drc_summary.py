#!/usr/bin/env python3
"""Count DRC markers per rule in a KLayout lyrdb (host Python). Usage: drc_summary.py <file.lyrdb> [n_examples]"""
import re, sys, collections
t = open(sys.argv[1]).read()
n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
cnt = collections.Counter()
ex = collections.defaultdict(list)
for m in re.finditer(r'<item>(.*?)</item>', t, re.S):
    it = m.group(1)
    cat = re.search(r"<category>'?([^<']*)'?</category>", it).group(1)
    cnt[cat] += 1
    v = re.search(r'<value>(.*?)</value>', it, re.S)
    if len(ex[cat]) < n and v:
        ex[cat].append(v.group(1)[:160])
print('total', sum(cnt.values()))
for k, v in sorted(cnt.items()):
    print(k, v)
    for e in ex[k]:
        print('    ', e)
