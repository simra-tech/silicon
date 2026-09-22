#!/usr/bin/env python3
"""Review saved startup/configuration or functional waveforms; never infer pass from exit 0."""
import argparse
import gzip
import hashlib
import json
import math
import re
from pathlib import Path
from simulation_errors import solver_failure

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]

def check_transitions(cols, rows, sc, sr, case):
    """Saved-waveform contracts for quiet, masked-pulse, short-pulse and EN re-arm."""
    index={c:i for i,c in enumerate(cols)}
    def v(r,c):return r[index['v('+c+')']]
    def window(lo,hi):return [r for r in rows if lo*1e-6<=r[0]<=hi*1e-6]
    def state(t):return dict(zip(sc,min(sr,key=lambda r:abs(r[0]-t*1e-6))))
    def decode(d,p):
        bits=[d[f'v({p}{i})'] for i in range(8)]
        if any(.2<x<1 for x in bits):raise ValueError('ambiguous register bit')
        return sum(1<<i for i,x in enumerate(bits) if x>=1)
    pre=window(28,29);cfg=state(28);last=state(rows[-1][0]*1e6)
    tests={'pre_event_enabled':bool(pre) and all(v(r,'gate')>2.5 and v(r,'dig_trip')<.2 for r in pre),
           'configured_thresholds':decode(cfg,'soft')==153 and decode(cfg,'hard')==(254 if case in ['q','f'] else 200),
           'fast_disabled':cfg['v(fast_en)']<.2,
           'state_endpoint':abs(sr[-1][0]-rows[-1][0])<1e-12}
    values={'case':case}
    event=window(30,36)
    expected=1 if case=='q' else 3 if case=='f' else 1.8
    tests['requested_load_present']=bool(event) and abs(max(v(r,'iprof') for r in event)-expected)<1e-6
    if case in ['f','f_mid','clear_read']:
        tripped=window(34,39);disabled=window(41,41.9);rearmed=window(64,72) if case=='clear_read' else window(44,50)
        tests['hard_trip_before_clear']=bool(tripped) and all(v(r,'gate')<1 and v(r,'dig_trip')>1 and v(r,'tripped')>1 and v(r,'fault_n')<.33 for r in tripped)
        mid=state(35);tests['hard_cause_before_clear']=mid['v(cause1)']>1 and mid['v(cause0)']<.2
        if case!='clear_read':tests['disabled_gate_low']=bool(disabled) and all(v(r,'gate')<1 for r in disabled)
        tests['rearmed_after_clear']=bool(rearmed) and all(v(r,'gate')>2.5 and v(r,'dig_trip')<.2 and v(r,'tripped')<.2 and v(r,'fault_n')>2.5 for r in rearmed)
        tests['load_restored']=bool(rearmed) and all(abs(r[index['i(vim)']]-1)<.01 for r in rearmed)
        tests['cause_cleared']=last['v(cause1)']<.2 and last['v(cause0)']<.2
        tests['codes_after_clear']=decode(last,'soft')==153 and decode(last,'hard')==(200 if case=='clear_read' else 254)
        if case=='clear_read':
            frames=decode_serial(sc,sr);values['serial_frames']=frames
            expected_frames=[(8,0),(3,200),(0x8D,0x85),(0x8F,1),(0x90,0),(0x0C,1),(0x8D,0x80),(0x8F,1)]
            tests['serial_readback_and_clear']= [(x['command'],x['data']) for x in frames]==expected_frames
            tests['clear_does_not_restart_inrush']=last['v(inrush_active)']<.2
    else:
        active=window(28,rows[-1][0]*1e6)
        tests['no_trip']=bool(active) and all(v(r,'gate')>2.5 and v(r,'dig_trip')<.2 and v(r,'tripped')<.2 and v(r,'fault_n')>2.5 for r in active)
        tests['load_tracking']=all(abs(r[index['i(vim)']]-v(r,'iprof'))<.01 for r in active)
        tests['no_cause']=last['v(cause1)']<.2 and last['v(cause0)']<.2
        if case!='q':tests['hard_comparator_exercised']=max(v(r,'cmp_hard') for r in event)>1
        if case=='inrush_pulse':
            masked=window(29,36)
            tests['mask_covers_pulse']=bool(masked) and all(v(r,'inrush_active')>1 for r in masked)
            tests['mask_released_before_endpoint']=last['v(inrush_active)']<.2
        else:tests['unmasked']=all(v(r,'inrush_active')<.2 for r in active)
    return tests,values

def decode_serial(cols,rows):
    """Decode complete 16/24-clock transactions from saved pad-side waveforms."""
    import bisect
    index={c:i for i,c in enumerate(cols)};times=[r[0] for r in rows]
    def value(r,name):return r[index['v('+name+')']]
    bits=[]
    for prev,row in zip(rows,rows[1:]):
        if value(prev,'sclk_pad')<1.65<=value(row,'sclk_pad'):
            # Sample10ns later, well before the next falling edge at this fixture's clock.
            sample=rows[min(bisect.bisect_left(times,row[0]+10e-9),len(rows)-1)]
            if value(sample,'sclk_pad')<2.5:raise ValueError('serial sample outside stable high phase')
            data=value(sample,'sdi_pad');out=value(sample,'sdo')
            if .2<data<2.5 or .2<out<1:raise ValueError('ambiguous serial data level')
            bits.append((int(data>2.5),int(out>1)))
    frames=[];i=0
    while i<len(bits):
        if i+8>len(bits):raise ValueError('partial command byte')
        command=sum(bits[i+j][0]<<(7-j) for j in range(8));n=24 if command&128 else 16
        if i+n>len(bits):raise ValueError('partial serial frame')
        offset=16 if command&128 else 8;col=1 if command&128 else 0
        data=sum(bits[i+offset+j][col]<<(7-j) for j in range(8))
        frames.append(dict(command=command,data=data));i+=n
    return frames

def check_retry(cols,rows,sc,sr):
    index={c:i for i,c in enumerate(cols)};si={c:i for i,c in enumerate(sc)}
    def v(r,c):return r[index['v('+c+')']]
    def window(lo,hi):return [r for r in rows if lo*1e-6<=r[0]<=hi*1e-6]
    pre=window(38,39);end=window(1000,1140)
    tests=dict(pre_event_armed=bool(pre) and all(v(r,'gate')>2.5 and v(r,'dig_trip')<.2 and v(r,'inrush_active')<.2 for r in pre),
               final_latched=bool(end) and all(v(r,'gate')<1 and v(r,'dig_trip')>1 and v(r,'tripped')>1 and v(r,'fault_n')<.33 for r in end),
               final_current_low=all(abs(r[index['i(vim)']])<.01 for r in end),
               requested_fault=abs(max(v(r,'iprof') for r in rows)-1.8)<1e-6,
               state_endpoint=abs(sr[-1][0]-1140e-6)<1e-12)
    transitions=[];col=si['v(dig_trip)']
    for a,b in zip(sr,sr[1:]):
        if a[0]>40e-6 and (a[col]<.6)!=(b[col]<.6):
            transitions.append((int(b[col]>=.6),a[0]+(.6-a[col])*(b[0]-a[0])/(b[col]-a[col])))
    tests['two_trips_one_retry']=[x[0] for x in transitions]==[1,0,1]
    values={'trip_transitions':transitions}
    if tests['two_trips_one_retry']:
        t1,tr,t2=[x[1] for x in transitions];fosc=8.994e6
        values['hold_interval_s']=tr-t1
        tests['hold_8192cycles']=abs((tr-t1)*fosc-8193)<=2
        tests['first_trip_under_10us']=0<t1-40e-6<10e-6
        tests['retrip_under_10us']=0<t2-tr<10e-6
        retry=[r for r in rows if tr<=r[0]<=t2+1e-6]
        tests['gate_and_load_reenabled']=bool(retry) and max(v(r,'gate') for r in retry)>2.5 and max(r[index['i(vim)']] for r in retry)>1.7
    frames=decode_serial(sc,sr);values['serial_frames']=frames
    expected=[(8,0),(3,200),(0x0B,7),(9,0),(10,1),(0x8D,0xA5),(0x8E,0x18),(0x8F,2),(0x90,0)]
    tests['serial_config_status_retry_count']= [(x['command'],x['data']) for x in frames]==expected
    return tests,values

def read_wave(path):
    opener=gzip.open if path.suffix=='.gz' else open
    with opener(path,'rt') as f:
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
    if not path.exists():path=HERE/'results/waves'/(tag+'_analog_full.txt.gz')
    cols,rows=read_wave(path)
    state_path=ROOT/'build/g1_top'/('state_'+tag+'.txt')
    if not state_path.exists():state_path=HERE/'results/waves'/(tag+'_state_full.txt.gz')
    a=dict(m['options'])
    matches=[c for c in a['cases'] if tag.startswith(c+'_')]
    case_name=max(matches,key=len) if matches else a['cases'][0] if len(a['cases'])==1 else None
    if case_name is None:raise ValueError('cannot identify active case in batch manifest')
    a['cases']=[case_name]
    defaults={'c_mid':42,'a_s':48,'b_s':64,'d_s':60,'q':44,'f':50,'f_mid':50,'hard_pulse':44,'inrush_pulse':68,'clear_read':72,'retry_read':1140}
    phase_ns=a.get('event_shift_ns',0)
    if not math.isfinite(phase_ns) or not 0 <= phase_ns <= 500:
        raise ValueError('invalid fault phase shift')
    if phase_ns and (case_name not in ['c_mid','hard_pulse'] or a.get('timeline')=='compact' or a.get('tstop')):
        raise ValueError('unsupported fault phase/end-time combination')
    end=(a.get('tstop') or (28 if a.get('timeline')=='compact' else defaults.get(case_name,36)))*1e-6
    tests={'solver_completed':m['status']=='completed','waveform_endpoint':abs(rows[-1][0]-end)<1e-12}
    logpath=HERE/'logs'/(tag+'.log')
    tests['solver_log_clean']=logpath.exists() and not solver_failure(logpath.read_text())
    tests['solver_log_clean']=bool(tests['solver_log_clean'])
    values={}
    if a['analysis']=='prefix':
        tests['prefix_acceptance']=m['diagnostic_acceptance']=='passed'
        if end>=24e-6:
            state=state_path
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
        event=(16 if a.get('timeline')=='compact' else 30)*1e-6+phase_ns*1e-9
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
        state=state_path
        if state.exists():
            sc,sr=read_wave(state)
            tests['state_endpoint']=abs(sr[-1][0]-end)<1e-12
            ds=dict(zip(sc,min(sr,key=lambda r:abs(r[0]-(event-.2e-6)))))
            def code(prefix):
                bits=[ds['v(%s%d)'%(prefix,i)] for i in range(8)]
                if any(.2<x<1 for x in bits):raise ValueError('ambiguous configuration bit')
                return sum(1<<i for i,v in enumerate(bits) if v>=1)
            values['soft_code_before_fault']=code('soft');values['hard_code_before_fault']=code('hard')
            tests['configured_thresholds']=values['soft_code_before_fault']==153 and values['hard_code_before_fault']==(200 if a['cases']==['c_mid'] else 254)
            tests['fast_configuration']=ds['v(fast_en)']>1 if case_name=='c_fast' else ds['v(fast_en)']<.2
            ds=dict(zip(sc,sr[-1]));tests['hard_cause']=ds['v(cause1)']>1 and ds['v(cause0)']<.2
        else:
            tests['required_state_waveform']=False
            values['configuration_and_cause_check']='not run; required state waveform absent'
    elif case_name in ['a_s','b_s','d_s']:
        idx={c:i for i,c in enumerate(cols)}
        def val(r,c):return r[idx[c]]
        event=30e-6
        before=[r for r in rows if 29e-6<=r[0]<event]
        after=[r for r in rows if r[0]>=event]
        tests['pre_event_armed']=bool(before) and all(val(r,'v(gate)')>2.5 and val(r,'v(inrush_active)')<.2 and val(r,'v(dig_trip)')<.2 for r in before)
        tests['soft_comparator_exercised']=bool(after) and max(val(r,'v(cmp_soft)') for r in after)>1
        tests['hard_comparator_inactive']=bool(after) and max(val(r,'v(cmp_hard)') for r in after)<.2
        peak=1.4 if case_name=='d_s' else 1.5
        tests['requested_load_present']=abs(max(val(r,'v(iprof)') for r in after)-peak)<1e-6
        sc,sr=read_wave(state_path)
        tests['state_endpoint']=abs(sr[-1][0]-end)<1e-12
        state=dict(zip(sc,min(sr,key=lambda r:abs(r[0]-29e-6))));last=dict(zip(sc,sr[-1]))
        def code(d,p,n):
            bits=[d[f'v({p}{i})'] for i in range(n)]
            if any(.2<x<1 for x in bits):raise ValueError('ambiguous saved register bit')
            return sum(1<<i for i,x in enumerate(bits) if x>=1)
        tests['configured_thresholds']=code(state,'soft',8)==153 and code(state,'hard',8)==254
        values.update(soft_peak=code(last,'sp',16),fault_event_s=event,behavioral_front=m.get('effective',{}).get('front')=='beh')
        if case_name in ['a_s','d_s']:
            tests['no_trip']=all(val(r,'v(gate)')>2.5 and val(r,'v(dig_trip)')<.2 and val(r,'v(tripped)')<.2 and val(r,'v(fault_n)')>2.5 for r in after)
            tests['load_tracking']=max(abs(val(r,'i(vim)')-val(r,'v(iprof)')) for r in after)<.01
            tests['no_cause']=last['v(cause1)']<.2 and last['v(cause0)']<.2
            tests['subwindow_peak']=values['soft_peak']==0
        else:
            first=next((i for i,r in enumerate(after) if val(r,'v(gate)')<1),None)
            tests['gate_low_reached']=first is not None
            if first is not None:
                dt=after[first][0]-event;values['gate_low_delay_s']=dt
                # Named behavioral fixture's ideal clock is pinned in its deck.
                fosc=8.994e6 if a['netlist']=='pex' else 9.919e6
                tests['configured_256cycle_soft_window']=(255/fosc)<=dt<=(268/fosc)
                tests['stays_low']=all(val(r,'v(gate)')<1 for r in after[first:])
            tests['latched_soft_cause']=last['v(cause1)']<.2 and last['v(cause0)']>1 and last['v(dig_trip)']>1 and val(rows[-1],'v(tripped)')>1
            tests['current_low']=abs(val(rows[-1],'i(vim)'))<.01
            tests['fault_asserted']=val(rows[-1],'v(fault_n)')<.33
            tests['one_window_peak']=values['soft_peak']==1
    elif case_name in ['q','f','f_mid','hard_pulse','inrush_pulse','clear_read']:
        sc,sr=read_wave(state_path)
        extra,values=check_transitions(cols,rows,sc,sr,case_name)
        tests.update(extra)
    elif case_name=='retry_read':
        sc,sr=read_wave(state_path);extra,values=check_retry(cols,rows,sc,sr);tests.update(extra)
    else:
        return dict(status='not run',reason='functional acceptance evaluator does not support this case')
    return dict(status='passed' if all(tests.values()) else 'failed',tests=tests,values=values,
        waveform=str(path.relative_to(ROOT)),waveform_sha256=hashlib.sha256(gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()).hexdigest(),
        state_waveform_sha256=hashlib.sha256(gzip.decompress(state_path.read_bytes()) if state_path.suffix=='.gz' else state_path.read_bytes()).hexdigest() if state_path.exists() else None,
        manifest_sha256=hashlib.sha256(mp.read_bytes()).hexdigest(),
        limitations='Front-end abstraction is identified by manifest effective.front; beh does not verify BGR/SENSE/TRIP analog accuracy. C-PEX blocks; ideal oscillator and fitted output pads; not real-FET or full assembled RC qualification. Comparator numerical tolerance qualification and full serial counter readback remain separate. Compact timeline does not qualify SEU fill.')

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
