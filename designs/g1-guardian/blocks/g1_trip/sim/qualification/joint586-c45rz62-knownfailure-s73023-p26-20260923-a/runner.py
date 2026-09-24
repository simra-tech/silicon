"""Four original-method candidate counterexamples; all original failures retained."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
import numpy as np
from prepare_joint586_c45rz62_anchors import ROOT,SIM,CANDIDATE_SHA,CAP,candidate_source
from prepare_joint586_c45rz62_known_failures import transform
from run_joint586_c45rz62_anchors import sha,runtime_gate,scale_interval,open_wave,archive_new_wave,resolve_wave,run_bounded,analyze_wave,validate_saved_nodes,compare
from run_bgr_substitution_draw_audit import read_group
from run_joint586_transients import phase_parameters


def vector_gate(before,after,old,legacy,expected_legacy):
    assert len(before)==len(after)==len(old)==11512 and before==after
    assert [r[0] for r in before]==[r[0] for r in old] and len({r[0] for r in before})==11512
    assert [r for r in before if r[0]!=CAP]==[r for r in old if r[0]!=CAP]
    assert legacy==expected_legacy and len(legacy)==27
    law=scale_interval(dict(old)[CAP],dict(before)[CAP],'45');assert law['status']=='passed'
    return dict(parameters_before=before,parameters_after=after,legacy27=legacy),law


def source_gate(out,prep):
    original=SIM/'qualification'/prep['original_run'];parent=original.parent
    assert all(sha(ROOT/n)==v for n,v in prep['bindings_sha256'].items())
    assert prep['watchdog_s']==1200 and prep['tmax']=='0.2ns'
    assert all(sha(out/n)==v for n,v in prep['source_hashes'].items())
    assert sha(out/'sense.spice')==CANDIDATE_SHA and (out/'sense.spice').read_text()==candidate_source((parent/'sense.spice').read_text())
    assert sha(out/'population_inventory.json')==prep['inventory_sha256']
    deck=(out/'probe.cir').read_text();assert deck==transform((original/'probe.cir').read_text(),parent.name,original.name,prep['run_id'],prep['seed'])
    assert sha(out/'probe.cir')==prep['deck_sha256']
    assert [l for l in deck.splitlines() if l.lower().startswith('.nodeset')]==prep['original_nodesets']
    validate_saved_nodes(deck,(out/'trip.spice').read_text());return original


def input_observation(data,prep):
    assert data.shape[1]==len(prep['wave_header']) and np.isfinite(data).all()
    if data.shape[1]==19:
        mean=(data[:,17]+data[:,18])/2;diff=data[:,17]-data[:,18]
        assert max(abs(mean-prep['condition'][4]))<1e-12 and max(abs(diff-prep['shunt_V']))<1e-12
        return dict(mean_common_mode_minmax_V=[float(min(mean)),float(max(mean))],differential_minmax_V=[float(min(diff)),float(max(diff))],shn_minmax_V=[float(min(data[:,18])),float(max(data[:,18]))])
    assert data.shape[1]==18;return dict(status='legacy18; actualSHN observation not run, original fixture unchanged')


def inspect_case(out,prep,state,log):
    original=source_gate(out,prep);runtime_gate(state,log)
    section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S);groups=prep['groups']
    before=read_group(section,'NON_BGR_BEFORE',groups['NON_BGR'])+read_group(section,'BGR_BEFORE',groups['BGR'])
    # The original TRANS fixture emits27 ungrouped legacy rows, not an OP-only marker.
    parsed=phase_parameters(section,groups,before)
    params,law=vector_gate(before,parsed['parameters_after'],prep['original_full11512'],parsed['legacy27'],prep['original_legacy27'])
    with open_wave(out/'phase0.dat','rb') as f:blob=f.read()
    with open_wave(original/'phase0.dat','rb') as f:oldblob=f.read()
    names=blob.splitlines()[0].decode().split();assert names==prep['wave_header']==oldblob.splitlines()[0].decode().split()
    values=lambda b:np.array([list(map(float,line.split())) for line in b.splitlines()[1:] if line.strip()])
    data,old=values(blob),values(oldblob);observation=input_observation(data,prep)
    assert np.all(np.diff(data[:,0])>0) and abs(data[-1,0]-1.02e-6)<1e-18
    analysis=analyze_wave(data[:,:13].tolist(),prep['prospective_sampling']);assert analysis['sampling_status']=='passed'
    originalsummary=json.loads((original/'summary.json').read_text());comparison=compare(old[:,:18],data[:,:18],names[:18],originalsummary['wave_analysis'],analysis,prep['comparison_bounds'])
    decisions={k:v['measured_edge_decision'] for k,v in analysis['comparators'].items()};expected=prep['unchanged_expected_hard']
    return dict(numerical_status='passed',parameter_audit=params,native_scale_law=law,actual_input_observation=observation,wave_analysis=analysis,
        observed_decisions=decisions,unchanged_expected_decision=expected,original_frozen_code_residual_status='passed' if all(v is expected for v in decisions.values()) else 'failed',
        intentional_cross_source_first18_comparisons=comparison,exact_old_wave_bytes=blob==oldblob,exact_old_numeric=np.array_equal(old,data),exact_old_grid=np.array_equal(old[:,0],data[:,0]),
        candidate_wall_s=state['wall_s'],original_wall_s=originalsummary['wall_s'],
        scope='Original fixed failed-condition codes and original0.2ns/SPARSE/nodesets; source changes only mainC45/RZ62. Any success is a paired diagnostic, not candidate recalibration/population/physical adoption. Full19 preserved where original had19; first18 descriptive comparisons plus explicitSHN observations.')


def bindings(path,digest):
    f=ROOT/path;assert sha(f)==digest;d=json.loads(f.read_text());assert len(d['controls'])==4
    assert all(sha(ROOT/n)==v for n,v in d['bindings_sha256'].items());return d


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execution',required=True);p.add_argument('--execution-sha256',required=True);p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True);a=p.parse_args()
    execution=bindings(a.execution,a.execution_sha256);case,=[c for c in execution['controls'] if c['run_id']==a.run_id];out=SIM/'qualification'/a.run_id
    assert sha(out/'preparation.json')==case['preparation_sha256'];prep=json.loads((out/'preparation.json').read_text());assert not (out/'run.json').exists();source_gate(out,prep)
    pd=Path('/foss/pdks/ihp-sg13g2');runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==prep['expected_runtime_identity'];(out/'runner.py').write_bytes(Path(__file__).read_bytes())
    (out/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,runner_sha256=sha(Path(__file__)),preparation_sha256=case['preparation_sha256'],execution_sha256=a.execution_sha256,source_hashes=prep['source_hashes'],arguments=sys.argv[1:]),indent=2)+'\n')
    with (out/'run.log').open('x') as f:state=run_bounded(['ngspice','-b',str((out/'probe.cir').relative_to(SIM))],f,out/'run.json',1200,cwd=SIM,interval_s=1)
    result=dict(numerical_status='failed',original_frozen_code_residual_status='not run')
    try:result.update(inspect_case(out,prep,state,(out/'run.log').read_text()))
    except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:result['analysis_error']=repr(error)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    if (out/'phase0.dat').exists():archive_new_wave(out/'phase0.dat')
    print(result['numerical_status'],result['original_frozen_code_residual_status']);raise SystemExit(0 if result['numerical_status']=='passed' else 1)


if __name__=='__main__':main()
