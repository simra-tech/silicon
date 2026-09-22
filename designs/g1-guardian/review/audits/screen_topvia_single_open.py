#!/usr/bin/env python3
"""Actual top-two-metal graph alternate paths for unique selected single TopVia2 cuts."""
import argparse
import collections
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
selected={}
for row in inventory['nets']:
    if row['net'] not in ('VDD','VDDA','VSS'):continue
    for via in row['vias']:
        for stage in via['cut_stages']:
            if stage['cut_layer']==133 and stage['actual_cut_count']==1:
                key=tuple(round(value/dbu) for value in stage['cut_bboxes_um'][0])
                if key in selected:assert selected[key]['net']==row['net']
                selected[key]={'net':row['net'],'point_um':via['point_um'],'cut_bbox_um':stage['cut_bboxes_um'][0]}
assert len(selected)==286
metals={layer:list(pya.Region(top.begin_shapes_rec(ly.layer(layer,0))).merged().each()) for layer in (126,134)}
binsize=round(50/dbu);indices={};boxes={};nodes={}
for layer,polygons in metals.items():
    index=collections.defaultdict(list);boxes[layer]=[poly.bbox() for poly in polygons]
    for number,box in enumerate(boxes[layer]):
        nodes[(layer,number)]={'layer':layer,'bbox_um':[v*dbu for v in (box.left,box.bottom,box.right,box.top)]}
        for ix in range(box.left//binsize,box.right//binsize+1):
            for iy in range(box.bottom//binsize,box.top//binsize+1):index[ix,iy].append(number)
    indices[layer]=index
def island(layer,point):
    hits=[number for number in indices[layer][point.x//binsize,point.y//binsize] if boxes[layer][number].contains(point) and metals[layer][number].inside(point)]
    return hits[0] if len(hits)==1 else None
groups={};cut_group={};unassigned=[]
for shape in pya.Region(top.begin_shapes_rec(ly.layer(133,0))).merged().each():
    box=shape.bbox();point=box.center();key=tuple((box.left,box.bottom,box.right,box.top))
    lower=island(126,point);upper=island(134,point)
    if lower is None or upper is None:
        unassigned.append([v*dbu for v in key]);continue
    assert (pya.Region(shape)-pya.Region(metals[126][lower])).is_empty() and (pya.Region(shape)-pya.Region(metals[134][upper])).is_empty()
    pair=((126,lower),(134,upper));group=groups.setdefault(pair,{'count':0});group['count']+=1
    if key in selected:cut_group[key]=pair
assert set(cut_group)==set(selected)
graph=collections.defaultdict(set)
for left,right in groups:graph[left].add(right);graph[right].add(left)
records=[]
for key,row in selected.items():
    left,right=cut_group[key];count=groups[left,right]['count'];previous={left:None};queue=collections.deque([left])
    if count==1:
        while queue and right not in previous:
            node=queue.popleft()
            for adjacent in graph[node]:
                if {node,adjacent}=={left,right}:continue
                if adjacent not in previous:previous[adjacent]=node;queue.append(adjacent)
    alternate=right in previous;path=[]
    if alternate:
        node=right
        while node is not None:path.append(list(node));node=previous[node]
        path.reverse()
    records.append({**row,'all_actual_cuts_between_same_two_upper_metal_plates':count,
        'local_parallel_cut_survival':count>1,'alternate_upper_metal_path_exists':alternate,
        'alternate_path_nodes':path,'status':'passed local parallel bridge' if count>1 else ('passed upper-metal alternate path' if alternate else 'not run: no alternate upper-only path; lower metals omitted'),
        'current_redistribution_margin':'not run; geometric connectivity does not establish current/R-drop margin after cut loss'})
result={'candidate_sha256':manifest['candidate_sha256'],'inventory_sha256':hashlib.sha256(a.inventory.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'scope':'Actual merged TopMetal1/TopMetal2 drawing islands connected only by fully landed actualTopVia2 cuts. One selected cut unavailable; same-plate parallel cuts or explicit graph alternate path is positive connectivity evidence. No lower-metal paths are considered: a negative upper-only result is NOT a full-chip disconnect proof. No current sharing, resistance, electromigration or yield qualification.',
    'metal_islands':{str(layer):len(polygons) for layer,polygons in metals.items()},'cut_groups':len(groups),'unassigned_cut_bboxes_um':unassigned,
    'summary':dict(collections.Counter(row['status'] for row in records)), 'records':records,
    'graph_nodes':{f'{key[0]}:{key[1]}':value for key,value in nodes.items()},
    'graph_edges':[{'lower':list(left),'upper':list(right),'actual_cut_count':group['count']} for (left,right),group in groups.items()]}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']))
