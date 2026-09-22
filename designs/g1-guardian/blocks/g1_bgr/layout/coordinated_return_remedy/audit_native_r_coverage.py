#!/usr/bin/env python3
"""Distinguish successful native request serialization from failed R coverage."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--request', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    request = json.loads(args.request.read_text())
    conductors = {int(r['layer']['id']): r['layer'] for r in request['tech']['conductors']}
    missing, unsupported, supported = [], [], []
    classes = collections.Counter()
    for device in request['devices']:
        classes[device['device_class_name']] += 1
        for terminal in device['terminals']:
            row = dict(device_id=device['id'], device_name=device['device_name'],
                       model=device['device_class_name'], terminal=terminal['name'], net=terminal['net_name'])
            regions = terminal.get('region_by_layer', [])
            row['layers'] = [r['layer'] for r in regions]
            if not regions:
                missing.append(row)
            elif any(int(r['layer'].get('id', 0)) not in conductors for r in regions):
                unsupported.append(row)
            else:
                supported.append(row)
    assert sum(classes.values()) == 1027
    assert classes['npn13G2'] == 292 and classes['rppd'] + classes['rhigh'] == 399
    assert len(missing) == 2365 and len(unsupported) == 336 and len(supported) == 1008
    assert all(r['terminal'] == 'B' and r['model'].startswith('sg13_hv_') for r in unsupported)
    assert len(request['net_extraction_requests']) == 55 and len(request['pins']) == 9
    count = lambda rows: dict(collections.Counter(r['model'] + ':' + r['terminal'] for r in rows))
    report = dict(status='failed full current-path R coverage', audit_execution='passed exact request inventory',
        input_sha256=sha(args.request), script_sha256=sha(Path(__file__)), device_classes=dict(classes),
        terminals_total=3709, supported_terminals=1008, unsupported_conductor_terminals=336,
        missing_geometry_terminals=2365, missing_by_model_terminal=count(missing),
        unsupported_by_model_terminal=count(unsupported), supported_by_model_terminal=count(supported),
        missing=missing, unsupported=unsupported, numerical_R='not run',
        nine_ground_dummies='Geometric proof separate; all nine remain in canonical electrical source.',
        conclusion='Native request is not a complete resistance model: HBT/R injection points and all MOS bodies are unrepresented.',
        remedy_scope='Requires independently source-mapped physical electrode/access boundaries and well/substrate ownership; no fabricated zero resistance or automatic native API adoption.',
        cards_decks_geometry='unchanged', adoption='not run', seed='not applicable')
    assert not args.output.exists()
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('missing', 'unsupported')}, indent=2))


if __name__ == '__main__':
    main()
