#!/usr/bin/env python3
"""Zero-C private-port parity control; no extracted capacitors or adoption."""
import argparse,json,os,subprocess
from pathlib import Path
import numpy as np
from expose_comp45_internal_nodes import expose,SOURCE
from test_expose_comp45_internal_nodes import tests as topology_tests
from run_loaded_compensation_candidate import parameter_gate
from run_loaded_followthrough import get_reference,errors
from run_loaded_ac_audit import observations
from run_loaded_noise_audit import TRIP,IMAGE,MANIFEST,sha,quiet_values,warning_inventory,table,run_bounded

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--anchor',type=Path,required=True);p.add_argument('--anchor-proof',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--cpu',type=int,choices=[1,7],required=True)
    p.add_argument('--mode',choices=['noise','step'],required=True);p.add_argument('--zero-noise-proof',type=Path)
    a=p.parse_args();assert os.sched_getaffinity(0)=={a.cpu} and not a.output.exists()
    proof=json.loads(a.anchor_proof.read_text());assert proof['status']=='passed candidate followthrough leaf' and proof['mode']==a.mode
    raw=(a.anchor/'candidate.spice').read_bytes();assert sha(a.anchor/'candidate.spice')==SOURCE
    text,sourceproof=expose(raw);controls=topology_tests(raw)
    if a.mode=='step':
        assert a.zero_noise_proof
        prior=json.loads(a.zero_noise_proof.read_text());assert prior['status']=='passed exact zero-C instrumentation control' and prior['mode']=='noise'
    else:assert a.zero_noise_proof is None
    a.output.mkdir(parents=True);newsource=a.output/'sense_private_nodes.spice';newsource.write_text(text)
    olddeck=(a.anchor/'probe.cir').read_text();oldsource=str(a.anchor/'candidate.spice')
    assert olddeck.count('.include '+oldsource)==1
    deck=olddeck.replace('.include '+oldsource,'.include '+str(newsource))
    # Only output destinations change beyond the explicitly proved source copy.
    other_old=str(a.anchor)+'/';other_new=str(a.output)+'/'
    deck=deck.replace(other_old,other_new)
    restored=deck.replace(other_new,other_old).replace('.include '+str(a.anchor/'sense_private_nodes.spice'),'.include '+oldsource)
    assert restored==olddeck
    (a.output/'probe.cir').write_text(deck)
    for name in ['run_comp45_private_zero_c.py','expose_comp45_internal_nodes.py','test_expose_comp45_internal_nodes.py']:
        (a.output/name).write_bytes((Path(__file__).parent/name).read_bytes())
    run,ref,prep,expected,_=get_reference('settling','rise')
    bound=120 if a.mode=='noise' else 600
    contract=dict(mode=a.mode,cpu=a.cpu,source=sourceproof,controls=controls,deck_inverse_exact=True,
        anchor_bindings={n:sha(a.anchor/n) for n in ['candidate.spice','probe.cir','run.log','summary.json']},
        anchor_proof_sha256=sha(a.anchor_proof),watchdog_s=bound,added_capacitors=0,
        criteria='Exact own11512/27, nineOP/sevenOBS and saved AC/noise or transient wave bytes; no tolerance waiver.',
        positive_C='not run',complete_field_coverage='failed/unresolved')
    (a.output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=MANIFEST,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],text=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==prep['expected_runtime_identity']
    (a.output/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,OCI_config=IMAGE,runtime_exact=True),indent=2)+'\n')
    with (a.output/'run.log').open('x') as log:state=run_bounded(['ngspice','-b',str(a.output/'probe.cir')],log,a.output/'run.json',bound,cwd=TRIP,interval_s=1)
    log=(a.output/'run.log').read_text();result=dict(status='failed zero-C instrumentation control',mode=a.mode,runtime=state,errors=errors(log),warnings=warning_inventory(log))
    try:
        assert state['status']=='completed' and state['returncode']==0 and not result['errors']
        assert ('LOADED_NOISE_END' if a.mode=='noise' else 'LOADED_FOLLOWTHROUGH_END') in log
        assert sha(newsource)==sourceproof['diagnostic_sha256']
        assert all(sha(a.anchor/n)==h for n,h in contract['anchor_bindings'].items())
        params=parameter_gate(log,prep['groups'],expected,'45')
        result.update(parameter_gate=params,own_parameter_gate_exact=params==proof['parameter_gate'],
            quiet_op_V=quiet_values(log),operating_point=observations(log))
        result['own_OP_exact']=result['quiet_op_V']==proof['quiet_op_V']
        result['own_observations_exact']=result['operating_point']==proof['operating_point']
        files=['ac.dat','noise.dat'] if a.mode=='noise' else ['phase0.dat']
        result['saved_wave_exact']={n:(a.output/n).read_bytes()==(a.anchor/n).read_bytes() for n in files}
        result['wave_diagnostics']={}
        for n in files:
            old=np.loadtxt(a.anchor/n,skiprows=1);new=np.loadtxt(a.output/n,skiprows=1)
            assert np.isfinite(old).all() and np.isfinite(new).all()
            result['wave_diagnostics'][n]=dict(old_shape=list(old.shape),new_shape=list(new.shape),
                max_absolute_difference=float(np.max(np.abs(old-new))) if old.shape==new.shape else None)
        assert result['own_parameter_gate_exact'] and result['own_OP_exact'] and result['own_observations_exact'] and all(result['saved_wave_exact'].values())
        result['status']='passed exact zero-C instrumentation control'
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as exc:result['analysis_error']=repr(exc)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['parameter_gate','warnings']},indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)

if __name__=='__main__':main()
