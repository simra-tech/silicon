#!/usr/bin/env python3
"""Geometry/technology-LEF route RC estimates, explicitly not extracted RC."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'designs/g1-guardian/review/audits/external-routes-20260921.json'
tech=Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef')
dest=ROOT/'designs/g1-guardian/review/audits/external-route-rc-estimates-20260921.json'
if dest.exists():raise SystemExit('refusing overwrite')
text=tech.read_text();layers={}
for name,body in re.findall(r'^LAYER (\S+)\s*\n(.*?)^END \1\s*$',text,re.M|re.S):
    vals={}
    for key,pat in [('sheet_ohm',r'^\s*RESISTANCE RPERSQ (\S+)'),('area_pF_um2',r'^\s*CAPACITANCE\s+CPERSQDIST (\S+)'),('edge_pF_um',r'^\s*EDGECAPACITANCE\s+(\S+)')]:
        m=re.search(pat,body,re.M)
        if m:vals[key]=float(m[1])
    if vals:layers[name]=vals
rows=[]
for route in json.loads(source.read_text())['routes']:
    r=c=0
    for layer,v in route['layers'].items():
        p=layers[layer];length=v['length_um'];width=v['sampled_width_median_um']
        r+=v['estimated_squares']*p['sheet_ohm']
        c+=(length*width*p['area_pF_um2']+2*length*p['edge_pF_um'])*1000
    rows.append(dict(net=route['net'],wire_R_ohm_estimate=r,ground_C_fF_estimate=c,
                     via_count=len(route['via_instances']),
                     note='Via resistance omitted; width median approximation; no coupling, fill, receiver or terminal parasitics.'))
out=dict(scope='Analytical sensitivity estimates only, not sign-off RC',
 input_sha256={str(source.relative_to(ROOT)):hashlib.sha256(source.read_bytes()).hexdigest(),'pdk/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef':hashlib.sha256(tech.read_bytes()).hexdigest()},
 formula='R=sheet*L/W; C=area*L*W+edge*2*L. LEF standard capacitance unit pF; corner and temperature variation not represented.',
 layers=layers,routes=rows)
dest.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
