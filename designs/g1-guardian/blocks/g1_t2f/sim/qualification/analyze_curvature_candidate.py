#!/usr/bin/env python3
"""Diagnostic alternative: frozen nominal-PEX LUT after per-sample2point calibration.
No fitting to mismatch outcomes. Linear-calibration failures remain unchanged.
"""
import argparse,bisect,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--samples',type=int,default=20);args=parser.parse_args();assert args.samples in [20,100,300]
stem='curvature_candidate' if args.samples==20 else f'curvature_candidate{args.samples}'
frozen=json.loads((ROOT/'fixed_nominal_curve.json').read_text())
curve=frozen['curve_pairs_linear_reading_C_actual_temperature_C']
x=[pair[0] for pair in curve]
def correct(value):
 idx=max(0,min(len(curve)-2,bisect.bisect_right(x,value)-1));(x0,y0),(x1,y1)=curve[idx:idx+2]
 return y0+(value-x0)*(y1-y0)/(x1-x0)
rows=[]
for row in csv.DictReader((ROOT/f'mc{args.samples}_samples.csv').open()):
 if row['calibration_status']=='not run':continue
 cold=correct(-40+float(row['cold_residual_C']))+40;hot=correct(125+float(row['hot_residual_C']))-125
 rows.append({'seed':int(row['seed']),'linear_maximum_abs_residual_C':float(row['maximum_abs_residual_C']),'linear_calibration_status':row['calibration_status'],'candidate_cold_residual_C':cold,'candidate_hot_residual_C':hot,'candidate_maximum_abs_residual_C':max(abs(cold),abs(hot)),'candidate_endpoint_status':'passed' if max(abs(cold),abs(hot))<=2 else 'failed'})
with (ROOT/f'{stem}_samples.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
summary={'method':'Fixed inverse piecewise-linear nominal joint-PEX curve after per-sample25/100C linear calibration; extend outer segment beyond nominal reading range','nominal_curve_sha256':frozen['nominal_curve_sha256'],'curve_pairs_linear_reading_C_actual_temperature_C':curve,'completed_samples':len(rows),'held_out_samples':sum(r['seed']>=51021 for r in rows),'held_out_endpoint_failed':sum(r['seed']>=51021 and r['candidate_endpoint_status']=='failed' for r in rows),'linear_calibration_failed':sum(r['linear_calibration_status']=='failed' for r in rows),'candidate_endpoint_failed':sum(r['candidate_endpoint_status']=='failed' for r in rows),'candidate_maximum_abs_residual_C':max(r['candidate_maximum_abs_residual_C'] for r in rows),'status':'diagnostic candidate; not adopted','limitations':'Based on nominal simulated curvature only; original20samples have separate intermediate-temperature evidence; see held_out_samples count here. Corners/rails and packaged calibration not verified. Original linear-calibration acceptance evidence retained.'}
(ROOT/f'{stem}.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
