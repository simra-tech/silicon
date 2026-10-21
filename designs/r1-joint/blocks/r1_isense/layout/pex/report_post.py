#!/usr/bin/env python3
"""Pre- vs post-layout table of r1_isense (host python3): reads sim/results/<run>/summary.json of the revision-2
schematic campaign (suffix 20261021r2) and of the post-layout campaign (run_post.sh, suffix given).
  python3 report_post.py 20261021-a  > markdown rows on stdout, JSON in sim/results/summary-post-<suffix>.json"""
import json, os, sys
X = sys.argv[1]
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'sim', 'results')


def load(r):
    p = os.path.join(RES, r, 'summary.json')
    return json.load(open(p))['result'] if os.path.exists(p) else None


rows, out = [], {}


def row(name, pre, post, unit, crit=''):
    f = lambda v: 'not run' if v is None else ('%.4g' % v if isinstance(v, float) else str(v))
    rows.append('| %s | %s | %s | %s | %s |' % (name, f(pre), f(post), unit, crit))
    out[name] = dict(pre=pre, post=post, unit=unit, criterion=crit)


g = lambda d, *k: (None if d is None else (lambda v: v)(__import__('functools').reduce(lambda a, b: a.get(b) if isinstance(a, dict) else None, k, d)))
pre, post = load('isense-dc-20261021r2'), load('isense-post-dc-' + X)
pc, pr = load('isense-post-dc_c-' + X), load('isense-post-dc_r-' + X)
for key, unit, crit in (('gain', '', 'report (14)'), ('pedestal_error_uV', 'uV', 'report'),
                        ('offset_pedestal_off_uV', 'uV', '|x| <= 100'), ('vcm_out_V', 'V', '0.60 +/- 0.03')):
    row('DC tt %s (RC)' % key, g(pre, 'tt', key), g(post, 'tt', key), unit, crit)
    row('DC tt %s (devices + C / devices + R)' % key, None, '%s / %s' % (g(pc, 'tt', key), g(pr, 'tt', key)), unit, 'split')
cm = {}
for tag, s, r in (('m', '-0.1', 'cmm100'), ('p', '+0.1', 'cmp100')):
    cm[tag] = (g(load('isense-dc-%s-20261021r2' % r), 'tt', 'pedestal_mV'), g(load('isense-post-dc-%s-%s' % (r, X)), 'tt', 'pedestal_mV'))
if all(v is not None for v in cm['m'] + cm['p']):
    row('Kelvin CM -0.1 -> +0.1 V: output change (CM gain)', (cm['p'][0] - cm['m'][0]) * 1e3, (cm['p'][1] - cm['m'][1]) * 1e3, 'uV per 0.2 V', 'report')
else:
    row('Kelvin CM -0.1 -> +0.1 V: output change', None, None, 'uV per 0.2 V', 'report')
for deck, state in (('stb', 'normal'), ('stbaz', 'AZ closed')):
    a, b = load('isense-%s-20261021r2' % deck), load('isense-post-%s-%s' % (deck, X))
    for c in ('tt', 'ffx'):
        for loop in ('cm_out', 'dm_aux') if deck == 'stbaz' else ('cm_out', 'dm_out', 'dm_in'):
            pa = g(a, 'per_loop', c, loop); pb = g(b, 'per_loop', c, loop)
            if pa is None and pb is None:
                continue
            fmt = lambda d: None if d is None or d.get('worst_pm_deg') is None else ('%.1f deg / ' % d['worst_pm_deg']) + ('no 180 deg crossing' if d['worst_gm_db'] is None else '%.1f dB' % d['worst_gm_db'])
            row('%s %s %s PM / GM' % (state, c, loop), fmt(pa), fmt(pb), '', 'PM >= 60, GM >= 10')
a, b = load('isense-stbstep-20261021r2'), load('isense-post-stbstep-' + X)
for c in ('tt', 'ss'):
    row('step 0 -> 100 mV %s settle 0.5 %% (from edge start)' % c, g(a, c, 'settle_0p5pct_from_edge_start_ns'), g(b, c, 'settle_0p5pct_from_edge_start_ns'), 'ns', '<= 300')
    row('step %s overshoot count' % c, g(a, c, 'overshoot_count'), g(b, c, 'overshoot_count'), '', 'report')
print('| Quantity | Schematic (rev 2) | Post-layout | Unit | Criterion |\n| --- | --- | --- | --- | --- |')
print('\n'.join(rows))
json.dump(out, open(os.path.join(RES, 'summary-post-%s.json' % X), 'w'), indent=1)
