#!/usr/bin/env python3
"""Check previously unseen nominal temperatures without refitting the LUT."""
import bisect,csv,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
frozen=json.loads((HERE/'fixed_nominal_curve.json').read_text())
curve=frozen['curve_pairs_linear_reading_C_actual_temperature_C'];xs=[p[0] for p in curve]
nominal=list(csv.DictReader((HERE/'nominal_calibration.csv').open()))
f25=next(float(r['frequency_Hz']) for r in nominal if float(r['temperature_C'])==25)
slope=json.loads((HERE/'nominal_calibration.json').read_text())['frequency_slope_Hz_C']
name='t2f_interpolation_probe_20260921_01';path=HERE/'runs'/name/'manifest.json'
cases=json.loads(path.read_text())['cases'] if path.exists() else []
rows=[]
for temp in [-10,12.5,62.5,112.5]:
 matches=[c for c in cases if c['temperature_C']==temp];row={'temperature_C':temp,'status':'not run'}
 if matches and matches[0]['status']=='passed':
  c=matches[0];reading=25+(c['measurements']['freq']-f25)/slope;i=max(0,min(len(curve)-2,bisect.bisect_right(xs,reading)-1));(x0,y0),(x1,y1)=curve[i:i+2];corrected=y0+(reading-x0)*(y1-y0)/(x1-x0)
  row.update(status='passed',frequency_Hz=c['measurements']['freq'],linear_residual_C=reading-temp,fixed_curve_residual_C=corrected-temp)
 rows.append(row)
result={'method':'Original nominal25/100C calibration and eight-knot correction frozen; four new temperatures between original knots. No refitting.','source_run':name,'nominal_curve_sha256':frozen['nominal_curve_sha256'],'points':rows,'limits':'One mismatch-disabled typical sample. Bounds between every sampled temperature and at process/rail/mismatch extremes are not established.'}
(HERE/'interpolation_probe.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
