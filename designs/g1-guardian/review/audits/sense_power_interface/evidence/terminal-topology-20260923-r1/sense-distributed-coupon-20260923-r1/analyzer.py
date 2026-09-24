#!/usr/bin/env python3
"""Fail-closed signed-current/power analysis of the prospective passive coupon."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_vector(name):
    """Only case and ngspice's explicit voltage-source branch-current notation."""
    value = name.strip().lower()
    if value.endswith('#branch'):
        value = 'i('+value[:-7]+')'
    return value


def parse_waveform(path, expected):
    lines = path.read_text().splitlines()
    assert lines, 'Empty waveform'
    header = lines.pop(0).split()
    assert [normalize_vector(v) for v in header] == [normalize_vector(v) for v in expected], {
        'actual_vector_header': header, 'expected_vector_header': expected}
    return [[float(x) for x in line.split()] for line in lines if line.strip()]


def inspect_log(text):
    fatal = re.compile(r'\b(?:error|fatal)\b|no such (?:vector|device)|unknown (?:parameter|vector|device)|'
                       r'simulation(?:\(s\))? aborted|doanalyses:.*failed|timestep too small|'
                       r'segmentation fault|singular matrix', re.I)
    errors = [line for line in text.splitlines() if fatal.search(line)]
    warnings = [line for line in text.splitlines() if re.search(r'\bwarning\b', line, re.I)]
    return dict(status='failed' if errors else 'passed', fatal_lines=errors, warning_lines=warnings)


def audit(rows, direct=False):
    columns = 5 if direct else 12
    if len(rows) < 10 or any(len(row) != columns or not all(math.isfinite(x) for x in row) for row in rows):
        return dict(status='failed', reason='missing, malformed or nonfinite vectors')
    times = [r[0] for r in rows]
    if any(a >= b for a, b in zip(times, times[1:])) or abs(times[-1]-1.2e-6) > 1e-15:
        return dict(status='failed', reason='nonmonotonic or incomplete transient')
    if direct:
        residual = max(abs(r[1]-r[2]) for r in rows)
        return dict(status='passed' if residual <= 5e-11 else 'failed', voltage_residual_V=residual)
    voltage = []; current = []; kcl = []; power = []; contact = []
    for r in rows:
        _, _, model_v, p0, p1, _, model_i, raw0, raw1, av, f0, f1 = r
        i0 = raw0-f0*1e-12; i1 = raw1-f1*1e-12
        voltage.append(max(abs(model_v-(p0+2*p1)/3), abs(av-model_v)))
        contact.append(max(abs(p0-f0), abs(p1-f1)))
        current.append(max(abs(i0-model_i/3), abs(i1-2*model_i/3)))
        kcl.append(abs(i0+i1-model_i))
        power.append(abs(p0*i0+p1*i1-model_v*model_i))
    maximum = dict(voltage_residual_V=max(voltage), contact_voltage_residual_V=max(contact),
                   signed_current_residual_A=max(current), signed_KCL_residual_A=max(kcl),
                   power_residual_W=max(power))
    passed = (max(voltage+contact) <= 5e-11 and max(current+kcl) <= 1e-12 and max(power) <= 1e-12)
    return dict(maximum, status='passed' if passed else 'failed', rows=len(rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coupon', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    contract = json.loads((args.coupon/'contract.json').read_text())
    results = []; waves = {}
    for case in contract['cases']:
        name = case['name']; path = args.coupon/name/'waveform.dat'
        assert sha(args.coupon/name/'coupon.cir') == case['deck_sha256']
        record = dict(name=name, status='not run', accepted=False)
        if path.exists():
            try:
                log = path.with_name('simulator.log'); assert log.is_file(), 'Missing simulator log'
                log_gate = inspect_log(log.read_text(errors='replace')); record['simulator_log'] = log_gate
                assert log_gate['status'] == 'passed', 'Simulator fatal/error text, independent of exit status'
                rows = parse_waveform(path, case['columns'])
                result = audit(rows, direct=name == 'direct-zero-r'); waves[name] = rows
                expected = 'failed' if name == 'wrong-current-sign' else 'passed'
                record.update(result, waveform_sha256=sha(path), expected_status=expected,
                              accepted=result['status'] == expected)
                if name == 'wrong-current-sign':
                    record['accepted'] = (result.get('signed_current_residual_A', 0) > 1e-12
                                          and result.get('power_residual_W', 0) > 1e-12)
            except Exception as exc:
                record.update(status='failed analysis', error=repr(exc), accepted=False)
        results.append(record)
    direct = waves.get('direct-zero-r'); adapter = waves.get('adapter-zero-r')
    zero = dict(status='not run')
    if direct is not None and adapter is not None:
        same_time = [r[0] for r in direct] == [r[0] for r in adapter]
        same_model_voltage = [r[2] for r in direct] == [r[2] for r in adapter]
        zero = dict(status='passed' if same_time and same_model_voltage else 'failed',
                    exact_time_grid=same_time, exact_model_voltage=same_model_voltage,
                    scope='Passive coupon model-node voltage only, not full SENSE parity; no interpolation')
    passed = all(r['accepted'] for r in results) and zero['status'] == 'passed'
    output = dict(status='passed conditional passive implementation controls' if passed else 'failed or incomplete conditional passive controls',
                  contract_sha256=sha(args.coupon/'contract.json'), script_sha256=sha(Path(__file__)),
                  cases=results, zero_R=zero,
                  not_run=['Actual SENSE distributed weights', 'Full11512 parameter/wave parity',
                           'Intrinsic compact-model applicability', 'Physical PEX/electrical adoption'])
    args.output.write_text(json.dumps(output, indent=2)+'\n'); print(json.dumps(output, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__': main()
