#!/usr/bin/env python3
"""Strict archived full-population transient qualification, without waivers."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from prepare_joint586_transients import transform
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import analyze_wave
from wave_archive import open_wave

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
LABELS = ['enabled', 'repeat', 'hot', 'cold', 'disabled', 'disabledchanged', 'return']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_wave(first, second):
    """Decoded byte equality is independent of numeric equality and decisions."""
    a = [list(map(float, line.split())) for line in first.decode().splitlines()[1:] if line.strip()]
    b = [list(map(float, line.split())) for line in second.decode().splitlines()[1:] if line.strip()]
    same_grid = len(a) == len(b) and all(x[0] == y[0] for x, y in zip(a, b))
    return {'decoded_bytes_exact': first == second, 'numeric_rows_exact': a == b,
            'time_grid_exact': same_grid, 'first_rows': len(a), 'second_rows': len(b),
            'maximum_abs_node_delta_V_on_exact_grid': max((abs(xv-yv) for x, y in zip(a, b) for xv, yv in zip(x[1:], y[1:])), default=0) if same_grid else None}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    records, waves, vectors = {}, {}, {}
    for label in LABELS:
        run = SIM/'qualification'/(a.prefix+'-'+label)
        if not (run/'summary.json').exists():
            records[label] = {'run': run.name, 'status': 'not run to completion'}
            continue
        row, = json.loads((run/'summary.json').read_text())
        record = {'run': run.name, 'status': 'failed', 'solver_status': row['solver_status'],
                  'wall_s': row['wall_s'], 'errors': row['errors'],
                  'receipts_sha256': {name: sha(run/name) for name in ['summary.json', 'preparation.json', 'provenance.json', 'population_transient.cir', 'run.log', 'population_inventory.json']}}
        records[label] = record
        if row['parameter_wave_contract_status'] != 'passed' or row['decision_sampling_status'] != 'passed':
            continue
        prep = json.loads((run/'preparation.json').read_text())
        prov = json.loads((run/'provenance.json').read_text())
        reference = SIM/'qualification'/prep['qualified_op_run']
        op, = json.loads((reference/'summary.json').read_text())
        template = SIM/'qualification'/prep['template_run']
        assert op['op_qualification_status'] == 'passed'
        assert all(prov['input_checks'].values()) and prov['runtime_identity'] == prep['expected_runtime_identity']
        assert all(sha(ROOT/name) == value for name, value in prep['live_bindings_sha256'].items())
        assert all(sha(run/name) == sha(reference/name) == value for name, value in prep['source_hashes'].items())
        assert sha(run/'population_inventory.json') == prep['inventory_sha256']
        assert (run/'population_transient.cir').read_text() == transform((template/'hard_+0mV.cir').read_text(), template.name, run.name, prep['seed'], prep['temperatures_C'])
        log = (run/'run.log').read_text()
        phases = []
        waves[label], vectors[label] = [], []
        assert len(row['phases']) == len(prep['temperatures_C'])
        for index, phase in enumerate(row['phases']):
            section, = re.findall(r'^PHASE%d_BEGIN\n(.*?)^PHASE%d_END$' % (index, index), log, re.M | re.S)
            expected = op['phases'][prep['qualified_op_phase_indices'][index]]['parameters_before']
            params = phase_parameters(section, prep['groups'], expected)
            assert all(params[key] == phase[key] for key in params)
            with open_wave(run/('phase%d.dat' % index), 'rb') as stream:
                raw = stream.read()
            assert hashlib.sha256(raw).hexdigest() == phase['decoded_wave_sha256']
            lines = raw.decode().splitlines()
            assert len(lines[0].split()) == 18
            data = [list(map(float, line.split())) for line in lines[1:] if line.strip()]
            assert len(data) == phase['wave_rows'] and all(len(r) == 18 and all(math.isfinite(v) for v in r) for r in data)
            assert data[0][0] == 0 and abs(data[-1][0]-1.02e-6) < 1e-18
            assert all(x[0] < y[0] for x, y in zip(data, data[1:]))
            analysis = analyze_wave([r[:13] for r in data], prep['prospective_sampling'])
            assert analysis == phase['wave_analysis'] and analysis['sampling_status'] == 'passed'
            waves[label].append(raw)
            vectors[label].append(params['parameters_before'])
            phases.append({'temperature_C': phase['temperature_C'], 'decoded_wave_sha256': phase['decoded_wave_sha256'],
                           'wave_rows': len(data), 'decisions': phase['decisions'], 'sampling_status': analysis['sampling_status']})
        record.update(status='passed', phases=phases, warnings=row['warnings'])
    comparisons, checks = {}, {}
    pairs = [('enabled_repeat', 'enabled', 0, 'repeat', 0), ('disabled_seed_change', 'disabled', 0, 'disabledchanged', 0),
             ('return_initial_vs_standalone', 'enabled', 0, 'return', 0), ('return_hot_vs_standalone', 'hot', 0, 'return', 1),
             ('return_cold_vs_standalone', 'cold', 0, 'return', 2), ('same_instance_room_return', 'return', 0, 'return', 3)]
    for name, left, li, right, ri in pairs:
        if left in waves and right in waves:
            comparisons[name] = compare_wave(waves[left][li], waves[right][ri])
            comparisons[name]['all11512_parameters_exact'] = vectors[left][li] == vectors[right][ri]
    complete = all(r['status'] == 'passed' for r in records.values())
    if complete:
        checks = {name: comparison['decoded_bytes_exact'] and comparison['all11512_parameters_exact'] for name, comparison in comparisons.items()}
    result = {'status': 'passed strict transient controls' if complete and all(checks.values()) else 'failed or incomplete strict transient controls',
              'individual_controls': records, 'comparisons': comparisons, 'strict_checks': checks,
              'scope': 'New full joint586 mismatch population; all11512 parameters and18 saved vectors. Exact waveform/state equality failures are not replaced by numeric bounds or selected-decision agreement. No calibration accuracy, physical qualification, statistical yield or adoption inferred. Original nominal586 controls and all prior failures retained separately.'}
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'individual_controls'}, indent=2))


if __name__ == '__main__':
    main()
