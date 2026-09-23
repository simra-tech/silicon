#!/usr/bin/env python3
"""Owncorner transient controls plus actual-SHN append-only output parity pair."""
import argparse
import difflib
import json
from pathlib import Path
import re
from prepare_joint586_adverse import SIM,ROOT,REFERENCE,SEEDS,transform_fixture,sha
from result_directory import allocate_run

CASES=[('enabled','enabled',[25]),('repeat','enabled',[25]),('changed','changed',[25]),
    ('disabled','disabled',[25]),('disabledchanged','disabledchanged',[25]),
    ('hot','return',[125]),('cold','return',[-40]),('return','return',[25,125,-40,25]),
    ('cm0_old18','enabled',[25]),('cm0_shn19','enabled',[25])]


def append_shn(deck):
    assert 'XS shp shn ' in deck and 'Vshn shn 0 dc ' in deck
    assert 'v(shn)' not in deck
    changed=[]
    for line in deck.splitlines(True):
        if line.startswith('.save ') or line.startswith('wrdata '):
            assert line.endswith('\n')
            changed.append(line[:-1]+' v(shn)\n')
        elif line=='echo BIAS_OBSERVATION_OP_END\n':
            changed.append(line+'echo SHN_OBSERVATION_OP\nprint v(shn)\necho SHN_OBSERVATION_OP_END\n')
        else:changed.append(line)
    result=''.join(changed)
    inverse=result.replace('echo SHN_OBSERVATION_OP\nprint v(shn)\necho SHN_OBSERVATION_OP_END\n','').replace(' v(shn)\n','\n')
    assert inverse==deck
    return result


def phases(original,old_id,new_id,seed,temperatures):
    body,control=original.split('.control\n')
    header,rest=control.split('reset\n',1)
    assert header.count('setseed 73001\n')==1
    assert rest.startswith('echo PHASE0_BEGIN\n')
    phase,ending=rest[len('echo PHASE0_BEGIN\n'):].split('echo PHASE0_END\n')
    assert ending=='echo JOINT_POPULATION_TRAN_END\nquit 0\n.endc\n.end\n'
    body,n=re.subn(r'^\.temp .+$','.temp '+str(float(temperatures[0])),body,flags=re.M);assert n==1
    out=body+'.control\n'+header.replace('setseed 73001\n','setseed %d\n'%seed)+'reset\n'
    for index,temp in enumerate(temperatures):
        if len(temperatures)>1:out+='set temp=%d\n'%temp
        out+='echo PHASE%d_BEGIN\n'%index+phase.replace('/phase0.dat','/phase%d.dat'%index)+'echo PHASE%d_END\n'%index
    out+=ending
    out=out.replace(old_id,new_id)
    assert out.count('\nreset\n')==out.count('\nsetseed ')==1
    assert out.count('tran 0.2n 1.02u 0 0.2n\n')==len(temperatures)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--op-audit',type=Path,required=True)
    p.add_argument('--corner',choices=['slow','fast'],required=True)
    p.add_argument('--campaign-id',required=True)
    a=p.parse_args();assert re.fullmatch('[a-z0-9-]+',a.campaign_id)
    contract=json.loads(a.contract.read_text());audit=json.loads(a.op_audit.read_text())
    assert audit['status']=='passed strict owncorner OP qualification' and all(audit['checks'].values())
    assert audit['corner']==a.corner and audit['contract_sha256']==sha(a.contract)
    reference=SIM/'qualification'/REFERENCE;original=(reference/'population_transient.cir').read_text()
    originalprep=json.loads((reference/'preparation.json').read_text())
    path=SIM/'qualification'/(a.campaign_id+'.json');assert not path.exists()
    records=[]
    for label,oplabel,temperatures in CASES:
        opcase,=[x for x in contract['op_controls'] if x['corner']==a.corner and x['label']==oplabel]
        op=(ROOT/opcase['deck']).parent
        row,=json.loads((op/'summary.json').read_text())
        assert row['op_qualification_status']=='passed'
        assert all(sha(op/n)==v for n,v in audit['receipts_sha256'][oplabel].items())
        indices=[row['phases'].index(next(x for x in row['phases'] if x['temperature_C']==t)) for t in temperatures]
        if len(temperatures)==4:indices=[0,1,2,3]
        run_id=a.campaign_id+'-'+label;out=allocate_run(SIM,run_id)
        for name in opcase['source_hashes']:(out/name).write_bytes((op/name).read_bytes())
        (out/'population_inventory.json').write_bytes((reference/'population_inventory.json').read_bytes())
        common_mode=0. if label.startswith('cm0_') else None
        base,changes=transform_fixture(original,a.corner,3.3,1.2,common_mode)
        deck=phases(base,REFERENCE,run_id,opcase['seed'],temperatures)
        if label=='cm0_shn19':deck=append_shn(deck)
        (out/'population_transient.cir').write_text(deck)
        (out/'declared_adverse_transient_difference.diff').write_text(''.join(difflib.unified_diff(
            original.replace(REFERENCE,'@RUN@').splitlines(True),deck.replace(run_id,'@RUN@').splitlines(True),
            fromfile='qualifiedTypical',tofile=a.corner+'-'+label)))
        bindings={str(q.relative_to(ROOT)):sha(q) for q in [a.contract.resolve(),a.op_audit.resolve(),
            op/'summary.json',op/'provenance.json',op/'population_op.cir',reference/'population_transient.cir',
            reference/'preparation.json',Path(__file__).resolve(),SIM/'run_joint586_adverse_transient.py']}
        prep=dict(run=run_id,label=label,corner=a.corner,seed=opcase['seed'],enabled=opcase['enabled'],
            temperatures_C=temperatures,op_reference=str(op.relative_to(ROOT)),op_phase_indices=indices,
            expected_vectors=[row['phases'][i]['parameters_before'] for i in indices],groups=contract['groups'],
            common_mode_V=common_mode,columns=19 if label=='cm0_shn19' else 18,
            source_hashes=opcase['source_hashes'],deck_sha256=sha(out/'population_transient.cir'),
            inventory_sha256=contract['inventory_sha256'],live_bindings_sha256=bindings,
            expected_runtime_identity=contract['expected_runtime_identity'],prospective_sampling=originalprep['prospective_sampling'],
            watchdog_s=1200*len(temperatures),physical_scope=contract['physical_scope'],
            original18_parity_reference=a.campaign_id+'-cm0_old18' if label=='cm0_shn19' else None,
            scope='Owncorner qualification only. Sources/cards/11512 inventory unchanged. Original5MHz/1.02us/0.6Vactual+legacy20ns decision rules retained. ActualSHN19thvector only ondeclaredCM0outputpair; original18fullbyte/numericprojection mandatory. No population/accuracy/physicaladoption release.')
        (out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n')
        records.append(dict(label=label,run=run_id,preparation_sha256=sha(out/'preparation.json'),deck_sha256=prep['deck_sha256'],watchdog_s=prep['watchdog_s']))
    result=dict(status='not run; owncorner transient qualification andSHNoutputpair prepared',corner=a.corner,
        contract_sha256=sha(a.contract),op_audit_sha256=sha(a.op_audit),cases=records,
        expected_bulk_GiB=.65,no_population_release=True)
    path.write_text(json.dumps(result,indent=2)+'\n');print(path.relative_to(ROOT),sha(path))


if __name__=='__main__':main()
