#!/usr/bin/env python3
"""Prepare a frozen HYS feedback prefix; run only the imposed-input bridge control.

No analog-run mode exists. Prefix/full decks need separate reviewed invocation.
Outputs are local HOME-worktree qualification directories, never external allocator.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import numpy as np

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
REFERENCE = 'clock-coupling-host-low-20260922-a'
PDK = '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
IMAGE = 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
OUTS = (['clk']+['s%d'%i for i in range(7,-1,-1)] +
        ['h%d'%i for i in range(7,-1,-1)]+['count%d'%i for i in range(23,-1,-1)]+
        ['sync_soft','sync_hard','soft_mask','soft_armed','trip','rst_n'])
RAW = ['osc','en','cmp_soft','cmp_hard']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p, d):
    with p.open('x') as f: f.write(json.dumps(d,indent=2)+'\n')
def bridges(run_id):
    return '''.model adc adc_bridge(in_low=0.55 in_high=0.65 rise_delay=1p fall_delay=1p)
.model adc_clock adc_bridge(in_low=0.6 in_high=0.6 rise_delay=1p fall_delay=1p)
.model dac dac_bridge(out_low=0 out_high=1.2 out_undef=0.6 t_rise=0.3n t_fall=0.3n)
.model rtl d_cosim simulation="ivlng" sim_args=["qualification/%s/g1_hys_diagnostic.vvp"]
aclock [osc] [d_osc] adc_clock
aadc [en cmp_soft cmp_hard] [d_en d_cs d_ch] adc
adig [d_osc d_en d_cs d_ch] [%s] rtl
adac [%s] [%s] dac
Vosc osc 0 PULSE(0 1.2 20n .2n .2n 50n 100n)
Ven en 0 PWL(0 0 50n 0 50.3n 1.2)
''' % (run_id, ' '.join('d_'+s for s in OUTS), ' '.join('d_'+s for s in OUTS), ' '.join(OUTS))

def save_vectors(analog=False):
    nodes=RAW+OUTS
    if analog: nodes+=['shp','vref','iptat','vref_buf','vped','isense','xt.icmp','xt.vth_soft','xt.vth_hard']
    return ' '.join('v('+s+')' for s in nodes)

def prepare(run_id, direct_tran=False):
    assert not os.environ.get('G1_RESULTS_ROOT'), 'Unset allocator env after mounting immutable inputs'
    reference=SIM/'qualification'/REFERENCE
    previous=json.loads((reference/'provenance.json').read_text())
    baseline=json.loads((reference/'summary.json').read_text())[0]
    parity=json.loads((reference/'host_parity.json').read_text())
    assert parity['status']=='passed' and all(parity['checks'].values())
    assert previous['seed']==71001 and len(baseline['fingerprints'])==27
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(p.relative_to(pd)):sha(p) for p in (pd/'libs.tech/ngspice/models').rglob('*') if p.is_file()},
        osdi_sha256={str(p.relative_to(pd)):sha(p) for p in (pd/'libs.tech/ngspice/osdi').glob('*.osdi')},
        image_identity_enforcement='flow/run.sh expected config ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2',
        iverilog_version=subprocess.run(['iverilog','-V'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True).stdout)
    assert runtime['pdk_commit']==previous['pdk_commit']==PDK
    assert runtime['model_sha256']==previous['model_sha256']
    assert runtime['ngspice_version']==previous['ngspice_version']
    assert previous['image_id_observed_by_host']==IMAGE
    out=SIM/'qualification'/run_id
    out.mkdir()
    for name in ['sense.spice','trip.spice','bgr.spice','summary.json','provenance.json','host_parity.json']:
        shutil.copyfile(reference/name,out/('reference_'+name if name.endswith('.json') else name))
    ctrl=ROOT/'designs/g1-guardian/blocks/g1_ctrl/rtl'
    for name in ['g1_trip_timer.v','g1_sync2.v','g1_digital_top.v']:
        shutil.copyfile(ctrl/name,out/name)
    for name in ['g1_hys_diagnostic.v','prepare_hys_feedback.py','.spiceinit']:
        shutil.copyfile(SIM/name,out/name)
    # Both reset/divider blocks must match original statements, ignoring comments/whitespace.
    wrapper=(out/'g1_hys_diagnostic.v').read_text()
    original_rtl=(out/'g1_digital_top.v').read_text()
    clean=lambda s: re.sub(r'\s+','',re.sub(r'//[^\n]*','',s))
    old=original_rtl[original_rtl.index('wire arst_n'):original_rtl.index('assign cmp_clk = cmp_clk_q;')+len('assign cmp_clk = cmp_clk_q;')]
    new=wrapper[wrapper.index('wire arst_n'):wrapper.index('assign cmp_clk = cmp_clk_q;')+len('assign cmp_clk = cmp_clk_q;')]
    assert clean(old)==clean(new), 'Reset/divider copy differs'
    bridge=bridges(run_id)
    digital='* Actual timer imposed-input bridge control; no analog circuit qualification\n'+bridge
    digital+='Vcs cmp_soft 0 PWL(0 0 1.2u 0 1.201u 1.2 1.6u 1.2 1.601u 0)\n'
    digital+='Vch cmp_hard 0 PWL(0 0 800n 0 801n 1.2 1.0u 1.2 1.001u 0)\n'
    digital+='.save '+save_vectors()+'\n.control\nset num_threads=1\nset wr_singlescale\nset wr_vecnames\nset numdgt=17\n'
    if direct_tran:
        digital+='setseed 71001\nreset\n'
    digital+='tran .2n 3u 0 .2n\nwrdata qualification/'+run_id+'/digital.dat '+save_vectors()+'\necho HYS_DIGITAL_COMPLETE\nquit 0\n.endc\n.end\n'
    (out/'digital.cir').write_text(digital)
    archived=(reference/(baseline['case']+'.cir')).read_text()
    (out/'reference.cir').write_text(archived)
    prefix=archived.split('.control\n')[0]
    prefix=prefix.replace(REFERENCE,run_id)
    prefix=re.sub(r'^\*[^\n]*\n','',prefix,flags=re.M)
    prefix=re.sub(r'^V[sh][0-7] .+\n','',prefix,flags=re.M)
    prefix=re.sub(r'^Vclk .+\n','',prefix,flags=re.M)
    prefix=re.sub(r'^Vsh .+\n','Vsh shp 0 PWL(0 .010 1.2u .010 1.201u .035 1.6u .035 1.601u .010)\n',prefix,flags=re.M)
    prefix=re.sub(r'^\.save .+\n','',prefix,flags=re.M)
    params='\n'.join(line for line in archived.splitlines() if line.startswith('print @'))
    assert len(params.splitlines())==27
    for name,endpoint in [('prefix',.9),('full_future',3.)]:
        text='* Actual timer and loaded original SENSE/TRIP/BGR; HYS1 diagnostic\n'+prefix+bridge
        text+='.save '+save_vectors(True)+'\n.control\nset num_threads=1\nset numdgt=15\nset filetype=ascii\nsetseed 71001\nreset\nop\n'
        text+='echo HYS_PARAMETERS_BEFORE\n'+params+'\n'
        text+='tran .2n %gu 0 .2n\n'%endpoint
        text+='echo HYS_PARAMETERS_AFTER\n'+params+'\nset wr_singlescale\nset wr_vecnames\n'
        text+='wrdata qualification/'+run_id+'/'+name+'.dat '+save_vectors(True)+'\necho HYS_ANALOG_COMPLETE\nquit 0\n.endc\n.end\n'
        if direct_tran:
            assert text.count('reset\nop\n')==1
            text=text.replace('reset\nop\n','reset\n')
            before='echo HYS_PARAMETERS_BEFORE\n'+params+'\n'
            assert text.count(before)==1
            text=text.replace(before,'')
        (out/(name+'.cir')).write_text(text)
    write_json(out/'runtime.json',runtime)
    write_json(out/'port_map.json',dict(inputs=RAW,outputs=OUTS,vector_order='MSB first',count_bits=24))
    write_json(out/'preparation.json',dict(status='passed',reference=REFERENCE,seed=71001,
        analog_status='not run',runtime_parity='passed',reset_divider_statement_parity='passed',
        static_configuration=dict(soft_time=1,decay=0,hyst_en=1,hyst_2=0,soft_en=1,hard_en=0,inrush=0,soft_code=128,hard_code=240,offset=0),
        prefix_endpoint_us=.9,prefix_watchdog_s=300,full_future_endpoint_us=3,full_future_launch='Not authorized',
        direct_tran=direct_tran,parameter_contract=('27 exact post-transient values vs frozen reference; independent pre-transient query NOT RUN' if direct_tran else '27 before and27 after exact values'),
        sources={n:sha(out/n) for n in ['sense.spice','trip.spice','bgr.spice','g1_trip_timer.v','g1_sync2.v','g1_digital_top.v','g1_hys_diagnostic.v']},
        reference_inputs={str(p.relative_to(ROOT)):sha(p) for p in reference.iterdir() if p.name in ['sense.spice','trip.spice','bgr.spice','summary.json','provenance.json','host_parity.json']},
        scope='Static configuration, ideal clock/bridge. No production mutation, serial/FAST/GATE/pad/route-skew qualification.'))
    write_json(out/'frozen_inputs.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()})
    print(json.dumps(dict(output=str(out.relative_to(ROOT)),status='prepared; analog not run'),indent=2))

def digital(run_id):
    out=SIM/'qualification'/run_id
    frozen=json.loads((out/'frozen_inputs.json').read_text())
    assert all(sha(out/n)==v for n,v in frozen.items())
    commands=[['timeout','20','iverilog','-g2005','-Wall','-Wno-timescale','-s','g1_hys_diagnostic','-o',str(out/'g1_hys_diagnostic.vvp')]+[str(out/n) for n in ['g1_hys_diagnostic.v','g1_trip_timer.v','g1_sync2.v']],
              ['timeout','20','ngspice','-b','qualification/'+run_id+'/digital.cir']]
    env=dict(os.environ)
    env['LD_LIBRARY_PATH']='/foss/tools/iverilog/lib'+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    results=[]
    for name,cmd in zip(['compile','digital'],commands):
        start=time.monotonic()
        with (out/(name+'.log')).open('x') as f:
            proc=subprocess.run(cmd,cwd=str(SIM),stdout=f,stderr=subprocess.STDOUT,env=env)
        results.append(dict(stage=name,command=cmd,returncode=proc.returncode,wall_s=time.monotonic()-start))
        if proc.returncode: break
    checks=dict(compiler_and_simulator_completed=len(results)==2 and all(r['returncode']==0 for r in results),
                input_freeze=all(sha(out/n)==v for n,v in frozen.items()))
    if checks['compiler_and_simulator_completed']:
        try: checks.update(check_digital(out))
        except Exception as exc: checks.update(waveform_checked=False,error=str(exc))
    report=dict(status='passed' if all(v is True for v in checks.values()) else 'failed',checks=checks,commands=results,
                analog_status='not run',upper_counter_dynamic_toggle_coverage='not run; upper bits remain zero under this brief pulse')
    write_json(out/'digital_check.json',report)
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='passed' else 1

def check_digital(out):
    p=out/'digital.dat'
    header=p.open().readline().lower().split()
    assert header==['time']+['v('+n+')' for n in RAW+OUTS]
    data=np.loadtxt(str(p),skiprows=1)
    t=data[:,0]; values=dict(zip(RAW+OUTS,data[:,1:].T))
    assert np.isfinite(data).all() and np.all(np.diff(t)>0) and abs(t[-1]-3e-6)<1e-15
    def sample(n,at): return np.interp(at,t,values[n])>.6
    def code(prefix,width,at): return sum((1<<i)*int(sample(prefix+str(i),at)) for i in range(width))
    samples=[]
    for i in range(30):
        at=(20.1+100*i+5)*1e-9
        samples.append(dict(t=at,raw_s=sample('cmp_soft',at),raw_h=sample('cmp_hard',at),
            sync_s=sample('sync_soft',at),sync_h=sample('sync_hard',at),
            rst=sample('rst_n',at),clk=sample('clk',at),count=code('count',24,at),
            soft=code('s',8,at),hard=code('h',8,at),armed=sample('soft_armed',at),
            mask=sample('soft_mask',at),trip=sample('trip',at)))
    rows=samples[3:]
    count_ok=True
    for prev,row in zip(samples[2:],samples[3:]):
        expected=prev['count']+1 if prev['sync_s'] else max(0,prev['count']-1)
        count_ok &= row['count']==expected
    checks=dict(waveform_finite_complete=True,completion_marker='HYS_DIGITAL_COMPLETE' in (out/'digital.log').read_text(),
        reset_assert_release=[s['rst'] for s in samples[:4]]==[False,False,True,True],
        actual_divider_phase=all(s['clk']==(i%2==1) for i,s in enumerate(samples[2:],start=2)),
        sync_soft_two_flops=all(s['sync_s']==samples[i-1]['raw_s'] for i,s in enumerate(samples) if i>=3),
        sync_hard_two_flops=all(s['sync_h']==samples[i-1]['raw_h'] for i,s in enumerate(samples) if i>=3),
        actual_counter_up_down=count_ok,soft_code_tracks_armed=all(s['soft']==(127 if s['count'] else 128) and s['armed']==bool(s['count']) for s in rows),
        major_carry_both_directions=any(a['soft']==128 and b['soft']==127 for a,b in zip(rows,rows[1:])) and any(a['soft']==127 and b['soft']==128 for a,b in zip(rows,rows[1:])),
        hard_code_port_order=all(s['hard']==240 for s in rows),
        mask_inactive=all(not s['mask'] for s in rows),no_latch=all(not s['trip'] for s in rows),
        recovered_final_count=samples[-1]['count']==0)
    write_json(out/'digital_samples.json',[{k:(bool(v) if isinstance(v,np.bool_) else v) for k,v in s.items()} for s in samples])
    return {k:bool(v) for k,v in checks.items()}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','digital']);p.add_argument('--run-id',required=True)
    p.add_argument('--direct-tran',action='store_true',help='Separate reviewed lifecycle revision; no explicit OP or pre-transient parameter query')
    a=p.parse_args();assert re.fullmatch('[a-z0-9][a-z0-9_-]+',a.run_id)
    if a.mode=='prepare': prepare(a.run_id,a.direct_tran)
    else: raise SystemExit(digital(a.run_id))
