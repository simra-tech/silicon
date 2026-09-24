#!/usr/bin/env python3
"""Independent post-execution audit; no simulation launch or acceptance substitution."""
import argparse
import json
from pathlib import Path

from prepare_dac586_static_controls import SIM, ROOT, CASES, REFERENCE, transform
from run_dac586_static_control import analyze, sha, read_op, compare_columns


def audit(prefix, implementation, implementation_hash):
    assert sha(implementation) == implementation_hash
    frozen = json.loads(implementation.read_text())
    assert all(sha(ROOT/name) == value for name, value in frozen['source_sha256'].items())
    results = []
    for label, soft, hard, temperatures in CASES:
        out = SIM/'qualification'/(prefix+'-'+label)
        prep = json.loads((out/'preparation.json').read_text())
        assert sha(out/'preparation.json') == frozen['preparations_sha256'][str((out/'preparation.json').relative_to(ROOT))]
        assert prep['codes'] == [soft, hard] and prep['temperatures_C'] == temperatures
        assert all(sha(ROOT/name) == value for name, value in prep['bindings_sha256'].items())
        assert all(sha(out/name) == value for name, value in prep['source_hashes'].items())
        assert sha(out/'population_inventory.json') == prep['inventory_sha256']
        original = (SIM/'qualification'/REFERENCE/'population_op.cir').read_text()
        assert (out/'dac_static.cir').read_text() == transform(original, REFERENCE, out.name, soft, hard, temperatures, prep['groups'])
        if not all((out/name).exists() for name in ['run.json', 'run.log', 'summary.json', 'provenance.json']):
            results.append({'run': out.name, 'status': 'not run', 'label': label})
            continue
        provenance = json.loads((out/'provenance.json').read_text())
        assert provenance['runtime_identity'] == prep['expected_runtime_identity']
        assert provenance['implementation_sha256'] == implementation_hash
        assert provenance['runner_sha256'] == frozen['source_sha256'][str((SIM/'run_dac586_static_control.py').relative_to(ROOT))]
        assert all(provenance['input_checks'].values())
        state = json.loads((out/'run.json').read_text())
        recomputed = analyze(out, prep, state)
        recorded = json.loads((out/'summary.json').read_text())
        assert recorded == recomputed, 'Recorded result does not match independent log/data reanalysis'
        results.append({'run': out.name, 'label': label, 'status': recomputed['status'],
            'solver_status': recomputed['solver_status'], 'wall_s': recomputed['wall_s'],
            'errors': recomputed['errors'], 'exact_comparisons': recomputed['exact_comparisons'],
            'receipts_sha256': {name: sha(out/name) for name in
                ['preparation.json', 'run.json', 'run.log', 'summary.json', 'provenance.json', 'dac_static.cir']}})
    repeat = {'status': 'not run'}
    if all(next(row for row in results if row['label'] == label)['status'] == 'passed' for label in ['output', 'repeat']):
        paths = [SIM/'qualification'/(prefix+'-'+label)/'op0.dat' for label in ['output', 'repeat']]
        header = paths[0].read_text().splitlines()[0].split()
        exact = compare_columns(read_op(paths[0], header), read_op(paths[1], header), 12)
        repeat = {'status': 'passed' if all(exact.values()) else 'failed', 'checks': exact}
    passed = all(row['status'] == 'passed' for row in results) and repeat['status'] == 'passed'
    return {'status': 'passed static anchor qualification' if passed else 'incomplete or failed static anchor qualification',
        'controls': results, 'repeat_full12': repeat, 'implementation_sha256': implementation_hash,
        'expected_controls': 11, 'completed_controls': sum(row['status'] in ['passed', 'failed'] for row in results),
        'scope': 'Static anchors only; all256, isolated leakage, dynamic settling and statistical acceptance NOT RUN.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix', required=True)
    p.add_argument('--implementation', required=True)
    p.add_argument('--implementation-sha256', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    result = audit(a.prefix, ROOT/a.implementation, a.implementation_sha256)
    destination = ROOT/a.output
    assert not destination.exists()
    destination.write_text(json.dumps(result, indent=2)+'\n')
    print(result['status'])
