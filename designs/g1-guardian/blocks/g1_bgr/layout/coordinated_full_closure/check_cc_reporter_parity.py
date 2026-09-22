#!/usr/bin/env python3
"""Require all 21 small-control native capacitance binary64 values unchanged."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--original', type=Path, required=True)
    ap.add_argument('--adapted', type=Path, required=True)
    ap.add_argument('--historical', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.exists()
    receipt = dict(status='failed exact binary64 reporter parity', checks={}, inputs={})
    try:
        records = []
        caps = []
        for folder in (args.original, args.adapted):
            launch = json.loads((folder / 'launch.json').read_text())
            assert launch['status'] == 'passed' and launch['inputs_unchanged']
            data = json.loads((folder / 'result/summary.json').read_text())
            assert data['status'] == 'passed raw CC generation; completeness not qualified'
            assert data['all_inputs_tools_unchanged'] and data['capacitor_count'] == 21
            assert data['binary64_roundtrip'] == 'passed' and data['blackbox'] is False
            records.append(data)
            cap_file = folder / 'result/exact_capacitances.json'
            assert sha(cap_file) == data['capacitance_sha256']
            caps.append(json.loads(cap_file.read_text()))
            for path in (folder / 'launch.json', folder / 'result/summary.json', cap_file):
                receipt['inputs'][str(path)] = sha(path)
        assert records[0]['reporter'] == 'original' and records[1]['reporter'] == 'count-only'
        assert records[1]['report_callback_counts']['overlap'] > 0
        assert records[1]['report_callback_counts']['sidewall'] > 0
        assert records[1]['report_callback_counts']['sideoverlap'] > 0
        for field in ('database_sha256', 'script_sha256', 'tool_files', 'technology_sha256',
                      'extracted_layers', 'unknown_layers', 'source_net_names', 'native_capacitors'):
            assert records[0][field] == records[1][field], field
        assert caps[0] == caps[1]
        assert all(float.fromhex(row['capacitance_fF_hex']) == row['capacitance_fF'] for row in caps[0])
        csv_files = list(args.historical.rglob('*_k25d_pex_netlist.csv'))
        assert len(csv_files) == 1
        with csv_files[0].open() as handle:
            old = {(r['Net1'], r['Net2']): float(r['Capacitance [fF]'])
                   for r in csv.DictReader(handle, delimiter=';') if r['Device'].startswith('C')}
        current = {(r['net1'], r['net2']): r['capacitance_fF'] for r in caps[0]}
        assert current.keys() == old.keys() and len(current) == 21
        assert all(round(value, 3) == old[key] for key, value in current.items())
        receipt['inputs'][str(csv_files[0])] = sha(csv_files[0])
        receipt.update(status='passed exact binary64 reporter parity', capacitor_count=21,
                       worker_sha256=records[0]['script_sha256'],
                       checks=dict(all_21_net_pairs='passed', all_21_binary64_values='passed',
                                   native_precision_roundtrip='passed', historical_rounded_CSV='passed',
                                   identical_geometry_options_tools='passed', reporter_callbacks_exercised='passed',
                                   full_BRG_extraction='not run', material_completeness='not qualified',
                                   electrical='not run', resistance='not applicable: CC only'))
    except Exception as error:
        receipt['error'] = repr(error)
        raise
    finally:
        args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
