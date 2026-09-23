#!/usr/bin/env python3
"""Compact internal TRIP remedy evidence; original failures remain visible."""
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
    p.add_argument('--bulk-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.bulk_root=a.bulk_root.resolve();a.output=a.output.resolve()
    assert not a.output.exists()and HERE in a.output.parents
    groups=['trip-internal-screen-20260923-r'+str(i)for i in(1,2,3)]
    groups+=['trip-internal-'+kind+'-20260923-r'+str(i)for kind in('build','drc','lvs')for i in(2,3)]
    groups+=['trip-fill-inventory-20260923-r'+str(i)for i in(1,2)]
    groups+=['trip-internal-global-20260923-r3','trip-internal-cuts-20260923-r3']
    files=[];statuses=[]
    for name in groups:
        base=a.bulk_root/name
        q=base/('analysis.json'if(base/'analysis.json').exists()else'summary.json')
        status=json.loads(q.read_text())['status'];assert status!='running'
        statuses.append(dict(group=name,status=status))
        for path in sorted(base.rglob('*')):
            if not path.is_file():continue
            if path.suffix in('.json','.py','.log','.lyrdb','.cdl','.cir')or(path.suffix=='.gds'and path.name!='g1_trip.gds'):
                files.append((path,Path(name)/path.relative_to(base)))
    a.output.mkdir(parents=True);records=[]
    for source,relative in files:
        data=source.read_bytes();original=sha(data)
        if source.suffix!='.gds':
            text=data.decode()
            for old,new in((str(a.bulk_root),'${BULK}'),(str(REPO),'${REPO}'),('/work/','${REPO}/')):text=text.replace(old,new)
            assert getpass.getuser()not in text and '/home/'not in text and '/opt/sim/'not in text,relative
            data=text.encode()
        dest=a.output/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        records.append(dict(path=str(dest.relative_to(REPO)),original_sha256=original,exported_sha256=sha(data),
                            bytes=len(data),path_only_sanitized=sha(data)!=original))
    (a.output/'export_manifest.json').write_text(json.dumps(dict(status='passed compact internal-remedy export; no adoption',
        groups=statuses,artifacts=records,full_native_GDS_reexported=False,
        omitted='Full candidate GDS and binary LVS databases retained by hashes in original receipts; source, recipes, reference, strict comparisons, overlays and logs exported',
        transformation='Only bulk/workspace paths in textual evidence replaced; original hashes preserved'),indent=2)+'\n')
    helpers=['screen_trip_internal_access.py','build_trip_internal.py','check_trip_internal_lvs.py',
             'inspect_trip_fill_conflicts.py','export_trip_internal_global.py','prune_trip_fill.py',
             'audit_trip_internal_cuts.py','TRIP_INTERNAL_ACCESS_CONTRACT.md','export_trip_internal_evidence.py']
    paths=sorted([HERE/name for name in helpers]+[q for q in a.output.rglob('*')if q.is_file()])
    inventory=dict(status='frozen compact internal-remedy milestone; no adoption',files=[
        dict(path=str(q.relative_to(REPO)),sha256=sha(q.read_bytes()),bytes=q.stat().st_size)for q in paths])
    inventory.update(file_count=len(paths),total_bytes=sum(r['bytes']for r in inventory['files']))
    destination=a.output/'commit_inventory.json';destination.write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(dict(path=str(destination.relative_to(REPO)),sha256=sha(destination.read_bytes()),
                          file_count=len(paths),total_bytes=inventory['total_bytes']),indent=2))


if __name__=='__main__':main()
