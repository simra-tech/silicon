#!/usr/bin/env python3
"""Export bounded supply-feed evidence, preserving failures and original hashes."""
import argparse
import getpass
import gzip
import hashlib
import io
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[4]


def sha(data):return hashlib.sha256(data).hexdigest()


def groups():
    names=[]
    for macro,date,revision in [('bgr','20260922','r1'),('osc','20260922','r1'),('t2f','20260922','r1'),
                               ('gate','20260923','r1'),('dut','20260923','r1'),('dose','20260923','r1'),('ls','20260923','r2')]:
        for kind in('build','checks','core-drc'):
            rev='r3'if macro=='bgr'and kind=='build'else revision
            names.append(macro+'-power-interface-'+kind+'-'+date+'-'+rev)
    for name in('bgr-power-interface-build-20260922-r1','bgr-power-interface-build-20260922-r2',
                 'ls-power-interface-build-20260923-r1','ls-corridor-inventory-20260923-r1',
                 'bgr-power-interface-context-20260922-r1','osc-power-interface-context-20260922-r1',
                 't2f-power-interface-context-20260922-r1','t2f-power-interface-context-20260922-r2',
                 't2f-power-interface-context-20260923-r3','gate-power-interface-context-20260923-r1',
                 'remaining-power-inventory-20260922-r1','remaining-power-inventory-20260922-r2',
                 'remaining-power-inventory-20260923-r3','pad-metal-controls-20260923-r1',
                 'pad-metal-full-20260923-r1','pad-cut-replay-20260923-r1'):
        names.append(name)
    names.extend('shared-vdda-screen-20260923-r'+str(i)for i in range(1,7))
    names.extend('shared-vdda-'+kind+'-20260923-r1'for kind in('build','checks'))
    names.extend('shared-vdda-native-'+kind+'-20260923-r'+str(i)for kind in('baseline','candidate')for i in(1,2))
    for prefix,revision in [('west-supply','r2'),('trip-supply','r2'),('t2f-vdda','r1')]:
        names.extend(prefix+'-'+kind+'-20260923-'+revision for kind in('screen','build','checks','core-drc'))
    names.extend(['west-supply-screen-20260923-r1','trip-supply-screen-20260923-r1'])
    assert len(names)==len(set(names))
    return names


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bulk-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.bulk_root=a.bulk_root.resolve();a.output=a.output.resolve()
    assert not a.output.exists()and HERE in a.output.parents
    planned=[];statuses=[]
    for name in groups():
        base=a.bulk_root/name;assert base.is_dir(),name
        q=base/('analysis.json'if(base/'analysis.json').exists()else'summary.json')
        status=json.loads(q.read_text())['status']
        # Preserve the two original 240-second child-watchdog failures.
        original_watchdog=name in('shared-vdda-native-baseline-20260923-r1','shared-vdda-native-candidate-20260923-r1')
        assert status!='running',(name,status)
        if original_watchdog:assert json.loads(q.read_text())['decks'][0]['returncode']==124
        statuses.append(dict(group=name,original_status=status,
                             terminal_classification='failed original 240-second child watchdog'if original_watchdog else status))
        for path in sorted(base.rglob('*')):
            if not path.is_file():continue
            keep=path.suffix in('.json','.py','.log','.lyrdb')or path.name in('power_overlay.gds','raw_network.json.gz')
            if keep:planned.append((path,Path(name)/path.relative_to(base)))
    a.output.mkdir(parents=True);records=[]
    for source,relative in planned:
        data=source.read_bytes();original=sha(data);compressed=source.suffix=='.gz'
        if source.suffix!='.gds':
            text=(gzip.decompress(data)if compressed else data).decode()
            for old,new in((str(a.bulk_root),'${BULK}'),(str(REPO),'${REPO}'),('/work/','${REPO}/')):
                text=text.replace(old,new)
            assert getpass.getuser()not in text,relative
            assert '/home/'not in text and '/opt/sim/'not in text,relative
            data=text.encode()
            if compressed:
                buffer=io.BytesIO()
                with gzip.GzipFile(filename='',mode='wb',fileobj=buffer,mtime=0)as stream:stream.write(data)
                data=buffer.getvalue()
        dest=a.output/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        records.append(dict(path=str(dest.relative_to(REPO)),original_sha256=original,
                            exported_sha256=sha(data),bytes=len(data),path_only_sanitized=sha(data)!=original))
    report=dict(status='passed portable evidence export; independent limited-scope checks, no adoption',
                groups=statuses,artifacts=records,full_native_GDS_reexported=False,
                transformation='Textual runtime paths only; gzip decoded/scanned/recompressed deterministically; original hashes preserved')
    (a.output/'export_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    # This exporter does not freeze unfinished internal TRIP implementation.
    exclusions={'screen_trip_internal_access.py','build_trip_internal.py','check_trip_internal_lvs.py','export_trip_internal_global.py','TRIP_INTERNAL_ACCESS_CONTRACT.md'}
    paths=sorted(q for q in list(HERE.glob('*.py'))+list(HERE.glob('*.md'))+list(a.output.rglob('*'))
                 if q.is_file()and q.name not in exclusions and q.name!='commit_inventory.json')
    inventory=dict(status='frozen remaining-feed evidence; no adoption',
                   files=[dict(path=str(q.relative_to(REPO)),sha256=sha(q.read_bytes()),bytes=q.stat().st_size)for q in paths])
    inventory.update(file_count=len(paths),total_bytes=sum(r['bytes']for r in inventory['files']))
    destination=a.output/'commit_inventory.json';destination.write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(dict(path=str(destination.relative_to(REPO)),sha256=sha(destination.read_bytes()),
                          file_count=len(paths),total_bytes=inventory['total_bytes']),indent=2))


if __name__=='__main__':main()
