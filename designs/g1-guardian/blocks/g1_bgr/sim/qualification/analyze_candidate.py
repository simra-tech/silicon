#!/usr/bin/env python3
"""Keep numerical, harness, and TC outcomes separate for isolated BGR candidates."""
import argparse,hashlib,json,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
 ap=argparse.ArgumentParser();ap.add_argument('run_id');a=ap.parse_args();p=HERE/'runs'/a.run_id;m=json.loads((p/'manifest.json').read_text());rows=m['cases'];cmd=m['command'];get=lambda k,d:cmd[cmd.index(k)+1] if k in cmd else d;suite=get('--suite','unknown');expected={'qualify':6,'corners':81,'startup':6,'stress':3,'capload':9,'nominal':1}.get(suite,len(get('--seeds','').split(',')) if '--seeds' in cmd else int(get('--samples','20')));good=[r for r in rows if r['status']=='passed'];result={'run_id':a.run_id,'manifest_sha256':hashlib.sha256((p/'manifest.json').read_bytes()).hexdigest(),'suite':suite,'expected_cases':expected,'attempted_cases':len(rows),'completed_cases':len(good),'numerically_failed_cases':sum(r['status']=='failed' for r in rows),'timeout_cases':sum(r['timed_out'] for r in rows),'not_run_cases':max(0,expected-len(rows)),'tc_failed_cases':sum(r.get('tc_status')=='failed' for r in rows),'tc_failed_seeds':[r['seed'] for r in rows if r.get('tc_status')=='failed'],'frozen_parameters_failed_cases':[]}
 for r in rows:
  if r.get('startup') or r.get('stress'):continue
  n=len(r['fingerprint_parameters']);fp=r['fingerprints']
  if len(fp)!=2*n or fp[:n]!=fp[n:]:result['frozen_parameters_failed_cases'].append(r['name'])
 if suite=='qualify':
  by={r['name']:r for r in rows};needed=['enabled_a','enabled_repeat','enabled_seed2','enabled_reverse','disabled_a','disabled_seed2'];checks={}
  if all(k in by for k in needed):
   fp=lambda k:by[k]['fingerprints'][:len(by[k]['fingerprint_parameters'])]
   checks={'all_complete':len(good)==6,'all_parameters_frozen':not result['frozen_parameters_failed_cases'],'repeat_exact':fp('enabled_a')==fp('enabled_repeat'),'reverse_temperature_exact':fp('enabled_a')==fp('enabled_reverse'),'disabled_seed_invariant':fp('disabled_a')==fp('disabled_seed2'),'seed_variation':fp('enabled_a')!=fp('enabled_seed2'),'repeat_waveform_exact':(p/'enabled_a.dat').read_bytes()==(p/'enabled_repeat.dat').read_bytes()}
   classes={}
   for name,marker in [('MOSVth','[delvto]'),('MOSmobility','[factuo]'),('Rsheet','[nsmm_rsh]'),('HBTarea','[area]')]:
    indices=[i for i,q in enumerate(by['enabled_a']['fingerprint_parameters']) if marker in q];classes[name]={'count':len(indices),'varied':sum(fp('enabled_a')[i]!=fp('enabled_seed2')[i] for i in indices)};checks[name+'_varies']=classes[name]['varied']>0
   result['classes']=classes
  result.update(qualification_checks=checks,qualification_status='passed' if len(checks)>=11 and all(checks.values()) else 'failed or incomplete')
 tc=[r['tc_ppm_C'] for r in good if 'tc_ppm_C' in r]
 if tc:result['tc_ppm_C']={'minimum':min(tc),'maximum':max(tc),'mean':statistics.mean(tc),'sample_std':statistics.stdev(tc) if len(tc)>1 else None}
 result['scope']='Isolated simulated candidate. No physical layout/newrouting extraction or spatialyield qualification. Baseline failures remain unchanged.';(p/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
