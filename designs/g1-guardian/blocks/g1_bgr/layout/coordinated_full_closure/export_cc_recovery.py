#!/usr/bin/env python3
"""Export completed CC recovery/failure evidence with exact private inventory."""
import argparse
import datetime
import getpass
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess

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
    stamp = datetime.datetime.strptime(gate['utc'].replace('+00:00', ''), '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
    assert gate['status'] == 'passed' and gate['expected_growth_gib'] >= .1
    assert 0 <= (datetime.datetime.now(datetime.timezone.utc) - stamp).total_seconds() < 1800
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    groups = {
        'union_failure': 'bgr-cpex-20260922-r3',
        'reporter/original': 'bgr-cc-api-pilot-original-20260922-r1',
        'reporter/count': 'bgr-cc-api-pilot-count-20260922-r1',
        'full_raw': 'bgr-cc-api-full-count-20260922-r1',
        'materials': 'bgr-cc-material-audit-20260922-r1',
        'contact_ownership': 'bgr-contact-ownership-20260922-r1',
        'm5_alias': 'bgr-m5-alias-audit-20260922-r1',
        'substrate/failed_r1': 'bgr-substrate-binding-20260922-r1',
        'substrate/passed_r2': 'bgr-substrate-binding-20260922-r2',
        'blackbox_domains': 'bgr-blackbox-domain-audit-20260922-r1',
        'diagnostic_views': 'bgr-native-cc-views-20260922-r1',
    }
    replacements = [(str(ROOT).encode(), b'<repository>'), (str(bulk).encode(), b'<results-root>'),
                    (str(Path.home()).encode(), b'<home>'), (b'.' + b'private/', b'<private>/')]
    forbidden = [old for old, _ in replacements] + [getpass.getuser().encode()]
    rows = []
    payload = []
    def add(group, relative, original, binary=False):
        data = original
        if not binary:
            for old, replacement in replacements:
                data = data.replace(old, replacement)
        assert all(token not in data for token in forbidden), (group, relative)
        if relative.endswith('.gz'):
            assert all(token not in gzip.decompress(data) for token in forbidden), (group, relative)
        if relative.endswith('.json'):
            json.loads(data.decode())
        target = group + '/' + relative
        payload.append((target, data))
        rows.append(dict(source_group=group, source_relative=relative, export=target,
                         original_sha256=sha(original), export_sha256=sha(data),
                         original_bytes=len(original), export_bytes=len(data), host_prefix_redacted=data != original))
    for group, relative in groups.items():
        folder = bulk / relative
        status = folder / ('launch.json' if (folder / 'launch.json').exists() else 'summary.json')
        assert json.loads(status.read_text())['status'] != 'running'
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                assert path.suffix != '.pyc'
                add(group, str(path.relative_to(folder)), path.read_bytes(), path.suffix in ('.gds', '.oas', '.gz'))
    test = subprocess.run(['python3', str(HERE / 'test_native_cc_views.py')], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert test.returncode == 0
    add('focused_tests', 'test.log', test.stdout)
    add('focused_tests', 'summary.json', (json.dumps(dict(status='passed', returncode=0,
        test_source_sha256=sha((HERE / 'test_native_cc_views.py').read_bytes()),
        helper_sha256=sha((HERE / 'prepare_native_cc_views.py').read_bytes())), indent=2) + '\n').encode())
    total = sum(len(data) for _, data in payload)
    assert total < .1 * 2**30 and gate['effective_storage_free_bytes'] > total + 8 * 2**30
    out = HERE / 'evidence/cc-recovery-20260922-r1'
    out.mkdir(parents=True, exist_ok=False)
    for name, data in payload:
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    manifest = dict(status='passed export/privacy/JSON gates', artifact_count=len(rows), artifact_bytes=total,
                    artifacts=rows, script_sha256=sha(Path(__file__).read_bytes()),
                    scope='raw CC and explicitly assumption-grounded diagnostic view, not adoption',
                    redaction='Host prefixes in text only; binary artifacts unchanged; original/exported hashes retained.')
    (out / 'export_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    names = ['REPORTER_RECOVERY_CONTRACT_20260922.md', 'CC_RECOVERY_RESULTS_20260922.md',
             'export_cc_api.py', 'run_cc_api.py', 'check_cc_reporter_parity.py', 'audit_cc_materials.py',
             'classify_native_contacts.py', 'audit_m5_alias.py', 'prove_substrate_binding.py',
             'audit_blackbox_domains.py', 'prepare_native_cc_views.py', 'test_native_cc_views.py', 'export_cc_recovery.py']
    files = [HERE / name for name in names] + [p for p in out.rglob('*') if p.is_file()]
    inventory = dict(groups={'BGR_native_CC_recovery_and_scope': [dict(path=str(p.relative_to(ROOT)),
                          sha256=sha(p.read_bytes()), bytes=p.stat().st_size) for p in sorted(files)]})
    assert not args.inventory.exists()
    args.inventory.write_text(json.dumps(inventory, indent=2) + '\n')
    print(json.dumps(dict(status=manifest['status'], files=len(files), bytes=sum(p.stat().st_size for p in files)), indent=2))


if __name__ == '__main__':
    main()
