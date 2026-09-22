#!/usr/bin/env python3
"""Compare archived controlled solver runs, preserving analog errors and transitions."""
import argparse,json
from pathlib import Path
import numpy as np
SIM=Path(__file__).resolve().parent

def crossings(a,col):
 x=a[:,col]-.6;ii=np.flatnonzero(x[:-1]*x[1:]<0)
 return [{'time_s':float(a[i,0]-x[i]*(a[i+1,0]-a[i,0])/(x[i+1]-x[i])),'rising':bool(x[i+1]>x[i])} for i in ii]
def compare(candidate):
 d=SIM/'qualification'/candidate;preflight='controlled_profile_preflight.json' if (d/'controlled_profile_preflight.json').exists() else 'controlled_solver_preflight.json';p=json.loads((d/preflight).read_text());ref=SIM/'qualification'/p['reference_run']
 x=json.loads((ref/'summary.json').read_text())[0];y=json.loads((d/'summary.json').read_text())[0]
 a=np.loadtxt(next(ref.glob('*.dat')),skiprows=1);b=np.loadtxt(next(d.glob('*.dat')),skiprows=1)
 grid=np.linspace(0,min(a[-1,0],b[-1,0]),52001);aa=np.column_stack([np.interp(grid,a[:,0],a[:,i]) for i in range(1,a.shape[1])]);bb=np.column_stack([np.interp(grid,b[:,0],b[:,i]) for i in range(1,b.shape[1])])
 header=next(d.glob('*.dat')).read_text().splitlines()[0].split()[1:]
 transitions={}
 for col,name in [(5,'soft'),(6,'hard')]:
  u,v=crossings(a,col),crossings(b,col);same=len(u)==len(v) and all(i['rising']==j['rising'] for i,j in zip(u,v))
  transitions[name]={'reference':u,'candidate':v,'same_count_and_polarity':same,'max_time_displacement_s':max((abs(i['time_s']-j['time_s']) for i,j in zip(u,v)),default=0) if same else None}
 result={'reference':p['reference_run'],'candidate':candidate,'preflight_status':p['status'],'fingerprints_exact':x['fingerprints']==y['fingerprints'],'fingerprint_count':len(y['fingerprints']),'completed':x['solver_status']==y['solver_status']=='passed','endpoint_s':[float(a[-1,0]),float(b[-1,0])],'all_late_decisions_exact':all([v>.6 for v in x['both_sampled_output_V'][k]]==[v>.6 for v in y['both_sampled_output_V'][k]] for k in ['soft','hard']),'late_outputs_V':{'reference':x['both_sampled_output_V'],'candidate':y['both_sampled_output_V']},'whole_trace_comparison':{'grid_step_s':float(grid[1]-grid[0]),'points':len(grid),'max_abs_difference_V':dict(zip(header,map(float,np.max(abs(aa-bb),axis=0)))),'rms_difference_V':dict(zip(header,map(float,np.sqrt(np.mean((aa-bb)**2,axis=0)))))},'measure_difference':{k:y['measures'][k]-v for k,v in x['measures'].items()},'transitions':transitions,'wall_s':{'reference':x['wall_s'],'candidate':y['wall_s']},'scope':'Selected controlled source/sample/late-decision agreement only. Whole-trace differences retained; no global solver or shortened-settling qualification.'}
 result['selected_sample_decision_status']='passed' if result['completed'] and result['fingerprints_exact'] and result['all_late_decisions_exact'] and p['status']=='passed' else 'failed'
 out=d/('profile_comparison.json' if preflight=='controlled_profile_preflight.json' else 'solver_comparison.json')
 with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['late_outputs_V','transitions']},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');compare(p.parse_args().run)
