#!/usr/bin/env python3
"""Compact completed diagnostic checkpoint; never modifies Git or raw evidence."""
import argparse
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'flow/run.sh').is_file())


def sha(b):return hashlib.sha256(b).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--gate',type=Path,required=True)
    ap.add_argument('--inventory',type=Path,required=True);a=ap.parse_args()
    gate=json.loads(a.gate.read_text());assert gate['status']=='passed'
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert 0<=age<1800 and len(os.sched_getaffinity(0))==1 and not a.inventory.exists()
    bulk=Path(os.environ['G1_RESULTS_ROOT']);out=HERE/'checkpoint-evidence-20260923-r1'
    assert not out.exists()
    folders=['analog-pair-reference-20260923-r1','sense-r100-full-reference-20260923-r1',
        'trip-hard-full-reference-20260923-r1','analog-pair-native-lvs-20260923-r1',
        'analog-pair-mapping-profile-20260923-r1','analog-pair-overlay-flat-20260923-r1',
        'analog-pair-flat-context-20260923-r1','analog-pair-flat-native-lvs-20260923-r1',
        'analog-pair-flat-dummy-proof-20260923-r2','analog-pair-prepurge-capture-20260923-r1',
        'analog-pair-prepurge-capture-stop-20260923-r1','analog-pair-prepurge-capture-stop-20260923-r2',
        'analog-pair-prepurge-audit-20260923-r1','analog-pair-prepurge-identity-20260923-r1',
        'analog-pair-prepurge-audit-20260923-r2','analog-pair-prepurge-audit-20260923-r3',
        'analog-pair-met2-purge-20260923-r1','analog-pair-all-purge-20260923-r1']
    folders+=['l2n-capture-control-20260923-r'+str(i) for i in range(1,5)]
    replacements=[(str(bulk).encode(),b'<results-root>'),(str(ROOT).encode(),b'<repository>'),
        (b'/work/',b'<repository>/'),(b'.'+b'private/',b'<private>/')]
    forbidden=[b'/'+b'home/',b'/opt/'+b'sim/',b'.'+b'private/']
    payload=[];rows=[];omitted=[]
    for folder in folders:
        d=bulk/folder;assert d.is_dir(),d
        for p in sorted(d.rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts:continue
            rel=folder+'/'+str(p.relative_to(d));raw=p.read_bytes()
            if p.suffix not in ('.json','.log','.txt','.py','.rb','.lvs','.cdl','.cir') or p.name in ('resources.json','resources.log'):
                omitted.append(dict(path=rel,bytes=len(raw),sha256=sha(raw),reason='Retained raw artifact outside compact checkpoint'))
                continue
            portable=raw
            for old,new in replacements:portable=portable.replace(old,new)
            assert all(x not in portable for x in forbidden),p
            if p.suffix=='.json':json.loads(portable)
            compressed=len(portable)>32768
            data=gzip.compress(portable,mtime=0) if compressed else portable
            target=rel+('.gz' if compressed else '')
            rows.append(dict(path=target,original_sha256=sha(raw),original_bytes=len(raw),
                portable_decoded_sha256=sha(portable),export_sha256=sha(data),export_bytes=len(data),
                host_prefix_redacted=portable!=raw,gzip=compressed))
            payload.append((target,data))
    total=sum(len(data) for _,data in payload)
    assert total<20*2**20 and total<gate['expected_growth_gib']*2**30
    assert gate['effective_storage_free_bytes']>total+8*2**30
    out.mkdir()
    for name,data in payload:
        p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    manifest=dict(status='passed compact export hash/privacy/JSON checks',artifacts=rows,omitted=omitted,
        scope='Completed source and purge diagnostics only; no native full-chip LVS acceptance',payload_bytes=total,
        exporter_sha256=sha(Path(__file__).read_bytes()))
    (out/'export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    excluded={'stop_capture_r2.py','flatten_pure_fill.py'}
    sources=sorted(p for p in HERE.iterdir() if p.suffix in ('.py','.md') and p.name not in excluded
        and not p.name.startswith('flatten_pure_fill'))
    files=sources+sorted(p for p in out.rglob('*') if p.is_file())
    for p in sources:assert all(x not in p.read_bytes() for x in forbidden),p
    inventory=dict(groups={'analog_pair_reference_and_purge_diagnostics':[
        dict(path=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size) for p in files]})
    a.inventory.write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(dict(files=len(files),bytes=sum(p.stat().st_size for p in files),inventory_sha256=sha(a.inventory.read_bytes()))))


if __name__=='__main__':main()
