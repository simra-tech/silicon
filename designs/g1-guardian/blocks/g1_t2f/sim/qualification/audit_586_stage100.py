#!/usr/bin/env python3
"""Classify all100 attempted samples; keep electrical/solver failures explicit."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_586_calibration_samples import HERE, REFERENCE, sha
from run_bgr_substitution_draw_audit import read_group


def terminal_outcome(parent):
    return parent.get('status') not in [None, 'running', 'not run', 'paused before next leaf; remaining conditions not run']


def isolated_watchdog(runtime, failed):
    return (runtime == failed.get('runtime') and runtime.get('status') == 'timeout'
        and runtime.get('timeout_s') == 600 and not failed.get('errors'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    audit = json.loads(args.audit.read_text())
    assert audit['status'] == 'passed read-only evidence audit' and audit['requested_samples'] == 100
    assert [r['seed'] for r in audit['records']] == list(range(74101,74201))
    prep = json.loads((REFERENCE/'preparation.json').read_text())
    records, problems = [], []
    for record in audit['records']:
        row = dict(seed=record['seed'], evidence_status=record.get('evidence_status'),
            numerical_status='not run', original_accuracy_status='not run', failed_leaves=[])
        records.append(row)
        try:
            assert record['evidence_status'] == 'passed'
            run = HERE/'runs'/record['run']
            assert sha(run/'summary.json') == record['summary_sha256']
            assert sha(run/'provenance.json') == record['provenance_sha256']
            parent, = json.loads((run/'summary.json').read_text())
            assert terminal_outcome(parent) and parent['leaves']
            if record['numerical_completed_leaves'] == 4:
                assert record['complete'] and parent['status'] in ['passed','failed original linear calibration']
                row.update(numerical_status='passed all4', original_accuracy_status='passed' if parent['status']=='passed' else 'failed original linear calibration')
            else:
                expected = parent.get('parameters_first_completed_leaf')
                for entry in parent['leaves']:
                    if entry['status'] == 'passed':
                        continue
                    leaf = run/('p%02d' % entry['index'])
                    failed, = json.loads((leaf/'summary.json').read_text())
                    runtime = json.loads((leaf/'run.json').read_text())
                    assert isolated_watchdog(runtime,failed), 'Non-watchdog error needs separate source/harness diagnosis'
                    log = (leaf/'run.log').read_text()
                    item = dict(index=entry['index'], status='failed original600s watchdog; no retry',
                        before3180_status='not run to completion', after3180_status='not run to completion',
                        runtime=runtime, log_sha256=sha(leaf/'run.log'))
                    before = None
                    for when in ['BEFORE','AFTER']:
                        if all('P0_'+tag+'_'+when+'_END' in log for tag in prep['groups']):
                            values = {tag: read_group(log,'P0_'+tag+'_'+when,keys) for tag,keys in prep['groups'].items()}
                            assert sum(map(len,values.values())) == 3180
                            if expected is not None:
                                assert values == expected
                            if when == 'BEFORE':
                                before = values
                            elif before is not None:
                                assert values == before
                            item[when.lower()+'3180_status'] = 'passed full query inventory; exact same-sample anchor when available'
                            item[when.lower()+'_vector_sha256'] = hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()
                    row['failed_leaves'].append(item)
                assert row['failed_leaves'], 'Incomplete coverage without classified numerical failure'
                row.update(numerical_status='failed isolated recorded watchdog', original_accuracy_status='not run to completion')
        except (AssertionError,OSError,ValueError,KeyError,IndexError) as error:
            row['disposition_error'] = repr(error)
            problems.append(dict(seed=record['seed'],error=repr(error)))
    vectors = [r['full_parameter_vector_sha256'] for r in audit['records'] if r.get('full_parameter_vector_sha256')]
    if len(vectors) != len(set(vectors)):
        problems.append(dict(error='Duplicate available full sample vectors'))
    if audit['primitive_distinctness']['status'] != 'passed':
        problems.append(dict(error='Available complete-sample primitive distinctness did not pass'))
    result = dict(status='passed source/harness audit disposition; continue fixed300 characterization' if not problems else 'blocked source/parameter/harness disposition',
        fixed_sample_denominator=100, attempted_samples=len(records),
        numerically_complete_samples=sum(r['numerical_status']=='passed all4' for r in records),
        isolated_numerical_failed_samples=sum(r['numerical_status']=='failed isolated recorded watchdog' for r in records),
        original_accuracy_passed_samples=sum(r['original_accuracy_status']=='passed' for r in records),
        original_accuracy_failed_samples=sum(r['original_accuracy_status']=='failed original linear calibration' for r in records),
        accuracy_not_run_to_completion_samples=sum(r['original_accuracy_status']=='not run to completion' for r in records),
        records=records, blocking_problems=problems, full_evidence_audit_sha256=sha(args.audit),
        classifier_sha256=sha(Path(__file__)),
        scope='Required100-screen boundary for predeclared300. Electrical failures and isolated archived600s solver watchdog failures stayfailed in fixeddenominator; no retry, replacement, survivor yield or acceptance change. Source/parameter/harness discrepancies block release. Full3180/accuracy absent on incomplete leaves is explicitlynotrun, never inferredpassed.')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['records']},indent=2))
    raise SystemExit(0 if not problems else 1)


if __name__ == '__main__':
    main()
