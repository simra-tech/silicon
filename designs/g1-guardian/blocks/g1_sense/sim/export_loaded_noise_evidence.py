#!/usr/bin/env python3
"""Export one compact noise milestone; path-only reversible normalization."""
import argparse
import getpass
import gzip
import hashlib
import io
import json
from pathlib import Path

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bulk-root',type=Path,required=True)
    p.add_argument('--receipt-root',type=Path,required=True)
    p.add_argument('--existing-audit',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--inventory-only',action='store_true')
    a=p.parse_args()
    if a.inventory_only:
        root=Path(__file__).resolve().parents[5]
        sim=Path(__file__).resolve().parent
        paths=sorted(f for f in a.output.rglob('*') if f.is_file())
        paths += [sim/n for n in ['run_loaded_noise_audit.py','audit_existing_noise.py','export_loaded_noise_evidence.py']]
        paths += [sim.parent/'reports/LOADED_NOISE_20260923.md']
        destination=a.output/'commit_inventory.json'; assert not destination.exists()
        rows=[dict(path=str(f.resolve().relative_to(root)),sha256=sha(f.read_bytes()),bytes=f.stat().st_size) for f in paths]
        destination.write_text(json.dumps(dict(status='frozen exact listed files only',files=rows,
            total_bytes=sum(r['bytes'] for r in rows),self_excluded=True),indent=2)+'\n')
        print(json.dumps(dict(files=len(rows),sha256=sha(destination.read_bytes()),bytes=sum(r['bytes'] for r in rows))))
        return
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    records=[]
    def add(src,rel):
        raw=src.read_bytes(); cooked=raw.replace(str(a.bulk_root).encode(),b'${RESULTS_ROOT}').replace(b'/work/',b'${REPOSITORY_ROOT}/')
        assert cooked.replace(b'${REPOSITORY_ROOT}/',b'/work/').replace(b'${RESULTS_ROOT}',str(a.bulk_root).encode())==raw
        assert getpass.getuser().encode() not in cooked and b'/home/' not in cooked
        target=a.output/rel; target.parent.mkdir(parents=True,exist_ok=True)
        payload=cooked
        if str(target).endswith('.gz'):
            memory=io.BytesIO()
            with gzip.GzipFile(fileobj=memory,mode='wb',filename='',mtime=0) as stream:
                stream.write(cooked)
            payload=memory.getvalue()
        target.write_bytes(payload)
        records.append(dict(path=str(target.relative_to(a.output)),sha256=sha(payload),bytes=len(payload),
            original_sha256=sha(raw),decoded_portable_sha256=sha(cooked),path_normalization_applied=raw!=cooked,inverse_exact=True))
    for revision in [1,2,3]:
        src=a.bulk_root/('sense-loaded-noise-20260923-r%d'%revision)
        names=['contract.json','runner.py','noise.cir']
        if revision>1:names+=['summary.json','provenance.json','run.log']
        if revision==2:names+=['ac.dat']
        if revision==3:names+=['ac.dat','noise.dat']
        for name in names:
            add(src/name,Path('r%d'%revision)/(name+('.gz' if name in ['run.log','noise.cir'] else '')))
        receipt=a.receipt_root/('sense_loaded_noise_20260923_r%d'%revision)
        add(receipt/'tool.log',Path('r%d'%revision)/'bounded_tool.log.gz')
    add(a.existing_audit,Path('existing_ideal_noise_audit.json'))
    result=dict(status='passed compact export, source evidence statuses unchanged',records=records,
        normalization='Only configured results root and fixed /work/ prefix replaced with portable tokens; exact inverse asserted per file. Log/deck gzip uses mtime0.',
        no_simulation=True)
    (a.output/'artifact_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],files=len(records),bytes=sum(r['bytes'] for r in records))))

if __name__=='__main__':main()
