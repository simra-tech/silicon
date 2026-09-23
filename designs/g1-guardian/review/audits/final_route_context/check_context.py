#!/usr/bin/env python3
"""Apply the existing 1% 24-to48um matrix-context criterion to final routes."""
import argparse
import json
import math
from pathlib import Path
from route_inventory import sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('width12', 'width24', 'width48', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    matrices, identities, input_hashes = {}, [], {}
    for width in (12, 24, 48):
        directory = getattr(args, 'width'+str(width))
        paths = {name: directory/name for name in ('manifest.json', 'clip/provenance.json', 'analysis/summary.json', 'analysis/ac_checks.json')}
        payload = {name: json.loads(path.read_text()) for name, path in paths.items()}
        run, clip, summary, ac = [payload[key] for key in paths]
        assert run['status'].startswith('passed') and len(run['steps']) == 4
        assert all(row['returncode'] == 0 for row in run['steps'])
        assert clip['status'].startswith('passed') and clip['context_um'] == width
        assert len(ac) == 8 and all(row['status'] == 'passed' and row['returncode'] == 0 and
                                   row['tolerance_F'] == 1e-25 and row['max_abs_error_F'] < 1e-25 for row in ac)
        assert {row['deck'] for row in ac} == {f'{v}_{m}_{d}.cir' for v in ('no_fill', 'actual_fill') for m in ('grounded', 'floating') for d in ('P', 'N')}
        identities.append({key: clip[key] for key in ('source_gds_sha256', 'inventory_sha256', 'geometry_audit_sha256', 'script_sha256', 'pair', 'length_um')})
        matrices[width] = {}
        for variant in ('no_fill', 'actual_fill'):
            for mode in ('grounded', 'floating'):
                matrix = summary['results'][variant]['modes'][mode]['matrix_fF']
                assert len(matrix) == 2 and all(len(row) == 2 for row in matrix)
                assert all(math.isfinite(v) for row in matrix for v in row)
                matrices[width][variant+'_'+mode] = matrix
        input_hashes[str(width)] = {name: sha(path) for name, path in paths.items()}
    assert identities[0] == identities[1] == identities[2]
    errors, rows = {}, []
    for key, wide in matrices[48].items():
        small = matrices[24][key]
        assert all(v != 0 for row in wide for v in row), 'Original relative criterion undefined for a zero denominator'
        values = [[abs(small[i][j]-wide[i][j])/abs(wide[i][j]) for j in range(2)] for i in range(2)]
        errors[key] = max(v for row in values for v in row)
        rows.append(dict(boundary=key, relative_errors=values, maximum_relative_error=errors[key],
                         status='passed' if errors[key] <= .01 else 'failed'))
    result = dict(status='passed' if all(row['status'] == 'passed' for row in rows) else 'failed',
        criterion='Existing interface contract: every 2x2 entry changes <=1% from24to48um relative to48um value',
        tolerance=.01, checks=rows, observed_matrices_fF=matrices, identity=identities[0],
        input_hashes=input_hashes, script_sha256=sha(Path(__file__)),
        numerical_graph_AC_checks='passed all24',
        not_run=['longitudinal convergence', 'whole-route extraction', 'actual-source electrical acceptance'],
        not_applicable=['random seed for deterministic capacitor-network checks'],
        scope='One fixed20um metal-only midpoint under explicit context-grounding assumptions, not fullchip parasitic acceptance')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('observed_matrices_fF', 'input_hashes')}, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
