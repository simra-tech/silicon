#!/usr/bin/env python3
"""Portable compact SENSE interface evidence; no full native GDS duplication."""
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
    a=p.parse_args();a.output=a.output.resolve();a.bulk_root=a.bulk_root.resolve()
    assert not a.output.exists() and HERE in a.output.parents
    a.output.mkdir(parents=True)
    records=[]
    groups={
        'screen-20260922-r1':['analysis.json','source.py'],
        'build-20260922-r1':['analysis.json','source.py','power_overlay.gds'],
        'coupon-20260922-r1':['summary.json','source.py','stock.log'],
        'coupon-20260922-r2':['summary.json','source.py','stock.log','reports/*.lyrdb'],
        'pad-20260922-r1':['analysis.json','source.py'],
        'parent-main-20260922-r1':['summary.json','source.py','main.log','reports/*.lyrdb'],
        'candidate-main-20260922-r1':['summary.json','source.py','main.log','reports/*.lyrdb'],
        'graph-20260922-r1':['analysis.json','source.py'],
        'signal-overlay-20260922-r1':['analysis.json','source.py'],
    }
    def copy(path,relative):
        data=path.read_bytes();original=sha(data)
        if path.suffix!='.gds':
            text=data.decode()
            for old,new in ((str(a.bulk_root.resolve()),'${BULK}'),(str(REPO),'${REPO}'),('/work/','${REPO}/')):
                text=text.replace(old,new)
            assert getpass.getuser() not in text
            assert '/home/' not in text and '/opt/sim/' not in text
            data=text.encode()
        destination=a.output/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(data)
        records.append(dict(path=str(destination.relative_to(REPO)),original_sha256=original,
                            exported_sha256=sha(data),bytes=len(data),path_only_sanitized=sha(data)!=original))
    for suffix,patterns in groups.items():
        root=a.bulk_root/('sense-power-interface-'+suffix)
        for pattern in patterns:
            paths=sorted(root.glob(pattern));assert paths,(root,pattern)
            for path in paths:copy(path,Path(suffix)/path.relative_to(root))
    copy(a.bulk_root/'sense-power-interface-marker-comparison-20260922-r1.json',Path('marker-comparison.json'))
    (a.output/'export_manifest.json').write_text(json.dumps(dict(
        status='passed compact portable evidence export; no adoption',artifacts=records,
        transformation='Only bulk/workspace path strings in textual files replaced; original hashes retained; GDS unchanged',
        full_native_GDS_reexported=False),indent=2)+'\n')
    paths=sorted(q for q in list(HERE.glob('*'))+list(a.output.rglob('*'))
                 if q.is_file() and q.suffix in ('.py','.md','.json','.log','.gds','.lyrdb'))
    inventory=dict(status='frozen commit-ready candidate evidence; no adoption',
                   files=[dict(path=str(q.relative_to(REPO)),sha256=sha(q.read_bytes()),bytes=q.stat().st_size)for q in paths])
    assert all(getpass.getuser() not in row['path']for row in inventory['files'])
    inventory['file_count']=len(paths);inventory['total_bytes']=sum(r['bytes']for r in inventory['files'])
    manifest=a.output/'commit_inventory.json';manifest.write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(dict(path=str(manifest.relative_to(REPO)),sha256=sha(manifest.read_bytes()),
                          file_count=len(paths),total_bytes=inventory['total_bytes']),indent=2))


if __name__=='__main__':main()
