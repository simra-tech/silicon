#!/usr/bin/env python3
"""Check the scoped full HYS mechanism and separately expose settling conflict."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import numpy as np

SIM=Path(__file__).resolve().parent
ROOT=SIM.parents[4]
sys.path.insert(0,str(SIM.parents[1]/'g1_top/sim'))
from simulation_errors import solver_failure

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_wave(p):
    with p.open() as f:header=f.readline().lower().split()
    data=np.loadtxt(str(p),skiprows=1)
    assert data.ndim==2 and len(header)==data.shape[1]
    assert np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
    return header,data

def crossings(t,v,up=True):
    inds=np.flatnonzero((v[:-1]<.6)&(v[1:]>=.6) if up else (v[:-1]>.6)&(v[1:]<=.6))
    return [float(t[i]+(.6-v[i])/(v[i+1]-v[i])*(t[i+1]-t[i])) for i in inds]

def project_numeric_row(line,columns):
    """Keep exact common-column bytes, its trailing separator and original EOL.

    ngspice wrdata emits one trailing space after each numeric field. Do not
    normalize number formatting, internal spacing or line endings.
    """
    fields=list(re.finditer(rb'\S+',line))
    assert len(fields)>columns
    end=fields[columns-1].end()
    assert line[end:end+1]==b' '
    eol=b'\r\n' if line.endswith(b'\r\n') else b'\n' if line.endswith(b'\n') else b''
    return line[:end+1]+eol

def raw_prefix_rows(path,project_columns=None):
    rows=[]
    with path.open('rb') as stream:
        stream.readline()  # header projection is checked independently by name
        for line in stream:
            if not line.strip():continue
            if float(line.split()[0])>.85e-6:break
            rows.append(project_numeric_row(line,project_columns) if project_columns else line)
    return rows

def check(out,log_path,returncode):
    prep=json.loads((out/'preparation.json').read_text())
    ref=SIM/'qualification'/prep['reference']
    baseline=json.loads((ref/'reference_summary.json').read_text())[0]
    att=json.loads((ref/'digital_attestation.json').read_text())
    log=log_path.read_text()
    params=[list(x) for x in re.findall(r'^(@[^=\n]+) = (\S+)',log,re.M)]
    checks=dict(simulator_returncode_zero=returncode==0,solver_and_bridge_log_clean=not solver_failure(log),
        completion_marker=log.count('HYS_ANALOG_COMPLETE')==1,
        all27_post_parameters_exact=params==baseline['fingerprints'] and len(params)==27,
        no_before_query_claim='HYS_PARAMETERS_BEFORE' not in log,
        all_reference_inputs_unchanged=all(sha(ROOT/n)==v for n,v in prep['reference_inputs'].items()),
        full_deck_unchanged=sha(out/'full.cir')==prep['deck_sha256'],
        compiled_control_attested=att['status']=='passed' and all(att['checks'].values()))
    result=dict(mechanism_status='failed',checks=checks,parameters_after=params,
        same_instance_parameters_before='not run',overall_design_qualification='not run',
        warnings=dict(model_vmax=log.count('greater than specified by vmax'),temperature_limiter_nan=log.count('temperature limiting function received NaN'),
                      total_warning_mentions=len(re.findall('warning',log,re.I))))
    try:
        header,data=read_wave(out/'full.dat')
        rh,rd=read_wave(ref/'prefix.dat')
        assert header==rh+['v(xt.cmp_clk_n)'] and len(header)==62
        t=data[:,0];assert abs(t[-1]-3e-6)<1e-15
        values=dict(zip(header[1:],data[:,1:].T))
        def val(n,at):return float(np.interp(at,t,values['v('+n+')']))
        def bit(n,at):
            v=val(n,at)
            return 0 if -.1<=v<=.1 else 1 if 1.1<=v<=1.3 else None
        def code(p,w,at):
            b=[bit(p+str(i),at) for i in range(w)]
            return None if None in b else sum((1<<i)*b[i] for i in range(w))
        checks['finite_full_endpoint_all61_vectors']=True
        a=rd[rd[:,0]<=.85e-6];b=data[data[:,0]<=.85e-6,:-1]
        grid_equal=a.shape==b.shape and np.array_equal(a[:,0],b[:,0])
        checks['prefix_grid_exact_0_to_850ns']=bool(grid_equal)
        checks['prefix_original60_values_exact']=bool(grid_equal and np.array_equal(a,b))
        reference_bytes=raw_prefix_rows(ref/'prefix.dat')
        full_bytes=raw_prefix_rows(out/'full.dat',61)  # time plus60 original values
        checks['prefix_original60_decoded_bytes_exact']=reference_bytes==full_bytes
        result['prefix_parity']=dict(reference_rows=len(a),full_rows=len(b),header_comparison='Explicit projection drops only new62nd column actual hard clock',
            all_original_columns_numeric_exact=checks['prefix_original60_values_exact'],
            all_original_columns_decoded_bytes_exact=checks['prefix_original60_decoded_bytes_exact'],
            reference_decoded_prefix_sha256=hashlib.sha256(b''.join(reference_bytes)).hexdigest(),
            full_projected_decoded_prefix_sha256=hashlib.sha256(b''.join(full_bytes)).hexdigest(),
            byte_comparison='Original time+60 numeric fields including exact spacing/formatting and newline; only extra hard-clock field projected away')
        if grid_equal:result['prefix_parity']['max_abs_original_column_difference']=float(np.max(np.abs(a-b)))
        osc=crossings(t,values['v(osc)'])
        soft=crossings(t,values['v(clk)'])
        hard=crossings(t,values['v(xt.cmp_clk_n)'])
        checks['osc_10MHz_period']=len(osc)>=28 and all(abs(b-a-100e-9)<1e-12 for a,b in zip(osc,osc[1:]))
        checks['soft_clock_5MHz_period']=len(soft)>=12 and all(abs(b-a-200e-9)<1e-12 for a,b in zip(soft,soft[1:]))
        checks['hard_actual_clock_5MHz_period']=len(hard)>=11 and all(abs(b-a-200e-9)<.5e-9 for a,b in zip(hard,hard[1:]))
        ports=json.loads((ref/'port_map.json').read_text())
        samples=[]
        for edge in osc:
            at=edge+5e-9
            if at>t[-1]:continue
            samples.append(dict(edge_s=edge,sample_s=at,rst=bit('rst_n',at),clock=bit('clk',at),
                count=code('count',24,at),soft_code=code('s',8,at),hard_code=code('h',8,at),
                raw_soft_at_edge=bit('cmp_soft',max(0,edge-1e-12)),raw_hard_at_edge=bit('cmp_hard',max(0,edge-1e-12)),
                sync_soft=bit('sync_soft',at),sync_hard=bit('sync_hard',at),mask=bit('soft_mask',at),
                armed=bit('soft_armed',at),trip=bit('trip',at)))
        checks['reset_release_phase']=[s['rst'] for s in samples[:4]]==[0,0,1,1]
        checks['sampled_divider_phase']=all(s['clock']==i%2 for i,s in enumerate(samples) if i>=2)
        checks['all_sampled_digital_levels_valid']=all(bit(n,s['sample_s']) is not None for s in samples[3:] for n in ports['outputs'])
        late=[s for s in samples if s['sample_s']>=.6e-6]
        checks['hard_code_stays240']=all(s['hard_code']==240 for s in late)
        checks['soft_code_tracks_actual_counter']=all(s['count'] is not None and s['soft_code']==(127 if s['count'] else 128) and s['armed']==bool(s['count']) for s in late)
        checks['no_inrush_or_trip_mask']=all(s['mask']==0 and s['trip']==0 for s in late)
        transitions=[];sync_ok=True;counter_ok=True
        for prev,row in zip(samples,samples[1:]):
            if row['sample_s']<.6e-6:continue
            valid=prev['count'] is not None and prev['sync_soft'] is not None
            expected=(prev['count']+1 if prev['sync_soft'] else max(0,prev['count']-1)) if valid else None
            counter_ok &= valid and row['count']==expected
            sync_ok &= prev['raw_soft_at_edge'] is not None and prev['raw_hard_at_edge'] is not None and row['sync_soft']==prev['raw_soft_at_edge'] and row['sync_hard']==prev['raw_hard_at_edge']
            transitions.append(dict(edge_s=row['edge_s'],previous_count=prev['count'],previous_sync_soft=prev['sync_soft'],expected_count=expected,actual_count=row['count']))
        checks['actual_timer_up_down_recurrence']=bool(counter_ok)
        checks['actual_sync2_latency']=bool(sync_ok)
        stimulus=np.where(t<=1.2e-6,.010,np.where(t<1.201e-6,.010+(t-1.2e-6)/1e-9*.025,np.where(t<=1.6e-6,.035,np.where(t<1.601e-6,.035-(t-1.6e-6)/1e-9*.025,.010))))
        checks['imposed_shunt_profile_exact']=bool(np.max(np.abs(values['v(shp)']-stimulus))<1e-9)
        # Physical DAC bit midpoint crossings; group one ideal-bridge update within1ns.
        bits=[]
        for i in range(8):
            for up in [True,False]:
                bits += [dict(bit=i,rising=up,time_s=x) for x in crossings(t,values['v(s%d)'%i],up) if x>.6e-6]
        bits.sort(key=lambda x:x['time_s']);groups=[]
        for event in bits:
            if not groups or event['time_s']-groups[-1][-1]['time_s']>1e-9:groups.append([])
            groups[-1].append(event)
        code_events=[]
        for group in groups:
            start,end=group[0]['time_s'],group[-1]['time_s']
            event=dict(first_bit_midpoint_s=start,last_bit_midpoint_s=end,bits=group,
                before_code=code('s',8,start-2e-9),after_code=code('s',8,end+2e-9),
                count_after=code('count',24,end+5e-9),waveform_samples=[])
            stop=min(t[-1],end+200e-9)
            mask=(t>=max(0,start-2e-9))&(t<=stop)
            event['waveform_extrema']={n:dict(min_V=float(values['v('+n+')'][mask].min()),max_V=float(values['v('+n+')'][mask].max())) for n in ['xt.vth_soft','vref_buf','xt.icmp']}
            for delta in [-2,1,5,20,50,100,200]:
                at=end+delta*1e-9
                if 0<=at<=t[-1]:event['waveform_samples'].append(dict(offset_ns=delta,time_s=at,vth_soft_V=val('xt.vth_soft',at),vref_buf_V=val('vref_buf',at),icmp_V=val('xt.icmp',at)))
            following=[x for x in soft if x>=start-1e-12]
            event['next_soft_evaluation_s']=following[0] if following else None
            delay=max(0,following[0]-start) if following else None
            event['delay_to_next_soft_evaluation_s']=delay
            event['one_us_settling_interval_status']='not run' if delay is None else ('passed' if delay>=1e-6 else 'failed')
            code_events.append(event)
        wanted={(128,127),(127,128)}
        covered={(e['before_code'],e['after_code']) for e in code_events if len({b['bit'] for b in e['bits']})==8}
        checks['both_actual_eight_bit_major_carries']=wanted<=covered
        decisions=[]
        for label,edges,threshold,raw,synced in [('soft',soft,'xt.vth_soft','cmp_soft','sync_soft'),('hard',hard,'xt.vth_hard','cmp_hard','sync_hard')]:
            for edge in edges:
                at=edge+20e-9
                if at>t[-1]:continue
                differential=val('xt.icmp',edge)-val(threshold,edge)
                q=val(raw,at);observed=0 if q<.4 else 1 if q>.8 else None
                guarded=edge>=.6e-6 and abs(differential)>.005
                expected=int(differential>0) if guarded else None
                prior=[e for e in code_events if e['first_bit_midpoint_s']<=edge+1e-12]
                last=prior[-1]['first_bit_midpoint_s'] if prior else None
                decisions.append(dict(comparator=label,actual_evaluation_edge_s=edge,sample_s=at,
                    shunt_V=val('shp',edge),icmp_V=val('xt.icmp',edge),threshold_V=val(threshold,edge),differential_V=differential,
                    raw_sample_V=q,observed=observed,guarded=guarded,expected=expected,
                    decision_status=('passed' if observed==expected else 'failed') if guarded else 'not run',
                    synchronized_at_sample=bit(synced,at),counter_at_sample=code('count',24,at),
                    effective_soft_code_at_sample=code('s',8,at),last_soft_code_change_s=last,
                    less_than_one_us_after_code_change=last is not None and edge-last<1e-6))
        guarded=[d for d in decisions if d['guarded']]
        checks['all_guarded_actual_decisions_match']=bool(guarded) and all(d['decision_status']=='passed' for d in guarded)
        checks['guarded_soft_high_exercised']=any(d['comparator']=='soft' and 1.201e-6<=d['actual_evaluation_edge_s']<=1.6e-6 and d['expected']==1 and d['decision_status']=='passed' for d in guarded)
        checks['guarded_soft_low_before_and_after']=all(any(d['comparator']=='soft' and lo<=d['actual_evaluation_edge_s']<=hi and d['expected']==0 and d['decision_status']=='passed' for d in guarded) for lo,hi in [(.6e-6,1.2e-6),(2.5e-6,3e-6)])
        checks['final_quiet_recovery']=all(code('count',24,at)==0 and code('s',8,at)==128 and bit('trip',at)==0 and all(bit(n,at)==0 for n in ['cmp_soft','cmp_hard','sync_soft','sync_hard']) for at in [2.8e-6,2.9e-6,2.99e-6])
        result.update(rows=len(t),endpoint_s=float(t[-1]),counter_samples=samples,counter_transitions=transitions,
            code_events=code_events,evaluations=decisions,maximum_sampled_counter=max(s['count'] for s in samples if s['count'] is not None),
            one_us_settling_interval_status=('failed' if any(e['one_us_settling_interval_status']=='failed' for e in code_events) else 'not run' if not code_events or any(e['one_us_settling_interval_status']=='not run' for e in code_events) else 'passed'),
            waveform_sha256=sha(out/'full.dat'))
    except (OSError,ValueError,AssertionError,IndexError,KeyError,TypeError) as exc:
        checks['waveform_analysis_completed']=False
        result['waveform_analysis_error']=type(exc).__name__+': '+str(exc)
    result['mechanism_status']='passed' if all(checks.values()) else 'failed'
    result['interpretation']='Mechanism and existing1us settling-interval contract are separate outcomes; no complete HYS or physical-interface qualification.'
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--log',type=Path,required=True);p.add_argument('--returncode',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert re.fullmatch('[a-z0-9][a-z0-9_-]+',a.run_id)
    result=check(SIM/'qualification'/a.run_id,a.log,a.returncode)
    with a.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['mechanism_status']=='passed' else 1)
