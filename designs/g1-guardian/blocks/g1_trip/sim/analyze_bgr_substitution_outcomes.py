#!/usr/bin/env python3
"""Read retained source-substitution results; never run or reclassify a simulation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from run_bgr_substitution_draw_audit import read_group

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def warning_inventory(log):
    families, instances, hierarchy = Counter(), Counter(), Counter()
    first_sim_time, last_sim_time = {}, {}
    substring_only_parameter_lines = 0
    current_time = None
    for line in log.splitlines():
        progress = re.search(r'Reference value\s*:\s*(\S+)', line)
        if progress:
            current_time = float(progress[1])
        if 'warning' not in line.lower() and not re.search(r'\bnan\b', line, re.I):
            if 'nan' in line.lower():
                substring_only_parameter_lines += 1
            continue
        match = re.match(r'OSDI\(debug\) (\S+): (.*)', line)
        instance, family = (match[1], match[2]) if match else ('unclassified', line)
        families[family] += 1
        instances[instance] += 1
        hierarchy[instance.split('.')[1] if '.' in instance else 'unclassified'] += 1
        first_sim_time.setdefault(family, current_time)
        last_sim_time[family] = current_time
    return {'count': sum(families.values()), 'families': dict(families),
            'retained_runner_nan_substring_false_positives': substring_only_parameter_lines,
            'instances': dict(instances), 'hierarchy_counts': dict(hierarchy),
            'first_preceding_progress_time_s': first_sim_time,
            'last_preceding_progress_time_s': last_sim_time,
            'scope': 'Progress values bracket printed warnings, not exact event times. None means no preceding progress report.'}


def progress_windows(path):
    if not path.exists():
        return {'status': 'not available'}
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    windows = []
    # The declared top clock rises at20ns+200ns*k and falls100.2ns later.
    for lo, hi in [(0, 19.9), (20, 20.2), (20.2, 119.9), (120.2, 120.4),
                   (120.4, 219.9), (220, 220.2), (320.2, 320.4),
                   (420, 420.2), (520.2, 520.4), (620, 620.2)]:
        selected = [r for r in rows if lo*1e-9 <= r.get('last_reported_sim_time_s', -1) <= hi*1e-9]
        windows.append({'simulation_window_ns': [lo, hi], 'progress_samples': len(selected),
                        'first_wall_s': selected[0]['wall_s'] if selected else None,
                        'last_wall_s': selected[-1]['wall_s'] if selected else None,
                        'observed_wall_span_s': selected[-1]['wall_s']-selected[0]['wall_s'] if selected else None})
    return {'status': 'available', 'sample_count': len(rows), 'windows': windows,
            'scope': 'One-second sampled progress only; wall spans are observed lower bounds, not accepted-step counts or exact event attribution.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = {}
    for temperature in ['room', 'hot']:
        run = SIM / 'qualification' / ('joint-bgr586-nominal-substitution-%s-20260922-a' % temperature)
        prep = json.loads((run / 'preparation.json').read_text())
        result, = json.loads((run / 'summary.json').read_text())
        log = (run / 'run.log').read_text()
        baseline, = json.loads((SIM / 'qualification' / prep['required_baseline_op_run'] / 'summary.json').read_text())
        inventory = json.loads((run / 'non_bgr_inventory.json').read_text())
        before = read_group(log, 'NON_BGR_BEFORE', inventory['queries'])
        bgr = read_group(log, 'BGR_BEFORE', prep['candidate2842_queries'])
        reference = SIM / 'qualification' / prep['reference_run']
        original, = json.loads((reference / 'summary.json').read_text())
        state = json.loads((run / 'run.json').read_text())
        results[temperature] = {
            'run': run.name, 'reference_run': reference.name,
            'summary_sha256': hashlib.sha256((run / 'summary.json').read_bytes()).hexdigest(),
            'log_sha256': hashlib.sha256((run / 'run.log').read_bytes()).hexdigest(),
            'solver_status': result['solver_status'], 'watchdog_status': result['watchdog_status'],
            'wall_s': result['wall_s'], 'last_reported_sim_time_s': state.get('last_reported_sim_time_s'),
            'required_endpoint_s': 1.02e-6, 'before_nonBGR8670_exact': before == baseline['ordered_parameter_groups']['NON_BGR_ALL'],
            'before_BGR2842_nominal_exact': [v for k, v in bgr] == prep['candidate2842_nominal_expected'],
            'complete_before_after_checks': result['parameter_audit']['checks'],
            'wave_export_exists': any(run.glob('*.dat*')),
            'selected_lower_point_both_LOW': result['selected_lower_point_both_LOW'],
            'decision_analysis_status': result['wave_analysis']['sampling_status'],
            'warnings': warning_inventory(log), 'progress': progress_windows(run / 'run.progress.jsonl'),
            'original_reference_wall_s': original['wall_s'],
            'original_reference_warnings': warning_inventory((reference / (prep['case'] + '.log')).read_text()),
            'original_reference_wave_analysis': original['wave_analysis'],
            'scope': 'No waveform parity across changed BGR source. Missing AFTER/endpoint is not passed by BEFORE parity.'}
    output = {'scope': 'Controlled model-level source diagnostic, not physical qualification, calibration, yield or original-failure waiver.',
              'results': results, 'hot_numerical_acceptance': 'failed watchdog; full endpoint and AFTER comparisons not run',
              'new_simulations': 'not run by this reader'}
    with args.output.open('x') as stream:
        json.dump(output, stream, indent=2)
        stream.write('\n')
    print(json.dumps({key: {k: row[k] for k in ['solver_status', 'wall_s', 'last_reported_sim_time_s', 'before_nonBGR8670_exact', 'before_BGR2842_nominal_exact', 'decision_analysis_status']} for key, row in results.items()}, indent=2))


if __name__ == '__main__':
    main()
