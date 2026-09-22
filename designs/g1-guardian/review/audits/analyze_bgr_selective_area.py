#!/usr/bin/env python3
"""Read-only selective BGR footprint arithmetic using existing audited native GDS units."""
import argparse,collections,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
base=Path(__file__).resolve().parent;root=Path(__file__).resolve().parents[4]
inventory_path=base/'bgr-array-area-20260922-r2/inventory.json';summary_path=base/'bgr-array-area-20260922-r2/summary.json'
manifest_path=root/'designs/g1-guardian/blocks/g1_bgr/sim/qualification/candidates/bgr_selective_loop16/manifest.json'
source_path=root/'designs/g1-guardian/blocks/g1_bgr/sim/postlayout/g1_bgr_pex.spice'
generator_path=root/'designs/g1-guardian/blocks/g1_bgr/layout/g1_bgr_layout.py'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
inventory=json.loads(inventory_path.read_text());prior=json.loads(summary_path.read_text());manifest=json.loads(manifest_path.read_text())
assert sha(source_path)==prior['source_netlist_sha256']==manifest['source_sha256']=='72417e072003d2ce28a108c47ef6ac86927ce6c6f89f3a614f360165a31c9d77'
assert inventory['gds_sha256']==sha(root/'designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top.gds')
units={row['name']:row for row in prior['scaled_units']};loop=manifest['replicated_original_instances'];qref=['XQ60','XM43','XM44','XM51']+[f'XR{i}' for i in range(17,23)]
q1q2=['XQ56']+[f'XQ{i}' for i in range(68,75)]+['XQ76']
assert len(loop)==40 and len(qref)==10 and len(q1q2)==9 and not set(loop)&set(qref)
assert collections.Counter(name[:2] for name in loop)=={'XM':13,'XQ':12,'XR':15}
def group(names):
    return {'instances':[units[name] for name in names],'count_by_kind':dict(collections.Counter(units[name]['kind'] for name in names)),
        'native_bbox_sum_um2':sum(units[name]['bbox_area_um2'] for name in names)}
groups={'selective_loop_unit':group(loop),'Qref_unit':group(qref),'Q1_Q2_unit':group(q1q2)}
native=prior['baseline_all_PCell_bbox_sum_um2'];overhead=prior['baseline_macro_to_bbox_ratio'];proposals={}
for label,loop_scale,qref_scale in [('selective16',16,1),('selective32_Qref4',32,4)]:
    count=(loop_scale-1)*len(loop)+(qref_scale-1)*len(qref)
    area=native+(loop_scale-1)*groups['selective_loop_unit']['native_bbox_sum_um2']+(qref_scale-1)*groups['Qref_unit']['native_bbox_sum_um2']
    proposals[label]={'added_units':count,'native_bbox_sum_um2':area,'baseline_overhead_extrapolation_um2':area*overhead,
        'ratio_to_local_envelope_by_bbox':area/prior['local_envelope_area_um2']}
for scale in (8,16,32):
    area=native+(scale-1)*groups['Q1_Q2_unit']['native_bbox_sum_um2']
    proposals[f'Q1_Q2_only{scale}']={'added_units':(scale-1)*9,'native_bbox_sum_um2':area,'baseline_overhead_extrapolation_um2':area*overhead,
        'electrical_adequacy':'not run; width/currentdensity preservation is not a TC acceptance result'}
source_lines={line.split()[0]:line for line in source_path.read_text().splitlines() if line.startswith('X')}
res_names=[name for name in loop if name.startswith('XR')]
length_sum=sum(float(re.search(r'\bl=([\d.]+)u',source_lines[name])[1]) for name in res_names)
assert length_sum==743.5
resistor_pitch_screen={'retained_generator_pitch_um':1.9,'pitch_is_foundry_minimum':False,'loop32_body_only_pitch_footprint_um2':32*1.9*length_sum,
    'loop32_native_head_height_pitch_footprint_um2':32*1.9*sum(units[name]['height_um'] for name in res_names),
    'Qref4_native_head_height_pitch_footprint_um2':4*1.9*sum(units[name]['height_um'] for name in qref if name.startswith('XR')),
    'scope':'Retains current straightresistor pitch and full length; not an optimum packing or minimum legal pitch claim. Native height includes contact heads, but externalstraps,dummies,guard,routing remain omitted.'}
result={'status':'footprint arithmetic complete; physical fit and electrical adequacy not established','inputs':{str(path.relative_to(root)):sha(path) for path in (inventory_path,summary_path,manifest_path,source_path,generator_path)},
    'groups':groups,'proposals':proposals,'resistor_pitch_screen':resistor_pitch_screen,'local_envelope_um':prior['local_envelope_um'],'local_envelope_um2':prior['local_envelope_area_um2'],
    'baseline_macro_um2':prior['baseline_macro_um2'],'baseline_native_bbox_sum_um2':native,'baseline_die_area_mm2':1.8225,'owner_die_area_budget_mm2':2.0,
    'limitations':['Native bbox sums include installedPCell contacts/implants/wells, but can overlap legally; they are not rigorous packing lower bounds.',
        'Existing local envelope36888um2 is neighboringmacro/ring-limited and contains existingdecaps/PDN/routes; no new floorplan movement or larger envelope authorized here.',
        'Extra MOSgatecontacts/bodyties, HBT externalrings, arraydummies, guardclearance and routing not fully included; baselineoverhead is an extrapolation only.',
        'At retained1.9um pitch loop32 resistor bodies alone exceed the entire local envelope, before Qref/HBT/MOS/guards. A broader floorplan tradeoff or different mechanism is required before claiming fit.',
        'The difference between2mm2budget and1.8225mm2die is not freely available core area; any die/ring/macro changes need explicit coordinated layout and checks.',
        'No sourcecandidate, geometry, PDKmodel or deck changed; no newPEX or circuit simulation.']}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({key:result[key] for key in ('status','proposals','resistor_pitch_screen','local_envelope_um2')},indent=2))
