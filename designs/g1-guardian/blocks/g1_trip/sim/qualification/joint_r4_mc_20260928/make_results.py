#!/usr/bin/env python3
"""joint_r4_mc_20260928: compact per-seed summaries and RESULTS_TABLE.md (r3 format for r4, then r3 vs r4 per seed).

r4 input: the per-seed summaries written by runner_r4mc.py --summary-dir (bulk `summaries/s<seed>/summary.json`).
r3 input: the compact r3 summaries in ../joint_r3_mc_20260926/s<seed>/summary.json.
A seed whose r4 runner has not finished is reported as "incomplete" with the probes that did finish; probes that
did not start are "not run".

  python3 make_results.py <r4 summaries dir> <output dir (the repository run directory)>
"""
import json, statistics, sys
from pathlib import Path
src, out = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
R3 = out.parent / 'joint_r3_mc_20260926'
SEEDS = range(79001, 79025)


def load_r4(seed):
    f = src / ('s%d' % seed) / 'summary.json'
    if not f.exists():
        return None
    s = json.loads(f.read_text())
    for p in s['probes']:
        p.pop('warnings', None)
    if 'calibration' in s:
        s['calibration'].pop('all_attempts', None)
    return s


def cls_of(s):
    if s is None:
        return 'not run'
    st = s['status']
    if st == 'running':
        return 'incomplete'
    if st == 'passed':
        return 'passed'
    if 'numerical' in st:
        return 'numerical' + (' + electrical' if s['electrical_failures'] else '')
    return 'electrical'


def per_temp(s, kind):
    res = []
    for t in (25, -40, 125):
        ps = [p for p in s['probes'] if p['kind'] == kind and p['temperature_C'] == t] if s else []
        if not ps:
            res.append('not run'); continue
        ok = sum(1 for p in ps if p['status'] == 'passed' and p['decisions'] == p.get('expected_decisions'))
        num = sum(1 for p in ps if p['status'] != 'passed')
        res.append('%d/%d%s' % (ok, len(ps), ' (%d num.)' % num if num else ''))
    return res


def reach(s):
    cr = s.get('calibration_reach') if s else None
    if not cr:
        return None, None
    r = 'soft %+.2f mV (%+d), hard %+.2f mV (%+d)%s' % (cr['soft']['offset_before_cal_mV_shunt'], cr['soft']['correction'],
        cr['hard']['offset_before_cal_mV_shunt'], cr['hard']['correction'], ' CLIPPED' if cr['soft']['clipped'] or cr['hard']['clipped'] else '')
    c = 'guard %d/%d, residual %d/%d' % (cr['soft']['corrected_code'], cr['hard']['corrected_code'], cr['soft']['residual_code'], cr['hard']['residual_code'])
    return r, c


def hot_residual(s):
    """Decisions of the 125 C residual probes, soft/hard at 24.5 and 25.5 mV (T = trip, n = no trip, x = numerical)."""
    if not s:
        return 'not run'
    out_ = []
    for sh in (.0245, .0255):
        ps = [p for p in s['probes'] if p['kind'] == 'residual' and p['temperature_C'] == 125 and abs(p['shunt_V'] - sh) < 1e-9]
        if not ps:
            out_.append('not run'); continue
        p = ps[0]
        if p['status'] != 'passed':
            out_.append('x/x'); continue
        d = p['decisions']
        out_.append('%s/%s' % ('T' if d['soft'] else 'n', 'T' if d['hard'] else 'n'))
    return '24.5: %s, 25.5: %s' % tuple(out_)


r4s = {sd: load_r4(sd) for sd in SEEDS}
r3s = {sd: json.loads((R3 / ('s%d' % sd) / 'summary.json').read_text()) for sd in SEEDS}
for sd, s in r4s.items():
    if s is not None:
        (out / ('s%d' % sd)).mkdir(exist_ok=True)
        (out / ('s%d' % sd) / 'summary.json').write_text(json.dumps(s, indent=1) + '\n')

counts = {'passed': 0, 'electrical': 0, 'numerical': 0, 'incomplete': 0, 'not run': 0}
rows, fails, off = [], [], {'soft': [], 'hard': []}
for sd in SEEDS:
    s = r4s[sd]; c = cls_of(s)
    counts[c.split(' ')[0] if c.startswith('numerical') else c] += 1
    r, codes = reach(s)
    if s and s.get('calibration_reach'):
        for k in off: off[k].append(s['calibration_reach'][k]['offset_before_cal_mV_shunt'])
    if r is None:
        r = 'not reached: ' + s['bracket_status'] if s else 'not run'; codes = '-'
    core = (s.get('total_core_seconds') or sum(p['wall_s'] for p in s['probes'])) / 3600 if s else 0
    rows.append('| %d | %s | %s | %s | %s | %s | %.1f |' % (sd, c, r, codes, ' / '.join(per_temp(s, 'guard')), ' / '.join(per_temp(s, 'residual')), core))
    for p in (s['probes'] if s else []):
        if p.get('class_') == 'electrical' or p['status'] != 'passed':
            fails.append((sd, p['leaf'], p['kind'], p['temperature_C'], p['shunt_V'] * 1e3, p['codes'], p.get('decisions'), p.get('expected_decisions'),
                          'electrical' if p['status'] == 'passed' else 'numerical: %s, %.0f s%s' % (p['watchdog_status'], p['wall_s'], '; ' + p['errors'][0][:60] if p['errors'] else '')))
L = ['Seeds 24: **passed %d**, electrical fail %d, numerical fail %d, incomplete at the deadline %d, not run %d.' % (
     counts['passed'], counts['electrical'], counts['numerical'], counts['incomplete'], counts['not run']), '',
     '## r4 (r3 format)', '',
     '| Seed | Result | Calibration reach at 25 C / 25 mV: offset before calibration, mV shunt (signed correction, LSB) | Codes soft/hard | Guards 25 / -40 / 125 C (correct/probes) | Residual +/-0.5 mV 25 / -40 / 125 C | Core h |',
     '| --- | --- | --- | --- | --- | --- | --- |'] + rows
if len(off['soft']) > 1:
    L += ['', 'Calibrated seeds (%d): offset before calibration, mV shunt: soft mean %+.2f, sd %.2f, range %+.2f..%+.2f; hard mean %+.2f, sd %.2f, range %+.2f..%+.2f.' % (
        len(off['soft']), statistics.mean(off['soft']), statistics.stdev(off['soft']), min(off['soft']), max(off['soft']),
        statistics.mean(off['hard']), statistics.stdev(off['hard']), min(off['hard']), max(off['hard']))]
L += ['', '| Seed | Probe | Kind | T (C) | Shunt (mV) | Codes | Decisions | Expected | Class |', '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
L += ['| %d | %s | %s | %d | %.2f | %s | %s | %s | %s |' % f for f in fails] or ['| - | none | | | | | | | |']

L += ['', '## r3 vs r4 per seed (same seeds, same draw for every r3 device)', '',
      'Offset = offset before calibration at 25 C / 25 mV, mV shunt. Hard code = calibrated (guard) / bracket-midpoint (residual) hard code. '
      'Residual = correct/probes at +/-0.5 mV about the room crossing, 25 C and 125 C. Hot residual = soft/hard decision at 125 C '
      '(T trip, n no trip; expected n/n at 24.5 mV and T/T at 25.5 mV).', '',
      '| Seed | r3 result | r4 result | Hard offset r3 / r4 | Soft offset r3 / r4 | Hard code r3 / r4 | Residual 25 C r3 / r4 | Residual 125 C r3 / r4 | Hot residual r3 | Hot residual r4 |',
      '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
for sd in SEEDS:
    a, b = r3s[sd], r4s[sd]
    def o(s, k):
        cr = s.get('calibration_reach') if s else None
        return '%+.2f' % cr[k]['offset_before_cal_mV_shunt'] if cr else '-'
    def hc(s):
        cr = s.get('calibration_reach') if s else None
        return '%d/%d' % (cr['hard']['corrected_code'], cr['hard']['residual_code']) if cr else '-'
    L.append('| %d | %s | %s | %s / %s | %s / %s | %s / %s | %s / %s | %s / %s | %s | %s |' % (
        sd, cls_of(a), cls_of(b), o(a, 'hard'), o(b, 'hard'), o(a, 'soft'), o(b, 'soft'), hc(a), hc(b),
        per_temp(a, 'residual')[0], per_temp(b, 'residual')[0], per_temp(a, 'residual')[2], per_temp(b, 'residual')[2], hot_residual(a), hot_residual(b)))
(out / 'RESULTS_TABLE.md').write_text('\n'.join(L) + '\n')
print(L[0])
json.dump({'counts': counts, 'offsets_mV': off}, sys.stdout); print()
