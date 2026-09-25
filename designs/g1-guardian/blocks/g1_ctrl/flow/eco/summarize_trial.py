#!/usr/bin/env python3
"""Summarise one LibreLane trial run: per-step wall time and the signoff metrics.
Usage: summarize_trial.py <run dir> [out.json]"""
import glob
import json
import os
import sys

run = sys.argv[1]
steps = []
for d in sorted(glob.glob(os.path.join(run, '[0-9]*-*'))):
    rt = os.path.join(d, 'runtime.txt')
    t = open(rt).read().strip() if os.path.exists(rt) else 'not run to completion'
    if t[:2].isdigit():
        h, m, s = t.split(':'); t = round(int(h) * 3600 + int(m) * 60 + float(s), 1)
    steps.append((os.path.basename(d), t))
m = json.load(open(os.path.join(run, 'final', 'metrics.json'))) if os.path.exists(os.path.join(run, 'final', 'metrics.json')) else {}
keys = ['design__instance__count', 'design__instance__area', 'design__instance__utilization',
        'timing__setup__ws', 'timing__hold__ws', 'timing__setup_vio__count', 'timing__hold_vio__count',
        'design__max_slew_violation__count', 'design__max_cap_violation__count',
        'design__max_fanout_violation__count', 'route__drc_errors', 'route__wirelength',
        'antenna__violating__nets', 'antenna__violating__pins', 'magic__drc_error__count',
        'klayout__drc_error__count', 'design__lvs_error__count', 'design__lvs_device_difference__count',
        'design__lvs_net_difference__count', 'design__xor_difference__count',
        'design__disconnected_pin__count', 'design__instance__count__class:antenna_cell',
        'design__instance__count__class:timing_repair_buffer', 'design__instance__count__class:clock_buffer']
sel = {k: m.get(k, 'missing') for k in keys}
for k in list(m):
    if k.startswith(('timing__setup__ws__corner', 'timing__hold__ws__corner', 'design__max_slew_violation__count__corner')):
        sel[k] = m[k]
total = sum(t for _, t in steps if isinstance(t, float))
res = {'run': run, 'total_step_seconds': round(total, 1), 'steps': steps, 'metrics': sel}
if len(sys.argv) > 2:
    json.dump(res, open(sys.argv[2], 'w'), indent=1)
print('total step time %.0f s over %d steps' % (total, len(steps)))
for s, t in steps:
    if isinstance(t, float) and t > 20 or not isinstance(t, float):
        print('  %-45s %s' % (s, t))
for k, v in sel.items():
    print('  %s = %s' % (k, v))
