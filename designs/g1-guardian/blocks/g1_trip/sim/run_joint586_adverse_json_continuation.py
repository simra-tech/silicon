#!/usr/bin/env python3
"""Explicit JSON-sequence adapter for an unchanged archived staged runner.

The original resumed-stage comparison rejects tuple conditions after JSON has
serialized them as lists. Only that representation is normalized here. Source,
runtime, provenance and all frozen per-leaf deck hashes remain checked by the
original runner. This does not rerun calibration or relax any numerical check.
"""
import json
from pathlib import Path
import sys
import run_joint586_adverse_staged as original

ORIGINAL_SHA = 'a754fc24ce389886647f3ce7aea03b36afda437da82142b6cce2a76059c32fc2'


def normalized_conditions(conditions, saved):
    normalized = json.loads(json.dumps(conditions))
    assert normalized == saved, 'Condition values/order changed, not serialization'
    return normalized


def qualify(out):
    assert original.sha(Path(original.__file__)) == ORIGINAL_SHA
    assert original.sha(out/'runner.py') == ORIGINAL_SHA
    saved = json.loads((out/'provenance.json').read_text())
    plan = json.loads((out/'heldout_plan.json').read_text())
    summary, = json.loads((out/'summary.json').read_text())
    assert saved['runner_sha256'] == plan['runner_sha256'] == ORIGINAL_SHA
    assert original.sha(out/'heldout_plan.json') == (out/'heldout_plan.sha256').read_text().strip()
    assert original.sha(out/'provenance.json') == plan['provenance_sha256']
    # Re-generate every declared leaf before and after the representation change.
    ref = original.SIM/'qualification'/original.REFERENCE
    deck = (ref/'population_transient.cir').read_text()
    before = original.heldout_plan(summary['calibration'], len(summary['probes']))
    original.CONDITIONS = normalized_conditions(original.CONDITIONS, saved['conditions'])
    after = original.heldout_plan(summary['calibration'], len(summary['probes']))
    assert before == after == [{k:v for k,v in r.items() if k != 'deck_sha256'} for r in plan['rows']]
    for row in plan['rows']:
        body = original.adverse_deck(deck, ref.name, out.name, plan['seed'], row['codes'], row['shunt_V'], row['condition'], plan['corner'])
        body = body.replace('qualification/'+out.name+'/phase0.dat', 'qualification/'+out.name+'/p%02d/phase0.dat' % row['index'])
        assert original.hashlib.sha256(body.encode()).hexdigest() == row['deck_sha256']
    return dict(scope='JSON tuple/list representation only; original checks remain active',
                adapter_sha256=original.sha(Path(__file__)), original_runner_sha256=ORIGINAL_SHA,
                plan_sha256=original.sha(out/'heldout_plan.json'),
                provenance_sha256=original.sha(out/'provenance.json'), unchanged_deck_count=60)


def main():
    assert sys.argv.count('--stage') == sys.argv.count('--run-id') == 1
    stage = sys.argv[sys.argv.index('--stage')+1]
    assert stage in ['leaf', 'assemble'], 'No calibration through this adapter'
    run_id = sys.argv[sys.argv.index('--run-id')+1]
    assert Path(run_id).name == run_id
    out = original.SIM/'qualification'/run_id
    receipt = qualify(out)
    suffix = stage
    if stage == 'leaf':
        assert sys.argv.count('--leaf-index') == 1
        suffix += '%02d' % int(sys.argv[sys.argv.index('--leaf-index')+1])
    destination = out/('json_continuation_adapter_'+suffix+'.json')
    try:
        with destination.open('x') as stream:
            json.dump(receipt, stream, indent=2); stream.write('\n')
    except FileExistsError:
        assert json.loads(destination.read_text()) == receipt
    original.main()


if __name__ == '__main__':
    main()
