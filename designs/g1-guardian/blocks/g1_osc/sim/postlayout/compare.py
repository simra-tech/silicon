#!/usr/bin/env python3
"""Table of the post-layout OSC runs (postlayout/results_postlayout.txt) against the schematic runs
with the same tag (../results_osc.txt); prints Markdown."""
import re
import sys
import os

here = os.path.dirname(os.path.abspath(__file__))


def parse(path, prefix):
    d = {}
    tag = None
    for ln in open(path):
        if ln.startswith('== '):
            tag = ln[3:].strip()
            if tag.startswith(prefix):
                tag = tag[len(prefix):]
        elif ln.startswith('OSC') and tag:
            m = re.search(r'f_MHz= *([0-9.]+) +duty_pct= *([0-9.]+) +idd_uA= *([0-9.]+)', ln)
            d[tag] = tuple(float(x) for x in m.groups())
        elif ln.startswith('STARTUP') and tag:
            m = re.search(r'first_edge_us= *([0-9.]+).*f_MHz_end= *([0-9.]+)', ln)
            d[tag] = ('startup', float(m.group(1)), float(m.group(2)))
    return d


sch = parse(os.path.join(here, '..', 'results_osc.txt'), '')
pex = parse(os.path.join(here, 'results_postlayout.txt'), 'pex_')
print('| run (MOS / RES / CAP / VDD / T / code) | schematic f (MHz) | post-layout f (MHz) | delta | post-layout duty (%) | I<sub>DD</sub> (µA) |')
print('| --- | --- | --- | --- | --- | --- |')
for tag, v in pex.items():
    name = tag.replace('osc_', '').replace('mos_', '').replace('res_', '').replace('cap_', '').replace('_', ' / ')
    if v[0] == 'startup':
        s = sch.get(tag)
        print('| %s | first edge %.2f µs, %.3f MHz | first edge %.2f µs, %.3f MHz | %+.1f %% | | |' % (
            name, s[1] if s else float('nan'), s[2] if s else float('nan'), v[1], v[2], (v[2] / s[2] - 1) * 100 if s else float('nan')))
        continue
    s = sch.get(tag)
    if s:
        print('| %s | %.3f | %.3f | %+.1f %% | %.1f | %.0f |' % (name, s[0], v[0], (v[0] / s[0] - 1) * 100, v[1], v[2]))
    else:
        print('| %s | not run | %.3f | | %.1f | %.0f |' % (name, v[0], v[1], v[2]))
