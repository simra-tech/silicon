#!/usr/bin/env python3
"""Account for every saved API mismatch without inventing a matching waiver."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bulk', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    (a.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    all_results = {}
    for variant, folder in [('original','fullchip-api-original-20260923-r6'),
                            ('adapter','fullchip-api-adapter-20260923-r1')]:
        root = a.bulk/folder
        paths = [root/'summary.json', root/'diagnostic/summary.json', root/'diagnostic/comparison.json']
        receipt, summary, pairs = [json.loads(p.read_text()) for p in paths]
        assert receipt['status'] == 'completed diagnostic; inspect strict outcome' and receipt['inputs_unchanged']
        assert summary['status'] == 'failed scoped API comparison' and not summary['engine_equivalent']
        assert len(pairs) == 1 and pairs[0]['status'] == 'NoMatch'
        pair = pairs[0]
        assert summary['clone_checks']['binary64_parameters'] == 428749
        assert summary['clone_checks']['actual_terminal_bindings'] == 245160
        assert all(r['status'] == 'passed expected disposition' for r in summary['API_controls'])
        bad = pair['bad']['device']
        assert len(bad) == pair['pairs']['device']['Mismatch']
        assert len(pair['bad']['net']) == pair['pairs']['net']['Mismatch']
        groups, origin, rows = Counter(), Counter(), []
        for i, row in enumerate(bad):
            left, right = row['layout'], row['reference']
            groups[(left['model'] if left else '<absent>', right['model'] if right else '<absent>')] += 1
            origin[(right['name'].split('.')[0] if right else '<unpaired native>')] += 1
            diffs = {}
            if left and right:
                assert left['parameters'].keys() == right['parameters'].keys()
                for name in left['parameters']:
                    lv, rv = float(left['parameters'][name]), float(right['parameters'][name])
                    if lv.hex() != rv.hex():
                        diffs[name] = dict(layout=lv, reference=rv, difference=lv-rv,
                                           layout_binary64=lv.hex(), reference_binary64=rv.hex())
            rows.append(dict(index=i, pair=row, literal_parameter_differences=diffs,
                             cause='Unresolved: comparator pairing is not independent source identity proof'))
        models = {}
        for side in ('layout','reference'):
            inventory = summary['after_simplify'][side]
            assert sum(inventory['models'].values()) == inventory['devices']
            models[side] = {k.lower():v for k,v in inventory['models'].items()}
        all_results[variant] = dict(status='failed strict comparison; complete saved mismatch accounting passed',
            input_sha256={str(p.relative_to(a.bulk)):sha(p) for p in paths},
            wall_s=receipt['run']['wall_s'], pair_statuses=pair['pairs'], models=models,
            model_count_deltas={m:models['layout'].get(m,0)-models['reference'].get(m,0)
                                for m in sorted(set(models['layout'])|set(models['reference']))},
            bad_model_pairs=[dict(layout=k[0],reference=k[1],count=v) for k,v in sorted(groups.items())],
            reference_origin_counts=dict(sorted(origin.items())), bad_devices=rows,
            bad_nets=pair['bad']['net'], layout_pin_count=len(summary['after_simplify']['layout']['pins']),
            reference_pin_count=len(summary['after_simplify']['reference']['pins']),
            strict_pin_pair_identity=summary['strict_actual_pin_pair_identity'])
    old, new = all_results['original'], all_results['adapter']
    assert old['models']['layout'] == new['models']['layout']
    assert {k:v for k,v in old['models']['reference'].items() if k!='ptap1'} == {
        k:v for k,v in new['models']['reference'].items() if k!='ptap1'}
    assert old['pair_statuses']['device']['Match'] == new['pair_statuses']['device']['Match'] == 61023
    assert new['pair_statuses']['device']['Mismatch']-old['pair_statuses']['device']['Mismatch'] == 386
    result = dict(status='passed complete diagnostic accounting; both strict comparisons FAILED',
        views=all_results, source_prefix_effect='386 reachable source taps newly visible; no native change',
        caveats=['Literal parameter deltas are not necessarily the comparator failure cause; stock primary/secondary semantics retained.',
                 'Node names on opposite sides are not assumed equivalent or unequal by spelling.',
                 'All 93 engine pin pairs carry Match, but actual 71-versus-22 interface identity fails.',
                 'No inference that every discrepancy belongs to IO; source-origin ledger includes core DUT and dose records.'],
        not_run=['Native extraction on adapter','Physical interface adapter','Source-global or PolyRes remedy adoption'],
        not_applicable=['Analog simulation','Statistical seed'], script_sha256=sha(Path(__file__)))
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])


if __name__ == '__main__':
    main()
