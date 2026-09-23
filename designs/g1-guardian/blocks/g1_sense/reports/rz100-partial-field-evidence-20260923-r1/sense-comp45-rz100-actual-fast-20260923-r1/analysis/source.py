#!/usr/bin/env python3
"""Conditional paired Tian math; incomplete fields cannot certify physical PM."""
import argparse,json,math
from pathlib import Path
import numpy as np
from run_loaded_noise_audit import sha,table
from run_return_ratio import return_ratio
from analyze_loaded_ac_audit import controls,negative_real_crossings

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--differential-proof',type=Path)
    a=p.parse_args();assert not a.output.exists();controls()
    records={};contracts={};waves={};bindings={}
    for mode in ['differential','tian_voltage','tian_current']:
        path=a.parent/mode;proof=a.differential_proof if mode=='differential' and a.differential_proof else path/'summary.json'
        r=json.loads(proof.read_text());c=json.loads((path/'contract.json').read_text())
        if mode=='differential' and a.differential_proof:
            assert r['saved_data_only'] and all(sha(path/n)==h for n,h in r['original_failed_leaf_bindings'].items())
        assert r['status']=='passed partial-C source/OP/finite leaf' and r['mode']==mode
        records[mode]=r;contracts[mode]=c
        waves[mode]=table(path/'ac.dat',['frequency','ac_re','ac_im'] if mode=='differential' else ['frequency','ir','ii','vr','vi'])
        bindings[mode]={n:sha(path/n) for n in ['summary.json','contract.json','candidate.spice','probe.cir','ac.dat','provenance.json']}
    source=records['differential']['source_sha256']
    assert all(r['source_sha256']==source for r in records.values())
    assert all(c['source_sha256']==source for c in contracts.values())
    baseline_hash=sha(a.differential_proof) if a.differential_proof else bindings['differential']['summary.json']
    assert all(c['partial_baseline_sha256']==baseline_hash for mode,c in contracts.items() if mode!='differential')
    assert records['tian_voltage']['parameter_gate']['parameters']==records['tian_current']['parameter_gate']['parameters']==records['differential']['parameter_gate']['parameters']
    assert records['tian_voltage']['operating_point']==records['tian_current']['operating_point']
    assert sha(a.parent/'tian_voltage/probe.spice')==sha(a.parent/'tian_current/probe.spice')
    assert np.array_equal(waves['tian_voltage'][:,0],waves['tian_current'][:,0])
    points,unity=return_ratio(waves['tian_voltage'].tolist(),waves['tian_current'].tolist())
    assert all(math.isfinite(v) for r in points for v in r.values())
    f=waves['tian_voltage'][:,0];phase=np.array([r['phase_unwrapped_deg'] for r in points]);mag=np.array([r['magnitude'] for r in points])
    gm=[dict(frequency_Hz=freq,phase_level_deg=level,gain_margin_dB=-20*((1-t)*math.log10(mag[i])+t*math.log10(mag[i+1]))) for i,t,freq,level in negative_real_crossings(f,phase)]
    d=records['differential'];result=dict(status='completed conditional partial-C analysis; completefield NOT qualified',
        bindings=bindings,source_sha256=source,gain_1Hz_V_per_V=d['gain_1Hz_V_per_V'],gain_status=d['gain_status'],
        halfpower_downcrossings_Hz=d['halfpower_downcrossings_Hz'],bandwidth_status=d['bandwidth_status'],
        unity_downcrossings=unity,negative_real_crossings=gm,
        conditional_PM_status='passed' if unity and all(r['conditional_phase_margin_deg']>=60 for r in unity) else 'failed',
        conditional_GM_status=('passed' if all(r['gain_margin_dB']>=10 for r in gm) else 'failed') if gm else 'not run: no odd180 crossing in finite band',
        substrate='134VSUBS pairs explicitly omitted in this hypothesis, not zero physical coupling or bounds',
        missing_fields='MIM plate extrinsic/tap/contact completefields and finite wireR/attachment planes unresolved; fullchip/fill context not run',
        full_postlayout_PM_acceptance='not qualified',adoption='not run')
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    (a.output/'return_ratio.json').write_text(json.dumps(points,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
