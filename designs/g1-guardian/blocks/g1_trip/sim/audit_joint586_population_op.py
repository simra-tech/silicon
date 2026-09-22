#!/usr/bin/env python3
"""Cross-run full-population OP qualification; no transient permission implied."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

SIM = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def variation(first, second):
    assert [key for key, value in first] == [key for key, value in second]
    devices = {}
    counts = collections.Counter()
    for (key, a), (_, b) in zip(first, second):
        primitive = key.split('[', 1)[0].rsplit('.', 1)[0][3:]
        domain = 'BGR' if primitive.startswith('xbgr.') else 'nonBGR'
        kind = 'HBT' if key.startswith('@q.') else ('CMIM' if key.startswith('@c.') else ('R' if '.nr1[' in key else 'MOS'))
        entry = devices.setdefault(primitive, {'domain': domain, 'kind': kind, 'changed': False})
        entry['changed'] |= a != b
        if a != b:
            counts[domain+'.'+kind] += 1
    result = {}
    for key in sorted({r['domain']+'.'+r['kind'] for r in devices.values()}):
        rows = [r for r in devices.values() if r['domain']+'.'+r['kind'] == key]
        result[key] = {'primitive_count': len(rows), 'primitives_with_changed_values': sum(r['changed'] for r in rows),
                       'changed_parameter_count': counts[key]}
    assert len(devices) == 3500
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--recovery-map', type=Path)
    a = p.parse_args()
    runs, rows, receipts, original_failures = {}, {}, {}, {}
    recoveries = json.loads(a.recovery_map.read_text()) if a.recovery_map else {}
    assert set(recoveries).issubset({'disabled', 'disabledchanged'})
    labels = ['enabled', 'repeat', 'changed', 'return', 'disabled', 'disabledchanged']
    for label in labels:
        run = SIM/'qualification'/(a.prefix+'-'+label)
        if label in recoveries:
            original = run
            failed, = json.loads((original/'summary.json').read_text())
            assert failed['op_qualification_status'] == 'failed' and failed['watchdog_status'] == 'timeout'
            run = SIM/'qualification'/recoveries[label]
            contract = json.loads((run/'recovery_contract.json').read_text())
            validation = json.loads((run/'recovery_validation.json').read_text())
            assert contract['reference_run'] == original.name and contract['new_run'] == run.name
            assert validation['recovery_status'] == 'passed' and validation['original11512_before_recovery_before_after_exact']
            assert (run/'population_op.cir').read_text().replace(run.name, original.name) == (original/'population_op.cir').read_text()
            original_failures[label] = {'run': original.name, 'status': 'failed original120s watchdog, preserved',
                                        'summary_sha256': sha(original/'summary.json'), 'recovery_validation_sha256': sha(run/'recovery_validation.json')}
        runs[label] = run
        row, = json.loads((run/'summary.json').read_text())
        rows[label] = row
        receipts[label] = {name: sha(run/name) for name in ['summary.json', 'provenance.json', 'preparation.json', 'population_inventory.json', 'population_op.cir', 'run.log']}
    individual = {label: row['op_qualification_status'] == 'passed' for label, row in rows.items()}
    result = {'individual_controls': individual, 'receipts_sha256': receipts,
              'actual_control_runs': {label: run.name for label, run in runs.items()},
              'original_failed_attempts': original_failures,
              'status': 'failed or incomplete OP control',
              'transient_qualification': 'not run: repeat, full11512 freeze and temperature checks still required before broad joint transient calibration',
              'scope': 'New BGR586+gm4 joint mismatch population; old71002 nominalBGR control and all original failures remain separate. Stale inherited10MHz/code153 comments retained; executable5MHz/code135151 authoritative.'}
    if all(individual.values()):
        values = {label: row['phases'][0]['parameters_before'] for label, row in rows.items()}
        bytype = variation(values['enabled'], values['changed'])
        checks = {'enabled_repeat_all11512_exact': values['enabled'] == values['repeat'],
                  'enabled_repeat_opdata_exact': (runs['enabled']/'op0.dat').read_bytes() == (runs['repeat']/'op0.dat').read_bytes(),
                  'enabled_changed_seed_all3500_primitives_vary': all(row['primitive_count'] == row['primitives_with_changed_values'] for row in bytype.values()),
                  'disabled_changed_seed_all11512_exact': values['disabled'] == values['disabledchanged'],
                  'disabled_changed_seed_opdata_exact': (runs['disabled']/'op0.dat').read_bytes() == (runs['disabledchanged']/'op0.dat').read_bytes(),
                  'return_all11512_exact_vs_enabled': all(phase['parameters_before'] == phase['parameters_after'] == values['enabled'] for phase in rows['return']['phases']),
                  'return_initial_opdata_exact_vs_enabled': (runs['return']/'op0.dat').read_bytes() == (runs['enabled']/'op0.dat').read_bytes()}
        result.update(checks=checks, enabled_changed_seed_variation_by_primitive=bytype,
                      return_exact_opdata_bytes=rows['return']['return_exact_opdata_bytes'],
                      return_max_abs_node_change_V=rows['return']['return_max_abs_node_change_V'],
                      return_separate_1uV_bound=rows['return']['return_separate_1uV_bound'])
        result['status'] = 'passed full OP parameter/control contract; inspect distinct return equality' if all(checks.values()) else 'failed OP cross-run contract'
        result['strict_return_status'] = 'passed' if result['return_exact_opdata_bytes'] else 'failed exact OPdata equality; not silently replaced by1uV bound'
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'receipts_sha256'}, indent=2))


if __name__ == '__main__':
    main()
