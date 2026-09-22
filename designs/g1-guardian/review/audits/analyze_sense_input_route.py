#!/usr/bin/env python3
import argparse,json,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();d=a.directory;s=json.loads((d/'summary.json').read_text());root=Path(__file__).resolve().parents[4];old=root/'designs/g1-guardian/blocks/g1_sense/sim/qualification/corners-20260921-a/tt_typ_3.3V_27C.log';orig={}
for l in old.read_text().splitlines():
 if l.startswith('ROW '):
  t=l.split();orig[t[1]]=list(map(float,t[2:]))
result={'scope':'Printed six-significant-digit OP data; derived differences have corresponding rounding limits. Numerical completion is not a product-performance gate.','control_exact_original_printed_vectors':all(v[:7]==orig[k] for k,v in s[0]['rows'].items()),'original_log_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'rows':[]}
for x in s:
 for cm in ['-0.1','0','0.3']:
  r=x['rows'];u=r[f't0_c{cm}_s0'];v=r[f't0_c{cm}_s0.025'];w=r[f't0_c{cm}_s0.05'];gain=(w[0]-u[0])/.05;nom=s[0]['rows'][f't0_c{cm}_s0.025'];result['rows'].append({'R_scale':x['scale'],'external_average_CM_V':float(cm),'gain_V_V':gain,'output_at_25mV_V':v[0],'output_delta_vs_zeroR_mV':1000*(v[0]-nom[0]),'core_differential_at_25mV_V':v[-2]-v[-1],'midpoint_nonlinearity_input_uV':1e6*(v[0]-(u[0]+w[0])/2)/gain,'supply_current_at_25mV_A':-v[6]})
assert result['control_exact_original_printed_vectors'];(d/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copyfile(__file__,d/'analyzer.py');print(json.dumps(result,indent=2))
