#!/usr/bin/env python3
"""Export completed MOS evidence, preserving originals and disclosing redaction."""
import argparse,datetime,getpass,hashlib,json,os,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
def digest(data):return hashlib.sha256(data).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--resource-gate',type=Path,required=True);ap.add_argument('--inventory',type=Path,required=True);a=ap.parse_args()
 gate=json.loads(a.resource_gate.read_text());stamp=datetime.datetime.strptime(gate['utc'].replace('+00:00',''),'%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
 assert gate['status']=='passed' and gate['expected_growth_gib']>=.03 and 0<=(datetime.datetime.now(datetime.timezone.utc)-stamp).total_seconds()<1800
 bulk=Path(os.environ['G1_RESULTS_ROOT']).resolve();groups={}
 for tag,run in [('nmos30/r1','bgr-mos-nmos30-20260922-r1'),('nmos30/r2','bgr-mos-nmos30-20260922-r2'),('full336/r1','bgr-mos-full-20260922-r1'),('full336/r2','bgr-mos-full-20260922-r2')]:
  base=bulk/run;receipt=json.loads((base/'run.json').read_text());assert receipt['status'] in ('passed','failed')
  groups[tag]=(base,[p for p in base.iterdir() if p.is_file()])
  if tag!='full336/r1':
   for k in ('drc','lvs'):
    stock=bulk/(run+'-'+k);assert json.loads((stock/'summary.json').read_text())['status'] in('passed','failed')
    groups[tag+'/'+k]=(stock,[p for p in stock.rglob('*') if p.is_file() and p.suffix in('.json','.log','.lyrdb','.lvsdb','.cir','.py')])
 rows=[];payload=[];total=0
 substitutions=[(str(ROOT).encode(),b'<repository>'),(str(bulk).encode(),b'<results-root>'),(str(Path.home()).encode(),b'<home>')]
 for group,(base,files) in groups.items():
  for p in sorted(files):
   raw=p.read_bytes();data=raw
   if p.suffix!='.gds':
    for old,new in substitutions:data=data.replace(old,new)
   assert not re.search(rb'/home/|/opt/sim|\.private',data) and getpass.getuser().encode() not in data,str(p)
   if p.suffix=='.json':json.loads(data.decode())
   rel=group+'/'+str(p.relative_to(base));payload.append((rel,data));total+=len(data)
   rows.append(dict(source_run=base.name,source_relative=str(p.relative_to(base)),export=rel,
                    original_sha256=digest(raw),export_sha256=digest(data),original_bytes=len(raw),export_bytes=len(data),host_prefix_redacted=data!=raw))
 assert total<.03*2**30 and gate['effective_storage_free_bytes']>total+8*2**30
 out=HERE/'evidence/20260922-r1';out.mkdir(parents=True,exist_ok=False)
 for rel,data in payload:
  p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);assert digest(p.read_bytes())==digest(data)
 manifest=dict(status='passed export/privacy/JSON gates',artifacts=rows,artifact_count=len(rows),artifact_bytes=total,
               original_artifacts_unchanged=True,redaction='Only repository, external-results and home path prefixes; no numerical/check content changed.',
               full_BGR_PEX_electrical='not run in this isolated-bank export',script_sha256=digest(Path(__file__).read_bytes()))
 (out/'export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 public=[p for p in HERE.iterdir() if p.is_file()]+[p for p in out.rglob('*') if p.is_file()]
 inventory=dict(groups={'mos336_stock_milestone':[dict(path=str(p.relative_to(ROOT)),sha256=digest(p.read_bytes()),bytes=p.stat().st_size) for p in sorted(public)]})
 a.inventory.write_text(json.dumps(inventory,indent=2)+'\n');print(json.dumps(dict(status=manifest['status'],files=len(public),bytes=sum(p.stat().st_size for p in public)),indent=2))
if __name__=='__main__':main()
