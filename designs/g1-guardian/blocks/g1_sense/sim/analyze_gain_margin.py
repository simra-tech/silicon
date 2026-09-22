#!/usr/bin/env python3
"""Gain-margin screen of preserved conditional return ratios, no global claim."""
import argparse,json,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('runs',nargs='+',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();results=[]
for run in a.runs:
 points=json.loads((run/'return_ratio.json').read_text());s=json.loads((run/'summary.json').read_text());cross=[]
 for lo,hi in zip(points,points[1:]):
  pl,ph=lo['phase_unwrapped_deg'],hi['phase_unwrapped_deg']
  for k in range(math.floor((min(pl,ph)-180)/360)-1,math.ceil((max(pl,ph)-180)/360)+1):
   level=180+360*k
   if pl==ph or not min(pl,ph)<=level<max(pl,ph):continue
   q=(level-pl)/(ph-pl);mag=math.exp(math.log(lo['magnitude'])+q*math.log(hi['magnitude']/lo['magnitude']))
   cross.append({'phase_deg':level,'frequency_Hz':math.exp(math.log(lo['frequency_Hz'])+q*math.log(hi['frequency_Hz']/lo['frequency_Hz'])),'conditional_gain_margin_dB':-20*math.log10(mag)})
 valid=s['DC_probe_equivalence_status']=='passed'
 results.append({'run':run.name,'DC_equivalent':valid,'frequency_range_Hz':[points[0]['frequency_Hz'],points[-1]['frequency_Hz']],'phase_crossings':cross,'conditional_10dB_screen':('passed' if all(x['conditional_gain_margin_dB']>=10 for x in cross) else 'failed') if valid and cross else 'not run/undefined: no negative-real crossing in sampled range' if valid else 'failed DC-equivalence','last_frequency_magnitude':points[-1]['magnitude'],'last_frequency_phase_deg':points[-1]['phase_unwrapped_deg'],'conditional_phase_margin':s['unity_downcrossings']})
report={'scope':'Conditional main OTA feedback, other loops closed; piecewise interpolation on preserved100points/decade complex return ratio. No infinite-frequency/global-stability inference; no new simulation.','runs':results}
with a.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
for x in results:print(x['run'],x['conditional_10dB_screen'],[v['conditional_gain_margin_dB'] for v in x['phase_crossings']])
