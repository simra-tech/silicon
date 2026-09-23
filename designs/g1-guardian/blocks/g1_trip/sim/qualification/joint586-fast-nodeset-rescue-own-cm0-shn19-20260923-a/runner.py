#!/usr/bin/env python3
"""One fixed-nodeset fast control, original bounds and separate exact comparisons."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from prepare_joint586_fast_nodeset_rescue import SIM,ROOT,sha,transform
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import run_bounded,validate_saved_nodes
from audit_joint586_adverse_transients import wave_check
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave,open_wave


def errors_in(log):
    return [l for l in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse',l,re.I)]


def numerical_gate(state,log):
    assert state['status']=='completed' and state['returncode']==0 and not errors_in(log)
    assert 'Using SPARSE 1.3 as Direct Linear Solver' in log and 'Using KLU as Direct Linear Solver' not in log
    assert 'JOINT_POPULATION_TRAN_END' in log


def phase_audit(case,log,out):
    deck=(out/'population_transient.cir').read_text()
    outputs=[line for line in deck.splitlines() if line.startswith('wrdata ')]
    assert len(outputs)==len(case['temperatures_C'])
    phases=[];blobs=[]
    for i,temp in enumerate(case['temperatures_C']):
        section,=re.findall(r'^PHASE%d_BEGIN\n(.*?)^PHASE%d_END$'%(i,i),log,re.M|re.S)
        params=phase_parameters(section,case['groups'],case['expected_vectors'][i])
        with open_wave(out/('phase%d.dat'%i),'rb') as stream:blob=stream.read()
        assert blob.splitlines()[0].decode().split()==['time']+outputs[i].split()[2:]
        data,analysis=wave_check(blob,case['columns'],case['prospective_sampling'])
        cm=case['common_mode_V'];observation='not applicable: original SHN0 fixture without savedSHN'
        if cm is not None and case['columns']==19:
            means=[(r[17]+r[18])/2 for r in data];diffs=[r[17]-r[18] for r in data]
            assert max(abs(v-cm) for v in means)<1e-12 and max(abs(v-.025) for v in diffs)<1e-12
            observation=dict(mean_common_mode_minmax_V=[min(means),max(means)],differential_minmax_V=[min(diffs),max(diffs)])
        phase=dict(params,temperature_C=temp,decoded_wave_sha256=hashlib.sha256(blob).hexdigest(),wave_rows=len(data),
            wave_analysis=analysis,decisions={k:v['measured_edge_decision'] for k,v in analysis['comparators'].items()},
            actual_input_observation=observation,original_wave_comparison='not run: original full waveform unavailable')
        old=SIM/'qualification'/case['original_run']/('phase%d.dat'%i)
        if old.exists() or Path(str(old)+'.gz').exists():
            with open_wave(old,'rb') as stream:oldblob=stream.read()
            olddata,oldanalysis=wave_check(oldblob,case['columns'],case['prospective_sampling'])
            phase['original_wave_comparison']=dict(decoded_bytes_exact=blob==oldblob,numeric_rows_exact=data==olddata,
                time_grid_exact=[r[0] for r in data]==[r[0] for r in olddata],
                decisions_exact=phase['decisions']=={k:v['measured_edge_decision'] for k,v in oldanalysis['comparators'].items()},
                original_decoded_sha256=hashlib.sha256(oldblob).hexdigest(),scope='All false exact booleans remain failed comparisons; not a tolerance waiver.')
        phases.append(phase);blobs.append(blob)
    return phases,blobs


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--contract-sha256',required=True);p.add_argument('--kind',choices=['own','fixture'],required=True)
    p.add_argument('--label',required=True);p.add_argument('--image-id',required=True);a=p.parse_args()
    assert sha(a.contract)==a.contract_sha256
    packet=json.loads(a.contract.read_text());case,=[c for c in packet['cases'] if c['kind']==a.kind and c['label']==a.label]
    assert case['scheduling']=='new independent process','Completed cache must not be rerun'
    assert all(sha(ROOT/n)==v for n,v in packet['bindings_sha256'].items())
    out=SIM/'qualification'/case['run'];old=SIM/'qualification'/case['original_run']
    assert not (out/'run.log').exists() and json.loads((out/'preparation.json').read_text())==case
    expected,audit=transform((old/'population_transient.cir').read_text(),case['original_run'],case['run'],packet['fixed_guesses'])
    assert (out/'population_transient.cir').read_text()==expected and sha(out/'population_transient.cir')==case['deck_sha256']
    assert audit==case['transform']
    assert all(sha(out/n)==sha(old/n)==v for n,v in case['source_hashes'].items())
    assert sha(out/'population_inventory.json')==case['inventory_sha256']
    validate_saved_nodes(expected,(out/'trip.spice').read_text())
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==case['runtime_identity']
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:],contract_sha256=a.contract_sha256,
        runtime_identity=runtime,source_hashes=case['source_hashes'],runner_sha256=sha(Path(__file__)),
        input_checks=dict(deck=True,sources=True,bindings=True,inventory=True,runtime=True),scope=packet['scope']),indent=2)+'\n')
    with (out/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str((out/'population_transient.cir').relative_to(SIM))],stream,out/'run.json',case['watchdog_s'],cwd=SIM,interval_s=1)
    log=(out/'run.log').read_text();result=dict(status='failed fixed-nodeset control',runtime=state,errors=errors_in(log),
        phases=[],parameter_wave_status='not run',decision_sampling_status='not run',warnings=warning_inventory(log),scope=packet['scope'])
    try:
        numerical_gate(state,log)
        phases,blobs=phase_audit(case,log,out)
        result.update(phases=phases,parameter_wave_status='passed',decision_sampling_status='passed' if all(p['wave_analysis']['sampling_status']=='passed' for p in phases) else 'failed',
            status='passed finite fullparameter fixed-nodeset control; exact comparisons separate')
        if len(blobs)==4:result['return_decoded_bytes_exact']=blobs[0]==blobs[3]
    except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:result['analysis_error']=repr(error)
    (out/'summary.json').write_text(json.dumps([result],indent=2)+'\n')
    for wave in out.glob('phase*.dat'):archive_new_wave(wave)
    print(json.dumps({k:v for k,v in result.items() if k not in ['phases','warnings']},indent=2))
    raise SystemExit(0 if result['parameter_wave_status']==result['decision_sampling_status']=='passed' else 1)


if __name__=='__main__':main()
