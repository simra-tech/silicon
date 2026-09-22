#!/usr/bin/env python3
"""Ledger/LEF analytical wire sensitivities; NOT extracted or full-path RC."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ledger', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.exists()
    tech = Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef')
    assert sha(tech) == '054f5b7b24d72365b4b1088be1331e04c1c2e3805de9f99c37e71938ed231efc'
    sheet = {}
    for name, body in re.findall(r'^LAYER (\S+)\s*\n(.*?)^END \1\s*$', tech.read_text(), re.M | re.S):
        match = re.search(r'RESISTANCE RPERSQ (\S+)', body)
        if match and name.startswith('Metal'):
            sheet['M' + name[5:]] = float(match[1])
    ledger = json.loads(args.ledger.read_text())
    groups = collections.defaultdict(list)
    for route in ledger['routes']:
        if not route['role'].startswith('return_') or route['purpose'] not in ('return_trunk', 'functional_return_row', 'star_branch'):
            continue
        x0, y0, x1, y1 = route['bbox_dbu']
        width = min(x1 - x0, y1 - y0) / 1000
        length = (max(x1 - x0, y1 - y0) - min(x1 - x0, y1 - y0)) / 1000
        assert abs(width - .8) < 1e-9 and length >= 0
        resistance = sheet[route['layer']] * length / width
        groups[route['role']].append(dict(route, centerline_length_um=length, width_um=width,
                                        sheet_ohm_per_square=sheet[route['layer']], wire_ohm_estimate=resistance,
                                        voltage_uV_per_uA_through_segment=resistance))
    assert set(groups) == {'return_XQ56', 'return_XQ60', 'return_XQ62', 'return_XQ67'}
    rows = []
    for role, routes in sorted(groups.items()):
        trunk = [route for route in routes if route['purpose'] == 'return_trunk']
        branch = [route for route in routes if route['purpose'] == 'functional_return_row']
        star = [route for route in routes if route['purpose'] == 'star_branch']
        assert len(trunk) == 1 and branch and star
        rows.append({'role': role, 'trunk_wire_ohm_estimate': trunk[0]['wire_ohm_estimate'],
                     'longest_row_wire_ohm_estimate': max(route['wire_ohm_estimate'] for route in branch),
                     'star_branch_wire_ohm_estimate': sum(route['wire_ohm_estimate'] for route in star),
                     'row_count': len(branch), 'segments': routes})
    result = {'status': 'passed arithmetic only', 'scope': 'Analytical ledger centerline/technologyLEF wire sensitivity, NOT extractedRC or completepath bound',
              'inputs': {str(path): sha(path) for path in (args.ledger, tech, Path(__file__))}, 'rows': rows,
              'omitted': ['native contact and emitter stubs', 'all via/contact resistance', 'spreading and bends',
                          'generalVSS/starhub distributed resistance', 'temperature/process variation', 'current distribution'],
              'formula': 'R=sheet_ohm_per_square*centerline_length_um/width_um; uV per uA through that segment numerically equals ohms.',
              'currents_voltage_error_electrical': 'not run; actual multi-injection tree currents required',
              'precision_star_zero_ohm_claim': 'failed/not justified; geometrical singlejoin is not an ideal equipotential',
              'seed': 'not applicable'}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({**result, 'rows': [{key: value for key, value in row.items() if key != 'segments'} for row in rows]}, indent=2))


if __name__ == '__main__':
    main()
