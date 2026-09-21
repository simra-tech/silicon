#!/usr/bin/env python3
"""UNQUALIFIED diagnostic: ideal f proportional to IPTAT/VREF, two-point calibration.
Not an oscillator simulation or acceptance evidence for T2F. All sample data retained.
"""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parent
rows=[]
for run in ['bgr_mc20_20260921_01','bgr_mc100_20260921_01']:
 for case in json.loads((ROOT/'runs'/run/'manifest.json').read_text())['cases']:
  d=[[float(x) for x in line.split()] for line in (ROOT/'runs'/run/(case['name']+'.dat')).read_text().splitlines()[1:]]
  f={x[0]:x[2]/x[1] for x in d}
  residual={t:25+(v-f[25])/(f[100]-f[25])*75-t for t,v in f.items() if t not in (25,100)}
  worst=max(map(abs,residual.values()))
  rows.append({'seed':case['seed'],'max_abs_residual_C':worst,'cold_residual_C':residual[-40.0],'hot_residual_C':residual[125.0],'proxy_status':'passed' if worst<=2 else 'failed','actual_T2F_calibration_status':'not run'})
with (ROOT/'ideal_iptat_vref_proxy.csv').open('w') as output:
 writer=csv.DictWriter(output,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
print('Diagnostic-only proxy failures:',sum(row['proxy_status']=='failed' for row in rows))
print('Worst:',max(rows,key=lambda row:row['max_abs_residual_C']))
