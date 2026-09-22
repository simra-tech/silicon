#!/usr/bin/env python3
"""Qualify independent-temperature comparator leaves against complete archived cases."""
import argparse,hashlib,json,re
from pathlib import Path
import numpy as np
from wave_archive import resolve_wave
SIM=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--reference',required=True);p.add_argument('--candidate',required=True);p.add_argument('--seed',type=int,required=True);a=p.parse_args();r=SIM/'qualification'/a.reference;c=SIM/'qualification'/a.candidate
rs=next(x for x in json.loads((r/'summary.json').read_text()) if x['seed']==a.seed);cs=next(x for x in json.loads((c/'summary.json').read_text()) if x['seed']==a.seed);rp=json.loads((r/'provenance.json').read_text());cp=json.loads((c/'provenance.json').read_text())
base=lambda d:(d/f'seed{a.seed}.cir').read_text().split('.control')[0].replace(d.name,'@RUN@')
checks={'source_snapshot_exact':(r/'cmp.spice').read_bytes()==(c/'cmp.spice').read_bytes(),'generated_circuit_before_control_exact':base(r)==base(c),'models_exact':rp['model_hashes']==cp['model_hashes'],'image_exact':rp['image_id']==cp['image_id'],'ngspice_exact':rp['ngspice']==cp['ngspice'],'transient_commands_exact':set(re.findall(r'^tran .+$',(r/f'seed{a.seed}.cir').read_text(),re.M))==set(re.findall(r'^tran .+$',(c/f'seed{a.seed}.cir').read_text(),re.M))};cases=[]
for i,case in enumerate(cs['cases']):
 j=next(j for j,row in enumerate(rs['cases']) if row['temp_C']==case['temp_C'] and row['average_CM_V']==case['average_CM_V']);ref=rs['cases'][j]
 assert case['status']==ref['status']=='passed'
 x,y=ref['sampled_q_V'],case['sampled_q_V'];u=np.loadtxt(resolve_wave(r/(ref['tag']+'.dat')),skiprows=1);v=np.loadtxt(resolve_wave(c/(case['tag']+'.dat')),skiprows=1);grid=np.linspace(0,min(u[-1,0],v[-1,0]),400901);diff=[np.interp(grid,u[:,0],u[:,k])-np.interp(grid,v[:,0],v[:,k]) for k in range(1,u.shape[1])]
 cases.append({'temperature_C':case['temp_C'],'CM_V':case['average_CM_V'],'fingerprints_exact':rs['fingerprints'][j]==cs['fingerprints'][i],'observed_parameters':len(cs['fingerprints'][i]),'decision_count':len(x),'candidate_decision_count':len(y),'decision_mismatch_count':sum((xx>.6)!=(yy>.6) for xx,yy in zip(x,y)),'max_sampled_q_difference_V':max(abs(xx-yy) for xx,yy in zip(x,y)),'ambiguity_interval_exact':ref['ambiguity_interval_V']==case['ambiguity_interval_V'],'endpoints_s':[float(u[-1,0]),float(v[-1,0])],'full_trace_grid_points':len(grid),'full_trace_max_abs_difference_V':list(map(lambda d:float(np.max(abs(d))),diff))})
report={'reference':a.reference,'candidate':a.candidate,'seed':a.seed,'checks':checks,'cases':cases,'scope':'Individual-temperature process partition vs multi-temperature process. Same circuit and sampled parameters, complete401 staircase decisions and full trace comparison. No changed numerical settings or acceptance limits.'};report['status']='passed' if all(checks.values()) and all(x['fingerprints_exact'] and x['observed_parameters']==32 and x['decision_count']==x['candidate_decision_count']==401 and x['decision_mismatch_count']==0 and x['ambiguity_interval_exact'] for x in cases) else 'failed'
with (c/'partition_comparison.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(report,indent=2))
