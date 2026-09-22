#!/usr/bin/env python3
"""All-code full-switch transfer from bounded OP leaves with frozen-sample checks."""
import argparse,json,math,subprocess,sys
from pathlib import Path
from result_directory import allocate_run
SIM=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True);p.add_argument('--seed',type=int,default=51001);p.add_argument('--temps',default='25');p.add_argument('--chunk-size',type=int,default=8);p.add_argument('--resume',action='store_true');p.add_argument('--tight',action='store_true');p.add_argument('--workers',type=int,default=1);p.add_argument('--code-start',type=int,default=0);p.add_argument('--code-stop',type=int,default=256);a=p.parse_args();assert 1<=a.chunk_size<=16 and 1<=a.workers<=12
assert 0<=a.code_start<a.code_stop<=256 and a.code_stop-a.code_start>=2
out=SIM/'qualification'/a.run_id
if a.resume:assert out.is_dir()
else:
 out=allocate_run(SIM,a.run_id);(out/'driver.py').write_text(Path(__file__).read_text());(out/'provenance.json').write_text(json.dumps({'arguments':sys.argv[1:],'code_range_half_open':[a.code_start,a.code_stop],'scope':'Full actualBGR/SENSE reference buffer, both fullDAC switch trees with comparators heldreset. Each code set uses same device order and same seed;31observed parameters must match across every chunk/temp. Declared code-range DC transfer only; partial ranges do not establish all256code completion; no dynamic settling claim.'},indent=2)+'\n')
summary={'seed':a.seed,'code_range_half_open':[a.code_start,a.code_stop],'status':'not run to completion','leaves':[],'transfer':[],'return_temperature_checks':[]};fp=None;source=None;allrows=[];first_temperature_rows={}
def persist():(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
def leaf_command(ti,temp,start):
 leaf=f'{a.run_id}-t{ti}-c{start:03d}'
 command=[sys.executable,str(SIM/'run_dac_qualification.py'),'--run-id',leaf,'--image-id',a.image_id,'--seeds',str(a.seed),'--temps',str(temp),'--codes',','.join(map(str,range(start,min(a.code_stop,start+a.chunk_size)))),'--hold-comparators-reset','--actual-bgr','--solver','klu']
 if a.tight:command.append('--tight')
 return leaf,SIM/'qualification'/leaf,command
for ti,temp in enumerate(map(float,a.temps.split(','))):
 phase_rows=[];group_results={}
 for start in range(a.code_start,a.code_stop,a.chunk_size):
  leaf,d,cmd=leaf_command(ti,temp,start)
  if a.workers>1 and (start-a.code_start)%(a.chunk_size*a.workers)==0:
   # Each group contains at most the allocated worker count. All started leaves
   # finish before checking a stop/failure or launching another group.
   if (out/'PAUSE_REQUESTED').exists():summary['next_command']=cmd[2:];persist();sys.exit(0)
   active=[];group_results={}
   for code_start in range(start,min(a.code_stop,start+a.chunk_size*a.workers),a.chunk_size):
    _,directory,command=leaf_command(ti,temp,code_start)
    if a.resume and directory.exists():continue
    active.append((code_start,subprocess.Popen(command,cwd=SIM)))
   for code_start,process in active:group_results[code_start]=process.wait()
  if a.resume and d.exists():
   previous=json.loads((d/'provenance.json').read_text());assert previous['arguments']==cmd[2:],'Changed cached arguments';assert (d/'summary.json').exists(),'Incomplete oldleaf requires explicit recovery';rc=group_results.get(start,0)
  else:
   if a.workers==1:
    if (out/'PAUSE_REQUESTED').exists():summary['next_command']=cmd[2:];persist();sys.exit(0)
    rc=subprocess.run(cmd,cwd=SIM).returncode
   else:rc=group_results[start]
  r=json.loads((d/'summary.json').read_text())[0] if (d/'summary.json').exists() else {'status':'failed','rows':[],'fingerprints':[]}
  provenance=json.loads((d/'provenance.json').read_text())
  identity={k:provenance[k] for k in ['source_hashes','model_hashes','image_id','pdk_commit','ngspice','solver']}
  if source is None:source=identity
  if fp is None and r['fingerprints']:fp=r['fingerprints'][0]
  expected_codes=list(range(start,min(a.code_stop,start+a.chunk_size)))
  row_contract=(len(r['rows'])==len(expected_codes) and all(len(row)==8 and all(math.isfinite(x) for x in row) and row[0]==0 and row[1]==temp for row in r['rows']) and [row[2] for row in r['rows']]==expected_codes)
  valid=rc==0 and r['status']=='passed' and r.get('frozen_fingerprints') and r['fingerprints'][0]==fp and identity==source and row_contract
  summary['leaves'].append({'run':leaf,'status':'passed' if valid else 'failed/incomplete','raw_status':r['status'],'wall_s':r.get('wall_s'),'valid_rows':len(r['rows']),'row_contract_status':'passed' if row_contract else 'failed','frozen_sample_exact':bool(r['fingerprints']) and r['fingerprints'][0]==fp,'source_model_engine_exact':identity==source})
  if not valid:summary['status']='failed/incomplete';persist();sys.exit(1)
  # Each leaf contains local temperature index 0. Give aggregate rows their
  # campaign phase index so a repeated temperature cannot merge two sweeps.
  phase_rows.extend([[ti,*row[1:]] for row in r['rows']]);persist()
 rows=sorted(phase_rows,key=lambda r:r[2]);assert [r[2] for r in rows]==list(range(a.code_start,a.code_stop))
 allrows.extend(rows)
 if temp in first_temperature_rows:
  reference=first_temperature_rows[temp]
  exact=[row[1:] for row in rows]==[row[1:] for row in reference]
  summary['return_temperature_checks'].append({'temperature_C':temp,'temperature_index':ti,'reference_temperature_index':reference[0][0],'printed_rows_exact_status':'passed' if exact else 'failed','scope':'Saved printed values; precision inherited from ngspice echo, not full binary solution.'})
 else:first_temperature_rows[temp]=rows
 for col,name in [(3,'soft'),(4,'hard')]:
  v=[r[col] for r in rows];lsb=(v[-1]-v[0])/(len(rows)-1);dnl=[(w-u)/lsb-1 for u,w in zip(v,v[1:])] if lsb>0 else [];inl=[(w-v[0])/lsb-i for i,w in enumerate(v)] if lsb>0 else []
  summary['transfer'].append({'temperature_C':temp,'temperature_index':ti,'threshold':name,'minimum_step_V':min(w-u for u,w in zip(v,v[1:])),'min_DNL_LSB':min(dnl) if dnl else None,'max_abs_endpoint_INL_LSB':max(map(abs,inl)) if inl else None,'endpoint_lsb_V':lsb,'monotonicity_status':'passed' if dnl and min(dnl)>-1 else 'failed','INL_acceptance':'not applicable: no allocated standalone limit'})
summary.update(status='passed numerical/all-code completion' if (a.code_start,a.code_stop)==(0,256) else 'passed numerical/declared-code completion',monotonicity_status='passed' if all(x['monotonicity_status']=='passed' for x in summary['transfer']) else 'failed',return_temperature_status=('passed' if all(x['printed_rows_exact_status']=='passed' for x in summary['return_temperature_checks']) else 'failed') if summary['return_temperature_checks'] else 'not run',frozen_observed_parameters=fp,rows=allrows);persist()
