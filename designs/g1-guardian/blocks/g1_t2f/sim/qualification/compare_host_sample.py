#!/usr/bin/env python3
"""Strict same-input legacy T2F host replay check, preserving both runs."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', required=True)
    parser.add_argument('--candidate', required=True)
    args = parser.parse_args()
    assert all(Path(name).name == name for name in [args.reference, args.candidate])
    directories = [HERE/'runs'/name for name in [args.reference, args.candidate]]
    manifests = [json.loads((path/'manifest.json').read_text()) for path in directories]
    old, new = manifests
    checks = {key: old[key] == new[key] for key in
              ['image_id', 'pdk_commit', 'ngspice', 'input_sha256',
               'realized_netlist_sha256', 'models_sha256', 'seed', 'mismatch', 'op_only']}
    cases = []
    checks['four_temperature_sets'] = (
        len(old['cases']) == len(new['cases']) == 4 and
        {c['temperature_C'] for c in old['cases']} ==
        {c['temperature_C'] for c in new['cases']} == {-40, 25, 100, 125})
    for before in old['cases']:
        after = next((c for c in new['cases'] if c['name'] == before['name']), None)
        item = {'name': before['name'], 'checks': {'candidate_present': after is not None}}
        if after is not None:
            item['checks'].update({key: before.get(key) == after.get(key) for key in
                                  ['temperature_C', 'seed', 'hbt', 'mos', 'res', 'cap',
                                   'vdd', 'vdd12', 'deck_sha256', 'measurements', 'fingerprints',
                                   'completed_tstop_s', 't2f_hbt_vce_max_V', 'hbt_vce_status']})
            item['checks']['both_complete'] = all(c['status'] == 'passed' and c['solver_exit'] == 0
                                                  and not c['timed_out'] for c in [before, after])
            for suffix in ['cir', 'dat']:
                values = [sha(d/(before['name']+'.'+suffix)) for d in directories]
                item[suffix+'_sha256'] = values
                item['checks'][suffix+'_byte_identical'] = values[0] == values[1]
            item['checks']['deck_hashes_authentic'] = item['cir_sha256'] == [before['deck_sha256'], after['deck_sha256']]
        item['status'] = 'passed' if all(item['checks'].values()) else 'failed'
        cases.append(item)
    result = {'reference': args.reference, 'candidate': args.candidate,
              'manifest_sha256': [sha(d/'manifest.json') for d in directories],
              'checks': checks, 'cases': cases,
              'status': 'passed' if all(checks.values()) and all(c['status'] == 'passed' for c in cases) else 'failed',
              'scope': 'Exact source/model/runtime, seed/fingerprint, full output-vector and numerical measurement replay for one physical T2F sample only.'}
    with (directories[1]/'host_parity.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
