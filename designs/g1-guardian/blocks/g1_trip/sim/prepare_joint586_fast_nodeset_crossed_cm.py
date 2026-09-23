#!/usr/bin/env python3
"""Prepare72 fixed-nodeset fast crossed checks only after its own first-sample audit."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from run_joint586_fast_nodeset_staged import SIM,ROOT,REFERENCE,sha,adverse_deck
from audit_joint586_fast_nodeset_calibration import first_sample_gate
from prepare_joint586_crossed_cm_contract import rows
from result_directory import allocate_run


def checks_for_corner(scope,corner,tree):
    assert corner=='fast','Only separately qualified fixed-nodeset fast method; no other corner inheritance'
    assert tree['bracket_status']=='passed selected probes'
    result=[]
    for declared in scope['checks']:
        if declared['corner']!=corner:continue
        row=dict(declared,index=len(result))
        row['codes']=[tree[row['calibration_code_key']][k] for k in ['soft','hard']]
        assert all(type(code) is int and 0<=code<=255 for code in row['codes'])
        result.append(row)
    assert len(result)==72 and sum(r['kind']=='guard' for r in result)==48
    assert all(r['seed']==78101 for r in result)
    return result


def make_deck(original,run_id,row):
    deck=adverse_deck(original,REFERENCE,run_id,row['seed'],row['codes'],row['shunt_V'],row['condition'],row['corner'])
    old='qualification/'+run_id+'/phase0.dat'
    assert deck.count(old)==1
    deck=deck.replace(old,'qualification/'+run_id+'/p%02d/phase0.dat'%row['index'])
    assert deck.count('.nodeset ')==1 and '.options klu' not in deck.lower()
    return deck


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True)
    p.add_argument('--first-sample-audit',type=Path,required=True);p.add_argument('--first-sample-audit-sha256',required=True)
    a=p.parse_args();assert sha(a.first_sample_audit)==a.first_sample_audit_sha256
    audit=json.loads(a.first_sample_audit.read_text());assert first_sample_gate(audit)
    record,=audit['records'];assert record['seed']==78101 and record['corner']=='fast'
    parent=SIM/'qualification'/record['run'];summary,=json.loads((parent/'summary.json').read_text())
    assert sha(parent/'summary.json')==record['summary_sha256'] and sha(parent/'provenance.json')==record['provenance_sha256']
    assert summary['seed']==78101 and summary['corner']=='fast' and len(summary['parameters_before_first_probe'])==11512
    contract=SIM/'qualification/joint586-fast-nodeset-staged-contract-20260923-a/contract.json'
    campaign=json.loads(contract.read_text());assert sha(contract)==audit['campaign_contract_sha256']
    assert all(sha(ROOT/n)==v for n,v in campaign['live_bindings_sha256'].items())
    scope_path=SIM/'qualification/joint586-crossed-cm144-contract-20260923-a.json'
    assert sha(scope_path)=='f250640a8ede68ef9d6fa8471e56597ec000cb695877e71017c3d0d9fb1f1e06'
    scope=json.loads(scope_path.read_text());assert scope['checks']==rows(campaign['required_crossed_CM_conditions'])
    reference=SIM/'qualification'/REFERENCE;prep=json.loads((reference/'preparation.json').read_text())
    assert all(sha(reference/n)==v for n,v in prep['source_hashes'].items())
    declared=checks_for_corner(scope,'fast',summary['calibration'])
    out=allocate_run(SIM,a.run_id)
    for name in ['sense.spice','trip.spice','bgr.spice','population_inventory.json']:
        shutil.copyfile(str(reference/name),str(out/name))
    for row in declared:
        leaf=out/('p%02d'%row['index']);leaf.mkdir()
        deck=make_deck((reference/'population_transient.cir').read_text(),a.run_id,row)
        (leaf/'probe.cir').write_text(deck);row['deck_sha256']=hashlib.sha256(deck.encode()).hexdigest()
    paths=[a.first_sample_audit,parent/'summary.json',parent/'provenance.json',contract,scope_path,
        reference/'preparation.json',reference/'population_transient.cir',reference/'population_inventory.json']
    paths += [SIM/n for n in ['prepare_joint586_fast_nodeset_crossed_cm.py','run_joint586_fast_nodeset_crossed_cm.py',
        'audit_joint586_fast_nodeset_crossed_cm.py','test_joint586_fast_nodeset_crossed_cm.py','run_joint586_fast_nodeset_staged.py',
        'audit_joint586_fast_nodeset_calibration.py','run_joint586_transients.py','prepare_joint586_adverse.py',
        'prepare_joint586_adverse_transients.py','prepare_bgr_calibration_probe.py','run_nominal_clock_probe.py',
        'audit_joint586_adverse_transients.py','run_joint586_fast_nodeset_rescue.py','prepare_joint586_fastcold_nodeset.py','wave_archive.py']]
    bindings=dict(campaign['live_bindings_sha256']);bindings.update({str(q.absolute().relative_to(ROOT)):sha(q) for q in paths})
    packet=dict(run=a.run_id,corner='fast',seed=78101,cases=declared,expected_vector=summary['parameters_before_first_probe'],
        groups=prep['groups'],source_hashes=prep['source_hashes'],inventory_sha256=prep['inventory_sha256'],
        runtime_identity=prep['expected_runtime_identity'],prospective_sampling=prep['prospective_sampling'],
        first_sample_audit_sha256=a.first_sample_audit_sha256,live_bindings_sha256=bindings,
        watchdog_s=1200,scope='72 fast fixed-nodeset deterministic crossed checks of the same already calibrated78101 draw. Original48guards/24residuals,1200s,11512+27,19vectors. No new independent population sample, refit, retry or source/solver adoption. This does not inherit original non-nodeset fast fixture outcomes; original failures and cross-method exact-wave failures remain retained.')
    (out/'preparation.json').write_text(json.dumps(packet,indent=2)+'\n');print(out.name,sha(out/'preparation.json'))


if __name__=='__main__':main()

