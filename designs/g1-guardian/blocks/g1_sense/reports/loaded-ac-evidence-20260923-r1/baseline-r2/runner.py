#!/usr/bin/env python3
"""One bounded actual-BGR/full-TRIP loaded SENSE AC or conditional Tian leaf."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import numpy as np
from run_loaded_noise_audit import (SIM, TRIP, REFERENCE, IMAGE, MANIFEST, SOURCE,
    sha, table, group_commands, read_group, quiet_values, warning_inventory, run_bounded)

MODES=('baseline','differential','common','psrr_vdda','psrr_vdd','tian_voltage','tian_current')
OBS=['v(isense)','v(vped)','v(vref_buf)','v(xs.vp)','v(xs.vn)','i(vdda)','i(vdd)']

def source_probe(original):
    line='XOTA vp vn iptat isense vdd vss g1_ota_main_candidate'
    changed='XOTA vp main_loop_e iptat isense vdd vss g1_ota_main_candidate'
    addition='Vmain_probe main_loop_e vn dc 0 ac {pv}\nImain_probe vss main_loop_e dc 0 ac {pi}\n'
    assert original.count(line)==1 and 'main_loop_e' not in original
    derived=original.replace(line,changed).replace('.ends',addition+'.ends',1)
    assert derived.replace(addition,'',1).replace(changed,line)==original
    return derived

def make_deck(original, out, mode, groups):
    prefix=original.split('tran 0.2n 1.02u 0 0.2n\n')[0]
    before=prefix.split('.control\n')[0]
    restored=before
    if mode in ('differential','common'):
        old='Vsh shp 0 dc 0.025000000000000001'
        new='Vsh shp noise_cm dc 0.025000000000000001 ac '+('1' if mode=='differential' else '0')+'\nVcm_measure noise_cm 0 dc 0 ac '+('-.5' if mode=='differential' else '1')
        old_x='XS shp 0 vref iptat isense vped vref_buf vdda 0 g1_sense'
        new_x=old_x.replace('XS shp 0 ','XS shp noise_cm ')
        assert before.count(old)==before.count(old_x)==1
        before=before.replace(old,new).replace(old_x,new_x)
        assert before.replace(new,old).replace(new_x,old_x)==restored
    elif mode=='baseline':
        old='Vsh shp 0 dc 0.025000000000000001'
        before=before.replace(old,old+' ac 1')
        assert before.replace(old+' ac 1',old)==restored
    elif mode.startswith('psrr_'):
        old='Vdda vdda 0 dc {VDDA}' if mode=='psrr_vdda' else 'Vdd vdd 0 dc {VDD}'
        assert before.count(old)==1
        before=before.replace(old,old+' ac 1')
        assert before.replace(old+' ac 1',old)==restored
    else:
        old='.include qualification/'+REFERENCE+'/sense.spice'
        assert before.count(old)==1
        before=before.replace(old,'.include '+str(out/'probe.spice'))
        before+='.param pv=%d pi=%d\n'%(mode=='tian_voltage',mode=='tian_current')
    controls=prefix.split('.control\n',1)[1]
    observation_save='save '+' '.join(OBS)+(' v(xs.main_loop_e) i(v.xs.vmain_probe)' if mode.startswith('tian_') else '')+'\n'
    assert controls.count('\nop\n')==1
    controls=controls.replace('\nop\n','\n'+observation_save+'op\n')
    controls+='echo AC_DC_OBS_BEGIN\nprint '+' '.join(OBS)+'\necho AC_DC_OBS_END\n'
    if mode.startswith('tian_'):
        controls+='echo EXTRA_SHUNT_BEGIN\nprint v(xs.main_loop_e)\necho EXTRA_SHUNT_END\n'
    controls+='set numdgt=17\nset wr_singlescale\nset wr_vecnames\n'
    if mode.startswith('tian_'):
        controls+='save v(xs.main_loop_e) i(v.xs.vmain_probe)\n'
    if mode in ('differential','common'):
        controls+='save v(noise_cm)\n'
    controls+='ac dec 100 1 1g\n'
    if mode.startswith('tian_'):
        controls+='let ir=real(-i(v.xs.vmain_probe))\nlet ii=imag(-i(v.xs.vmain_probe))\nlet vr=real(v(xs.main_loop_e))\nlet vi=imag(v(xs.main_loop_e))\n'
        controls+='wrdata '+str(out/'ac.dat')+' ir ii vr vi\n'
    else:
        controls+='let ac_re=real(v(isense))\nlet ac_im=imag(v(isense))\n'
        controls+='wrdata '+str(out/'ac.dat')+' ac_re ac_im\n'
        if mode in ('differential','common'):
            controls+='let p_re=real(v(shp))\nlet p_im=imag(v(shp))\nlet n_re=real(v(noise_cm))\nlet n_im=imag(v(noise_cm))\n'
            controls+='wrdata '+str(out/'input_basis.dat')+' p_re p_im n_re n_im\n'
    controls+='setplot op1\nset numdgt=15\n'+group_commands(groups,'AFTER')
    controls+='echo LOADED_AC_END\nquit 0\n.endc\n.end\n'
    return before+'.control\n'+controls

def observations(log):
    section,=re.findall(r'^AC_DC_OBS_BEGIN\n(.*?)^AC_DC_OBS_END$',log,re.M|re.S)
    pairs=dict((k,float(v)) for k,v in re.findall(r'^([vi]\([^\n=]+\))\s*=\s*(\S+)',section,re.M))
    assert set(pairs)==set(OBS) and all(math.isfinite(v) for v in pairs.values())
    return pairs

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mode',choices=MODES,required=True)
    p.add_argument('--baseline',type=Path)
    p.add_argument('--noise-anchor',type=Path,required=True)
    p.add_argument('--prepare-only',action='store_true')
    a=p.parse_args(); assert not a.output.exists()
    if not a.prepare_only:assert os.sched_getaffinity(0)=={1}
    ref=TRIP/'qualification'/REFERENCE
    prep=json.loads((ref/'preparation.json').read_text()); old=json.loads((ref/'summary.json').read_text())[0]['phases'][0]
    expected=old['parameters_before']; assert len(expected)==11512 and sha(ref/'sense.spice')==SOURCE
    assert all(sha(ref/n)==h for n,h in prep['source_hashes'].items())
    noise=json.loads((a.noise_anchor/'summary.json').read_text())
    assert noise['status'].startswith('passed') and all(noise['parameter_OP_provenance'][k] for k in ['full11512_exact','legacy27_exact','quiet9OP_exact'])
    base=None
    if a.mode!='baseline':
        assert a.baseline
        base=json.loads((a.baseline/'summary.json').read_text());assert base['status']=='passed source/OP/AC leaf'
    a.output.mkdir(parents=True)
    if a.mode.startswith('tian_'):(a.output/'probe.spice').write_text(source_probe((ref/'sense.spice').read_text()))
    deck=make_deck((ref/'population_transient.cir').read_text(),a.output,a.mode,prep['groups'])
    (a.output/'probe.cir').write_text(deck);(a.output/'runner.py').write_bytes(Path(__file__).read_bytes())
    contract=dict(mode=a.mode,reference_run=REFERENCE,source_hashes=prep['source_hashes'],
        noise_anchor_summary_sha256=sha(a.noise_anchor/'summary.json'),baseline_summary_sha256=sha(a.baseline/'summary.json') if base else None,
        deck_sha256=sha(a.output/'probe.cir'),source_inverse_exact=True,model_identity='11512/legacy27 exact before/after/reference',
        DC_voltage_bound_V=1e-6,DC_supply_current_bound_A=1e-9,
        DC_criterion_origin='Unchanged established run_return_ratio.py probe equivalence; exact float equality separately recorded.',
        extra_probe_rshunt_ohm=1e12 if a.mode.startswith('tian_') else None,
        input_basis='Differential: P+.5,N-.5; common: P1,N1. DC P25mV/N0 unchanged. Ideal new common-mode node has0V DC so its unchanged global rshunt carries0A.',
        method='Existing Tian2001 two injections at mainOTA negative input; V=e-f,Iground-to-e, if=-I(V). Allotherloops remainclosed.',
        criteria='Conditional PM>=60deg, GM>=10dB; closed-loop gain19.9..20.1 andBW>=2MHz. PSRR/CMRR descriptive (no allocated limit).',
        scope='ActualBGR586/fullTRIP TT25C seed73001 frozenclockDC. Not globalstability, periodicnoise, physicalPEX or cornerpopulation.',watchdog_s=120)
    (a.output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    if a.prepare_only:print(json.dumps(contract,indent=2));return
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=MANIFEST,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],text=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==prep['expected_runtime_identity']
    (a.output/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,OCI_config_digest=IMAGE,OCI_manifest_digest=MANIFEST),indent=2)+'\n')
    with (a.output/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str(a.output/'probe.cir')],stream,a.output/'run.json',120,cwd=TRIP,interval_s=1)
    log=(a.output/'run.log').read_text()
    errors=[s for s in log.splitlines() if re.search(r'(?i)^error|timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse',s)]
    result=dict(status='failed',mode=a.mode,runtime=state,errors=errors,warnings=warning_inventory(log),scope=contract['scope'])
    try:
        assert state['status']=='completed' and state['returncode']==0 and not errors and 'LOADED_AC_END' in log
        for when in ['BEFORE','AFTER']:
            allparams=read_group(log,'NON_BGR_'+when,prep['groups']['NON_BGR'])+read_group(log,'BGR_'+when,prep['groups']['BGR'])
            assert allparams==expected
        assert read_group(log,'LEGACY27_AFTER',prep['groups']['LEGACY27'])==[[q,dict(expected)[q]] for q in prep['groups']['LEGACY27']]
        op=quiet_values(log);obs=observations(log)
        delta={k:abs(op[k]-old['quiet_op_V'][k]) for k in op}
        result.update(full11512_and27_exact=True,quiet_op_V=op,operating_point=obs,quiet_op_reference_abs_delta_V=delta,quiet_op_reference_exact=op==old['quiet_op_V'])
        assert max(delta.values())<=1e-6
        if base:
            difference={k:abs(obs[k]-base['operating_point'][k]) for k in OBS}
            assert all(difference[k]<=(1e-9 if k.startswith('i(') else 1e-6) for k in OBS)
            result['baseline_DC_probe_equivalence']=dict(status='passed',abs_delta=difference,exact=obs==base['operating_point'])
        else:assert op==old['quiet_op_V']
        if a.mode.startswith('tian_'):
            header=['frequency','ir','ii','vr','vi']
            match,=re.findall(r'^v\(xs.main_loop_e\)\s*=\s*(\S+)',log,re.M)
            result['extra_probe_rshunt_signed_DC_A']=float(match)/1e12
        else:header=['frequency','ac_re','ac_im']
        ac=table(a.output/'ac.dat',header)
        assert ac.shape==(901,len(header)) and abs(ac[-1,0]/1e9-1)<1e-12
        result['frequency_Hz']=[float(ac[0,0]),float(ac[-1,0])];result['rows']=len(ac)
        if a.mode=='baseline':
            anchor=table(a.noise_anchor/'ac.dat',['frequency','ac_re','ac_im'])
            assert np.array_equal(ac[:701],anchor)
            result['prior_noise_AC_first701_exact']=True
        if a.mode in ('differential','common'):
            basis=table(a.output/'input_basis.dat',['frequency','p_re','p_im','n_re','n_im'])
            target=np.array([.5,0,-.5,0] if a.mode=='differential' else [1,0,1,0])
            assert np.array_equal(basis[:,0],ac[:,0]) and float(np.max(np.abs(basis[:,1:]-target)))<=1e-12
            result['input_basis_max_abs_error']=float(np.max(np.abs(basis[:,1:]-target)))
        result['status']='passed source/OP/AC leaf'
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as e:result['analysis_error']=repr(e)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='warnings'},indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)

if __name__=='__main__':main()
