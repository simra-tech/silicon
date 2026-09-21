#!/usr/bin/env python3
"""Bounded simulator qualification on preserved G1 block fixtures.

Run inside the EDA container with repository mounted at /work. This reports
solver/data completion, not circuit-specification acceptance.
"""
import argparse, datetime, hashlib, json, math, os, platform, re, shutil, subprocess, sys, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BLOCKS=ROOT/'designs/g1-guardian/blocks'
sys.path.insert(0,str(BLOCKS/'g1_top/sim'))
from run_bounded import run_bounded,atomic_json
FIXTURES={
 't2f_mc_25':('g1_t2f/sim/qualification/runs/t2f_mc_s51001_20260921_01/ptat_T25.cir',32e-6),
 't2f_mc_cold':('g1_t2f/sim/qualification/runs/t2f_mc_s51001_20260921_01/ptat_T-40.cir',32e-6),
 'bgr_noise':('g1_bgr/sim/qualification/runs/bgr_noise_20260921_01/noise.cir',None),
 'bgr_mc':('g1_bgr/sim/qualification/runs/bgr_mc20_20260921_01/mc_42001.cir',125),
 'sense_noise':('g1_sense/sim/qualification/noise-20260921-b/noise_tt_3.3V_27C.cir',1e7),
 'osc':('g1_osc/sim/qualification/runs/osc_trim80_shard0_20260921_01/tt_typ_typ_1.2_27_c8.cir',6e-6),
 'gate_io_first':('g1_gate/sim/campaigns/20260921T140450Z_b8966582/io_first.cir',16e-6),
 'gate_core_first':('g1_gate/sim/campaigns/20260921T140450Z_b8966582/core_first.cir',16e-6),
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--simulator',default='ngspice');ap.add_argument('--image-id',required=True);ap.add_argument('--label',required=True);ap.add_argument('--timeout',type=float,default=300);ap.add_argument('cases',nargs='*',default=list(FIXTURES));a=ap.parse_args()
 if not re.fullmatch('[A-Za-z0-9_-]+',a.label) or any(c not in FIXTURES for c in a.cases):ap.error('invalid label/case')
 out=ROOT/'designs/g1-guardian/review/runtime'/ (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+a.label+'_'+uuid.uuid4().hex[:8]);out.mkdir(parents=True,exist_ok=False)
 exe=Path(shutil.which(a.simulator) or a.simulator)
 pdk=Path('/foss/pdks/ihp-sg13g2')
 md=dict(options=vars(a),architecture=platform.machine(),image_id=a.image_id,simulator_sha256=sha(exe),version=subprocess.check_output([str(exe),'-v'],text=True),pdk_commit=(pdk/'COMMIT').read_text().strip(),model_hashes={str(p.relative_to(pdk)):sha(p) for directory in ['libs.tech/ngspice','libs.tech/verilog-a'] for p in sorted((pdk/directory).rglob('*')) if p.is_file()},runner_sha256=sha(Path(__file__)))
 md['bounded_runner_sha256']=sha(BLOCKS/'g1_top/sim/run_bounded.py')
 results=[];atomic_json(out/'campaign.json',dict(md,status='running',cases=results))
 for case in a.cases:
  rel,endpoint=FIXTURES[case];source=BLOCKS/rel;base=next(p for p in source.parents if (p/'.spiceinit').exists());dest=out/case;dest.mkdir();shutil.copyfile(base/'.spiceinit',dest/'.spiceinit')
  deck=source.read_text();inputs={str(source.relative_to(ROOT)):sha(source)}
  def include(m):
   raw=m[2].strip('"\'');p=Path(raw)
   if not p.is_absolute():
    p=next((x/raw for x in [source.parent,base] if (x/raw).exists()),None)
    if p is None:raise FileNotFoundError(raw)
   inputs[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)]=sha(p)
   return m[1]+str(p)
  deck=re.sub(r'(?im)^(\.include\s+)(\S+)',include,deck)
  outputs=[]
  def wr(m):
   name=Path(m[1]).name;outputs.append(name);return 'wrdata '+str(dest/name)+m[2]
  deck=re.sub(r'(?im)^wrdata\s+(\S+)([^\n]*)',wr,deck)
  deck=deck.replace('.control','.control\nset num_threads=1',1)
  dp=dest/'fixture.cir';dp.write_text(deck)
  with (dest/'run.log').open('x') as log:r=run_bounded([str(exe),'-b',str(dp)],log,dest/'run.json',a.timeout,cwd=dest,metadata=dict(case=case,input_hashes=inputs,deck_sha256=sha(dp),image_id=a.image_id),interval_s=5)
  r['data_completion']='failed';r['metrics']={}
  try:
   log=(dest/'run.log').read_text()
   if r['status']!='completed' or re.search(r'Timestep too small|simulation aborted|doAnalyses:|^Error:',log,re.I|re.M):raise ValueError('solver not complete or error')
   for name in outputs:
    p=dest/name;lines=p.read_text().splitlines();rows=[]
    for line in lines:
     try:row=[float(x) for x in line.split()]
     except ValueError:continue
     if row:rows.append(row)
    if len(rows)<2 or any(len(row)!=len(rows[0]) or not all(map(math.isfinite,row)) for row in rows):raise ValueError('invalid data '+name)
    if endpoint is not None and abs(rows[-1][0]-endpoint)>max(1e-12,abs(endpoint)*1e-10):raise ValueError('wrong endpoint '+name)
    r['metrics'][name]=dict(rows=len(rows),columns=len(rows[0]),start=rows[0][0],end=rows[-1][0],minimum=[min(row[i] for row in rows) for i in range(len(rows[0]))],maximum=[max(row[i] for row in rows) for i in range(len(rows[0]))],last=rows[-1],sha256=sha(p))
   if not outputs:raise ValueError('no saved data')
   r['data_completion']='passed'
  except (ValueError,OSError) as e:r['data_error']=str(e)
  atomic_json(dest/'run.json',r);results.append({k:r.get(k) for k in ['case','status','wall_s','returncode','data_completion','data_error','metrics']});atomic_json(out/'campaign.json',dict(md,status='running',cases=results));print(case,r['status'],r['data_completion'],r['wall_s'],flush=True)
 atomic_json(out/'campaign.json',dict(md,status='completed',cases=results));print(out.relative_to(ROOT),flush=True)
 if any(r['data_completion']!='passed' for r in results):raise SystemExit(1)
if __name__=='__main__':main()
