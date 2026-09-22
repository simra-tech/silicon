#!/usr/bin/env python3
"""Summarize retained fixed-calibration process/supply populations separately."""
import argparse, hashlib, json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run-ids', default='')
    ap.add_argument('--batch-prefix')
    ap.add_argument('--output', required=True)
    a=ap.parse_args()
    runs=[x for x in a.run_ids.split(',') if x]
    expected=None
    if a.batch_prefix:
        batch=json.loads((HERE/'runs'/(a.batch_prefix+'_batch.json')).read_text())
        expected=len(batch['expected_seeds'])
        runs.extend(f'{a.batch_prefix}_s{s}' for s in batch['expected_seeds'])
    groups={};rows=[];missing=[]
    for run in runs:
        path=HERE/'runs'/run/'manifest.json'
        if not path.exists():missing.append(run);continue
        m=json.loads(path.read_text())
        for sample in m['cases']:
            points=[p for child in sample['children'] for p in child['cases']]
            independent=sample.get('independent_points',[])
            row={'run_id':run,'manifest_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                 'corner':m['corner'],'seed':sample['seed'], 'numerical_and_fingerprint_status':sample['status'],
                 'attempted_transients':len(points),'completed_transients':sum(p['status']=='passed' for p in points),
                 'failed_transients':sum(p['status']=='failed' for p in points),
                 'timeouts':sum(p['timed_out'] for p in points),
                 'fixed_parameters':sample.get('frozen_parameter_status','not run'),
                 'independent_points':independent,
                 'hbt_vce_status':'passed' if points and all(p.get('hbt_vce_status')=='passed' for p in points) else 'failed or incomplete'}
            for method in ['linear','nominal_lut','reciprocal']:
                values=[p[method+'_error_C'] for p in independent]
                status='not run'
                if len(independent)==4:
                    status='passed' if all(p[method+'_status']=='passed' for p in independent) else 'failed'
                row[method]={'status':status,'maximum_abs_error_C':max((abs(v) for v in values if v is not None),default=None)}
            rows.append(row)
    for corner in sorted({r['corner'] for r in rows}):
        rr=[r for r in rows if r['corner']==corner]
        groups[corner]={'attempted_samples':len(rr),'complete_samples':sum(r['numerical_and_fingerprint_status']=='passed' for r in rr),
                        'completed_transients':sum(r['completed_transients'] for r in rr),
                        'failed_transients':sum(r['failed_transients'] for r in rr),'timeout_transients':sum(r['timeouts'] for r in rr),
                        'calibration_methods':{method:{'failed_samples':sum(r[method]['status']=='failed' for r in rr),
                                                       'not_run_samples':sum(r[method]['status']=='not run' for r in rr),
                                                       'maximum_abs_error_C':max((r[method]['maximum_abs_error_C'] for r in rr if r[method]['maximum_abs_error_C'] is not None),default=None)}
                                               for method in ['linear','nominal_lut','reciprocal']}}
    result={'expected_samples':expected if expected is not None else len(runs), 'groups':groups,'samples':rows,'not_run_manifests':missing,
            'calibration_policy':'Each corner/physical seed calibrated at25/100C nominal3.3/1.2V; coefficients frozen for low3.0/1.08 and high3.6/1.32V endpoints−40/125C. Only four independent points per sample.',
            'limitations':'Corner populations are separate; equal seed integers are not paired process samples. Frozen LUT/reciprocal candidates remain unadopted. Ideal IPTAT termination/output load and capacitance-only PEX; not packaged calibration or silicon yield.'}
    (HERE/a.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['samples','not_run_manifests']},indent=2))


if __name__=='__main__':main()
