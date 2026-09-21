#!/usr/bin/env python3
"""Review saved startup/configuration or functional waveforms; never infer pass from exit 0."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]

def read_wave(path):
    with path.open() as f:
        cols=f.readline().split()
        rows=[list(map(float,l.split())) for l in f if l.strip()]
    if len(rows)<2 or any(len(r)!=len(cols) or not all(map(math.isfinite,r)) for r in rows):
        raise ValueError('missing/nonfinite/incomplete waveform')
    if rows[0][0]!=0 or any(b[0]<a[0] for a,b in zip(rows,rows[1:])):
        raise ValueError('invalid waveform times')
    return cols,rows

def check(tag):
    mp=HERE/'logs'/(tag+'.json');m=json.loads(mp.read_text())
    path=ROOT/'build/g1_top'/('waves_'+tag+'.txt')
    cols,rows=read_wave(path)
    a=m['options'];end=(a.get('tstop') or (28 if a.get('timeline')=='compact' else 42 if a['cases']==['c_mid'] else 36))*1e-6
    tests={'solver_completed':m['status']=='completed','waveform_endpoint':abs(rows[-1][0]-end)<1e-12}
    values={}
    if a['analysis']=='prefix':
        tests['prefix_acceptance']=m['diagnostic_acceptance']=='passed'
        if end>=24e-6:
            state=ROOT/'build/g1_top'/('state_'+tag+'.txt')
            sc,sr=read_wave(state);d=dict(zip(sc,sr[-1]))
            tests['state_endpoint']=abs(sr[-1][0]-end)<1e-12
            def decode(p):
                bits=[d['v(%s%d)'%(p,i)] for i in range(8)]
                if any(0.2<x<1 for x in bits):raise ValueError('ambiguous DAC logic level')
                return sum((1<<i) for i,x in enumerate(bits) if x>=1)
            values.update(soft_code=decode('soft'),hard_code=decode('hard'),inrush=d['v(inrush_active)'],en=d['v(en_core)'])
            if a['cases']==['c']:
                tests.update(soft_code=values['soft_code']==153,hard_code=values['hard_code']==254,
                    armed=values['inrush']<0.2 and values['en']>1,not_tripped=d['v(dig_trip)']<0.2)
    elif a['cases'] in [['c'],['c_fast'],['e'],['e20'],['c_mid']]:
        idx={c:i for i,c in enumerate(cols)}
        def val(r,c):return r[idx[c]]
        def sample(t):return min(rows,key=lambda r:abs(r[0]-t))
        event=(16 if a.get('timeline')=='compact' else 30)*1e-6
        before=[r for r in rows if event-1e-6<=r[0]<event]
        after=[r for r in rows if r[0]>=event]
        tests['pre_event_armed']=bool(before) and all(val(r,'v(gate)')>2.5 and val(r,'v(inrush_active)')<0.2 and val(r,'v(dig_trip)')<0.2 for r in before)
        crossing=next((i for i,r in enumerate(after) if val(r,'v(gate)')<1),None)
        if crossing is not None:
            dt=after[crossing][0]-event
            values['gate_low_delay_s']=dt
            tests['latency_under_10us']=0<=dt<10e-6
            tests['stays_low']=all(val(r,'v(gate)')<1 for r in after[crossing:])
        else:tests['gate_low_reached']=False
        last=rows[-1]
        values.update(gate_end_V=val(last,'v(gate)'),current_end_A=val(last,'i(vim)'))
        tests['digital_trip_latched']=val(last,'v(dig_trip)')>1
        tests['analog_trip_latched']=val(last,'v(tripped)')>1
        tests['load_current_below_1pct']=abs(values['current_end_A'])<0.01
        tests['fault_asserted']=val(last,'v(fault_n)')<0.33
        peak=max(val(r,'v(iprof)') for r in after)
        expected={'c':3,'c_fast':3,'e':4,'e20':4,'c_mid':1.8}[a['cases'][0]]
        tests['requested_fault_present']=abs(peak-expected)<1e-6
        values['modeled_gate_and_switch_only']=True
        values['fault_event_s']=event
        state=ROOT/'build/g1_top'/('state_'+tag+'.txt')
        if state.exists():
            sc,sr=read_wave(state)
            ds=dict(zip(sc,min(sr,key=lambda r:abs(r[0]-(event-.2e-6)))))
            def code(prefix):
                bits=[ds['v(%s%d)'%(prefix,i)] for i in range(8)]
                if any(.2<x<1 for x in bits):raise ValueError('ambiguous configuration bit')
                return sum(1<<i for i,v in enumerate(bits) if v>=1)
            values['soft_code_before_fault']=code('soft');values['hard_code_before_fault']=code('hard')
            tests['configured_thresholds']=values['soft_code_before_fault']==153 and values['hard_code_before_fault']==(200 if a['cases']==['c_mid'] else 254)
            ds=dict(zip(sc,sr[-1]));tests['hard_cause']=ds['v(cause1)']>1 and ds['v(cause0)']<.2
        else:values['configuration_and_cause_check']='not run; state waveform absent in older runner'
    else:
        return dict(status='not run',reason='functional acceptance evaluator does not support this case')
    return dict(status='passed' if all(tests.values()) else 'failed',tests=tests,values=values,
        waveform=str(path.relative_to(ROOT)),waveform_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        manifest_sha256=hashlib.sha256(mp.read_bytes()).hexdigest(),
        limitations='C-PEX blocks; ideal oscillator and fitted output pads; not real-FET or full assembled RC qualification. Comparator numerical tolerance qualification and full serial counter readback remain separate. Compact timeline does not qualify SEU fill.')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('tag');ap.add_argument('--output',required=True);a=ap.parse_args()
    try:r=check(a.tag)
    except (OSError,ValueError,KeyError) as exc:
        # Public evidence uses repository-relative paths on every host.
        r={'status':'failed','error':str(exc).replace(str(ROOT)+'/', '')}
    r.update(tag=a.tag,checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with Path(a.output).open('x') as f:json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps(r,indent=2))
    if r['status']!='passed':raise SystemExit(1)

if __name__=='__main__':main()
