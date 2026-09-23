#!/usr/bin/env python3
"""Read-only two-failure thermal/decision contrasts; no causal identification."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from wave_archive import open_wave

SIM=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(seed,index):
    parent=SIM/'qualification'/('joint586-calibration-s%d-20260922-a'%seed)
    result,=json.loads((parent/'summary.json').read_text())
    entry=result['probes'][index];leaf=SIM/'qualification'/entry['run']
    full=json.loads((leaf/'summary.json').read_text());state=json.loads((leaf/'run.json').read_text())
    assert entry['status']=='passed' and state['status']=='completed' and state['returncode']==0
    assert sha(leaf/'summary.json')==entry['summary_sha256']
    assert sha(leaf/'probe.cir')==entry['deck_sha256']
    params=full['parameter_audit'];assert params['parameters_before']==params['parameters_after']==result['parameters_before_first_probe']
    assert len(params['parameters_before'])==11512
    with open_wave(leaf/'phase0.dat','rb') as stream:blob=stream.read()
    assert hashlib.sha256(blob).hexdigest()==entry['decoded_wave_sha256']
    lines=blob.decode().splitlines();header=lines[0].split()
    data=np.array([list(map(float,l.split())) for l in lines[1:] if l.strip()])
    assert data.shape==(entry['wave_rows'],18) and np.isfinite(data).all()
    assert abs(data[-1,0]-1.02e-6)<1e-18
    assert header==['time','v(clk)','v(xt.icmp)','v(xt.vth_soft)','v(xt.vth_hard)','v(cmp_soft)','v(cmp_hard)',
        'v(isense)','v(xt.cmp_clk_n)','v(xt.xch.xp)','v(xt.xch.xq)','v(xt.xch.xn)','v(xt.xch.yn)',
        'v(vref)','v(iptat)','v(vref_buf)','v(vped)','v(shp)']
    events=full['wave_analysis']['actual_clock_rising_crossings_s']['hard'][-3:]
    observations=[]
    for delay in [-1,0,.1,.3,.5,1,20]:
        samples=[]
        for edge in events:
            values={name:float(np.interp(edge+delay*1e-9,data[:,0],data[:,i])) for i,name in enumerate(header[1:],1)}
            values['hard_differential_V']=values['v(xt.icmp)']-values['v(xt.vth_hard)']
            values['algebraic_terms_V']={
                'input_divider_deviation':values['v(xt.icmp)']-values['v(isense)']/2,
                'sense_above_pedestal_half':(values['v(isense)']-values['v(vped)'])/2,
                'pedestal_half':values['v(vped)']/2,'negative_hard_threshold':-values['v(xt.vth_hard)']}
            values['reconstruction_residual_V']=sum(values['algebraic_terms_V'].values())-values['hard_differential_V']
            samples.append(values)
        observations.append(dict(delay_after_actual_hard_edge_ns=delay,
            mean_V={k:sum(s[k] for s in samples)/3 for k in samples[0] if k!='algebraic_terms_V'},
            mean_algebraic_terms_V={k:sum(s['algebraic_terms_V'][k] for s in samples)/3 for k in samples[0]['algebraic_terms_V']}))
    return dict(seed=seed,index=index,temperature_C=entry['temperature_C'],shunt_V=entry['shunt_V'],codes=entry['codes'],
        decisions=entry['decisions'],expected_decisions=entry['expected_decisions'],
        source_hashes=result['source_hashes'],actual_legacy_sampling_status=full['wave_analysis']['sampling_status'],
        hard_late_decisions=full['wave_analysis']['comparators']['hard'],
        original_numerical_status='passed; this read-only contrast is not the full independent population audit',
        observations=observations,receipts_sha256={n:sha(leaf/n) for n in ['summary.json','run.json','probe.cir']},
        decoded_wave_sha256=entry['decoded_wave_sha256'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    rows=[inspect(seed,index) for seed in [73023,73073] for index in [22,23,26,27]]
    contrasts=[]
    for seed in [73023,73073]:
        selected={r['index']:r for r in rows if r['seed']==seed}
        assert all(r['codes']==selected[22]['codes'] for r in selected.values())
        for j,delay in enumerate([-1,0,.1,.3,.5,1,20]):
            room=selected[22]['observations'][j];hot=selected[26]['observations'][j]
            slopes={}
            for temp,lo,hi in [(25,22,23),(125,26,27)]:
                low=selected[lo]['observations'][j]['mean_V'];high=selected[hi]['observations'][j]['mean_V']
                slopes[str(temp)]={k:(high[k]-low[k])/.001 for k in ['v(isense)','v(xt.icmp)','v(xt.vth_hard)','hard_differential_V']}
            contrasts.append(dict(seed=seed,delay_after_actual_hard_edge_ns=delay,
                hot_minus_room_low_input_V={k:hot['mean_V'][k]-room['mean_V'][k] for k in room['mean_V']},
                hot_minus_room_algebraic_terms_V={k:hot['mean_algebraic_terms_V'][k]-room['mean_algebraic_terms_V'][k] for k in room['mean_algebraic_terms_V']},
                low_high_pair_periodic_finite_difference_V_per_V=slopes))
    result=dict(status='completed read-only two-failure triage',records=rows,contrasts=contrasts,
        scope='Linear interpolation at each actual hard-clock edge then arithmetic mean of last three cycles. Algebraic identity only, not causal attribution. Paired input slopes include dynamic loading/kickback, not an isolated DC gain. All original electrical failures, ±0.5mV criterion, codes and population denominator unchanged. No new simulation.',
        instrumented_or_isolated_source_controls='not run',analyzer_sha256=sha(Path(__file__)))
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(a.output.name,sha(a.output))


if __name__=='__main__':main()
