#!/usr/bin/env python3
"""External-board energy/current accounting for conditional manual isolation."""
import argparse
import json
from pathlib import Path
import numpy as np
from prepare_manual_isolation import VECTORS


def integral_product(time, first, second):
    """Exact product integral of two piecewise-linear saved vectors."""
    time,first,second = map(np.asarray,(time,first,second))
    assert time.shape==first.shape==second.shape and time.ndim==1 and len(time)>1
    assert all(np.isfinite(a).all() for a in [time,first,second])
    dt=np.diff(time);assert np.all(dt>0)
    return float(np.sum(dt*(2*first[:-1]*second[:-1]+first[:-1]*second[1:]+
                            first[1:]*second[:-1]+2*first[1:]*second[1:])/6))


def signed_parts(time, first, second):
    """Integrate positive and negative power separately, splitting every root."""
    signed=integral_product(time,first,second)
    positive=0.;negative=0.
    for t0,t1,a0,a1,b0,b1 in zip(time[:-1],time[1:],first[:-1],first[1:],second[:-1],second[1:]):
        fractions={0.,1.}
        for x,y in [(a0,a1),(b0,b1)]:
            if y!=x and 0 < -x/(y-x) < 1: fractions.add(float(-x/(y-x)))
        fractions=sorted(fractions)
        for left,right in zip(fractions[:-1],fractions[1:]):
            aa=np.array([a0+(a1-a0)*left,a0+(a1-a0)*right])
            bb=np.array([b0+(b1-b0)*left,b0+(b1-b0)*right])
            value=integral_product(np.array([0.,(t1-t0)*(right-left)]),aa,bb)
            if value>=0:positive+=value
            else:negative+=value
    assert abs(positive+negative-signed)<=1e-12*max(abs(signed),positive-negative,1e-30)
    return dict(signed_J=signed,positive_provided_J=positive,
                negative_absorbed_J=negative,absolute_J=positive-negative)


def tests():
    t=np.array([0.,.17,.41,1.])
    assert abs(integral_product(t,t,t)-1/3)<1e-15
    assert abs(integral_product(t,2*t,3*t)-2)<1e-15
    assert abs(integral_product(t,-t,t)+1/3)<1e-15
    assert integral_product(np.array([0.,16e-6]),np.array([.01,.01]),np.array([.05,.05]))==8e-9
    split=signed_parts(np.array([0.,1.]),np.array([-.5,.5]),np.ones(2))
    assert split['signed_J']==0 and split['positive_provided_J']==.125 and split['negative_absorbed_J']==-.125
    for bad in [np.array([0.,1.,.5,2.]),np.array([0.,1.,2.,float('nan')])]:
        try:integral_product(bad,t,t)
        except AssertionError:pass
        else:raise AssertionError('Invalid time accepted')
    return dict(status='passed', controls=['nonuniform linear-product analytic integral',
        'quadratic current scaling and signed energy', '10mA/5ohm/16us equals8nJ',
        'nonmonotonic/nonfinite rejection','opposite energy flow cannot cancel positive total'])


def analyze(wave,contract):
    assert wave.ndim==2 and wave.shape[1]==1+len(VECTORS)
    assert np.isfinite(wave).all() and np.all(np.diff(wave[:,0])>0)
    t=wave[:,0]; assert t[0]==0 and abs(t[-1]-16e-6)<1e-15
    v={name:wave[:,i+1] for i,name in enumerate(VECTORS)}
    a=contract['assumptions'];limits=contract['prospective_acceptance']
    one=np.ones_like(t)
    energy=lambda x,y:integral_product(t,x,y)
    square=lambda x:energy(x,x)
    load=v['i(lload)'];idrain=v['i(vfet)'];igate=v['i(vig)']
    vgs=v['v(gfet,source)'];vbus=v['v(bus)'];raw=v['v(rawbus)']
    dis=(raw-vbus)/a['disconnect_R_ohm']
    gate_device=igate-vgs/a['pulldown_R_ohm']
    # Drain KCL supplies the diode current below. It is NOT an independent
    # diode-current observation, so this algebraic residual cannot certify it.
    diode=load-idrain
    resistors=dict(load=square(load)*a['load_R_ohm'],
        disconnect=square(dis)*a['disconnect_R_ohm'],
        bleeder=square(vbus)/a['bleed_R_ohm'],
        gate_series=square(igate)*10,
        gate_pulldown=square(vgs)/a['pulldown_R_ohm'],
        shunt_and_return=square(idrain+igate)*.035)
    storage_initial=dict(bus_C=.5*a['bus_C_F']*vbus[0]**2,
        contact_C=.5*a['contact_C_F']*(raw[0]-vbus[0])**2,
        load_L=.5*a['load_L_H']*load[0]**2)
    storage_final=dict(bus_C=.5*a['bus_C_F']*vbus[-1]**2,
        contact_C=.5*a['contact_C_F']*(raw[-1]-vbus[-1])**2,
        load_L=.5*a['load_L_H']*load[-1]**2)
    supplied=dict(raw_bus=-energy(raw,v['i(vbus)']),
        analog_rail=-energy(v['v(vdda_s)'],v['i(vdda)']),
        core_rail=-energy(v['v(vdd_s)'],v['i(vdd)']),
        EN=-energy(v['v(en_pad)'],v['i(ven)']),
        gate_to_external_board=energy(v['v(gate)'],igate))
    provided_parts={name:signed_parts(t,voltage,current) for name,voltage,current in
        [('raw_bus',raw,-v['i(vbus)']),('analog_rail',v['v(vdda_s)'],-v['i(vdda)']),
         ('core_rail',v['v(vdd_s)'],-v['i(vdd)']),('EN',v['v(en_pad)'],-v['i(ven)']),
         ('gate_to_external_board',v['v(gate)'],igate)]}
    fet=energy(v['v(dfet,source)'],idrain)+energy(vgs,gate_device)
    diode_energy=energy(v['v(drain)']-vbus,diode)
    stored_delta=sum(storage_final.values())-sum(storage_initial.values())
    external_residual=supplied['raw_bus']+supplied['gate_to_external_board']-sum(resistors.values())-fet-diode_energy-stored_delta
    initial_bus=abs(float(vbus[0]))
    initial_current=abs(float(load[0]));peak=float(max(abs(load)))
    prerequisites=initial_bus<=limits['initial_bus_abs_max_V'] and initial_current<=limits['initial_load_abs_max_A']
    conditional=prerequisites and peak<limits['all_window_load_abs_max_A'] and resistors['load']<limits['load_resistor_energy_max_J']
    gate_pass=max(v['v(gate)'])<1 and max(vgs)<1
    result=dict(status='completed conditional external-board accounting',controls=tests(),
        simulated_initial_bus_V=initial_bus,simulated_initial_load_A=initial_current,
        simulated_peak_abs_load_A=peak,simulated_bus_minmax_V=[float(min(vbus)),float(max(vbus))],
        simulated_gate_max_V=float(max(v['v(gate)'])),simulated_VGS_max_V=float(max(vgs)),
        conditional_manual_isolation='passed' if conditional else 'failed',
        simulated_initial_prerequisites='passed' if prerequisites else 'failed',
        historical_gate_voltage='passed' if gate_pass else 'failed',
        resistor_dissipation_J=resistors, initial_external_storage_J=storage_initial,
        final_external_storage_J=storage_final, signed_source_provided_energy_J=supplied,
        source_provided_absorbed_energy_parts=provided_parts,
        signed_FET_terminal_energy_J=fet,signed_derived_diode_energy_J=diode_energy,
        external_energy_balance_residual_J=external_residual,
        diode_current='Derived by drain KCL, not independently measured; energy balance is accounting only',
        physical_measurement='not run',
        limitations='Saved-point piecewise-linear energy/current diagnostic. No between-point maximum, self-heating/SOA, automatic rail-loss protection, complete PVT/board envelope, or native tap/PEX qualification. Analog/core source energy includes internal driver losses/storage not independently partitioned.')
    if contract['disconnect']=='closed negative control':
        result['negative_control_exercised']=not conditional and peak>=.01 and max(vgs)>=1
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder',type=Path)
    p.add_argument('--test-only',action='store_true')
    a=p.parse_args()
    if a.test_only:print(json.dumps(tests()));return
    assert a.folder
    lines=(a.folder/'wave.tsv').read_text().splitlines()
    assert lines[0].split()==['time']+VECTORS
    wave=np.array([list(map(float,line.split())) for line in lines[1:] if line.strip()])
    result=analyze(wave,json.loads((a.folder/'contract.json').read_text()))
    target=a.folder/'analysis.json';assert not target.exists()
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
