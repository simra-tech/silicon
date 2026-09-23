#!/usr/bin/env python3
"""Independent own-six KLU checks, including original disabled-to-nominal rule."""
import argparse,gzip,hashlib,json,math,re
from pathlib import Path
from prepare_586_klu_population_qualification import HERE,ROOT,REFERENCES,sha,transform
from run_586_population_control import phase_text,exact_wave
from run_586_source_control import load_wave
from run_bgr_substitution_draw_audit import read_group
from run_586_nearendpoint_recovery import validate_wave
from analyze_586_population import changed_primitives

def numerical_gate(runtime,result,log):
    assert runtime['status']=='completed' and runtime['returncode']==0
    assert result['runtime']==runtime and not result.get('analysis_error') and not result['errors']
    assert not re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse',log,re.I|re.M)
    assert 'Using KLU as Direct Linear Solver' in log

def audit_case(case):
    run=HERE/'runs'/case['run_id'];old=HERE/'runs'/case['original_run']
    prep=json.loads((old/'preparation.json').read_text())
    assert (run/'probe.cir').read_text()==transform((old/'probe.cir').read_text())
    assert all(sha(run/n)==sha(old/n)==v for n,v in case['source_hashes'].items())
    if 'input_binding' in case:assert all(sha(run/n)==v for n,v in case['input_binding'].items())
    else:assert sha(run/'preparation.json')==case['preparation_sha256'] and sha(run/'probe.cir')==case['deck_sha256']
    result,=json.loads((run/'summary.json').read_text());prov=json.loads((run/'provenance.json').read_text());runtime=json.loads((run/'run.json').read_text())
    assert prov['runtime_identity']==prep['runtime'] and all(prov['input_checks'].values())
    assert sha(run/'runner.py')==prov['runner_sha256']
    log=(run/'run.log').read_text();numerical_gate(runtime,result,log)
    enabled=HERE/'runs'/REFERENCES[case['corner']]
    with gzip.open(str(enabled/'phase0.dat.gz'),'rb') as stream:header=stream.readline().decode().split()
    phases=[]
    for index,temp in enumerate(case['temperatures_C']):
        section=phase_text(log,index)
        before={tag:read_group(section,'P%d_%s_BEFORE'%(index,tag),keys) for tag,keys in prep['groups'].items()}
        after={tag:read_group(section,'P%d_%s_AFTER'%(index,tag),keys) for tag,keys in prep['groups'].items()}
        assert sum(map(len,before.values()))==3180 and before==after==case['expected_full3180']
        if not case['mismatch_enabled']:assert before==prep['nominal_parameters']
        blob,data=load_wave(run/('phase%d.dat'%index));vce=validate_wave(blob,data,header)
        values={k:float(v) for k,v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)',section)}
        assert all(k in values and math.isfinite(values[k]) for k in ['freq','t_a','t_b','t_half_a','fout_hi','fout_lo']) and values['freq']>0 and values['t_b']>values['t_a']
        phases.append(dict(temperature_C=temp,parameters_before=before,parameters_after=after,wave_rows=len(data),waveform_sha256=hashlib.sha256(blob).hexdigest(),measurements=values,t2f_hbt_external_vce_max_V=vce))
    return dict(status='passed independent finite/input/full3180 evidence',phases=phases,
        receipts_sha256={n:sha(run/n) for n in ['probe.cir','preparation.json','provenance.json','summary.json','run.json','run.log','runner.py']})

def analyze(own,nominal,corner):
    cases={r['label']:r for r in own['cases'] if r['corner']==corner};assert set(cases)=={'enabled','repeat','changed','disabled','disabledchanged','return'}
    report=dict(corner=corner,status='not run; six-control evidence incomplete',controls={},comparisons={},solver_adoption='not run; separate review required')
    results={}
    for label,case in cases.items():
        if not (HERE/'runs'/case['run_id']/'summary.json').exists():
            report['controls'][label]=dict(status='not run to completion');continue
        try:results[label]=audit_case(case);report['controls'][label]=results[label]
        except (AssertionError,ValueError,OSError,KeyError,IndexError) as error:report['controls'][label]=dict(status='failed evidence gate',error=repr(error))
    nominal_case,=[c for c in nominal['cases'] if c['corner']==corner];nom=HERE/'runs'/nominal_case['run_id']
    if len(results)!=6 or not (nom/'summary.json').exists():
        if any(r['status'].startswith('failed') for r in report['controls'].values()):report['status']='failed evidence gate'
        report['nominal_reference']='not run to completion' if not (nom/'summary.json').exists() else 'not audited until all six complete'
        return report
    try:
        nprep=json.loads((nom/'preparation.json').read_text());assert sha(nom/'preparation.json')==nominal_case['preparation_sha256']
        nrow,=json.loads((nom/'summary.json').read_text());nlog=(nom/'run.log').read_text();nrun=json.loads((nom/'run.json').read_text());nprov=json.loads((nom/'provenance.json').read_text())
        numerical_gate(nrun,nrow,nlog);assert all(nprov['input_checks'].values()) and sha(nom/'runner.py')==nprov['runner_sha256']
        oldnom=HERE/'runs'/nprep['original_run'];oldprep=json.loads((oldnom/'preparation.json').read_text())
        assert nprov['runtime_identity']==json.loads((oldnom/'provenance.json').read_text())['runtime_identity']
        assert (nom/'probe.cir').read_text()==(oldnom/'probe.cir').read_text().replace('\n.control\n','\n.options klu\n.control\n')
        assert all(sha(nom/n)==sha(oldnom/n)==v for n,v in nprep['source_hashes'].items())
        nparams={tag:read_group(nlog,tag+'_BEFORE',keys) for tag,keys in nprep['groups'].items()};nafter={tag:read_group(nlog,tag+'_AFTER',keys) for tag,keys in nprep['groups'].items()}
        assert nparams==nafter==nprep['expected_full3180'] and sum(map(len,nparams.values()))==3180
        nblob,ndata=load_wave(nom/nrow['output_wave']);oldblob,_=load_wave(oldnom/oldprep['output_wave']);validate_wave(nblob,ndata,oldblob.splitlines()[0].decode().split())
        def vector(label,phase=0):return results[label]['phases'][phase]['parameters_before']
        params=dict(enabled_repeat=vector('enabled')==vector('repeat'),enabled_return_initial=vector('enabled')==vector('return'),enabled_return_final=vector('enabled')==vector('return',3),disabledchanged=vector('disabled')==vector('disabledchanged'),disablednominal=vector('disabled')==nparams)
        waves={}
        for name,a,i,b,j in [('repeat','enabled',0,'repeat',0),('return_initial','enabled',0,'return',0),('return_final','enabled',0,'return',3),('disabledchanged','disabled',0,'disabledchanged',0)]:
            waves[name]=exact_wave(HERE/'runs'/cases[a]['run_id']/('phase%d.dat'%i),HERE/'runs'/cases[b]['run_id']/('phase%d.dat'%j))
        waves['disablednominal']=exact_wave(HERE/'runs'/cases['disabled']['run_id']/'phase0.dat',nom/nrow['output_wave'])
        inventory=json.loads((HERE/'runs'/cases['enabled']['run_id']/'population_inventory.json').read_text())
        variation=changed_primitives(inventory,vector('enabled'),vector('changed'));assert len(variation)==1129
        report.update(status='passed six-control same-KLU qualification' if all(params.values()) and all(all(r.values()) for r in waves.values()) and all(r['status']=='passed' for r in variation) else 'failed exact/variation qualification; no waiver',
            comparisons=dict(full3180=params,waveforms=waves),variation=variation,
            nominal_reference=dict(status='passed independent full3180 finite reference',receipts_sha256={n:sha(nom/n) for n in ['probe.cir','preparation.json','provenance.json','summary.json','run.log','run.json']}))
    except (AssertionError,ValueError,OSError,KeyError,IndexError) as error:report.update(status='failed nominal/crossrun evidence gate',error=repr(error))
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--implementation',type=Path,required=True);p.add_argument('--implementation-sha256',required=True);p.add_argument('--corner',choices=['typical','slow','fast'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    assert sha(a.implementation)==a.implementation_sha256
    impl=json.loads(a.implementation.read_text());assert all(sha(ROOT/n)==v for n,v in impl['implementation_bindings_sha256'].items())
    ownpath=ROOT/impl['own6_packet'];nompath=ROOT/impl['nominal_packet'];assert sha(ownpath)==impl['own6_packet_sha256'] and sha(nompath)==impl['nominal_packet_sha256']
    result=analyze(json.loads(ownpath.read_text()),json.loads(nompath.read_text()),a.corner)
    result.update(implementation_sha256=sha(a.implementation),own6_packet_sha256=sha(ownpath),nominal_packet_sha256=sha(nompath),auditor_sha256=sha(Path(__file__)))
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])

if __name__=='__main__':main()
