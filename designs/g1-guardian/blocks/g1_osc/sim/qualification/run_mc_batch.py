#!/usr/bin/env python3
"""Independent OSC physical samples, at most four bounded single-thread workers.
Qualification must be established separately for selected runtime/model tuple.
"""
import argparse,concurrent.futures,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def one(task):
 prefix,seed,image,codes,corner,scale,stop=task;run_id=f'{prefix}_s{seed}';cmd=[sys.executable,str(HERE/'run_mc.py'),'--run-id',run_id,'--suite','screen','--image-id',image,'--first-seed',str(seed),'--samples','1','--codes',codes,'--tuple',corner,'--r-charge-scale',str(scale)]
 if stop:cmd+=['--stop-file',stop]
 start=time.monotonic()
 with (HERE/'runs'/f'{run_id}_driver.log').open('x') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
 p=HERE/'runs'/run_id/'manifest.json';d=json.loads(p.read_text()) if p.exists() else {'cases':[]};r=d['cases']
 return {'seed':seed,'run_id':run_id,'driver_exit':rc,'wall_seconds':time.monotonic()-start,'attempted_codes':len(r),'completed_codes':sum(x['status']=='passed' for x in r),'failed_codes':sum(x['status']=='failed' for x in r),'timeouts':sum(x['timed_out'] for x in r)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prefix',required=True);ap.add_argument('--image-id',required=True);ap.add_argument('--first-seed',type=int,required=True);ap.add_argument('--samples',type=int,required=True);ap.add_argument('--workers',type=int,default=3);ap.add_argument('--codes',default=','.join(map(str,range(16))));ap.add_argument('--tuple',choices=['nominal','slowhot'],default='nominal');ap.add_argument('--r-charge-scale',type=float,default=1);ap.add_argument('--stop-file',type=Path);a=ap.parse_args();assert 1<=a.workers<=4 and a.samples>0
 p=HERE/'runs'/f'{a.prefix}_batch.json';assert not p.exists();seeds=list(range(a.first_seed,a.first_seed+a.samples));m={'command':sys.argv,'expected_seeds':seeds,'codes':a.codes,'cases':[]};save=lambda:p.write_text(json.dumps(m,indent=2)+'\n');save();tasks=[(a.prefix,s,a.image_id,a.codes,a.tuple,a.r_charge_scale,str(a.stop_file.resolve()) if a.stop_file else None) for s in seeds]
 with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:
  pending={};n=0
  while pending or n<len(tasks):
   stopping=bool(a.stop_file and a.stop_file.exists())
   while not stopping and len(pending)<a.workers and n<len(tasks):task=tasks[n];pending[pool.submit(one,task)]=task[1];n+=1
   if not pending:break
   done,_=concurrent.futures.wait(pending,return_when=concurrent.futures.FIRST_COMPLETED)
   for f in done:pending.pop(f);r=f.result();m['cases'].append(r);save();print(json.dumps(r),flush=True)
  m['not_started_seeds']=seeds[n:];m['campaign_status']='paused at requested leaf boundary' if a.stop_file and a.stop_file.exists() else 'finished';save()
if __name__=='__main__':main()
