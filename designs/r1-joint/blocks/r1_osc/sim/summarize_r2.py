#!/usr/bin/env python3
"""Collect the revision-2 trim curves (schematic and post-layout) and the revision-1 references into
results/summary_r2.json and print the README tables. Host Python, reads sim/runs/<id>/results.json only.
  python3 designs/r1-joint/blocks/r1_osc/sim/summarize_r2.py"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, 'runs')
CORNERS = [('tt', 1.2, 27), ('ss', 1.08, 125), ('ff', 1.32, -40), ('ss', 1.08, -40), ('ff', 1.32, 125)]
SETS = {  # view -> run ids holding its 32-code curves
    'r1-sch': ['r1a-trim32-tt', 'r1a-reach', 'r1d-trim32-cross'],
    'r1-post-k': ['post-trim32-tt-20261021', 'post-reach-20261021'],
    'r2-sch': ['r2-sch-trim32-tt-20261021', 'r2-sch-reach-20261021', 'r2-sch-cross-20261021'],
    'r2c-post': ['r2-post-trim32-tt-20261021', 'r2-post-reach-20261021', 'r2-post-cross-20261021'],
    'r2-post': ['r2-postd-trim32-tt-20261021', 'r2-postd-reach-20261021', 'r2-postd-cross-20261021'],
}


def load(run):
    p = os.path.join(RUNS, run, 'results.json')
    return json.load(open(p)) if os.path.exists(p) else []


def key(c):
    return '%s/%gV/%gC' % c


out = {}
for view, runs in SETS.items():
    pts = [p for r in runs for p in load(r) if p.get('deck') == 'tb_osc30.cir' and p.get('rc') == 0 and 'f_MHz' in p]
    out[view] = {}
    for c in CORNERS:
        cur = {p['code']: p for p in pts if (p['corner'], round(p['vdd'], 2), round(p['temp'])) == c}
        if len(cur) != 32:
            continue
        f = [cur[k]['f_MHz'] for k in range(32)]
        st = [100.0 * (1.0 - f[k + 1] / f[k]) for k in range(31)]   # as the r1 README: (f(k) - f(k+1)) / f(k)
        out[view][key(c)] = dict(f_MHz=f, step_pct=st, monotonic=all(s > 0 for s in st), step_min=min(st), step_max=max(st),
                                 step_max_at=st.index(max(st)), duty=[min(cur[k]['duty_pct'] for k in cur), max(cur[k]['duty_pct'] for k in cur)],
                                 idd_c22=cur[22]['idd_uA'], idd=[min(cur[k]['idd_uA'] for k in cur), max(cur[k]['idd_uA'] for k in cur)],
                                 tloop_max=max(cur[k]['tloop_ns'] for k in cur), tloop_c22=cur[22]['tloop_ns'])
extra = {}
for r in ('r2-postd-startup-20261021', 'r2-postd-jitter-20261021', 'r1a-startup', 'post-jitter-20261021-b'):
    extra[r] = load(r)
json.dump(dict(views=out, other=extra), open(os.path.join(HERE, 'results', 'summary_r2.json'), 'w'), indent=1)

for view, d in out.items():
    print('==', view)
    for c, v in d.items():
        f = v['f_MHz']
        print('%-16s c0 %.2f c16 %.2f c22 %.2f c31 %.2f | step %.2f-%.2f (max at %d->%d) mono %s duty %.2f-%.2f IDD22 %.1f tloop22 %.2f max %.2f'
              % (c, f[0], f[16], f[22], f[31], v['step_min'], v['step_max'], v['step_max_at'], v['step_max_at'] + 1,
                 v['monotonic'], v['duty'][0], v['duty'][1], v['idd_c22'], v['tloop_c22'], v['tloop_max']))
for view in ('r2-sch', 'r2-post'):
    if 'tt/1.2V/27C' in out[view]:
        print('== %s full curves' % view)
        for c, v in out[view].items():
            print(c, ' '.join('%.2f' % x for x in v['f_MHz']))
            print('   step', ' '.join('%.2f' % x for x in v['step_pct']))

# ---- README tables (markdown) ----
CK = [key(c) for c in CORNERS]
NAME = {'tt/1.2V/27C': 'tt / 1.2 V / 27 °C', 'ss/1.08V/125C': 'ss / 1.08 V / 125 °C', 'ff/1.32V/-40C': 'ff / 1.32 V / −40 °C',
        'ss/1.08V/-40C': 'ss / 1.08 V / −40 °C', 'ff/1.32V/125C': 'ff / 1.32 V / 125 °C'}
print('\n### MD: post-layout curves (r2-post)')
print('| Corner | Code 0 | Code 16 | Code 22 | Code 31 | Step min–max (codes of max) | Monotonic | Duty | IDD code 22 | Loop delay max |')
print('| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |')
for c in CK:
    v = out['r2-post'].get(c)
    if not v:
        print('| %s | not run |' % NAME[c]); continue
    f = v['f_MHz']
    print('| %s | %.2f | %.2f | %.2f | %.2f | %.2f–%.2f %% (%d→%d) | %s | %.2f–%.2f %% | %.1f µA | %.2f ns |' % (
        NAME[c], f[0], f[16], f[22], f[31], v['step_min'], v['step_max'], v['step_max_at'], v['step_max_at'] + 1,
        'yes' if v['monotonic'] else 'NO', v['duty'][0], v['duty'][1], v['idd_c22'], v['tloop_max']))
print('\n### MD: views')
print('| Point | r1 schematic | r1 post (layout k) | r2 schematic | r2 post (layout r2d) | r2 post vs r2 schematic |')
print('| --- | --- | --- | --- | --- | --- |')
for c in CK:
    for code in (0, 22, 31):
        vals = []
        for view in ('r1-sch', 'r1-post-k', 'r2-sch', 'r2-post'):
            v = out[view].get(c)
            vals.append(v['f_MHz'][code] if v else None)
        fm = lambda x: '%.2f' % x if x is not None else 'not run'
        d = '%+.1f %%' % (100 * (vals[3] / vals[2] - 1)) if vals[2] and vals[3] else '—'
        print('| %s, code %d | %s | %s | %s | %s | %s |' % (NAME[c], code, fm(vals[0]), fm(vals[1]), fm(vals[2]), fm(vals[3]), d))
    for view in ():
        pass
print('| Step max, all codes | ' + ' | '.join(
    ('%.2f %%' % max(v['step_max'] for v in out[view].values())) if out[view] else 'not run'
    for view in ('r1-sch', 'r1-post-k', 'r2-sch', 'r2-post')) + ' | — |')
if out['r2-post'].get('tt/1.2V/27C'):
    v = out['r2-post']['tt/1.2V/27C']
    print('\n### MD: tt curve r2-post')
    print('| Code | ' + ' | '.join(str(k) for k in range(16)) + ' |')
    print('| --- ' * 17 + '|')
    print('| f (MHz) | ' + ' | '.join('%.2f' % x for x in v['f_MHz'][:16]) + ' |')
    print('| step to next (%) | ' + ' | '.join('%.2f' % x for x in v['step_pct'][:16]) + ' |')
    print('| Code | ' + ' | '.join(str(k) for k in range(16, 32)) + ' |')
    print('| --- ' * 17 + '|')
    print('| f (MHz) | ' + ' | '.join('%.2f' % x for x in v['f_MHz'][16:]) + ' |')
    print('| step to next (%) | ' + ' | '.join('%.2f' % x for x in v['step_pct'][16:]) + ' | — |')
