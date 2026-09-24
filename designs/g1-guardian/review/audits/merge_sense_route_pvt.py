#!/usr/bin/env python3
"""Validate complete, disjoint frozen SENSE route-PVT shards without re-simulation."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--shards', nargs='+', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
provenance = [json.loads((path/'provenance.json').read_text()) for path in a.shards]
records = [row for path in a.shards for row in json.loads((path/'summary.json').read_text())]
identity_fields = ('candidate_sha256', 'R_P_ohm', 'R_N_ohm', 'gain_limits_V_per_V',
                   'route_scales', 'source_netlist_sha256', 'baseline_summary_sha256', 'ngspice_version')
assert all(all(item[key] == provenance[0][key] for key in identity_fields) for item in provenance)
planned = [name for item in provenance for name in item['planned_tuples']]
assert len(planned) == len(set(planned)) == 108
assert len(records) == 324
keys = [(row['name'], row['scale']) for row in records]
assert len(set(keys)) == 324 and set(keys) == set(itertools.product(planned, (0,1,2)))
expected_corners = set(itertools.product(('tt','ss','ff'), ('typ','bcs','wcs'), (3.0,3.3,3.6), (-40,27,85,125)))
assert {tuple(row['corner']) for row in records} == expected_corners
limits = provenance[0]['gain_limits_V_per_V']
by_scale = {}
for scale in (0,1,2):
    leaves = [row for row in records if row['scale'] == scale]
    complete = [row for row in leaves if row['status'] == 'passed']
    for row in complete:
        assert len(row['rows']) == 9
        assert all(len(values)==11 and all(map(math.isfinite, values)) for values in row['rows'].values())
        gains = [(row['rows'][f't0_c{cm}_s0.05'][0]-row['rows'][f't0_c{cm}_s0'][0])/.05 for cm in (-.1,0,.3)]
        assert min(gains)==row['gain_min'] and max(gains)==row['gain_max']
        assert row['gain_status']==('passed' if min(gains)>=limits[0] and max(gains)<=limits[1] else 'failed')
    failed = [row for row in complete if row['gain_status']=='failed']
    by_scale[scale] = {'leaves':len(leaves), 'complete_OP_points':9*len(complete),
        'numerical_status':'passed' if len(complete)==108 else 'failed',
        'gain_status':'passed' if len(complete)==108 and not failed else 'failed',
        'gain_min_V_per_V':min(row['gain_min'] for row in complete),
        'gain_max_V_per_V':max(row['gain_max'] for row in complete),
        'gain_failed_tuples':[{'name':row['name'],'corner':row['corner'],'gain_min':row['gain_min'],'gain_max':row['gain_max']} for row in failed],
        'zero_shunt_output_V_range':[min(offset['zero_shunt_output_V'] for row in complete for offset in row['offsets']), max(offset['zero_shunt_output_V'] for row in complete for offset in row['offsets'])],
        'worst_CM_zero_output_span_V':max(max(item['zero_shunt_output_V'] for item in row['offsets'])-min(item['zero_shunt_output_V'] for item in row['offsets']) for row in complete)}
zero = [row for row in records if row['scale']==0]
parity = len(zero)==108 and all(row.get('baseline_printed_vectors_exact') is True and row['baseline_printed_vector_max_abs_delta_by_column']==[0]*7 for row in zero)
result = {'status':'passed fixed-LEF-R candidate PVT anchor' if by_scale[1]['gain_status']=='passed' and parity and all(item['numerical_status']=='passed' for item in by_scale.values()) else 'failed',
    'coverage_status':'passed', 'tuples':108, 'leaves':324, 'OP_points':2916,
    'zero_R_baseline_seven_printed_vectors_exact_status':'passed' if parity else 'failed',
    'identity':{key:provenance[0][key] for key in identity_fields}, 'scales':by_scale,
    'inputs':{str(path):{'summary_sha256':sha(path/'summary.json'),'provenance_sha256':sha(path/'provenance.json')} for path in a.shards},
    'script_sha256':sha(Path(__file__)),
    'interpretation':['Scale1 uses original frozen LEF geometry estimate, not target resistance: M2-5 .103 ohm/square and Via1-4 20 ohm/cut equal pinned process-table MAX at reference conditions. Target values are .088 ohm/square and 9 ohm/cut.',
        'Scale2 is diagnostic stress, not a foundry metal-process/temperature bound. Metal TC1 target3500ppm/K does not establish a guaranteed hot bound; via TC is unspecified in this table.',
        'Original source and all printed offsets retained. No fitted pedestal/calibration or resized-SENSE substitution.',
        'Schematic frozen108 MOS/resistor/supply/temperature tuples with ideal rails/VREF/PTAT. Pads, actual BGR, route parasitic C, full route PEX and temperature-dependent metal/via model are not run in this anchor.']}
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({key:result[key] for key in ('status','tuples','leaves','OP_points','zero_R_baseline_seven_printed_vectors_exact_status','scales')},indent=2))
