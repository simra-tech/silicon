#!/usr/bin/env python3
"""Bind actual cut inventory to macro-access coordinates and qualified-scope current evidence."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--inventory',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();assert not a.output.exists()
base=Path(__file__).parent
meshpath=base/'supply-mesh-20260921-r3/mesh.json'
currentpath=base/'current-envelopes-20260922-r1/summary.json'
inventory=json.loads(a.inventory.read_text());mesh=json.loads(meshpath.read_text());currents=json.loads(currentpath.read_text())
assert inventory['def_sha256']==mesh['inputs']['designs/g1-guardian/blocks/g1_padring/flow/runs/assembly-1350/final/def/g1_chip_top.def']
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
nets={row['net']:row for row in inventory['nets']}
def unique_stages(vias):
    stages={}
    for via in vias:
        for stage in via['cut_stages']:
            key=(stage['cut_layer'],tuple(sorted(tuple(box) for box in stage['cut_bboxes_um'])))
            stages[key]=stage
    return list(stages.values())
summary={}
for name,row in nets.items():
    stages=unique_stages(row['vias'])
    summary[name]={'wire_segments':len(row['wires']),'via_sites':len(row['vias']),
        'unique_physical_cut_groups':len(stages),
        'duplicate_cut_group_records_removed':sum(len(via['cut_stages']) for via in row['vias'])-len(stages),
        'unresolved_via_sites':sum(via['status']!='passed' for via in row['vias']),
        'stages_by_layer_and_count':dict(collections.Counter(f"{stage['cut_layer']}:{stage['actual_cut_count']}" for stage in stages)),
        'single_cut_stages':sum(stage['actual_cut_count']==1 for stage in stages),
        'missing_or_uncovered_wire_samples':sum(not wire['centerline_covered'] or any(width is None for width in wire['actual_sampled_width_um']) for wire in row['wires']),
        'smallest_sampled_wire_um':min((width for wire in row['wires'] for width in wire['actual_sampled_width_um'] if width is not None),default=None)}
macro_names={'bgr':'BGR','sense':'SENSE','trip':'TRIP','gate':'GATE_core'}
accesses=[]
for rail,network in mesh['networks'].items():
    for terminal in network['terminals']:
        sites=[terminal['point_um']]+[via['point'] for via in terminal.get('pin_vias',[])]
        actual=[via for via in nets[rail]['vias'] if via['point_um'] in sites]
        unique={(tuple(via['point_um']),via['definition']):via for via in actual}
        actual=list(unique.values());stages=unique_stages(actual)
        current_macro=next((target for source,target in macro_names.items() if ('u_'+source+'/') in terminal['name']),None)
        branch=next((item for item in currents['branches'] if item['macro']==current_macro and item['rail']==rail),None)
        current_diagnostics=[]
        if branch is not None:
            for stage in stages:
                limit=stage['per_cut_table_limit_mA_at105C_11years'];n=stage['actual_cut_count']
                current_diagnostics.append({'layer':stage['cut_layer'],'cuts':n,
                    'assumption':'Apply entire observed macro feed current to this access, separately per access; this is NOT extracted access current or a proven worst-case bound. Equal sharing is diagnostic only.',
                    'windows':{window:{metric:{'observed_macro_total_mA':abs(values[metric])*1000,
                        'table_utilization_if_all_current_in_one_cut':abs(values[metric])*1000/limit,
                        'table_utilization_if_equal_sharing':abs(values[metric])*1000/(limit*n),
                        'table_utilization_equal_sharing_one_cut_open':abs(values[metric])*1000/(limit*(n-1)) if n>1 else None}
                        for metric in ('mean_A','rms_A','sampled_abs_peak_A')} for window,values in branch['windows'].items()}})
        accesses.append({'terminal':terminal['name'],'rail':rail,'stack_point_um':terminal['point_um'],
            'pin_rectangles':terminal.get('pin_rectangles'), 'matched_actual_sites':actual,
            'binding_status':'passed' if actual and all(via['status']=='passed' for via in actual) else 'failed',
            'macro_current_source':None if branch is None else {'macro':branch['macro'],'probe':branch['probe'],'temperature_C':currents['temperature_C'],'run':currents['run']},
            'diagnostic_current_allocations':current_diagnostics,
            'actual_access_current_and_margin_status':'not run; access partition, return currents, waveform applicability and hot/lifetime conditions not qualified',
            'minimum_current_target_mA_equal_sharing':min((stage['branch_mA_at_engineering_target_conditional_equal_sharing'] for stage in stages),default=None),
            'internal_port_to_device_stack':'not run in this top-level inventory'})
result={'status':'inventory analysis complete; EM/current-margin qualification not run','candidate_sha256':inventory['candidate_sha256'],
    'inputs':{str(path):sha(path) for path in (a.inventory,meshpath,currentpath)},'script_sha256':sha(Path(__file__)),
    'nets':summary,'macro_accesses':accesses,
    'current_source_limitations':currents['limitations'],
    'limits':'11 years at105C only; engineering target50% is not a foundry derating. No pulse relaxation, unequal-sharing or125C extrapolation.',
    'remaining':['Pad-internal GATE/IOVDD/IOVSS inventory separate; gate_o is control, not gate-charge output.',
        'Wire sampling is not exhaustive minimum-neck extraction.', 'Local multi-cut bridge survival is not full path one-cut-open simulation.',
        'Macro-internal contacts/port stacks, guards/taps, true per-access/shared-return waveforms and worst-case PVT/activity are not run.']}
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'nets':summary,'macro_accesses':len(accesses),'matched_macro_current_sources':sum(row['macro_current_source'] is not None for row in accesses)},indent=2))
