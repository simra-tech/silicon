#!/usr/bin/env python3
"""Original per-corner nominal-rail calibration, frozen at four adverse endpoints."""
import argparse
import json
from pathlib import Path
from prepare_586_adverse_controls import HERE, CORNERS, CONDITIONS, sha


def calibrate(rows):
    assert set(rows) == {label for label, temperature, vdda, vdd, role in CONDITIONS}
    f25, f100 = rows['cal25'], rows['cal100']
    slope = (f100-f25)/75
    assert slope > 0
    points = []
    for label, temperature, vdda, vdd, role in CONDITIONS:
        inferred = 25+(rows[label]-f25)/slope
        residual = inferred-temperature
        points.append(dict(label=label, temperature_C=temperature, VDDA_V=vdda, VDD_V=vdd, role=role,
            frequency_Hz=rows[label], inferred_temperature_C=inferred, linear_error_C=residual,
            linear_status='passed' if abs(residual) <= 2 else 'failed'))
    worst = max(abs(p['linear_error_C']) for p in points if p['role'] == 'independent')
    return dict(status='passed' if worst <= 2 else 'failed', slope_Hz_per_C=slope, points=points,
                maximum_independent_abs_residual_C=worst,
                criterion='Original samecorner25/100C at3.3/1.2V calibratedonce; fourheldoutlow/highrailendpoints≤2C; no refit/LUT')


def analyze_corner(entries, receipts=None, errors=None):
    labels = {label for label, temperature, vdda, vdd, role in CONDITIONS}
    assert set(entries) <= labels
    missing = sorted(labels-set(entries))
    report = dict(status='not run' if missing else 'failed controls', missing_receipts=missing,
        control_statuses={label: entries[label]['control_status'] if label in entries else 'not run'
                          for label in sorted(labels)}, receipts_sha256=receipts or {}, receipt_errors=errors or {})
    report['known_failed_controls'] = sorted(label for label, row in entries.items()
        if row['control_status'] != 'passed' or row.get('full3180_status') != 'passed')
    if errors or report['known_failed_controls']:
        report['status'] = 'failed controls; incomplete coverage' if missing else 'failed controls'
        return report
    if missing:
        return report
    vector = entries['cal25']['parameters_before']
    exact = all(e['parameters_before'] == e['parameters_after'] == vector for e in entries.values())
    report['full3180_samecorner_allconditions_status'] = 'passed' if exact else 'failed'
    if not exact:
        report['status'] = 'failed same-corner parameter identity'
        return report
    try:
        calibration = calibrate({label: e['measurements']['freq'] for label, e in entries.items()})
        report.update(status=calibration['status'], calibration=calibration)
    except (AssertionError, KeyError, TypeError, ZeroDivisionError) as error:
        report.update(status='failed calibration analysis', analysis_error=repr(error))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    packet = json.loads(args.packet.read_text())
    result = dict(status='not run to completion', corners={}, packet_sha256=sha(args.packet),
        scope='Two deterministic final586 selected-adverse corners only. Historical six-condition calibration policy retained; no statistical/adoption/newphysicalCC claim.')
    for corner in CORNERS:
        cases = [c for c in packet['cases'] if c['corner'] == corner]
        assert len(cases) == 6
        entries, receipts, errors = {}, {}, {}
        for case in cases:
            run = HERE/'runs'/case['run_id']
            if not (run/'summary.json').exists():
                continue
            try:
                row, = json.loads((run/'summary.json').read_text())
                assert sha(run/'preparation.json') == case['preparation_sha256'] and sha(run/'probe.cir') == case['deck_sha256']
                receipts[case['run_id']] = {n: sha(run/n) for n in ['summary.json', 'provenance.json', 'preparation.json']}
                entries[case['label']] = row
            except (OSError, ValueError, AssertionError, KeyError) as error:
                errors[case['label']] = repr(error)
        result['corners'][corner] = analyze_corner(entries, receipts, errors)
    statuses = [c['status'] for c in result['corners'].values()]
    result['status'] = ('passed selected-adverse deterministic controls' if all(s == 'passed' for s in statuses)
        else 'failed selected-adverse deterministic controls; failures retained' if any(s.startswith('failed') for s in statuses)
        else 'not run to completion')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
