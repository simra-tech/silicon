#!/usr/bin/env python3
"""Exact reversible source-only three-PMOS projection for OSC R0.95 LVS.

The canonical source is never replaced. New-GDS native dummy extraction and
strict stock LVS remain separate checks; this output is comparison-only.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parents[2]/'review/audits/io_tap_closure/physical_source'
sys.path.insert(0, str(PARENT))
import prepare_current_dummy_reference as old

CANON_SHA = '126acd51cae404f55e9a3470d521d0d90f5115e668fbf393ac48c492e4507333'
OLD_CANON_SHA = '94e50a2a7f0646282f4499831bcfe03a2cf8871fbc33a7549b6e8f94fded207b'
OLD_PROJECTED_SHA = '9f38371f303672a7169733493c9d444cacbda2d5889e0f79659b5e1224490369'
SOURCE_REPORT_SHA = '16fd7356b220e6942a06e8fbce9c092a4378ffa87fb14d36333ebb26c53862a8'
GEOMETRY_SHA = '18b897feb06b7a02508ea8734d40845d69bcb515955368daba9dd1938a1949c9'
GEOMETRY_REPORT_SHA = 'b0fcf94e29a5fa53f470803fd4e8041efb3222ce423b19094134ec6b973b5243'
OLD_NATIVE_PROOF_SHA = 'd9be7112004e2bed148da9ff63f74c4f0375ed42c0109bca5e1f87c0af9224aa'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def project(canonical, old_canonical, old_projected, source_report,
            geometry, geometry_report, old_native_proof):
    assert sha(canonical) == CANON_SHA and sha(old_canonical) == OLD_CANON_SHA
    assert sha(old_projected) == OLD_PROJECTED_SHA
    assert sha(source_report) == SOURCE_REPORT_SHA
    assert sha(geometry) == GEOMETRY_SHA and sha(geometry_report) == GEOMETRY_REPORT_SHA
    assert sha(old_native_proof) == OLD_NATIVE_PROOF_SHA
    source_info = json.loads(Path(source_report).read_text())
    geom_info = json.loads(Path(geometry_report).read_text())
    old_dummy = json.loads(Path(old_native_proof).read_text())
    assert source_info['source_sha256'] == OLD_CANON_SHA and source_info['candidate_sha256'] == CANON_SHA
    assert len(source_info['substitutions']) == 2 and {r['before'].split()[0] for r in source_info['substitutions']} == {'RRA', 'RRB'}
    assert geom_info['GDS_sha256'] == GEOMETRY_SHA and geom_info['preserved_other_cells'] == 305
    assert geom_info['preserved_target_fill_instances'] == 58
    assert old_dummy['status'] == 'passed independent three-dummy source/native-terminal proof'
    before = Path(canonical).read_bytes()
    old_bytes = Path(old_canonical).read_bytes()
    for row in source_info['substitutions']:
        first, second = row['before'].encode(), row['after'].encode()
        assert old_bytes.count(first) == 1 and before.count(second) == 1
        before = before.replace(second, first)
    assert before == old_bytes, 'New canonical source differs beyond two OSC charging resistor lengths'
    raw = Path(canonical).read_bytes()
    lines, cells = old.parse(raw)
    flat_before, _ = old.flattened(cells)
    cell = cells['G1_VSS_DERIVATIVE__SG13G2_LEVELDOWN']
    inst, = [i for i in cell['instances'] if i['name'].upper() == 'MP0']
    assert inst['model'].upper() == 'SG13_HV_PMOS'
    assert [node.upper() for node in inst['nodes']] == ['VDD']*4
    assert inst['params'] == ['m=1', 'w=4.65u', 'l=450.00n', 'ng=1']
    index, = inst['record']['indices']
    line = lines[index].encode()
    offset = sum(len(item.encode()) for item in lines[:index])
    projected = raw[:offset] + raw[offset+len(line):]
    assert projected[:offset] + line + projected[offset:] == raw
    _, projected_cells = old.parse(projected)
    flat_after, _ = old.flattened(projected_cells)
    removed = {path: flat_before[path] for path in set(flat_before)-set(flat_after)}
    assert old.allowed(removed) and len(removed) == 3
    assert all(flat_after[path] == flat_before[path] for path in flat_after)
    assert cells[old.TOP]['pins'] == projected_cells[old.TOP]['pins'] and len(cells[old.TOP]['pins']) == 22
    # Existing comparison reference may differ only by the two source-level
    # resistor lengths; this does not inherit old native GDS extraction.
    recovered = projected
    for row in source_info['substitutions']:
        first, second = row['before'].encode(), row['after'].encode()
        assert recovered.count(second) == 1
        recovered = recovered.replace(second, first)
    assert recovered == Path(old_projected).read_bytes()
    return projected, dict(status='passed exact reversible source-only three-dummy projection; new native proof and stock LVS not run',
                           canonical_source_sha256=CANON_SHA, projected_source_sha256=hashlib.sha256(projected).hexdigest(),
                           old_canonical_source_sha256=OLD_CANON_SHA, old_projected_source_sha256=OLD_PROJECTED_SHA,
                           new_geometry_sha256=GEOMETRY_SHA, geometry_report_sha256=GEOMETRY_REPORT_SHA,
                           source_report_sha256=SOURCE_REPORT_SHA, old_native_dummy_proof_sha256=OLD_NATIVE_PROOF_SHA,
                           removed=removed, removed_record=line.decode(), offset=offset,
                           all_other_source_primitives_parameters_and_pins_held=True,
                           reverse_bytes_exact=True, source_projection_is_not_canonical=True,
                           new_native_dummy_proof='not run', strict_stock_lvs='not run')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('canonical', 'old_canonical', 'old_projected', 'source_report',
                 'geometry', 'geometry_report', 'old_native_proof'):
        ap.add_argument('--'+name.replace('_', '-'), type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    args = ap.parse_args()
    assert not args.output_dir.exists()
    projected, report = project(*(getattr(args, name) for name in
        ('canonical', 'old_canonical', 'old_projected', 'source_report',
         'geometry', 'geometry_report', 'old_native_proof')))
    args.output_dir.mkdir(parents=True)
    (args.output_dir/'physical_AP_three_dummy_comparison_only.cdl').write_bytes(projected)
    (args.output_dir/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ('status', 'projected_source_sha256', 'new_native_dummy_proof', 'strict_stock_lvs')}))


if __name__ == '__main__':
    main()
