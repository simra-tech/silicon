#!/usr/bin/env python3
"""Copy completed r2 evidence exactly; no simulation or geometry modification."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    target=HERE/'evidence/r2';target.mkdir(parents=True,exist_ok=False)
    base=ROOT/'build/scratch/bgr-hbt-worstrows-20260922-r2'
    pairs=[(base/n,'preparation/'+n) for n in ['pilot.gds','pilot.cdl','preparation.json','subset.json','route_ledger.json','terminal_graph.json','neighbor_obstructions.json','revision_audit.json','run.json']]
    for kind in ['drc','lvs']:
        folder=ROOT/('build/scratch/bgr-hbt-worstrows-stock-20260922-r2-'+kind)
        result=json.loads((folder/'summary.json').read_text());assert result['status'] in ['passed','failed']
        pairs.extend([(folder/'summary.json',kind+'/summary.json'),(folder/'stock.log',kind+'/stock.log')])
        ext='*.lyrdb' if kind=='drc' else '*.lvsdb'
        pairs.extend((p,kind+'/'+p.name) for p in sorted((folder/'reports').rglob(ext)))
    manifest=[]
    for source,name in pairs:
        out=target/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(source.read_bytes())
        assert sha(source)==sha(out)
        manifest.append(dict(source=str(source.relative_to(ROOT)),export=name,sha256=sha(out),bytes=out.stat().st_size))
    result=dict(status='passed exact evidence copy',files=manifest,export_script_sha256=sha(Path(__file__)),
                original_evidence_retained=True,transformation='none')
    (target/'export_manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

