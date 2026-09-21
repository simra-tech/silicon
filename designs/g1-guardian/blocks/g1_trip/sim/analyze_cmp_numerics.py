#!/usr/bin/env python3
"""Compare all staircase decisions and analog sample voltages, preserving raw evidence."""
import json,math
from pathlib import Path
P=Path(__file__).resolve().parent/'qualification'
pairs=[('tight_arch_high','cmp-tight-x86-20260921-a','cmp-tight-arm46-20260921-a'),('tight_arch_low','cmp-tight-lowcm-x86-20260921-a','cmp-tight-lowcm-arm46-20260921-a'),('tight_step','cmp-tight-arm46-20260921-a','cmp-tight-step-arm46-20260921-a'),('tight_method','cmp-tight-x86-20260921-a','cmp-tighttrap-x86-20260921-a')]
out=[]
for label,aa,bb in pairs:
 a=json.loads((P/aa/'summary.json').read_text())[0];b=json.loads((P/bb/'summary.json').read_text())[0]
 assert a['status']==b['status']=='passed'
 ac,bc=a['cases'][0],b['cases'][0];av,bv=ac['sampled_q_V'],bc['sampled_q_V'];assert len(av)==len(bv)==401
 delta=[x-y for x,y in zip(av,bv)];ad,bd=dict(a['fingerprints'][0]),dict(b['fingerprints'][0]);assert ad.keys()==bd.keys()
 row={'comparison':label,'reference':aa,'candidate':bb,'sample_count':401,'decision_mismatch_count':sum((x>.6)!=(y>.6) for x,y in zip(av,bv)),'maximum_sampled_voltage_difference_V':max(map(abs,delta)),'rms_sampled_voltage_difference_V':math.sqrt(sum(x*x for x in delta)/401),'reference_transition_interval_V':ac['ambiguity_interval_V'],'candidate_transition_interval_V':bc['ambiguity_interval_V'],'both_monotonic':ac['monotonic_decisions'] and bc['monotonic_decisions'],'sample_parameters_max_absolute_difference':max(abs(float(ad[k])-float(bd[k])) for k in ad)}
 row['selected_decision_agreement_status']='passed' if row['decision_mismatch_count']==0 and row['both_monotonic'] and ac['ambiguity_interval_V']==bc['ambiguity_interval_V'] else 'failed';out.append(row)
result={'scope':'Seed61001 comparator schematic,25C,CM0.5/1V,401staircase decisions,1kohm/1pF inputsource; accuracy resolution0.1mV. Agreement is scoped; no PEX/alltemperature/allseed/runtime qualification. All analog sample voltages compared; continuous trajectories remain in original saved files.','comparisons':out}
(P/'comparator_numerical_assessment_20260921.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
