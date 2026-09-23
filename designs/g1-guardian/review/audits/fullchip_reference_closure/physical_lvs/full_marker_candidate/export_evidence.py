#!/usr/bin/env python3
"""Export the IO marker candidate and immutable failures with portable provenance."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]


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
        'initial_count_failed': 'full-io-marker-20260923-r1',
        'alias_audit': 'full-io-marker-alias-audit-20260923-r1',
        'candidate': 'full-io-marker-20260923-r2',
        'native_lvs_failed': 'full-io-marker-lvs-original-20260923-r1',
        'flatten_worker': 'full-io-marker-flatten-worker-20260923-r1',
        'flatten_proof': 'full-io-marker-flatten-proof-20260923-r1',
        'ports_failed': 'full-io-marker-ports-20260923-r1',
        'layer_inventory': 'full-io-marker-layer-probe-20260923-r1',
        'material_scope': 'full-io-marker-material-20260923-r1',
        'ports_recovered': 'full-io-marker-ports-20260923-r2',
        'dummy_worker': 'full-io-marker-dummy-worker-20260923-r1',
        'dummy_proof': 'full-io-marker-dummy-proof-20260923-r1',
        'comparison_worker_superseded_unrun': 'full-io-marker-comparison-worker-20260923-r1',
        'comparison_worker': 'full-io-marker-comparison-worker-20260923-r2',
        'comparison_original_failed': 'full-io-marker-api-original-20260923-r1',
        'comparison_adapter_failed': 'full-io-marker-api-adapter-20260923-r1',
        'comparison_dummy_failed': 'full-io-marker-api-dummy-20260923-r1',
        'discrepancy_ledger': 'full-io-marker-comparison-audit-20260923-r1',
        'independent_dut_incidence': 'full-io-marker-dut-incidence-20260923-r1',
        'launch_preparation': 'full-io-marker-launch-preparation-20260923-r1',
        'stock_main': 'full-io-marker-main-20260923-r1',
        'stock_maximal': 'full-io-marker-maximal-20260923-r1',
        'stock_antenna': 'full-io-marker-antenna-20260923-r1',
        'stock_density': 'full-io-marker-density-20260923-r1'}
    receipts = [
        'full_io_marker_build_20260923_r1', 'full_io_marker_count_probe_20260923_r1',
        'full_io_marker_hierarchy_probe_20260923_r1', 'full_io_marker_alias_audit_20260923_r1',
        'full_io_marker_build_20260923_r2', 'full_io_marker_lvs_original_20260923_r1',
        'full_io_marker_flatten_20260923_r1', 'full_io_marker_ports_20260923_r1',
        'full_io_marker_layer_probe_20260923_r1', 'full_io_marker_tm2_semantics_20260923_r1',
        'full_io_marker_material_20260923_r1', 'full_io_marker_ports_20260923_r2',
        'full_io_marker_dummy_20260923_r1', 'full_io_marker_api_original_20260923_r1',
        'full_io_marker_api_adapter_20260923_r1', 'full_io_marker_api_dummy_20260923_r1',
        'full_io_marker_dut_incidence_20260923_r1', 'full_io_marker_main_20260923_r1',
        'full_io_marker_maximal_20260923_r1', 'full_io_marker_antenna_20260923_r1',
        'full_io_marker_density_20260923_r1']
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
            assert summary['GDS_sha256'] == 'ae62bf68aa001144c08a37c58ac3553c6e5f2013a6824b340218e84962066aca'
        for source in sorted(base.rglob('*')):
            if not source.is_file() or source.name.endswith('.progress.jsonl'):
                continue
            if source.suffix in ('.odb', '.lvsdb'):
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
    paths = sorted([q for q in HERE.iterdir() if q.is_file() and q.suffix in ('.py', '.md')]
                   + [q for q in a.output.rglob('*') if q.is_file()])
    inventory = []
    for source in paths:
        raw = source.read_bytes(); assert not forbidden.search(raw), str(source)
        inventory.append(dict(path=str(source.relative_to(ROOT)), sha256=digest(raw), bytes=len(raw)))
    result = dict(groups={'source_held_fullchip_io_markers': inventory}, files=len(inventory),
                  bytes=sum(row['bytes'] for row in inventory))
    a.inventory.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'groups'}))


if __name__ == '__main__':
    main()
