#!/usr/bin/env python3
"""Fresh-gated bounded full-BGR geometry execution with immutable receipts."""
import argparse,datetime,hashlib,json,os,re,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--resource-gate',type=Path,required=True);ap.add_argument('--cpu',type=int,default=0);a=ap.parse_args()
 assert re.fullmatch('bgr-assembly-[a-z0-9-]+',a.run_id) and a.cpu in range(4)
 g=json.loads(a.resource_gate.read_text());stamp=datetime.datetime.strptime(g['utc'].replace('+00:00',''),'%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
 assert g['status']=='passed' and 0<=(datetime.datetime.now(datetime.timezone.utc)-stamp).total_seconds()<1800
 assert g['project_cpu_budget']>=4 and g['external_allocation']['expected_growth_gib']>=2
 bulk=Path(os.environ['G1_RESULTS_ROOT']).resolve();assert str(bulk)==g['external_allocation']['root'];out=bulk/a.run_id;out.mkdir(exist_ok=False)
 files=[HERE/'build_assembly.py',HERE/'CONTRACT_20260922.md',Path(__file__).resolve(),ROOT/'flow/run.sh'];bindings={p:sha(p) for p in files}
 for p in files:(out/p.name).write_bytes(p.read_bytes())
 cmd=['flow/run.sh','timeout','--kill-after=5','300','python3',str((HERE/'build_assembly.py').relative_to(ROOT)),'--output',str(out)]
 receipt=dict(status='running',command=cmd,cpu=a.cpu,watchdog_s=300,resource_gate_sha256=sha(a.resource_gate),sources={str(p.relative_to(ROOT)):h for p,h in bindings.items()},started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 dump(out/'run.json',receipt);start=time.monotonic()
 with(out/'run.log').open('x') as f:r=subprocess.run(cmd,cwd=str(ROOT),env=dict(os.environ,G1_CPUS='1',G1_CPUSET=str(a.cpu),G1_MEMORY='4g'),stdout=f,stderr=subprocess.STDOUT)
 unchanged=all(sha(p)==h for p,h in bindings.items());size=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
 receipt.update(status='passed' if r.returncode==0 and unchanged and size<2*2**30 else'failed',returncode=r.returncode,wall_s=time.monotonic()-start,source_bindings_unchanged=unchanged,output_bytes=size,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 dump(out/'run.json',receipt);print(json.dumps(receipt,indent=2));return 0 if receipt['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
