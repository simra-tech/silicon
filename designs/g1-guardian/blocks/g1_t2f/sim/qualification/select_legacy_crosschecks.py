#!/usr/bin/env python3
"""Retain all native failures and near-boundary samples for legacy confirmation.
Selection applies independently to linear and unchanged nominal-curve results.
"""
import csv,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
linear=list(csv.DictReader((HERE/'mc100_samples.csv').open()))
candidate={int(r['seed']):r for r in csv.DictReader((HERE/'curvature_candidate100_samples.csv').open())}
rows=[]
for r in linear:
 seed=int(r['seed'])
 if seed<51021 or r['calibration_status']=='not run':continue
 c=candidate[seed];values=[float(r['cold_residual_C']),float(r['hot_residual_C']),float(c['candidate_cold_residual_C']),float(c['candidate_hot_residual_C'])]
 failure=any(abs(v)>2 for v in values);near=any(abs(abs(v)-2)<=.05 for v in values)
 if not(failure or near):continue
 name=f't2f_mc100_legacycheck_s{seed}_20260921_01';p=HERE/'runs'/name/'manifest.json';cases=json.loads(p.read_text())['cases'] if p.exists() else []
 row={'seed':seed,'native_run_id':r['run_id'],'legacy_run_id':name,'selection_failure':failure,'selection_within_0p05C_of_boundary':near,'native_linear_cold_residual_C':float(r['cold_residual_C']),'native_linear_hot_residual_C':float(r['hot_residual_C']),'legacy_status':'not run'}
 if len(cases)==4 and all(c['status']=='passed' for c in cases):
  f={c['temperature_C']:c['measurements']['freq'] for c in cases};slope=(f[100]-f[25])/75;errors={t:25+(f[t]-f[25])/slope-t for t in [-40,125]}
  row.update(legacy_status='passed',legacy_linear_cold_residual_C=errors[-40],legacy_linear_hot_residual_C=errors[125],maximum_linear_error_difference_C=max(abs(errors[-40]-float(r['cold_residual_C'])),abs(errors[125]-float(r['hot_residual_C']))),legacy_linear_acceptance='passed' if max(map(abs,errors.values()))<=2 else 'failed',native_linear_acceptance=r['calibration_status'])
 rows.append(row)
result={'selection':'Every new native physical sample with any linear/candidate endpoint failure or any endpoint within0.05C of either±2C boundary; frozen curve, no refitting. These repeats confirm runtime sensitivity and do not replace or prune the original ensemble.','samples':rows,'selected_samples':len(rows),'completed_crosschecks':sum(r['legacy_status']=='passed' for r in rows)}
(HERE/'legacy_crosscheck_selection.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
