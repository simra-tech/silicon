#!/usr/bin/env python3
"""Compact portable source-held via evidence, retaining every actual failure."""
import argparse
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'flow/run.sh').is_file())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--resource-gate',type=Path,required=True)
    ap.add_argument('--inventory',type=Path,required=True)
    a=ap.parse_args()
    gate=json.loads(a.resource_gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and 0<=age<1800 and not a.inventory.exists()
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    groups={
        'saved_parent_map':'bgr-residual-saved-map-20260923-r1',
        'screen/foreign_capture_failed':'bgr-dvbe-cuts-screen-20260923-r1',
        'screen/eight_cuts':'bgr-dvbe-cuts-screen-20260923-r2',
        'screen/six_cuts':'bgr-dvbe-cuts-screen-20260923-r3',
        'candidate/eight_cuts':'bgr-dvbe-cuts-candidate-20260923-r1',
        'candidate/final':'bgr-dvbe-cuts-candidate-20260923-r2',
        'stock/eight_drc':'bgr-dvbe-cuts-drc-20260923-r1',
        'stock/eight_lvs':'bgr-dvbe-cuts-lvs-20260923-r1',
        'stock/final_drc':'bgr-dvbe-cuts-drc-20260923-r2',
        'stock/final_lvs':'bgr-dvbe-cuts-lvs-20260923-r2',
        'context/fill_spacing_failed':'bgr-dvbe-cuts-parent-context-20260923-r1',
        'context/current_digital':'bgr-dvbe-cuts-parent-context-20260923-r3',
        'network_controls':'bgr-dvbe-cuts-network-controls-20260923-r1',
        'BN_model_control':'bgr-dvbe-cuts-BN-audit-20260923-r1',
        'metal_preparation':'bgr-dvbe-cuts-metal-prepare-20260923-r1',
        'network/kpex':'bgr-metal-r-dvbe-cuts-kpex-20260923-r1',
        'network/lef':'bgr-metal-r-dvbe-cuts-lef-20260923-r1',
        'fixture':'bgr-dvbe-cuts-fixture-20260923-r1',
        'zero/prefix_failed':'bgr-dvbe-cuts-zero-20260923-r1',
        'zero/exact':'bgr-dvbe-cuts-zero-20260923-r2',
        'nominal/kpex':'bgr-dvbe-cuts-kpex-20260923-r1',
        'comparison':'bgr-dvbe-cuts-comparison-20260923-r1'}
    receipts=['bgr-residual-saved-launch-20260923-r1']
    for name,indices in [('screen',range(1,4)),('build',range(1,3)),('context',range(1,6)),('drc',range(1,4)),('lvs',range(1,3)),('network',range(1,3)),('zero',range(1,4)),('kpex',range(1,2))]:
        receipts.extend('bgr-dvbe-cuts-'+name+'-launch-20260923-r'+str(i) for i in indices)
    replacements=[((str(ROOT)+'/').encode(),b'<repository>/'),(str(bulk).encode(),b'<results-root>'),
                  (b'/work/',b'<repository>/'),(b'.'+b'private/',b'<private>/')]
    forbidden=[bulk.name.encode(),b'/'+b'home/',b'/opt/'+b'sim/',b'.'+b'private/']
    payload=[]; rows=[]; excluded=[]

    def add(path,target):
        original=path.read_bytes()
        if target=='candidate/eight_cuts/bank.gds':
            excluded.append(dict(source_id=target,sha256=digest(original),bytes=len(original),
                reason='Historical failed candidate retained in bulk; exact builder/overlay/parent hashes reproduce it. One final GDS exported.'))
            return
        if path.name in ('resources.json','resources.log') or path.suffix=='.pyc':
            return
        binary=path.suffix in ('.gds','.npy')
        decoded=gzip.decompress(original) if path.suffix=='.gz' else original
        portable=decoded
        if not binary:
            for old,new in replacements:
                portable=portable.replace(old,new)
        assert all(word not in portable for word in forbidden),path
        effective_suffix=Path(path.stem).suffix if path.suffix=='.gz' else path.suffix
        if effective_suffix=='.json':
            obj=json.loads(portable)
            assert not isinstance(obj,dict) or not str(obj.get('status','')).startswith('running'),path
        if effective_suffix=='.jsonl':
            for line in portable.decode().splitlines():
                json.loads(line)
        compress=path.suffix=='.gz' or (not binary and len(portable)>65536)
        exported=gzip.compress(portable,mtime=0) if compress else portable
        if compress and not target.endswith('.gz'):
            target+='.gz'
        rows.append(dict(export=target,original_sha256=digest(original),original_decoded_sha256=digest(decoded),
            portable_decoded_sha256=digest(portable),export_sha256=digest(exported),
            original_bytes=len(original),export_bytes=len(exported),host_prefix_redacted=decoded!=portable,
            gzip=compress,binary_unchanged=binary and exported==original))
        payload.append((target,exported))

    for group,name in groups.items():
        folder=bulk/name;assert folder.is_dir(),folder
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                add(path,group+'/'+str(path.relative_to(folder)))
    absent=[]
    for name in receipts:
        folder=bulk/name
        if not folder.exists():
            absent.append(name);continue
        for path in sorted(folder.iterdir()):
            if path.name in ('run.json','run.log','prelaunch.json','runner.py','observer_bindings.json'):
                add(path,'receipts/'+name+'/'+path.name)
    total=sum(len(data) for _,data in payload)
    assert total<gate['expected_growth_gib']*2**30
    assert gate['effective_storage_free_bytes']>total+8*2**30
    out=HERE/'evidence-20260923-r1';out.mkdir(exist_ok=False)
    for target,data in payload:
        path=out/target;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    manifest=dict(status='passed portable via evidence/privacy/JSON checks',artifacts=rows,excluded=excluded,
        absent_receipt_names=absent,bytes=total,exporter_sha256=digest(Path(__file__).read_bytes()),
        scope='Conditional source-held redundant routing; not complete electrical/model-plane qualification or integration')
    (out/'export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    files=sorted([p for p in HERE.iterdir() if p.suffix in ('.py','.md')]+[p for p in out.rglob('*') if p.is_file()])
    for p in files:
        content=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
        assert all(word not in content for word in forbidden),p
    inventory=dict(groups={'BGR_redundant_DVBE_cuts_and_conditional_OP':[
        dict(path=str(p.relative_to(ROOT)),sha256=digest(p.read_bytes()),bytes=p.stat().st_size) for p in files]})
    a.inventory.write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(dict(files=len(files),bytes=sum(p.stat().st_size for p in files),payload_bytes=total),indent=2))


if __name__=='__main__':
    main()
