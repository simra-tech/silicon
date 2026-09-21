#!/usr/bin/env python3
"""Compare preselected legacy repeats, retaining missing and strict-match failures."""
import bisect,json,math
from pathlib import Path
from reciprocal_calibration import fit_calibration,infer_temperature
HERE=Path(__file__).resolve().parent
curve=json.loads((HERE/'fixed_nominal_curve.json').read_text())['curve_pairs_linear_reading_C_actual_temperature_C']
def lut(t):
 i=max(0,min(len(curve)-2,bisect.bisect_right([x[0] for x in curve],t)-1));(a,b),(c,d)=curve[i:i+2];return b+(t-a)*(d-b)/(c-a)
def summary(m):
 cases=m['cases'];assert len(cases)==4 and all(c['status']=='passed' for c in cases)
 f={c['temperature_C']:c['measurements']['freq'] for c in cases};fp=[c['fingerprints'] for c in cases];assert all(len(x)==10 and x[:5]==x[5:]==fp[0][:5] for x in fp)
 slope=(f[100]-f[25])/75;a,b=fit_calibration(f[25],f[100]);out={'frequencies':f,'fingerprints':fp[0][:5]}
 for method in ['linear','lut','reciprocal']:
  err={t:((25+(f[t]-f[25])/slope) if method=='linear' else lut(25+(f[t]-f[25])/slope) if method=='lut' else infer_temperature(f[t],a,b))-t for t in [-40,125]};out[method]={'residuals_C':err,'status':'passed' if max(map(abs,err.values()))<=2 else 'failed'}
 return out
rows=[]
for sample in json.loads((HERE/'legacy_crosscheck_selection.json').read_text())['samples']:
 seed=sample['seed'];old=HERE/'runs'/f't2f_mc100_20260921_01_s{seed}'/'manifest.json';new=HERE/'runs'/sample['legacy_run_id']/'manifest.json';row={'seed':seed,'native_run':old.parent.name,'legacy_run':new.parent.name,'status':'not run'}
 if new.exists():
  om=json.loads(old.read_text());nm=json.loads(new.read_text())
  try:
   a=summary(om);b=summary(nm);eq=a['fingerprints']==b['fingerprints'];ulps=[abs(float(x)-float(y))/max(math.ulp(float(x)),math.ulp(float(y))) for x,y in zip(a['fingerprints'],b['fingerprints'])]
   row.update(status='completed comparison',identical_model_hashes=om['models_sha256']==nm['models_sha256'],identical_netlist_hashes=om['realized_netlist_sha256']==nm['realized_netlist_sha256'],strict_fingerprint_match='passed' if eq else 'failed',maximum_parameter_ulp_difference=max(ulps),separate_4ulp_roundoff_diagnostic='passed' if max(ulps)<=4 else 'failed',native=a,legacy=b,maximum_frequency_relative_difference_ppm=max(abs(a['frequencies'][t]/b['frequencies'][t]-1)*1e6 for t in a['frequencies']),maximum_linear_residual_difference_C=max(abs(a['linear']['residuals_C'][t]-b['linear']['residuals_C'][t]) for t in [-40,125]),all_method_classifications_agree=all(a[k]['status']==b[k]['status'] for k in ['linear','lut','reciprocal']))
  except (AssertionError,KeyError):row['status']='not run to completion'
 rows.append(row)
result={'scope':'Preselected endpoint failures and <=0.05C near-boundary samples from expanded100.25/100 remain calibration members; repeats are not new physical samples. Strict bit matching and separately reviewed4ULP diagnostic both retained. No global simulator adoption.','cases':rows}
(HERE/'legacy_crosscheck_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k not in ['native','legacy']} for r in rows],indent=2))
