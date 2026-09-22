#!/usr/bin/env python3
"""Compact portable precision-stem/metallic-R evidence, including failures."""
import argparse
import datetime
import getpass
import gzip
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resource-gate', type=Path, required=True)
    ap.add_argument('--inventory', type=Path, required=True)
    args = ap.parse_args()
    gate = json.loads(args.resource_gate.read_text())
    stamp = datetime.datetime.strptime(gate['utc'].replace('+00:00',''),'%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
    assert gate['status']=='passed' and 0 <= (datetime.datetime.now(datetime.timezone.utc)-stamp).total_seconds()<1800
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    groups = {'native_request':'bgr-native-r-request-20260922-r2',
              'access_geometry':'bgr-return-access-geometry-20260922-r1',
              'precision_rail':'bgr-precision-rail-sensitivity-20260922-r1',
              'precision_stem':'bgr-assembly-precisionstem-20260922-r1',
              'precision_stem_drc':'bgr-assembly-precisionstem-20260922-r1-drc',
              'precision_stem_lvs':'bgr-assembly-precisionstem-20260922-r1-lvs',
              'metal_preparation':'bgr-metal-network-prepare-20260922-r1'}
    for scenario,revisions in [('kpex',range(1,5)),('lef',range(1,3))]:
        for revision in revisions:
            groups['controls/'+scenario+'/r'+str(revision)]='bgr-metal-r-controls-'+scenario+'-20260922-r'+str(revision)
        for revision in (1,2):
            groups['full/'+scenario+'/r'+str(revision)]='bgr-metal-r-full-'+scenario+'-20260922-r'+str(revision)
    replacements=[(str(ROOT).encode(),b'<repository>'),(str(bulk).encode(),b'<results-root>'),
                  (str(Path.home()).encode(),b'<home>'),(b'.'+b'private/',b'<private>/')]
    forbidden=[getpass.getuser().encode(),b'/'+b'home/',b'/opt/'+b'sim/',b'.'+b'private/']
    rows,payload,omitted=[],[],[]
    def normalize(data):
        for old,new in replacements:
            data=data.replace(old,new)
        assert all(word not in data for word in forbidden)
        return data
    def add(group,relative,original,binary=False,compressed=False):
        if compressed:
            decoded=gzip.decompress(original)
            normalized=normalize(decoded)
            json.loads(normalized.decode())
            data=original if decoded==normalized else gzip.compress(normalized,mtime=0)
        else:
            data=original if binary else normalize(original)
            if binary:
                assert all(word not in data for word in forbidden)
            if relative.endswith('.json'):
                json.loads(data.decode())
        target=group+'/'+relative
        payload.append((target,data))
        rows.append(dict(export=target,original_sha256=sha(original),export_sha256=sha(data),
                         original_bytes=len(original),export_bytes=len(data),host_prefix_redacted=data!=original))
    for group,folder in groups.items():
        base=bulk/folder
        status=next((p for p in (base/'launch.json',base/'run.json',base/'summary.json') if p.exists()),None)
        assert status is not None and json.loads(status.read_text())['status']!='running',group
        for path in sorted(base.rglob('*')):
            if not path.is_file():
                continue
            relative=str(path.relative_to(base))
            data=path.read_bytes()
            if group=='native_request' and (relative in ('request.json','request.pb') or relative.startswith('engine/')):
                omitted.append(dict(group=group,relative=relative,sha256=sha(data),bytes=len(data),
                    reason='Large request / installed engine copy retained in bulk; pinned generator and complete coverage ledger exported.'))
                continue
            assert path.suffix!='.pyc',path
            add(group,relative,data,binary=path.suffix in ('.gds','.oas','.npy'),compressed=path.suffix=='.gz')
    private=ROOT/('.'+'private/research/verification')
    name='bgr_native_r_request_prelaunch_failure_20260922_r1.json'
    add('preserved_prelaunch_failure',name,(private/name).read_bytes())
    total=sum(len(data) for _,data in payload)
    assert total<.1*2**30 and gate['effective_storage_free_bytes']>total+8*2**30
    out=HERE/'evidence/metallization-20260922-r1'
    out.mkdir(parents=True,exist_ok=False)
    for relative,data in payload:
        target=out/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    manifest=dict(status='passed portable export/privacy/JSON checks',artifacts=rows,
        omitted_retained_bulk=omitted,bytes=total,source_sha256=sha(Path(__file__).read_bytes()),
        scope='Stock-qualified precision stem; conditional full metallic network, no compact-model/electrical adoption.')
    (out/'export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    names=['METALLIZATION_R_CONTRACT_20260922.md','METALLIZATION_R_RESULTS_20260922.md',
           'audit_metal_r_solution.py','audit_native_r_coverage.py','audit_return_access_geometry.py',
           'build_precision_stem.py','extend_precision_rail.py','extract_metal_r.py',
           'prepare_metal_r_network.py','prepare_native_r_request.py','run_metal_r.py','export_metal_milestone.py']
    files=[HERE/name for name in names]+[p for p in out.rglob('*') if p.is_file()]
    for path in files:
        data=path.read_bytes()
        # Source scanner literals are deliberately concatenated above, so
        # the source itself receives the same literal privacy check.
        assert all(word not in data for word in forbidden),(str(path), 'privacy')
    inventory=dict(groups={'BGR_precision_stem_and_conditional_full_metallic_R':[
        dict(path=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size) for p in sorted(files)]})
    assert not args.inventory.exists()
    args.inventory.write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(dict(files=len(files),bytes=sum(p.stat().st_size for p in files),evidence_bytes=total),indent=2))


if __name__=='__main__':
    main()
