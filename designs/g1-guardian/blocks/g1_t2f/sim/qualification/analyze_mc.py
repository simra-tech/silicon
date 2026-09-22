#!/usr/bin/env python3
"""Retain every attempted sample; frozen per-sample25/100C calibration at endpoints."""
import argparse,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--samples',type=int,default=20);parser.add_argument('--run-aliases',type=Path);args=parser.parse_args();assert args.samples in [20,100,300]
runs={51001:'t2f_mc_s51001_20260921_01',51002:'t2f_mc_s51002_20260921_01',**{seed:f't2f_mc20_20260921_01_s{seed}' for seed in range(51003,51021)}}
runs.update({seed:f't2f_mc100_20260921_01_s{seed}' for seed in range(51021,51001+min(args.samples,100))})
runs.update({seed:f't2f_mc300_20260921_01_s{seed}' for seed in range(51101,51001+args.samples)})
if args.run_aliases:
 aliases=json.loads(args.run_aliases.read_text())
 for seed,name in aliases['run_ids'].items():
  seed=int(seed);assert seed in runs;assert '/' not in name and '..' not in name;runs[seed]=name
rows=[]
for seed,name in runs.items():
 p=ROOT/'runs'/name/'manifest.json';manifest=json.loads(p.read_text()) if p.exists() else {};cases=manifest.get('cases',[])
 r={'seed':seed,'run_id':name,'image_id':manifest.get('image_id','not run'),'attempted_temperatures':len(cases),'completed_temperatures':sum(c['status']=='passed' for c in cases),'failed_temperatures':sum(c['status']=='failed' for c in cases),'not_completed_temperatures':4-sum(c['status']=='passed' for c in cases),'calibration_status':'not run','fingerprints_status':'not run'}
 if len(cases)==4 and all(c['status']=='passed' for c in cases):
  fps=[c['fingerprints'] for c in cases];qualified=all(len(fp)==10 and fp[:5]==fp[5:]==fps[0][:5] for fp in fps);r['fingerprints_status']='passed' if qualified else 'failed'
  if qualified:
   f={c['temperature_C']:c['measurements']['freq'] for c in cases};assert set(f)=={-40,25,100,125}
   slope=(f[100]-f[25])/75;err={t:25+(f[t]-f[25])/slope-t for t in [-40,125]};worst=max(map(abs,err.values()))
   r.update(slope_Hz_C=slope,frequency25_Hz=f[25],cold_residual_C=err[-40],hot_residual_C=err[125],maximum_abs_residual_C=worst,calibration_status='passed' if worst<=2 else 'failed',hbt_vce_max_V=max(c['t2f_hbt_vce_max_V'] for c in cases))
 rows.append(r)
q=ROOT/'runs/t2f_mc_s51001_20260921_01/ptat_T25.dat';repeat=ROOT/'runs/t2f_mc_repeat_s51001_20260921_01/ptat_T25.dat'
assert q.read_bytes()==repeat.read_bytes()
summary={'expected_samples':args.samples,'attempted_samples':sum(r['attempted_temperatures']>0 for r in rows),'completed_samples':sum(r['completed_temperatures']==4 for r in rows),'expected_transients':args.samples*4,'attempted_transients':sum(r['attempted_temperatures'] for r in rows),'completed_transients':sum(r['completed_temperatures'] for r in rows),'failed_transients':sum(r['failed_temperatures'] for r in rows),'not_completed_transients':sum(r['not_completed_temperatures'] for r in rows),'calibration_passed_samples':sum(r['calibration_status']=='passed' for r in rows),'calibration_failed_samples':sum(r['calibration_status']=='failed' for r in rows),'calibration_not_run_samples':sum(r['calibration_status']=='not run' for r in rows),'fingerprint_failed_samples':sum(r['fingerprints_status']=='failed' for r in rows),'repeat_vectors_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'criteria':'Frozen25/100C per-sample calibration, endpoint residual<=2C at-40/125C','limitations':'Typical process and3.3/1.2V endpoint ensemble; refer to separate intermediate-temperature results. Higher counts and rail/process ensembles require separate runs.'}
summary['completed_samples_by_image']={image:sum(r['image_id']==image and r['completed_temperatures']==4 for r in rows) for image in sorted({r['image_id'] for r in rows if r['image_id']!='not run'})}
complete=[r for r in rows if 'maximum_abs_residual_C' in r]
if complete:summary['worst_sample']=max(complete,key=lambda r:r['maximum_abs_residual_C'])
(ROOT/f'mc{args.samples}_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
with (ROOT/f'mc{args.samples}_samples.csv').open('w') as f:
 writer=csv.DictWriter(f,lineterminator="\n",fieldnames=sorted({k for row in rows for k in row}));writer.writeheader();writer.writerows(rows)
print(json.dumps(summary,indent=2))
