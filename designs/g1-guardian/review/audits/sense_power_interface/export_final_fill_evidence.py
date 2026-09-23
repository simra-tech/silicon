#!/usr/bin/env python3
"""Export explicit completed fill/check groups without re-exporting full native GDS."""
import argparse
import getpass
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[4]


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bulk-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--group',action='append',required=True)
    a=p.parse_args();a.bulk_root=a.bulk_root.resolve();a.output=a.output.resolve()
    assert not a.output.exists()and HERE in a.output.parents
    assert len(a.group)==len(set(a.group))
    files=[];statuses=[]
    for name in a.group:
        assert Path(name).name==name
        base=a.bulk_root/name
        meta=base/('analysis.json'if(base/'analysis.json').exists()else'summary.json')
        status=json.loads(meta.read_text())['status'];assert not status.startswith('running')
        statuses.append(dict(group=name,status=status,original_metadata_sha256=sha(meta.read_bytes())))
        for source in sorted(base.rglob('*')):
            if not source.is_file():continue
            if source.name in('filled_native.gds','sealed_native.gds'):continue
            if source.suffix in('.json','.py','.log','.lyrdb','.gds'):
                files.append((source,Path(name)/source.relative_to(base)))
    a.output.mkdir(parents=True);records=[]
    for source,relative in files:
        raw=source.read_bytes();data=raw
        if source.suffix!='.gds':
            text=raw.decode()
            for old,new in((str(a.bulk_root),'${BULK}'),(str(REPO),'${REPO}'),('/work/','${REPO}/')):
                text=text.replace(old,new)
            assert getpass.getuser()not in text and '/home/'not in text and '/opt/sim/'not in text,relative
            data=text.encode()
        dest=a.output/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        records.append(dict(path=str(dest.relative_to(REPO)),bytes=len(data),
            original_sha256=sha(raw),exported_sha256=sha(data),path_only_sanitized=data!=raw))
    (a.output/'export_manifest.json').write_text(json.dumps(dict(
        status='passed completed fill/check evidence export; no adoption',groups=statuses,artifacts=records,
        full_native_GDS_reexported=False,
        omitted='Full native GDS remains bound by source hashes; exact additive filler overlays and generation/check scripts retained',
        transformation='Only bulk/workspace paths in textual evidence replaced; original artifact hashes retained'),indent=2)+'\n')
    helpers=[HERE/name for name in('audit_filled_source_delta.py','export_final_fill_evidence.py','FINAL_FILL_REVIEW_20260923.md')]
    paths=sorted(helpers+[q for q in a.output.rglob('*')if q.is_file()])
    manifest=dict(status='frozen completed fill/check milestone; absolute failures retained',files=[
        dict(path=str(q.relative_to(REPO)),sha256=sha(q.read_bytes()),bytes=q.stat().st_size)for q in paths])
    manifest.update(file_count=len(paths),total_bytes=sum(r['bytes']for r in manifest['files']))
    destination=a.output/'commit_inventory.json';destination.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(path=str(destination.relative_to(REPO)),sha256=sha(destination.read_bytes()),
        file_count=len(paths),total_bytes=manifest['total_bytes']),indent=2))


if __name__=='__main__':main()
