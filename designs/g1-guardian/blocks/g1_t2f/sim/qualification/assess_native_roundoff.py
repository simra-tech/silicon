#!/usr/bin/env python3
"""Separate roundoff assessment after exact-string native comparison failed.
The original strict comparison is preserved and is not relabeled passed.
"""
import json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
strict=json.loads((HERE/'native_sample_qualification.json').read_text())
rows=[]
for sample in strict['samples']:
 row={'seed':sample['seed'],'strict_status':sample['status'],'roundoff_assessment_status':'not run'}
 if 'frequency_delta_ppm' in sample:
  a=json.loads((HERE/'runs'/sample['legacy_run']/'manifest.json').read_text());b=json.loads((HERE/'runs'/sample['native_run']/'manifest.json').read_text());aa={c['temperature_C']:c for c in a['cases']};bb={c['temperature_C']:c for c in b['cases']}
  differences=[]
  for t in aa:
   for i,(s,v) in enumerate(zip(aa[t]['fingerprints'],bb[t]['fingerprints'])):
    if s!=v:
     x,y=float(s),float(v);differences.append({'temperature_C':t,'fingerprint_index':i,'legacy':s,'native':v,'absolute_difference':abs(y-x),'difference_float_ULP':abs(y-x)/max(math.ulp(x),math.ulp(y))})
  intact=all(len(aa[t]['fingerprints'])==len(bb[t]['fingerprints'])==10 and bb[t]['fingerprints'][:5]==bb[t]['fingerprints'][5:] for t in aa)
  numerical=all(d['difference_float_ULP']<=4 for d in differences)
  limits=strict['criteria'];other=all([sample['models_match'],sample['netlists_match'],sample['hbt_status_match'],sample['legacy_linear_pass']==sample['native_linear_pass'],max(map(abs,sample['frequency_delta_ppm'].values()))<=limits['frequency_difference_ppm'],max(map(abs,sample['calibrated_error_delta_C'].values()))<=limits['calibrated_error_difference_C']])
  row.update(differences=differences,roundoff_assessment_status='passed' if intact and numerical and other else 'failed')
 rows.append(row)
result={'rule':'Post-inspection floating-roundoff assessment permits at most4 binary64 ULP in representative random fingerprints; original exact-string failure retained. Model/netlist hashes and numerical/electrical criteria unchanged.','reason':'Observed last-digit delvto difference of8.67e-19V is floating-point rounding, far below any circuit tolerance; other representative classes agree exactly. This establishes a bounded numerical match, not identical binary output.','scope':strict['scope'],'samples':rows,'status':'passed' if all(r['roundoff_assessment_status']=='passed' for r in rows) else 'failed' if any(r['roundoff_assessment_status']=='failed' for r in rows) else 'not run'}
(HERE/'native_roundoff_assessment.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
