#!/usr/bin/env python3
"""Evaluate the frozen physical two-point model; never fit independent outcomes."""
import argparse,csv,hashlib,json
from pathlib import Path
from reciprocal_calibration import fit_calibration,infer_temperature
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--samples',type=int,default=100);args=parser.parse_args();assert args.samples in [100,300]
stem='reciprocal_candidate' if args.samples==100 else 'reciprocal_candidate300'
frozen=json.loads((HERE/'reciprocal_candidate_frozen.json').read_text())
assert hashlib.sha256((HERE/'reciprocal_calibration.py').read_bytes()).hexdigest()==frozen['equation_source_sha256']
rows=[];samples=[]
def evaluate(group,seed,f25,f100,points):
 a,b=fit_calibration(f25,f100);out=[]
 for temp,freq,source in points:
  row={'group':group,'seed':seed,'temperature_C':temp,'frequency_Hz':freq,'source_run':source,'calibration_a_K_s':a,'calibration_b_s':b,'role':'calibration' if temp in [25,100] else 'independent'}
  try:
   inferred=infer_temperature(freq,a,b);error=inferred-temp;row.update(inferred_temperature_C=inferred,residual_C=error,status='passed' if abs(error)<=2 else 'failed')
  except ValueError:row['status']='failed';row['failure_reason']='nonphysical model denominator'
  rows.append(row);out.append(row)
 independent=[r for r in out if r['role']=='independent'];samples.append({'group':group,'seed':seed,'independent_points':len(independent),'failed_points':sum(r['status']=='failed' for r in independent),'maximum_abs_residual_C':max((abs(r['residual_C']) for r in independent if 'residual_C' in r),default=None)})
nominal=list(csv.DictReader((HERE/'nominal_calibration.csv').open()));nom={float(r['temperature_C']):float(r['frequency_Hz']) for r in nominal}
points=[(t,f,'nominal_calibration.csv') for t,f in nom.items()]
probe='t2f_interpolation_probe_20260921_01';pm=HERE/'runs'/probe/'manifest.json'
if pm.exists():points.extend((c['temperature_C'],c['measurements']['freq'],probe) for c in json.loads(pm.read_text())['cases'] if c['status']=='passed')
evaluate('nominal_and_between_knots',0,nom[25],nom[100],points)
for row in csv.DictReader((HERE/f'mc{args.samples}_samples.csv').open()):
 if row['calibration_status']=='not run':continue
 seed=int(row['seed']);m=json.loads((HERE/'runs'/row['run_id']/'manifest.json').read_text());f={c['temperature_C']:c['measurements']['freq'] for c in m['cases']};points=[(t,x,row['run_id']) for t,x in f.items()]
 if seed<=51020:
  mid=f't2f_mc20_mid_{"a" if seed<=51010 else "b"}_20260921_01_s{seed}';path=HERE/'runs'/mid/'manifest.json'
  if path.exists():points.extend((c['temperature_C'],c['measurements']['freq'],mid) for c in json.loads(path.read_text())['cases'] if c['status']=='passed')
 evaluate('smoke20_eight_temperatures' if seed<=51020 else 'expanded_endpoint_samples' if seed<=51100 else 'prospective_extension_endpoint_samples',seed,f[25],f[100],points)
groups={}
for group in sorted({r['group'] for r in rows}):
 ss=[s for s in samples if s['group']==group];rr=[r for r in rows if r['group']==group and r['role']=='independent'];groups[group]={'samples':len(ss),'independent_points':len(rr),'failed_samples':sum(s['failed_points']>0 for s in ss),'failed_points':sum(r['status']=='failed' for r in rr),'maximum_abs_residual_C':max((abs(r['residual_C']) for r in rr if 'residual_C' in r),default=None)}
for name,data in [(stem+'_points.csv',rows),(stem+'_samples.csv',samples)]:
 with (HERE/name).open('w') as f:
  writer=csv.DictWriter(f,lineterminator="\n",fieldnames=sorted({k for r in data for k in r}));writer.writeheader();writer.writerows(data)
summary={'equation_freeze':frozen,'groups':groups,'status':'unadopted physical-model candidate; original linear and nominal-LUT results unchanged','selection_context':'Physical model chosen after reviewing linear-error/reference-drift diagnostics. Equation frozen before expanded reciprocal errors were computed; expanded cohort is not represented as a wholly blind model-selection holdout.','limitations':'No ensemble regression or additional calibration point. Typical-process nominal-rail samples only; supply policy, process extremes, nonlinear PDK effects and packaged calibration require independent validation. No clamping of inferred temperature.'}
(HERE/(stem+'.json')).write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
