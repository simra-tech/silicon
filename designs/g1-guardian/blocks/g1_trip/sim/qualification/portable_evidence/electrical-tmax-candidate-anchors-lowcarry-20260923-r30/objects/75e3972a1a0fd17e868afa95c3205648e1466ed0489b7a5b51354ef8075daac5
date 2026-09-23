"""Three original-step candidate diagnostics only; never inherited calibration qualification."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
import numpy as np
from prepare_joint586_c45rz62_anchors import ROOT,SIM,PARENT,CAP,CANDIDATE_SHA,candidate_source,deck_transform
from prepare_joint586_tmax_probe import sha
from run_joint586_tmax_probe import runtime_gate
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import run_bounded,analyze_wave,validate_saved_nodes
from compare_joint586_tmax_probe import compare
from c45rz62_native_scale import scale_interval
from wave_archive import open_wave,archive_new_wave,resolve_wave


def source_and_input_gate(out,prep):
    assert prep['tmax']=='0.2n' and prep['seed']==73001 and prep['watchdog_s']==1200
    assert all(sha(ROOT/n)==v for n,v in prep['live_bindings_sha256'].items())
    assert all(sha(out/n)==v for n,v in prep['source_hashes'].items())
    assert sha(out/'sense.spice')==CANDIDATE_SHA
    assert (out/'sense.spice').read_text()==candidate_source((PARENT/'sense.spice').read_text())
    assert sha(out/'population_inventory.json')==prep['inventory_sha256']
    original=PARENT/prep['original_leaf'];deck=(out/'probe.cir').read_text()
    assert deck==deck_transform((original/'probe.cir').read_text(),PARENT.name,prep['original_leaf'],prep['run_id'],'0.2n')
    assert sha(out/'probe.cir')==prep['deck_sha256']
    validate_saved_nodes(deck,(out/'trip.spice').read_text())
    return original


def candidate_parameter_gate(section,prep):
    params=phase_parameters(section,prep['groups'],prep['expected_candidate_parameters'])
    assert params['legacy27']==prep['expected_legacy27']
    observed=params['parameters_before'];old=prep['expected_old_parameters']
    assert len(old)==len(observed)==11512
    assert [r for r in observed if r[0]!=CAP]==[r for r in old if r[0]!=CAP]
    law=scale_interval(dict(old)[CAP],dict(observed)[CAP],'45');assert law['status']=='passed'
    assert law==prep['native_scale_law']
    return params,law


def inspect_case(out,prep,state,log):
    original=source_and_input_gate(out,prep);runtime_gate(state,log)
    section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S)
    # Full parameters and native area law are gates BEFORE waveform observations.
    params,law=candidate_parameter_gate(section,prep)
    with open_wave(out/'phase0.dat','rb') as f:blob=f.read()
    with open_wave(original/'phase0.dat','rb') as f:oldblob=f.read()
    names=blob.splitlines()[0].decode().split();assert names==oldblob.splitlines()[0].decode().split()
    values=lambda b:np.array([list(map(float,line.split())) for line in b.splitlines()[1:] if line.strip()])
    data,old=values(blob),values(oldblob)
    assert data.shape[1]==18 and np.isfinite(data).all() and np.all(np.diff(data[:,0])>0) and abs(data[-1,0]-1.02e-6)<1e-18
    analysis=analyze_wave(data[:,:13].tolist(),prep['prospective_sampling']);assert analysis['sampling_status']=='passed'
    oldsummary=json.loads((original/'summary.json').read_text())
    comparisons=compare(old,data,names,oldsummary['wave_analysis'],analysis,prep['method_comparison_bounds'])
    return dict(numerical_status='passed',parameter_audit=params,native_scale_law=law,wave_analysis=analysis,
        intentional_cross_source_comparisons= comparisons,exact_old_wave_bytes=blob==oldblob,exact_old_numeric=np.array_equal(old,data),
        exact_old_grid=np.array_equal(old[:,0],data[:,0]),old_codes=prep['codes'],original_wall_s=oldsummary['wall_s'],candidate_wall_s=state['wall_s'],
        scope='Intentional C45/RZ62 circuit change at original0.2ns. Original fixed calibration codes are diagnostic stimuli, not new-source calibration. Cross-source exact/screen failures retained descriptively; no population, physical-source or solver adoption.')


def bindings(execution,execution_sha):
    path=ROOT/execution;assert sha(path)==execution_sha;d=json.loads(path.read_text())
    assert all(sha(ROOT/n)==v for n,v in d['bindings_sha256'].items())
    assert len(d['controls'])==3 and [c['leaf'] for c in d['controls']]==['p00','p08','p09']
    assert all(c['tmax']=='0.2n' for c in d['controls'])
    return d


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execution',required=True);p.add_argument('--execution-sha256',required=True)
    p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True);a=p.parse_args();d=bindings(a.execution,a.execution_sha256)
    case,=[c for c in d['controls'] if c['run_id']==a.run_id];out=SIM/'qualification'/a.run_id
    assert sha(out/'preparation.json')==case['preparation_sha256'];prep=json.loads((out/'preparation.json').read_text());assert not (out/'run.log').exists()
    source_and_input_gate(out,prep)
    pd=Path('/foss/pdks/ihp-sg13g2');runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==prep['expected_runtime_identity']
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    (out/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,execution_sha256=a.execution_sha256,runner_sha256=sha(Path(__file__)),
        preparation_sha256=case['preparation_sha256'],source_hashes=prep['source_hashes'],arguments=sys.argv[1:]),indent=2)+'\n')
    with (out/'run.log').open('x') as f:state=run_bounded(['ngspice','-b',str((out/'probe.cir').relative_to(SIM))],f,out/'run.json',1200,cwd=SIM,interval_s=1)
    result=dict(numerical_status='failed',source_adoption='not run')
    try:result.update(inspect_case(out,prep,state,(out/'run.log').read_text()))
    except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:result['analysis_error']=repr(error)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    if (out/'phase0.dat').exists():archive_new_wave(out/'phase0.dat')
    print(result['numerical_status']);raise SystemExit(0 if result['numerical_status']=='passed' else 1)


if __name__=='__main__':main()
