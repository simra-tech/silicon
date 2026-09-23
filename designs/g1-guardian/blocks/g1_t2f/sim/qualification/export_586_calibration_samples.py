#!/usr/bin/env python3
"""Export audited T2F samples without copying bulk waveforms or repeated inventories."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

from prepare_586_source_controls import HERE as SIM, ROOT


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def copy_text(source, target):
    assert source.stat().st_size < 16*1024*1024
    assert not re.search(r'/(?:home/|Users/|opt/sim/)', source.read_text()), 'Private machine path'
    shutil.copyfile(str(source), str(target))
    assert sha(target) == sha(source)


def validate_audit(audit):
    assert audit['status'].startswith('passed read-only evidence audit')
    records = audit['records']
    assert len(records) == audit['requested_samples'] == audit['completed_samples']
    assert all(r['complete'] for r in records), 'Do not label incomplete cohort as exported completion'
    assert len({r['seed'] for r in records}) == len(records)
    assert len({r['run'] for r in records}) == len(records)
    # Electrical failures are intentionally allowed and exported, never filtered.
    assert audit['passed_samples']+audit['failed_complete_samples'] == len(records)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text())
    records = validate_audit(audit)
    assert not args.output.exists()
    args.output.mkdir(parents=True)
    objects = args.output/'objects'
    objects.mkdir()
    copy_text(args.audit, args.output/'cohort_audit.json')
    manifests = []
    for record in records:
        run = SIM/'runs'/record['run']
        assert sha(run/'summary.json') == record['summary_sha256']
        assert sha(run/'provenance.json') == record['provenance_sha256']
        destination = args.output/record['run']
        destination.mkdir()
        parent_files = []
        for source in sorted(run.iterdir()):
            if not source.is_file():
                continue
            item = dict(name=source.name, sha256=sha(source), bytes=source.stat().st_size)
            if source.name in ['summary.json', 'provenance.json']:
                copy_text(source, destination/source.name)
                item['exported_as'] = record['run']+'/'+source.name
            elif source.name in ['runner.py', 'population_inventory.json', 't2f.spice', 'bgr.spice', '.spiceinit']:
                object_path = objects/item['sha256']
                if not object_path.exists():
                    copy_text(source, object_path)
                assert sha(object_path) == item['sha256']
                item['exported_as'] = 'objects/'+item['sha256']
            else:
                item['exported_as'] = None
            parent_files.append(item)
        leaves = []
        for audit_leaf in record['leaves']:
            leaf = run/('p%02d' % audit_leaf['index'])
            assert sha(leaf/'summary.json') == audit_leaf['summary_sha256']
            assert sha(leaf/'probe.cir') == audit_leaf['deck_sha256']
            assert sha(leaf/'run.log') == audit_leaf['log_sha256']
            entries = []
            for source in sorted(leaf.iterdir()):
                assert source.is_file(), 'Unexpected nested leaf artifact'
                entries.append(dict(name=source.name, sha256=sha(source), bytes=source.stat().st_size))
            leaves.append(dict(logical_leaf=str(leaf.relative_to(ROOT)), status=audit_leaf['status'], files=entries,
                               full_parameter_wave_calibration_reaudit=audit_leaf['full_reaudit']))
        manifest = dict(logical_run=str(run.relative_to(ROOT)), seed=record['seed'], status=record['status'],
                        parent_files=parent_files, leaves=leaves, audit_sha256=sha(args.audit),
                        exporter_sha256=sha(Path(__file__)),
                        scope='Exact parent summary/provenance plus content-addressed frozen sources, inventory and runner. Parent stores full first 3180-vector once; all leaf parameter/wave/calibration checks are in the hash-bound cohort audit. Every leaf artifact, including failures, is retained in bulk with exact bytes/hash manifest. No machine-specific bulk path or waveform duplication; no omitted failed sample or survivor-yield inference.')
        (destination/'artifact_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
        manifests.append(dict(run=record['run'], seed=record['seed'], status=record['status'], manifest_sha256=sha(destination/'artifact_manifest.json')))
    result = dict(status='completed audited evidence exported; electrical outcomes unchanged', audit_sha256=sha(args.audit),
                  sample_count=len(records), passed_samples=audit['passed_samples'], failed_complete_samples=audit['failed_complete_samples'],
                  records=manifests, exporter_sha256=sha(Path(__file__)),
                  exported_bytes=sum(p.stat().st_size for p in args.output.rglob('*') if p.is_file()))
    (args.output/'export_manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'records'}, indent=2))


if __name__ == '__main__':
    main()
