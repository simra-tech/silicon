#!/usr/bin/env python3
"""Summary of a reduced power-sequencing pad-deck run (red-team power_io 'pg' decks): python3 analyze_pg.py <wrdata.txt>
GATE maximum and its time (with VDD and IOVDD there), the intervals with GATE above 1 V and 0.5 V, and the maxima of
tripped and en_i. Same quantities as the red team's scripts/sum_pg.py, without numpy."""
import json, sys
f = open(sys.argv[1]); hdr = [h.replace('v(', '').replace(')', '') for h in f.readline().split()]
rows = [list(map(float, l.split())) for l in f if l.strip()]
c = {h: i for i, h in enumerate(hdr)}
t = [r[0] for r in rows]; g = [r[c['gate']] for r in rows]
i = max(range(len(g)), key=lambda k: g[k])
def above(th):
    idx = [k for k in range(len(g)) if g[k] > th]
    return (t[idx[0]] * 1e3, t[idx[-1]] * 1e3) if idx else None
out = dict(file=sys.argv[1].rsplit('/', 1)[-1], t_end_ms=t[-1] * 1e3, gate_max_V=g[i], t_gate_max_ms=t[i] * 1e3,
           vdd_at_gate_max=rows[i][c['vdd']], iovdd_at_gate_max=rows[i][c['iovdd']],
           gate_above_1V_ms=above(1.0), gate_above_0p5V_ms=above(0.5),
           tripped_max_V=max(r[c['tripped']] for r in rows), en_i_max_V=max(r[c['en_i']] for r in rows))
print(json.dumps(out, indent=1))
