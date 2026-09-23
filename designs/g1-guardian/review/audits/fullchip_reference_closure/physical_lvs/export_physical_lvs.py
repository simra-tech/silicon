#!/usr/bin/env python3
"""Portable immutable failure evidence, with original/exported hash provenance."""
import argparse
import ast
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--inventory', type=Path, required=True)
    a = ap.parse_args()
    a.output = a.output.resolve()
    a.inventory = a.inventory.resolve()
    assert not a.output.exists() and not a.inventory.exists()
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    forbidden = re.compile(rb'/(?:home|opt[/]sim)/|[.]private/')
    sources = {
        'deep_preflight_failed': 'fullchip-native-strict-lvs-20260923-r1',
        'deep_failed': 'fullchip-native-strict-lvs-20260923-r2',
        'flat_diagnostic': 'fullchip-native-strict-lvs-flat-20260923-r1',
        'saved_topology': 'fullchip-saved-io-topology-20260923-r1',
        'tap_adapter': 'fullchip-tap-prefix-adapter-20260923-r1',
        'api_adapter': 'fullchip-api-adapter-20260923-r1',
        'api_discrepancy_ledger': 'fullchip-api-discrepancy-ledger-20260923-r1',
        'saved_interface_probe': 'fullchip-saved-interface-probe-20260923-r1',
        'physical_interface_adapter_preflight_failed': 'fullchip-physical-interface-adapter-20260923-r1',
        'physical_interface_adapter': 'fullchip-physical-interface-adapter-20260923-r2',
        'api_discrepancy_ledger_full': 'fullchip-api-discrepancy-ledger-20260923-r2',
        'historical_helper_reconstruction': 'fullchip-physical-interface-helper-reconstruction-20260923-r1',
        'remaining_io_deficits_r1': 'io-remaining-deficits-20260923-r1',
        'remaining_io_deficits_r2': 'io-remaining-deficits-20260923-r2',
    }
    for i in range(1, 6):
        sources['parser_control_r' + str(i)] = 'fullchip-strict-lvs-parser-controls-20260923-r' + str(i)
    for i in range(1, 4):
        sources['tap_reader_r' + str(i)] = 'fullchip-tap-reader-20260923-r' + str(i)
        sources['api_flatten_proof_r' + str(i)] = 'fullchip-api-flatten-proof-20260923-r' + str(i)
    for i in range(1, 7):
        sources['api_original_r' + str(i)] = 'fullchip-api-original-20260923-r' + str(i)
    for i in range(1, 5):
        sources['pin_lifecycle_controls_r' + str(i)] = 'fullchip-pin-id-controls-20260923-r' + str(i)
    for i in range(1, 3):
        sources['substrate_scope_r' + str(i)] = 'fullchip-substrate-scope-20260923-r' + str(i)
        sources['physical_interface_original_r' + str(i)] = 'fullchip-physical-interface-original-20260923-r' + str(i)
    assert (bulk / sources['flat_diagnostic'] / 'summary.json').is_file()
    assert not json.loads((bulk / sources['flat_diagnostic'] / 'summary.json').read_text())['status'].startswith('running')
    rows = []
    a.output.mkdir(parents=True)
    for label, dirname in sources.items():
        source = bulk / dirname
        if not source.exists():
            rows.append(dict(group=label, status='not run', files=[]))
            continue
        receipt = source/'summary.json'
        if receipt.exists():
            assert not json.loads(receipt.read_text()).get('status','').startswith('running'), label
        for p in sorted(source.rglob('*')):
            if not p.is_file() or p.name.endswith('.progress.jsonl'):
                continue
            rel = p.relative_to(source)
            original = p.read_bytes()
            if p.suffix == '.lvsdb':
                # Native database is textual but has no host paths; do not edit
                # its internal record stream. Compression is lossless only.
                assert not forbidden.search(original), str(rel)
                buffer = io.BytesIO()
                with gzip.GzipFile(fileobj=buffer, mode='wb', compresslevel=1, mtime=0) as stream:
                    stream.write(original)
                data = buffer.getvalue()
                assert gzip.decompress(data) == original
                dest = a.output / label / (str(rel) + '.gz')
                method = 'lossless gzip; decompressed bytes equal original database'
            else:
                text = original.decode('utf-8')
                text = text.replace(str(bulk), '<results>')
                text = text.replace(str(ROOT), '<repository>')
                text = text.replace('/work/' + '.' + 'private/', '<private-context>/')
                text = text.replace('<repository>/' + '.' + 'private/', '<private-context>/')
                text = text.replace('.' + 'private/', '<private-context>/')
                data = text.encode('utf-8')
                assert not forbidden.search(data), str(rel)
                dest = a.output / label / rel
                method = 'portable path projection; numbers/status/source parameters unchanged'
                if dest.suffix == '.json':
                    json.loads(text)
                if dest.suffix == '.py':
                    ast.parse(text)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            rows.append(dict(path=str(dest.relative_to(a.output)), original_sha256=digest(original),
                             exported_sha256=digest(data), original_bytes=len(original), exported_bytes=len(data),
                             projection=method))
    manifest = dict(status='passed portable evidence export; individual failed checks retained',
                    records=rows, physical_or_source_adoption='not run',
                    exporter_sha256=digest(Path(__file__).read_bytes()))
    (a.output / 'export_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    files = [p for p in HERE.iterdir() if p.is_file() and p.suffix in ('.py', '.rb', '.md')]
    files += [p for p in a.output.rglob('*') if p.is_file()]
    inventory = []
    for p in sorted(files):
        data = p.read_bytes()
        if p.suffix != '.gz':
            assert not forbidden.search(data), str(p.relative_to(ROOT))
        inventory.append(dict(path=str(p.relative_to(ROOT)), bytes=len(data), sha256=digest(data)))
    report = dict(groups={'current_fullchip_LVS_and_source_binding': inventory},
                  files=len(inventory), bytes=sum(r['bytes'] for r in inventory))
    a.inventory.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'groups'}, indent=2))


if __name__ == '__main__':
    main()
