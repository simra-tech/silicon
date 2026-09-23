#!/usr/bin/env python3
"""Independent read-only evidence audit; retain failed and incomplete samples."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from run_586_calibration_sample import HERE, REFERENCE, TEMPERATURES, sample_deck, calibrate, sha
from run_586_population_control import phase_text
from run_586_source_control import load_wave
from run_bgr_substitution_draw_audit import read_group


def rounded_measurement_consistency(phase):
    # ngspice meas prints t_a/t_b at fewer digits than 'print freq'. Recomputing
    # exact frequency from those rounded times is not an exact-value comparison.
    times = []
    for name in ['t_a', 't_b']:
        token, = re.findall(r'(?m)^'+name+r'\s*=\s*([-+0-9.eE]+)', phase)
        value = Decimal(token)
        half_last_digit = Decimal(10)**value.as_tuple().exponent/2
        times.append((value, half_last_digit))
    delta = times[1][0]-times[0][0]
    uncertainty = times[0][1]+times[1][1]
    assert delta > uncertainty
    low, high = Decimal(16)/(delta+uncertainty), Decimal(16)/(delta-uncertainty)
    token, = re.findall(r'(?m)^freq\s*=\s*([-+0-9.eE]+)', phase)
    assert low <= Decimal(token) <= high
    return dict(status='passed printed-time rounding consistency', frequency_interval_Hz=[float(low), float(high)],
                scope='Printed meas time resolution only; exact retained freq scalar remains authoritative, no calibration tolerance change.')


def primitive_distinctness(inventory, vectors):
    converted = [{tag: dict(rows) for tag, rows in vector.items()} for vector in vectors]
    rows = []
    for primitive in inventory['primitives']:
        fingerprints = {tuple(float(v[primitive['group']][key]) for key in primitive['queries']) for v in converted}
        rows.append(dict(instance=primitive['instance'], group=primitive['group'], distinct_draws=len(fingerprints),
                         status='passed' if len(fingerprints) == len(vectors) else 'failed'))
    return dict(status='passed' if len(vectors) >= 2 and all(r['status'] == 'passed' for r in rows) else 'not run' if len(vectors) < 2 else 'failed',
                samples=len(vectors), primitives=len(rows), records=rows)


def audit_sample(run, seed):
    summary_path = run/'summary.json'
    if not summary_path.exists():
        return dict(seed=seed, run=run.name, status='not run', complete=False, evidence_status='not run')
    parent, = json.loads(summary_path.read_text())
    provenance = json.loads((run/'provenance.json').read_text())
    reference = json.loads((REFERENCE/'preparation.json').read_text())
    assert parent['seed'] == provenance['seed'] == seed
    assert provenance['runtime_identity'] == reference['runtime']
    assert provenance['reference_deck_sha256'] == sha(REFERENCE/'probe.cir')
    assert provenance['reference_preparation_sha256'] == sha(REFERENCE/'preparation.json')
    assert sha(run/'runner.py') == provenance['runner_sha256']
    assert provenance['source_hashes'] == reference['source_hashes']
    assert all(sha(run/name) == expected for name, expected in provenance['source_hashes'].items())
    assert sha(run/'population_inventory.json') == reference['inventory_sha256'] == provenance['inventory_sha256']
    leaves, vectors, frequencies = [], [], {}
    for entry in parent['leaves']:
        index, temperature = entry['index'], entry['temperature_C']
        assert TEMPERATURES[index] == temperature
        leaf = run/('p%02d' % index)
        row, = json.loads((leaf/'summary.json').read_text())
        assert sha(leaf/'summary.json') == entry['summary_sha256']
        assert row['index'] == index and row['temperature_C'] == temperature and row['status'] == entry['status']
        assert (leaf/'probe.cir').read_text() == sample_deck((REFERENCE/'probe.cir').read_text(), seed, temperature)
        assert sha(leaf/'probe.cir') == row['deck_sha256'] == entry['deck_sha256']
        assert all(sha(leaf/name) == expected for name, expected in provenance['source_hashes'].items())
        audit = dict(index=index, temperature_C=temperature, status=row['status'],
                     summary_sha256=sha(leaf/'summary.json'), log_sha256=sha(leaf/'run.log'),
                     deck_sha256=sha(leaf/'probe.cir'), full_reaudit='not run; failed leaf retained')
        if row['status'] == 'passed':
            assert row['runtime']['status'] == 'completed' and row['runtime']['returncode'] == 0 and not row['errors']
            assert json.loads((leaf/'run.json').read_text()) == row['runtime']
            log = (leaf/'run.log').read_text()
            assert not any(re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', line, re.I) for line in log.splitlines())
            phase = phase_text(log, 0)
            before = {tag: read_group(phase, 'P0_'+tag+'_BEFORE', keys) for tag, keys in reference['groups'].items()}
            after = {tag: read_group(phase, 'P0_'+tag+'_AFTER', keys) for tag, keys in reference['groups'].items()}
            assert sum(map(len, before.values())) == 3180 and before == after == row['parameters_before'] == row['parameters_after']
            assert row['full3180_status'] == 'passed'
            blob, wave = load_wave(leaf/'phase0.dat')
            assert sha(leaf/'probe.cir') == row['deck_sha256']
            assert hashlib.sha256(blob).hexdigest() == row['waveform_sha256']
            assert wave.shape == (row['wave_rows'], 13) and np.isfinite(wave).all() and abs(wave[-1, 0]-32e-6) < 1e-12
            measures = {k: float(v) for k, v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)', phase)}
            assert measures == row['measurements']
            audit['frequency_printed_time_consistency'] = rounded_measurement_consistency(phase)
            vce = float(max(np.abs(wave[:, i]-wave[:, j]).max() for i, j in [(7, 8), (9, 8), (10, 11), (12, 11)]))
            assert vce == row['t2f_hbt_external_vce_max_V'] and vce <= 1.6
            vectors.append(before)
            frequencies[temperature] = measures['freq']
            audit['full_reaudit'] = 'passed'
        leaves.append(audit)
    assert len({r['index'] for r in leaves}) == len(leaves)
    complete = len(leaves) == 4 and parent['status'] not in ['running', 'paused before next leaf; remaining conditions not run']
    if len(vectors) == 4:
        assert all(vector == vectors[0] for vector in vectors)
        assert parent['parameters_first_completed_leaf'] == vectors[0]
        assert parent['full3180_across_temperatures'] == 'passed'
        calibration = calibrate(frequencies)
        assert parent['calibration'] == calibration and parent['calibration_status'] == calibration['status']
        assert parent['status'] == ('passed' if calibration['status'] == 'passed' else 'failed original linear calibration')
    return dict(seed=seed, run=run.name, status=parent['status'], complete=complete, evidence_status='passed',
        numerical_completed_leaves=sum(r['status'] == 'passed' for r in leaves), leaves=leaves,
        summary_sha256=sha(summary_path), provenance_sha256=sha(run/'provenance.json'),
        full_parameter_vector_sha256=hashlib.sha256(json.dumps(parent.get('parameters_first_completed_leaf'), sort_keys=True).encode()).hexdigest()
            if parent.get('parameters_first_completed_leaf') is not None else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--first-seed', type=int, required=True)
    parser.add_argument('--last-seed', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert 74101 <= args.first_seed <= args.last_seed <= 74400 and not args.output.exists()
    records = []
    vectors = []
    for seed in range(args.first_seed, args.last_seed+1):
        run = HERE/'runs'/('t2f586-calibration-s%d-20260922-a' % seed)
        try:
            record = audit_sample(run, seed)
            records.append(record)
            if record['complete'] and record['numerical_completed_leaves'] == 4:
                parent, = json.loads((run/'summary.json').read_text())
                vectors.append(parent['parameters_first_completed_leaf'])
        except (AssertionError, OSError, ValueError, KeyError, IndexError) as error:
            records.append(dict(seed=seed, run=run.name, evidence_status='failed', complete=False, error=repr(error)))
    result = dict(status='passed read-only evidence audit' if all(r['evidence_status'] in ['passed', 'not run'] for r in records) else 'failed evidence audit',
        requested_samples=len(records), completed_samples=sum(r['complete'] for r in records),
        passed_samples=sum(r.get('status') == 'passed' for r in records),
        failed_complete_samples=sum(r['complete'] and r.get('status') != 'passed' for r in records),
        distinct_full_parameter_vectors=len({r['full_parameter_vector_sha256'] for r in records if r.get('full_parameter_vector_sha256')}),
        records=records, primitive_distinctness=primitive_distinctness(json.loads((REFERENCE/'population_inventory.json').read_text()), vectors),
        auditor_sha256=sha(Path(__file__)),
        scope='All requested samples retained including failures and notrun. Evidence integrity separate from originallinear±2C acceptance. No stage release or survivor-yield claim.')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'records'}, indent=2))


if __name__ == '__main__':
    main()
