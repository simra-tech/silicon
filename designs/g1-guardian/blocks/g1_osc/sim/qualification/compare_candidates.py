#!/usr/bin/env python3
"""Compare isolated resistor-sizing candidates with the retained baseline."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
base=[]
for i in range(4):base+=json.loads((ROOT/'runs'/f'osc_trim80_shard{i}_20260921_01/manifest.json').read_text())['cases']
def key(r):return (r['mos'],r['res'],r['cap'],r['vdd'],r['temp'],r['code'])
lookup={key(r):r for r in base};details=[];summary=[]
for candidate in ['r098','r095']:
 rows=[]
 for i in range(2):
  p=ROOT/'runs'/f'osc_{candidate}_candidate_shard{i}_20260921_01'/'manifest.json'
  if not p.exists():continue
  m=json.loads(p.read_text());rows+=m['cases'];source=(p.parent/'osc_source.spice').read_text().splitlines();variant=(p.parent/'osc.spice').read_text().splitlines();changes=[(a,b) for a,b in zip(source,variant) if a!=b]
  assert len(source)==len(variant) and len(changes)==4
  assert {a.split()[0] for a,b in changes}=={'XR53','XR54','XR55','XR56'}
  for a,b in changes:
   assert a.replace('l=58.5u','l=VALUE')==b.replace('l=57.33u','l=VALUE').replace('l=55.575u','l=VALUE')
  for r in m['cases']:
   deck=(p.parent/(r['name']+'.cir')).read_text();assert 'Cload osc_clk 0 50f' in deck
 for r in rows:
  b=lookup[key(r)];d={'candidate':candidate,'name':r['name'],'code':r['code'],'status':r['status'],'baseline_frequency_MHz':b['measurements']['fmhz']}
  if r['status']=='passed':d.update(candidate_frequency_MHz=r['measurements']['fmhz'],frequency_change_percent=(r['measurements']['fmhz']/b['measurements']['fmhz']-1)*100,duty_change_percentage_points=r['measurements']['duty']-b['measurements']['duty'])
  details.append(d)
 for mos,temp in [('tt',27),('ss',125)]:
  group=[r for r in rows if r['mos']==mos and r['temp']==temp];good=[r for r in group if r['status']=='passed'];d={'candidate':candidate,'mos':mos,'temperature_C':temp,'expected_codes':16,'recorded_codes':len(group),'completed_codes':len(good),'trim_reach_status':'not run'}
  if len(good)==16:
   good.sort(key=lambda r:r['code']);f=[r['measurements']['fmhz'] for r in good];best=min(good,key=lambda r:abs(r['measurements']['fmhz']-10));changes=[r for r in details if r['candidate']==candidate and r['name'] in {x['name'] for x in group}]
   d.update(frequency_monotonic_status='passed' if all(a>b for a,b in zip(f,f[1:])) else 'failed',trim_reach_status='passed' if min(f)<=10<=max(f) else 'failed',frequency_min_MHz=min(f),frequency_max_MHz=max(f),nearest_code=best['code'],nearest_frequency_MHz=best['measurements']['fmhz'],maximum_abs_duty_change_percentage_points=max(abs(r['duty_change_percentage_points']) for r in changes),current_max_uA=max(r['measurements']['iua'] for r in good))
  summary.append(d)
(ROOT/'candidate_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
with (ROOT/'candidate_comparison.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=sorted({k for r in details for k in r}));writer.writeheader();writer.writerows(details)
print(json.dumps(summary,indent=2))
