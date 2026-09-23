#!/usr/bin/env python3
"""Compact native evidence export, retaining each failed intermediate proof."""
import argparse,getpass,gzip,hashlib,io,json
from pathlib import Path

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bulk-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    here=Path(__file__).resolve().parent;root=here.parents[5]
    folders=['sense-comp45-native-inventory-20260923-r1']
    folders+=['sense-comp45-native-build-20260923-r'+str(n) for n in range(1,10)]
    folders+=['sense-comp45-native-reference-20260923-r'+str(n)+s for n in range(1,4) for s in ['', '-preparation']]
    folders+=['sense-comp45-native-stock-20260923-r'+str(n)+s for n in range(1,3) for s in ['', '-preparation']]
    a.output.mkdir(parents=True);rows=[];omitted=[]
    for folder in folders:
        sourcebase=a.bulk_root/folder;assert sourcebase.is_dir(),sourcebase
        for source in sorted(sourcebase.rglob('*')):
            if not source.is_file():continue
            assert not source.is_symlink()
            raw=source.read_bytes()
            if source.suffix=='.lvsdb' or (source.name=='g1_sense_physical.gds' and folder!='sense-comp45-native-build-20260923-r9'):
                omitted.append(dict(path=str(source.relative_to(a.bulk_root)),sha256=sha(raw),bytes=len(raw),reason='Intermediate full geometry or large database retained by original hash; snapshot/derived reference and reports exported'))
                continue
            portable=raw
            if source.suffix!='.gds':
                pairs=[(str(a.bulk_root).encode(),b'${RESULTS_ROOT}'),(b'/work/',b'${REPOSITORY_ROOT}/')]
                for old,new in pairs:portable=portable.replace(old,new)
                restored=portable
                for old,new in reversed(pairs):restored=restored.replace(new,old)
                assert restored==raw
            assert b'/home/' not in portable and getpass.getuser().encode() not in portable
            zipped=source.suffix in {'.json','.log','.lyrdb'};data=portable
            if zipped:
                memory=io.BytesIO()
                with gzip.GzipFile(fileobj=memory,mode='wb',filename='',mtime=0) as stream:stream.write(portable)
                data=memory.getvalue()
            target=a.output/folder/source.relative_to(sourcebase)
            if zipped:target=target.with_name(target.name+'.gz')
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(data)
            rows.append(dict(path=str(target.relative_to(a.output)),sha256=sha(data),bytes=len(data),original_sha256=sha(raw),decoded_portable_sha256=sha(portable),inverse_exact=True))
    (a.output/'artifact_manifest.json').write_text(json.dumps(dict(status='completed export; failed intermediate results retained',records=rows,omitted=omitted,no_new_checks=True),indent=2)+'\n')
    paths=sorted(q for q in a.output.rglob('*') if q.is_file())
    paths += [here/q for q in ['README.md','inspect_passive_sites.py','build_candidate.py','audit_candidate.py','run_stock.py','export_evidence.py']]
    records=[dict(path=str(q.resolve().relative_to(root)),sha256=sha(q.read_bytes()),bytes=q.stat().st_size) for q in paths]
    inventory=a.output/'commit_inventory.json'
    inventory.write_text(json.dumps(dict(status='frozen listed files only',files=records,total_bytes=sum(q['bytes'] for q in records),self_excluded=True),indent=2)+'\n')
    print(json.dumps(dict(files=len(records),bytes=sum(q['bytes'] for q in records),sha256=sha(inventory.read_bytes()))))

if __name__=='__main__':main()
