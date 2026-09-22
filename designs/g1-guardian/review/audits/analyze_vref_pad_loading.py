#!/usr/bin/env python3
"""Summarize retained BGR/AnalogPad DC data; no performance threshold inferred."""
import argparse, hashlib, json, shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--run',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args(); a.output.mkdir(exist_ok=False)
shutil.copyfile(__file__,a.output/'analyzer.py')
root=Path(__file__).resolve().parents[4]
oldpath=root/'designs/g1-guardian/blocks/g1_bgr/sim/qualification/runs/bgr_array_baseline_nominal_20260921_01/nominal.dat'
old=[list(map(float,l.split())) for l in oldpath.read_text().splitlines()[1:]]
d=json.loads((a.run/'manifest.json').read_text());base=d['cases'][0]['rows'];cases=[]
assert len(old)==len(base)==34
assert all(x==y[:4] for x,y in zip(base,old)), 'Original baseline differs'
fig,ax=plt.subplots(1,2,figsize=(11,4.3))
for c in d['cases']:
 r=c['rows']; assert c['status']=='passed' and len(r)==34
 assert all(x[0]==b[0] for x,b in zip(r,base))
 nominal=next(x for x in r if x[0]==25)
 v=[x[1] for x in r]; delta=[x[1]-b[1] for x,b in zip(r,base)]
 s={'name':c['name'],'solver_status':'passed','scope_status':'characterized; no performance limit assigned',
    'temperature_points':len(r),'VREF_25C_V':nominal[1], 'VREF_core_shift_25C_V':nominal[1]-next(x[1] for x in base if x[0]==25),
    'core_TC_box_ppm_C':(max(v)-min(v))/nominal[1]/165*1e6,
    'core_shift_min_V':min(delta),'core_shift_max_V':max(delta),
    'max_abs_core_shift_temperature_C':r[max(range(len(delta)),key=lambda i:abs(delta[i]))][0],
    'wave_sha256':c['wave_sha256']}
 if c['route_mode'] is not None:
  s.update({'pad_25C_V':nominal[3],'pad_input_current_25C_A':nominal[4],
   'pad_input_current_min_A':min(x[4] for x in r),'pad_input_current_max_A':max(x[4] for x in r),
   'external_R_ohm':c['external_R_ohm'],'route_mode':c['route_mode'],
   'supply_25C_A':-nominal[6], 'digital_supply_25C_A':-nominal[7]})
  if c['external_R_ohm'] is None:
   ax[1].plot([x[0] for x in r],[z*1e6 for z in delta],label='Whole-tree R' if c['route_mode'] else 'Ideal route')
 if c['route_mode'] in [None,1]:
  label='Baseline' if c['route_mode'] is None else ('Pad open' if c['external_R_ohm'] is None else f"Pad + {c['external_R_ohm']/1e6:g} MΩ")
  ax[0].plot([x[0] for x in r],v,label=label)
 cases.append(s)
ax[0].set(ylabel='Core VREF (V)',xlabel='Ambient temperature (°C)',title='Nominal models; whole-tree series-R sensitivity')
ax[1].set(ylabel='Core VREF shift (µV)',xlabel='Ambient temperature (°C)',title='Unloaded external pad: modeled leakage effect')
for axt in ax:axt.grid(alpha=.25);axt.legend(fontsize=8)
fig.suptitle('Simulated BGR with stock AnalogPad — DC characterization, not startup qualification')
fig.tight_layout();fig.savefig(a.output/'vref_loading.png',dpi=160);fig.savefig(a.output/'vref_loading.svg')
(a.output/'summary.json').write_text(json.dumps({'baseline_equivalence':'passed: exact first4columns across34temperatures',
 'old_baseline_sha256':hashlib.sha256(oldpath.read_bytes()).hexdigest(), 'cases':cases,
 'scope':d['scope'],'unqualified':['downstream SENSE/T2F electrical loading','startup','process corners','mismatch','package leakage','exact branch RC','performance acceptance']},indent=2)+'\n')
print(json.dumps(cases,indent=2))
