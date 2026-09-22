#!/usr/bin/env python3
"""Bounded PEX-view/native parity and unsimplified installed-deck LVS export."""
import argparse,collections,datetime,hashlib,json,os,re,subprocess,time
from pathlib import Path
import pya
from run_stock import strict
from audit_unsimplified import audit
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
SUPPORT=Path('/usr/local/lib/python3.12/dist-packages/klayout_pex/pdk/ihp-sg13g2')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--run-id',required=True);ap.add_argument('--resource-gate',type=Path,required=True);a=ap.parse_args()
 assert re.fullmatch('bgr-pex-[a-z0-9-]+',a.run_id) and re.fullmatch('bgr-assembly-[a-z0-9-]+',a.candidate)
 assert len(os.sched_getaffinity(0))==1 and next(iter(os.sched_getaffinity(0))) in range(4) and pya.__version__=='0.30.9'
 gate=json.loads(a.resource_gate.read_text());age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
 assert gate['status']=='passed' and 0<=age<1800 and gate['external_allocation']['expected_growth_gib']>=2
 bulk=Path(os.environ['G1_RESULTS_ROOT']);assert str(bulk)==gate['external_allocation']['root'];base=bulk/a.candidate
 prep=json.loads((base/'preparation.json').read_text());assert prep['status']=='passed preparation'
 for kind in('drc','lvs'):assert json.loads((bulk/(a.candidate+'-'+kind)/'summary.json').read_text())['status']=='passed'
 junction=bulk/(a.candidate+'-lvs')/'junction_audit_r1.json';assert json.loads(junction.read_text())['status']=='passed'
 assert sha(base/'bank.gds')==prep['gds_sha256'] and sha(base/'bank.cdl')==prep['cdl_sha256']
 out=bulk/a.run_id;out.mkdir(exist_ok=False)
 wrapper=ROOT/'flow/pex/export_lvsdb.lvs'
 files=[base/'bank.gds',base/'bank.cdl',base/'preparation.json',wrapper,HERE/'prepare_pex_view.py',Path(__file__),HERE/'run_stock.py',HERE/'PEX_CONTRACT_20260922.md',HERE/'audit_unsimplified.py']
 files+=[bulk/(a.candidate+'-'+k)/'summary.json' for k in('drc','lvs')]
 files.append(junction)
 inputs={str(p):sha(p) for p in files};support={str(p.relative_to(SUPPORT)):sha(p) for p in SUPPORT.rglob('*') if p.is_file()}
 for p in files[3:9]:(out/p.name).write_bytes(p.read_bytes())
 version=subprocess.check_output(['kpex','--version'],text=True).strip();assert '0.3.12' in version
 receipt=dict(status='running',candidate=a.candidate,inputs=inputs,support_hashes=support,kpex_version=version,klayout_version=pya.__version__,
  resource_gate_sha256=sha(a.resource_gate),steps=[],started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),capacitance_electrical='not run',seed='not applicable')
 dump(out/'summary.json',receipt);start=time.monotonic()
 def step(name,cmd,limit):
  t=time.monotonic()
  with(out/(name+'.log')).open('x') as log:r=subprocess.run(['timeout','--kill-after=5',str(limit)]+cmd,stdout=log,stderr=subprocess.STDOUT)
  receipt['steps'].append(dict(name=name,command=cmd,watchdog_s=limit,returncode=r.returncode,wall_s=time.monotonic()-t));dump(out/'summary.json',receipt)
  assert r.returncode==0,(name,r.returncode)
 try:
  step('flatten',['python3',str(HERE/'prepare_pex_view.py'),'--input',str(base/'bank.gds'),'--output',str(out/'flat.gds'),'--report',str(out/'flat_parity.json')],60)
  assert json.loads((out/'flat_parity.json').read_text())['status']=='passed'
  cmd=['klayout','-b','-r',str(wrapper)]
  for arg in ['input='+str(out/'flat.gds'),'topcell=g1_bgr','schematic='+str(base/'bank.cdl'),'report='+str(out/'extraction.lvsdb'),
              'export_netlist='+str(out/'extracted.cir'),'target_netlist='+str(out/'stock_written.cir'),'log='+str(out/'extraction_detail.log'),
              'thr=1','run_mode=deep','no_simplify=true','combine_devices=false','purge=false','purge_nets=false','top_lvl_pins=true',
              'no_series_res=true','no_parallel_res=true']:cmd+=['-rd',arg]
  step('export_lvs',cmd,180)
  logs=(out/'export_lvs.log').read_text();assert 'Congratulations! Netlists match.' in logs and "Netlists don't match" not in logs
  receipt['strict_lvs']=strict(out/'extraction.lvsdb');assert receipt['strict_lvs']['status']=='passed'
  db=pya.LayoutVsSchematic();db.read(str(out/'extraction.lvsdb'));circuits=list(db.netlist().each_circuit());assert len(circuits)==1
  counts=collections.Counter(d.device_class().name for d in circuits[0].each_device());receipt['uncombined_device_classes']=dict(counts)
  assert sum(v for k,v in counts.items() if 'mos' in k)==336 and counts['npn13G2']==301 and counts['rppd']+counts['rhigh']==399 and sum(counts.values())==1036,counts
  receipt['source_node_parameter_audit']=audit(out/'extraction.lvsdb',out/'source_device_audit.json')['status'];assert receipt['source_node_parameter_audit']=='passed'
  receipt['extracted_net_count']=sum(1 for _ in circuits[0].each_net());receipt['flat_sha256']=sha(out/'flat.gds');receipt['database_sha256']=sha(out/'extraction.lvsdb');receipt['extracted_cir_sha256']=sha(out/'extracted.cir')
  receipt['status']='passed extraction preparation'
 except Exception as e:receipt.update(status='failed',error=repr(e))
 unchanged=all(sha(Path(p))==h for p,h in inputs.items()) and all(sha(SUPPORT/p)==h for p,h in support.items());size=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
 receipt.update(inputs_support_unchanged=unchanged,output_bytes=size,wall_s=time.monotonic()-start,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 if not unchanged or size>2*2**30:receipt['status']='failed final input/output gate'
 dump(out/'summary.json',receipt);print(json.dumps({k:v for k,v in receipt.items() if k not in('inputs','support_hashes')},indent=2));return 0 if receipt['status']=='passed extraction preparation' else 1
if __name__=='__main__':raise SystemExit(main())
