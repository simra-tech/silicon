#!/usr/bin/env python3
"""Own-source C45/R100 noise/step characterization; no original-source transfer."""
import argparse,json,math,re,subprocess
from pathlib import Path
import numpy as np
import os
def verify_cpu(cpu):
    assert cpu in (1,7) and os.sched_getaffinity(0)=={cpu}
from run_loaded_compensation_candidate import candidate_source,parameter_gate
from run_loaded_followthrough import get_reference,step_deck,TARGETS,errors
from run_loaded_ac_audit import OBS,observations
from run_loaded_noise_audit import (TRIP,IMAGE,MANIFEST,sha,quiet_values,warning_inventory,
    table,run_bounded,build_deck,integrate,tests)

SOURCE='bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782'


def prepare(original,out,mode,case,groups,run):
    base=build_deck(original,out,groups) if mode=='noise' else step_deck(original,out,mode,TARGETS[case],groups)
    old='.include qualification/'+run+'/sense.spice'
    new='.include '+str(out/'candidate.spice')
    assert base.count(old)==1
    deck=base.replace(old,new)
    assert deck.replace(new,old)==base
    prefix,control=deck.split('.control\n',1)
    assert control.count('\nop\n')==1
    save='save '+' '.join(OBS)+'\n'
    print_op='echo AC_DC_OBS_BEGIN\nprint '+' '.join(OBS)+'\necho AC_DC_OBS_END\n'
    control=control.replace('\nop\n','\n'+save+'op\n'+print_op)
    restored=control.replace('\n'+save+'op\n'+print_op,'\nop\n')
    assert prefix+'.control\n'+restored==deck
    return prefix+'.control\n'+control


def spectrum(out,log):
    ac=table(out/'ac.dat',['frequency','ac_re','ac_im'])
    noise=table(out/'noise.dat',['frequency','onoise_spectrum','inoise_spectrum'])
    assert ac.shape==noise.shape==(701,3) and np.array_equal(ac[:,0],noise[:,0])
    assert abs(noise[0,0]-1)<1e-12 and abs(noise[-1,0]/1e7-1)<1e-12 and np.all(noise[:,1:]>0)
    gain=np.hypot(ac[:,1],ac[:,2]);assert np.all(gain>0)
    error=float(np.max(abs(noise[:,1]/noise[:,2]/gain-1)));assert error<=1e-6
    bands=[]
    for upper in [1e3,1e5,2e6,1e7]:
        actual_upper=min(upper,float(noise[-1,0]))
        for duration in [0.,20e-9,200e-9,1e-6]:
            powers=[integrate(noise[:,0],noise[:,c]**2,1,actual_upper,duration) for c in [1,2]]
            coarse=[integrate(noise[:,0],noise[:,c]**2,1,actual_upper,duration,8) for c in [1,2]]
            err=max(abs(a/b-1) for a,b in zip(coarse,powers));assert err<=1e-6
            bands.append(dict(lower_Hz=1,upper_Hz=upper,actual_upper_Hz=actual_upper,assumed_boxcar_s=duration,
                output_rms_V=math.sqrt(powers[0]),input_stimulus_referred_rms_V=math.sqrt(powers[1]),
                quadrature_8_vs_16_relative_error=err))
    totals={k:float(v) for k,v in re.findall(r'^(onoise_total|inoise_total)\s*=\s*(\S+)',log,re.M)}
    assert set(totals)=={'onoise_total','inoise_total'} and all(math.isfinite(v) and v>0 for v in totals.values())
    band=next(r for r in bands if r['upper_Hz']==1e7 and r['assumed_boxcar_s']==0)
    return dict(AC_ASD_normalization_max_relative_error=error,gain_1Hz_V_per_V=float(gain[0]),bands=bands,
        native_printed_totals=totals,native_vs_integrated_relative_difference={
        'output':totals['onoise_total']/band['output_rms_V']-1,
        'input':totals['inoise_total']/band['input_stimulus_referred_rms_V']-1},
        noise_acceptance='not allocated; native/integrated discrepancy retained, no asserted equality')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['noise','dc','step'],required=True)
    p.add_argument('--case',choices=['nominal','rise','fall'],required=True)
    p.add_argument('--cpu',type=int,choices=[1,7],required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--initial-anchor',type=Path)
    p.add_argument('--initial-proof',type=Path)
    p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    assert not a.output.exists() and ((a.mode=='noise' and a.case=='nominal') or (a.mode!='noise' and a.case in TARGETS))
    if not a.prepare_only:verify_cpu(a.cpu)
    controls=tests()
    run,ref,prep,expected,original_op=get_reference('settling','rise')
    original=(ref/'sense.spice').read_text();candidate=candidate_source(original,'62','45')
    from prepare_comp45_rz_remedy import change
    candidate=change(candidate,100)
    a.output.mkdir(parents=True);(a.output/'candidate.spice').write_text(candidate)
    assert sha(a.output/'candidate.spice')==SOURCE
    deck=prepare((ref/'population_transient.cir').read_text(),a.output,a.mode,a.case,prep['groups'],run)
    (a.output/'probe.cir').write_text(deck);(a.output/'runner.py').write_bytes(Path(__file__).read_bytes())
    bound=600 if a.mode=='step' else 120
    anchor=None
    if a.mode=='step':
        assert a.initial_anchor
        anchor=json.loads((a.initial_proof or a.initial_anchor/'summary.json').read_text())
        assert anchor['status']=='passed candidate followthrough leaf' and anchor['mode']=='noise'
        assert sha(a.initial_anchor/'candidate.spice')==SOURCE
        if a.initial_proof:
            assert anchor['saved_data_only'] and all(sha(a.initial_anchor/n)==h for n,h in anchor['original_failed_leaf_bindings'].items())
    contract=dict(mode=a.mode,case=a.case,cpu=a.cpu,reference_run=run,candidate_source_sha256=SOURCE,
        original_source_hashes=prep['source_hashes'],reference_preparation_sha256=sha(ref/'preparation.json'),
        source_inverse_exact=True,deck_sha256=sha(a.output/'probe.cir'),watchdog_s=bound,controls=controls,
        initial_anchor_bindings={n:sha(a.initial_anchor/n) for n in ['summary.json','contract.json','candidate.spice','run.log']} if anchor else None,
        initial_proof_sha256=sha(a.initial_proof) if a.initial_proof else None,
        scope='New C45/R100 own-source seed73001 TT25C3.3/1.2V actual BGR586/fullTRIP fixture. No old population/physical adoption.',
        criteria=dict(native11511_and_legacy27_exact=True,candidate11512_before_after_exact=True,
            initial_step_OP_exact_to_own_noise=True,finite_wave_and_exact_headers=True,
            noise_ASD_V_per_sqrtHz=True,normalization_relative_max=1e-6,integration_relative_max=1e-6),
        noise_scope='ClockDC0; one-sided differential excitation also changes common mode. 20ns latency is NOT averaging aperture; boxcars are explicit sensitivities, not physical filters.',
        step_scope='Unchanged 0.2ns maxstep,1.02us,1ns edge at200ns. Independent finalDC target; no endpoint fitting or invented timing criterion.')
    (a.output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    if a.prepare_only:return
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=MANIFEST,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],text=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==prep['expected_runtime_identity']
    (a.output/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,OCI_config_digest=IMAGE,OCI_manifest_digest=MANIFEST,runtime_exact=True),indent=2)+'\n')
    with (a.output/'run.log').open('x') as log:
        state=run_bounded(['ngspice','-b',str(a.output/'probe.cir')],log,a.output/'run.json',bound,cwd=TRIP,interval_s=1)
    log=(a.output/'run.log').read_text()
    result=dict(status='failed',mode=a.mode,case=a.case,runtime=state,errors=errors(log),warnings=warning_inventory(log))
    try:
        assert state['status']=='completed' and state['returncode']==0 and not result['errors']
        assert ('LOADED_NOISE_END' if a.mode=='noise' else 'LOADED_FOLLOWTHROUGH_END') in log
        assert all(sha(ref/n)==h for n,h in prep['source_hashes'].items()) and sha(a.output/'candidate.spice')==SOURCE
        result['parameter_gate']=parameter_gate(log,prep['groups'],expected,'45')
        op=quiet_values(log);obs=observations(log)
        assert len(op)==9 and np.isfinite(list(op.values())+list(obs.values())).all()
        result.update(quiet_op_V=op,operating_point=obs,
            original_source_OP_exact=op==original_op,original_source_comparison='diagnostic only; deliberately changed source')
        if a.mode=='noise':result.update(spectrum(a.output,log))
        elif a.mode=='step':
            result['own_initial_OP_exact']=op==anchor['quiet_op_V']
            result['own_initial_observations_exact']=obs==anchor['operating_point']
            assert result['own_initial_OP_exact'] and result['own_initial_observations_exact']
            line,=re.findall(r'^wrdata .+$',(ref/'population_transient.cir').read_text(),re.M)
            header=['time']+line.split()[2:];wave=table(a.output/'phase0.dat',header)
            assert wave.shape[1]==18 and wave[-1,0]>=1.02e-6 and wave[0,0]<=1e-12
            expected_sh=np.interp(wave[:,0],[0,200e-9,201e-9,1.02e-6],[.025,.025,TARGETS[a.case],TARGETS[a.case]])
            error=float(max(abs(wave[:,header.index('v(shp)')]-expected_sh)));assert error<=1e-12
            result.update(rows=len(wave),endpoint_s=float(wave[-1,0]),input_waveform_max_abs_error_V=error)
        result['status']='passed candidate followthrough leaf'
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as exc:result['analysis_error']=repr(exc)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['warnings','parameter_gate']},indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__=='__main__':main()
