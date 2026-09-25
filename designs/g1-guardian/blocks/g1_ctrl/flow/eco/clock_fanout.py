#!/usr/bin/env python3
"""Clock-buffer fanout from a gate netlist: for every clkbuf_*/clkload-driving
net, count input pins attached. Limit to check: 8 (stdcell liberty
default_max_fanout). Usage: clock_fanout.py <nl.v> [limit]"""
import re
import sys
from collections import Counter

text = open(sys.argv[1]).read()
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 8
inst_re = re.compile(r'^\s*(sg13g2_\w+)\s+(\S+)\s*\((.*?)\);', re.S | re.M)
pin_re = re.compile(r'\.(\w+)\(\s*([^()]*?)\s*\)')
drv, loads = {}, Counter()
for m in inst_re.finditer(text):
    cell, name, body = m.groups()
    for pin, net in pin_re.findall(body):
        if not net:
            continue
        if pin in ('X', 'Y', 'Q', 'Q_N'):
            drv[net] = name
        else:
            loads[net] += 1
clk = {n: loads[n] for n, d in drv.items() if d.startswith('clkbuf')}
worst = sorted(clk.items(), key=lambda kv: -kv[1])[:5]
viol = [kv for kv in clk.items() if kv[1] > limit]
print('clock-buffer nets %d, max fanout %d, >%d: %d; worst %s' % (len(clk), max(clk.values()), limit, len(viol), worst))
sys.exit(1 if viol else 0)
