#!/usr/bin/env python3
"""Separate boundary characterization, system guard bands and step checks.
Raw solver outputs and generated summaries remain unchanged.
"""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directories',nargs='+',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();out=[]
for d in a.directories:
    if not (d/'summary.json').exists():continue
    prov=json.loads((d/'provenance.json').read_text())
    for raw in json.loads((d/'summary.json').read_text()):
        row={'run':str(d),'case':raw['case'],'netlist':prov['netlist'],'hold_scale':prov.get('candidate_hold_capacitance_scale',1),'separate_conditioners':prov.get('separate_conditioners',False),
             'actual_bgr':prov.get('actual_bgr',False),'solver_status':raw['solver_status'],'wall_s':raw['wall_s'],'shunt_V':raw['shunt_V'],'endpoint_us':prov.get('transient_endpoint_us',1.52),
             'range_scope':'within specified SENSE range' if 0<=raw['shunt_V']<=.05 else 'outside-contract diagnostic','boundary_characterization_status':raw['decision_status'],'system_band_status':'not run'}
        samples=raw.get('sampled_output_V',[]);row['sampled_evaluations']=len(samples)
        if raw['solver_status']=='passed' and samples:
            hard=raw['case'].startswith('hard');nom=(254 if hard else 153)*1.04/5300
            row['nominal_threshold_shunt_V']=nom
            if 'step_metrics' in raw:
                row['boundary_characterization_status']='not applicable (step stimulus)';row['system_band_status']='not applicable (step characterization)'
                row['analog_step_status']=raw['analog_step_status'];row['step_metrics']=raw['step_metrics']
            elif prov.get('seed') is not None or prov.get('actual_bgr'):
                row['system_band_status']='not applicable (statistical calibration probe)'
            elif .9*nom<raw['shunt_V']<1.1*nom:
                row['system_band_status']='not applicable (inside adopted10percent ambiguity band)'
            else:
                expected=raw['shunt_V']>=1.1*nom
                row['system_band_status']='passed' if all((v>.6)==expected for v in samples) else 'failed'
            if not 0<=raw['shunt_V']<=.05: row['system_band_status']='not applicable (outside specified0-50mV SENSE range)'
            row['quiet_soft_hard_V']=raw.get('quiet_soft_hard_V')
            row['measures']=raw['measures']
        out.append(row)
result={'scope':'Loaded SENSE/TRIP fixtures with ideal BGR or actual BGR as marked per row; no RTL/pads/FET. Boundary criterion quiet differential1mV is diagnostic, not the adopted10percent system criterion. Step criteria refer to analog output only.',
        'raw_summary_note':'Prefix fixture has3evaluations despite legacy raw-summary text sayinglast10. Step raw summaries may retain an inactive quiet-state wrong-decision count; assessment marks that criterion not applicable.',
        'cases':out,'attempted':len(out),'solver_completed':sum(r['solver_status']=='passed' for r in out),'timed_out':sum(r['solver_status']=='not run to completion' for r in out),'solver_failed':sum(r['solver_status']=='failed' for r in out)}
with a.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))
