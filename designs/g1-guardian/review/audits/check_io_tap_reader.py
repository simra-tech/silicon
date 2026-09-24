#!/usr/bin/env python3
"""Check reader binding and original node/A/P preservation against source CDL."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('directory', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()
report = json.loads((a.directory / 'stock_reader.json').read_text())
rows = {(row['cell'], row['variant']): row for row in report['rows']}
results = []
for cell in ('sg13g2_Filler400', 'sg13g2_LevelUpInv', 'sg13g2_RCClampInverter'):
    original_path = a.directory / (cell + '_original.cdl')
    expected = {}
    for line in original_path.read_text().splitlines():
        if not re.match(r'^X\S+\s+\S+\s+\S+\s+ptap1\b', line, re.I):
            continue
        tokens = line.split()
        params = dict(token.split('=', 1) for token in tokens[4:])
        def scaled(text, scale):
            match = re.fullmatch(r'([0-9.]+)([fpnu]?)', text)
            assert match
            return float(match[1]) * {'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, '': 1}[match[2]] * scale
        expected['_G1_BIND_' + tokens[0]] = {
            'area_um2': scaled(params['A'], 1e12), 'perimeter_um': scaled(params['P'], 1e6),
            'tie': tokens[1].upper(), 'well': tokens[2].upper()}
    original = rows[cell, 'original']
    normalized = rows[cell, 'normalized']
    assert hashlib.sha256(original_path.read_bytes()).hexdigest() == original['input_sha256']
    for phase in ('before_simplify', 'after_simplify'):
        orig_devices = [dev for circuit in original[phase] for dev in circuit['devices']]
        norm_devices = [dev for circuit in normalized[phase] for dev in circuit['devices']]
        orig_taps = [dev for dev in orig_devices if dev['model'].lower() == 'ptap1']
        norm_taps = {dev['name']: dev for dev in norm_devices if dev['model'].lower() == 'ptap1'}
        assert not orig_taps and set(norm_taps) == set(expected)
        for name, params in expected.items():
            for key, value in params.items():
                actual = norm_taps[name][key]
                assert (math.isclose(actual, value, rel_tol=1e-12, abs_tol=1e-12)
                        if isinstance(value, float) else actual == value), (name, key, actual, value)
        assert sorted((dev['name'], dev['model']) for dev in orig_devices) == sorted(
            (dev['name'], dev['model']) for dev in norm_devices if dev['model'].lower() != 'ptap1')
    if cell == 'sg13g2_Filler400':
        assert original['after_simplify'] == []
    results.append({'cell': cell, 'status': 'passed', 'source_taps_preserved_after_normalization': expected,
                    'original_taps_bound': 0, 'normalized_taps_bound': len(expected),
                    'non_tap_device_identity_preserved': True})
result = {'status': 'passed', 'reader_report_sha256': hashlib.sha256((a.directory / 'stock_reader.json').read_bytes()).hexdigest(),
          'scope': 'Source-derived reader binding only; original electrical A/P and node intent retained, no layout equivalence inferred.',
          'cells': results, 'stock_LVS': 'not run'}
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
