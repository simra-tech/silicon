#!/usr/bin/env python3
"""Conservative local1x2 via placement feasibility; no geometry mutation or DRC pass."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pya
from sense_route_manifest import load_candidate_resistances
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();assert not a.output.exists();assert len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
manifest,_=load_candidate_resistances(a.manifest);inventory=json.loads(a.inventory.read_text());assert inventory['candidate_sha256']==manifest['candidate_sha256']
ly=pya.Layout();ly.read(str(a.manifest.parent/'g1_chip_top.gds'));top=ly.cell('g1_chip_top');dbu=ly.dbu
def region(layer,datatype,box):return (pya.Region(top.begin_shapes_rec_overlapping(ly.layer(layer,datatype),box)) & pya.Region(box)).merged()
def bounds(poly):
    box=poly if isinstance(poly,pya.Box) else poly.bbox()
    return [value*dbu for value in (box.left,box.bottom,box.right,box.top)]
results=[]
for net in inventory['nets']:
    if net['net'] in ('VDD','VDDA','VSS','IOVDD','IOVSS','GATE'):continue
    for via in net['vias']:
        for stage in via['cut_stages']:
            if stage['actual_cut_count']!=1:continue
            box=pya.DBox(*stage['cut_bboxes_um'][0]).to_itype(dbu);assert box.width()==190 and box.height()==190 and dbu==.001
            center=box.center();options=[]
            for dx,dy in ((.41,0),(-.41,0),(0,.41),(0,-.41)):
                moved=box.moved(round(dx/dbu),round(dy/dbu));landing=(box+moved).enlarged(round(.05/dbu));query=landing.enlarged(round(.35/dbu))
                cut_region=region(stage['cut_layer'],0,query)-pya.Region(box)
                cut_spacing_clear=(cut_region & pya.Region(moved).sized(round(.22/dbu))).is_empty()
                layers=[]
                for layer in (stage['lower_layer'],stage['upper_layer']):
                    actual=region(layer,0,query);hits=[shape for shape in actual.each() if shape.inside(center)]
                    assert len(hits)==1
                    own=pya.Region(hits[0]);others=actual-own;clearance=pya.Region(landing).sized(round(.21/dbu))
                    conflicts=others & clearance;fill=region(layer,22,query) & pya.Region(landing).sized(round(.30/dbu))
                    layers.append({'layer':layer,'landing_bbox_um':bounds(landing),'local_distinct_metal_conflicts_um':[bounds(shape) for shape in conflicts.each()],
                        'added_metal_area_um2':(pya.Region(landing)-actual).area()*dbu*dbu,
                        'fill_keepout_intersection_area_um2':fill.area()*dbu*dbu,
                        'existing_cut_fully_covered':(pya.Region(box)-own).is_empty()})
                metal_clear=all(not row['local_distinct_metal_conflicts_um'] for row in layers)
                options.append({'added_cut_offset_um':[dx,dy],'added_cut_bbox_um':bounds(moved),'cut_spacing_clear':cut_spacing_clear,'metals':layers,
                    'status':'feasible local spacing, fill review required' if metal_clear and cut_spacing_clear and any(row['fill_keepout_intersection_area_um2'] for row in layers) else ('feasible local spacing' if metal_clear and cut_spacing_clear else 'blocked local spacing')})
            feasible=[row for row in options if row['status'].startswith('feasible')]
            results.append({'net':net['net'],'via_definition':via['definition'],'point_um':via['point_um'],'cut_layer':stage['cut_layer'],
                'existing_cut_bbox_um':stage['cut_bboxes_um'][0],'options':options,'feasible_options':len(feasible),
                'provisional_best_option':None if not feasible else min(feasible,key=lambda row:(sum(item['fill_keepout_intersection_area_um2'] for item in row['metals']),sum(item['added_metal_area_um2'] for item in row['metals']))),
                'one_cut_open_after_proposed_pair':'local common rectangular landing would retain one bridge; physical candidate/global path check not run',
                'current_RC_disposition':'not run; root current/impedance assignment and affected electrical check needed; no blind implementation'})
assert len(results)==31
result={'candidate_sha256':manifest['candidate_sha256'],'inventory_sha256':hashlib.sha256(a.inventory.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'scope':'Conservative local geometric screening only. Existing cut retained; one additional.19um cut at.41um pitch in four axial directions, .05um metal enclosure,.21um distinct-metal spacing,.22um cut spacing,.30um fill keepout. Same-layer components clipped to local window: remotely connected same-net metal can be conservatively treated as obstacle. This is NOT stock DRC, antenna, density, LVS, current-margin or coupling acceptance.',
    'results':results,'summary':{'single_cut_sites':31,'sites_with_local_option':sum(row['feasible_options']>0 for row in results),'sites_blocked_all_four':sum(row['feasible_options']==0 for row in results)}}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']))
