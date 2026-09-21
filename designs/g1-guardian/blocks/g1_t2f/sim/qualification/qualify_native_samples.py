#!/usr/bin/env python3
"""Prespecified scoped native screen on a second and an electrically failing seed.
All calibration points for each sample come from the same runtime.
"""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
LIMITS={'frequency_difference_ppm':100,'calibrated_error_difference_C':0.05}
rows=[]
for seed,legacy in [(51002,'t2f_mc_s51002_20260921_01'),(51010,'t2f_mc20_20260921_01_s51010')]:
 native=f't2f_native47_qualification_s{seed}_20260921_01'
 row={'seed':seed,'legacy_run':legacy,'native_run':native,'status':'not run'}
 path=HERE/'runs'/native/'manifest.json'
 if path.exists():
  a=json.loads((HERE/'runs'/legacy/'manifest.json').read_text());b=json.loads(path.read_text())
  row.update(legacy_image=a['image_id'],native_image=b['image_id'])
  aa={c['temperature_C']:c for c in a['cases']};bb={c['temperature_C']:c for c in b['cases']}
  if set(aa)==set(bb)=={-40,25,100,125} and all(c['status']=='passed' for c in b['cases']):
   af={t:c['measurements']['freq'] for t,c in aa.items()};bf={t:c['measurements']['freq'] for t,c in bb.items()}
   def errors(f):
    slope=(f[100]-f[25])/75
    return {t:25+(f[t]-f[25])/slope-t for t in [-40,125]}
   ae,be=errors(af),errors(bf)
   row.update(fingerprints_match=all(aa[t]['fingerprints']==bb[t]['fingerprints'] for t in aa),models_match=a['models_sha256']==b['models_sha256'],netlists_match=a['realized_netlist_sha256']==b['realized_netlist_sha256'],frequency_delta_ppm={t:(bf[t]/af[t]-1)*1e6 for t in aa},legacy_errors_C=ae,native_errors_C=be,calibrated_error_delta_C={t:be[t]-ae[t] for t in ae},legacy_linear_pass=max(map(abs,ae.values()))<=2,native_linear_pass=max(map(abs,be.values()))<=2,hbt_status_match=all(aa[t]['hbt_vce_status']==bb[t]['hbt_vce_status'] for t in aa))
   row['status']='passed' if all([row['fingerprints_match'],row['models_match'],row['netlists_match'],row['hbt_status_match'],row['legacy_linear_pass']==row['native_linear_pass'],max(map(abs,row['frequency_delta_ppm'].values()))<=LIMITS['frequency_difference_ppm'],max(map(abs,row['calibrated_error_delta_C'].values()))<=LIMITS['calibrated_error_difference_C']]) else 'failed'
 rows.append(row)
result={'criteria':LIMITS,'criteria_rationale':'Frequency100ppm and temperature0.05C numerical screening tolerances, set before these native runs;0.05C is2.5% of2C acceptance limit. Exact model/netlist/fingerprint agreement and same electrical outcomes also required. These are numerical equivalence checks, not design requirement relaxation.','scope':'Joint BGR/T2F typical process,3.3/1.2V, C-PEX32us, same frozen physical samples. No global simulator or IO startup acceptance.','samples':rows,'status':'passed' if all(r['status']=='passed' for r in rows) else 'failed' if any(r['status']=='failed' for r in rows) else 'not run'}
(HERE/'native_sample_qualification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
