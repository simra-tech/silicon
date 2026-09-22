#!/usr/bin/env python3
"""Rank saved external terminal extrema without asserting foundry reliability."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = ['bgr_terminal_corners81_20260922_01',
        'bgr_terminal_startup6_20260922_01']


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    inventory = json.loads((HERE/'voltage_scope_audit_20260922.json').read_text())
    devices = inventory['netlist_inventory']['g1_bgr']
    geometry = {d['instance']: d for d in devices['MOS_instances']}
    short = devices['instances_shorter_than_documented_3p3V_gate_condition']
    result = {
        'source_hashes': {'voltage_scope_audit_20260922.json':
                          sha(HERE/'voltage_scope_audit_20260922.json')},
        'scope': 'Analysis of retained simulated external terminal extrema; no new simulation.',
        'documentary_interpretation': (
            'The documented 3.3 V VGS condition at 27 C requires HV NMOS '
            'L>=0.6um or HV PMOS L>=0.5um. A smaller simulated voltage does '
            'not establish an operating rating for excluded geometry or '
            'temperature. Literal PSP MAX fields remain separate diagnostics.'),
        'reliability_qualification': 'not run', 'groups': {}}
    for run in RUNS:
        directory = HERE/'runs'/run
        manifest = json.loads((directory/'manifest.json').read_text())
        result['source_hashes'][str((directory/'manifest.json').relative_to(HERE))] = sha(directory/'manifest.json')
        assert not manifest['not_run_cases']
        assert len(manifest['cases']) == (81 if 'corners81' in run else 6)
        maxima = {}
        records = []
        for case in manifest['cases']:
            assert case['status'] == 'passed' and case['solver_exit'] == 0
            assert not case['timed_out'] and case['original_vectors_byte_identical']
            name = case['name']
            assert sha(directory/(name+'.cir')) == case['deck_sha256']
            assert sha(directory/(name+'.dat')) == sha(HERE/'runs'/manifest['source_run']/(name+'.dat'))
            records.append({'case': name,
                            'terminals_sha256': sha(directory/(name+'_terminals.dat')),
                            'original_vectors_byte_identical': True})
            for value in case['external_terminal_extrema']:
                key = (value['instance'], value['pair'])
                if key not in maxima or value['maximum_absolute_V'] > maxima[key]['maximum_absolute_V']:
                    maxima[key] = dict(value, case=name)
                    if key[0] in geometry:
                        maxima[key]['length'] = geometry[key[0]]['length']
        result['groups'][run] = {
            'completed_cases': len(records), 'verified_artifacts': records,
            'axis': 'temperature_C' if 'corners81' in run else 'time_s',
            'external_terminal_ranking': sorted(maxima.values(), key=lambda x: -x['maximum_absolute_V']),
            'short_HV_NMOS_VGS': [maxima[(instance, 'gs')] for instance in short],
            'HBT_VCE_maximum_V': max(v['maximum_absolute_V'] for v in maxima.values()
                                      if v['instance'].startswith('XQ') and v['pair'] == 'ce'),
            'literal_PSP_MAX_exceedance_cases': sum(bool(c['literal_model_parameter_exceedances'])
                                                   for c in manifest['cases'])}
    output = HERE/'terminal_ranking_20260922.json'
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({name: {k: v for k, v in group.items()
                           if k not in ['external_terminal_ranking', 'verified_artifacts']}
                      for name, group in result['groups'].items()}, indent=2))


if __name__ == '__main__':
    main()
