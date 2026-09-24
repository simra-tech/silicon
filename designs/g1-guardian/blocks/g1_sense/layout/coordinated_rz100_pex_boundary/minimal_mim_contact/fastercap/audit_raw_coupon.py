#!/usr/bin/env python3
"""Audit saved native CMIM FasterCap geometry and unmodified Maxwell matrices."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def face_area(path):
    areas = []
    heights = set()
    for line in path.read_text().splitlines():
        if not line.startswith('T '):
            continue
        nums = list(map(float, line.split()[2:]))
        assert len(nums) == 12  # three vertices plus an orientation point
        x1, y1, z1, x2, y2, z2, x3, y3, z3 = nums[:9]
        assert z1 == z2 == z3
        heights.add(z1)
        areas.append(abs((x2-x1)*(y3-y1)-(x3-x1)*(y2-y1))/2)
    assert len(areas) == 2 and len(heights) == 1
    return sum(areas), next(iter(heights))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    prior = json.loads((a.run/'summary.json').read_text())
    assert prior['status'].startswith('completed raw FasterCap coupon')
    assert prior['inputs_unchanged'] and prior['iteration_count'] >= 2
    files = {r['name']: r for r in prior['geometry_files']}
    inputdir = a.run/'engine/sense_mim_method_control__sense_mim_method_control/FasterCap_Input_Files'
    bottom = next(inputdir.glob('*outside=ismim_net=bottom.geo'))
    top = next(inputdir.glob('*outside=ismim_net=top.geo'))
    assert sha(bottom) == files[bottom.name]['sha256']
    assert sha(top) == files[top.name]['sha256']
    bottom_area, bottom_z = face_area(bottom)
    top_area, top_z = face_area(top)
    assert abs(bottom_area-67.24) < 1e-9 and abs(top_area-49) < 1e-9
    assert abs(top_z-bottom_z-.04) < 1e-12
    log = a.run/'FasterCap_Output.txt'
    raw = log.read_text()
    assert sha(log) == prior['solver_log_sha256']
    version = re.search(r'^Running FasterCap version (\S+)', raw, re.M).group(1)
    norms = [float(x) for x in re.findall(r'Weighted Frobenius norm of the difference between capacitance \(auto option\):\s*(\S+)', raw)]
    panels = [int(x) for x in re.findall(r'Number of panels after refinement:\s*(\d+)', raw)]
    iterations = json.loads((a.run/'raw_matrices.json').read_text())
    assert sha(a.run/'raw_matrices.json') == prior['raw_matrices_sha256']
    assert len(iterations) == prior['iteration_count'] and len(norms) == len(iterations)-1
    names = iterations[-1]['names']
    assert names == ['g1_VSUBS','g2_bottom','g3_top']
    first, last = (q['matrix_F'] for q in iterations[-2:])
    assert last == prior['raw_matrix_F']
    pairs = [(0,1),(0,2),(1,2)]
    changes = {}
    asymmetry = {}
    for i,j in pairs:
        label = names[i]+'__'+names[j]
        previous = (first[i][j]+first[j][i])/2
        current = (last[i][j]+last[j][i])/2
        changes[label] = abs(current-previous)/abs(current)
        asymmetry[label] = abs(last[i][j]-last[j][i])/abs(current)
    symmetric = [[(last[i][j]+last[j][i])/2 for j in range(3)] for i in range(3)]
    leading_minor_2 = symmetric[0][0]*symmetric[1][1]-symmetric[0][1]**2
    leading_minor_3 = (symmetric[0][0]*(symmetric[1][1]*symmetric[2][2]-symmetric[1][2]**2)
                       -symmetric[0][1]*(symmetric[0][1]*symmetric[2][2]-symmetric[0][2]*symmetric[1][2])
                       +symmetric[0][2]*(symmetric[0][1]*symmetric[1][2]-symmetric[0][2]*symmetric[1][1]))
    positive_definite = symmetric[0][0] > 0 and leading_minor_2 > 0 and leading_minor_3 > 0
    quantitative_1pct = (norms[-1] <= .01 and all(v <= .01 for v in changes.values())
                          and all(v <= .01 for v in asymmetry.values()) and positive_definite)
    result = dict(status='passed saved raw geometry/matrix audit; quantitative convergence not qualified',
                  source_summary_sha256=sha(a.run/'summary.json'),
                  solver_version=version, solver_binary_sha256=prior['FasterCap_binary_sha256'],
                  generated_bottom_face_um2=bottom_area, generated_top_face_um2=top_area,
                  bottom_top_separation_um=top_z-bottom_z,
                  iteration_count=len(iterations), weighted_norms=norms,
                  refined_panel_counts=panels, configured_auto_tolerance=prior['args']['tolerance'],
                  final_auto_norm_below_configured_tolerance=norms[-1] < prior['args']['tolerance'],
                  final_relative_change_from_previous=changes,
                  final_reciprocity_relative_difference=asymmetry,
                  symmetrized_matrix_positive_definite=positive_definite,
                  quantitative_1pct_matrix_qualified=quantitative_1pct,
                  raw_matrix_F=last, substrate_reference='VSUBS virtual; not bound to VSS',
                  intrinsic_extrinsic_ownership='not qualified',
                  full_macro_PEX='not qualified', electrical_adoption='not run')
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k:result[k] for k in ['status','solver_version','iteration_count',
        'generated_bottom_face_um2','generated_top_face_um2','bottom_top_separation_um',
        'final_auto_norm_below_configured_tolerance']}))


if __name__ == '__main__':
    main()
