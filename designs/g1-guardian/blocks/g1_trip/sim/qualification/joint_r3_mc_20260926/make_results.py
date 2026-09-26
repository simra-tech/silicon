#!/usr/bin/env python3
"""joint_r3_mc_20260926: build the compact per-seed summaries and RESULTS_TABLE.md from the full per-seed
summaries (bulk `full_summaries/s<seed>.json`, written by runner_r3mc.py or, for resumed seeds, runner_r3mc_r2.py).

  python3 make_results.py <full_summaries dir> <output dir (the repository run directory)>
"""
import json, statistics, sys
from pathlib import Path
src, out = Path(sys.argv[1]), Path(sys.argv[2])
rows, counts, off = [], {'passed': 0, 'electrical': 0, 'numerical': 0}, {'soft': [], 'hard': []}
fails = []
for f in sorted(src.glob('s*.json')):
    s = json.loads(f.read_text())
    for p in s['probes']:
        p.pop('warnings', None)
    if 'calibration' in s:
        s['calibration'].pop('all_attempts', None)
    (out / ('s%d' % s['seed'])).mkdir(exist_ok=True)
    (out / ('s%d' % s['seed']) / 'summary.json').write_text(json.dumps(s, indent=1) + '\n')
    probes = s['probes']
    def per_temp(kind):
        res = []
        for t in (25, -40, 125):
            ps = [p for p in probes if p['kind'] == kind and p['temperature_C'] == t]
            if not ps:
                res.append('not run'); continue
            ok = sum(1 for p in ps if p['status'] == 'passed' and p['decisions'] == p.get('expected_decisions'))
            num = sum(1 for p in ps if p['status'] != 'passed')
            res.append('%d/%d%s' % (ok, len(ps), ' (%d num.)' % num if num else ''))
        return ' / '.join(res)
    cr = s.get('calibration_reach')
    if cr:
        for k in off: off[k].append(cr[k]['offset_before_cal_mV_shunt'])
        reach = 'soft %+.2f mV (%+d), hard %+.2f mV (%+d)%s' % (cr['soft']['offset_before_cal_mV_shunt'], cr['soft']['correction'],
                cr['hard']['offset_before_cal_mV_shunt'], cr['hard']['correction'], ' CLIPPED' if cr['soft']['clipped'] or cr['hard']['clipped'] else '')
        codes = 'guard %d/%d, residual %d/%d' % (cr['soft']['corrected_code'], cr['hard']['corrected_code'], cr['soft']['residual_code'], cr['hard']['residual_code'])
    else:
        reach, codes = 'not reached: ' + s['bracket_status'], '-'
    st = s['status']
    if st == 'passed':
        counts['passed'] += 1; cls = 'passed'
    elif 'numerical' in st:
        counts['numerical'] += 1; cls = 'numerical' + (' + electrical' if s['electrical_failures'] else '')
    else:
        counts['electrical'] += 1; cls = 'electrical'
    for p in probes:
        if p.get('class_') == 'electrical' or p['status'] != 'passed':
            fails.append((s['seed'], p['leaf'], p['kind'], p['temperature_C'], p['shunt_V'] * 1e3, p['codes'], p.get('decisions'), p.get('expected_decisions'),
                          'electrical' if p['status'] == 'passed' else 'numerical: %s, %.0f s%s' % (p['watchdog_status'], p['wall_s'], '; ' + p['errors'][0][:60] if p['errors'] else '')))
    rows.append('| %d | %s | %s | %s | %s | %s | %.1f |' % (s['seed'], cls, reach, codes, per_temp('guard'), per_temp('residual'),
                s.get('total_core_seconds', sum(p['wall_s'] for p in probes)) / 3600))
n = len(rows)
lines = ['Seeds %d: **passed %d**, electrical fail %d, numerical fail %d.' % (n, counts['passed'], counts['electrical'], counts['numerical']), '',
         '| Seed | Result | Calibration reach at 25 C / 25 mV: offset before calibration, mV shunt (signed correction, LSB) | Codes soft/hard | Guards 25 / -40 / 125 C (correct/probes) | Residual +/-0.5 mV 25 / -40 / 125 C | Core h |',
         '| --- | --- | --- | --- | --- | --- | --- |'] + rows
lines += ['', 'Calibrated seeds (%d): offset before calibration, mV shunt: soft mean %+.2f, sd %.2f, range %+.2f..%+.2f; hard mean %+.2f, sd %.2f, range %+.2f..%+.2f.' % (
    len(off['soft']), statistics.mean(off['soft']), statistics.stdev(off['soft']), min(off['soft']), max(off['soft']),
    statistics.mean(off['hard']), statistics.stdev(off['hard']), min(off['hard']), max(off['hard']))]
lines += ['', '| Seed | Probe | Kind | T (C) | Shunt (mV) | Codes | Decisions | Expected | Class |', '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
for f in fails:
    lines.append('| %d | %s | %s | %d | %.2f | %s | %s | %s | %s |' % f)
(out / 'RESULTS_TABLE.md').write_text('\n'.join(lines) + '\n')
print(lines[0])
