#!/usr/bin/env python3
"""One stock DRC or strict LVS for a completed source-bound MOS candidate."""
import argparse,collections,datetime,hashlib,json,os,re,subprocess,time
from pathlib import Path
import xml.etree.ElementTree as ET
import pya
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5];PDK=Path('/foss/pdks/ihp-sg13g2')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def strict(path):
 db=pya.LayoutVsSchematic();db.read(str(path));xr=db.xref();X=pya.NetlistCrossReference
 names={X.Match:'Match',X.MatchWithWarning:'MatchWithWarning',X.Mismatch:'Mismatch',X.NoMatch:'NoMatch',X.Skipped:'Skipped',X.None_:'None'}
 rows=[]
 for pair in xr.each_circuit_pair():
  row=dict(status=names[pair.status()],children={})
  for kind,method in [('device',xr.each_device_pair),('net',xr.each_net_pair),('pin',xr.each_pin_pair),('subcircuit',xr.each_subcircuit_pair)]:
   row['children'][kind]=dict(collections.Counter(names[p.status()] for p in method(pair)))
  rows.append(row)
 return dict(status='passed' if rows and all(r['status']=='Match' and all(set(c)<={'Match'} for c in r['children'].values()) for r in rows) else'failed',circuits=rows,sha256=sha(path))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--kind',choices=['drc','lvs'],required=True)
 ap.add_argument('--resource-gate',type=Path,required=True);a=ap.parse_args()
 assert re.fullmatch('bgr-mos-[a-z0-9-]+',a.candidate)
 assert len(os.sched_getaffinity(0))==1 and next(iter(os.sched_getaffinity(0))) in range(4)
 assert pya.__version__=='0.30.9' and(PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
 gate=json.loads(a.resource_gate.read_text());age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
 assert gate['status']=='passed' and 0<=age<1800 and gate['external_allocation']['expected_growth_gib']>=.5
 bulk=Path(os.environ['G1_RESULTS_ROOT']);base=bulk/a.candidate
 prep=json.loads((base/'preparation.json').read_text());assert prep['status']=='passed preparation'
 assert sha(base/'bank.gds')==prep['gds_sha256'] and sha(base/'bank.cdl')==prep['cdl_sha256']
 for p,h in prep['inputs'].items():assert sha(ROOT/p)==h
 inputs={str(p.relative_to(base)):sha(p) for p in base.iterdir() if p.is_file()}
 out=bulk/(a.candidate+'-'+a.kind);out.mkdir(exist_ok=False)
 (out/'run_stock.py').write_bytes(Path(__file__).read_bytes())
 rules={str(p.relative_to(PDK)):sha(p) for p in (PDK/'libs.tech/klayout/tech').rglob('*') if p.is_file() and p.suffix in('.drc','.lvs','.py','.rb','.json')}
 cmd=['python3',str(PDK/('libs.tech/klayout/tech/'+a.kind+'/run_'+a.kind+'.py')),'--run_mode=deep','--topcell=bgr_mos_bank','--run_dir='+str(out/'reports')]
 cmd+=['--path='+str(base/'bank.gds'),'--no_density','--mp=1'] if a.kind=='drc' else['--layout='+str(base/'bank.gds'),'--netlist='+str(base/'bank.cdl')]
 receipt=dict(status='running',candidate=a.candidate,kind=a.kind,command=cmd,source_inputs=prep['inputs'],candidate_inputs=inputs,
  stock_rule_hashes=rules,watchdog_s=180,resource_gate_sha256=sha(a.resource_gate),script_sha256=sha(Path(__file__)),
  started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),density_antenna_PEX_analog='not run',seed='not applicable')
 dump(out/'summary.json',receipt);start=time.monotonic()
 with(out/'stock.log').open('x') as log:r=subprocess.run(['timeout','--kill-after=5','180']+cmd,stdout=log,stderr=subprocess.STDOUT)
 ok=False
 try:
  if a.kind=='drc':
   reports=[]
   for p in(out/'reports').rglob('*.lyrdb'):
    cats=collections.Counter(x.findtext('category') for x in ET.parse(p).findall('.//items/item'))
    reports.append(dict(path=str(p.relative_to(out)),sha256=sha(p),markers=sum(cats.values()),categories=dict(cats)))
   receipt['reports']=reports;ok=bool(reports) and all(x['markers']==0 for x in reports)
  else:
   reports=[strict(p) for p in(out/'reports').rglob('*.lvsdb')];receipt['strict_lvs']=reports
   logs='\n'.join(p.read_text(errors='replace') for p in(out/'reports').rglob('*.log'))
   receipt['explicit_match']='Congratulations! Netlists match.' in logs and "Netlists don't match" not in logs
   ok=bool(reports) and all(x['status']=='passed' for x in reports) and receipt['explicit_match']
 except Exception as e:receipt['parse_error']=str(e)
 unchanged=all(sha(base/p)==h for p,h in inputs.items()) and all(sha(ROOT/p)==h for p,h in prep['inputs'].items()) and all(sha(PDK/p)==h for p,h in rules.items())
 growth=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
 receipt.update(status='passed' if ok and r.returncode==0 and unchanged and growth<.5*2**30 else'failed',returncode=r.returncode,
  wall_s=time.monotonic()-start,inputs_rules_unchanged=unchanged,output_bytes=growth,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 dump(out/'summary.json',receipt);print(json.dumps({k:v for k,v in receipt.items() if k not in ('source_inputs','candidate_inputs','stock_rule_hashes')},indent=2))
 return 0 if receipt['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
