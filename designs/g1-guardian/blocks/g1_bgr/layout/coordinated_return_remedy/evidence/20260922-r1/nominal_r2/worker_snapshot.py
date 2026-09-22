#!/usr/bin/env python3
"""Qualified-current partial tree sensitivity; explicitly not self-consistent IR."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    for name in ('wire', 'via', 'currents', 'candidate', 'output'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1
    wire, via, currents, candidate = [json.loads(p.read_text()) for p in
                                    (args.wire, args.via, args.currents, args.candidate / 'preparation.json')]
    assert wire['source_count'] == via['source_count'] == 76
    assert currents['source_sha256'] == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    assert currents['source_devices'] == 1036 and currents['nominal_temperature_C'] == 27
    assert candidate['status'] == 'passed preparation'
    assert sha(args.candidate / 'bank.gds') == candidate['gds_sha256']
    changes = json.loads((args.candidate / 'changed_shapes.json').read_text())
    changed = {c['array_id'] for c in changes['changes']}
    assert len(changed) == 36 and changes['removed_cuts'] == 72 and changes['added_cuts'] == 144
    lef = Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef')
    tech = Path('/usr/local/lib/python3.12/dist-packages/klayout_pex_protobuf/ihp-sg13g2_tech.pb.json')
    rex = Path('/usr/local/lib/python3.12/dist-packages/klayout_pex/rcx25/r/r_extractor.py')
    assert sha(lef) == '054f5b7b24d72365b4b1088be1331e04c1c2e3805de9f99c37e71938ed231efc'
    assert sha(tech) == '6ece2ac73930696f77b257d14fcf9d29d9e02451e7df99c72239746c18369a92'
    lef_values = {}
    for name, body in re.findall(r'^LAYER (\S+)\s*\n(.*?)^END \1\s*$', lef.read_text(), re.M | re.S):
        if name in ('Metal2', 'Metal4', 'Via2', 'Via3'):
            values = re.findall(r'^\s*RESISTANCE\s+(?:RPERSQ\s+)?([0-9.]+)\s*;', body, re.M)
            assert len(values) == 1
            lef_values[name] = float(values[0])
    assert lef_values == dict(Metal2=.103, Metal4=.103, Via2=20., Via3=20.)
    resistance = json.loads(tech.read_text())['process_parasitics']['resistance']
    kpex_sheets = {x['layer_name']: x['resistance'] / 1000 for x in resistance['layers']}
    kpex_vias = {x['via_name']: x['resistance'] / 1000 for x in resistance['vias']}
    assert kpex_sheets['Metal2'] == kpex_sheets['Metal4'] == .088
    assert kpex_vias['Via2'] == kpex_vias['Via3'] == 9.
    conversion_lines = [x.strip() for x in rex.read_text().splitlines() if 'milliohm' in x]
    assert any('milliohm_to_ohm' in x for x in conversion_lines)
    assert any('milliohm_by_cnt_to_ohm_by_square' in x for x in conversion_lines)
    injection = {r['source_id']: r['injection_into_return_wire_A'] for r in currents['selected_hbt_return_emitters']}
    assert len(injection) == 76
    assert set(injection) == {s for r in wire['roles'] for s in r['sources']}
    assert all(math.isfinite(v) for v in injection.values())
    arrays = {a['id']: a for a in via['arrays']}
    results = []
    for wr, vr in zip(wire['roles'], via['roles']):
        assert wr['role'] == vr['role'] and wr['sources'] == vr['sources']
        names = wr['sources']
        currents_A = [injection[s] for s in names]
        paths = {s: set(vr['via_paths'][s]) for s in names}
        scenarios = {}
        for technology, wire_scale, via_scale in [('LEF', 1., 1.), ('KPEX', .088 / .103, 9. / 20.)]:
            for geometry in ('original_two_cut', 'candidate_common_four_cut'):
                values = {key: value['parallel_ohm'] * via_scale /
                          (2 if geometry == 'candidate_common_four_cut' and key in changed else 1)
                          for key, value in arrays.items()}
                branch = {key: sum(injection[s] for s in names if key in paths[s]) for key in values}
                via_matrix = [[sum(values[e] for e in sorted(paths[a] & paths[b])) for b in names] for a in names]
                if technology == 'LEF' and geometry == 'original_two_cut':
                    assert via_matrix == vr['added_via_transfer_ohm']
                wire_V = [sum(wr['transfer_ohm'][i][j] * wire_scale * value for j, value in enumerate(currents_A)) for i in range(len(names))]
                via_V = [sum(via_matrix[i][j] * value for j, value in enumerate(currents_A)) for i in range(len(names))]
                error = max(abs(via_V[i] - sum(values[e] * branch[e] for e in paths[s])) for i, s in enumerate(names))
                assert error < 1e-15
                total_V = [a + b for a, b in zip(wire_V, via_V)]
                scenarios[technology + ':' + geometry] = dict(max_drop_V=max(total_V), min_drop_V=min(total_V),
                    per_source=[dict(source=s, injection_A=injection[s], partial_wire_V=wire_V[i],
                                     partial_ledger_via_V=via_V[i], partial_total_V=total_V[i]) for i, s in enumerate(names)],
                    independent_via_KCL_matrix_error_V=error,
                    arrays=[dict(id=e, wire_current_A=branch[e], parallel_ohm=values[e], drop_V=branch[e] * values[e])
                            for e in sorted(set().union(*paths.values()))])
        results.append(dict(role=wr['role'], sources=len(names), total_injection_A=sum(currents_A), scenarios=scenarios))
    args.output.mkdir(exist_ok=False)
    files = (args.wire, args.via, args.currents, args.candidate / 'preparation.json',
             args.candidate / 'changed_shapes.json', lef, tech, rex, Path(__file__))
    report = dict(status='passed partial nominal sensitivity evaluation; full IR qualification not run',
        inputs={str(p): sha(p) for p in files}, canonical_source_sha256=currents['source_sha256'],
        source_count=76, total_wire_injection_A=sum(injection.values()), nominal_temperature_C=27,
        current_basis='Full1036 common-wrapper inference qualified with representative22 external ports, not individually metered all ports.',
        representative_control=currents['representative_control'],
        aggregate_node_KCL_residual_A=currents['aggregate_maximum_abs_kcl_residual_A'],
        resistance_scenarios=dict(LEF=dict(M2_M4_ohm_per_square=.103, Via2_Via3_ohm_per_cut=20),
                                  KPEX=dict(M2_M4_ohm_per_square=.088, Via2_Via3_ohm_per_cut=9)),
        pinned_native_R_conversion_lines=conversion_lines, roles=results,
        omitted=via['omitted'], adoption='not run', full_IR_PVT_transient_lifetime='not run', seed='not applicable')
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (args.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({r['role']: {key: value['max_drop_V'] for key, value in r['scenarios'].items()} for r in results}, indent=2))


if __name__ == '__main__':
    main()
