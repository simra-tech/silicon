#!/usr/bin/env python3
"""Item 2 summary: per-seed results of the full-chip mismatch runs (run ids psmc<seed>[rt]) from runs.json.

Writes mc_seeds.csv and mc_summary.json next to this file. Run summarize.py first.

Static crossing code (derived, comparator offset excluded): the DAC thresholds are linear in the code,
vth(code) = s * (code + c0), with c0 = 254.92 from the nominal r4 q run (vth_soft 0.804266 V at code 153,
vth_hard 1.00340 V at code 254). Per seed, s is taken from the QUIET threshold at the written code (hard 200,
soft 153) and the crossing code at the QUIET load (1 A = 25 mV) is icmp / s - c0. It contains the SENSE, BGR and
DAC-string mismatch but not the comparators' own offset, which only a calibration sweep shows.
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
C0 = 254.92


def stats(v):
    v = [x for x in v if isinstance(x, (int, float)) and not isinstance(x, bool)]
    if not v:
        return None
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return dict(n=len(v), mean=m, sd=sd, min=min(v), max=max(v))


def main():
    runs = json.load(open(os.path.join(HERE, 'runs.json')))
    rows = []
    for r in runs:
        rid = (r.get('options') or {}).get('run_id') or ''
        if not rid.startswith('psmc'):
            continue
        case = (r.get('options') or {}).get('cases', ['?'])[0]
        if case == 'cal':
            case = 'cal_%s' % (r.get('options') or {}).get('cal_kind')
        res = r.get('results', {})
        q = res.get('QUIET', {})
        tr = res.get('TRIP') or res.get('NO_TRIP_EXPECTED') or {}
        t2 = res.get('T2F', {})
        row = dict(case=case, seed=int(rid[4:9]), retry=rid.endswith('rt') or rid.endswith('h'), run_id=rid, status=r['status'],
                   wall_s=r.get('wall_s'), last_sim_time_us=(r.get('last_sim_time_s') or 0) * 1e6,
                   solver_message=r.get('solver_message'))
        cal = res.get('CAL')
        if case.startswith('cal') and cal:
            deck = os.path.join(HERE, '..', '..', 'decks', r['tag'] + '.cir')
            if not os.path.exists(deck) and os.environ.get('PS_EVIDENCE'):
                deck = os.path.join(os.environ['PS_EVIDENCE'], 'decks', r['tag'] + '.cir')
            sched = []
            if os.path.exists(deck):
                for l in open(deck):
                    if l.startswith('* CALSCHED'):
                        sched = [(int(a), float(b) * 1e-6) for a, b in (x.split('@') for x in l.split()[3:])]
                        break
            t = cal.get('first_cmp_hard_s' if case == 'cal_hard' else 'first_cmp_soft_s')
            if sched and isinstance(t, float):
                fired = [c for c, tw in sched if tw <= t]
                if fired and r['status'] != 'completed' and (r.get('last_sim_time_s') or 0) > t:
                    # stopped numerically after the first firing: the CAL measures were emitted on the partial run
                    row['status'] = 'not run to completion after the crossing (numbers usable)'
                if fired:
                    row['cal_first_fire_code'] = fired[-1]
                    row['cal_crossing_code'] = fired[-1] + 1     # between the firing code and the silent code above
                    row['cal_first_fire_after_write_us'] = (t - sched[len(fired) - 1][1]) * 1e6
                    row['cal_window'] = '%d..%d' % (sched[0][0], sched[-1][0])
        if r['status'] == 'completed' or row['status'].startswith('not run to completion after'):
            row.update(tripped_max_V=tr.get('tripped_max'), cause=tr.get('cause'), gate_min_V=tr.get('gate_min'),
                       vref_V=q.get('vref'), isense_V=q.get('isense'), icmp_V=q.get('icmp'),
                       vth_soft_V=q.get('vth_soft'), vth_hard_V=q.get('vth_hard'), t2f_MHz=t2.get('f_MHz'),
                       code_hard=q.get('code_hard'), code_soft=q.get('code_soft'))
            try:
                sh = q['vth_hard'] / (q['code_hard'] + C0)
                ss = q['vth_soft'] / (q['code_soft'] + C0)
                row['static_cross_hard'] = q['icmp'] / sh - C0
                row['static_cross_soft'] = q['icmp'] / ss - C0
            except (KeyError, TypeError, ZeroDivisionError):
                pass
            row['electrical'] = 'passed' if (tr.get('tripped_max') is not None and tr['tripped_max'] < 0.6
                                             and (tr.get('gate_min') or 0) > 3.0) else 'failed'
            if case.startswith('cal'):     # a calibration sweep trips by design; it passes when the crossing lies inside its window
                for k in ('static_cross_hard', 'static_cross_soft'):
                    row.pop(k, None)
                row['electrical'] = 'passed' if row.get('cal_first_fire_code') not in (None, int(row.get('cal_window', '0..0').split('..')[0])) \
                    else 'failed (crossing not inside the window)'
        rows.append(row)
    rows.sort(key=lambda x: (x['case'], x['seed'], x['retry']))
    cols = ['case', 'seed', 'run_id', 'retry', 'status', 'electrical', 'wall_s', 'last_sim_time_us', 'tripped_max_V',
            'gate_min_V', 'vref_V', 'isense_V', 'icmp_V', 'vth_soft_V', 'vth_hard_V', 'static_cross_hard',
            'static_cross_soft', 't2f_MHz', 'cal_window', 'cal_first_fire_code', 'cal_crossing_code',
            'cal_first_fire_after_write_us', 'solver_message']
    with open(os.path.join(HERE, 'mc_seeds.csv'), 'w') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([('%.6g' % r[c]) if isinstance(r.get(c), float) else r.get(c) for c in cols])
    summ = {}
    for case in sorted(set(r['case'] for r in rows)):
        rs = [r for r in rows if r['case'] == case]
        seeds = sorted(set(r['seed'] for r in rs))
        per_seed = {}
        for s in seeds:
            att = [r for r in rs if r['seed'] == s]
            done = [r for r in att if r['status'] == 'completed'] + \
                [r for r in att if r['status'].startswith('not run to completion after')]
            if done:
                per_seed[s] = ('completed', done[0])
            elif any(r['status'] == 'running' for r in att):
                per_seed[s] = ('running', None)
            elif not any(r['retry'] for r in att):
                per_seed[s] = ('failed, retry pending', None)
            else:
                per_seed[s] = ('numerical failure', None)
        comp = [v[1] for v in per_seed.values() if v[0] == 'completed']
        summ[case] = dict(
            seeds_launched=len(seeds),
            completed=len(comp),
            completed_on_retry=sum(1 for v in comp if v['retry']),
            electrical_passed=sum(1 for v in comp if v.get('electrical') == 'passed'),
            electrical_failed=sum(1 for v in comp if v.get('electrical') == 'failed'),
            numerical_failure=sum(1 for v in per_seed.values() if v[0] == 'numerical failure'),
            retry_pending=sum(1 for v in per_seed.values() if v[0] == 'failed, retry pending'),
            running=sum(1 for v in per_seed.values() if v[0] == 'running'),
            first_attempt_numerical_failures=sum(1 for r in rs if not r['retry'] and r['status'] == 'failed'),
            tripped_max_V=stats([v.get('tripped_max_V') for v in comp]),
            vref_V=stats([v.get('vref_V') for v in comp]),
            isense_V=stats([v.get('isense_V') for v in comp]),
            static_cross_hard=stats([v.get('static_cross_hard') for v in comp]),
            static_cross_soft=stats([v.get('static_cross_soft') for v in comp]),
            t2f_MHz=stats([v.get('t2f_MHz') for v in comp]),
            cal_crossing_code=stats([v.get('cal_crossing_code') for v in comp]))
    with open(os.path.join(HERE, 'mc_summary.json'), 'w') as f:
        json.dump(summ, f, indent=1, sort_keys=True)
    print(json.dumps(summ, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
