#!/usr/bin/env python3
"""Bounded independent physical samples for one fixed process/calibration policy."""
import argparse,concurrent.futures,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def one(task):
 prefix,seed,image,corner,stop=task;run=f'{prefix}_s{seed}';cmd=[sys.executable,str(HERE/'run_adverse_calibration.py'),'--run-id',run,'--image-id',image,'--corner',corner,'--first-seed',str(seed),'--samples','1']
 if stop:cmd+=['--stop-file',stop]
 start=time.monotonic()
 with (HERE/'runs'/f'{run}_driver.log').open('x') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
 p=HERE/'runs'/run/'manifest.json';m=json.loads(p.read_text()) if p.exists() else {'cases':[]};samples=m['cases'];s=samples[0] if samples else {};points=s.get('independent_points',[])
 return {'seed':seed,'run_id':run,'driver_exit':rc,'wall_seconds':time.monotonic()-start,'sample_status':s.get('status','not run'),'attempted_transients':sum(len(c['cases']) for c in s.get('children',[])),'completed_transients':sum(p['status']=='passed' for c in s.get('children',[]) for p in c['cases']),'independent_points':len(points),'calibration_failures':{method:sum(p[method+'_status']=='failed' for p in points) for method in ['linear','nominal_lut','reciprocal']}}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prefix',required=True);ap.add_argument('--image-id',required=True);ap.add_argument('--corner',choices=['nominal','slow','fast'],required=True);ap.add_argument('--first-seed',type=int,required=True);ap.add_argument('--samples',type=int,required=True);ap.add_argument('--workers',type=int,default=3);ap.add_argument('--stop-file',type=Path);a=ap.parse_args();assert 1<=a.workers<=4 and a.samples>0;p=HERE/'runs'/f'{a.prefix}_batch.json';assert not p.exists();seeds=list(range(a.first_seed,a.first_seed+a.samples));m={'command':sys.argv,'expected_seeds':seeds,'corner':a.corner,'cases':[]};save=lambda:p.write_text(json.dumps(m,indent=2)+'\n');save();tasks=[(a.prefix,s,a.image_id,a.corner,str(a.stop_file.resolve()) if a.stop_file else None) for s in seeds]
 with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:
  pending={};n=0
  while pending or n<len(tasks):
   stopping=bool(a.stop_file and a.stop_file.exists())
   while not stopping and len(pending)<a.workers and n<len(tasks):t=tasks[n];pending[pool.submit(one,t)]=t[1];n+=1
   if not pending:break
   done,_=concurrent.futures.wait(pending,return_when=concurrent.futures.FIRST_COMPLETED)
   for f in done:pending.pop(f);r=f.result();m['cases'].append(r);save();print(json.dumps(r),flush=True)
  m['not_started_seeds']=seeds[n:];m['campaign_status']='paused at requested leaf boundary' if a.stop_file and a.stop_file.exists() else 'finished';save()
if __name__=='__main__':main()
