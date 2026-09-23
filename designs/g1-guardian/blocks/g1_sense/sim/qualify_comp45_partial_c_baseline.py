#!/usr/bin/env python3
"""Saved-only own-positive-C baseline; preserve exact cross-source DC failure."""
import argparse,json
from pathlib import Path
import numpy as np
from run_loaded_noise_audit import sha,table
from run_loaded_compensation_candidate import controls,crossings

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['leaf','original','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    result=json.loads((a.leaf/'summary.json').read_text());old=json.loads((a.original/'summary.json').read_text())
    assert result['status']=='failed partial-C diagnostic' and result['mode']=='differential'
    assert result['runtime']['status']=='completed' and result['runtime']['returncode']==0 and not result['errors']
    assert old['status']=='passed candidate source/finite leaf' and old['case']==result['case']
    assert result['parameter_gate']==old['parameter_gate']
    assert result['parameter_gate']['unchanged11511_exact'] and result['parameter_gate']['candidate11512_before_after_exact'] and result['parameter_gate']['legacy27_exact']
    delta={n:abs(v-old['quiet_op_V'][n]) for n,v in result['quiet_op_V'].items()}
    obs={n:abs(v-old['operating_point'][n]) for n,v in result['operating_point'].items()}
    assert all(np.isfinite(v) and v<=1e-6 for v in delta.values())
    assert all(np.isfinite(v) and v<=(1e-9 if n.startswith('i(') else 1e-6) for n,v in obs.items())
    wave=table(a.leaf/'ac.dat',['frequency','ac_re','ac_im'])
    basis=table(a.leaf/'input_basis.dat',['frequency','p_re','p_im','n_re','n_im'])
    assert wave.shape==(901,3) and basis.shape==(901,5) and np.array_equal(wave[:,0],basis[:,0])
    assert np.max(abs(basis[:,1:]-np.array([.5,0,-.5,0])))<=1e-12
    controls();mag=abs(wave[:,1]+1j*wave[:,2]);db=20*np.log10(mag);bw=crossings(wave[:,0],db,db[0]-3.010299956639812)
    result['original_failure_status']=result['status'];result['original_failure_analysis_error']=result.pop('analysis_error')
    result.update(status='passed partial-C source/OP/finite leaf',saved_data_only=True,
        baseline_scope='Own intentionally positive-C circuit baseline only. Exact cross-source DC diagnostic remainsFAILED; zero-C exact controls separatelyPASS. No sourcecampaign/fullfield inheritance.',
        cross_source_exact_DC='failed retained',cross_source_bounded_original_criteria=dict(voltage_limit_V=1e-6,current_limit_A=1e-9,quiet_voltage_deltas=delta,observation_deltas=obs),
        gain_1Hz_V_per_V=float(mag[0]),gain_status='passed' if 19.9<=mag[0]<=20.1 else 'failed',
        halfpower_downcrossings_Hz=[q[2] for q in bw],bandwidth_status='passed' if bw and bw[0][2]>=2e6 else 'failed',
        original_failed_leaf_bindings={n:sha(a.leaf/n) for n in ['summary.json','contract.json','candidate.spice','probe.cir','run.log','ac.dat','input_basis.dat','provenance.json']},
        original_candidate_anchor_sha256=sha(a.original/'summary.json'),new_simulation=False)
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','gain_1Hz_V_per_V','halfpower_downcrossings_Hz','cross_source_exact_DC']},indent=2))

if __name__=='__main__':main()
