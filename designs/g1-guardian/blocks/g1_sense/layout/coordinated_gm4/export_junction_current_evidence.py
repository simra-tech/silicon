#!/usr/bin/env python3
"""Compact portable intrinsic-observation/current ledger; originals and failures retained."""
import argparse
import getpass
import gzip
import hashlib
import io
import json
import os
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
SOURCES=('SHARED_JUNCTION_DIAGNOSTIC_CONTRACT_20260922.md SHARED_JUNCTION_OBSERVATION_20260922.md '
         'SUPPLY_TERMINAL_MAPPING_20260922.md JUNCTION_CHARGE_OBSERVATION_PROPOSAL_20260922.md '
         'analyze_shared_junction_metadata.py inspect_psp_node_descriptor.py map_supply_terminal_currents.py '
         'observe_shared_junction_metadata.py reconstruct_shared_node_mapping.py prepare_shared_bias_control.py '
         'run_shared_bias_control.py analyze_shared_bias_control.py export_junction_current_evidence.py').split()


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output=a.output.resolve();assert not a.output.exists()
    bulk=Path(os.environ['G1_RESULTS_ROOT']).resolve();selected=[]
    def add(folder,names):
        for name in names.split():
            relative=Path(folder)/name;source=bulk/relative
            assert source.is_file() and not source.is_symlink();selected.append((source,relative))
    for name in ('room-20260922-r1','room-20260922-r2','hot-20260922-r1','hot-20260922-r2'):
        folder='sense-shared-junction-metadata-'+name
        add(folder,'summary.json bindings.json run.json run.log probe.cir sense.spice trip.spice bgr.spice runner_snapshot.py contract.md op0.dat currents.dat monitor_voltages.dat')
        if (bulk/folder/'all_op.raw').exists():add(folder,'all_op.raw')
    add('sense-shared-junction-metadata-room-20260922-r1','read_only_scale_and_nodes.json read_only_scale_and_nodes_r2.json analyzer_r2_snapshot.py reconstructed_mapping_r1_failure.json reconstructed_mapping_r2.json')
    add('sense-shared-junction-metadata-room-20260922-r2','reconstructed_mapping_r3.json')
    add('sense-shared-junction-metadata-hot-20260922-r2','reconstructed_mapping_r2.json')
    add('sense-shared-bias-control-20260922-r1','analysis.json bindings.json contract.json run.json run.log probe.cir builder_snapshot.py runner_snapshot.py equal_a.raw equal_b.raw negative_body.raw')
    add('','sense-psp-descriptor-20260922-r2.json sense-psp-descriptor-r1-failed-script.py sense-supply-terminal-mapping-20260922-r1.json')
    for name in ('check.json','check.log'):
        selected.append((ROOT/'.private/research/verification/psp_descriptor_20260922_r1'/name,Path('retained-descriptor-failure')/name))
    def privacy(data):
        s=data.decode();assert getpass.getuser() not in s
        assert not re.search(r'/(?:home|Users|opt/sim)/[^\s"<>]+',s)
    assert sum(s.stat().st_size for s,_ in selected)<32*2**20
    a.output.mkdir(parents=True);rows=[]
    for source,relative in selected:
        raw=source.read_bytes()
        data=raw.decode().replace(str(bulk),'${RESULTS_ROOT}').replace(str(ROOT),'${WORKSPACE}').encode()
        privacy(data);compressed=source.suffix in ('.log','.raw','.cir')
        dest=a.output/str(relative)
        if compressed:dest=dest.with_name(dest.name+'.gz')
        dest.parent.mkdir(parents=True,exist_ok=True)
        if compressed:
            buffer=io.BytesIO()
            with gzip.GzipFile(fileobj=buffer,mode='wb',mtime=0) as stream:stream.write(data)
            encoded=buffer.getvalue()
        else:encoded=data
        dest.write_bytes(encoded)
        rows.append(dict(path=str(dest.relative_to(ROOT)),sha256=sha(dest),bytes=len(encoded),source_sha256=sha(source),
                         decoded_sha256=hashlib.sha256(data).hexdigest(),source_relative=str(relative),
                         transformation=('gzip; ' if compressed else '')+('decoded byte-exact' if data==raw else 'explicit results/workspace prefix replacement; original retained')))
    manifest=a.output/'export_manifest.json'
    manifest.write_text(json.dumps(dict(status='passed portable observations; applicability/charge/completePEX unqualified',
                                        files=rows,exporter_sha256=sha(Path(__file__)),failures_retained=True),indent=2)+'\n')
    files=[HERE/n for n in SOURCES]+[ROOT/r['path'] for r in rows]+[manifest]
    records=[]
    for path in files:
        assert path.is_file() and not path.is_symlink()
        data=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes();privacy(data)
        records.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),bytes=path.stat().st_size))
    inventory=a.output/'commit_inventory.json'
    inventory.write_text(json.dumps(dict(status='frozen observation/current milestone; root owns Git',files=sorted(records,key=lambda r:r['path']),
                                        count=len(records),bytes=sum(r['bytes'] for r in records),
                                        excludes=['unchanged geometry/card/deck sources','electrical102terminal input ledgers already exported by electrical owner']),indent=2)+'\n')
    print(json.dumps(dict(count=len(records),bytes=sum(r['bytes'] for r in records),inventory=str(inventory.relative_to(ROOT)),sha256=sha(inventory)),indent=2))


if __name__=='__main__':main()
