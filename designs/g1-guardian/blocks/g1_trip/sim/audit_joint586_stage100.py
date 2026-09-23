#!/usr/bin/env python3
"""Fixed100 disposition: preserve electrical/isolated solver failures, block corrupt evidence."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from audit_joint586_calibration import SIM,REFERENCE,sha
from audit_joint586_population_op import variation
from analyze_joint586_failed_leaf import failed_inventory
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import analyze_wave
from wave_archive import open_wave


def terminal(status):
    return status not in [None,'running','not run','paused before next leaf']


def classify_numerical_failure(runtime,entry):
    if entry.get('errors'):return 'blocked explicit solver/harness error'
    if runtime.get('status')=='timeout' and runtime.get('timeout_s')==1200:
        return 'isolated original1200s watchdog'
    if runtime.get('status')=='completed' and runtime.get('returncode')==0:
        return 'completed analysis requires independent waveform classification'
    return 'blocked unclassified execution failure'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--audit',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    audit=json.loads(a.audit.read_text())
    assert audit['status'].startswith('passed read-only evidence audit') and audit['requested_samples']==100
    assert [r['seed'] for r in audit['records']]==list(range(73001,73101))
    prep=json.loads((SIM/'qualification'/REFERENCE/'preparation.json').read_text())
    records=[];problems=[];vectors=[]
    for record in audit['records']:
        row=dict(seed=record['seed'],original_status=record['status'],numerical_status='not run',
            full_requested_guard_residual_status='not run',failed_leaves=[]);records.append(row)
        try:
            assert record['complete'] and terminal(record['status'])
            run=SIM/'qualification'/record['run']
            assert sha(run/'summary.json')==record['summary_sha256'] and sha(run/'provenance.json')==record['provenance_sha256']
            parent,=json.loads((run/'summary.json').read_text());assert parent['probes']
            expected=parent['parameters_before_first_probe'];sample_vector=expected
            for entry in parent['probes']:
                if entry['status']=='passed':continue
                leaf=run/entry['run'].split('/')[-1]
                runtime=json.loads((leaf/'run.json').read_text());kind=classify_numerical_failure(runtime,entry)
                if kind=='isolated original1200s watchdog':
                    failure=failed_inventory(run,entry,prep,expected)
                    if sample_vector is None:sample_vector=failure.get('parameters_before')
                    failure={k:v for k,v in failure.items() if k not in ['parameters_before','parameters_after']}
                    row['failed_leaves'].append(failure)
                elif kind=='completed analysis requires independent waveform classification':
                    log=(leaf/'run.log').read_text();section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S)
                    assert expected is not None
                    phase_parameters(section,prep['groups'],expected)
                    with open_wave(leaf/'phase0.dat','rb') as stream:blob=stream.read()
                    data=[list(map(float,line.split())) for line in blob.decode().splitlines()[1:] if line.strip()]
                    assert data and all(len(r)==18 and all(math.isfinite(v) for v in r) for r in data) and abs(data[-1][0]-1.02e-6)<1e-18
                    decision=analyze_wave([r[:13] for r in data],prep['prospective_sampling'])
                    assert decision['sampling_status']!='passed','Originalfailedentry notexplained by independentlyreproduced decisionfailure'
                    row['failed_leaves'].append(dict(run=entry['run'],status='failed electrical decision sampling; fullnumeric/inventory evidence independently valid',
                        full11512_status='passed',decoded_wave_sha256=hashlib.sha256(blob).hexdigest(),sampling_status=decision['sampling_status']))
                else:raise AssertionError(kind)
            if sample_vector is not None:
                assert len(sample_vector)==11512
                vectors.append((record['seed'],sample_vector))
            row['numerical_status']='failed isolated recorded watchdog' if any(r['status'].startswith('failed original1200s') for r in row['failed_leaves']) else 'completed attempted analyses'
            if parent['status']=='passed fullcalibration guard residual':
                row['full_requested_guard_residual_status']='passed'
            elif parent['bracket_status']=='passed selected probes':
                row['full_requested_guard_residual_status']='failed original electrical or numerical criteria; all requested leaves retained'
            else:
                row['full_requested_guard_residual_status']='not run after failed calibration; failed sample retained'
            row['source_harness_disposition']='passed evidence classification; original outcome unchanged'
        except (AssertionError,OSError,ValueError,KeyError,IndexError) as error:
            row['source_harness_disposition']='blocked';row['error']=repr(error);problems.append(dict(seed=record['seed'],error=repr(error)))
    primitive_checks=[]
    if vectors:
        first_seed,first=vectors[0]
        for seed,vector in vectors[1:]:
            bytype=variation(first,vector)
            passed=all(r['primitive_count']==r['primitives_with_changed_values'] for r in bytype.values())
            primitive_checks.append(dict(seed=seed,reference_seed=first_seed,status='passed' if passed else 'failed',groups=bytype))
            if not passed:problems.append(dict(seed=seed,error='Availablefull11512draw doesnotvary acrossall3500 randomizedprimitives'))
    output=dict(status='passed source/harness disposition; continue predeclared300 characterization' if not problems else 'blocked source/parameter/harness disposition',
        fixed_sample_denominator=100,terminal_samples=sum(r.get('complete',False) for r in audit['records']),
        original_full_passed_samples=sum(r['original_status']=='passed fullcalibration guard residual' for r in records),
        original_failed_samples=sum(terminal(r['original_status']) and r['original_status']!='passed fullcalibration guard residual' for r in records),
        isolated_numerical_failed_samples=sum(r['numerical_status']=='failed isolated recorded watchdog' for r in records),
        available_full_vectors=len(vectors),primitive_variation_checks=primitive_checks,records=records,blocking_problems=problems,
        evidence_audit_sha256=sha(a.audit),classifier_sha256=sha(Path(__file__)),
        scope='Fixed100screenforpredeclared300, includingoriginal36failures. Exactsource/deck/runtime/wave audit remainsmandatory. Electricalfailures and diagnosedoriginal1200s solverfailures remainfailedsamples, not survivorfiltering or permission to omitremaining200. MissingAFTER/legacy/wave explicitlynotrun. Source/harness/parameter inconsistencies block launch; no retry/replacement/calibration/threshold change.')
    a.output.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:v for k,v in output.items() if k not in ['records','primitive_variation_checks']},indent=2))
    raise SystemExit(0 if not problems else 1)


if __name__=='__main__':main()
