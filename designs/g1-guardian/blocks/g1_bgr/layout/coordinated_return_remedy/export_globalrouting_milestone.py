#!/usr/bin/env python3
"""Portable global-routing closure evidence with retained failures and one final native candidate."""
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
    groups={}
    candidates={'globalwide_r1':'bgr-assembly-globalwide-20260922-r1',
                'globalwide_r2':'bgr-assembly-globalwide-20260922-r2',
                'globalrails_r1':'bgr-assembly-globalrails-20260922-r1',
                'signalbypass_r1':'bgr-assembly-signalbypass-20260922-r1'}
    for tag,folder in candidates.items():
        groups['candidate/'+tag]=folder
        for kind in ('drc','lvs'):groups['stock/'+tag+'/'+kind]=folder+'-'+kind
    for variant in ('globalwide','globalrails','signalbypass'):
        groups['metal_preparation/'+variant]='bgr-'+variant+'-metal-prepare-20260922-r1'
        for scenario in ('kpex','lef'):
            groups['metal/'+variant+'/'+scenario]='bgr-metal-r-'+variant+'-'+scenario+'-20260922-r1'
    groups['original_raw_replay_lef']='bgr-metal-raw-replay-lef-20260922-r1'
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
            if group.startswith('candidate/') and group!='candidate/signalbypass_r1' and path.suffix=='.gds':
                omitted.append(dict(group=group,relative=relative,sha256=sha(data),bytes=len(data),
                    reason='Intermediate candidate GDS retained in bulk; frozen generators, audits and final native GDS exported.'))
                continue
            assert path.suffix!='.pyc',path
            add(group,relative,data,binary=path.suffix in ('.gds','.oas','.npy'),compressed=path.suffix=='.gz')
    extras=['bgr-global-widening-preflight-20260922-r1.json',
            'bgr-global-rail-remedy-preflight-20260922-r1.json','bgr-global-rail-remedy-preflight-20260922-r2.json',
            'bgr-signal-bypass-preflight-20260922-r1.json','bgr-signal-bypass-preflight-20260922-r2.json',
            'bgr-metal-raw-kpex-replay-comparison-20260922-r1.json']
    for variant in ('globalwide','globalrails','signalbypass'):
        for scenario in ('kpex','lef'):
            extras.append('bgr-metal-'+variant+'-comparison-'+scenario+'-20260922-r1.json')
    for name in extras:add('comparisons_preflights',name,(bulk/name).read_bytes())
    total=sum(len(data) for _,data in payload)
    assert total<.1*2**30 and gate['effective_storage_free_bytes']>total+8*2**30
    out=HERE/'evidence/globalrouting-20260922-r1'
    out.mkdir(parents=True,exist_ok=False)
    for relative,data in payload:
        target=out/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    manifest=dict(status='passed portable export/privacy/JSON checks',artifacts=rows,
        omitted_retained_bulk=omitted,bytes=total,source_sha256=sha(Path(__file__).read_bytes()),
        scope='Stock-qualified lower-metal supply and c2/VBE remedies; conditional fixed-current gains only, no model/electrical adoption.')
    (out/'export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    names=['GLOBAL_ROUTING_RESULTS_20260922.md','NONLINEAR_METALLIC_DIAGNOSTIC_CONTRACT_20260922.md',
           'audit_global_widening.py','build_global_widening.py','build_global_widening_r2.py',
           'audit_global_rail_remedy.py','audit_global_rail_remedy_r2.py','build_global_rail_remedy.py',
           'audit_signal_bypass.py','audit_signal_bypass_r2.py','build_signal_bypass.py',
           'compare_metal_candidates.py','compare_saved_metal_raw.py','prepare_candidate_metal.py',
           'replay_metal_solution.py','run_candidate_metal.py','export_globalrouting_milestone.py']
    files=[HERE/name for name in names]+[p for p in out.rglob('*') if p.is_file()]
    for path in files:
        data=path.read_bytes()
        # Source scanner literals are deliberately concatenated above, so
        # the source itself receives the same literal privacy check.
        assert all(word not in data for word in forbidden),(str(path), 'privacy')
    inventory=dict(groups={'BGR_global_routing_and_conditional_metal_comparison':[
        dict(path=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size) for p in sorted(files)]})
    assert not args.inventory.exists()
    args.inventory.write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(dict(files=len(files),bytes=sum(p.stat().st_size for p in files),evidence_bytes=total),indent=2))


if __name__=='__main__':
    main()
