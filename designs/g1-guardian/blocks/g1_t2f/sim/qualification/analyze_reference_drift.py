#!/usr/bin/env python3
"""Diagnose loaded-reference drift within the actual joint physical samples.
Four-point transient averages are not the standalone dense DC TC sweep.
"""
import csv,json,math,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent
rows=[]
for row in csv.DictReader((HERE/'mc100_samples.csv').open()):
 if row['calibration_status']=='not run':continue
 m=json.loads((HERE/'runs'/row['run_id']/'manifest.json').read_text());v={c['temperature_C']:c['measurements']['vref_avg'] for c in m['cases']}
 rows.append({'seed':int(row['seed']),'run_id':row['run_id'],'vref25_V':v[25],'loaded_reference_four_point_box_TC_ppm_C':(max(v.values())-min(v.values()))/v[25]/165*1e6,'loaded_reference_25_to_100_slope_ppm_C':(v[100]/v[25]-1)/75*1e6,'linear_cold_residual_C':float(row['cold_residual_C']),'linear_hot_residual_C':float(row['hot_residual_C']),'linear_endpoint_status':row['calibration_status']})
def correlation(x,y):
 mx,my=statistics.mean(x),statistics.mean(y);den=math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y));return sum((a-mx)*(b-my) for a,b in zip(x,y))/den if den else None
result={'method':'Reference transient average over the same16 oscillator periods used for frequency at each temperature; actual joint BGR/T2F sample and loading. Four-point boxTC is only a sampled diagnostic, not a dense standalone DC acceptance sweep.','samples':len(rows),'sampled_TC_over_50ppm_C':sum(r['loaded_reference_four_point_box_TC_ppm_C']>50 for r in rows),'correlation_loaded_reference_slope_vs_linear_cold_error':correlation([r['loaded_reference_25_to_100_slope_ppm_C'] for r in rows],[r['linear_cold_residual_C'] for r in rows]),'linear_failed_samples':sum(r['linear_endpoint_status']=='failed' for r in rows),'interpretation':'Correlation is diagnostic and does not isolate BGR from comparator/mirror/passive variation. Separate standalone BGR seeds are not paired to these samples. Calibration acceptance comes from actual oscillation, never from this reference proxy.'}
(HERE/'reference_drift_diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
with (HERE/'reference_drift_samples.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
print(json.dumps(result,indent=2))
