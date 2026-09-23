#!/usr/bin/env python3
"""Source-bound loaded AC transfer and conditional Tian analysis; no simulation."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from run_loaded_noise_audit import sha, table
from run_return_ratio import return_ratio


def crossings(frequency, values, level):
    """Log-frequency interpolation of a downward crossing in linear values."""
    answer=[]
    for i in range(len(values)-1):
        if values[i]>=level>values[i+1]:
            t=(level-values[i])/(values[i+1]-values[i])
            answer.append((i,t,float(np.exp(np.log(frequency[i])+t*np.log(frequency[i+1]/frequency[i])))))
    return answer


def rejection_db(signal, disturbance):
    # A zero denominator is not silently converted to an arbitrary large dB.
    assert np.all(np.abs(disturbance)>0) and np.all(np.abs(signal)>0)
    out=20*np.log10(np.abs(signal)/np.abs(disturbance))
    assert np.all(np.isfinite(out))
    return out


def negative_real_crossings(frequency, phase):
    """All odd-180-degree crossings in either direction, not just first descent."""
    answer=[]
    lo=int(math.floor((min(phase)-180)/360))-1
    hi=int(math.ceil((max(phase)-180)/360))+1
    for k in range(lo,hi+1):
        level=180+360*k
        for i in range(len(phase)-1):
            a,b=phase[i:i+2]
            if a<=level<b or a>level>=b:
                t=(level-a)/(b-a)
                answer.append((i,t,float(np.exp(np.log(frequency[i])+t*np.log(frequency[i+1]/frequency[i]))),level))
    return sorted(answer,key=lambda row:row[2])


def controls():
    f=np.array([1.,10.,100.]);a=np.array([0.,-3.,-6.])
    assert math.isclose(crossings(f,a,-3.)[0][2],10.,rel_tol=1e-14)
    assert np.array_equal(rejection_db(np.array([20.+0j]),np.array([.02+0j])),[60.])
    assert len(negative_real_crossings(f,np.array([-170.,-190.,-170.])))==2
    try:rejection_db(np.ones(1),np.zeros(1))
    except AssertionError:pass
    else:raise AssertionError('Zero denominator not rejected')
    # Analytic one-pole two-injection fixture: A=B=C=0,D=T/(1+T).
    ff=np.geomspace(1,1e7,701);tt=100/(1+1j*ff/1000)
    voltage=[[float(f),0.,0.,float((t/(1+t)).real),float((t/(1+t)).imag)] for f,t in zip(ff,tt)]
    current=[[float(f),0.,0.,0.,0.] for f in ff]
    points,unity=return_ratio(voltage,current)
    calculated=np.array([complex(p['T_real'],p['T_imag']) for p in points])
    assert np.max(np.abs(calculated-tt)/np.abs(tt))<5e-14
    assert len(unity)==1 and abs(unity[0]['frequency_Hz']/math.sqrt(100**2-1)/1000-1)<1e-6
    return {'status':'passed','controls':['log-frequency crossing','both-direction odd180 crossings','voltage ratio dB','zero rejection denominator fails','analytic Tian one-pole complex transfer/unity']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--baseline',type=Path)
    p.add_argument('--controls-only',action='store_true');a=p.parse_args()
    tested=controls()
    if a.controls_only:print(json.dumps(tested));return
    assert a.parent and a.output and not a.output.exists()
    modes=['baseline','differential','common','psrr_vdda','psrr_vdd','tian_voltage','tian_current']
    leaves={};data={};bindings={};contracts={}
    for mode in modes:
        folder=a.baseline if mode=='baseline' and a.baseline else a.parent/mode
        leaves[mode]=json.loads((folder/'summary.json').read_text())
        contracts[mode]=json.loads((folder/'contract.json').read_text())
        assert leaves[mode]['status']=='passed source/OP/AC leaf' and leaves[mode]['full11512_and27_exact']
        assert contracts[mode]['source_hashes']==contracts['baseline']['source_hashes']
        if mode!='baseline':assert contracts[mode]['baseline_summary_sha256']==sha((a.baseline or a.parent/'baseline')/'summary.json')
        header=['frequency','ir','ii','vr','vi'] if mode.startswith('tian_') else ['frequency','ac_re','ac_im']
        data[mode]=table(folder/'ac.dat',header)
        assert np.array_equal(data[mode][:,0],data['baseline'][:,0])
        bindings[mode]={n:sha(folder/n) for n in ['summary.json','contract.json','ac.dat','probe.cir','provenance.json','run.log']}
    f=data['baseline'][:,0]
    assert leaves['tian_voltage']['operating_point']==leaves['tian_current']['operating_point']
    assert sha(a.parent/'tian_voltage/probe.spice')==sha(a.parent/'tian_current/probe.spice')
    transfer={k:v[:,1]+1j*v[:,2] for k,v in data.items() if not k.startswith('tian_')}
    # Independently exported input basis proves interpretation. Numerical solver
    # residual is reported, not turned into an unapproved equivalence tolerance.
    residual=transfer['baseline']-transfer['differential']-.5*transfer['common']
    ad=transfer['differential'];gain=20*np.log10(abs(ad))
    bandwidth=crossings(f,gain,gain[0]-3.010299956639812)
    points,unity=return_ratio(data['tian_voltage'].tolist(),data['tian_current'].tolist())
    assert all(math.isfinite(v) for p in points for v in p.values())
    phase=np.array([p['phase_unwrapped_deg'] for p in points]);mag=np.array([p['magnitude'] for p in points])
    phase_cross=negative_real_crossings(f,phase)
    gm=[{'frequency_Hz':freq,'phase_level_deg':level,'gain_margin_dB':float(-20*((1-t)*math.log10(mag[i])+t*math.log10(mag[i+1])))} for i,t,freq,level in phase_cross]
    ratios={name:rejection_db(ad,transfer[mode]) for name,mode in [('CMRR','common'),('PSRR_VDDA','psrr_vdda'),('PSRR_VDD','psrr_vdd')]}
    samples={}
    for target in [1.,1e3,1e5,1e6,2e6,1e7]:
        j=int(np.argmin(abs(np.log(f/target))))
        samples[str(target)]={'actual_frequency_Hz':float(f[j]),'differential_gain_V_per_V':float(abs(ad[j])),**{k+'_dB':float(v[j]) for k,v in ratios.items()},**{k+'_output_transfer_dB':float(20*np.log10(abs(transfer[k][j]))) for k in ['common','psrr_vdda','psrr_vdd']}}
    result=dict(status='completed scoped analysis',controls=tested,bindings=bindings,
        criteria={'gain':'19.9..20.1','bandwidth_Hz':2e6,'conditional_PM_deg':60.,'conditional_GM_dB':10.,'PSRR_CMRR_acceptance':'not allocated'},
        gain_1Hz_V_per_V=float(abs(ad[0])),gain_status='passed' if 19.9<=abs(ad[0])<=20.1 else 'failed',
        bandwidth_downcrossings_Hz=[b[2] for b in bandwidth],bandwidth_status='passed' if bandwidth and bandwidth[0][2]>=2e6 else 'failed',
        unity_downcrossings=unity,conditional_PM_status='passed' if unity and all(u['conditional_phase_margin_deg']>=60 for u in unity) else 'failed',
        negative_real_crossings=gm,conditional_GM_status=('passed' if all(g['gain_margin_dB']>=10 for g in gm) else 'failed') if gm else 'not run: no odd180 crossing in finite sampled band',
        minimum_sampled_return_difference=float(min(p['return_difference_magnitude'] for p in points)),
        stimulus_superposition_max_abs_residual_V_per_V=float(max(abs(residual))),stimulus_superposition_exact=bool(np.all(residual==0)),
        rejection_definition='20log10(abs(differential-output transfer)/abs(common or selected supply-output transfer)); V/V input-referred rejection, not standalone output ripple attenuation.',
        selected_samples=samples,scope='TT25C seed73001 actual BGR586/full TRIP loaded frozen clock DC0. Main external resistor-feedback Tian loop conditional only; other loops closed. No global/corner/periodic/physical PEX stability or adoption.')
    a.output.mkdir(parents=True)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    (a.output/'return_ratio.json').write_text(json.dumps(points,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
