#!/usr/bin/env python3
"""Bounded external-output geometry run; unique IDs preserve every failure."""
import argparse,datetime,hashlib,json,os,re,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--subset',choices=['nmos30','full'],required=True)
 p.add_argument('--resource-gate',type=Path,required=True);p.add_argument('--cpu',type=int,default=0);a=p.parse_args()
 assert re.fullmatch('bgr-mos-[a-z0-9-]+',a.run_id) and 0<=a.cpu<=3
 gate=json.loads(a.resource_gate.read_text());stamp=datetime.datetime.strptime(gate['utc'].replace('+00:00',''),'%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
 assert gate['status']=='passed' and 0<=(datetime.datetime.now(datetime.timezone.utc)-stamp).total_seconds()<1800
 assert gate['external_allocation']['expected_growth_gib']>=.5 and gate['project_cpu_budget']>=4
 bulk=Path(os.environ['G1_RESULTS_ROOT']).resolve();assert bulk.is_dir() and str(bulk)==gate['external_allocation']['root']
 out=bulk/a.run_id;out.mkdir(exist_ok=False)
 bindings={p:sha(p) for p in [HERE/'build_mos_bank.py',HERE/'CONTRACT_20260922.md',Path(__file__).resolve(),ROOT/'flow/run.sh']}
 for f in bindings:(out/f.name).write_bytes(f.read_bytes())
 command=['flow/run.sh','timeout','--kill-after=5','180','python3',str((HERE/'build_mos_bank.py').relative_to(ROOT)),
          '--output',str(out),'--subset',a.subset]
 env=dict(os.environ,G1_CPUS='1',G1_CPUSET=str(a.cpu),G1_MEMORY='4g')
 receipt=dict(status='running',command=command,resource_gate_sha256=sha(a.resource_gate),cpu=a.cpu,watchdog_s=180,
             sources={str(p.relative_to(ROOT)):h for p,h in bindings.items()},started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 dump(out/'run.json',receipt);start=time.monotonic()
 with(out/'run.log').open('x') as log:r=subprocess.run(command,cwd=str(ROOT),env=env,stdout=log,stderr=subprocess.STDOUT)
 receipt.update(status='passed' if r.returncode==0 else'failed',returncode=r.returncode,wall_s=time.monotonic()-start,
  finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources_unchanged=all(sha(p)==h for p,h in bindings.items()),
  output_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
 if receipt['output_bytes']>.5*2**30 or not receipt['sources_unchanged']:receipt['status']='failed output/input gate'
 dump(out/'run.json',receipt);print(json.dumps(receipt,indent=2));return 0 if receipt['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
