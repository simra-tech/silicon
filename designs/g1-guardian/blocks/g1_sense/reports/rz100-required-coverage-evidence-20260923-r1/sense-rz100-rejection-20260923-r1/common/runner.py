#!/usr/bin/env python3
"""R100 nominal source-held partial-field CMRR/PSRR; no full-PEX claim."""
import argparse,json,os,subprocess
from pathlib import Path
import numpy as np
from prepare_rz100_actual_partial_c import prepare,SOURCE
from run_loaded_followthrough import get_reference,errors
from run_loaded_ac_audit import make_deck,OBS,observations
from run_loaded_noise_audit import TRIP,IMAGE,MANIFEST,sha,quiet_values,warning_inventory,table,run_bounded
from run_loaded_compensation_candidate import parameter_gate
from analyze_loaded_ac_audit import rejection_db,controls

MODES=('common','psrr_vdda','psrr_vdd')
PARTIAL='ffb14762659eaf02b6a62e9edea3caa0e143cbc7881378b329d6ab9945a6554b'

def deck_for(original,out,mode,groups,run):
    assert mode in MODES
    deck=make_deck(original,out,mode,groups)
    old='.include qualification/'+run+'/sense.spice'
    new='.include '+str(out/'candidate.spice')
    assert deck.count(old)==1
    updated=deck.replace(old,new)
    assert updated.replace(new,old)==deck
    # Explicit all-input vectors qualify both intended excitation and quiet
    # non-selected supply/input AC sources, including ideal-ground SHN.
    vectors=['real(v(shp))','imag(v(shp))',
             'real(v(noise_cm))' if mode=='common' else '0*real(v(shp))',
             'imag(v(noise_cm))' if mode=='common' else '0*imag(v(shp))',
             'real(v(vdda))','imag(v(vdda))','real(v(vdd))','imag(v(vdd))']
    names=['stim_'+str(i) for i in range(8)]
    extra=''.join('let '+n+'='+v+'\n' for n,v in zip(names,vectors))
    extra+='wrdata '+str(out/'stimulus.dat')+' '+' '.join(names)+'\n'
    old_line='setplot op1\n';assert updated.count(old_line)==1
    updated=updated.replace(old_line,extra+old_line)
    ac='ac dec 100 1 1g\n';saved='save v(vdda) v(vdd)\n'
    assert updated.count(ac)==1;updated=updated.replace(ac,saved+ac)
    assert updated.replace(saved,'').replace(extra,'').replace(new,old)==deck
    return updated

def verify_stimulus(mode,data):
    target={'common':[1,0,1,0,0,0,0,0],
            'psrr_vdda':[0,0,0,0,1,0,0,0],
            'psrr_vdd':[0,0,0,0,0,0,1,0]}[mode]
    assert data.shape==(901,9) and np.isfinite(data).all()
    error=float(np.max(abs(data[:,1:]-np.array(target))))
    assert error<=1e-12
    return error

def tests():
    controls()
    for mode in MODES:
        target={'common':[1,0,1,0,0,0,0,0], 'psrr_vdda':[0,0,0,0,1,0,0,0], 'psrr_vdd':[0,0,0,0,0,0,1,0]}[mode]
        good=np.column_stack([np.geomspace(1,1e9,901),np.tile(target,(901,1))])
        assert verify_stimulus(mode,good)==0
        bad=good.copy();bad[:,1:]*=-1
        try:verify_stimulus(mode,bad)
        except AssertionError:pass
        else:raise AssertionError('wrong sign accepted')
        bad=good.copy();bad[:,[5,7]]=bad[:,[7,5]]
        if mode!='common':
            try:verify_stimulus(mode,bad)
            except AssertionError:pass
            else:raise AssertionError('wrong rail accepted')
    run,ref,prep,_,_=get_reference('settling','rise')
    original=(ref/'population_transient.cir').read_text()
    for mode in MODES:
        made=deck_for(original,Path('/temporary-control-only'),mode,prep['groups'],run)
        assert made.count('wrdata /temporary-control-only/stimulus.dat ')==1
        assert made.count('save v(vdda) v(vdd)\n')==1
    broken=original.replace('Vdda vdda 0 dc {VDDA}','Vdda_wrong vdda 0 dc {VDDA}')
    try:deck_for(broken,Path('/temporary-control-only'),'psrr_vdda',prep['groups'],run)
    except AssertionError:pass
    else:raise AssertionError('missing excitation source accepted')
    return dict(status='passed',controls=['original dB/zero-denominator controls','three exact input-basis controls','three wrong-sign rejects','two wrong-rail rejects','three actual-deck inverse controls','missing source reject'])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['packet','baseline','output']:p.add_argument('--'+key,type=Path)
    p.add_argument('--mode',choices=MODES);p.add_argument('--cpu',type=int,choices=[1,2])
    p.add_argument('--controls-only',action='store_true');a=p.parse_args()
    checked=tests()
    if a.controls_only:print(json.dumps(checked));return
    assert all([a.packet,a.baseline,a.output,a.mode]) and os.sched_getaffinity(0)=={a.cpu} and not a.output.exists()
    packet=json.loads((a.packet/'summary.json').read_text())
    assert packet['status']=='prepared own-native R100 partial-C diagnostic'
    assert packet['canonical_candidate_sha256']==sha(a.packet/'candidate.spice')==SOURCE
    assert packet['diagnostic_source_sha256']==sha(a.packet/'sense_partial_c.spice')==PARTIAL
    source,proof=prepare((a.packet/'candidate.spice').read_bytes(),packet['view_manifest'],packet['raw_rows'])
    assert source==(a.packet/'sense_partial_c.spice').read_text()
    assert packet['added_count']==844 and packet['excluded_count']==134 and packet['zero_noise_sha256'] and packet['zero_step_sha256']
    base=json.loads((a.baseline/'summary.json').read_text());bc=json.loads((a.baseline/'contract.json').read_text())
    assert base['status']=='passed partial-C source/OP/finite leaf' and base['mode']=='differential' and base['case']=='nominal'
    assert base['source_sha256']==sha(a.baseline/'candidate.spice')==PARTIAL and bc['own_native_partial_C']
    run,ref,prep,expected,_=get_reference('settling','rise')
    assert bc['source_hashes']==prep['source_hashes']
    a.output.mkdir(parents=True);(a.output/'candidate.spice').write_text(source)
    (a.output/'probe.cir').write_text(deck_for((ref/'population_transient.cir').read_text(),a.output,a.mode,prep['groups'],run))
    (a.output/'runner.py').write_bytes(Path(__file__).read_bytes())
    contract=dict(mode=a.mode,cpu=a.cpu,source_sha256=PARTIAL,canonical_source_sha256=SOURCE,
        source_hashes=prep['source_hashes'],packet_sha256=sha(a.packet/'summary.json'),
        baseline_bindings={n:sha(a.baseline/n) for n in ['summary.json','contract.json','candidate.spice','ac.dat','provenance.json']},
        helper_hashes={n:sha(Path(__file__).parent/n) for n in ['run_loaded_ac_audit.py','run_loaded_compensation_candidate.py','prepare_rz100_actual_partial_c.py']},
        deck_sha256=sha(a.output/'probe.cir'),watchdog_s=120,DC_gate_V=1e-6,DC_gate_A=1e-9,
        rejection='20log10(abs(differential output transfer)/abs(disturbance output transfer)); no allocated rejection limit',
        scope='ActualBGR/fullTRIP nominal seed73001 frozen clockDC0; same844 source-pair partialC. 134VSUBS omitted, no physicalzero/bound; modelplane/fullfield/finiteR/fullchipfill unresolved. No adoption.')
    (a.output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=MANIFEST,pdk_commit=(pd/'COMMIT').read_text().strip(),ngspice_version=subprocess.check_output(['ngspice','--version'],text=True),model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==prep['expected_runtime_identity']
    (a.output/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,OCI_config=IMAGE,OCI_manifest=MANIFEST),indent=2)+'\n')
    with (a.output/'run.log').open('x') as log:state=run_bounded(['ngspice','-b',str(a.output/'probe.cir')],log,a.output/'run.json',120,cwd=TRIP,interval_s=1)
    log=(a.output/'run.log').read_text();result=dict(status='failed',mode=a.mode,runtime=state,errors=errors(log),warnings=warning_inventory(log),controls=checked)
    try:
        assert state['status']=='completed' and state['returncode']==0 and not result['errors'] and 'LOADED_AC_END' in log
        assert sha(a.output/'candidate.spice')==PARTIAL and all(sha(ref/n)==h for n,h in prep['source_hashes'].items())
        pg=parameter_gate(log,prep['groups'],expected,'45');assert pg['parameters']==base['parameter_gate']['parameters'];result['parameter_gate']=pg
        op=quiet_values(log);obs=observations(log)
        dq={k:abs(op[k]-base['quiet_op_V'][k]) for k in op};dv={k:abs(obs[k]-base['operating_point'][k]) for k in OBS}
        result.update(quiet_op_V=op,operating_point=obs,quiet_delta_V=dq,observation_delta=dv,own_OP_exact=op==base['quiet_op_V'] and obs==base['operating_point'])
        assert max(dq.values())<=1e-6 and all(v<=(1e-9 if k.startswith('i(') else 1e-6) for k,v in dv.items())
        wave=table(a.output/'ac.dat',['frequency','ac_re','ac_im']);diff=table(a.baseline/'ac.dat',['frequency','ac_re','ac_im'])
        stimulus=table(a.output/'stimulus.dat',['frequency']+['stim_'+str(i) for i in range(8)])
        assert wave.shape==diff.shape==(901,3) and np.array_equal(wave[:,0],diff[:,0]) and np.array_equal(stimulus[:,0],wave[:,0])
        result['stimulus_max_error']=verify_stimulus(a.mode,stimulus)
        rejection=rejection_db(diff[:,1]+1j*diff[:,2],wave[:,1]+1j*wave[:,2])
        result['selected_samples']={str(f):dict(actual_frequency_Hz=float(wave[j,0]),rejection_dB=float(rejection[j]),output_transfer_V_per_V=float(abs(wave[j,1]+1j*wave[j,2]))) for f in [1,1e3,1e5,1e6,2e6,1e7] for j in [int(np.argmin(abs(np.log(wave[:,0]/f))))]}
        result.update(status='passed source/OP/finite conditional rejection leaf',rejection_acceptance='not allocated',full_PEX='not qualified',rows=len(wave))
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as exc:result['analysis_error']=repr(exc)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['parameter_gate','warnings']},indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)
if __name__=='__main__':main()
