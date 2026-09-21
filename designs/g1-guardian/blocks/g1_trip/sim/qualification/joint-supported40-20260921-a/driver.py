#!/usr/bin/env python3
"""Replay frozen joint calibration at a lower hard setting with in-range guards."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

SIM = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--image-id', required=True)
    p.add_argument('--baseline-run', required=True)
    p.add_argument('--seed', type=int, default=71001)
    p.add_argument('--hard-nominal-code', type=int, default=204)
    p.add_argument('--temperatures', default='25,-40,125')
    a = p.parse_args()
    baseline = SIM / 'qualification' / a.baseline_run / 'summary.json'
    sample = next(r for r in json.loads(baseline.read_text()) if r['seed'] == a.seed)
    if sample.get('bracket_status') != 'passed selected probes':
        raise ValueError('Baseline must have completed its calibration bracket')
    hard_target = a.hard_nominal_code * 1.04 / 5300
    guards = [.9 * hard_target, 1.1 * hard_target]
    if not 0 <= a.hard_nominal_code <= 255 or max(guards) > .05:
        raise ValueError('Hard code and both robust guards must fit specified range')
    raw_code = a.hard_nominal_code + sample['signed_correction_codes']['hard']
    codes = {'soft': sample['corrected_codes']['soft'],
             'hard': max(0, min(255, raw_code))}
    out = SIM / 'qualification' / a.run_id
    out.mkdir(parents=True, exist_ok=False)
    (out / 'driver.py').write_text(Path(__file__).read_text())
    report = {'arguments': sys.argv[1:], 'baseline_campaign': a.baseline_run,
              'seed': a.seed, 'hard_nominal_code': a.hard_nominal_code,
              'ideal_nominal_hard_target_V': hard_target,
              'frozen_correction': sample['signed_correction_codes'],
              'programmed_codes': codes, 'hard_clipped': raw_code != codes['hard'],
              'scope': 'Isolated supported-setting characterization; canonical defaults unchanged. Exact ideal-code target used for ±10% guards. Same baseline sample fingerprint required. Only selected-code monotonicity qualified.',
              'status': 'not run to completion', 'probes': []}
    fp = sample['probes'][0]['fingerprints']
    for temp in map(float, a.temperatures.split(',')):
        for index, shunt in enumerate(guards):
            leaf = f'{a.run_id}-p{len(report["probes"]):02d}'
            cmd = [sys.executable, str(SIM/'run_kickback_qualification.py'),
                   '--run-id', leaf, '--image-id', a.image_id, '--seed', str(a.seed),
                   '--actual-bgr', '--soft-code', str(codes['soft']),
                   '--hard-code', str(codes['hard']), '--shunt-value', str(shunt),
                   '--temperature', str(temp), '--offsets-mv=0', '--tstop-us', '.52',
                   '--maxstep-ns', '.2', '--tight', '--gear']
            rc = subprocess.run(cmd, cwd=SIM).returncode
            rpath = SIM/'qualification'/leaf/'summary.json'
            entry = {'run': leaf, 'shunt_V': shunt, 'temperature_C': temp,
                     'expected_hard_high': bool(index), 'runner_returncode': rc,
                     'solver_status': 'not run', 'decision_status': 'not run'}
            if rpath.exists():
                result = json.loads(rpath.read_text())[0]
                entry.update(solver_status=result['solver_status'],
                             wall_s=result['wall_s'],
                             fingerprints_match_baseline=result.get('fingerprints') == fp,
                             sampled_outputs_V=result.get('both_sampled_output_V'))
                if result['solver_status'] == 'passed' and entry['fingerprints_match_baseline']:
                    values = result['both_sampled_output_V']['hard']
                    valid = len(values) == 3 and all(v > .6 if index else v < .6 for v in values)
                    entry['decision_status'] = 'passed' if valid else 'failed'
            report['probes'].append(entry)
            (out/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    report['status'] = 'passed' if all(r['decision_status'] == 'passed' for r in report['probes']) else 'failed'
    (out/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
