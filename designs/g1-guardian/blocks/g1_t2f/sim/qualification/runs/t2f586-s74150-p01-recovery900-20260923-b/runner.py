#!/usr/bin/env python3
"""One separate exact-input900s recovery; original sample is never rewritten."""
import argparse,hashlib,json,math,re,subprocess,sys
from pathlib import Path
import numpy as np
from run_586_calibration_sample import HERE,ROOT,sha,calibrate
from run_586_population_control import phase_text
from run_586_source_control import load_wave
from run_bgr_substitution_draw_audit import read_group
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave

def validate_wave(blob,data,header):
    assert blob.splitlines()[0].decode().split()==header
    assert data.ndim==2 and data.shape[1]==13 and np.isfinite(data).all()
    assert abs(data[-1,0]-32e-6)<1e-12 and np.all(np.diff(data[:,0])>0)
    vce=float(max(np.abs(data[:,i]-data[:,j]).max() for i,j in [(7,8),(9,8),(10,11),(12,11)]))
    assert vce<=1.6
    return vce

def numerical_gate(state,errors,log):
    assert state['status']=='completed' and state['returncode']==0 and not errors
    assert 'Using SPARSE 1.3 as Direct Linear Solver' in log and 'Using KLU as Direct Linear Solver' not in log

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--implementation',type=Path,required=True);p.add_argument('--implementation-sha256',required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--image-id',required=True);a=p.parse_args()
    assert sha(a.implementation)==a.implementation_sha256
    implementation=json.loads(a.implementation.read_text());packet_path=ROOT/implementation['preparation_packet']
    assert sha(packet_path)==implementation['preparation_packet_sha256']
    assert all(sha(ROOT/n)==v for n,v in implementation['implementation_bindings_sha256'].items())
    case,=[c for c in json.loads(packet_path.read_text())['cases'] if c['seed']==a.seed]
    out=HERE/'runs'/case['run_id'];prep=json.loads((out/'preparation.json').read_text());assert sha(out/'preparation.json')==case['preparation_sha256']
    assert not (out/'run.log').exists() and not (out/'summary.json').exists()
    parent=HERE/'runs'/prep['original_parent'];old=parent/prep['original_leaf']
    assert all(sha(ROOT/n)==v for n,v in prep['bindings_sha256'].items())
    assert all(sha(out/n)==v for n,v in prep['source_hashes'].items())
    assert (out/'probe.cir').read_bytes()==(old/'probe.cir').read_bytes() and sha(out/'probe.cir')==case['exact_deck_sha256']
    inventory=json.loads((out/'population_inventory.json').read_text());assert inventory['parameter_count']==3180 and inventory['primitive_count']==1129
    siblings=[]
    for r in prep['successful_original_leaf_reuse']:
        leaf=parent/r['leaf'];assert all(sha(leaf/n)==v for n,v in r['receipts_sha256'].items())
        row,=json.loads((leaf/'summary.json').read_text());assert row['status']==row['full3180_status']=='passed'
        assert row['parameters_before']==row['parameters_after']==prep['expected_full3180'];siblings.append(row)
    assert len(siblings)==3
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),ngspice=subprocess.check_output(['ngspice','--version'],universal_newlines=True),models_sha256={str(f.relative_to(pd)):sha(f) for f in sorted((pd/'libs.tech/ngspice/models').glob('*.lib'))},osdi_sha256={str(f.relative_to(pd)):sha(f) for f in sorted((pd/'libs.tech/ngspice/osdi').glob('*.osdi'))})
    assert runtime==prep['expected_runtime_identity']
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:],runtime_identity=runtime,implementation_sha256=sha(a.implementation),packet_sha256=sha(packet_path),preparation_sha256=sha(out/'preparation.json'),input_checks=dict(runtime=True,exactdeck=True,sources=True,full3180reference=True,siblinghashes=True),source_hashes=prep['source_hashes'],runner_sha256=sha(Path(__file__))),indent=2)+'\n')
    with (out/'run.log').open('x') as stream:state=run_bounded(['ngspice','-b','probe.cir'],stream,out/'run.json',900,cwd=out,interval_s=1)
    log=(out/'run.log').read_text();errors=[l for l in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse',l,re.I)]
    result=dict(status='failed separate recovery attempt',runtime=state,errors=errors,warnings=warning_inventory(log),full3180_status='not run to completion',separate_calibration_status='not run',original_sample_status='failed original600s; unchanged',seed=a.seed,temperature_C=prep['temperature_C'])
    try:
        numerical_gate(state,errors,log);phase=phase_text(log,0)
        before={tag:read_group(phase,'P0_'+tag+'_BEFORE',keys) for tag,keys in prep['groups'].items()}
        after={tag:read_group(phase,'P0_'+tag+'_AFTER',keys) for tag,keys in prep['groups'].items()}
        assert sum(map(len,before.values()))==3180 and before==after==prep['expected_full3180']
        blob,data=load_wave(out/'phase0.dat');vce=validate_wave(blob,data,prep['expected_header_tokens'])
        values={k:float(v) for k,v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)',phase)}
        assert all(k in values and math.isfinite(values[k]) for k in ['freq','t_a','t_b','t_half_a','fout_hi','fout_lo']) and values['freq']>0 and values['t_b']>values['t_a']
        frequencies={r['temperature_C']:r['measurements']['freq'] for r in siblings};assert prep['temperature_C'] not in frequencies
        frequencies[prep['temperature_C']]=values['freq'];assert set(frequencies)=={25,100,-40,125}
        derived=calibrate(frequencies)
        result.update(status='passed numerical recovery; separate original-criterion calibration recorded',full3180_status='passed',parameters_before=before,parameters_after=after,
            measurements=values,wave_rows=len(data),waveform_sha256=hashlib.sha256(blob).hexdigest(),t2f_hbt_external_vce_max_V=vce,
            separate_calibration_status=derived['status'],separate_calibration=derived,separate_frequencies_Hz=frequencies,
            original_successful_leaf_hashes=prep['successful_original_leaf_reuse'],original_failure=prep['original_failure'],
            scope='Distinct900s recovery, not a replacement or rewrite of original600s failed sample. Original frozen25/100 linear±2C evaluated on hashbound3original leaves+recovery. No population success denominator changes.')
    except (AssertionError,ValueError,OSError,KeyError,IndexError) as error:result.update(status='failed separate recovery attempt',analysis_error=repr(error))
    (out/'summary.json').write_text(json.dumps([result],indent=2)+'\n')
    if (out/'phase0.dat').exists():archive_new_wave(out/'phase0.dat')
    print(json.dumps({k:v for k,v in result.items() if k not in ['warnings','parameters_before','parameters_after']},indent=2));raise SystemExit(0 if result['status'].startswith('passed numerical') else 1)

if __name__=='__main__':main()
