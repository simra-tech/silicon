#!/usr/bin/env python3
"""All-code full-switch transfer from bounded OP leaves with frozen-sample checks."""
import argparse,json,subprocess,sys
from pathlib import Path
SIM=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True);p.add_argument('--seed',type=int,default=51001);p.add_argument('--temps',default='25');p.add_argument('--chunk-size',type=int,default=8);p.add_argument('--resume',action='store_true');a=p.parse_args();assert 1<=a.chunk_size<=16
out=SIM/'qualification'/a.run_id
if a.resume:assert out.is_dir()
else:
 out.mkdir(exist_ok=False);(out/'driver.py').write_text(Path(__file__).read_text());(out/'provenance.json').write_text(json.dumps({'arguments':sys.argv[1:],'scope':'Full actualBGR/SENSE reference buffer, both fullDAC switch trees with comparators heldreset. Each code set uses same device order and same seed;31observed parameters must match across every chunk/temp. Full256code DC transfer only; no dynamic settling claim.'},indent=2)+'\n')
summary={'seed':a.seed,'status':'not run to completion','leaves':[],'transfer':[]};fp=None;source=None;allrows=[]
def persist():(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for ti,temp in enumerate(map(float,a.temps.split(','))):
 for start in range(0,256,a.chunk_size):
  leaf=f'{a.run_id}-t{ti}-c{start:03d}';d=SIM/'qualification'/leaf
  cmd=[sys.executable,str(SIM/'run_dac_qualification.py'),'--run-id',leaf,'--image-id',a.image_id,'--seeds',str(a.seed),'--temps',str(temp),'--codes',','.join(map(str,range(start,min(256,start+a.chunk_size)))),'--hold-comparators-reset','--actual-bgr','--solver','klu']
  if a.resume and d.exists():
   previous=json.loads((d/'provenance.json').read_text());assert previous['arguments']==cmd[2:],'Changed cached arguments';assert (d/'summary.json').exists(),'Incomplete oldleaf requires explicit recovery';rc=0
  else:
   if (out/'PAUSE_REQUESTED').exists():summary['next_command']=cmd[2:];persist();sys.exit(0)
   rc=subprocess.run(cmd,cwd=SIM).returncode
  r=json.loads((d/'summary.json').read_text())[0] if (d/'summary.json').exists() else {'status':'failed','rows':[],'fingerprints':[]}
  provenance=json.loads((d/'provenance.json').read_text())
  identity={k:provenance[k] for k in ['source_hashes','model_hashes','image_id','pdk_commit','ngspice','solver']}
  if source is None:source=identity
  if fp is None and r['fingerprints']:fp=r['fingerprints'][0]
  valid=rc==0 and r['status']=='passed' and r.get('frozen_fingerprints') and r['fingerprints'][0]==fp and identity==source
  summary['leaves'].append({'run':leaf,'status':'passed' if valid else 'failed/incomplete','raw_status':r['status'],'wall_s':r.get('wall_s'),'valid_rows':len(r['rows']),'frozen_sample_exact':bool(r['fingerprints']) and r['fingerprints'][0]==fp,'source_model_engine_exact':identity==source})
  if not valid:summary['status']='failed/incomplete';persist();sys.exit(1)
  allrows.extend(r['rows']);persist()
 rows=sorted([r for r in allrows if r[1]==temp],key=lambda r:r[2]);assert len(rows)==256 and [r[2] for r in rows]==list(range(256))
 for col,name in [(3,'soft'),(4,'hard')]:
  v=[r[col] for r in rows];lsb=(v[-1]-v[0])/255;dnl=[(w-u)/lsb-1 for u,w in zip(v,v[1:])];inl=[(w-v[0])/lsb-i for i,w in enumerate(v)]
  summary['transfer'].append({'temperature_C':temp,'threshold':name,'minimum_step_V':min(w-u for u,w in zip(v,v[1:])),'min_DNL_LSB':min(dnl),'max_abs_endpoint_INL_LSB':max(map(abs,inl)),'endpoint_lsb_V':lsb,'monotonicity_status':'passed' if min(dnl)>-1 and lsb>0 else 'failed','INL_acceptance':'not applicable: no allocated standalone limit'})
summary.update(status='passed numerical/all-code completion',frozen_observed_parameters=fp,rows=allrows);persist()
