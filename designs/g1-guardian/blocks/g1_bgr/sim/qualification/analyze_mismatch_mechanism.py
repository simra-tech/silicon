#!/usr/bin/env python3
"""Correlate retained BGR samples; representative parameters are not full isolation."""
import csv,json,math,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent
def corr(x,y):
 a,b=statistics.mean(x),statistics.mean(y);den=math.sqrt(sum((v-a)**2 for v in x)*sum((w-b)**2 for w in y));return sum((v-a)*(w-b) for v,w in zip(x,y))/den if den else None
rows=[]
for name in ['bgr_mc20_20260921_01','bgr_mc100_20260921_01']:
 path=HERE/'runs'/name
 for c in json.loads((path/'manifest.json').read_text())['cases']:
  if c['status']!='passed':continue
  with (path/(c['name']+'.dat')).open() as f:next(f);d=[list(map(float,line.split())) for line in f if line.strip()]
  lookup={r[0]:r for r in d};slope=(lookup[100][1]/lookup[25][1]-1)/75*1e6;fp=list(map(float,c['fingerprints'][:3]))
  rows.append({'seed':c['seed'],'tc_ppm_C':c['tc_ppm_C'],'signed_25_to_100_slope_ppm_C':slope,'vref25_V':c['vref25'],'iptat25_A':lookup[25][2],'NMOS_cascode_XM34_delvto_V':fp[0],'R1_XR16_nsmm_rsh':fp[1],'Q1_XQ56_area_factor':fp[2],'tc_status':c['tc_status']})
features=['NMOS_cascode_XM34_delvto_V','R1_XR16_nsmm_rsh','Q1_XQ56_area_factor']
summary={'method':'Pearson correlation across all100retained independent samples. XM34 is one NMOS-cascode finger;XR16 is R1;XQ56 is unitQ1. These three representative fingerprints do not isolate complete mismatch classes.','samples':len(rows),'TC_failed_samples':sum(r['tc_status']=='failed' for r in rows),'correlations':{feature:{target:corr([r[feature] for r in rows],[r[target] for r in rows]) for target in ['signed_25_to_100_slope_ppm_C','tc_ppm_C','vref25_V','iptat25_A']} for feature in features},'limitation':'Correlation alone is not a causal variance decomposition. Isolated-class or fixed-draw ablation must verify unchanged physical draws for other classes; equal seeds across changed library sections do not guarantee that.'}
(HERE/'mismatch_mechanism.json').write_text(json.dumps(summary,indent=2)+'\n')
with (HERE/'mismatch_mechanism_samples.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
print(json.dumps(summary,indent=2))
