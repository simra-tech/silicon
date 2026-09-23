"""Read-only full reconstruction of six matched diagnostic outcomes."""
import argparse
import gzip
import json
import re
import numpy as np
from prepare_joint586_tmax_matrix import ROOT,SIM,sha,matched_transform
from run_joint586_tmax_probe import runtime_gate
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import analyze_wave
from compare_joint586_tmax_probe import compare


def audit_case(case):
    out=SIM/'qualification'/case['run_id'];record=dict(run_id=case['run_id'],numerical_status='not run',audit_status='not run')
    if not (out/'run.json').exists():return record
    record.update(numerical_status='failed',audit_status='failed')
    try:
        assert sha(out/'preparation.json')==case['preparation_sha256'];prep=json.loads((out/'preparation.json').read_text())
        assert all(sha(ROOT/n)==v for n,v in prep['live_bindings_sha256'].items())
        original=SIM/'qualification'/prep['original_run'];state=json.loads((out/'run.json').read_text());log=(out/'run.log').read_text()
        record['runtime']=state;runtime_gate(state,log)
        assert (out/'probe.cir').read_text()==matched_transform((original/'probe.cir').read_text(),prep['original_run'],case['run_id'],prep['seed'])
        assert sha(out/'probe.cir')==prep['deck_sha256']
        assert all(sha(out/n)==v for n,v in prep['source_hashes'].items())
        provenance=json.loads((out/'provenance.json').read_text());assert provenance['runtime_identity']==prep['expected_runtime_identity']
        section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S)
        parameters=phase_parameters(section,prep['groups'],prep['expected_parameters']);assert parameters['legacy27']==prep['expected_legacy27']
        with gzip.open(out/'phase0.dat.gz','rb') as stream:blob=stream.read()
        with gzip.open(original/'phase0.dat.gz','rb') as stream:oldblob=stream.read()
        names=blob.splitlines()[0].decode().split();assert names==oldblob.splitlines()[0].decode().split()
        values=lambda data:np.array([list(map(float,l.split())) for l in data.splitlines()[1:] if l.strip()])
        data=values(blob);old=values(oldblob)
        assert data.shape[1]==18 and np.isfinite(data).all() and np.all(np.diff(data[:,0])>0) and abs(data[-1,0]-1.02e-6)<1e-18
        analysis=analyze_wave(data[:,:13].tolist(),prep['prospective_sampling']);assert analysis['sampling_status']=='passed'
        oldsummary=json.loads((original/'summary.json').read_text());comparison=compare(old,data,names,oldsummary['wave_analysis'],analysis,prep['bounds'])
        summary=json.loads((out/'summary.json').read_text())
        assert summary['numerical_status']=='passed' and summary['parameter_audit']==parameters and summary['wave_analysis']==analysis
        assert summary['comparisons']==comparison and summary['exact_wave_bytes']==(blob==oldblob)
        assert summary['exact_numeric_rows']==np.array_equal(old,data) and summary['exact_time_grid']==np.array_equal(old[:,0],data[:,0])
        screen=all(comparison['checks'].values());assert summary['consistency_status']==('passed prospective matched screen' if screen else 'failed prospective matched screen')
        record.update(numerical_status='passed',audit_status='passed independent reconstruction',consistency_status=summary['consistency_status'],
            exact_wave_bytes=summary['exact_wave_bytes'],exact_numeric_rows=summary['exact_numeric_rows'],exact_time_grid=summary['exact_time_grid'],
            original_wall_s=oldsummary['wall_s'],candidate_wall_s=state['wall_s'],comparisons=comparison,
            receipts_sha256={n:sha(out/n) for n in ['preparation.json','probe.cir','provenance.json','run.json','run.log','summary.json','phase0.dat.gz']})
    except (AssertionError,KeyError,ValueError,IndexError,OSError) as error:record['audit_error']=repr(error)
    return record


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',required=True);p.add_argument('--packet-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    packet=ROOT/a.packet;assert sha(packet)==a.packet_sha256;d=json.loads(packet.read_text());assert len(d['controls'])==6
    assert all(sha(ROOT/n)==v for n,v in d['bindings_sha256'].items())
    records=[audit_case(c) for c in d['controls']]
    result=dict(status='completed independent matched diagnostics; no adoption',packet_sha256=a.packet_sha256,auditor_sha256=sha(__import__('pathlib').Path(__file__)),records=records,
        requested=6,numerical_passed=sum(r['numerical_status']=='passed' for r in records),not_run=sum(r['numerical_status']=='not run' for r in records),
        evidence_failed=sum(r['audit_status']=='failed' for r in records),consistency_passed=sum(r.get('consistency_status')=='passed prospective matched screen' for r in records),
        scope='Exact grid/wave failures remain distinct. Engineering screen is not a verified universal error bound. ±0.1mV/new-SENSE/population qualification not run.')
    output=ROOT/a.output;assert not output.exists();output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'],result['numerical_passed'],result['consistency_passed'])
    raise SystemExit(0 if result['numerical_passed']==6 and result['evidence_failed']==0 else 1)


if __name__=='__main__':main()
