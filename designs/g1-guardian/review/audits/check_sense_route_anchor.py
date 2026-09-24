#!/usr/bin/env python3
"""Evaluate the existing SENSE 20 +/-0.1 gain requirement in a route-R anchor."""
import argparse
import hashlib
import json
import math
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('directory', type=Path)
a = p.parse_args()
target = a.directory / 'acceptance.json'
assert not target.exists()
summary = json.loads((a.directory / 'summary.json').read_text())
analysis = json.loads((a.directory / 'analysis.json').read_text())
assert len(summary) == 3 and {row['scale'] for row in summary} == {0, 1, 2}
assert all(row['status'] == 'passed' and len(row['rows']) == 9 for row in summary)
assert analysis['control_exact_original_printed_vectors'] is True
assert len(analysis['rows']) == 9
groups = []
for scale in (0, 1, 2):
    rows = [row for row in analysis['rows'] if row['R_scale'] == scale]
    assert len(rows) == 3 and {row['external_average_CM_V'] for row in rows} == {-.1, 0, .3}
    gains = [row['gain_V_V'] for row in rows]
    outputs = [row['output_at_25mV_V'] for row in rows]
    assert all(math.isfinite(v) for v in gains + outputs)
    groups.append({'R_scale': scale, 'gain_min_V_V': min(gains), 'gain_max_V_V': max(gains),
                   'gain_19p9_to_20p1': 'passed' if all(19.9 <= gain <= 20.1 for gain in gains) else 'failed',
                   'CM_output_span_at_25mV_mV': 1000 * (max(outputs) - min(outputs))})
result = {'status': groups[1]['gain_19p9_to_20p1'],
          'scope': 'Simulated nominal schematic TT/3.3V/27C with candidate analytical route R; not PVT/PEX/dynamic qualification.',
          'control_exact_original_printed_vectors': True,
          'printed_precision': 'six significant digits', 'groups': groups,
          'input_sha256': {name: hashlib.sha256((a.directory / name).read_bytes()).hexdigest()
                           for name in ('summary.json', 'analysis.json', 'provenance.json')},
          'CM_acceptance': 'not applicable: descriptive span; no independent span bound assigned in this anchor',
          'scale2_interpretation': 'Diagnostic sensitivity only, not a physical process/temperature bound'}
target.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
assert result['status'] == 'passed'
