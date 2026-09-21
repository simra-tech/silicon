#!/usr/bin/env python3
"""Check common random draws before comparing isolated main-pair area candidates."""
import argparse,json,re,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--baseline-analysis',required=True,type=Path);p.add_argument('--scale',required=True,type=float);a=p.parse_args()
base=json.loads(a.baseline_analysis.read_text());new=json.loads((a.candidate/'analysis.json').read_text())['sample_results'];reports=[]
def fingerprint(f):
    text=f.read_text().split('FINGERPRINT 0\n')[1].split('Doing analysis')[0]
    return {k:float(v) for k,v in re.findall(r'^(@n\.[^=]+) = ([-+0-9.eE]+)',text,re.M)}
for n in new:
    seed=n['seed'];f=next(Path(d)/f'seed{seed}.log' for d in base['source_run_directories'] if (Path(d)/f'seed{seed}.log').exists())
    b,c=fingerprint(f),fingerprint(a.candidate/f'seed{seed}.log');unchanged=[];scaled=[]
    for k in b:
        if '.xota.xm' not in k:unchanged.append(b[k]==c[k])
        elif k.endswith('[l]'):scaled.append(math.isclose(b[k],c[k],abs_tol=1e-17))
        elif k.endswith('[w]'):scaled.append(math.isclose(b[k]-96e-6,c[k]-a.scale*96e-6,abs_tol=1e-17))
        elif k.endswith('[delvto]'):scaled.append(math.isclose(b[k],c[k]*math.sqrt(a.scale),abs_tol=1e-15))
        elif k.endswith('[factuo]'):scaled.append(math.isclose(b[k]-1,(c[k]-1)*math.sqrt(a.scale),abs_tol=1e-14))
    old=next(x for x in base['sample_results'] if x['seed']==seed)
    reports.append({'seed':seed,'unchanged_parameter_count':len(unchanged),'unchanged_parameters_exact':all(unchanged),'scaled_main_pair_random_draws_match':all(scaled),
        'baseline_residual_V':old['worst_frozen_continuous_correction_residual_V'],'candidate_residual_V':n['worst_frozen_continuous_correction_residual_V'],
        'candidate_offset_target':n['offset_target_status'],'candidate_gain_target':n['gain_target_status']})
out={'scope':'Deliberately selected worst baseline samples; common underlying random numbers checked, not independent yield samples','main_input_pair_area_scale':a.scale,'samples':reports}
(a.candidate/'comparison.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
