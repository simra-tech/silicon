#!/usr/bin/env python3
"""Read-only retained120/240s watchdog and realized-parameter observations."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    original = HERE/'bgr586-screen80-b6-20260922-a/s44090'
    recovery = HERE/'bgr586-s44090-recovery240s-20260922-a/s44090'
    records = []
    for run in [original, recovery]:
        log = (run/'run.log').read_text()
        params = re.findall(r'^(@\S+)\s*=\s*(\S+)', log, re.M)
        progress = [float(v) for v in re.findall(r'Reference value\s*:\s*([-+\deE.]+)', log)]
        state = json.loads((run/'run.json').read_text())
        records.append({'logical_run': str(run.relative_to(ROOT)), 'state': state['status'],
                        'wall_s': state['wall_s'], 'deck_sha256': sha(run/'nominal.cir'),
                        'log_sha256': sha(run/'run.log'), 'parameters_printed': params,
                        'last_reported_sweep_temperature_C': progress[-1] if progress else None,
                        'reported_sweep_progress_C': progress,
                        'dynamic_gmin_attempts': log.count('Starting dynamic gmin stepping'),
                        'dynamic_gmin_failures': log.count('Dynamic gmin stepping failed'),
                        'true_gmin_completions': log.count('True gmin stepping completed'),
                        'error_lines': [line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|analysis aborted)', line)],
                        'voltage_warning_count': log.count('voltage is greater than specified by vmax'),
                        'waveform_exported': (run/'nominal.dat').exists()})
    x, y = [r['parameters_printed'] for r in records]
    assert len(x) == len(y) == 2842 and x == y
    assert records[0]['deck_sha256'] == records[1]['deck_sha256']
    ref = json.loads((HERE/'runs/bgr_one_draw_20260922_r1/manifest.json').read_text())
    assert [k for k, v in x] == ref['parameters']
    population = [ref['cases'][0]['parameters_before']]
    for pattern in ['bgr586-screen20-b*-20260922-a', 'bgr586-screen80-b*-20260922-a', 'bgr586-screen200-b*-20260922-a']:
        for run in HERE.glob(pattern):
            population += [r['parameters_before'] for r in json.loads((run/'summary.json').read_text()) if r['status'] == 'passed']
    assert len(population) == 299
    mat = np.array([[float(v) for k, v in row] for row in population])
    values = np.array([float(v) for k, v in x])
    sd = mat.std(axis=0)
    z = (values-mat.mean(axis=0))/np.where(sd > 0, sd, np.inf)
    extremes = [{'parameter': x[i][0], 'value': float(values[i]), 'empirical_standardized_distance': float(z[i]),
                 'completed299_min': float(mat[:, i].min()), 'completed299_max': float(mat[:, i].max())}
                for i in np.argsort(abs(z))[-10:][::-1]]
    out = {'status': 'passed read-only failed-attempt observation, not numerical recovery',
           'attempts': records, 'all2842_original_before_recovery_before_exact': True,
           'after_inventory_status': 'not run to completion in either attempt',
           'waveform_prefix_parity': 'not applicable: neither failed DC sweep exported a waveform',
           'completed_population_reference_count': 299, 'largest_empirical_parameter_distances': extremes,
           'interpretation': 'Same finite initial2842 realization and exact input deck; longer watchdog progressed from15C to25C while repeated gmin recovery remained slow. No terminal TC, supply/load test, numerical success or recovery claim. Parameter ranks are descriptive across completed299 and do not establish cause or justify dropping44090.',
           'further_simulation_status': 'not run; no additional retry or solver/acceptance change'}
    with a.output.open('x') as stream:
        json.dump(out, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in out.items() if k not in ['attempts', 'largest_empirical_parameter_distances']}, indent=2))


if __name__ == '__main__':
    main()
