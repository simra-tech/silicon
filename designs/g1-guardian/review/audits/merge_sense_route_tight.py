#!/usr/bin/env python3
"""Strict merge of retained38tuples plus exact70tuple continuation; old failures retained."""
import argparse,hashlib,json,math
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,required=True);p.add_argument('--resume',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest();load=lambda path:json.loads(path.read_text())
old=load(a.original/'summary.json');new=load(a.resume/'summary.json');oldprov=load(a.original/'provenance.json');newprov=load(a.resume/'provenance.json');binding=load(a.resume/'resume_binding.json');contract=load(a.resume/'contract.json')
assert new['status']=='passed' and old['status']=='failed'
assert binding['prior_summary_sha256']==sha(a.original/'summary.json') and binding['prior_provenance_sha256']==sha(a.original/'provenance.json')
assert old['model_and_source_hashes_unchanged'] and new['model_and_source_hashes_unchanged']
assert sha(a.original/'contract.json')==sha(a.resume/'contract.json')==oldprov['contract_sha256']==newprov['contract_sha256']
assert all(oldprov[key]==newprov[key] for key in ('source_sha256','candidate_sha256','R_ohm','PDK_models','PDK_commit'))
prefix=old['results'][:-1];assert [row['name'] for row in prefix]==binding['completed_tuples_retained']
rows=prefix+new['results'];assert len(rows)==108 and len({row['name'] for row in rows})==108
assert [row['name'] for row in rows]==oldprov['planned_tuples']
leaves=[];metrics=[]
for index,row in enumerate(rows):
    assert row['status']=='passed' and row['zero_R_equivalence_status']=='passed' and row['candidate_gain_status']=='passed'
    folder=a.original if index<len(prefix) else a.resume
    assert set(row['runs'])==set(contract['fixtures']) and len(row['runs'])==3
    for kind,run in row['runs'].items():
        leaf=folder/row['name']/kind;state=load(leaf/'run.json');assert state['status']=='completed' and state['returncode']==0
        assert run['status']=='passed' and run['precision_ok'] and not run['errors'] and len(run['rows'])==9
        assert sha(leaf/'fixture.cir')==run['deck_sha256']==state['deck_sha256']
        assert state['source_sha256']==oldprov['source_sha256'] and state['contract_sha256']==oldprov['contract_sha256']
        assert all(len(values)==7 and all(math.isfinite(value) for value in values) for values in run['rows'].values())
        for cm in (-.1,0,.3):
            zero=run['rows'][f't0_c{cm}_s0'];half=run['rows'][f't0_c{cm}_s0.025'];full=run['rows'][f't0_c{cm}_s0.05'];gain=(full[0]-zero[0])/.05
            metrics.append({'tuple':row['name'],'fixture':kind,'CM_V':cm,'gain_V_per_V':gain,'zero_shunt_output_offset_from_VPED_V':zero[0]-zero[1],
                'midpoint_linearity_residual_V':half[0]-(zero[0]+full[0])/2,'supply_current_zero_shunt_A':-zero[6]})
        leaves.append({'tuple':row['name'],'fixture':kind,'deck_sha256':run['deck_sha256'],'run_json_sha256':sha(leaf/'run.json'),'log_sha256':sha(leaf/'tool.log'),'wall_s':state['wall_s']})
assert len(leaves)==324 and len(metrics)==972
route=[row for row in metrics if row['fixture']=='candidate_R1'];lo,hi=contract['gain_limits_V_per_V'];assert all(lo<=row['gain_V_per_V']<=hi for row in route)
maxvoltage=max(row['voltage_max_abs_delta_V'] for row in rows);maxcurrent=max(row['current_max_limit_ratio'] for row in rows);maxgain=max(row['gain_max_abs_delta_V_per_V'] for row in rows)
assert maxvoltage<=contract['voltage_abs_limit_V'] and maxcurrent<=1 and maxgain<contract['gain_abs_delta_limit_V_per_V']
result={'status':'passed focused108tuple tight route-R gate','tuples':108,'leaves':324,'OP_points':2916,'candidate_sha256':oldprov['candidate_sha256'],'source_sha256':oldprov['source_sha256'],
    'contract_sha256':oldprov['contract_sha256'],'PDK_commit':oldprov['PDK_commit'],'R_ohm':oldprov['R_ohm'],'model_source_contract_binding':'passed',
    'input_hashes':{'original_summary':sha(a.original/'summary.json'),'resume_summary':sha(a.resume/'summary.json'),'resume_binding':sha(a.resume/'resume_binding.json')},
    'script_sha256':sha(Path(__file__)),'zero_R_equivalence_max_voltage_delta_V':maxvoltage,'zero_R_equivalence_max_current_limit_ratio':maxcurrent,'zero_R_equivalence_max_gain_delta_V_per_V':maxgain,
    'candidate_gain_range_V_per_V':[min(row['gain_V_per_V'] for row in route),max(row['gain_V_per_V'] for row in route)],
    'candidate_zero_shunt_offset_from_VPED_range_V':[min(row['zero_shunt_output_offset_from_VPED_V'] for row in route),max(row['zero_shunt_output_offset_from_VPED_V'] for row in route)],
    'metrics':metrics,'leaf_bindings':leaves,'retained_failures':['Original lowerprecision108exactparity aggregate failed5tuples; unchanged.','Original2xRdiagnostic39gainfailures; unchanged, notrerun.','Initialtightaggregate externallySIGTERM-interruptedtuple39; retained asfailed/incomplete, no numericalfailureinference.'],
    'scope':'Fixed LEF-based geometryR(.103ohm/sq,20ohm/via are pinnedtableMAXreferencevalues, not nominaltargets) overfrozen108MOS/resistor/supply/temp tuples. No metal/via temperaturecorner bound, coupled RC, gm4source, via21candidate electrical qualification, fullIO acceptance or productionpromotion.'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({key:value for key,value in result.items() if key not in ('metrics','leaf_bindings')},indent=2))
