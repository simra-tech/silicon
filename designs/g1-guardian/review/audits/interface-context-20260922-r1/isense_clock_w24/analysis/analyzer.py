#!/usr/bin/env python3
"""Reduce the retained KPEX capacitor graph under explicit fill boundary conditions."""
import argparse,hashlib,json,re,shutil
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False);shutil.copyfile(__file__,a.output/'analyzer.py')
scale={'f':1e-15,'a':1e-18,'p':1e-12,'n':1e-9,'u':1e-6,'':1}
results={}
for variant in ['no_fill','actual_fill']:
 path=a.input/variant/'kpex/clip__sense_fill_clip/sense_fill_clip_k25d_pex_netlist.spice';caps=[]
 for line in path.read_text().splitlines():
  t=line.split()
  if not t or not t[0].lower().startswith('c'):continue
  m=re.fullmatch(r'([\d.eE+\-]+)([afpnu]?)',t[3]);caps.append((t[1],t[2],float(m[1])*scale[m[2]]))
 nodes=sorted({x for u,v,c in caps for x in [u,v]});fills=[n for n in nodes if n.startswith('FILL_')];grounds=[n for n in nodes if n not in fills+['P','N']]
 assert 'VSUBS' in grounds and all(n=='VSUBS' or n.startswith('CTX_L') for n in grounds),grounds
 idx={n:i for i,n in enumerate(nodes)};K=np.zeros((len(nodes),len(nodes)))
 for u,v,c in caps:
  i,j=idx[u],idx[v];K[i,i]+=c;K[j,j]+=c;K[i,j]-=c;K[j,i]-=c
 assert np.max(abs(K.sum(axis=1)))<1e-27
 ext=[idx['P'],idx['N']];ins=[idx[n] for n in fills];Kpp=K[np.ix_(ext,ext)]
 rec={'netlist_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'capacitors':len(caps),'nets':len(nodes),'fill_nodes':len(fills),'grounded_context_nodes':grounds,'row_sum_residual_F':float(np.max(abs(K.sum(axis=1)))),'modes':{}}
 for mode in ['grounded','floating']:
  eff=Kpp.copy();res=0.;cond=None
  if mode=='floating' and ins:
   ff=K[np.ix_(ins,ins)];fp=K[np.ix_(ins,ext)];T=np.linalg.solve(ff,-fp);eff+=K[np.ix_(ext,ins)]@T;res=float(np.max(abs(ff@T+fp)));cond=float(np.linalg.cond(ff))
  assert np.min(np.linalg.eigvalsh(eff))>0
  rec['modes'][mode]={'matrix_fF':(eff*1e15).tolist(),'P_ground_equivalent_fF':float(eff[0].sum()*1e15),'N_ground_equivalent_fF':float(eff[1].sum()*1e15),'mutual_fF':float(-eff[0,1]*1e15),'balanced_differential_energy_C_fF':float(np.array([.5,-.5])@eff@np.array([.5,-.5])*1e15),'common_mode_energy_C_fF':float(np.ones(2)@eff@np.ones(2)*1e15),'floating_charge_residual_F':res,'floating_matrix_condition':cond}
  for drive in ['P','N']:
   deck=[f'* {variant} {mode} drive {drive}; diagnostic capacitor-network AC only']
   for i,(u,v,c) in enumerate(caps):
    conv=lambda n:'0' if n in grounds or (mode=='grounded' and n in fills) else n
    u,v=conv(u),conv(v)
    if u!=v:deck.append(f'C{i} {u} {v} {c:.17g}')
   deck+=['VP P 0 DC 0 AC '+str(int(drive=='P')),'VN N 0 DC 0 AC '+str(int(drive=='N')),'.control','set numdgt=17','ac lin 1 1Meg 1Meg','let cp = -imag(i(VP))/(2*pi*1e6)','let cn = -imag(i(VN))/(2*pi*1e6)','print cp cn','quit','.endc','.end']
   (a.output/f'{variant}_{mode}_{drive}.cir').write_text('\n'.join(deck)+'\n')
 results[variant]=rec
(a.output/'summary.json').write_text(json.dumps({'scope':'Exact raw KPEX 2.5D capacitor graph reduction; clipped context conductors and substrate grounded. Floating fill means zero small-signal net charge, no DC leakage modeled. Not whole-route or full-chip extraction.','results':results},indent=2)+'\n');print(json.dumps(results,indent=2))
