#!/usr/bin/env python3
"""Quick DEF/GDS route dimensions; geometric estimates, never parasitic extraction."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import statistics
import pya

ROOT=Path(__file__).resolve().parents[4];B=ROOT/'designs/g1-guardian/blocks/g1_padring'
METALS={'Metal1':8,'Metal2':10,'Metal3':30,'Metal4':50,'Metal5':67,'TopMetal1':126,'TopMetal2':134}
WANTED={'d_elt_bare','d_std_bare','g_shared_bare','hbt_b_bare','hbt_c_bare','hbt_e_bare','i_core.bgr_r4_33','i_core.t2f_en_33','i_core.t2f_mode_33'}
p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('--nets',help='Comma-separated exact DEF net names; default retains original nine-net audit');a=p.parse_args()
if a.nets:WANTED=set(a.nets.split(','))
if a.output.exists():raise FileExistsError('Preserve prior audit')
gds=B/'layout/g1_chip_top.gds';deffile=B/'flow/runs/assembly-1350/final/def/g1_chip_top.def'
l=pya.Layout();l.read(str(gds));top=l.cell('g1_chip_top');dbu=l.dbu;regions={}
d=deffile.read_text();units=int(re.search(r'UNITS DISTANCE MICRONS (\d+)',d)[1]);sec=re.search(r'^NETS \d+ ;(.*?)^END NETS',d,re.M|re.S)[1]
rows=[]
for entry in re.findall(r'^\s*- (.*?) ;',sec,re.M|re.S):
    name=entry.split()[0]
    if name not in WANTED:continue
    totals=collections.defaultdict(float);segments=[];vias=[]
    endpoints=re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)',entry.split('+')[0])
    for route in re.split(r'(?:\+ ROUTED|\bNEW)\s+',entry)[1:]:
        layer=route.split()[0];coords=list(re.finditer(r'\(\s+([*\d-]+)\s+([*\d-]+)(?:\s+\d+)?\s+\)',route));points=[]
        for q in coords:points.append([points[-1][i] if q[i+1]=='*' else int(q[i+1])/units for i in (0,1)])
        if layer not in regions:regions[layer]=pya.Region(top.begin_shapes_rec(l.layer(METALS[layer],0))).merged()
        for start,end in zip(points,points[1:]):
            assert start[0]==end[0] or start[1]==end[1]
            length=abs(start[0]-end[0])+abs(start[1]-end[1])
            if not length:continue
            totals[layer]+=length;horizontal=start[1]==end[1]
            narrow=pya.Region(pya.DPath([pya.DPoint(*start),pya.DPoint(*end)],2*dbu).to_itype(dbu))
            widths=[];clipped=False
            for fraction in (.25,.5,.75):
                x,y=[start[i]+fraction*(end[i]-start[i]) for i in (0,1)]
                box=pya.DBox(x-dbu,y-10,x+dbu,y+10) if horizontal else pya.DBox(x-10,y-dbu,x+10,y+dbu)
                cross=(regions[layer]&pya.Region(box.to_itype(dbu))).merged();point=pya.DPoint(x,y).to_itype(dbu)
                hits=[poly for poly in cross.each() if poly.inside(point)]
                width=None
                if hits:
                    bounds=hits[0].bbox();width=(bounds.height() if horizontal else bounds.width())*dbu;clipped|=width>=19.998
                widths.append(width)
            valid=[w for w in widths if w is not None];median=statistics.median(valid) if valid else None
            segments.append({'layer':layer,'start_um':start,'end_um':end,'length_um':length,'centerline_covered':(narrow-regions[layer]).is_empty(),
                             'sample_fractions':[.25,.5,.75],'sampled_widths_um':widths,'sample_range_clipped':clipped,
                             'estimated_squares_from_median_width':length/median if median else None})
        if coords:
            tail=route[coords[-1].end():].strip().split()
            if tail and 'via' in tail[0].lower():vias.append({'name':tail[0],'point_um':points[-1]})
    bylayer={}
    for layer,length in totals.items():
        selected=[s for s in segments if s['layer']==layer];widths=[w for s in selected for w in s['sampled_widths_um'] if w is not None]
        bylayer[layer]={'length_um':length,'sampled_width_min_um':min(widths) if widths else None,
                       'sampled_width_median_um':statistics.median(widths) if widths else None,'sampled_width_max_um':max(widths) if widths else None,
                       'estimated_squares':sum(s['estimated_squares_from_median_width'] or 0 for s in selected)}
    rows.append({'net':name,'endpoints':endpoints,'total_length_um':sum(totals.values()),'layers':bylayer,'via_instances':vias,'segments':segments,
                 'centerline_coverage_status':'passed' if segments and all(s['centerline_covered'] for s in segments) else 'failed'})
assert {r['net'] for r in rows}==WANTED
result={'scope':'DEF interconnect with actual GDS width sampling, not PEX or electrical load qualification','tool':pya.__version__,
        'inputs':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (gds,deffile)},'routes':rows,
        'limitations':['Lengths exclude macro-internal, IO-cell and bondpad conductors.','Widths sampled at 25/50/75 percent per DEF segment; pads/junctions can widen a sample.','Squares are L / median sampled width, excluding via/contact resistance and corner corrections.','No capacitance, coupling, substrate or receiver-device load is extracted.']}
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ('net','total_length_um','layers','centerline_coverage_status')} for r in rows],indent=2))
