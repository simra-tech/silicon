#!/usr/bin/env python3
"""Aggregate qualified staircase ambiguity intervals without inventing a unique offset."""
import argparse,collections,datetime,json,math,statistics
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('campaigns',type=Path,nargs='+');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 samples=[];seen=set();duplicate=[]
 for directory in a.campaigns:
  path=directory/'summary.json'
  if not path.exists():samples.append({'campaign':directory.name,'seed':None,'status':'not run'});continue
  for raw in json.loads(path.read_text()):
   seed=raw['seed']
   if seed in seen:duplicate.append(seed)
   seen.add(seed);cases=[]
   for row in raw['cases']:
    interval=row.get('ambiguity_interval_V')
    finite=interval is not None and len(interval)==2 and all(map(math.isfinite,interval)) and interval[0]<=interval[1]
    cases.append({'tag':row['tag'],'temperature_C':row['temp_C'],'average_CM_V':row['average_CM_V'],'solver_waveform_status':row['status'],'ambiguity_interval_V':interval,'ambiguity_interval_width_V':interval[1]-interval[0] if finite else None,'finite_interval_status':'passed' if finite else 'failed/no bracket' if row['status']=='passed' else 'not run','monotonic_decisions':row.get('monotonic_decisions'),'unique_crossing_bracketed':row.get('bracketed'),'sampled_decisions':len(row.get('sampled_q_V',[]))})
   drifts=[]
   for cm in sorted(set(r['average_CM_V'] for r in cases)):
    reference=next((r for r in cases if r['average_CM_V']==cm and r['temperature_C']==25 and r['finite_interval_status']=='passed'),None)
    if reference:
     lo,hi=reference['ambiguity_interval_V']
     for row in cases:
      if row['average_CM_V']==cm and row['finite_interval_status']=='passed':
       low,high=row['ambiguity_interval_V'];drifts.append({'temperature_C':row['temperature_C'],'average_CM_V':cm,'offset_change_envelope_V':[low-hi,high-lo],'nominal_gain10_shunt_equivalent_envelope_V':[(low-hi)/10,(high-lo)/10]})
   samples.append({'campaign':directory.name,'seed':seed,'status':raw['status'],'watchdog_status':raw['watchdog_status'],'wall_s':raw['wall_s'],'wall_s_scope':raw.get('wall_s_scope','complete original multi-temperature bundle'),'runtime_forecast_eligible':not raw.get('case_evidence') or all(x['kind']=='new individual-temperature leaf' for x in raw['case_evidence']),'case_evidence':raw.get('case_evidence',[]),'frozen_observed_parameters':raw['frozen_fingerprints'],'observed_parameter_count':len(raw['fingerprints'][0]) if raw['fingerprints'] else 0,'cases':cases,'temperature_change_diagnostic':drifts})
 cases=[r for s in samples for r in s.get('cases',[])];times=[s['wall_s'] for s in samples if s['status']=='passed' and s.get('runtime_forecast_eligible',False)]
 report={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Cell-PEX comparator staircase with declared ideal symmetric source network. Reports an ambiguity interval from all401 sampled decisions, not a unique offset or loaded-chain/system yield. Temperature-difference envelopes include both reference and current ambiguity; divisionby10 is nominal shunt-equivalent diagnostic only, not joint calibration.','campaigns':[p.name for p in a.campaigns],'duplicate_seeds':duplicate,'aggregate_status':'failed duplicate seeds' if duplicate else 'passed unique seeds','attempted_seed_count':len([s for s in samples if s['seed'] is not None]),'numerical_status_counts':dict(collections.Counter(s['status'] for s in samples)),'finite_interval_status_counts':dict(collections.Counter(r['finite_interval_status'] for r in cases)),'nonmonotonic_case_count':sum(r['monotonic_decisions'] is False for r in cases),'frozen_parameter_failures':sum(s.get('frozen_observed_parameters') is False for s in samples),'complete_case_count':sum(r['solver_waveform_status']=='passed' for r in cases),'maximum_ambiguity_width_V':max((r['ambiguity_interval_width_V'] for r in cases if r['ambiguity_interval_width_V'] is not None),default=None),'component_offset_acceptance':'not applicable: no allocated standalone offset/ambiguity limit; system acceptance belongs to loaded calibrated chain','median_wall_s_per_seed':statistics.median(times) if times else None,'forecast100_core_hours_for_this_CM_temperature_scope':statistics.mean(times)*100/3600 if times else None,'samples':samples}
 with a.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))
if __name__=='__main__':main()
