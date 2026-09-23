#!/usr/bin/env python3
"""Separate bounded cross-source DC gate; original exact-DC failure stays failed."""
import argparse
import json
from pathlib import Path
import numpy as np
from run_loaded_compensation_candidate import candidate_source,parameter_gate
from run_loaded_followthrough import get_reference,errors
from run_loaded_ac_audit import observations,OBS
from run_loaded_noise_audit import sha,table,quiet_values
from analyze_loaded_ac_audit import controls,crossings


def bounded_dc(quiet,obs,old_quiet,old_obs):
    assert quiet.keys()==old_quiet.keys() and obs.keys()==old_obs.keys()
    assert len(quiet)==9 and set(obs)==set(OBS)
    q={n:abs(quiet[n]-old_quiet[n]) for n in quiet}
    d={n:abs(obs[n]-old_obs[n]) for n in obs}
    assert all(np.isfinite(list(q.values()))) and all(np.isfinite(list(d.values())))
    assert all(v<=1e-6 for v in q.values())
    assert all(v<=(1e-9 if n.startswith('i(') else 1e-6) for n,v in d.items())
    return dict(status='passed new bounded cross-source comparison',
                voltage_limit_V=1e-6,current_limit_A=1e-9,
                quiet_abs_delta_V=q,observed_abs_delta=d,
                exact_quiet_equality=quiet==old_quiet,
                exact_observed_equality=obs==old_obs)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--leaf',type=Path,required=True)
    p.add_argument('--original-baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--comparison',choices=['bounded','own-source'],default='bounded')
    a=p.parse_args();assert not a.output.exists();controls()
    old=json.loads((a.leaf/'summary.json').read_text())
    contract=json.loads((a.leaf/'contract.json').read_text())
    assert old['status']=='failed' and old['mode']=='differential'
    if a.comparison=='bounded':
        assert old['analysis_error']=="AssertionError('Passive candidate DC must match its exact original differential topology')"
    else:
        assert old['analysis_error'] in ["AssertionError('Passive candidate DC must match its exact original differential topology')",'AssertionError()']
        assert old['old_exact_DC_status']=='failed'
    assert old['runtime']['status']=='completed' and old['runtime']['returncode']==0
    case=old['case']
    _,ref,prep,expected,_=get_reference('settling','rise') if case=='nominal' else get_reference('adverse',case)
    assert json.loads((a.leaf/'provenance.json').read_text())['runtime_identity']==prep['expected_runtime_identity']
    assert all(sha(ref/n)==h for n,h in prep['source_hashes'].items())
    length=format(contract['main_RZ_body_area_um2']['candidate'],'g')
    width=str(contract.get('main_MIM_width_um',50))
    assert (a.leaf/'candidate.spice').read_text()==candidate_source((ref/'sense.spice').read_text(),length,width)
    assert sha(a.leaf/'candidate.spice')==contract['candidate_source_sha256']
    anchor=json.loads((a.original_baseline/'summary.json').read_text())
    ac=json.loads((a.original_baseline/'contract.json').read_text())
    assert anchor['status'] in ['passed source/OP/AC leaf','passed source/OP/finite leaf']
    assert anchor['full11512_and27_exact'] and anchor['mode']=='differential'
    assert ac['source_hashes']==prep['source_hashes']
    assert ac['reference_run']==contract['reference_run']
    if case=='nominal':assert sha(a.original_baseline/'summary.json')==contract['original_differential_summary_sha256']
    log=(a.leaf/'run.log').read_text()
    assert not errors(log) and ('LOADED_AC_END' if case=='nominal' else 'LOADED_FOLLOWTHROUGH_END') in log
    result=dict(old);result['original_failure_analysis_error']=result.pop('analysis_error')
    result['original_failure_status']=old['status']
    result['parameter_gate']=parameter_gate(log,prep['groups'],expected,width)
    quiet=quiet_values(log);obs=observations(log)
    assert len(quiet)==9 and set(obs)==set(OBS)
    assert np.isfinite(list(quiet.values())+list(obs.values())).all()
    if a.comparison=='bounded':
        result['new_bounded_DC_gate']=bounded_dc(quiet,obs,anchor['quiet_op_V'],anchor['operating_point'])
    else:
        try:
            diagnostic=bounded_dc(quiet,obs,anchor['quiet_op_V'],anchor['operating_point'])
        except AssertionError:
            diagnostic=dict(status='failed cross-source diagnostic',voltage_limit_V=1e-6,current_limit_A=1e-9,
                quiet_abs_delta_V={n:abs(quiet[n]-anchor['quiet_op_V'][n]) for n in quiet},
                observed_abs_delta={n:abs(obs[n]-anchor['operating_point'][n]) for n in obs})
        assert diagnostic['status']=='failed cross-source diagnostic'
        result['cross_source_DC_diagnostic']=diagnostic
        result['baseline_acceptance']='Own-source finite OP, full native parameter accounting and exact source inverse only. No cross-source DC equivalence; paired probes must independently meet original 1uV/1nA gate against this candidate OP.'
    assert result['quiet_op_V']==quiet and result['operating_point']==obs
    wave=table(a.leaf/'ac.dat',['frequency','ac_re','ac_im'])
    basis=table(a.leaf/'input_basis.dat',['frequency','p_re','p_im','n_re','n_im'])
    assert wave.shape==(901,3) and np.array_equal(wave[:,0],basis[:,0])
    assert np.max(abs(basis[:,1:]-np.array([.5,0,-.5,0])))<=1e-12
    mag=abs(wave[:,1]+1j*wave[:,2]);db=20*np.log10(mag)
    points=crossings(wave[:,0],db,db[0]-3.010299956639812)
    result.update(status='passed candidate source/finite leaf',reanalysis_only=True,
        gain_1Hz_V_per_V=float(mag[0]),gain_status='passed' if 19.9<=mag[0]<=20.1 else 'failed',
        halfpower_downcrossings_Hz=[q[2] for q in points],
        bandwidth_status='passed' if points and points[0][2]>=2e6 else 'failed',
        original_failed_leaf_bindings={n:sha(a.leaf/n) for n in
            ['summary.json','contract.json','runner.py','candidate.spice','probe.cir','run.log','ac.dat','input_basis.dat','provenance.json']},
        original_baseline_bindings={n:sha(a.original_baseline/n) for n in ['summary.json','contract.json','probe.cir']},
        qualification_scope=('New explicit cross-source 1uV/1nA diagnostic; original exact-DC gate remains FAILED.' if a.comparison=='bounded' else 'Own-source characterization only; original exact AND bounded cross-source DC diagnostics remain FAILED.')+' Saved data only, no simulator/tolerance/card change, no prior-campaign or physical adoption.')
    a.output.mkdir(parents=True)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in result.items() if k not in ['warnings','parameter_gate']},indent=2))


if __name__=='__main__':main()
