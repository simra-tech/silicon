#!/usr/bin/env python3
"""Plot retained baseline/candidate simulated distributions; no paired-yield claim."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
HERE=Path(__file__).resolve().parent
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--baseline-runs',required=True);ap.add_argument('--output-prefix',default='array_candidate_comparison_20260922');a=ap.parse_args()
 groups=[('Baseline',a.baseline_runs.split(','),'#334155'),('4× units; quarter-length R',['bgr_array4_density_v2_mc20_20260922_01','bgr_array4_density_v2_mc80_20260922_01'],'#c75d2c'),('4× units; parallel full-length R',['bgr_array4_parallel_r_mc20_20260922_01','bgr_array4_parallel_r_mc80_20260922_01'],'#167d8d')]
 fig,axes=plt.subplots(1,3,figsize=(13.2,4.2));counts=[]
 for label,runs,color in groups:
  rows=[]
  for run in runs:
   p=HERE/'runs'/run/'manifest.json'
   if not p.exists():continue
   m=json.loads(p.read_text());rows.extend((run,r) for r in m['cases'] if r['status']=='passed' and r.get('mm') and r['name'].startswith('mc_'))
  if not rows:continue
  tc=np.array([r['tc_ppm_C'] for _,r in rows]);vr=np.array([r['vref25'] for _,r in rows]);power=[]
  for run,r in rows:
   d=np.loadtxt(HERE/'runs'/run/(r['name']+'.dat'),skiprows=1);power.append(-np.interp(25,d[:,0],d[:,3])*r['vdd']*1e3)
  n=len(rows);fail=int(np.sum(tc>50));counts.append({'label':label,'samples':n,'TC_failures':fail,'runs':runs});axes[0].step(np.sort(tc),np.arange(1,n+1)/n,where='post',color=color,label=f'{label} (n={n}; fail={fail})');axes[1].scatter(vr,tc,s=13,color=color,alpha=.7);axes[2].scatter(power,tc,s=13,color=color,alpha=.7)
 for ax in axes:ax.axhline(50,color='#991b1b',linestyle='--',linewidth=.9) if ax is not axes[0] else ax.axvline(50,color='#991b1b',linestyle='--',linewidth=.9);ax.grid(alpha=.2);ax.spines[['top','right']].set_visible(False)
 axes[0].set(xlabel='Temperature coefficient (ppm/°C)',ylabel='Empirical cumulative fraction',ylim=(0,1.02),title='TC distribution');axes[0].legend(loc='lower right',fontsize=7)
 axes[1].set(xlabel='VREF at 25°C (V)',ylabel='TC (ppm/°C)',title='Reference level and drift');axes[2].set(xlabel='BGR power at 25°C (mW)',ylabel='TC (ppm/°C)',title='Power tradeoff')
 fig.suptitle('Simulated isolated BGR candidates — unchanged baseline retained',fontsize=13);fig.text(.5,.01,'Typical process, 3.3 V; −40…125°C. Added routing/spatial correlation unmodeled; candidate physical checks incomplete.',ha='center',fontsize=8);fig.tight_layout(rect=(0,.06,1,.93));fig.savefig(HERE/(a.output_prefix+'.png'),dpi=170);fig.savefig(HERE/(a.output_prefix+'.svg'));(HERE/(a.output_prefix+'.json')).write_text(json.dumps({'series':counts,'limitations':'No physical silicon yield or adoption; candidates differ in geometry and random-instance population.'},indent=2)+'\n')
if __name__=='__main__':main()
