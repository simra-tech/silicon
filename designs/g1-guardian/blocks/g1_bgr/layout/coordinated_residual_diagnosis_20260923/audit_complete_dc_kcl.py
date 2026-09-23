#!/usr/bin/env python3
"""Complete stationary compact-model KCL; physical BN transfer remains unresolved."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ('run', 'prepared', 'BN-proof', 'output'):
        ap.add_argument('--'+key, type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists()
    proof = json.loads(a.BN_proof.read_text())
    assert proof['status'] == 'passed restricted exact-model DC branch proof'
    assert proof['source_resistors'] == 399 and len(proof['negative_controls']) == 4
    assert all(sha(Path(p)) == h for p, h in proof['inputs'].items())
    summary_path = a.run/'summary.json'
    old_analysis_path = a.run/'conditional_analysis.json'
    summary = json.loads(summary_path.read_text())
    old = json.loads(old_analysis_path.read_text())
    assert summary['status'] == 'passed conditional nonlinear OP completion and source controls'
    assert summary['all2842_parameters_exact'] and old['observed_TEMP_C'] == 27
    assert len(summary['raw_fields']) == 3885 and len(old['devices']) == 1036
    folder = a.prepared/summary['case']
    paths = [summary_path, old_analysis_path, a.BN_proof, a.run/'metal_node_voltages.json',
             folder/'positive_edges.json', folder/'terminal_map.json', folder/'point_nodes.json',
             folder/'anchors.json', Path(__file__).resolve()]
    inputs = {str(p): sha(p) for p in paths}
    voltage = json.loads(paths[3].read_text())
    edges = json.loads(paths[4].read_text())
    terms = json.loads(paths[5].read_text())
    points = json.loads(paths[6].read_text())
    anchors = json.loads(paths[7].read_text())
    assert len(terms) == 3346 and len(points) == 3355
    mapped = {(r['source_id'], r['terminal']): r['new'] for r in terms}
    outgoing = collections.defaultdict(list)
    for e in edges:
        assert e['R_ohm'] > 0
        current = (voltage[e['a']]-voltage[e['b']])/e['R_ohm']
        outgoing[e['a']].append(current)
        outgoing[e['b']].append(-current)
    device = collections.defaultdict(list)
    records = []
    for row in old['devices']:
        name = row['source_id']
        if name.startswith('XR'):
            ibody = row['raw_resistor_ibody_A']
            assert math.isfinite(ibody)
            currents = {'1': -ibody, '2': ibody, 'BN': 0.0}
            attribution = 'Exact stationary unchanged-model branch proof; not measured per-device substrate current'
        else:
            currents = row['current_entering_device_A']
            assert currents is not None
            attribution = row['attribution']
        assert all(math.isfinite(v) for v in currents.values())
        for term, value in currents.items():
            if name.startswith('XR') and term == 'BN':
                assert value == 0
                continue
            device[mapped[(name, term)]].append(value)
        records.append(dict(source_id=name, current_entering_device_A=currents,
                            model_terminal_sum_A=math.fsum(currents.values()), attribution=attribution))
    assert sum(r['source_id'].startswith('XR') for r in records) == 399
    assert sum(len(r['current_entering_device_A']) for r in records) == 3745
    reference_nodes = {r['source_net'] for r in anchors if r['kind'] == 'actual macro port'}
    assert len(reference_nodes) == 9
    residual = {node: math.fsum(outgoing[node]+device[node]) for node in voltage if node not in reference_nodes}
    assert all(math.isfinite(v) for v in residual.values())
    result = dict(status='completed full stationary compact-model KCL accounting; physical model planes not qualified',
        inputs=inputs, model_devices=1036, model_terminal_incidences=3745,
        mapped_metal_terminal_incidences=3346, ideal_resistor_BN_terms=399,
        finite_metal_nodes=len(voltage), nonreference_nodes=len(residual),
        max_absolute_nonreference_KCL_A=max(abs(v) for v in residual.values()),
        max_absolute_device_terminal_sum_A=max(abs(r['model_terminal_sum_A']) for r in records),
        worst_nodes=sorted((dict(node=n, residual_A=v) for n, v in residual.items()),
                           key=lambda r: abs(r['residual_A']), reverse=True)[:30],
        external_reference_nodes=sorted(reference_nodes), devices=records,
        numeric_acceptance='not assigned a new tolerance; residuals reported exactly',
        physical_substrate_potential='not run/unresolved;399 ideal global VSS assignments remain conditional',
        transient_BN_currents='not applicable to this DC-only branch proof',
        intrinsic_contact_deembedding='unresolved', adoption='not run')
    assert all(sha(Path(p)) == h for p, h in inputs.items())
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
