#!/usr/bin/env python3
"""Reanalyze saved finite AC after fixing the decimal-only scale audit; no simulator."""
import argparse
import json
from pathlib import Path
import numpy as np
from run_loaded_compensation_candidate import parameter_gate
from run_loaded_followthrough import get_reference,errors
from run_loaded_ac_audit import observations
from run_loaded_noise_audit import sha,table,quiet_values
from analyze_loaded_ac_audit import controls,crossings


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--leaf',type=Path,required=True)
    p.add_argument('--original-baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();controls()
    failed=json.loads((a.leaf/'summary.json').read_text())
    contract=json.loads((a.leaf/'contract.json').read_text())
    assert failed['status']=='failed' and failed['case']=='nominal' and failed['mode']=='differential'
    assert "'predicted_decimal_interval'" in failed['analysis_error']
    assert failed['runtime']['status']=='completed' and failed['runtime']['returncode']==0
    _,ref,prep,expected,op=get_reference('settling','rise')
    provenance=json.loads((a.leaf/'provenance.json').read_text())
    assert provenance['runtime_identity']==prep['expected_runtime_identity']
    assert all(sha(ref/n)==h for n,h in prep['source_hashes'].items())
    assert sha(a.leaf/'candidate.spice')==contract['candidate_source_sha256']
    original=json.loads((a.original_baseline/'summary.json').read_text())
    assert original['status']=='passed source/OP/AC leaf' and original['full11512_and27_exact']
    assert sha(a.original_baseline/'summary.json')==contract['original_differential_summary_sha256']
    log=(a.leaf/'run.log').read_text();assert not errors(log) and 'LOADED_AC_END' in log
    result=dict(failed)
    result['original_failure_status']=failed['status']
    result['original_failure_analysis_error']=result.pop('analysis_error')
    result['parameter_gate']=parameter_gate(log,prep['groups'],expected)
    quiet=quiet_values(log);obs=observations(log)
    result.update(quiet_op_V=quiet,operating_point=obs,original9OP_exact=quiet==op,
        same_topology_original9OP_exact=quiet==original['quiet_op_V'],
        same_topology_original_supply_current_exact=all(obs[n]==original['operating_point'][n] for n in ['i(vdda)','i(vdd)']))
    assert result['same_topology_original9OP_exact'] and result['same_topology_original_supply_current_exact']
    wave=table(a.leaf/'ac.dat',['frequency','ac_re','ac_im'])
    basis=table(a.leaf/'input_basis.dat',['frequency','p_re','p_im','n_re','n_im'])
    assert wave.shape==(901,3) and np.array_equal(wave[:,0],basis[:,0])
    assert np.max(abs(basis[:,1:]-np.array([.5,0,-.5,0])))<=1e-12
    mag=abs(wave[:,1]+1j*wave[:,2]);db=20*np.log10(mag)
    points=crossings(wave[:,0],db,db[0]-3.010299956639812)
    result.update(status='passed candidate source/finite leaf',reanalysis_only=True,
        gain_1Hz_V_per_V=float(mag[0]),gain_status='passed' if 19.9<=mag[0]<=20.1 else 'failed',
        halfpower_downcrossings_Hz=[q[2] for q in points],
        bandwidth_status='passed' if points and points[0][2]>=2e6 else 'failed',
        original_failed_leaf_bindings={n:sha(a.leaf/n) for n in
            ['summary.json','contract.json','runner.py','candidate.spice','probe.cir','run.log','ac.dat','input_basis.dat','provenance.json']},
        corrected_parameter_gate_source_sha256=sha(Path(__file__).with_name('run_loaded_compensation_candidate.py')),
        corrected_parameter_gate_tests_sha256=sha(Path(__file__).with_name('test_loaded_compensation_candidate.py')),
        recovery_scope='Original decimal-only audit was not an enclosure of binary64 native expression. Explicit outward-operation interval replaces that mathematical error, not the simulator or electrical criteria. Original failed files retained; no analog rerun.')
    a.output.mkdir(parents=True)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in result.items() if k not in ['warnings','parameter_gate']},indent=2))


if __name__=='__main__':main()
