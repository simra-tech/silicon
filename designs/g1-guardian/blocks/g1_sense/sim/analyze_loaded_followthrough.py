#!/usr/bin/env python3
"""Analyze source-qualified adverse AC triples or independently targeted steps."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from run_loaded_noise_audit import sha,table
from run_return_ratio import return_ratio
from analyze_loaded_ac_audit import controls,crossings,negative_real_crossings
from run_loaded_followthrough import TARGETS


def characterize_step(time,voltage,initial,target,start=200e-9,end=1.02e-6):
    time=np.asarray(time);voltage=np.asarray(voltage)
    assert time.ndim==voltage.ndim==1 and time.shape==voltage.shape and len(time)>=3
    assert np.isfinite(time).all() and np.isfinite(voltage).all() and np.all(np.diff(time)>0)
    assert time[0]<=start and time[-1]>=end and math.isfinite(initial) and math.isfinite(target)
    amplitude=target-initial;assert amplitude!=0
    after=time>=start;t=time[after];v=voltage[after];tolerance=.01*abs(amplitude)
    outside=np.nonzero(abs(v-target)>tolerance)[0]
    last=int(outside[-1]) if len(outside) else -1
    settled=last<len(t)-1
    bracket=None if not settled or last<0 else [float(t[last]),float(t[last+1])]
    normalized=(v-initial)/amplitude
    level_times={}
    for level in [.1,.9,.99]:
        reached=np.nonzero(normalized>=level)[0]
        level_times[str(level)]=float(t[reached[0]]-start) if len(reached) else None
    return dict(amplitude_V=amplitude,target_independent_DC_V=target,initial_independent_DC_V=initial,
        band_halfwidth_V=tolerance,saved_endpoint_s=float(time[-1]),
        settled_through_saved_endpoint=settled,last_outside_and_next_inside_bracket_s=bracket,
        first_saved_time_after_final_entry_delay_s=float(t[last+1]-start) if settled else None,
        sampled_overshoot_percent=float(100*max(0.,max(normalized)-1)),
        first_sampled_progress_crossing_delay_s=level_times,
        maximum_poststep_absolute_error_V=float(max(abs(v-target))),
        last200ns_minmax_V=[float(min(voltage[time>=end-200e-9])),float(max(voltage[time>=end-200e-9]))],
        scope='Saved-point band only, no between-point proof. Independent DC target at clockDC0; clock ripple not filtered or refitted.')


def tests():
    controls()
    t=np.array([0,200,300,400,500,600,800,1020])*1e-9
    v=np.array([1,1,1.9,2.03,1.99,2,2,2])
    r=characterize_step(t,v,1.,2.)
    assert r['settled_through_saved_endpoint'] and abs(r['sampled_overshoot_percent']-3)<1e-12
    # Ringing after first99% crossing must move final band entry later.
    assert r['first_saved_time_after_final_entry_delay_s']>r['first_sampled_progress_crossing_delay_s']['0.99']
    fall=characterize_step(t,3-v,2.,1.)
    assert math.isclose(fall['sampled_overshoot_percent'],r['sampled_overshoot_percent'],abs_tol=1e-12)
    v[-1]=2.1;assert not characterize_step(t,v,1.,2.)['settled_through_saved_endpoint']
    try:characterize_step(t,v,1.,1.)
    except AssertionError:pass
    else:raise AssertionError('zero amplitude accepted')
    return dict(status='passed',controls=['existing AC/Tian controls','rise/fall sign symmetry','last-entry not first crossing','late ringing fails saved-endpoint settling','zero amplitude rejected'])


def leaf(folder):
    r=json.loads((folder/'summary.json').read_text());c=json.loads((folder/'contract.json').read_text())
    assert r['status']=='passed source/OP/finite leaf' and r['full11512_and27_exact']
    assert r['case']==c['case'] and r['mode']==c['mode']
    return r,c


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kind',choices=['adverse','settling']);p.add_argument('--case')
    p.add_argument('--parent',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--test-only',action='store_true');a=p.parse_args();control=tests()
    if a.test_only:print(json.dumps(control));return
    assert a.parent and a.output and a.case and a.kind and not a.output.exists()
    if a.kind=='adverse':
        records={};contracts={};waves={}
        for name in ['differential','tian_voltage','tian_current']:
            folder=a.parent/name;records[name],contracts[name]=leaf(folder)
            assert records[name]['case']==a.case
            header=['frequency','ac_re','ac_im'] if name=='differential' else ['frequency','ir','ii','vr','vi']
            waves[name]=table(folder/'ac.dat',header)
            assert np.array_equal(waves[name][:,0],waves['differential'][:,0])
            assert contracts[name]['source_hashes']==contracts['differential']['source_hashes']
            if name!='differential':assert contracts[name]['baseline_summary_sha256']==sha(a.parent/'differential/summary.json')
        assert records['tian_voltage']['operating_point']==records['tian_current']['operating_point']
        assert sha(a.parent/'tian_voltage/probe.spice')==sha(a.parent/'tian_current/probe.spice')
        f=waves['differential'][:,0];mag=abs(waves['differential'][:,1]+1j*waves['differential'][:,2]);db=20*np.log10(mag)
        bw=crossings(f,db,db[0]-3.010299956639812)
        points,unity=return_ratio(waves['tian_voltage'].tolist(),waves['tian_current'].tolist())
        assert all(math.isfinite(v) for point in points for v in point.values())
        phase=np.array([r['phase_unwrapped_deg'] for r in points]);magnitude=np.array([r['magnitude'] for r in points])
        gm=[dict(frequency_Hz=freq,phase_level_deg=level,gain_margin_dB=-20*((1-t)*math.log10(magnitude[i])+t*math.log10(magnitude[i+1]))) for i,t,freq,level in negative_real_crossings(f,phase)]
        result=dict(status='completed scoped adverse analysis',gain_1Hz_V_per_V=float(mag[0]),gain_status='passed' if 19.9<=mag[0]<=20.1 else 'failed',
            halfpower_downcrossings_Hz=[b[2] for b in bw],bandwidth_status='passed' if bw and bw[0][2]>=2e6 else 'failed',
            unity_downcrossings=unity,conditional_PM_status='passed' if unity and all(p['conditional_phase_margin_deg']>=60 for p in unity) else 'failed',
            negative_real_crossings=gm,conditional_GM_status=('passed' if all(g['gain_margin_dB']>=10 for g in gm) else 'failed') if gm else 'not run: finite band has no odd180 crossing',
            scope='One own-corner draw attrueCM0/shunt25mV; conditional main loop only, clockDC0. No global/periodic/PVTpopulation/physicalPEX adoption.')
    else:
        step,sc=leaf(a.parent/'step');dc,dc_contract=leaf(a.parent/'dc')
        assert step['case']==dc['case']==a.case
        assert sc['source_hashes']==dc_contract['source_hashes'] and sc['reference_summary_sha256']==dc_contract['reference_summary_sha256']
        assert step['quiet_op_reference_exact']
        header=['time','v(clk)','v(xt.icmp)','v(xt.vth_soft)','v(xt.vth_hard)','v(cmp_soft)','v(cmp_hard)','v(isense)','v(xt.cmp_clk_n)','v(xt.xch.xp)','v(xt.xch.xq)','v(xt.xch.xn)','v(xt.xch.yn)','v(vref)','v(iptat)','v(vref_buf)','v(vped)','v(shp)']
        wave=table(a.parent/'step/phase0.dat',header)
        result=characterize_step(wave[:,0],wave[:,header.index('v(isense)')],step['quiet_op_V']['v(isense)'],dc['quiet_op_V']['v(isense)'])
        gain=result['amplitude_V']/(TARGETS[a.case]-.025)
        result.update(status='completed scoped settling characterization',DC_endpoint_gain_V_per_V=gain,DC_endpoint_gain_status='passed' if 19.9<=gain<=20.1 else 'failed',
            settling_time_limit='not allocated; saved-endpoint band disposition is characterization, not an invented timing limit',source_or_model_change=False)
        records={'step':step,'dc':dc};points=None
    result.update(case=a.case,controls=control,bindings={name:{n:sha(a.parent/name/n) for n in ['summary.json','contract.json','probe.cir','provenance.json','run.log']} for name in records})
    a.output.mkdir(parents=True);(a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    if points is not None:(a.output/'return_ratio.json').write_text(json.dumps(points,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
