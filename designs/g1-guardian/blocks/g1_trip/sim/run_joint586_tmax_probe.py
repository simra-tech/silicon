"""One prepared TMAX-only replay; numerical and proposed consistency results separate."""
import argparse
import gzip
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from prepare_joint586_tmax_probe import SIM,ROOT,ORIGINAL,sha,transform
from compare_joint586_tmax_probe import compare
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import run_bounded,analyze_wave,validate_saved_nodes
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave


def runtime_gate(state,log):
    errors=[line for line in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse',line,re.I)]
    assert state['status']=='completed' and state['returncode']==0 and not errors
    assert 'Using SPARSE 1.3 as Direct Linear Solver' in log and 'JOINT_POPULATION_TRAN_END' in log


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',required=True);p.add_argument('--packet-sha256',required=True);p.add_argument('--image-id',required=True);a=p.parse_args()
    packet_path=ROOT/a.packet;assert sha(packet_path)==a.packet_sha256;packet=json.loads(packet_path.read_text())
    out=SIM/'qualification'/packet['run_id'];assert sha(out/'preparation.json')==packet['preparation_sha256'];prep=json.loads((out/'preparation.json').read_text())
    assert not (out/'run.log').exists()
    assert all(sha(ROOT/n)==v for n,v in prep['live_bindings_sha256'].items())
    assert (out/'probe.cir').read_text()==transform((ORIGINAL/'probe.cir').read_text(),out.name)
    assert sha(out/'probe.cir')==prep['deck_sha256']==packet['deck_sha256']
    assert all(sha(out/n)==sha(ORIGINAL.parent/n)==v for n,v in prep['source_hashes'].items())
    assert sha(out/'population_inventory.json')==prep['inventory_sha256']
    validate_saved_nodes((out/'probe.cir').read_text(),(out/'trip.spice').read_text())
    pd=Path('/foss/pdks/ihp-sg13g2');runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==prep['expected_runtime_identity']
    (out/'runner.py').write_text(Path(__file__).read_text());(out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:],runtime_identity=runtime,
        runner_sha256=sha(Path(__file__)),packet_sha256=a.packet_sha256,preparation_sha256=sha(out/'preparation.json'),source_hashes=prep['source_hashes']),indent=2)+'\n')
    with (out/'run.log').open('x') as stream:state=run_bounded(['ngspice','-b',str((out/'probe.cir').relative_to(SIM))],stream,out/'run.json',1200,cwd=SIM,interval_s=1)
    log=(out/'run.log').read_text();result=dict(numerical_status='failed',consistency_status='not run',runtime=state,warnings=warning_inventory(log),scope=prep['scope'])
    try:
        runtime_gate(state,log)
        section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S)
        params=phase_parameters(section,prep['groups'],prep['expected_parameters']);assert params['legacy27']==prep['expected_legacy27']
        blob=(out/'phase0.dat').read_bytes()
        with gzip.open(ORIGINAL/'phase0.dat.gz','rb') as stream:oldblob=stream.read()
        names=blob.splitlines()[0].decode().split();assert names==oldblob.splitlines()[0].decode().split()
        data=np.array([list(map(float,l.split())) for l in blob.splitlines()[1:] if l.strip()]);old=np.array([list(map(float,l.split())) for l in oldblob.splitlines()[1:] if l.strip()])
        assert data.shape[1]==18 and np.isfinite(data).all() and np.all(np.diff(data[:,0])>0) and abs(data[-1,0]-1.02e-6)<1e-18
        analysis=analyze_wave(data[:,:13].tolist(),prep['prospective_sampling']);assert analysis['sampling_status']=='passed'
        original=json.loads((ORIGINAL/'summary.json').read_text());comparisons=compare(old,data,names,original['wave_analysis'],analysis,prep['bounds'])
        result.update(numerical_status='passed',consistency_status='passed prospective single-leaf screen' if all(comparisons['checks'].values()) else 'failed prospective single-leaf screen',
            parameter_audit=params,wave_analysis=analysis,comparisons=comparisons,exact_wave_bytes=blob==oldblob,exact_numeric_rows=np.array_equal(old,data),
            exact_time_grid=np.array_equal(old[:,0],data[:,0]),original_wall_s=original['wall_s'],decoded_wave_sha256=sha(out/'phase0.dat'))
    except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:result['analysis_error']=repr(error)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    if (out/'phase0.dat').exists():archive_new_wave(out/'phase0.dat')
    print(result['numerical_status'],result['consistency_status']);raise SystemExit(0 if result['numerical_status']=='passed' else 1)


if __name__=='__main__':main()
