#!/usr/bin/env python3
"""Bounded source-held adverse AC or nominal loaded-step leaf; no PEX claim."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import numpy as np
from run_loaded_noise_audit import (TRIP, REFERENCE, SOURCE, IMAGE, MANIFEST, sha,
    table, group_commands, read_group, quiet_values, warning_inventory, run_bounded)
from run_loaded_ac_audit import OBS, observations, source_probe

ADVERSE={
    'slow':('joint586-slow-fixture-controls-20260923-b-low_cold_cm0',
        '7da1fda7e7f3f3e46d07f936b6e9d8486950354e1555d6e92bda61188afc6094',
        'abff711fab0d2d409e45b6db4179c8fb0b8187ac3489cec693ed8f56b8758e5a'),
    'fast':('joint586-fast-fixture-controls-20260923-b-high_hot_cm0',
        '35011811c9fd4c50d7a7b0e6eb5e776e23dd7c9e138b089e9b331242bdc9ffd1',
        '12e6aba48123f22001e4b2ea37856761f998e6ad38963126639315ddc85480ae')}
TARGETS={'rise':.05,'fall':0.}
TRAN='tran 0.2n 1.02u 0 0.2n\n'


def errors(log):
    return [l for l in log.splitlines() if re.search(r'(?i)^\s*(?:error|fatal)\b|timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse',l)]


def adverse_deck(original,out,mode,run,groups):
    prefix,_=original.split(TRAN,1)
    before,controls=prefix.split('.control\n',1);unchanged=before
    if mode=='differential':
        for line,ac in [('Vsh shp 0 dc 0.012500000000000001','.5'),('Vshn shn 0 dc -0.012500000000000001','-.5')]:
            assert before.count(line)==1;before=before.replace(line,line+' ac '+ac)
        assert before.replace(' ac .5','').replace(' ac -.5','')==unchanged
    else:
        old='.include qualification/'+run+'/sense.spice';new='.include '+str(out/'probe.spice')
        assert before.count(old)==1;before=before.replace(old,new)
        assert before.replace(new,old)==unchanged
        before+='.param pv=%d pi=%d\n'%(mode=='tian_voltage',mode=='tian_current')
    saved='save '+' '.join(OBS)+' v(shn)'+(' v(xs.main_loop_e) i(v.xs.vmain_probe)' if mode.startswith('tian_') else '')+'\n'
    assert controls.count('\nop\n')==1
    controls=controls.replace('\nop\n','\n'+saved+'op\n')
    controls+='echo AC_DC_OBS_BEGIN\nprint '+' '.join(OBS)+'\necho AC_DC_OBS_END\n'
    if mode.startswith('tian_'):controls+='echo EXTRA_SHUNT_BEGIN\nprint v(xs.main_loop_e)\necho EXTRA_SHUNT_END\n'
    controls+='set numdgt=17\nset wr_singlescale\nset wr_vecnames\nac dec 100 1 1g\n'
    if mode=='differential':
        controls+='let ac_re=real(v(isense))\nlet ac_im=imag(v(isense))\nwrdata '+str(out/'ac.dat')+' ac_re ac_im\n'
        controls+='let p_re=real(v(shp))\nlet p_im=imag(v(shp))\nlet n_re=real(v(shn))\nlet n_im=imag(v(shn))\nwrdata '+str(out/'input_basis.dat')+' p_re p_im n_re n_im\n'
    else:
        controls+='let ir=real(-i(v.xs.vmain_probe))\nlet ii=imag(-i(v.xs.vmain_probe))\nlet vr=real(v(xs.main_loop_e))\nlet vi=imag(v(xs.main_loop_e))\nwrdata '+str(out/'ac.dat')+' ir ii vr vi\n'
    controls+='setplot op1\nset numdgt=15\n'+group_commands(groups,'AFTER')+'echo LOADED_FOLLOWTHROUGH_END\nquit 0\n.endc\n.end\n'
    return before+'.control\n'+controls


def step_deck(original,out,mode,target,groups):
    old='Vsh shp 0 dc 0.025000000000000001';assert original.count(old)==1
    if mode=='step':new=old+' PWL(0 .025 200n .025 201n '+format(target,'.17g')+' 1.02u '+format(target,'.17g')+')'
    else:new='Vsh shp 0 dc '+format(target,'.17g')
    changed=original.replace(old,new);assert changed.replace(new,old)==original
    if mode=='dc':
        changed=changed.split(TRAN,1)[0]+group_commands(groups,'AFTER')+'echo LOADED_FOLLOWTHROUGH_END\nquit 0\n.endc\n.end\n'
    else:
        line,=re.findall(r'^wrdata .+$',changed,re.M);parts=line.split();parts[1]=str(out/'phase0.dat');replacement=' '.join(parts)
        changed=changed.replace(line,'set numdgt=17\n'+replacement)
        addition='set numdgt=15\n'+group_commands({'LEGACY27':groups['LEGACY27']},'AFTER')+'echo LOADED_FOLLOWTHROUGH_END\n'
        assert changed.count('quit 0\n')==1;changed=changed.replace('quit 0\n',addition+'quit 0\n')
        assert changed.replace(addition,'').replace('set numdgt=17\n'+replacement,line).replace(new,old)==original
    return changed


def get_reference(kind,case):
    run=ADVERSE[case][0] if kind=='adverse' else REFERENCE
    ref=TRIP/'qualification'/run
    prep=json.loads((ref/'preparation.json').read_text());saved,=json.loads((ref/'summary.json').read_text())
    if kind=='adverse':
        assert sha(ref/'summary.json')==ADVERSE[case][1]
        assert sha(ref/'population_transient.cir')==ADVERSE[case][2]
        assert saved['status']=='passed required fixture control'
        expected=saved['parameters']['parameters_before']
        assert expected==saved['parameters']['parameters_after']
    else:
        assert saved['parameter_wave_contract_status']=='passed'
        expected=saved['phases'][0]['parameters_before']
    assert len(expected)==11512
    assert sha(ref/'sense.spice')==SOURCE and sha(ref/'population_transient.cir')==prep['deck_sha256']
    assert all(sha(ref/n)==h for n,h in prep['source_hashes'].items())
    return run,ref,prep,expected,quiet_values((ref/'run.log').read_text())


def check_parameters(log,groups,expected):
    for when in ['BEFORE','AFTER']:
        observed=read_group(log,'NON_BGR_'+when,groups['NON_BGR'])+read_group(log,'BGR_'+when,groups['BGR'])
        assert observed==expected
    assert read_group(log,'LEGACY27_AFTER',groups['LEGACY27'])==[[q,dict(expected)[q]] for q in groups['LEGACY27']]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kind',choices=['adverse','settling'],required=True)
    p.add_argument('--case',choices=['slow','fast','rise','fall'],required=True)
    p.add_argument('--mode',choices=['differential','tian_voltage','tian_current','dc','step'],required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--baseline',type=Path)
    p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    assert not a.output.exists()
    assert ((a.kind=='adverse' and a.case in ADVERSE and a.mode in ['differential','tian_voltage','tian_current']) or
            (a.kind=='settling' and a.case in TARGETS and a.mode in ['dc','step']))
    if not a.prepare_only:assert os.sched_getaffinity(0)=={1}
    run,ref,prep,expected,old_op=get_reference(a.kind,a.case)
    base=None
    if a.mode.startswith('tian_'):
        assert a.baseline
        base=json.loads((a.baseline/'summary.json').read_text())
        assert base['status']=='passed source/OP/finite leaf' and base['mode']=='differential' and base['case']==a.case
        assert base['reference_summary_sha256']==sha(ref/'summary.json')
    a.output.mkdir(parents=True)
    original=(ref/'population_transient.cir').read_text()
    if a.kind=='adverse':
        if a.mode.startswith('tian_'):(a.output/'probe.spice').write_text(source_probe((ref/'sense.spice').read_text()))
        deck=adverse_deck(original,a.output,a.mode,run,prep['groups'])
    else:deck=step_deck(original,a.output,a.mode,TARGETS[a.case],prep['groups'])
    (a.output/'probe.cir').write_text(deck);(a.output/'runner.py').write_bytes(Path(__file__).read_bytes())
    bound=600 if a.mode=='step' else 120
    contract=dict(kind=a.kind,case=a.case,mode=a.mode,reference_run=run,
        source_hashes=prep['source_hashes'],reference_summary_sha256=sha(ref/'summary.json'),reference_deck_sha256=sha(ref/'population_transient.cir'),
        reference_log_sha256=sha(ref/'run.log'),deck_sha256=sha(a.output/'probe.cir'),source_inverse_exact=True,
        baseline_summary_sha256=sha(a.baseline/'summary.json') if base else None,
        full11512_and27_exact=True,DC_voltage_bound_V=1e-6,DC_supply_current_bound_A=1e-9,
        gates='Differential andinitialstep9OPexact; TianboundedDC+exactstatus; finalDCbias intentionallydifferent. Allfullparametersheld.',
        watchdog_s=bound,scope='Selected source-held actualBGR/fullTRIP schematic. No global/cornerpopulation/periodicstability/physicalPEX/modelplane acceptance.',
        step_scope='25→50or0mV positiveinput, negativeheld0; 1nsedge200..201ns. IndependentfinalDCtarget, noendpointfitting or inventedsettlinglimit.' if a.kind=='settling' else None)
    (a.output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    if a.prepare_only:print(json.dumps(contract,indent=2));return
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=MANIFEST,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],text=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    (a.output/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,OCI_manifest_digest=MANIFEST,OCI_config_digest=IMAGE,runtime_exact=runtime==prep['expected_runtime_identity']),indent=2)+'\n')
    assert runtime==prep['expected_runtime_identity']
    with (a.output/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str(a.output/'probe.cir')],stream,a.output/'run.json',bound,cwd=TRIP,interval_s=1)
    log=(a.output/'run.log').read_text()
    result=dict(status='failed',kind=a.kind,case=a.case,mode=a.mode,runtime=state,errors=errors(log),warnings=warning_inventory(log),reference_summary_sha256=sha(ref/'summary.json'))
    try:
        assert state['status']=='completed' and state['returncode']==0 and not result['errors'] and 'LOADED_FOLLOWTHROUGH_END' in log
        check_parameters(log,prep['groups'],expected);result['full11512_and27_exact']=True
        op=quiet_values(log);result['quiet_op_V']=op
        result['quiet_op_reference_exact']=op==old_op
        result['quiet_op_reference_abs_delta_V']={k:abs(op[k]-old_op[k]) for k in op}
        if a.mode in ['differential','step']:assert op==old_op
        if a.kind=='adverse':
            obs=observations(log);result['operating_point']=obs
            if base:
                differences={k:abs(obs[k]-base['operating_point'][k]) for k in OBS}
                assert max(result['quiet_op_reference_abs_delta_V'].values())<=1e-6
                assert all(differences[k]<=(1e-9 if k.startswith('i(') else 1e-6) for k in OBS)
                result['baseline_DC_probe_equivalence']=dict(status='passed',abs_delta=differences,exact=obs==base['operating_point'])
                value,=re.findall(r'^v\(xs.main_loop_e\)\s*=\s*(\S+)',log,re.M)
                result['extra_probe_rshunt_signed_DC_A']=float(value)/1e12
            header=['frequency','ac_re','ac_im'] if a.mode=='differential' else ['frequency','ir','ii','vr','vi']
            ac=table(a.output/'ac.dat',header);assert ac.shape==(901,len(header)) and abs(ac[-1,0]/1e9-1)<1e-12
            result['frequency_Hz']=[float(ac[0,0]),float(ac[-1,0])];result['rows']=len(ac)
            if a.mode=='differential':
                basis=table(a.output/'input_basis.dat',['frequency','p_re','p_im','n_re','n_im'])
                assert np.array_equal(basis[:,0],ac[:,0])
                error=float(np.max(abs(basis[:,1:]-np.array([.5,0,-.5,0]))));assert error<=1e-12
                result['input_basis_max_abs_error']=error
        elif a.mode=='step':
            line,=re.findall(r'^wrdata .+$',original,re.M);header=['time']+line.split()[2:]
            wave=table(a.output/'phase0.dat',header)
            assert wave.shape[1]==18 and wave[-1,0]>=1.02e-6 and wave[0,0]<=1e-12
            sh=wave[:,header.index('v(shp)')]
            expected_sh=np.interp(wave[:,0],[0,200e-9,201e-9,1.02e-6],[.025,.025,TARGETS[a.case],TARGETS[a.case]])
            error=float(max(abs(sh-expected_sh)));assert error<=1e-12
            result.update(rows=len(wave),endpoint_s=float(wave[-1,0]),input_waveform_max_abs_error_V=error,settling_acceptance='not assessed; requires independent finalDCtarget analysis')
        result['status']='passed source/OP/finite leaf'
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as exc:result['analysis_error']=repr(exc)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='warnings'},indent=2));raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__=='__main__':main()
