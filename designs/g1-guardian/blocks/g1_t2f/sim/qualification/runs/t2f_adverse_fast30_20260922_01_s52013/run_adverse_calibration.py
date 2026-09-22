#!/usr/bin/env python3
"""One fixed process population; fixed nominal-rail25/100C calibration per sample.
Pilot/OP qualification precedes expansion. Separate output IDs never overwrite.
"""
import argparse,bisect,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
from reciprocal_calibration import fit_calibration,infer_temperature
HERE=Path(__file__).resolve().parent
def nominal_lut(value):
 curve=json.loads((HERE/'fixed_nominal_curve.json').read_text())['curve_pairs_linear_reading_C_actual_temperature_C'];i=max(0,min(len(curve)-2,bisect.bisect_right([p[0] for p in curve],value)-1));(x0,y0),(x1,y1)=curve[i:i+2];return y0+(value-x0)*(y1-y0)/(x1-x0)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--image-id',required=True);ap.add_argument('--corner',choices=['nominal','slow','fast'],required=True);ap.add_argument('--first-seed',type=int,default=51901);ap.add_argument('--samples',type=int,default=1);ap.add_argument('--op-only',action='store_true');ap.add_argument('--stop-file',type=Path);a=ap.parse_args()
 h,m,r,c={'nominal':('typ','tt','typ','typ'),'slow':('wcs','ss','wcs','wcs'),'fast':('bcs','ff','bcs','bcs')}[a.corner]
 out=HERE/'runs'/a.run_id;out.mkdir(parents=True,exist_ok=False);shutil.copy(__file__,out/'run_adverse_calibration.py');shutil.copy(HERE/'adverse_calibration_protocol.json',out/'protocol.json')
 frozen=json.loads((HERE/'reciprocal_candidate_frozen.json').read_text());assert hashlib.sha256((HERE/'reciprocal_calibration.py').read_bytes()).hexdigest()==frozen['equation_source_sha256']
 ledger={'command':sys.argv,'corner':a.corner,'expected_seeds':list(range(a.first_seed,a.first_seed+a.samples)),'calibration':'Same physical corner/seed,25/100C at3.3/1.2V; unchanged coefficients atlow/highrails and−40/125C','op_only':a.op_only,'cases':[]};save=lambda:(out/'manifest.json').write_text(json.dumps(ledger,indent=2)+'\n');save()
 for seed in ledger['expected_seeds']:
  if a.stop_file and a.stop_file.exists():ledger['campaign_status']='paused before next sample';save();break
  sample={'seed':seed,'children':[],'status':'not run'};ledger['cases'].append(sample);save()
  for label,v,v12,temps in [('cal',3.3,1.2,'25,100'),('low',3.0,1.08,'-40,125'),('high',3.6,1.32,'-40,125')]:
   if a.stop_file and a.stop_file.exists():sample['status']='not run to completion';save();break
   name=f'{a.run_id}_s{seed}_{label}';cmd=[sys.executable,str(HERE/'run_joint_adverse.py'),'--run-id',name,'--image-id',a.image_id,'--hbt',h,'--mos',m,'--res',r,'--cap',c,'--vdd',str(v),'--vdd12',str(v12),'--temperatures='+temps,'--mismatch','--seed',str(seed)]
   if a.op_only:cmd+=['--op-only']
   if a.stop_file:cmd+=['--stop-file',str(a.stop_file.resolve())]
   start=time.monotonic()
   with (out/(name+'_driver.log')).open('x') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
   path=HERE/'runs'/name/'manifest.json';data=json.loads(path.read_text()) if path.exists() else {};sample['children'].append({'label':label,'run_id':name,'driver_exit':rc,'wall_seconds':time.monotonic()-start,'cases':data.get('cases',[]),'fingerprint_parameters':data.get('fingerprint_parameters'),'model_sha256':data.get('models_sha256'),'netlist_sha256':data.get('realized_netlist_sha256')});save()
  children=sample['children'];points=[p for ch in children for p in ch['cases']]
  if len(points)==6 and all(p['status']=='passed' for p in points):
   nfp=len(children[0]['fingerprint_parameters']);fp0=points[0]['fingerprints'][:nfp];expected=nfp*(1 if a.op_only else 2)
   frozen_ok=all(len(p['fingerprints'])==expected and p['fingerprints'][:nfp]==fp0 and (a.op_only or p['fingerprints'][nfp:]==fp0) for p in points)
   hashes_ok=all(ch['model_sha256']==children[0]['model_sha256'] and ch['netlist_sha256']==children[0]['netlist_sha256'] for ch in children)
   sample.update(status='passed' if frozen_ok and hashes_ok else 'failed',frozen_parameter_status='passed' if frozen_ok else 'failed',consistent_source_model_hashes=hashes_ok)
   if sample['status']=='passed' and not a.op_only:
    cal={p['temperature_C']:p['measurements']['freq'] for p in children[0]['cases']}
    try:aa,bb=fit_calibration(cal[25],cal[100])
    except ValueError as exc:sample.update(status='failed',calibration_failure=str(exc));save();continue
    slope=(cal[100]-cal[25])/75;sample['independent_points']=[]
    for ch in children[1:]:
     for p in ch['cases']:
      freq=p['measurements']['freq'];temp=p['temperature_C'];lin=25+(freq-cal[25])/slope
      try:rec=infer_temperature(freq,aa,bb)
      except ValueError:rec=None
      sample['independent_points'].append({'label':ch['label'],'temperature_C':temp,'frequency_Hz':freq,'linear_error_C':lin-temp,'nominal_lut_error_C':nominal_lut(lin)-temp,'reciprocal_error_C':rec-temp if rec is not None else None,'nominal_lut_status':'passed' if abs(nominal_lut(lin)-temp)<=2 else 'failed','linear_status':'passed' if abs(lin-temp)<=2 else 'failed','reciprocal_status':'passed' if rec is not None and abs(rec-temp)<=2 else 'failed'})
  save();print(json.dumps({k:v for k,v in sample.items() if k!='children'}),flush=True)
if __name__=='__main__':main()
