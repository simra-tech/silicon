#!/usr/bin/env python3
"""Export the pad candidate and immutable failures with portable provenance."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--inventory', type=Path, required=True)
    a = p.parse_args(); a.output = a.output.resolve(); a.inventory = a.inventory.resolve()
    assert not a.output.exists() and not a.inventory.exists()
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    private = ROOT / '.private'
    folders = {
        'initial_serialization_failed': 'bondpad-outward-20260923-r1',
        'retained_frame_candidate': 'bondpad-outward-20260923-r2',
        'candidate': 'bondpad-outward-20260923-r3',
        'actual_placement_odb': 'bondpad-outward-odb-20260923-r1',
        'notch_unit_failed': 'bondpad-outward-unit-20260923-r1',
        'notch_unit_stock_failed': 'bondpad-outward-unit-stock-20260923-r1',
        'swept_unit': 'bondpad-outward-unit-20260923-r2',
        'swept_unit_stock_context_failed': 'bondpad-outward-unit-stock-20260923-r2',
        'connectivity': 'bondpad-outward-connectivity-20260923-r1',
        'independent_geometry': 'bondpad-outward-independent-20260923-r1',
        'public_bondmap': 'bondpad-outward-public-map-20260923-r1',
        'stock_main': 'bondpad-outward-main-20260923-r1',
        'stock_maximal': 'bondpad-outward-maximal-20260923-r2',
        'stock_antenna': 'bondpad-outward-antenna-20260923-r1',
        'stock_density': 'bondpad-outward-density-20260923-r1'}
    receipts = [
        'bondpad_build_20260923_r1', 'bondpad_serialization_probe_20260923_r1',
        'bondpad_build_20260923_r2', 'bondpad_odb_20260923_r1',
        'bondpad_notch_rule_20260923_r1', 'bondpad_unit_prep_20260923_r1',
        'bondpad_unit_stock_20260923_r1', 'bondpad_build_20260923_r3',
        'bondpad_unit_stock_20260923_r2', 'bondpad_connectivity_20260923_r1',
        'bondpad_full_maximal_20260923_r1', 'bondpad_full_maximal_20260923_r2',
        'bondpad_saved_audits_20260923_r1', 'bondpad_full_main_20260923_r1',
        'bondpad_antenna_20260923_r1', 'bondpad_density_20260923_r1',
        'bondpad_public_map_20260923_r1']
    forbidden = re.compile(rb'/(?:home|opt[/]sim)/|[.]private/')
    a.output.mkdir(parents=True); records = []; retained = []

    def export(source, relative):
        raw = source.read_bytes(); data = raw
        method = 'byte-identical binary geometry' if source.suffix == '.gds' else 'portable path projection only'
        if source.name == 'resources.json':
            value = json.loads(raw)
            keys = ('status', 'checks', 'utc', 'sample_seconds', 'capacity_cpus',
                    'host_busy_cpus', 'project_busy_cpus', 'otherwise_available_cpus',
                    'project_cpu_budget', 'quota_used_kib', 'quota_soft_kib', 'quota_hard_kib',
                    'filesystem_free_bytes', 'effective_storage_free_bytes', 'reserve_gib',
                    'expected_growth_gib', 'inodes_free', 'ram_available_bytes', 'policy')
            projected = {key: value[key] for key in keys}
            projected['external_storage'] = {key: value['external_allocation'][key]
                for key in ('available_bytes', 'filesystem_free_bytes', 'inodes_free',
                            'quota_available_bytes', 'reserve_gib', 'expected_growth_gib')}
            data = (json.dumps(projected, indent=2) + '\n').encode()
            method = 'resource metrics only; host/quota-service identity and raw command text withheld'
        elif source.suffix != '.gds':
            text = raw.decode()
            for old, new in [(str(private), '<private-context>'), (str(bulk), '<results>'),
                             (str(ROOT), '<repository>'), ('/work/' + '.' + 'private/', '<private-context>/'),
                             ('.' + 'private/', '<private-context>/')]:
                text = text.replace(old, new)
            data = text.encode()
        assert not forbidden.search(data), str(source)
        if source.suffix == '.json':
            json.loads(data)
        if source.suffix == '.py':
            ast.parse(data.decode())
        destination = a.output / relative; destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        records.append(dict(path=str(relative), original_sha256=digest(raw), exported_sha256=digest(data),
                            original_bytes=len(raw), exported_bytes=len(data), projection=method))

    for group, folder in folders.items():
        base = bulk / folder; assert base.is_dir(), folder
        if group.startswith('stock_'):
            summary = json.loads((base / 'summary.json').read_text())
            assert summary['status'] != 'running'
            assert summary['GDS_sha256'] == 'ab02b653c6b0e29e7693bed55e097081e6e41f67e24c59102494e6fbc1724541'
        for source in sorted(base.rglob('*')):
            if not source.is_file() or source.name.endswith('.progress.jsonl'):
                continue
            if source.suffix == '.odb' or (source.suffix == '.gds' and group in ('initial_serialization_failed', 'retained_frame_candidate')):
                raw = source.read_bytes()
                retained.append(dict(group=group, filename=str(source.relative_to(base)),
                                     sha256=digest(raw), bytes=len(raw), disposition='retained immutable original outside this compact export'))
                continue
            export(source, Path(group) / source.relative_to(base))
    for name in receipts:
        base = private / 'research' / 'verification' / name; assert base.is_dir(), name
        if (base / 'run.json').exists():
            assert json.loads((base / 'run.json').read_text())['status'] != 'running'
        for source in sorted(base.iterdir()):
            if source.is_file() and source.name in ('run.json', 'run.log', 'runner.py', 'resources.json',
                                                  'prelaunch.json', 'prelaunch_failure.json'):
                export(source, Path('receipts') / name / source.name)
    (a.output / 'manifest.json').write_text(json.dumps(dict(
        status='passed portable export; original failures and non-adoption retained',
        records=records, large_immutable_originals_not_duplicated=retained), indent=2) + '\n')
    maps = [ROOT / 'designs/g1-guardian/padframe/README.md',
            ROOT / 'designs/g1-guardian/padframe/bondmap_candidate_20260923.csv']
    paths = sorted([q for q in HERE.iterdir() if q.is_file() and q.suffix in ('.py', '.md')]
                   + [q for q in a.output.rglob('*') if q.is_file()] + maps)
    inventory = []
    for source in paths:
        raw = source.read_bytes(); assert not forbidden.search(raw), str(source)
        inventory.append(dict(path=str(source.relative_to(ROOT)), sha256=digest(raw), bytes=len(raw)))
    result = dict(groups={'outward_bondpad_closure': inventory}, files=len(inventory),
                  bytes=sum(row['bytes'] for row in inventory))
    a.inventory.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'groups'}))


if __name__ == '__main__':
    main()
