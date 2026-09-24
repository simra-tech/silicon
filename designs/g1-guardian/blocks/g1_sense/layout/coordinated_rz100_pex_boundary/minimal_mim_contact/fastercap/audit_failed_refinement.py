#!/usr/bin/env python3
"""Audit retained raw matrices from a failed FasterCap coupon refinement."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def matrices(raw):
    lines = raw.splitlines()
    out = []
    for i, line in enumerate(lines):
        if line.strip() != 'Capacitance matrix is:':
            continue
        assert lines[i + 1].strip() == 'Dimension 3 x 3'
        rows = [line.split() for line in lines[i + 2:i + 5]]
        names = [row[0] for row in rows]
        assert names == ['g1_VSUBS', 'g2_bottom', 'g3_top']
        value = [[float(x) / 1e6 for x in row[1:]] for row in rows]
        assert all(len(row) == 3 and all(math.isfinite(x) for x in row) for row in value)
        out.append(value)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    failed = json.loads((a.run / 'summary.json').read_text())
    ref = json.loads((a.reference / 'summary.json').read_text())
    assert failed['status'] == 'failed raw FasterCap coupon'
    assert failed['inputs_unchanged'] and ref['inputs_unchanged']
    assert failed['args']['tolerance'] == 0.01 and ref['args']['tolerance'] == 0.05
    assert failed['geometry_files'] == ref['geometry_files']
    assert failed['input_list_sha256'] == ref['input_list_sha256']
    raw = (a.run / 'FasterCap_Output.txt').read_text()
    assert 'Error: Out of memory, program execution stopped!' in raw
    series = matrices(raw)
    assert len(series) >= 2
    norms = [float(x) for x in re.findall(
        r'Weighted Frobenius norm of the difference between capacitance \(auto option\):\s*(\S+)', raw)]
    assert len(norms) == len(series) - 1
    last, prev = series[-1], series[-2]
    names = ['VSUBS', 'bottom', 'top']
    mutual = {}
    reciprocal = {}
    default_delta = {}
    for i, j in [(0, 1), (0, 2), (1, 2)]:
        label = names[i] + '__' + names[j]
        now = -(last[i][j] + last[j][i]) / 2
        prior = -(prev[i][j] + prev[j][i]) / 2
        baseline = -(ref['raw_matrix_F'][i][j] + ref['raw_matrix_F'][j][i]) / 2
        assert now > 0 and prior > 0 and baseline > 0
        mutual[label] = now
        reciprocal[label] = abs(last[i][j] - last[j][i]) / now
        default_delta[label] = abs(now - baseline) / now
    change = {names[i] + '__' + names[j]:
              abs(mutual[names[i] + '__' + names[j]] -
                  (-(prev[i][j] + prev[j][i]) / 2)) /
              mutual[names[i] + '__' + names[j]]
              for i, j in [(0, 1), (0, 2), (1, 2)]}
    s = [[(last[i][j] + last[j][i]) / 2 for j in range(3)] for i in range(3)]
    det2 = s[0][0] * s[1][1] - s[0][1] ** 2
    det3 = (s[0][0] * (s[1][1] * s[2][2] - s[1][2] ** 2)
            - s[0][1] * (s[0][1] * s[2][2] - s[0][2] * s[1][2])
            + s[0][2] * (s[0][1] * s[1][2] - s[0][2] * s[1][1]))
    result = dict(status='failed 1% refinement; retained partial matrices only',
                  solver_log_sha256=sha(a.run / 'FasterCap_Output.txt'),
                  summary_sha256=sha(a.run / 'summary.json'),
                  reference_summary_sha256=sha(a.reference / 'summary.json'),
                  exact_geometry_parity=True, matrix_count=len(series),
                  final_reported_auto_norm=norms[-1],
                  auto_norm_meets_1pct=norms[-1] <= 0.01,
                  last_two_mutual_relative_change=change,
                  last_matrix_reciprocity_relative_difference=reciprocal,
                  default_5pct_vs_last_mutual_relative_difference=default_delta,
                  last_mutual_F=mutual,
                  last_symmetrized_matrix_positive_definite=(s[0][0] > 0 and det2 > 0 and det3 > 0),
                  raw_last_matrix_F=last, raw_matrices_F=series,
                  raw_solver_failure='address-space cap / FasterCap out of memory',
                  qualified_capacitance='not run', electrical_adoption='not run')
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'matrix_count',
         'final_reported_auto_norm', 'last_two_mutual_relative_change',
         'last_matrix_reciprocity_relative_difference')}))


if __name__ == '__main__':
    main()
