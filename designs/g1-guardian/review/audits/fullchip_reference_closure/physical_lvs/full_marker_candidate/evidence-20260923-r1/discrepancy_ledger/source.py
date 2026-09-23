#!/usr/bin/env python3
"""Account for every current strict comparison failure without a waiver."""
import argparse
from collections import Counter
import json
from pathlib import Path
from prepare_saved_workers import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('original', 'adapter', 'dummy', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); assert not a.output.exists()
    views = {}
    for name in ('original', 'adapter', 'dummy'):
        folder = getattr(a, name)
        paths = [folder / 'summary.json', folder / 'diagnostic/summary.json', folder / 'diagnostic/comparison.json']
        receipt, report, pairs = [json.loads(q.read_text()) for q in paths]
        assert receipt['status'] == 'completed diagnostic; inspect strict outcome' and receipt['inputs_unchanged']
        assert len(pairs) == 1
        pair = pairs[0]
        assert all(r['status'] == 'passed expected disposition' for r in report['API_controls'])
        assert report['clone_checks']['all_61521_primitive_records'] == 'passed'
        assert report['physical_interface_metadata']['status'].startswith('passed')
        details = {}
        for kind in ('device', 'net', 'pin', 'subcircuit'):
            bad = pair['bad'][kind]
            expected_bad = sum(v for k, v in pair['pairs'][kind].items() if k != 'Match')
            if kind == 'pin':
                expected_bad += sum(r['status'] == 'Match' for r in bad)
                assert all(r['layout'] != r['reference'] or r['layout'] is None
                           for r in bad if r['status'] == 'Match')
            assert len(bad) == expected_bad
            details[kind] = bad
        groups, origins = Counter(), Counter()
        records = []
        for row in details['device']:
            left, right = row['layout'], row['reference']
            groups[(left['model'] if left else '<absent>', right['model'] if right else '<absent>')] += 1
            origins[right['name'].split('.')[0] if right else '<unpaired native>'] += 1
            differences = {}
            if left and right and set(left['parameters']) == set(right['parameters']):
                for key in left['parameters']:
                    lv, rv = float(left['parameters'][key]), float(right['parameters'][key])
                    if lv.hex() != rv.hex():
                        differences[key] = dict(layout=lv, reference=rv, layout_binary64=lv.hex(), reference_binary64=rv.hex())
            records.append(dict(pair=row, literal_parameter_differences=differences))
        models = {side: {m.lower(): n for m, n in report['after_simplify'][side]['models'].items()} for side in ('layout', 'reference')}
        views[name] = dict(strict_status=report['status'], engine_equivalent=report['engine_equivalent'],
                           hashes={str(q.relative_to(folder)): sha(q) for q in paths}, comparison_source_sha256=report['actual_comparison_source_sha256'],
                           exclusion=receipt['exclusion'], pair_statuses=pair['pairs'],
                           strict_actual_pin_pair_identity=report['strict_actual_pin_pair_identity'],
                           models=models, model_count_delta={m: models['layout'].get(m, 0) - models['reference'].get(m, 0)
                               for m in sorted(set(models['layout']) | set(models['reference']))},
                           bad_model_pairs=[dict(layout=k[0], reference=k[1], count=v) for k, v in sorted(groups.items())],
                           reference_origin_counts=dict(origins), bad_devices=records,
                           bad_nets=details['net'], bad_pins=details['pin'], bad_subcircuits=details['subcircuit'],
                           graph_proof=report['physical_interface_metadata'])
    assert views['original']['models']['layout'] == views['adapter']['models']['layout'] == views['dummy']['models']['layout']
    original, adapted = views['original']['models']['reference'], views['adapter']['models']['reference']
    assert {k:v for k,v in original.items() if k != 'ptap1'} == {k:v for k,v in adapted.items() if k != 'ptap1'}
    assert adapted['ptap1'] - original.get('ptap1', 0) == 386
    result = dict(status='passed complete saved discrepancy accounting; strict outcomes remain separate', views=views,
                  script_sha256=sha(Path(__file__)),
                  caveats=['Comparator-selected pairs are not independent physical-instance identity proof.',
                           'Literal parameter differences are not automatically the sole mismatch cause.',
                           'No A/P substitution, global substrate join, same-net hint, warning promotion or model/rule change.',
                           'Three excluded comparison dummies remain in canonical source and native geometry.'],
                  full_native_LVS='failed original source', physical_adoption='not run', floating_fill_PEX='not run')
    a.output.mkdir(parents=True)
    (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({name: row['pair_statuses'] for name, row in views.items()}, indent=2))


if __name__ == '__main__':
    main()
