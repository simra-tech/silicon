#!/usr/bin/env python3
"""Independent72 deterministic evidence audit; missing and failed checks retained."""
import argparse
import json
from pathlib import Path
from run_joint586_fast_nodeset_crossed_cm import SIM,sha,check_inputs,inspect_leaf


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True)
    p.add_argument('--preparation-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();out=SIM/'qualification'/a.run_id;records=[]
    for index in range(72):
        record=dict(index=index,evidence_status='not run',numerical_status='not run',electrical_status='not run')
        records.append(record);leaf=out/('p%02d'%index)
        if not (leaf/'summary.json').exists():continue
        try:
            prep,row,leaf=check_inputs(out,a.preparation_sha256,index)
            saved=json.loads((leaf/'summary.json').read_text());state=json.loads((leaf/'run.json').read_text())
            provenance=json.loads((leaf/'provenance.json').read_text())
            assert provenance['runtime_identity']==prep['runtime_identity']
            assert provenance['preparation_sha256']==a.preparation_sha256
            assert provenance['source_hashes']==prep['source_hashes']
            assert sha(leaf/'runner.py')==provenance['runner_sha256']==sha(SIM/'run_joint586_fast_nodeset_crossed_cm.py')
            assert saved['runtime']==state and all(saved[k]==v for k,v in row.items())
            assert state['status'] in ['completed','timeout']
            record.update(evidence_status='passed failed-attempt receipts retained',
                numerical_status=saved['numerical_status'],electrical_status=saved['electrical_status'],
                receipts_sha256={n:sha(leaf/n) for n in ['summary.json','run.json','run.log','provenance.json','probe.cir']})
            if saved['numerical_status']=='passed':
                found=inspect_leaf(prep,row,leaf);assert all(saved[k]==v for k,v in found.items())
                record.update(evidence_status='passed independent full-vector/wave/decision audit',
                    actual_decisions=found['decisions'],expected_decisions=row['expected_decisions'],
                    actual_input_observation=found['actual_input_observation'])
        except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:
            record.update(evidence_status='failed evidence audit',analysis_error=repr(error))
    result=dict(status='completed72-check audit; no population credit',records=records,requested_checks=72,
        not_run=sum(r['evidence_status']=='not run' for r in records),
        evidence_failed=sum(r['evidence_status']=='failed evidence audit' for r in records),
        numerical_passed=sum(r['numerical_status']=='passed' for r in records),
        numerical_failed=sum(r['numerical_status']=='failed' for r in records),
        electrical_passed=sum(r['electrical_status']=='passed' for r in records),
        electrical_failed=sum(r['electrical_status']=='failed' for r in records),
        preparation_sha256=a.preparation_sha256,auditor_sha256=sha(Path(__file__)),
        scope='Same calibrated fixed-nodeset fast78101 draw,72 deterministic crossings,not72independent draws. No population credit or original non-nodeset equivalence. All original criteria/failures retained.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(a.output,sha(a.output))
    raise SystemExit(0 if not result['evidence_failed'] and not result['not_run'] else 1)


if __name__=='__main__':main()

