#!/usr/bin/env python3
"""Assess completion and settling of retained pad+10nF BGR transient cases."""
import argparse,hashlib,json,shutil
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False);shutil.copyfile(__file__,a.output/'analyzer.py');aud=Path(__file__).resolve().parent
runs=[aud/f'vref-pad-dynamic-20260922-r{i}' for i in [1,2,3]];targets={};allrows=[];waves={};records=[]
for run in runs:
 for c in json.loads((run/'manifest.json').read_text())['cases']:
  rec=dict(c,run=run.name);leaf=run/c['name'];state=json.loads((leaf/'run.json').read_text());rec['last_reported_sim_time_s']=state.get('last_reported_sim_time_s');rec['timed_out']=state.get('timed_out',state.get('status')=='timed_out');wave=leaf/'wave.tsv'
  if wave.exists():
   w=np.loadtxt(wave,skiprows=1);assert len(w)==c['rows'] and np.isfinite(w).all();rec['time_strictly_increasing']=bool(np.all(np.diff(w[:,0])>0));assert rec['time_strictly_increasing'];waves[(run.name,c['name'])]=w
   if c['case']=='load':targets[c['temperature_C']]=w[0,[1,3]]
  records.append(rec)
fig,axes=plt.subplots(1,3,figsize=(13,4.2));colors={-40.0:'tab:blue',27.0:'tab:orange',125.0:'tab:red'}
for r in records:
 key=(r['run'],r['name'])
 if key not in waves:continue
 w=waves[key];target=targets[r['temperature_C']];r['target_core_pad_V']=target.tolist();r['core_min_max_V']=[float(w[:,1].min()),float(w[:,1].max())];r['pad_min_max_V']=[float(w[:,3].min()),float(w[:,3].max())];r['final_core_pad_error_V']=(w[-1,[1,3]]-target).tolist();r['core_min_max_delta_V']=(np.array(r['core_min_max_V'])-target[0]).tolist();r['pad_min_max_delta_V']=(np.array(r['pad_min_max_V'])-target[1]).tolist()
 if r['case']=='startup':
  r['settling_characterization_s']={}
  for fraction in [.01,.001]:
   ok=np.abs(w[:,3]-target[1])<=fraction*abs(target[1]);after=np.logical_and.accumulate(ok[::-1])[::-1];inds=np.flatnonzero(after);r['settling_characterization_s'][str(fraction)]=float(w[inds[0],0]) if len(inds) else None
  if r['run'].endswith('r3'):axes[2].plot(w[:,0]*1e3,w[:,3],label=f"{r['temperature_C']:g}°C",color=colors[r['temperature_C']])
 else:
  i=0 if r['case']=='load' else 1;axes[i].plot(w[:,0]*1e3,(w[:,3]-target[1])*(1e3 if i==0 else 1e6),color=colors[r['temperature_C']],label=f"{r['temperature_C']:g}°C")
for i,ax in enumerate(axes):ax.grid(alpha=.25);ax.set_xlabel('Time (ms)');ax.legend(fontsize=8)
axes[0].set(title='External100nA load pulse',ylabel='External pad change (mV)');axes[1].set(title='3.3→3.0→3.3V supply dip',ylabel='External pad change (µV)');axes[2].set(title='1ms supply ramp;20ms observation',ylabel='External pad voltage (V)');axes[2].text(.96,.15,'125°C startup: timeout\n586µs last log; no waveform',transform=axes[2].transAxes,ha='right',fontsize=8,color='tab:red')
fig.suptitle('Simulated canonical BGR + stock AnalogPad +10nF: nominal models, estimated shared-routeR');fig.tight_layout();fig.savefig(a.output/'vref_dynamic.png',dpi=150);fig.savefig(a.output/'vref_dynamic.svg')
(a.output/'summary.json').write_text(json.dumps({'scope':'Selected transistor-level responses; dynamic acceptance limits not assigned. Settling bands1%/.1% are descriptive and require staying within through endpoint only.','cases':records},indent=2)+'\n')
for r in records:print(json.dumps(r))
