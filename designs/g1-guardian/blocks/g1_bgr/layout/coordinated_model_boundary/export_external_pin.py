#!/usr/bin/env python3
"""Portable plane-diagnostic evidence, original failures and exact inventory."""
import argparse
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resource-gate', type=Path, required=True)
    ap.add_argument('--inventory', type=Path, required=True)
    a = ap.parse_args()
    gate = json.loads(a.resource_gate.read_text())
    when = datetime.datetime.fromisoformat(gate['utc'])
    assert gate['status'] == 'passed' and 0 <= (datetime.datetime.now(datetime.timezone.utc)-when).total_seconds() < 1800
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    groups = {'boundary/r'+str(i):'bgr-model-boundary-20260923-r'+str(i) for i in (1,2)}
    groups.update({'point_preparation/r'+str(i):'bgr-external-pin-metal-prepare-20260923-r'+str(i) for i in (1,2,3)})
    groups.update({'network/kpex':'bgr-metal-r-externalpins-kpex-20260923-r1',
                   'network/lef_failed_preflight':'bgr-metal-r-externalpins-lef-20260923-r1',
                   'network/lef':'bgr-metal-r-externalpins-lef-20260923-r2',
                   'source_preparation':'bgr-external-pin-source-20260923-r1',
                   'zero':'bgr-external-pin-zero-20260923-r1',
                   'kpex':'bgr-external-pin-kpex-20260923-r1',
                   'lef':'bgr-external-pin-lef-20260923-r1'})
    replacements = [(str(ROOT).encode(), b'<repository>'), (str(bulk).encode(), b'<results-root>'),
                    (b'/work/', b'<repository>/'), (b'.'+b'private/', b'<private>/')]
    # Inside rootless containers the runtime username is "root", which is not
    # a personal identifier and occurs in portable placeholders. Use bulk owner.
    forbidden = [bulk.name.encode(), b'/'+b'home/', b'/opt/'+b'sim/', b'.'+b'private/']
    payload, rows = [], []
    for group, name in groups.items():
        folder = bulk / name
        for receipt_name in ('summary.json', 'launch.json', 'failure.json'):
            receipt = folder / receipt_name
            if receipt.exists():
                assert not json.loads(receipt.read_text())['status'].startswith('running')
        if group in ('kpex','lef'):
            assert json.loads((folder/'summary.json').read_text())['status'] == 'passed conditional nonlinear OP completion and source controls'
            assert (folder/'conditional_analysis.json').is_file()
        for path in sorted(folder.rglob('*')):
            if not path.is_file():
                continue
            assert path.suffix != '.pyc'
            original = path.read_bytes()
            binary = path.suffix in ('.gds','.npy','.gz')
            data = original
            if not binary:
                for old, new in replacements:
                    data = data.replace(old, new)
            inspected = gzip.decompress(data) if path.suffix == '.gz' else data
            assert all(word not in inspected for word in forbidden), path
            if path.suffix == '.json':
                json.loads(data.decode())
            elif path.suffix == '.jsonl':
                for line in data.decode().splitlines():
                    json.loads(line)
            target = group+'/'+str(path.relative_to(folder))
            payload.append((target,data))
            rows.append(dict(export=target, original_sha256=digest(original), export_sha256=digest(data),
                             original_bytes=len(original), export_bytes=len(data),
                             host_prefix_redacted=data != original, binary_unchanged=binary and data == original))
    total = sum(len(data) for _,data in payload)
    assert total < .10*2**30 and gate['effective_storage_free_bytes'] > total+8*2**30
    assert gate['expected_growth_gib'] * 2**30 >= total
    out = HERE/'evidence/external-pins-20260923-r1'
    out.mkdir(parents=True,exist_ok=False)
    for relative,data in payload:
        path = out/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    dump = lambda p,x:p.write_text(json.dumps(x,indent=2)+'\n')
    dump(out/'export_manifest.json',dict(status='passed portable export/privacy/JSON checks', artifacts=rows,
         bytes=total, exporter_sha256=digest(Path(__file__).read_bytes()),
         scope='Published-M2-emitter-pin conditional diagnostic, not calibrated model-plane or physical qualification.'))
    files = sorted([p for p in HERE.iterdir() if p.suffix in ('.py','.md')]+[p for p in out.rglob('*') if p.is_file()])
    for path in files:
        assert all(word not in path.read_bytes() for word in forbidden),path
    assert not a.inventory.exists()
    dump(a.inventory,dict(groups={'BGR_external_pin_boundary_diagnostic':[
         dict(path=str(p.relative_to(ROOT)),sha256=digest(p.read_bytes()),bytes=p.stat().st_size) for p in files]}))
    print(json.dumps(dict(files=len(files),bytes=sum(p.stat().st_size for p in files),evidence_bytes=total),indent=2))


if __name__ == '__main__':
    main()
