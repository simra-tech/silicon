#!/usr/bin/env python3
"""Run one prepared full JOINT KLU replay; exact equality failures stay separate."""
import argparse,gzip,json,re,subprocess,sys
from pathlib import Path
import numpy as np
from prepare_joint586_klu_replay import SIM,ROOT,ORIGINAL,sha,transform
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import run_bounded,analyze_wave,validate_saved_nodes
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',type=Path,required=True);p.add_argument('--image-id',required=True);a=p.parse_args()
    packet_path=a.packet if a.packet.is_absolute() else SIM/a.packet
    packet=json.loads(packet_path.read_text());out=SIM/'qualification'/packet['run_id'];prep=json.loads((out/'preparation.json').read_text())
    assert not (out/'run.log').exists() and sha(out/'preparation.json')==packet['preparation_sha256']
    assert (out/'probe.cir').read_text()==transform((ORIGINAL/'probe.cir').read_text(),out.name)
    validate_saved_nodes((out/'probe.cir').read_text(),(out/'trip.spice').read_text())
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='klu')
    expected=dict(prep['expected_runtime_identity'],solver='klu')
    checks=dict(runtime=runtime==expected,deck=sha(out/'probe.cir')==packet['deck_sha256']==prep['deck_sha256'],
        sources=all(sha(out/n)==sha(ORIGINAL.parent/n)==v for n,v in prep['source_hashes'].items()),
        inventory=sha(out/'population_inventory.json')==prep['inventory_sha256'],
        bindings=all(sha(ROOT/n)==v for n,v in prep['live_bindings_sha256'].items()))
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:],runtime_identity=runtime,input_checks=checks,
        runner_sha256=sha(Path(__file__)),preparation_sha256=sha(out/'preparation.json'),packet_sha256=sha(packet_path),
        source_hashes=prep['source_hashes'],scope=prep['scope'],physical_scope=prep['physical_scope']),indent=2)+'\n')
    assert all(checks.values()),'Input failure; no simulation'
    with (out/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str((out/'probe.cir').relative_to(SIM))],stream,out/'run.json',1200,cwd=SIM,interval_s=1)
    log=(out/'run.log').read_text()
    errors=[line for line in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse',line,re.I)]
    result=dict(status='failed',runtime=state,errors=errors,warnings=warning_inventory(log),scope=prep['scope'])
    try:
        assert state['status']=='completed' and state['returncode']==0 and not errors and 'JOINT_POPULATION_TRAN_END' in log
        assert 'Using KLU as Direct Linear Solver' in log and 'Using SPARSE 1.3 as Direct Linear Solver' not in log
        section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S)
        params=phase_parameters(section,prep['groups'],prep['expected_parameters']);assert params['legacy27']==prep['expected_legacy27']
        blob=(out/'phase0.dat').read_bytes();data=np.array([list(map(float,l.split())) for l in blob.splitlines()[1:] if l.strip()])
        with gzip.open(ORIGINAL/'phase0.dat.gz','rb') as stream:oldblob=stream.read()
        old=np.array([list(map(float,l.split())) for l in oldblob.splitlines()[1:] if l.strip()])
        assert data.shape[1]==18 and np.isfinite(data).all() and np.all(np.diff(data[:,0])>0) and abs(data[-1,0]-1.02e-6)<1e-18
        analysis=analyze_wave(data[:,:13].tolist(),prep['prospective_sampling']);assert analysis['sampling_status']=='passed'
        decisions={k:r['measured_edge_decision'] for k,r in analysis['comparators'].items()}
        names=blob.splitlines()[0].decode().split();assert names==oldblob.splitlines()[0].decode().split()
        grid=np.unique(np.concatenate([old[:,0],data[:,0]]))
        differences={name:float(np.max(np.abs(np.interp(grid,data[:,0],data[:,i])-np.interp(grid,old[:,0],old[:,i])))) for i,name in enumerate(names[1:],1)}
        oldsummary=json.loads((ORIGINAL/'summary.json').read_text())
        events={k:dict(original_s=oldsummary['wave_analysis']['actual_clock_rising_crossings_s'][k],klu_s=v,
            count_exact=len(v)==len(oldsummary['wave_analysis']['actual_clock_rising_crossings_s'][k]),
            index_paired_differences_s=[b-a for a,b in zip(oldsummary['wave_analysis']['actual_clock_rising_crossings_s'][k],v)])
            for k,v in analysis['actual_clock_rising_crossings_s'].items()}
        result.update(status='passed full parameter and numerical diagnostic; exact comparisons separate',parameter_audit=params,wave_analysis=analysis,
            decisions=decisions,decisions_equal_original=decisions==prep['original_decisions'],wave_rows=len(data),decoded_wave_sha256=sha(out/'phase0.dat'),
            exact_decoded_wave_status='passed' if blob==oldblob else 'failed exactbyte comparison',
            exact_time_grid_status='passed' if np.array_equal(old[:,0],data[:,0]) else 'failed exactgrid comparison',
            actual_clock_events=events,uniongrid_maximum_abs_voltage_difference_V=differences,
            comparison_scope='Linear interpolation on union of saved output grids; no rejected-step inference or numerical-bound waiver.',
            original_wall_s=oldsummary['wall_s'])
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as error:result['analysis_error']=repr(error)
    (out/'summary.json').write_text(json.dumps([result],indent=2)+'\n')
    if (out/'phase0.dat').exists():archive_new_wave(out/'phase0.dat')
    print(json.dumps({k:v for k,v in result.items() if k not in ['parameter_audit','wave_analysis','warnings']},indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__=='__main__':main()
