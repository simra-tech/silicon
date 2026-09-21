#!/usr/bin/env python3
"""Check four held-out temperatures with previously fixed per-sample calibration.
The optional nominal correction is frozen in fixed_nominal_curve.json.
"""
import bisect,csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
samples=list(csv.DictReader((ROOT/'mc20_samples.csv').open()))
frozen=json.loads((ROOT/'fixed_nominal_curve.json').read_text());curve=frozen['curve_pairs_linear_reading_C_actual_temperature_C'];xs=[p[0] for p in curve]
def correct(value):
 i=max(0,min(len(curve)-2,bisect.bisect_right(xs,value)-1));(x0,y0),(x1,y1)=curve[i:i+2];return y0+(value-x0)*(y1-y0)/(x1-x0)
rows=[]
for sample in samples:
 seed=int(sample['seed']);base=json.loads((ROOT/'runs'/sample['run_id']/'manifest.json').read_text());fingerprint=base['cases'][0]['fingerprints'][:5]
 name=f't2f_mc20_mid_{"a" if seed<=51010 else "b"}_20260921_01_s{seed}';p=ROOT/'runs'/name/'manifest.json'
 cases=json.loads(p.read_text())['cases'] if p.exists() else []
 for t in [-20,0,50,75]:
  found=[c for c in cases if c['temperature_C']==t];r={'seed':seed,'temperature_C':t,'run_id':name,'simulation_status':found[0]['status'] if found else 'not run','fingerprints_status':'not run','linear_status':'not run','candidate_status':'not run'}
  if found and found[0]['status']=='passed':
   c=found[0];fp=c['fingerprints'];valid=len(fp)==10 and fp[:5]==fp[5:]==fingerprint;r['fingerprints_status']='passed' if valid else 'failed'
   if valid:
    linear=25+(c['measurements']['freq']-float(sample['frequency25_Hz']))/float(sample['slope_Hz_C']);error=linear-t;candidate=correct(linear)-t
    r.update(frequency_Hz=c['measurements']['freq'],linear_residual_C=error,candidate_residual_C=candidate,linear_status='passed' if abs(error)<=2 else 'failed',candidate_status='passed' if abs(candidate)<=2 else 'failed')
  rows.append(r)
with (ROOT/'mc20_intermediate_points.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=sorted({k for r in rows for k in r}));writer.writeheader();writer.writerows(rows)
complete=[r for r in rows if 'linear_residual_C' in r]
summary={'expected_points':80,'completed_points':sum(r['simulation_status']=='passed' for r in rows),'failed_simulations':sum(r['simulation_status']=='failed' for r in rows),'not_run_points':sum(r['simulation_status']=='not run' for r in rows),'fingerprint_failures':sum(r['fingerprints_status']=='failed' for r in rows),'linear_failed_points':sum(r['linear_status']=='failed' for r in rows),'candidate_failed_points':sum(r['candidate_status']=='failed' for r in rows),'fixed_nominal_curve_source_sha256':frozen['nominal_curve_sha256'],'limits':'Same 20 samples, original25/100C calibration frozen. Candidate curve unchanged. Only typical process/nominal rails; new held-out samples and process/rail ensembles remain separate.'}
if complete:summary.update(maximum_linear_abs_residual_C=max(abs(r['linear_residual_C']) for r in complete),maximum_candidate_abs_residual_C=max(abs(r['candidate_residual_C']) for r in complete))
(ROOT/'mc20_intermediate_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
