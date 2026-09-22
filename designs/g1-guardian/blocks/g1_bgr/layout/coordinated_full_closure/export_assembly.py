#!/usr/bin/env python3
"""Completed assembly milestone export; original failures and hashes retained."""
import argparse,datetime,getpass,hashlib,json,os,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--resource-gate',type=Path,required=True);ap.add_argument('--inventory',type=Path,required=True);a=ap.parse_args()
 g=json.loads(a.resource_gate.read_text());stamp=datetime.datetime.strptime(g['utc'].replace('+00:00',''),'%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
 assert g['status']=='passed' and g['expected_growth_gib']>=.08 and 0<=(datetime.datetime.now(datetime.timezone.utc)-stamp).total_seconds()<1800
 bulk=Path(os.environ['G1_RESULTS_ROOT']);groups={}
 for revision in range(1,6):
  name='bgr-assembly-20260922-r'+str(revision);base=bulk/name
  assert json.loads((base/'run.json').read_text())['status'] in('passed','failed');groups['r'+str(revision)]=(base,[p for p in base.iterdir() if p.is_file()])
  if revision in(2,4,5):
   for kind in('drc','lvs'):
    stock=bulk/(name+'-'+kind);assert json.loads((stock/'summary.json').read_text())['status'] in('passed','failed')
    groups['r'+str(revision)+'/'+kind]=(stock,[p for p in stock.rglob('*') if p.is_file() and p.suffix in('.json','.py','.log','.cir','.lvsdb','.lyrdb')])
 rows=[];payload=[];total=0
 for group,(base,files) in groups.items():
  for p in sorted(files):
   raw=p.read_bytes();data=raw
   if p.suffix!='.gds':
    for old,new in[(str(ROOT),'<repository>'),(str(bulk),'<results-root>'),(str(Path.home()),'<home>')]:data=data.replace(old.encode(),new.encode())
   assert not re.search(rb'/home/|/opt/sim|\.private',data) and getpass.getuser().encode() not in data,str(p)
   if p.suffix=='.json':json.loads(data.decode())
   rel=group+'/'+str(p.relative_to(base));payload.append((rel,data));total+=len(data)
   rows.append(dict(source_run=base.name,source_relative=str(p.relative_to(base)),export=rel,original_sha256=sha(raw),export_sha256=sha(data),
                    original_bytes=len(raw),export_bytes=len(data),host_prefix_redacted=data!=raw))
 assert total<.08*2**30 and g['effective_storage_free_bytes']>total+8*2**30
 out=HERE/'evidence/20260922-r1';out.mkdir(parents=True,exist_ok=False)
 for rel,data in payload:
  p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);assert sha(p.read_bytes())==sha(data)
 manifest=dict(status='passed export/privacy/JSON gates',artifacts=rows,artifact_count=len(rows),artifact_bytes=total,original_artifacts_unchanged=True,
               redaction='Host path prefixes only; original and exported hashes both retained.',PEX_electrical_density_antenna='not run in this milestone',script_sha256=sha(Path(__file__).read_bytes()))
 (out/'export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 names=['build_assembly.py','run_geometry.py','run_stock.py','CONTRACT_20260922.md','RESULTS_20260922.md','audit_junctions.py','export_assembly.py']
 files=[HERE/n for n in names]+[p for p in out.rglob('*') if p.is_file()]
 inventory=dict(groups={'full1036_BGR_assembly':[dict(path=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size) for p in sorted(files)]})
 a.inventory.write_text(json.dumps(inventory,indent=2)+'\n');print(json.dumps(dict(status=manifest['status'],files=len(files),bytes=sum(p.stat().st_size for p in files)),indent=2))
if __name__=='__main__':main()
