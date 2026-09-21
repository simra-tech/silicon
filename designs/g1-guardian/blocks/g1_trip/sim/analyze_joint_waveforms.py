#!/usr/bin/env python3
"""Characterize actual comparator common mode and kickback in retained joint traces."""
import argparse,bisect,json
from pathlib import Path

def analyze(run):
 summary=json.loads((run/'summary.json').read_text())[0]
 if summary['solver_status']!='passed':
  return {'run':run.name,'status':'not run to completion','reason':'requires complete waveform'}
 points=[list(map(float,line.split())) for line in next(run.glob('*.dat')).read_text().splitlines()[1:]]
 time=[r[0] for r in points]
 def at(t):
  i=bisect.bisect_left(time,t);left,right=points[i-1],points[i]
  f=(t-left[0])/(right[0]-left[0]);return [a+f*(b-a) for a,b in zip(left,right)]
 result={'run':run.name,'status':'completed characterization','shunt_V':summary['shunt_V'],
         'range_scope':'within specified range' if summary['shunt_V']<=.05 else 'outside-contract diagnostic','comparators':{}}
 for name,col,phase in [('soft',3,20e-9),('hard',4,70.2e-9)]:
  rows=[]
  for cycle in [2,3,4]:
   start=cycle*100e-9+phase
   pre,kick,sample=(at(t) for t in [start-.2e-9,start+1e-9,start+20e-9])
   rows.append({'cycle':cycle,'sample_common_mode_V':(sample[2]+sample[col])/2,
                'sample_differential_V':sample[2]-sample[col],
                'differential_kick_1ns_V':(kick[2]-kick[col])-(pre[2]-pre[col]),
                'conditioner_kick_1ns_V':kick[2]-pre[2],
                'dac_kick_1ns_V':kick[col]-pre[col]})
  result['comparators'][name]=rows
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('runs',nargs='+',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 result={'scope':'Interpolated retained transistor-level waveform characterization, cycles2/3/4 only; not whole-chain timing acceptance or a noise-inclusive physical claim','runs':[analyze(r) for r in a.runs]}
 with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
