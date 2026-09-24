#!/usr/bin/env python3
"""Hash-bound changed-stage coverage of prospective interface windows; no extraction."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
m=json.loads(a.manifest.read_text());assert hashlib.sha256((a.manifest.parent/'g1_chip_top.gds').read_bytes()).hexdigest()==m['candidate_sha256']
pairs={'isense_clock':(615.72,733.92,734.4,29.4),'vref_dac':(711.27,732.,731.52,114.66),'vrefbuf_dac':(705.81,732.96,732.48,118.86),'iptat_isense':(632.73,733.44,733.92,260.82)}
stages=[{'id':index,'net':row['net'],'point_um':row['point_um'],'cut_layer':row['cut_layer'],'changed_bboxes_um':[row['added_cut_bbox_um']]+[metal['landing_bbox_um'] for metal in row['metals']]} for index,row in enumerate(m['via_patches'])]
windows=[];covered=set()
for name,(y,xp,xn,length) in pairs.items():
    bounds=[(xp+xn)/2-12,y-length/2-20,(xp+xn)/2+12,y+length/2+20];inside=[];partial=[]
    for row in stages:
        intersects=any(min(b[2],bounds[2])>max(b[0],bounds[0]) and min(b[3],bounds[3])>max(b[1],bounds[1]) for b in row['changed_bboxes_um'])
        contained=all(bounds[0]<=b[0] and bounds[1]<=b[1] and bounds[2]>=b[2] and bounds[3]>=b[3] for b in row['changed_bboxes_um'])
        if contained:inside.append(row['id']);covered.add(row['id'])
        elif intersects:partial.append(row['id'])
    windows.append({'pair':name,'context_um':24,'end_margin_um':20,'clip_bbox_um':bounds,'fully_captured_stage_ids':inside,'partially_captured_stage_ids':partial,
        'execution_disposition':'first bounded paired delta authorized after stock/core' if name=='isense_clock' else 'not run; separate prospective narrowwindow review; no automaticwide48retry'})
result={'candidate_sha256':m['candidate_sha256'],'parent_candidate_sha256':m['parent_candidate_sha256'],'manifest_sha256':hashlib.sha256(a.manifest.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'interface_preparer_sha256':hashlib.sha256(Path(__file__).with_name('prepare_interface_clip.py').read_bytes()).hexdigest(),'stages':stages,'windows':windows,'all_four_union_fully_captured_ids':sorted(covered),
    'missing_stage_ids':sorted(set(range(21))-covered),'scope':'Bounding-box coverage of all added cuts/landing rectangles, not targetnet connectivity or coupling acceptance. RootlongIPTATwide48 timeout retained; no watchdogextension orwideautomaticretry. Remaininglocalvia-neighborhood clips require physicalnet-target checks.'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print([(row['pair'],row['fully_captured_stage_ids'],row['partially_captured_stage_ids']) for row in windows]);print('missing',result['missing_stage_ids'])
