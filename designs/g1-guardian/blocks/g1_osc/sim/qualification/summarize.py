#!/usr/bin/env python3
"""Aggregate the four disjoint trim shards, retaining failed/incomplete cases."""
import csv,json
from collections import defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent
rows=[]
for shard in range(4):
 rows+=json.loads((HERE/'runs'/f'osc_trim80_shard{shard}_20260921_01'/'manifest.json').read_text())['cases']
assert len(rows)==80, 'All 80 attempts must be recorded before campaign summary'
assert len({r['name'] for r in rows})==80, 'Duplicate shard entries'
groups=defaultdict(list)
for row in rows:groups[(row['mos'],row['res'],row['cap'],row['vdd'],row['temp'])].append(row)
summary=[]
for key,group in groups.items():
 assert len(group)==16
 group.sort(key=lambda r:r['code']); good=[r for r in group if r['status']=='passed']
 entry=dict(zip(['mos','res','cap','vdd','temperature_C'],key));entry.update(attempted=16,completed=len(good),failed=sum(r['status']=='failed' for r in group),not_run=sum(r['status']=='not run' for r in group),trim_reach_status='not run')
 if len(good)==16:
  f=[r['measurements']['fmhz'] for r in group]; best=min(group,key=lambda r:abs(r['measurements']['fmhz']-10))
  entry.update(frequency_min_MHz=min(f),frequency_max_MHz=max(f),code8_frequency_MHz=f[8],nearest_code=best['code'],nearest_frequency_MHz=best['measurements']['fmhz'],nearest_error_percent=(best['measurements']['fmhz']/10-1)*100,trim_reach_status='passed' if min(f)<=10<=max(f) else 'failed',frequency_monotonic_status='passed' if all(a>b for a,b in zip(f,f[1:])) else 'failed',duty_min_percent=min(r['measurements']['duty'] for r in group),duty_max_percent=max(r['measurements']['duty'] for r in group),minimum_high_width_ns=min(r['high_width_s'] for r in group)*1e9,minimum_low_width_ns=min(r['low_width_s'] for r in group)*1e9)
 summary.append(entry)
(HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
with (HERE/'summary.csv').open('w') as f:
 keys=sorted({k for row in summary for k in row});writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(summary)
print(json.dumps(summary,indent=2))
