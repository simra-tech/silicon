#!/usr/bin/env python3
"""Compact portable physical-AP and declared comparison evidence; no Git writes."""
import argparse
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'flow/run.sh').is_file())


def digest(b):return hashlib.sha256(b).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--resource-gate',type=Path,required=True)
    ap.add_argument('--inventory',type=Path,required=True)
    a=ap.parse_args();assert not a.inventory.exists()
    gate=json.loads(a.resource_gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and 0<=age<1800
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    groups={
        'current_digital':'fullchip-current-digital-reference-20260923-r2',
        'failures/current_digital_ports':'fullchip-current-digital-reference-20260923-r1',
        'failures/raw_Manhattan':'io-tap-physical-dimensions-20260923-r1',
        'raw_geometry':'io-tap-physical-dimensions-20260923-r2',
        'failures/parent_minus_child':'io-tap-physical-ownership-20260923-r1',
        'direct_geometry':'io-direct-active-20260923-r1',
        'direct_ownership':'io-direct-ownership-20260923-r1',
        'hierarchy_accounting':'io-hierarchy-accounting-20260923-r1',
        'localization_not_source_input':'io-dimension-localize-20260923-r1',
        'current_native_binding':'io-current-native-20260923-r1',
        'failures/top_context':'io-deep-geometry-20260923-r1',
        'failures/empty_deep_region_false_completion':'io-deep-geometry-20260923-r2',
        'failures/empty_text_rejected':'io-deep-geometry-20260923-r3',
        'failures/deep_text_API':'io-text-control-20260923-r2',
        'failures/text_geometry_sequence':'io-text-geometry-control-20260923-r1',
        'literal_label_control':'io-deep-geometry-20260923-r5',
        'raw_junction':'io-deep-junction-20260923-r1',
        'junction_ownership':'io-junction-ownership-20260923-r1',
        'failures/superseded_AP':'io-physical-ap-source-20260923-r1',
        'physical_AP_source':'io-physical-ap-source-20260923-r2',
        'full_context':'io-full-context-20260923-r1',
        'pinned_formulas':'io-electrical-convention-20260923-r1',
        'conditional_SPI':'io-sensitivity-spi-20260923-r1',
        'stock_deep_FAILED':'io-physical-ap-native-lvs-20260923-r1',
        'saved_graph_interface':'io-current-diagnostics-20260923-r1',
        'full_source_comparison_FAILED':'io-current-comparison-20260923-r1',
        'current_dummy_native':'io-current-dummy-proof-20260923-r1',
        'projected_comparison_PASSED':'io-current-dummy-comparison-20260923-r1'}
    receipts=['io-'+n+'-launch-20260923-r'+str(i) for n,indices in [
        ('current-native',[1]),('direct-active',[1]),('direct-ownership',[1]),
        ('hierarchy-accounting',[1]),('dimension-localize',[1]),('deep-geometry',[1,2,3,5]),
        ('text-control',[1]),('text-geometry',[1]),('deep-junction',[1]),('junction-ownership',[1]),
        ('physical-ap-source',[1]),('ap-junction',[1]),('full-context',[1]),('physical-ap-lvs',[1]),
        ('electrical-convention',[1]),('sensitivity-spi',[1]),('current-diagnostic',[1]),
        ('current-comparison',[1]),('current-dummy-proof',[1]),('current-dummy-comparison',[1])]
        for i in indices]
    substitutions=[(str(bulk).encode(),b'<results-root>'),((str(ROOT)+'/').encode(),b'<repository>/'),
        (b'/work/',b'<repository>/'),(b'.'+b'private/',b'<private>/')]
    forbidden=[bulk.name.encode(),b'/'+b'home/',b'/opt/'+b'sim/',b'.'+b'private/']
    rows=[];payload=[];excluded=[];absent=[]
    def add(p,target):
        if p.suffix=='.pyc' or '__pycache__' in p.parts or p.name in ('resources.json','resources.log'):return
        raw=p.read_bytes()
        if p.suffix=='.lvsdb' or p.name.endswith('_extracted.cir'):
            excluded.append(dict(logical_path=target,sha256=digest(raw),bytes=len(raw),
                reason='Large raw saved database/netlist retained immutable in bulk; exact extraction command, hashes, full parsed reports and graph proofs exported.'))
            return
        binary=p.suffix in ('.gds','.oas','.npy')
        decoded=gzip.decompress(raw) if p.suffix=='.gz' else raw
        portable=decoded
        if not binary:
            for old,new in substitutions:portable=portable.replace(old,new)
            portable=re.sub(b'/'+b'home/[^/\\s\"]+/silicon-restored/',b'<repository>/',portable)
        assert all(s not in portable for s in forbidden),str(p)
        suffix=Path(p.stem).suffix if p.suffix=='.gz' else p.suffix
        if suffix=='.json':json.loads(portable)
        if suffix=='.jsonl':
            for line in portable.decode().splitlines():json.loads(line)
        compress=len(portable)>65536 or p.suffix=='.gz'
        data=gzip.compress(portable,mtime=0) if compress else portable
        if compress and not target.endswith('.gz'):target+='.gz'
        rows.append(dict(export=target,original_sha256=digest(raw),original_decoded_sha256=digest(decoded),
            portable_decoded_sha256=digest(portable),export_sha256=digest(data),original_bytes=len(raw),export_bytes=len(data),
            host_prefix_redacted=portable!=decoded,gzip=compress,binary_decoded_exact=binary and portable==decoded))
        payload.append((target,data))
    for group,name in groups.items():
        folder=bulk/name;assert folder.is_dir(),folder
        for p in sorted(folder.rglob('*')):
            if p.is_file():add(p,group+'/'+str(p.relative_to(folder)))
    for name in receipts:
        folder=bulk/name
        if not folder.exists():absent.append(name);continue
        for p in sorted(folder.iterdir()):
            if p.name in ('run.json','run.log','prelaunch.json','runner.py','observer_bindings.json','CPU0_successor.json'):
                add(p,'receipts/'+name+'/'+p.name)
    total=sum(len(data) for _,data in payload)
    assert total<gate['expected_growth_gib']*2**30 and gate['effective_storage_free_bytes']>total+8*2**30
    out=HERE/'evidence-20260923-r1';out.mkdir(exist_ok=False)
    for name,data in payload:
        p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    manifest=dict(status='passed portable evidence hash/privacy/JSON controls',artifacts=rows,excluded=excluded,
        absent_receipts=absent,payload_bytes=total,scope='Physical AP and declared scoped strict comparison, not electrical R qualification or adoption',
        exporter_sha256=digest(Path(__file__).read_bytes()))
    (out/'export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    digital=HERE.parents[1]/'fullchip_reference_closure/current_digital_reference'
    sources=sorted([p for folder in (HERE,digital) for p in folder.iterdir() if p.suffix in ('.py','.md')])
    evidence=sorted(p for p in out.rglob('*') if p.is_file())
    for p in sources+evidence:
        raw=p.read_bytes();decoded=gzip.decompress(raw) if p.suffix=='.gz' else raw
        assert all(s not in decoded for s in forbidden),p
    inventory=dict(groups={'physical_tap_source_and_current_scoped_LVS':[
        dict(path=str(p.relative_to(ROOT)),sha256=digest(p.read_bytes()),bytes=p.stat().st_size) for p in sources+evidence]})
    a.inventory.write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(dict(files=len(sources+evidence),bytes=sum(p.stat().st_size for p in sources+evidence)),indent=2))


if __name__=='__main__':main()
