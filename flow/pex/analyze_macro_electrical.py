#!/usr/bin/env python3
"""Summarize saved macro characterization without inventing acceptance limits."""
import argparse,hashlib,json,math
from pathlib import Path
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('campaign',type=Path);a=ap.parse_args()
root=a.campaign;manifest=json.loads((root/'campaign.json').read_text());block=manifest['options']['block']
def interp(rows,idx,target):
 for p,q in zip(rows,rows[1:]):
  if p[idx]<=target<=q[idx] and q[idx]>p[idx]:
   f=(target-p[idx])/(q[idx]-p[idx]);return [x+f*(y-x) for x,y in zip(p,q)]
 raise ValueError('target not bracketed')
results=[]
for case in manifest['cases']:
 if case['completion']!='passed':results.append(dict(case=case['case'],status='not run to completion'));continue
 p=root/(case['case']+'.tsv');lines=p.read_text().splitlines();header=lines[0].split();rows=[list(map(float,l.split())) for l in lines[1:] if l.strip()];idx={n:i for i,n in enumerate(header)}
 r=dict(case=case['case'],status='characterized; no allocated limit',wave_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 if block=='dut':
  points=[]
  for current in [1e-7,1e-6,8e-6,1e-5,1e-4]:
   try:
    v=interp(rows,idx['i(vm_c)'],current);d=dict(zip(header,v));ib=d['i(vm_b)'];pad_ib=-d['i(vb)'];pad_ic=-d['i(vc)']
    points.append(dict(Ic_A=current,Vbe_intrinsic_V=d['v(b)']-d['v(e)'],Vb_external_V=v[0],Ib_A=ib,beta=current/ib,base_pad_parasitic_A=pad_ib-ib,collector_pad_parasitic_A=pad_ic-current,external_base_relative_error=(pad_ib-ib)/ib))
   except ValueError:points.append(dict(Ic_A=current,status='not bracketed'))
  r['points']=points
  r['max_VCE_V']=max(v[idx['v(c)']]-v[idx['v(e)']] for v in rows)
  r['max_intrinsic_electrical_power_W']=max((v[idx['v(c)']]-v[idx['v(e)']])*v[idx['i(vm_c)']]+(v[idx['v(b)']]-v[idx['v(e)']])*v[idx['i(vm_b)']] for v in rows)
  r['self_heating']='Temperature rise not established; no fixture thermal resistance supplied.'
 elif block=='dose':
  d=dict(zip(header,min(rows,key=lambda r:abs(r[0]))))
  r['zero_gate']=dict(gate_V=d['v(g)'],HV_device_A=d['i(vm_dh)'],LV_device_A=d['i(vm_dl)'],HV_external_A=-d['i(vdh)'],LV_external_A=-d['i(vdl)'],HV_pad_A=-d['i(vdh)']-d['i(vm_dh)'],LV_pad_A=-d['i(vdl)']-d['i(vm_dl)'])
  r['fixture_leakage_sensitivity']=[dict(added_A=x,HV_fraction_of_device=x/max(abs(d['i(vm_dh)']),1e-300),LV_fraction_of_device=x/max(abs(d['i(vm_dl)']),1e-300)) for x in [1e-12,1e-10,1e-9,1e-8]]
 else:
  vdd,vdda=map(float,case['case'].split('_')[2:]);cross={}
  for node,threshold in [('v(in)',vdd/2),('v(out)',vdda/2)]:
   for direction in ['rise','fall']:
    for p,q in zip(rows,rows[1:]):
     u,v=p[idx[node]],q[idx[node]]
     if (direction=='rise' and u<threshold<=v) or (direction=='fall' and u>threshold>=v):
      cross[node+direction]=p[0]+(q[0]-p[0])*(threshold-u)/(v-u);break
  r['rise_delay_s']=cross['v(out)rise']-cross['v(in)rise'];r['fall_delay_s']=cross['v(out)fall']-cross['v(in)fall'];r['output_high_width_s']=cross['v(out)fall']-cross['v(out)rise']
  r['max_supply_current_A']=max(-v[idx['i(vdda)']] for v in rows)
 results.append(r)
dest=root/'characterization.json'
if dest.exists():raise SystemExit('refusing overwrite')
dest.write_text(json.dumps(dict(scope=manifest['scope'],campaign_sha256=hashlib.sha256((root/'campaign.json').read_bytes()).hexdigest(),analyzer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases=results),indent=2)+'\n')
print(dest)
