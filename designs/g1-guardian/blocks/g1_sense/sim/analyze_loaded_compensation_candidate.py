#!/usr/bin/env python3
"""Independent current/area and optional paired Tian checks for a new candidate."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from run_loaded_noise_audit import sha,table
from run_return_ratio import return_ratio
from analyze_loaded_ac_audit import controls,negative_real_crossings


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--original-baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--loop',action='store_true')
    p.add_argument('--differential-proof',type=Path)
    a=p.parse_args();assert not a.output.exists();controls()
    diff=a.parent/'differential'
    differential_proof=a.differential_proof or diff/'summary.json'
    candidate=json.loads(differential_proof.read_text())
    if a.differential_proof:
        assert candidate['reanalysis_only']
        assert all(sha(diff/n)==h for n,h in candidate['original_failed_leaf_bindings'].items())
    source=json.loads((a.original_baseline/'summary.json').read_text())
    assert candidate['status']=='passed candidate source/finite leaf'
    assert source['status'] in ['passed source/OP/finite leaf','passed source/OP/AC leaf']
    assert source['full11512_and27_exact'] and source['mode']=='differential'
    cc=json.loads((diff/'contract.json').read_text())
    original=json.loads((a.original_baseline/'contract.json').read_text())
    assert cc['original_source_sha256']==original['source_hashes']['sense.spice']
    assert all(original['source_hashes'][n]==h for n,h in cc['other_source_hashes'].items())
    assert cc['reference_run']==original['reference_run']
    old=source['operating_point'];new=candidate['operating_point']
    result=dict(status='completed scoped candidate analysis',case=candidate['case'],
        gain_1Hz_V_per_V=candidate['gain_1Hz_V_per_V'],gain_status=candidate['gain_status'],
        halfpower_downcrossings_Hz=candidate['halfpower_downcrossings_Hz'],bandwidth_status=candidate['bandwidth_status'],
        source_held_supply_OP_A={n:dict(original=old[n],candidate=new[n],abs_delta=abs(new[n]-old[n])) for n in ['i(vdda)','i(vdd)']},
        original_supply_current_exact=all(old[n]==new[n] for n in ['i(vdda)','i(vdd)']),
        original9OP_exact=candidate['quiet_op_V']==source['quiet_op_V'],
        main_MIM_area_um2=cc['main_MIM_area_um2'],
        main_RZ_body_area_um2=cc.get('main_RZ_body_area_um2',dict(original=6.2,candidate=6.2,delta=0)),
        physical_layout='not run',affected_population='not run',
        conditional_PM_status='not run',conditional_GM_status='not run',
        scope='Current is total fixture source OP, not macro-only, transient or worst-case envelope. MIM plate area only, not legal regenerated geometry/field proof. No old qualification inheritance.')
    sources={'original_baseline':a.original_baseline,'candidate_differential':diff}
    if a.loop:
        records={};waves={}
        for mode in ['tian_voltage','tian_current']:
            path=a.parent/mode;record=json.loads((path/'summary.json').read_text());contract=json.loads((path/'contract.json').read_text())
            assert record['status']=='passed candidate source/finite leaf'
            assert contract['candidate_source_sha256']==cc['candidate_source_sha256']
            assert contract['baseline_summary_sha256']==sha(differential_proof)
            records[mode]=record;waves[mode]=table(path/'ac.dat',['frequency','ir','ii','vr','vi'])
            sources[mode]=path
        assert records['tian_voltage']['operating_point']==records['tian_current']['operating_point']
        assert records['tian_voltage']['parameter_gate']['parameters']==records['tian_current']['parameter_gate']['parameters']
        assert np.array_equal(waves['tian_voltage'][:,0],waves['tian_current'][:,0])
        points,unity=return_ratio(waves['tian_voltage'].tolist(),waves['tian_current'].tolist())
        assert all(math.isfinite(value) for row in points for value in row.values())
        f=waves['tian_voltage'][:,0];phase=np.array([r['phase_unwrapped_deg'] for r in points]);mag=np.array([r['magnitude'] for r in points])
        gm=[dict(frequency_Hz=freq,phase_level_deg=level,gain_margin_dB=-20*((1-t)*math.log10(mag[i])+t*math.log10(mag[i+1]))) for i,t,freq,level in negative_real_crossings(f,phase)]
        result.update(unity_downcrossings=unity,negative_real_crossings=gm,
            conditional_PM_status='passed' if unity and all(r['conditional_phase_margin_deg']>=60 for r in unity) else 'failed',
            conditional_GM_status=('passed' if all(r['gain_margin_dB']>=10 for r in gm) else 'failed') if gm else 'not run: no odd180 crossing in finite band')
    result['bindings']={name:{n:sha(path/n) for n in ['summary.json','contract.json','probe.cir','provenance.json','ac.dat']} for name,path in sources.items()}
    result['differential_proof_sha256']=sha(differential_proof)
    a.output.mkdir(parents=True)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    if a.loop:(a.output/'return_ratio.json').write_text(json.dumps(points,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
