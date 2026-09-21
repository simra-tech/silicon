#!/usr/bin/env python3
"""Compare runtime fixture results using declared engineering parity tolerances."""
import argparse,json,re,math
from pathlib import Path

def read(path):
 rows=[]
 for line in path.read_text().splitlines():
  try:row=list(map(float,line.split()))
  except ValueError:continue
  if row:rows.append(row)
 return rows

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('baseline',type=Path);ap.add_argument('candidate',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 base=json.loads((a.baseline/'campaign.json').read_text());cand=json.loads((a.candidate/'campaign.json').read_text());tests={};metrics={}
 bm={r['case']:r for r in base['cases']};cm={r['case']:r for r in cand['cases']}
 for case,b in bm.items():
  c=cm.get(case,{});checks={'both_complete':b.get('data_completion')==c.get('data_completion')=='passed'};m={}
  if checks['both_complete']:
   if case in ['bgr_noise','bgr_mc','sense_noise']:
    for file in b['metrics']:
     br=read(a.baseline/case/file);cr=read(a.candidate/case/file)
     if len(br)!=len(cr) or any(len(x)!=len(y) for x,y in zip(br,cr)):checks[file+'_shape']=False;continue
     max_ratio=0.;max_abs=0.
     for x,y in zip(br,cr):
      for xx,yy in zip(x,y):
       delta=abs(xx-yy);max_abs=max(max_abs,delta);max_ratio=max(max_ratio,delta/(1e-9+1e-3*abs(xx)))
     checks[file+'_parity']=max_ratio<=1;m[file]={'max_tolerance_ratio':max_ratio,'max_abs_difference_mixed_units':max_abs}
   elif case=='osc':
    logs=[(p/case/'run.log').read_text() for p in [a.baseline,a.candidate]]
    for field in ['fmhz','duty','iua']:
     values=[float(re.findall(r'^'+field+r'\s*=\s*([-+0-9.eE]+)',log,re.M)[-1]) for log in logs]
     tol=.1 if field=='duty' else 1e-3*abs(values[0])+1e-9
     checks[field+'_parity']=abs(values[1]-values[0])<=tol;m[field]={'values':values,'tolerance':tol}
   else:
    bv=next(iter(b['metrics'].values()));cv=next(iter(c['metrics'].values()))
    for i,name in [(1,'gate'),(2,'gfet')]:
     delta=abs(bv['maximum'][i]-cv['maximum'][i]);checks[name+'_max_parity']=delta<=.01
     checks[name+'_safety_class']=(bv['maximum'][i]<1)==(cv['maximum'][i]<1)
     m[name+'_max_V']=[bv['maximum'][i],cv['maximum'][i]]
   m['observed_wall_s']=[b['wall_s'],c['wall_s']]
  tests[case]=checks;metrics[case]=m
 result={'status':'passed' if all(all(t.values()) for t in tests.values()) else 'failed','baseline':str(a.baseline),'candidate':str(a.candidate),'tests':tests,'metrics':metrics,'tolerances':'DC/AC vectors abs1e-9+rel0.1%; OSC frequency/current0.1%,duty0.1pp; gate maxima10mV and same1V safety class. Exploratory runtime parity, not specification acceptance.','timing_note':'First x86 fixture batch uses old5s polling timing floor; rerun with updatedhelper before speed ratio claims.'}
 with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
