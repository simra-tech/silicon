#!/usr/bin/env python3
"""Count markers per rule category in KLayout .lyrdb reports. Usage: summarize_lyrdb.py <out.json> <report.lyrdb> ..."""
import sys, json, re, collections
out = {}
for p in sys.argv[2:]:
    txt = open(p, errors='replace').read()
    cats = re.findall(r'<category>\s*<name>([^<]*)</name>', txt)
    items = re.findall(r'<item>.*?<category>([^<]*)</category>', txt, re.S)
    cnt = collections.Counter(c.strip("'") for c in items)
    out[p.rsplit('/', 1)[-1]] = {'rule_categories': len(set(cats)), 'items_total': sum(cnt.values()), 'items_per_rule': dict(cnt)}
json.dump(out, open(sys.argv[1], 'w'), indent=1)
for k, v in out.items(): print(k, v['rule_categories'], 'categories', v['items_total'], 'items', dict(list(v['items_per_rule'].items())[:5]))
