#!/usr/bin/env python3
"""Portable completed return-remedy evidence, preserving failed run identities."""
import argparse
import datetime
import getpass
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
    stamp = datetime.datetime.strptime(gate['utc'].replace('+00:00', ''), '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
    assert gate['status'] == 'passed' and gate['expected_growth_gib'] >= .1
    assert 0 <= (datetime.datetime.now(datetime.timezone.utc) - stamp).total_seconds() < 1800
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    groups = {'resistor_fields': 'bgr-resistor-field-domain-20260922-r2',
              'wire_tree': 'bgr-return-tree-sensitivity-20260922-r2',
              'wire_vias': 'bgr-return-tree-vias-20260922-r1',
              'nominal_r1': 'bgr-return-nominal-sensitivity-20260922-r1',
              'nominal_r2': 'bgr-return-nominal-sensitivity-20260922-r2'}
    for revision in ('r1', 'r2', 'r3'):
        groups['candidate/' + revision] = 'bgr-assembly-viaquad-20260922-' + revision
    for revision in ('r2', 'r3'):
        for kind in ('drc', 'lvs'):
            groups['stock/' + revision + '/' + kind] = 'bgr-assembly-viaquad-20260922-' + revision + '-' + kind
    replacements = [(str(ROOT).encode(), b'<repository>'), (str(bulk).encode(), b'<results-root>'),
                    (str(Path.home()).encode(), b'<home>'), (b'.' + b'private/', b'<private>/')]
    forbidden = [a for a, _ in replacements] + [getpass.getuser().encode()]
    rows, payload, omitted = [], [], []
    def add(group, relative, original, binary=False):
        data = original
        if not binary:
            for old, new in replacements:
                data = data.replace(old, new)
        assert all(old not in data for old in forbidden), (group, relative)
        if relative.endswith('.json'):
            json.loads(data.decode())
        target = group + '/' + relative
        payload.append((target, data))
        rows.append(dict(export=target, original_sha256=sha(original), export_sha256=sha(data),
                         original_bytes=len(original), export_bytes=len(data), host_prefix_redacted=data != original))
    for group, folder in groups.items():
        base = bulk / folder
        status = base / ('run.json' if (base / 'run.json').exists() else 'summary.json')
        assert json.loads(status.read_text())['status'] != 'running'
        for path in sorted(base.rglob('*')):
            if not path.is_file():
                continue
            relative = str(path.relative_to(base))
            if path.suffix == '.gds' and group != 'candidate/r3':
                omitted.append(dict(group=group, relative=relative, sha256=sha(path.read_bytes()),
                                    bytes=path.stat().st_size, reason='Retained original failure geometry in bulk; exact frozen generator exported.'))
                continue
            assert path.suffix != '.pyc'
            add(group, relative, path.read_bytes(), path.suffix in ('.gds', '.oas'))
    private = ROOT / ('.' + 'private/research/verification')
    for name in ('bgr_return_tree_failed_r1_20260922.py', 'bgr_return_tree_r1_failure_20260922.json',
                 'bgr_resistor_field_audit_failed_r1_20260922.py', 'bgr_resistor_field_audit_r1_failure_20260922.json'):
        add('preserved_preparation_failures', name, (private / name).read_bytes())
    total = sum(len(data) for _, data in payload)
    assert total < .1 * 2**30 and gate['effective_storage_free_bytes'] > total + 8 * 2**30
    out = HERE / 'evidence/20260922-r1'
    out.mkdir(parents=True, exist_ok=False)
    for name, data in payload:
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    manifest = dict(status='passed portable export/privacy/JSON checks', artifacts=rows,
        omitted_retained_bulk=omitted, bytes=total, source_sha256=sha(Path(__file__).read_bytes()),
        scope='Stock-qualified isolated via candidate; partial nominal R sensitivities and unresolved field domains; no adoption.')
    (out / 'export_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    sources = [HERE / name for name in ('build_viaquad.py', 'run_geometry.py', 'evaluate_nominal_returns.py',
                                      'RETURN_REMEDY_RESULTS_20260922.md', 'export_return_milestone.py')]
    sources += [HERE.parent / 'coordinated_full_closure' / name for name in
                ('RESISTOR_FIELD_DOMAIN_REVIEW_20260922.md', 'audit_resistor_field_domain.py',
                 'prepare_return_tree_sensitivity.py', 'augment_return_tree_vias.py')]
    files = sources + [p for p in out.rglob('*') if p.is_file()]
    inventory = dict(groups={'BGR_common_return_candidate_and_partial_sensitivity': [dict(path=str(p.relative_to(ROOT)),
        sha256=sha(p.read_bytes()), bytes=p.stat().st_size) for p in sorted(files)]})
    assert not args.inventory.exists()
    args.inventory.write_text(json.dumps(inventory, indent=2) + '\n')
    print(json.dumps(dict(files=len(files), bytes=sum(p.stat().st_size for p in files), evidence_bytes=total), indent=2))


if __name__ == '__main__':
    main()
