#!/usr/bin/env python3
"""Read-only six-control qualification; retain exact failures without a waiver."""
import argparse
import json
from pathlib import Path
from prepare_586_population import HERE, sha
from run_586_population_control import exact_wave


def changed_primitives(inventory, first, second):
    first = {group: dict(rows) for group, rows in first.items()}
    second = {group: dict(rows) for group, rows in second.items()}
    rows = []
    for primitive in inventory['primitives']:
        group = primitive['group']
        changed = [key for key in primitive['queries'] if float(first[group][key]) != float(second[group][key])]
        rows.append(dict(instance=primitive['instance'], group=group, kind=primitive['kind'],
                         changed_parameters=changed, status='passed' if changed else 'failed'))
    return rows


def analyze(packet_path):
    packet = json.loads(packet_path.read_text())
    cases = {row['label']: row for row in packet['cases']}
    assert set(cases) == {'enabled', 'repeat', 'changed', 'disabled', 'disabledchanged', 'return'}
    results, runs, receipts = {}, {}, {}
    for label, case in cases.items():
        run = HERE/'runs'/case['run_id']
        assert sha(run/'preparation.json') == case['preparation_sha256']
        assert sha(run/'probe.cir') == case['deck_sha256']
        result, = json.loads((run/'summary.json').read_text())
        provenance = json.loads((run/'provenance.json').read_text())
        assert provenance['packet_sha256'] == sha(packet_path) and all(provenance['input_checks'].values())
        assert all(sha(run/name) == value for name, value in case['source_hashes'].items())
        results[label], runs[label] = result, run
        receipts[case['run_id']] = {n: sha(run/n) for n in ['summary.json', 'provenance.json', 'preparation.json', 'run.log']}
    controls = {label: result['control_status'] for label, result in results.items()}
    report = dict(status='failed', control_statuses=controls, receipts_sha256=receipts,
                  packet_sha256=sha(packet_path), comparisons={}, variation='not run',
                  scope='Six NEW T2F586 mismatch controls; no ensemble/adoption release by this report. Exact repeat/disabled/return failures stay failures, separate from numerical completion. Original linear±2C criterion unchanged.')
    if not all(result['control_status'] == result['full3180_status'] == 'passed' for result in results.values()):
        report['reason'] = 'At least one declared control failed; no cross-run qualification waiver'
        return report
    def vector(label, phase=0):
        return results[label]['phases'][phase]['parameters_before']
    vector_checks = dict(enabled_repeat=vector('enabled') == vector('repeat'),
        enabled_return_initial=vector('enabled') == vector('return'),
        enabled_return_final=vector('enabled') == vector('return', 3),
        disabled_changed=vector('disabled') == vector('disabledchanged'))
    wave_checks = {}
    for label, first, pi, second, pj in [('enabled_repeat', 'enabled', 0, 'repeat', 0),
        ('enabled_return_initial', 'enabled', 0, 'return', 0),
        ('enabled_return_final', 'enabled', 0, 'return', 3),
        ('disabled_changed', 'disabled', 0, 'disabledchanged', 0)]:
        wave_checks[label] = exact_wave(runs[first]/('phase%d.dat' % pi), runs[second]/('phase%d.dat' % pj))
    inventory_path = runs['enabled']/'population_inventory.json'
    assert sha(inventory_path) == packet['inventory_sha256']
    inventory = json.loads(inventory_path.read_text())
    variation = changed_primitives(inventory, vector('enabled'), vector('changed'))
    assert len(variation) == 1129
    report.update(comparisons=dict(full3180_vectors=vector_checks, waveforms=wave_checks),
                  variation=dict(status='passed' if all(r['status'] == 'passed' for r in variation) else 'failed',
                                 changed_primitives=sum(r['status'] == 'passed' for r in variation),
                                 primitive_count=1129, groups={g: dict(total=sum(r['group'] == g for r in variation),
                                     changed=sum(r['group'] == g and r['status'] == 'passed' for r in variation)) for g in ['BGR', 'T2F']},
                                 primitives=variation))
    if all(vector_checks.values()) and all(all(v.values()) for v in wave_checks.values()) and report['variation']['status'] == 'passed':
        report['status'] = 'passed six-control qualification'
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = analyze(args.packet)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['variation', 'receipts_sha256']}, indent=2))
