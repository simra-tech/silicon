#!/usr/bin/env python3
"""Two proven T2F feed-open sites: local TopVia2 pair feasibility without layout mutation."""
import argparse,hashlib,json,os
from pathlib import Path
import pya
from sense_route_manifest import load_candidate_resistances
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--open-probe',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
m,_=load_candidate_resistances(a.manifest);probe=json.loads(a.open_probe.read_text());assert probe['candidate_sha256']==m['candidate_sha256']
targets=[row for row in probe['results'] if not row['all_recorded_macro_accesses_connected_to_source']];assert len(targets)==2
ly=pya.Layout();ly.read(str(a.manifest.parent/'g1_chip_top.gds'));top=ly.cell('g1_chip_top');dbu=ly.dbu;assert dbu==.001
def coords(box):return [value*dbu for value in (box.left,box.bottom,box.right,box.top)]
def local(layer,datatype,window):return (pya.Region(top.begin_shapes_rec_overlapping(ly.layer(layer,datatype),window))&pya.Region(window)).merged()
results=[]
for target in targets:
    old=pya.DBox(*target['cut_bbox_um']).to_itype(dbu);options=[]
    for dx,dy in ((1960,0),(-1960,0),(0,1960),(0,-1960)):
        new=old.moved(dx,dy);landing=(old+new).enlarged(650);window=landing.enlarged(3500)
        cuts=local(133,0,window)-pya.Region(old);cutclear=(cuts&pya.Region(new).sized(1060)).is_empty();metals=[]
        for layer,clearance in ((126,2000),(134,3000)):
            actual=local(layer,0,window);own=[shape for shape in actual.each() if shape.inside(old.center())];assert len(own)==1
            conflicts=(actual-pya.Region(own[0]))&pya.Region(landing).sized(clearance)
            fill=local(layer,22,window)&pya.Region(landing).sized(clearance)
            metals.append({'layer':layer,'landing_bbox_um':coords(landing),'distinct_metal_conflicts':[coords(shape.bbox()) for shape in conflicts.each()],
                'added_metal_area_um2':(pya.Region(landing)-actual).area()*dbu**2,'fill_keepout_area_um2':fill.area()*dbu**2,'clearance_screen_um':clearance*dbu})
        options.append({'added_cut_offset_um':[dx*dbu,dy*dbu],'added_cut_bbox_um':coords(new),'metals':metals,'cut_spacing_clear':cutclear,
            'status':'feasible local spacing' if cutclear and all(not row['distinct_metal_conflicts'] for row in metals) else 'blocked local spacing'})
    feasible=[row for row in options if row['status'].startswith('feasible')]
    results.append({'net':target['net'],'point_um':target['point_um'],'old_cut_bbox_um':target['cut_bbox_um'],'isolated_macro_accesses':[row for row in target['macro_access_probes'] if not row['connected_to_source']],
        'options':options,'provisional_best_option':None if not feasible else min(feasible,key=lambda row:(sum(metal['fill_keepout_area_um2'] for metal in row['metals']),sum(metal['added_metal_area_um2'] for metal in row['metals']))),
        'feasible_options':len(feasible)})
result={'candidate_sha256':m['candidate_sha256'],'open_probe_sha256':hashlib.sha256(a.open_probe.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'scope':'Retain original.9um cut; addone at1.96um pitch,1.06um cutgap. Landing minor width2.2um gives.65um enclosure on bothmetals above.5um minimum and avoids subminimumTM2 width. Conservativelocaldistinctmetal spacing2umTM1/3umTM2; notstockDRC, allwidth-dependent rules, currentsharing or coupling signoff.',
    'results':results,'stock_checks':'not run'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print([(row['net'],row['feasible_options']) for row in results])
