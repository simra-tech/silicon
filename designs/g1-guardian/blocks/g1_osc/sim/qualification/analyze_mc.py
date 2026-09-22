#!/usr/bin/env python3
"""Evaluate recorded OSC mismatch qualification and code-bracket evidence."""
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('run_id');a=ap.parse_args();out=HERE/'runs'/a.run_id;m=json.loads((out/'manifest.json').read_text());rows=m['cases'];n=len(m['fingerprint_parameters']);by={r['name']:r for r in rows};result={'run_id':a.run_id,'manifest_sha256':sha(out/'manifest.json'),'attempted_cases':len(rows),'expected_cases':len(m['expected_cases']),'completed_cases':sum(r['status']=='passed' for r in rows),'failed_cases':sum(r['status']=='failed' for r in rows),'timeout_cases':sum(r['timed_out'] for r in rows),'not_run_cases':sorted(set(m['expected_cases'])-set(by))}
 if 'enabled' in m['expected_cases']:
  needed=['enabled','repeat','seed2','cold','code15','disabled','disabled_seed2','transient','transient_repeat']
  checks={};fp=lambda k:by[k]['fingerprints'][:n]
  if all(k in by and by[k]['status']=='passed' for k in needed):
   checks['same_seed_repeat']=fp('enabled')==fp('repeat')
   checks['temperature_frozen']=fp('enabled')==fp('cold')
   checks['code_frozen']=fp('enabled')==fp('code15')
   checks['transient_frozen']=all(fp('enabled')==fp(k)==by[k]['fingerprints'][n:] for k in ['transient','transient_repeat'])
   checks['disabled_seed_invariant']=fp('disabled')==fp('disabled_seed2')
   checks['enabled_differs_disabled']=fp('enabled')!=fp('disabled')
   checks['seed_varies']=fp('enabled')!=fp('seed2')
   checks['repeat_waveform_identical']=sha(out/'transient.dat')==sha(out/'transient_repeat.dat')
   groups={}
   for group,marker in [('MOS','[delvto]'),('MOS_mobility','[factuo]'),('R','[nsmm_rsh]'),('CMIM','[scale]')]:
    indices=[i for i,p in enumerate(m['fingerprint_parameters']) if marker in p]
    groups[group]={'count':len(indices),'changed_seed_parameters':sum(fp('enabled')[i]!=fp('seed2')[i] for i in indices),'enabled_differs_disabled':sum(fp('enabled')[i]!=fp('disabled')[i] for i in indices)}
    checks[group+'_nonzero_variability']=bool(indices) and groups[group]['changed_seed_parameters']>0
   result['device_class_variability']=groups
  result.update(qualification_checks=checks,status='passed' if len(checks)>=12 and all(checks.values()) else 'failed or incomplete')
 else:
  samples=[]
  for seed in sorted({r['seed'] for r in rows}):
   rr=sorted([r for r in rows if r['seed']==seed],key=lambda r:r['code']);good=[r for r in rr if r['status']=='passed'];freq=[r['measurements']['fmhz'] for r in good];codes=[r['code'] for r in good];expected=[x for x in m['expected_cases'] if x.startswith(f's{seed}_')]
   frozen=bool(good) and all(len(r['fingerprints'])==2*n and r['fingerprints'][:n]==good[0]['fingerprints'][:n]==r['fingerprints'][n:] for r in good)
   bracket=(min(freq)<=10<=max(freq)) if len(good)==len(expected) and 0 in codes and 15 in codes else None
   samples.append({'seed':seed,'completed_codes':codes,'expected_code_count':len(expected),'fingerprint_frozen':frozen,'frequency_MHz':freq,'brackets_10MHz':bracket,'strict_monotonic_all16':all(freq[i]>freq[i+1] for i in range(15)) if codes==list(range(16)) else None})
  result.update(samples=samples,bracket_failures=sum(s['brackets_10MHz'] is False for s in samples),fingerprint_failures=sum(not s['fingerprint_frozen'] for s in samples),conditions=sorted({(r['mos'],r['res'],r['cap'],r['vdd'],r['temperature_C']) for r in rows}),limitations='Endpoint-only bracket does not establish all-code monotonicity. Recorded process/supply/temperature and ideal50fF load only, not receiver/jitter qualification.')
 (out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
