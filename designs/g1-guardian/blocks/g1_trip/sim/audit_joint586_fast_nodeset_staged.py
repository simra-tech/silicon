#!/usr/bin/env python3
"""Independent single-sample audit including immutable parallel scheduling ledger."""
import argparse
import json
from pathlib import Path
from audit_joint586_fast_nodeset_calibration import inspect, first_sample_gate
from run_joint586_fast_nodeset_staged import SIM, ROOT, sha, heldout_plan


def staged_inspect(run, contract):
    record = inspect(run, contract)
    result, = json.loads((run/'summary.json').read_text())
    if result['bracket_status'] != 'passed selected probes':
        record['staged_plan_status'] = 'not applicable; failed calibration retained'
        return record
    plan = json.loads((run/'heldout_plan.json').read_text())
    assert sha(run/'heldout_plan.json') == (run/'heldout_plan.sha256').read_text().strip()
    assert plan['runner_sha256'] == sha(run/'runner.py')
    assert plan['provenance_sha256'] == sha(run/'provenance.json')
    assert plan['calibration_summary_sha256'] == sha(run/'calibration_checkpoint.json')
    checkpoint, = json.loads((run/'calibration_checkpoint.json').read_text())
    assert plan['vector'] == checkpoint['parameters_before_first_probe'] == result['parameters_before_first_probe']
    assert len(plan['vector']) == 11512
    assert checkpoint['calibration'] == result['calibration']
    assert (plan['seed'],plan['corner']) == (result['seed'],result['corner'])
    n = len(checkpoint['probes'])
    assert result['probes'][:n] == checkpoint['probes']
    expected = heldout_plan(result['calibration'], n)
    assert [{k:v for k,v in row.items() if k != 'deck_sha256'} for row in plan['rows']] == expected
    assert len(result['probes']) == n+60
    for row, entry in zip(plan['rows'], result['probes'][n:]):
        leaf = run/('p%02d' % row['index'])
        assert json.loads((leaf/'entry.json').read_text()) == entry
        assert sha(leaf/'probe.cir') == row['deck_sha256'] == entry['deck_sha256']
        assert all(entry[k] == row[k] for k in ['codes','shunt_V','condition','kind','expected_decisions'])
    record.update(staged_plan_status='passed immutable60 ledger and ordered assembly',
                  staged_plan_sha256=sha(run/'heldout_plan.json'), calibration_checkpoint_sha256=sha(run/'calibration_checkpoint.json'))
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--contract', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args();assert not a.output.exists()
    run = SIM/'qualification'/a.run_id
    try:
        row = staged_inspect(run,a.contract);row['evidence_status']='passed'
    except (AssertionError,OSError,ValueError,KeyError,IndexError) as error:
        row = dict(run=a.run_id,status='failed evidence audit',complete=False,evidence_status='failed',error=repr(error))
    result = dict(status='passed read-only evidence audit; electrical failures separate' if row['evidence_status']=='passed' else 'failed evidence audit',
        requested_samples=1,completed_samples=int(row['complete']),records=[row],campaign_contract_sha256=sha(a.contract),
        auditor_sha256=sha(Path(__file__)),base_auditor_sha256=sha(SIM/'audit_joint586_fast_nodeset_calibration.py'))
    result['first_sample_gate_passed'] = first_sample_gate(result)
    with a.output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
    raise SystemExit(0 if result['first_sample_gate_passed'] else 1)


if __name__=='__main__':main()
