#!/usr/bin/env python3
"""Separate metal-backed rail probes from off-metal text coordinates without hiding either."""
import argparse
import hashlib
import json
from pathlib import Path
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('input', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args(); assert not a.output.exists()
source = json.loads(a.input.read_text())
local = source['standalone_probes']
valid = {(row['layer'], tuple(row['point_um'])) for row in local if row['physical_net']}
clusters = {tuple(sorted(row['physical_net'].items())) for row in local if row['physical_net']}
assert len(valid) == 10 and len(clusters) == 2
rows = []
for instance in source['assembled_instances']:
    probes = [row for row in instance['probes'] if (row['layer'], tuple(row['local_point_um'])) in valid]
    assert len(probes) == len(valid) and all(row['physical_net'] for row in probes)
    nets = {tuple(sorted(row['physical_net'].items())) for row in probes}
    rows.append({'instance_transform': instance['instance_transform'], 'metal_backed_probe_count': len(probes),
                 'top_physical_clusters': [dict(net) for net in nets], 'status': 'passed' if len(nets) == 1 else 'failed'})
result = {'scope': 'Two distinct standalone metal-backed IOVDD rail groups are joined after placement. Off-metal text coordinates remain unresolved probe locations, not discarded failures or physical disconnections. Not full IO LVS or all-device-terminal coverage.',
          'source_sha256': hashlib.sha256(a.input.read_bytes()).hexdigest(), 'candidate_sha256': source['candidate_sha256'],
          'standalone_distinct_metal_clusters': len(clusters), 'metal_backed_probes_each_pad': len(valid),
          'off_metal_standalone_text_points': [row for row in local if not row['physical_net']],
          'assembled_instances': rows, 'rail_group_joining_status': 'passed' if all(row['status'] == 'passed' for row in rows) else 'failed',
          'off_metal_text_location_resolution': 'not run', 'full_IO_LVS': 'failed; independent prior result unchanged'}
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
