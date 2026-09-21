#!/usr/bin/env python3
"""Nominal joint-PEX two-point PTAT fit. Requires every planned temperature."""
import csv,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
runs=['t2f_joint_cold_20260921_01','t2f_joint_temp7_20260921_01']
rows=[]
for run in runs:
 rows.extend(json.loads((HERE/'runs'/run/'manifest.json').read_text())['cases'])
assert len(rows)==8 and all(r['status']=='passed' for r in rows)
f={r['temperature_C']:r['measurements']['freq'] for r in rows}
assert set(f)=={-40,-20,0,25,50,75,100,125}
slope=(f[100]-f[25])/75
results=[{'temperature_C':t,'frequency_Hz':freq,'inferred_temperature_C':25+(freq-f[25])/slope,'residual_C':25+(freq-f[25])/slope-t,'role':'calibration' if t in (25,100) else 'independent'} for t,freq in sorted(f.items())]
worst=max(abs(r['residual_C']) for r in results if r['role']=='independent')
summary={'status':'passed' if worst<=2 else 'failed','criterion':'max independent-point absolute residual <=2C with25/100C nominal calibration','frequency_slope_Hz_C':slope,'max_abs_independent_residual_C':worst,'limitations':'One nominal joint C-PEX sample and3.3/1.2V;not statistical or corner acceptance;freeze calibration across supply not tested.','source_runs':runs}
(HERE/'nominal_calibration.json').write_text(json.dumps(summary,indent=2)+'\n')
with (HERE/'nominal_calibration.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=results[0]);writer.writeheader();writer.writerows(results)
print(json.dumps(summary,indent=2))
