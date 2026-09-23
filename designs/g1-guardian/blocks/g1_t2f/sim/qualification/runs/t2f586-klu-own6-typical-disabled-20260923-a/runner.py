#!/usr/bin/env python3
"""One frozen paired temperature/return diagnostic; no adoption or retries."""
import argparse,gzip,hashlib,json,re,subprocess,sys
from pathlib import Path
import numpy as np
from prepare_586_klu_temperature_coverage import HERE,ROOT,sha,transform
from run_586_population_control import phase_text
from run_586_source_control import load_wave
from run_nominal_clock_probe import run_bounded
from run_bgr_substitution_draw_audit import read_group
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave


def compare_wave(old_blob,new_blob):
    headers=[b.splitlines()[0].decode().split() for b in [old_blob,new_blob]];assert headers[0]==headers[1]
    x,y=[np.array([list(map(float,l.split())) for l in b.splitlines()[1:] if l.strip()]) for b in [old_blob,new_blob]]
    assert x.shape[1]==y.shape[1]==13 and np.isfinite(x).all() and np.isfinite(y).all()
    assert np.all(np.diff(x[:,0])>0) and np.all(np.diff(y[:,0])>0)
    grid=np.unique(np.concatenate([x[:,0],y[:,0]]))
    def events(data):
        return [float(a[0]+(.6-a[1])/(b[1]-a[1])*(b[0]-a[0])) for a,b in zip(data,data[1:]) if a[1]<.6<=b[1]]
    a,b=events(x),events(y)
    return dict(decoded_bytes_exact=old_blob==new_blob,numeric_rows_exact=bool(np.array_equal(x,y)),time_grid_exact=bool(np.array_equal(x[:,0],y[:,0])),
        maximum_abs_uniongrid_difference={name:float(np.max(np.abs(np.interp(grid,y[:,0],y[:,i])-np.interp(grid,x[:,0],x[:,i])))) for i,name in enumerate(headers[0][1:],1)},
        units={name:'A' if name.startswith('i(') else 'V' for name in headers[0][1:]},
        actual_fout_rising_events=dict(original_s=a,klu_s=b,count_exact=len(a)==len(b),index_paired_deltas_s=[v-u for u,v in zip(a,b)]),
        interpretation='Exact failures remain failures; common-grid differences descriptive, no acceptance bound or rejected-step inference.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',type=Path,required=True);p.add_argument('--label',required=True);p.add_argument('--image-id',required=True);a=p.parse_args()
    contract_path=a.contract if a.contract.is_absolute() else HERE/a.contract;contract=json.loads(contract_path.read_text())
    assert all(sha(ROOT/n)==v for n,v in contract['implementation_bindings_sha256'].items())
    packet_path=ROOT/contract['preparation_packet'];assert sha(packet_path)==contract['preparation_packet_sha256']
    case,=[c for c in json.loads(packet_path.read_text())['cases'] if c['label']==a.label]
    out=HERE/'runs'/case['run_id'];prep=json.loads((out/'preparation.json').read_text());old=HERE/'runs'/prep['original_run']
    assert sha(out/'preparation.json')==case['preparation_sha256'] and not (out/'run.log').exists()
    oldprov=old/'provenance.json' if (old/'provenance.json').exists() else old.parent/'provenance.json'
    original_provenance=json.loads(oldprov.read_text())
    assert original_provenance['runtime_identity']==prep['expected_runtime_identity']
    assert (out/'probe.cir').read_text()==transform((old/'probe.cir').read_text())
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),ngspice=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        models_sha256={str(f.relative_to(pd)):sha(f) for f in sorted((pd/'libs.tech/ngspice/models').glob('*.lib'))},
        osdi_sha256={str(f.relative_to(pd)):sha(f) for f in sorted((pd/'libs.tech/ngspice/osdi').glob('*.osdi'))})
    checks=dict(runtime=runtime==prep['expected_runtime_identity'],deck=sha(out/'probe.cir')==case['deck_sha256']==prep['deck_sha256'],
        original_deck=sha(old/'probe.cir')==prep['original_deck_sha256'],
        sources=all(sha(out/n)==sha(old/n if (old/n).exists() else old.parent/n)==v for n,v in prep['source_hashes'].items()),
        inventory=sha(out/'population_inventory.json')==prep['inventory_sha256'],bindings=all(sha(ROOT/n)==v for n,v in prep['bindings_sha256'].items()))
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:],runtime_identity=runtime,solver_selector='klu',input_checks=checks,
        preparation_sha256=sha(out/'preparation.json'),contract_sha256=sha(contract_path),original_provenance_sha256=sha(oldprov),
        runner_sha256=sha(Path(__file__)),source_hashes=prep['source_hashes'],scope=prep['prospective_contract']),indent=2)+'\n')
    assert all(checks.values()),'Input binding failure; no simulator launch'
    with (out/'run.log').open('x') as stream:state=run_bounded(['ngspice','-b','probe.cir'],stream,out/'run.json',prep['watchdog_s'],cwd=out,interval_s=1)
    log=(out/'run.log').read_text();errors=[l for l in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse',l,re.I)]
    result=dict(status='failed temperature diagnostic',runtime=state,errors=errors,warnings=warning_inventory(log),phases=[],original_outcome=prep['original_outcome'],solver_adoption='not run; not authorized')
    blobs=[]
    try:
        assert state['status']=='completed' and state['returncode']==0 and not errors
        assert 'Using KLU as Direct Linear Solver' in log and 'Using SPARSE 1.3 as Direct Linear Solver' not in log
        for i,temp in enumerate(prep['temperatures_C']):
            phase=phase_text(log,i)
            before={tag:read_group(phase,'P%d_%s_BEFORE'%(i,tag),keys) for tag,keys in prep['groups'].items()}
            after={tag:read_group(phase,'P%d_%s_AFTER'%(i,tag),keys) for tag,keys in prep['groups'].items()}
            assert sum(map(len,before.values()))==3180 and before==after==prep['expected_parameters']
            wave=out/('phase%d.dat'%i);blob,data=load_wave(wave);blobs.append(blob)
            assert data.shape[1]==13 and np.isfinite(data).all() and abs(data[-1,0]-32e-6)<1e-12 and np.all(np.diff(data[:,0])>0)
            values={k:float(v) for k,v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)',phase)}
            assert all(k in values and np.isfinite(values[k]) for k in ['freq','t_a','t_b','t_half_a','fout_hi','fout_lo']) and values['freq']>0 and values['t_b']>values['t_a']
            vce=float(max(np.abs(data[:,u]-data[:,v]).max() for u,v in [(7,8),(9,8),(10,11),(12,11)]));assert vce<=1.6
            row=dict(temperature_C=temp,parameters_before=before,parameters_after=after,wave_rows=len(data),waveform_sha256=hashlib.sha256(blob).hexdigest(),measurements=values,t2f_hbt_external_vce_max_V=vce,original_wave_comparison='not run; no original phase waveform')
            oldwave=old/('phase%d.dat.gz'%i)
            if oldwave.exists():
                with gzip.open(oldwave,'rb') as stream:oldblob=stream.read()
                row['original_wave_comparison']=compare_wave(oldblob,blob)
            result['phases'].append(row)
        if len(blobs)==4:
            result['same_klu_return_comparison']=compare_wave(blobs[0],blobs[3])
            assert result['same_klu_return_comparison']['decoded_bytes_exact'] and result['same_klu_return_comparison']['numeric_rows_exact'] and result['same_klu_return_comparison']['time_grid_exact']
        result['status']='passed fullparameter finite temperature diagnostic; exact SPARSE comparisons separate'
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as error:result['analysis_error']=repr(error)
    (out/'summary.json').write_text(json.dumps([result],indent=2)+'\n')
    for wave in sorted(out.glob('phase*.dat')):archive_new_wave(wave)
    print(json.dumps({k:v for k,v in result.items() if k not in ['phases','warnings']},indent=2));raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__=='__main__':main()
