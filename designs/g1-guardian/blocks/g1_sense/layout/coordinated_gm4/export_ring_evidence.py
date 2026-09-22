#!/usr/bin/env python3
"""Compact r7 and read-only MIM ownership evidence; no Git writes."""
import argparse
import getpass
import hashlib
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
SOURCES = ('build_ring_power_revision.py audit_ring_power_revision.py '
           'RING_POWER_REVISION_20260922.md audit_mim_ownership_api.py '
           'MIM_OWNERSHIP_BOUNDARY_20260922.md export_ring_evidence.py').split()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output = a.output.resolve()
    assert not a.output.exists()
    bulk = Path(os.environ['G1_RESULTS_ROOT']).resolve()
    stock = json.loads((bulk/'sense-ring-stock-20260922-r7a/summary.json').read_text())
    assert stock['status'] == 'passed'
    assert stock['GDS_sha256'] == '9559f0d309f0c14d2f226e56138dfd0283cf2b847f0b536929565e4a739b9b02'
    selected = []
    def add(folder, names):
        for name in names.split():
            relative = Path(folder)/name
            source = bulk/relative
            assert source.is_file() and not source.is_symlink()
            selected.append((source, relative))
    add('sense-ring-routing-20260922-r7a','manifest.json builder_snapshot.py g1_sense_physical.gds')
    add('sense-ring-routing-20260922-r7a-preparation','derived_builder.py adapter_snapshot.py bindings.json')
    add('sense-ring-reference-20260922-r7a','manifest.json g1_sense_physical.cdl audit_snapshot.py')
    add('sense-ring-stock-20260922-r7a','summary.json drc.log lvs.log drc/g1_sense_physical_g1_sense_physical_full.lyrdb lvs/g1_sense_physical_extracted.cir')
    add('', 'sense-ring-saved-20260922-r7a.json sense-ring-capacity-20260922-r7a.json sense-ring-junction-20260922-r7a.json')
    add('sense-mim-ownership-20260922-r2','summary.json script_snapshot.py')
    for receipt in ('sense_mim_ownership_20260922_r1',):
        for name in ('check.json','check.log'):
            source = ROOT/'.private/research/verification'/receipt/name
            assert source.is_file()
            selected.append((source,Path('retained-readonly-failures')/receipt/name))
    assert sum(s.stat().st_size for s,_ in selected) < 25*2**20
    def privacy(data):
        text = data.decode()
        assert getpass.getuser() not in text
        assert not re.search(r'/(?:home|Users|opt/sim)/[^\s"<>]+',text)
    a.output.mkdir(parents=True)
    rows = []
    for source, relative in selected:
        raw = source.read_bytes()
        encoded = raw if source.suffix == '.gds' else raw.decode().replace(str(bulk),'${RESULTS_ROOT}').replace(str(ROOT),'${WORKSPACE}').encode()
        if source.suffix != '.gds':
            privacy(encoded)
        dest = a.output/relative
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(encoded)
        rows.append(dict(path=str(dest.relative_to(ROOT)),sha256=sha(dest),bytes=len(encoded),
                         source_sha256=sha(source),source_relative=str(relative),
                         transformation='byte-exact' if encoded == raw else 'explicit results/workspace prefix replacement; original retained'))
    export = a.output/'export_manifest.json'
    export.write_text(json.dumps(dict(status='passed compact ring and ownership export',files=rows,
        exporter_sha256=sha(Path(__file__)),original_failures_retained=True,
        full_core_integration='parent owned',complete_PEX='not qualified',adoption='not run'),indent=2)+'\n')
    files = [HERE/name for name in SOURCES]+[ROOT/r['path'] for r in rows]+[export]
    frozen = []
    for path in files:
        assert path.is_file() and not path.is_symlink()
        if path.suffix != '.gds':
            privacy(path.read_bytes())
        frozen.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),bytes=path.stat().st_size))
    result = dict(status='frozen r7 and ownership milestone; root owns Git',files=sorted(frozen,key=lambda r:r['path']),
                  count=len(frozen),bytes=sum(r['bytes'] for r in frozen),
                  excludes=['unchanged committed power/assembly/method sources','raw binary LVS databases retained with stock hashes'])
    inventory = a.output/'commit_inventory.json'
    inventory.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(count=result['count'],bytes=result['bytes'],inventory=str(inventory.relative_to(ROOT)),
                         inventory_sha256=sha(inventory)),indent=2))


if __name__ == '__main__':
    main()
