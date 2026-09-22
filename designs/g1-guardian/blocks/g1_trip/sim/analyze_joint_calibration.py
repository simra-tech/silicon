#!/usr/bin/env python3
"""Summarize preserved joint-calibration evidence without omitting failed samples."""
import argparse
import collections
import datetime
import json
import math
import statistics
from pathlib import Path


def summarize(paths):
    rows = []
    duplicates = []
    seen = set()
    for path in paths:
        file = path / 'summary.json'
        if not file.exists():
            rows.append({'campaign': path.name, 'seed': None,
                         'completion': 'not run', 'reason': 'no summary yet'})
            continue
        for sample in json.loads(file.read_text()):
            seed = sample['seed']
            if seed in seen:
                duplicates.append(seed)
            seen.add(seed)
            probes = [dict(p) for p in sample.get('probes', [])]
            for probe in probes:
                rawpath=path.parent/probe.get('evidence_run',probe['run'])/'summary.json'
                if rawpath.exists():
                    raw=json.loads(rawpath.read_text())[0]
                    probe['watchdog_status']=raw.get('watchdog_status')
                    if raw.get('watchdog_status')=='interrupted':
                        probe['solver_status']='not run to completion'
                        probe['completion_reason']='owner interruption; raw solver classification retained separately'
            bracket = sample.get('bracket_status', 'not run')
            guards = sample.get('guards_status', 'not run')
            residual = sample.get('residual_half_mV_status', 'not run')
            finished = (bracket == 'passed selected probes'
                        and guards in ('passed', 'failed')
                        and residual in ('passed', 'failed'))
            # Electrical failure and numerical failure are separate. A driver may
            # stop a sample early after an ambiguous or non-bracketing probe.
            rejected = sample.get('status') == 'failed'
            guard_expect = {.027: {'soft': False, 'hard': False},
                            .033: {'soft': True, 'hard': False},
                            .045: {'soft': True, 'hard': False},
                            .055: {'soft': True, 'hard': True}}
            if sample.get('guard_definitions'):
                guard_expect={g['shunt_V']:g['expected'] for g in sample['guard_definitions']}
            observed_guards = [
                {'run': probe['run'], 'shunt_V': probe['shunt_V'],
                 'temp_C': probe['temp_C'],
                 'range_scope': 'within specified range' if probe['shunt_V'] <= .05
                                else 'outside-contract diagnostic',
                 'expected': guard_expect[probe['shunt_V']],
                 'observed': probe.get('decisions'),
                 'status': 'not run to completion' if probe.get('solver_status') != 'passed' else 'passed' if probe.get('status') == 'passed' and
                     probe.get('decisions') == guard_expect[probe['shunt_V']] else 'failed'}
                for probe in probes if probe['shunt_V'] in guard_expect and
                probe['codes'] == sample.get('corrected_codes')]
            cal_codes={k:math.floor(sum(v)/2+.5) for k,v in (sample.get('brackets') or {}).items()}
            observed_residuals=[]
            for probe in probes:
                if probe['shunt_V'] not in (.0245,.0255) or probe['codes']!=cal_codes: continue
                expected=probe['shunt_V']==.0255
                ok=probe.get('status')=='passed' and probe.get('decisions') and all(v==expected for v in probe['decisions'].values())
                observed_residuals.append({'run':probe['run'],'evidence_run':probe.get('evidence_run',probe['run']),
                    'shunt_V':probe['shunt_V'],'temp_C':probe['temp_C'],'expected_both_high':expected,
                    'observed':probe.get('decisions'),'status':'not run to completion' if probe.get('solver_status')!='passed' else 'passed' if ok else 'failed'})
            recoveries=[]
            for probe in probes:
                if probe.get('recovery_alias'):
                    original=json.loads((path.parent/probe['run']/'summary.json').read_text())[0]
                    recoveries.append({'original_run':probe['run'],
                        'original_solver_status':original['solver_status'],
                        'original_watchdog_status':original['watchdog_status'],
                        'original_wall_s':original['wall_s'],
                        'selected_recovery_run':probe['evidence_run'],
                        'selected_solver_status':probe['solver_status'],
                        'selected_wall_s':probe['wall_s']})
            row = {'campaign': path.name, 'seed': seed,
                   'completion': 'not run' if not probes else 'completed checks' if finished else
                   'interrupted calibration' if rejected and any(p.get('watchdog_status')=='interrupted' for p in probes) else 'rejected calibration' if rejected else 'not run to completion',
                   'bracket_status': bracket, 'guards_status': guards,
                   'residual_half_mV_status': residual,
                   'hard_full_robust_band_status': sample.get('hard_full_robust_band_status','not qualified: nominal50mV upper guard55mV is outside specified SENSE range'),
                   'hard_nominal_code':sample.get('hard_nominal_code',254),
                   'outside_range_probe_ids': [p['run'] for p in probes if p.get('shunt_V', 0) > .05 or p.get('shunt_V', 0) < 0],
                   'guard_scope': 'Expected guard definitions are explicit; each point carries its range scope. Outside-range probes do not establish full-band acceptance.',
                   'brackets': sample.get('brackets'),
                   'correction_codes': sample.get('signed_correction_codes'),
                   'programmed_codes': sample.get('corrected_codes'),
                   'clipped': sample.get('clipped'),
                   'completed_probe_count': len(probes),
                   'frozen27_sample_parameters_exact': bool(probes)
                   and len(probes[0].get('fingerprints', [])) == 27
                   and all(p.get('fingerprints') == probes[0]['fingerprints'] for p in probes),
                   'missing_or_short_fingerprint_probes': sum(len(p.get('fingerprints', [])) != 27 for p in probes),
                   'solver_status_counts': dict(collections.Counter(p.get('solver_status','not run') for p in probes)),
                   'retained_recovery_attempts': recoveries,
                   'probe_solver_failures': sum(p.get('solver_status') == 'failed' for p in probes),
                   'probe_incomplete_count': sum(p.get('solver_status') == 'not run to completion' for p in probes),
                   'owner_interrupted_count': sum(p.get('watchdog_status') == 'interrupted' for p in probes),
                   'probe_decision_rejections': sum(p.get('solver_status') == 'passed' and
                       p.get('status') != 'passed' for p in probes),
                   'fingerprint_mismatches': sum(p.get('physical_sample_fingerprint_matches') is False
                                                  for p in probes),
                   'probe_wall_s': sum(p.get('wall_s', 0) for p in probes),
                   'observed_guard_results': observed_guards,
                   'observed_residual_results': observed_residuals,
                   'failed_in_range_guard_probes': [g['run'] for g in observed_guards if g['status'] == 'failed' and g['shunt_V'] <= .05],
                   'failed_outside_range_diagnostic_probes': [g['run'] for g in observed_guards if g['status'] == 'failed' and g['shunt_V'] > .05],
                   'failed_residual_probes': [g['probe'] for g in sample.get('residual_half_mV_checks', [])
                                              if g['status'] == 'failed']}
            rows.append(row)
    times = [p['wall_s'] for path in paths if (path / 'summary.json').exists()
             for sample in json.loads((path / 'summary.json').read_text())
             for p in sample.get('probes', []) if p.get('solver_status') == 'passed']
    count = lambda field: dict(collections.Counter(r.get(field, 'not run') for r in rows))
    return {
        'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': 'Actual joint chain; selected-code bracketing, frozen system-band and calibration-point residual checks. No full-code monotonicity or physical yield claim.',
        'campaigns': [p.name for p in paths],
        'duplicate_seeds': duplicates,
        'combine_status': 'failed duplicate seeds; do not infer aggregate sample count' if duplicates else 'passed unique seeds',
        'sample_completion_counts': count('completion'),
        'bracket_status_counts': count('bracket_status'),
        'guards_status_counts': count('guards_status'),
        'residual_status_counts': count('residual_half_mV_status'),
        'clipped_count': {k: sum(bool((r.get('clipped') or {}).get(k)) for r in rows)
                          for k in ('soft', 'hard')},
        'solver_failures': sum(r.get('probe_solver_failures', 0) for r in rows),
        'incomplete_probes': sum(r.get('probe_incomplete_count',0) for r in rows),
        'owner_interrupted_probes': sum(r.get('owner_interrupted_count',0) for r in rows),
        'solver_failure_count_scope': 'Selected probe evidence only; timeouts and owner interruptions are separately incomplete, not solver failures. Original watchdog failures/incompletions replaced by explicit recovery aliases remain separately counted and listed; no independent-sample duplication.',
        'retained_original_incomplete_or_failed_attempts': sum(len(r.get('retained_recovery_attempts', [])) for r in rows),
        'decision_rejections': sum(r.get('probe_decision_rejections', 0) for r in rows),
        'fingerprint_mismatches': sum(r.get('fingerprint_mismatches', 0) for r in rows),
        'explicit_frozen27_audit_failures': sum(r.get('frozen27_sample_parameters_exact') is not True for r in rows),
        'missing_or_short_fingerprint_probes': sum(r.get('missing_or_short_fingerprint_probes', 0) for r in rows),
        'selected_probe_count': sum(r.get('completed_probe_count', 0) for r in rows),
        'probe_wall_s_median': statistics.median(times) if times else None,
        'forecast_100_samples_4cores_hours': statistics.median(times)*28*100/4/3600 if times else None,
        'forecast_300_samples_4cores_hours': statistics.median(times)*28*300/4/3600 if times else None,
        'forecast_limit': '28 probes/sample, four continuously available cores; forecasts exclude failures, extra checks, orchestration and further numerical qualification.',
        'samples': rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaigns', nargs='+', type=Path)
    parser.add_argument('--output', type=Path, help='New snapshot file; existing files are not overwritten')
    parser.add_argument('--summary-only', action='store_true', help='Keep full output file, print aggregate fields only')
    args = parser.parse_args()
    result = summarize(args.campaigns)
    data = json.dumps(result, indent=2) + '\n'
    if args.output:
        with args.output.open('x') as f:
            f.write(data)
    print(json.dumps({k:v for k,v in result.items() if k != 'samples'}, indent=2) if args.summary_only else data, end='\n' if args.summary_only else '')


if __name__ == '__main__':
    main()
