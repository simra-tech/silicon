#!/usr/bin/env python3
"""Portable explicit-body evidence and original failures; no raw host reports."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'flow/run.sh').exists())


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser()
    for name in ('resource-gate','inventory'): p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(); gate=json.loads(a.resource_gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and 0<=age<1800 and not a.inventory.exists()
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    groups={'preparation_before_namespace':'io-explicit-vss-reference-20260923-r3',
            'preparation':'io-explicit-vss-reference-20260923-r5',
            'reader_failure':'io-explicit-vss-comparison-20260923-r1',
            'comparison':'io-explicit-vss-comparison-20260923-r2',
            'accounting':'io-explicit-vss-accounting-20260923-r1',
            'dummy_reference':'io-explicit-vss-dummy-reference-20260923-r1'}
    replacements=[((str(ROOT)+'/').encode(),b'<repository>/'),(str(bulk).encode(),b'<results-root>'),
                  (b'/work/',b'<repository>/'),(b'.'+b'private/',b'<private>/')]
    forbidden=[b'/'+b'home/',b'/opt/'+b'sim/',b'.'+b'private/',bulk.name.encode()]
    payload=[]; manifest=[]; notrun=[]
    def add(path,target):
        original=path.read_bytes(); data=original
        for old,new in replacements: data=data.replace(old,new)
        assert all(s not in data for s in forbidden),path
        if path.suffix=='.json': json.loads(data)
        if path.suffix=='.jsonl':
            for line in data.splitlines(): json.loads(line)
        payload.append((target,data))
        manifest.append(dict(export=target,original_sha256=sha(original),export_sha256=sha(data),
            original_bytes=len(original),export_bytes=len(data),host_prefix_redacted=original!=data))
    for group,name in groups.items():
        folder=bulk/name
        if not folder.exists():
            assert group=='dummy_reference'
            notrun.append(group);continue
        summary=json.loads((folder/'summary.json').read_text())
        assert not summary['status'].startswith('running'),folder
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                assert path.suffix!='.pyc'
                add(path,group+'/'+str(path.relative_to(folder)))
    private=ROOT/('.'+'private')/'research/verification'
    receipts=['io_explicit_vss_prepare_20260923_r'+str(i) for i in range(1,8)]
    receipts+=['io_explicit_vss_compare_20260923_r1','io_explicit_vss_compare_20260923_r2',
               'io_explicit_vss_accounting_20260923_r1',
               'io_tap_primitive_inspection_20260923_r1','io_tap_primitive_inspection_20260923_r2',
               'io_explicit_vss_finish_20260923_r1']
    for name in receipts:
        folder=private/name;assert folder.is_dir()
        for path in sorted(folder.iterdir()):
            if path.name in ('runner.py','run.json','run.log','prelaunch.json'):
                if path.suffix=='.json': assert json.loads(path.read_text()).get('status')!='running'
                add(path,'receipts/'+name+'/'+path.name)
    total=sum(len(data) for _,data in payload)
    assert total<.1*2**30 and total<=gate['expected_growth_gib']*2**30
    assert gate['effective_storage_free_bytes']>=total+8*2**30
    out=HERE/'evidence-20260923-r1';out.mkdir(exist_ok=False)
    for relative,data in payload:
        path=out/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    result=dict(status='passed portable export/privacy/JSON',artifacts=manifest,bytes=total,
        exporter_sha256=sha(Path(__file__).read_bytes()),not_run_groups=notrun,
        scope='Owner-authorized explicit VSS body derivative; original strict failures/AP warnings held; not fullchip or ESD signoff')
    (out/'export_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    files=sorted([q for q in HERE.iterdir() if q.suffix in ('.py','.md')]+[q for q in out.rglob('*') if q.is_file()])
    for q in files: assert not q.is_symlink() and all(s not in q.read_bytes() for s in forbidden),q
    inventory=dict(groups={'explicit_IO_VSS_interface_and_strict_remaining_failures':[
        dict(path=str(q.relative_to(ROOT)),sha256=sha(q.read_bytes()),bytes=q.stat().st_size) for q in files]})
    a.inventory.write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(dict(files=len(files),bytes=sum(q.stat().st_size for q in files)),indent=2))


if __name__=='__main__':main()
