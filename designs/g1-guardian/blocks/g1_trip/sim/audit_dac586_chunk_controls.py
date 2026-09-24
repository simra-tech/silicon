#!/usr/bin/env python3
"""Independently re-read bounded DAC continuation evidence without launching SPICE."""
import argparse
import json
from prepare_dac586_chunk_controls import ROOT, SIM, transform
from run_dac586_chunk_control import analyze
from run_dac586_static_control import sha


def audit(execution, digest):
    assert sha(execution) == digest
    packet = json.loads(execution.read_text())
    assert all(sha(ROOT/name) == value for name, value in packet['source_and_reference_sha256'].items())
    rows = []
    for label in ['room', 'hot']:
        out = SIM/'qualification'/(packet['prefix']+'-'+label)
        prep = json.loads((out/'preparation.json').read_text())
        assert sha(out/'preparation.json') == packet['preparations_sha256'][str((out/'preparation.json').relative_to(ROOT))]
        reference = SIM/'qualification'/prep['initial_reference']
        assert (out/'dac_chunk.cir').read_text() == transform((reference/'dac_static.cir').read_text(), reference.name, out.name, prep['groups'])
        assert sha(out/'dac_chunk.cir') == prep['deck_sha256']
        assert all(sha(out/name) == value for name, value in prep['source_hashes'].items())
        assert all(sha(ROOT/name) == value for name, value in prep['bindings_sha256'].items())
        assert sha(out/'population_inventory.json') == prep['inventory_sha256']
        required = ['run.json', 'run.log', 'summary.json', 'provenance.json']
        if not all((out/name).exists() for name in required):
            rows.append(dict(label=label, status='not run'))
            continue
        provenance = json.loads((out/'provenance.json').read_text())
        assert provenance['execution_sha256'] == digest
        assert provenance['runtime_identity'] == prep['expected_runtime_identity']
        assert provenance['runner_sha256'] == packet['source_and_reference_sha256'][str((SIM/'run_dac586_chunk_control.py').relative_to(ROOT))]
        assert all(provenance['input_checks'].values())
        result = analyze(out, prep, json.loads((out/'run.json').read_text()))
        assert result == json.loads((out/'summary.json').read_text()), 'Independent reanalysis differs'
        rows.append(dict(label=label, status=result['status'], errors=result['errors'],
            comparisons=result['anchor_comparisons'], timing=result.get('timing'),
            receipts_sha256={name: sha(out/name) for name in required + ['dac_chunk.cir', 'run.progress.jsonl']}))
    return dict(status='passed' if all(row['status']=='passed' for row in rows) else 'failed or incomplete',
        execution_sha256=digest, controls=rows,
        scope='Only same-instance 127/128/127 room/hot continuation; all-code population and dynamic settling not run.')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execution', required=True);p.add_argument('--execution-sha256', required=True)
    p.add_argument('--output', required=True);a=p.parse_args()
    result=audit(ROOT/a.execution,a.execution_sha256)
    output=ROOT/a.output;assert not output.exists()
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])
