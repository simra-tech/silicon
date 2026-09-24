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
    groups = {
        'remaining_edges':'bgr-supply-remaining-20260923-r1',
        'screen':'bgr-supply-screen-20260923-r1',
        'upper_screen':'bgr-supply-upper-screen-20260923-r1',
        'candidate':'bgr-supply-candidate-20260923-r1',
        'stock/local_drc':'bgr-supply-drc-20260923-r1',
        'stock/local_lvs':'bgr-supply-lvs-20260923-r1',
        'context/original_failed':'bgr-supply-context-20260923-r1',
        'context/exact_flat_fill_failed':'bgr-supply-context-20260923-r2',
        'context/fill_inventory':'bgr-supply-fill-inventory-20260923-r1',
        'context/candidate':'bgr-supply-context-candidate-20260923-r1',
        'context/cluster_scope_failed':'bgr-supply-pruned-context-20260923-r2',
        'context/local_hypothesis_failed':'bgr-supply-local-control-20260923-r1',
        'context/local_control':'bgr-supply-local-control-20260923-r2',
        'context/clearance':'bgr-supply-pruned-context-20260923-r3',
        'context/terminals':'bgr-supply-context-terminals-20260923-r1',
        'stock/full_main':'bgr-supply-context-main-20260923-r1',
        'stock/full_maximal':'bgr-supply-context-maximal-20260923-r1',
        'stock/full_antenna':'bgr-supply-context-antenna-20260923-r1',
        'stock/full_density':'bgr-supply-context-density-20260923-r1',
        'network_controls_failed_reservation':'bgr-supply-network-controls-20260923-r1',
        'network_controls':'bgr-supply-network-controls-20260923-r2',
        'metal_preparation':'bgr-supply-metal-prepare-20260923-r1',
        'network/kpex':'bgr-metal-r-supply-kpex-20260923-r2',
        'network/lef':'bgr-metal-r-supply-lef-20260923-r2',
        'source_preparation':'bgr-supply-fixture-20260923-r1',
        'zero':'bgr-supply-zero-20260923-r1',
        'kpex':'bgr-supply-kpex-20260923-r1',
        'comparison':'bgr-supply-comparison-20260923-r1'}
    replacements = [((str(ROOT)+'/').encode(), b'<repository>/'), (str(bulk).encode(), b'<results-root>'),
                    (b'/work/', b'<repository>/'), (b'.'+b'private/', b'<private>/')]
    # Inside rootless containers the runtime username is "root", which is not
    # a personal identifier and occurs in portable placeholders. Use bulk owner.
    forbidden = [bulk.name.encode(), b'/'+b'home/', b'/opt/'+b'sim/', b'.'+b'private/']
    payload, rows, not_run = [], [], []
    for group, name in groups.items():
        folder = bulk / name
        if not folder.exists():
            assert group in ('comparison','zero','kpex'), group
            not_run.append(dict(group=group,status='not run; no output directory exists'))
            continue
        for receipt_name in ('summary.json', 'analysis.json', 'launch.json', 'failure.json', 'run.json'):
            receipt = folder / receipt_name
            if receipt.exists():
                assert not json.loads(receipt.read_text())['status'].startswith('running')
        if group=='kpex' and json.loads((folder/'summary.json').read_text())['status'] == 'passed conditional nonlinear OP completion and source controls':
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
    # Host resource/quota reports stay private; export only normalized execution
    # and prelaunch receipts. Their resource hashes preserve the binding.
    receipt_root=ROOT/('.'+'private')/'research/verification'
    receipt_names=[
        'bgr_supply_context_20260923_r1','bgr_supply_context_20260923_r2',
        'bgr_supply_pruned_context_20260923_r1','bgr_supply_pruned_context_20260923_r2',
        'bgr_supply_pruned_context_20260923_r3','bgr_supply_local_control_20260923_r1',
        'bgr_supply_local_control_20260923_r2','bgr_supply_context_terminals_20260923_r1',
        'bgr_supply_context_terminals_20260923_r2','bgr_supply_context_main_20260923_r1',
        'bgr_supply_context_maximal_20260923_r1','bgr_supply_context_antenna_20260923_r1',
        'bgr_supply_context_density_20260923_r1','bgr_supply_network_20260923_r1',
        'bgr_supply_network_20260923_r2','bgr_supply_network_20260923_r3',
        'bgr_supply_zero_20260923_r1','bgr_supply_kpex_20260923_r1',
        'bgr_supply_compare_20260923_r1']
    for name in receipt_names:
        folder=receipt_root/name
        assert folder.is_dir(),folder
        for path in sorted(folder.iterdir()):
            if path.name not in ('runner.py','run.json','run.log','prelaunch.json'):
                continue
            original=path.read_bytes();data=original
            for old,new in replacements:data=data.replace(old,new)
            assert all(word not in data for word in forbidden),path
            if path.suffix=='.json':
                content=json.loads(data)
                assert content.get('status')!='running',path
            target='receipts/'+name+'/'+path.name
            payload.append((target,data))
            rows.append(dict(export=target,original_sha256=digest(original),export_sha256=digest(data),
                             original_bytes=len(original),export_bytes=len(data),
                             host_prefix_redacted=data!=original,binary_unchanged=False))
    total = sum(len(data) for _,data in payload)
    assert total < .25*2**30 and gate['effective_storage_free_bytes'] > total+8*2**30
    assert gate['expected_growth_gib'] * 2**30 >= total
    out = HERE/'evidence/supply-20260923-r1'
    out.mkdir(parents=True,exist_ok=False)
    for relative,data in payload:
        path = out/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    dump = lambda p,x:p.write_text(json.dumps(x,indent=2)+'\n')
    dump(out/'export_manifest.json',dict(status='passed portable export/privacy/JSON checks', artifacts=rows,
         bytes=total, not_run_groups=not_run, exporter_sha256=digest(Path(__file__).read_bytes()),
         scope='Source-held supply routing, exact ten generated-fill exclusion/full-parent physical checks and conditional diagnostics; not complete model-plane or full-chip electrical qualification.'))
    files = sorted([p for p in HERE.iterdir() if p.suffix in ('.py','.md')]+[p for p in out.rglob('*') if p.is_file()])
    for path in files:
        assert all(word not in path.read_bytes() for word in forbidden),path
    assert not a.inventory.exists()
    dump(a.inventory,dict(groups={'BGR_supply_geometry_context_and_conditional_OP':[
         dict(path=str(p.relative_to(ROOT)),sha256=digest(p.read_bytes()),bytes=p.stat().st_size) for p in files]}))
    print(json.dumps(dict(files=len(files),bytes=sum(p.stat().st_size for p in files),evidence_bytes=total),indent=2))


if __name__ == '__main__':
    main()
