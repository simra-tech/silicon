#!/usr/bin/env python3
"""Compare retained legacy/native anchors without changing campaign data."""
import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
DESIGN=HERE.parents[3]
BASE=HERE/'runs/t2f_mc_s51001_20260921_01'
native={25:DESIGN/'review/runtime/20260921T145655Z_arm47_t2f_cb573c0f/t2f_mc_25',-40:DESIGN/'review/runtime/20260921T150209Z_arm47_t2f_cold_e9b0ad26/t2f_mc_cold'}
def metrics(path):
 with path.open() as f:
  header=f.readline().split();rows=[list(map(float,line.split())) for line in f if line.strip()]
 steady=[r for r in rows if r[0]>=5e-6]
 duration=steady[-1][0]-steady[0][0]
 averages={header[i]:sum((a[i]+b[i])*0.5*(b[0]-a[0]) for a,b in zip(steady,steady[1:]))/duration for i in [2,3,4]}
 return {'rows':len(rows),'end_s':rows[-1][0],'steady_time_weighted_mean':averages,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def log(path):
 s=path.read_text();return {'fingerprints':re.findall(r'@[^\s]+\s*=\s*([-+0-9.eE]+)',s),'freq':float(re.search(r'^freq\s*=\s*([-+0-9.eE]+)',s,re.M)[1])}
out=[]
for temp,path in native.items():
 stem=f'ptat_T{temp}';a=log(BASE/(stem+'.log'));b=log(path/'run.log');am=metrics(BASE/(stem+'.dat'));bm=metrics(path/(stem+'.dat'))
 row={'temperature_C':temp,'legacy_path':str(BASE.relative_to(DESIGN)),'native_path':str(path.relative_to(DESIGN)),'fingerprint_status':'passed' if len(a['fingerprints'])==10 and a['fingerprints']==b['fingerprints'] else 'failed','legacy_frequency_Hz':a['freq'],'native_frequency_Hz':b['freq'],'frequency_delta_ppm':(b['freq']/a['freq']-1)*1e6,'legacy':am,'native':bm,'steady_mean_relative_delta_ppm':{k:(bm['steady_time_weighted_mean'][k]/v-1)*1e6 for k,v in am['steady_time_weighted_mean'].items()}}
 out.append(row)
result={'scope':'Two temperatures, one fixed physical sample, same model cards. Numerical equivalence screen only; global runtime acceptance and broad MC seed equivalence not established.','comparisons':out}
(HERE/'native_comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
