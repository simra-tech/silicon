#!/usr/bin/env python3
"""Read-only exact-pair cache and original binary calibration decision replay."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from prepare_bgr_calibration_probe import transform
from run_bgr_substitution_transient import parameter_audit
from run_joint_calibration import calibration_codes

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(records):
    """Only an exact (soft,hard) tuple can satisfy the next original probe."""
    cache = {}
    for record in records:
        key = tuple(record['codes'])
        if key in cache:
            raise ValueError('Duplicate fixture requires explicit parity qualification')
        cache[key] = record
    valid = [r for r in records if r['status'] == 'passed']
    monotonic = {}
    for index, channel in enumerate(('soft', 'hard')):
        rows = sorted((r['codes'][index], r['decisions'][channel]) for r in valid)
        monotonic[channel] = all(a[1] >= b[1] for a, b in zip(rows, rows[1:]))
        # At a repeated code a different decision is also a violation, even
        # when sorting booleans might otherwise disguise its direction.
        monotonic[channel] &= all(a[1] == b[1] for a, b in zip(rows, rows[1:]) if a[0] == b[0])
    out = {'all_attempts': records, 'all_observed_probe_monotonicity': monotonic,
           'failed_attempts': [r['run'] for r in records if r['status'] != 'passed'],
           'selected_path': [], 'bracket_status': 'not run to completion',
           'scope': 'Original joint binary rule and rounding; exact code-pair cache only. Off-path attempts retained. Probed monotonicity is not full256-code qualification; nominal BGR substitution is not joint BGR mismatch.'}

    def probe(pair):
        record = cache.get(tuple(pair))
        if record is None:
            out['next_required_codes'] = pair
        elif record['status'] != 'passed':
            out['bracket_status'] = 'failed selected probe; no automatic retry'
            out['failed_selected_run'] = record['run']
        else:
            out['selected_path'].append(record['run'])
            return record['decisions']
        return None

    lo, hi = probe([0, 0]), probe([255, 255])
    if lo is None or hi is None:
        return out
    if not all(lo[k] and not hi[k] for k in ('soft', 'hard')):
        out['bracket_status'] = 'failed endpoint bracketing'
        return out
    lows, highs = [0, 0], [255, 255]
    while max(h-l for l, h in zip(lows, highs)) > 1:
        mid = [(l+h)//2 for l, h in zip(lows, highs)]
        decision = probe(mid)
        if decision is None:
            out['current_brackets'] = dict(zip(('soft', 'hard'), zip(lows, highs)))
            return out
        for i, channel in enumerate(('soft', 'hard')):
            if highs[i]-lows[i] > 1:
                if decision[channel]:
                    lows[i] = mid[i]
                else:
                    highs[i] = mid[i]
    out['brackets'] = dict(zip(('soft', 'hard'), zip(lows, highs)))
    out['off_path_runs'] = [r['run'] for r in records if r['run'] not in out['selected_path']]
    if not all(monotonic.values()):
        out['bracket_status'] = 'failed sampled monotonicity; no selected crossing adopted'
        return out
    out['bracket_status'] = 'passed selected probes'
    out.update(calibration_codes(out['brackets'], hard_nominal_code=204))
    out['fixed_residual_codes'] = {k: math.floor(sum(pair)/2+.5) for k, pair in out['brackets'].items()}
    return out


def load_record(name):
    run = SIM/'qualification'/name
    prep = json.loads((run/'preparation.json').read_text())
    row, = json.loads((run/'summary.json').read_text())
    assert prep['seed'] == row['seed'] == 71002
    assert prep['temperature_C'] == row['temperature_C'] == 25
    assert prep['shunt_V'] == row['shunt_V'] == .025
    assert prep['fixed_soft_hard_codes'] == row['codes']
    ref = SIM/'qualification'/prep['calibration_template_run']
    deck = run/'hard_+0mV.cir'
    assert deck.read_text() == transform((ref/deck.name).read_text(), ref.name, name, *row['codes'], .025, 25)
    assert sha(deck) == prep['prepared_deck_sha256']
    assert all(sha(run/key) == value for key, value in prep['source_hashes'].items())
    provenance = json.loads((run/'provenance.json').read_text())
    assert provenance['runtime_identity'] == prep['expected_runtime_identity']
    assert all(provenance['input_checks'].values())
    record = {'run': name, 'codes': row['codes'], 'status': row['probe_contract_status'],
              'decisions': row['decisions'], 'wall_s': row['wall_s'],
              'summary_sha256': sha(run/'summary.json'), 'deck_sha256': sha(deck),
              'provenance_sha256': sha(run/'provenance.json')}
    if record['status'] == 'passed':
        baseline = SIM/'qualification'/prep['full_nonBGR_baseline_run']
        base, = json.loads((baseline/'summary.json').read_text())
        inventory = json.loads((run/'non_bgr_inventory.json').read_text())
        audit = parameter_audit((run/'run.log').read_text(), prep, inventory, base['ordered_parameter_groups']['NON_BGR_ALL'])
        assert audit == row['parameter_audit'] and all(audit['checks'].values())
        assert row['wave_analysis']['sampling_status'] == 'passed'
        assert all(type(record['decisions'][k]) is bool for k in ('soft', 'hard'))
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = replay([load_record(name) for name in args.runs])
    result['auditor_sha256'] = sha(Path(__file__))
    result['original_algorithm_sha256'] = sha(SIM/'run_joint_calibration.py')
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'all_attempts'}, indent=2))


if __name__ == '__main__':
    main()
