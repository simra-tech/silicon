#!/usr/bin/env python3
"""Require full nonBGR OP draw parity before a separately authorized transient."""
import argparse
import hashlib
import json
from pathlib import Path

SIM = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    directories = [SIM / 'qualification' / name for name in [args.baseline, args.candidate]]
    prepared = [json.loads((p / 'preparation.json').read_text()) for p in directories]
    provenance = [json.loads((p / 'provenance.json').read_text()) for p in directories]
    results = [json.loads((p / 'summary.json').read_text())[0] for p in directories]
    assert [p['kind'] for p in prepared] == ['baseline', 'candidate']
    old, new = [r['ordered_parameter_groups'].get('NON_BGR_ALL', []) for r in results]
    caps = [pair for pair in old if pair[0].startswith('@c.')]
    prefixes = [(p / 'draw_audit.cir').read_text().split('.control\n')[0].replace(p.name, '@RUN@') for p in directories]
    checks = {
        'both_OP_inventories_qualified': all(r['op_inventory_qualification_status'] == 'passed' for r in results),
        'same_seed_and_room_temperature': all(p['seed'] == 71002 and p['temperature_C'] == 25 for p in prepared),
        'same_nonBGR_sources': all(sha(directories[0] / name) == sha(directories[1] / name) for name in ['sense.spice', 'trip.spice']),
        'same_circuit_prefix_except_BRG_source_contents': prefixes[0] == prefixes[1],
        'same_runtime_models': provenance[0]['runtime_identity'] == provenance[1]['runtime_identity'],
        'same_complete_nonBGR_query_order': len(old) == len(new) == 8670 and [p[0] for p in old] == [p[0] for p in new],
        'all8670_nonBGR_values_exact': len(old) == len(new) == 8670 and old == new,
        'six_CMIM_random_scales_present_exact': len(caps) == 6 and caps == [p for p in new if p[0].startswith('@c.')],
        'old27_and_candidate24_anchors_exact': all(r['original_legacy_required_exact'] for r in results),
        'new2842_nominal_parameters_exact': results[1]['candidate2842_all_nominal_exact'] is True,
        'all_inputs_match_preparation': all(all(p['input_checks'].values()) for p in provenance),
    }
    new_values = dict(new)
    differences = [{'parameter': key, 'baseline': value, 'candidate': new_values.get(key)}
                   for key, value in old if value != new_values.get(key)]
    legacy = [dict(r['ordered_parameter_groups'].get('LEGACY27', [])) for r in results]
    old_bgr = [{'parameter': key, 'baseline': value, 'candidate': legacy[1].get(key),
                'unchanged': value == legacy[1].get(key)} for key, value in legacy[0].items() if '.xbgr.' in key]
    output = {'status': 'passed full nonBGR OP draw parity' if all(checks.values()) else 'failed draw-parity gate',
              'baseline_run': args.baseline, 'candidate_run': args.candidate, 'checks': checks,
              'nonBGR_parameter_changes': differences, 'old_three_BGR_observations': old_bgr,
              'ordered_group_counts': [{tag: len(rows) for tag, rows in r['ordered_parameter_groups'].items()} for r in results],
              'evidence_hashes': [{name: sha(p / name) for name in ['preparation.json', 'provenance.json', 'summary.json', 'draw_audit.cir', 'non_bgr_inventory.json']} for p in directories],
              'scope': 'Observed complete8670nonBGRmismatchparameters at reconstructedroomOP, plus24originalanchors. BGRnominal replacement is a different circuit, not samewholechip sample. OPparity does not establish transient behavior, hotfullinventory, recalibration, reliability or yield. Any transient requires separate authorization; originalhotfailures retained.'}
    with args.output.open('x') as stream:
        json.dump(output, stream, indent=2)
        stream.write('\n')
    print(output['status'])
    print(json.dumps(checks, indent=2))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == '__main__':
    main()
