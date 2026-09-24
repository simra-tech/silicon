#!/usr/bin/env python3
"""Evaluate paired incremental coupling with phase-local finite-difference gain."""
import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path
from wave_archive import open_wave

SIM = Path(__file__).resolve().parent


def load(run_id, baseline=False):
    directory = SIM / 'qualification' / run_id
    summary = json.loads((directory / 'summary.json').read_text())
    if baseline:
        assert len(summary) == 1 and summary[0]['solver_status'] == 'passed'
        summary = summary[0]
        parity = json.loads((directory / 'host_parity.json').read_text())
        assert parity['status'] == 'passed' and all(parity['checks'].values())
    else:
        assert summary['status'] == 'passed' and all(summary['checks'].values())
    with open_wave(directory / (summary['case'] + '.dat')) as stream:
        columns = stream.readline().split()
        rows = [list(map(float, line.split())) for line in stream if line.strip()]
    assert len(columns) == 8 and rows and all(len(row) == 8 and all(math.isfinite(x) for x in row) for row in rows)
    assert abs(rows[-1][0] - .52e-6) < 1e-15
    assert all(b[0] > a[0] for a, b in zip(rows, rows[1:]))
    return {'summary': summary, 'columns': columns, 'rows': rows, 'times': [row[0] for row in rows],
            'provenance': json.loads((directory / 'provenance.json').read_text())}


def sample(wave, time, column):
    times = wave['times']
    assert times[0] <= time <= times[-1], 'No waveform extrapolation'
    index = bisect.bisect_left(times, time)
    if times[index] == time:
        return wave['rows'][index][column]
    low, high = wave['rows'][index-1:index+1]
    return low[column] + (time-low[0])/(high[0]-low[0])*(high[column]-low[column])


def differential(wave, time, which):
    return sample(wave, time, 2) - sample(wave, time, 3 if which == 'soft' else 4)


def gain_check(gain5, gain10):
    finite = all(math.isfinite(g) for g in [gain5, gain10])
    nonzero = finite and min(abs(gain5), abs(gain10)) > 1e-9 and gain5*gain10 > 0
    relative = abs(gain5-gain10)/max(abs(gain5), abs(gain10)) if nonzero else None
    return nonzero and relative <= .01, relative


def check(side, via_candidate=False):
    baseline_id = 'clock-coupling-host-%s-20260922-a' % side
    waves = {'baseline': load(baseline_id, baseline=True)}
    for mode in ['coupling', 'gain5', 'gain10']:
        run_id = ('clock-via-%s-20260922-a' % side) if via_candidate and mode == 'coupling' else ('clock-%s-%s-20260922-a' % (side, mode))
        waves[mode] = load(run_id)
        assert waves[mode]['summary']['reference'] == baseline_id
        assert waves[mode]['summary']['mode'] == mode
        assert waves[mode]['columns'] == waves['baseline']['columns']
        cap_ff = 5.286345256 if via_candidate else 5.233872140
        assert waves[mode]['provenance']['coupling_fF'] == (cap_ff if mode == 'coupling' else 0)
        if via_candidate and mode == 'coupling':
            from run_clock_coupling import VIA_SUMMARY_SHA
            assert waves[mode]['provenance']['via_candidate']
            assert waves[mode]['provenance']['via_summary_sha256'] == VIA_SUMMARY_SHA
        assert waves[mode]['provenance']['shunt_delta_uV'] == (0 if mode == 'coupling' else int(mode[4:]))
    checks = {'complete_exact_parameter_inputs': True}
    samples = []
    for which, phase, column in [('soft', 40e-9, 5), ('hard', 90.2e-9, 6)]:
        for cycle in [2, 3, 4]:
            time = cycle*100e-9 + phase
            base = differential(waves['baseline'], time, which)
            coupled = differential(waves['coupling'], time, which)
            g5 = (differential(waves['gain5'], time, which)-base)/5e-6
            g10 = (differential(waves['gain10'], time, which)-base)/10e-6
            converged, relative = gain_check(g5, g10)
            # Use the smaller magnitude when quoting an absolute error.
            error = abs(coupled-base)/min(abs(g5), abs(g10)) if converged else None
            expected = which == 'soft' or side == 'high'
            bq = sample(waves['baseline'], time, column)
            cq = sample(waves['coupling'], time, column)
            name = '%s_cycle%d' % (which, cycle)
            checks[name+'_local_gain_converged'] = converged
            checks[name+'_baseline_guard_correct'] = (bq > .6) == expected
            checks[name+'_coupled_guard_correct'] = (cq > .6) == expected
            checks[name+'_incremental_50uV'] = error is not None and error <= 50e-6
            samples.append(dict(comparator=which, cycle=cycle, time_s=time,
                baseline_differential_V=base, coupled_differential_V=coupled,
                gain5_V_V=g5, gain10_V_V=g10, gain_relative_difference=relative,
                conservative_abs_input_referred_error_V=error, baseline_output_V=bq,
                coupled_output_V=cq, expected_high=expected))
    base, coupled = waves['baseline'], waves['coupling']
    grid = sorted(set(base['times'] + coupled['times']))
    start = max(base['times'][0], coupled['times'][0])
    stop = min(base['times'][-1], coupled['times'][-1])
    grid = [t for t in grid if start <= t <= stop]
    peaks = {name: max(abs(sample(coupled, t, col)-sample(base, t, col)) for t in grid)
             for name, col in [('isense_V', 7), ('conditioned_input_V', 2)]}
    return dict(status='passed' if all(checks.values()) else 'failed', side=side,
        checks=checks, samples=samples, saved_piecewise_linear_peak_difference=peaks,
        source_and_contract_sha256={mode: waves[mode]['provenance']['contract_sha256'] for mode in ['coupling','gain5','gain10']},
        limitations='Incremental mutual-only nominal two-anchor diagnostic; ground load retained. Not full RC, continuous-time peak bound, other corners/seeds, full interface, or total threshold qualification.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--via-candidate', action='store_true')
    args = parser.parse_args()
    result = {'cases': [], 'via_candidate': args.via_candidate}
    for side in ['low', 'high']:
        try:
            result['cases'].append(check(side, args.via_candidate))
        except (OSError, ValueError, KeyError, AssertionError) as exc:
            result['cases'].append({'status': 'failed', 'side': side,
                'error': type(exc).__name__, 'electrical_acceptance': 'not run; input gate failed'})
    result['status'] = 'passed' if all(case['status'] == 'passed' for case in result['cases']) else 'failed'
    result['checker_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['physical_measurement'] = 'not applicable (numerical diagnostic)'
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
