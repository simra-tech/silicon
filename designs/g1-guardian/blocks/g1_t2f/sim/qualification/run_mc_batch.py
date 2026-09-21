#!/usr/bin/env python3
"""Execute independent joint-PEX physical samples in separate bounded processes.
Each sample uses the same seed/device ordering across four temperatures, retaining
all failed or incomplete runs. OP/seed qualification must precede this campaign.
"""
import argparse,concurrent.futures,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def run_one(task):
 prefix,seed,image_id,temperatures,stop_file=task
 run_id=f'{prefix}_s{seed}'
 cmd=[sys.executable,str(HERE/'run_joint.py'),'--run-id',run_id,'--image-id',image_id,'--temperatures='+temperatures,'--mismatch','--seed',str(seed)]
 if stop_file: cmd += ['--stop-file',stop_file]
 path=HERE/'runs'/f'{run_id}_driver.log'; start=time.monotonic()
 with path.open('x') as log: p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 mpath=HERE/'runs'/run_id/'manifest.json'
 rows=json.loads(mpath.read_text())['cases'] if mpath.exists() else []
 return {'run_id':run_id,'seed':seed,'driver_exit':p.returncode,'wall_seconds':time.monotonic()-start,'attempted_temperatures':len(rows),'completed_temperatures':sum(r['status']=='passed' for r in rows),'failed_temperatures':sum(r['status']=='failed' for r in rows),'incomplete_temperatures':sum(r['status']=='not run' for r in rows)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prefix',required=True);ap.add_argument('--image-id',required=True);ap.add_argument('--first-seed',type=int,required=True);ap.add_argument('--samples',type=int,required=True);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--temperatures',default='-40,25,100,125');ap.add_argument('--batch-tag',default='');ap.add_argument('--stop-file',type=Path);a=ap.parse_args();assert not a.batch_tag or a.batch_tag.replace('_','').isalnum()
 assert 1<=a.workers<=4 and a.samples>0
 ledger=HERE/'runs'/f'{a.prefix}{"_"+a.batch_tag if a.batch_tag else ""}_batch.json';assert not ledger.exists()
 manifest={'command':sys.argv,'expected_seeds':list(range(a.first_seed,a.first_seed+a.samples)),'workers':a.workers,'temperatures':a.temperatures,'cases':[]}
 ledger.write_text(json.dumps(manifest,indent=2)+'\n')
 tasks=[(a.prefix,seed,a.image_id,a.temperatures,str(a.stop_file.resolve()) if a.stop_file else None) for seed in manifest['expected_seeds']]
 with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:
  pending={}; next_task=0
  while pending or next_task<len(tasks):
   stopping=bool(a.stop_file and a.stop_file.exists())
   while not stopping and len(pending)<a.workers and next_task<len(tasks):
    task=tasks[next_task];pending[pool.submit(run_one,task)]=task[1];next_task+=1
   if not pending: break
   done,_=concurrent.futures.wait(pending,return_when=concurrent.futures.FIRST_COMPLETED)
   for future in done:
    pending.pop(future);row=future.result();manifest['cases'].append(row);ledger.write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(row),flush=True)
  manifest['not_started_seeds']=[task[1] for task in tasks[next_task:]]
  manifest['campaign_status']='paused at requested leaf boundary' if a.stop_file and a.stop_file.exists() else 'finished'
  ledger.write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
