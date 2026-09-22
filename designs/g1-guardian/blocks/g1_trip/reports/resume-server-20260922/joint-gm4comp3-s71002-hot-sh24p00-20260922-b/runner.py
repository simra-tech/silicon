#!/usr/bin/env python3
"""Bounded loaded SENSE/TRIP kickback anchors, with saved differential/decision traces.
No RTL or pad model. Fixed DC inputs screen dynamic decision shift; ramp and phase
campaigns are separate required work. Existing PEX extraction limits apply.
"""
import argparse, bisect, hashlib, json, math, os, re, subprocess, sys
from pathlib import Path
from wave_archive import archive_new_wave
from result_directory import allocate_run
SIM=Path(__file__).resolve().parent
ROOT=SIM.parents[4]
sys.path.insert(0,str(SIM.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen_source_text(path, expected_sha256=None):
    if expected_sha256 is None:return path.read_text()
    source_bytes=path.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest()!=expected_sha256:
        raise ValueError('Frozen candidate source bytes changed before leaf simulation')
    # Match read_text universal-newline behavior while using the exact bytes
    # whose hash was checked, avoiding a second source read.
    return source_bytes.decode().replace('\r\n','\n').replace('\r','\n')
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--run-id',required=True)
    p.add_argument('--image-id',required=True)
    p.add_argument('--timeout-s',type=float,default=300)
    p.add_argument('--replay-reference',help='Prior run ID: require identical normalized deck/source/model hashes before simulation')
    p.add_argument('--profile-reference',help='Archived same-solver reference; only rusage output instrumentation may differ')
    p.add_argument('--profile-rusage',action='store_true',help='Instrument OP and transient CPU/iteration breakdown; analysis settings unchanged')
    p.add_argument('--prepare-only',action='store_true',help='Generate and validate exact replay inputs without launching simulator')
    p.add_argument('--solver',choices=['sparse','klu'],default='sparse')
    p.add_argument('--solver-reference',help='Controlled solver comparison against a completed prior run; not a recovery alias')
    p.add_argument('--failed-solver-reference',help='Bounded changed-solver diagnostic of an archived numerical failure; not a recovery alias or waveform equivalence claim')
    p.add_argument('--seed',type=int)
    p.add_argument('--actual-bgr',action='store_true')
    p.add_argument('--sense-candidate',help='Immutable g1_sense/sim/qualification run containing sense_substrate_tied.spice; isolated source only')
    p.add_argument('--sense-candidate-sha256',help='Require exact consumed candidate bytes before simulation; no circuit change')
    p.add_argument('--code',type=int)
    p.add_argument('--soft-code',type=int)
    p.add_argument('--hard-code',type=int)
    p.add_argument('--temperature',type=float,default=25)
    p.add_argument('--gear',action='store_true')
    p.add_argument('--tight',action='store_true')
    p.add_argument('--headroom-candidate',action='store_true')
    p.add_argument('--shunt-value',type=float)
    p.add_argument('--netlist',choices=['sch','pex'],default='sch')
    p.add_argument('--separate-conditioners',action='store_true')
    p.add_argument('--tstop-us',type=float,default=1.52)
    p.add_argument('--step-from',type=float,help='Vsh before a1ns step starting0.5us; target set by offset')
    p.add_argument('--hold-scale',type=float,default=1)
    p.add_argument('--maxstep-ns',type=float,default=.2)
    p.add_argument('--offsets-mv',default='-0.25,0.25')
    p.add_argument('--threshold',choices=['soft','hard'],default='hard')
    a=p.parse_args(); assert 0<a.timeout_s<=600, 'Authorized watchdog bound is at most600s'; last_cycle=math.floor((a.tstop_us*1e-6-90.2e-9)/100e-9); assert last_cycle>=4
    assert sum(bool(x) for x in [a.replay_reference,a.solver_reference,a.failed_solver_reference,a.profile_reference])<=1, 'Reference modes are distinct evidence'
    assert not a.profile_reference or a.profile_rusage
    assert not a.prepare_only or a.replay_reference, 'Preparation requires exact archived reference'
    assert not a.sense_candidate_sha256 or (a.sense_candidate and re.fullmatch('[0-9a-f]{64}',a.sense_candidate_sha256)), 'Candidate hash requires explicit candidate and64lowercase hex digits'
    out=allocate_run(SIM,a.run_id)
    (out/'runner.py').write_text(Path(__file__).read_text())
    pd=Path('/foss/pdks/ihp-sg13g2')
    assert (pd/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    sense=SIM.parents[1]/'g1_sense/sim'/('netlist/g1_sense.spice' if a.netlist=='sch' else 'postlayout/g1_sense_pex.spice')
    if a.sense_candidate:
        assert a.netlist=='sch' and '/' not in a.sense_candidate and a.sense_candidate not in ['.','..']
        sense=SIM.parents[1]/'g1_sense/sim/qualification'/a.sense_candidate/'sense_substrate_tied.spice'
        assert sense.is_file()
    trip=SIM/('netlist/g1_trip.spice' if a.netlist=='sch' else 'postlayout/g1_trip_pex.spice')
    for name,src in [('sense',sense),('trip',trip)]:
        text=frozen_source_text(src,a.sense_candidate_sha256 if name=='sense' else None).replace(' sub! ',' vss ')
        if name=='trip' and a.headroom_candidate:
            assert a.netlist=='sch','Candidate requires fresh layout/PEX before extracted validation'
            # Keep all resistor instances/order: two unused lower units become grounded dummies.
            for before,after in [('XRC7 c6 c7','XRC7 c6 vss'),('XRC8 c7 c8','XRC8 vss vss'),('XRC9 c8 vss','XRC9 vss vss')]:
                assert text.count(before)==1;text=text.replace(before,after)
            def move_tap(m):
                old=int(m[2]);idx=190+old
                return m[1]+('s'+str(idx) if idx<254 else 't'+str(idx-254))+m[3]
            text,n=re.subn(r'^(XMS0_\d+[ab] )t(\d+)( .+)$',move_tap,text,flags=re.M);assert n==256
        if name=='trip' and a.hold_scale!=1:
            side=26*math.sqrt(a.hold_scale)
            text,n=re.subn(r'(cap_cmim w=)26u( l=)26u',lambda m:m[1]+f'{side:g}u'+m[2]+f'{side:g}u',text)
            assert n==3, f'Expected exactly3hold capacitors, got{n}'
        if name=='trip' and a.separate_conditioners:
            assert a.netlist=='sch', 'Separate conditioners need new physical extraction before PEX qualification'
            text=text.replace('XCOND isense icmp vss g1_cond','XCOND isense icmp vss g1_cond\nXCONDH isense icmp_h vss g1_cond')
            text=text.replace('XCH icmp vth_hard','XCH icmp_h vth_hard')
        (out/(name+'.spice')).write_text(text)
    bgr=None
    if a.actual_bgr:
        bgr=SIM.parents[1]/'g1_bgr/sim/qualification/runs/bgr_mc20_20260921_01/pex_mm.spice'
        assert sha(bgr)=='944aaf94b9a005718abd0ebd92956acc99e8cb7a23ec8556d406736f4e8ef6f9'
        (out/'bgr.spice').write_text(bgr.read_text())
    provenance={'runner_arguments':sys.argv[1:],'watchdog_timeout_s':a.timeout_s,'image_id_observed_by_host':a.image_id,'pdk_commit':(pd/'COMMIT').read_text().strip(),'ngspice_version':subprocess.check_output(['ngspice','--version'],text=True),
        'git_head':subprocess.check_output(['git','-c','safe.directory=/work','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_sha256':{str(f.relative_to(ROOT)):sha(f) for f in [sense,trip,Path(__file__),SIM/'tb_kickback.cir']},
        'model_sha256':{str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},
        'fixture':('Actual flagged BGR PEX drives SENSE VREF and IPTAT; ' if a.actual_bgr else 'Ideal VREF and PTAT; ')+f'25kOhm/1pF conditioner, both full DAC strings and clocked comparators, no RTL/pads; local grounded resistor bulks; nominal process with '+('mismatch enabled, '+str(a.temperature)+'C' if a.seed is not None else 'no mismatch,27C')+';10MHz0.2ns clock edges',
        'sense_candidate':a.sense_candidate,'sense_candidate_sha256':sha(sense) if a.sense_candidate else None,'headroom_candidate':a.headroom_candidate,'candidate_mapping':{'conditioner':'.375','dac_base_units':191,'nominal_soft_hard_codes':[115,191],'fractional_pedestal_offset_LSB':.25,'dummy_resistors':'XRC8/XRC9 grounded, instance order retained'} if a.headroom_candidate else None,'actual_bgr':a.actual_bgr,'bgr_source_sha256':sha(bgr) if bgr else None,'seed':a.seed,'programmed_code':a.code,'fixed_shunt_V':a.shunt_value,'separate_conditioners':a.separate_conditioners,'transient_endpoint_us':a.tstop_us,'candidate_hold_capacitance_scale':a.hold_scale,'candidate_scope':'isolated netlist sensitivity; no layout adoption',
        'rshunt':'1e12 Ohm as existing kickback fixture, not raised gmin','netlist':a.netlist,'solver':a.solver}
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    summary=[]
    for off in map(float,a.offsets_mv.split(',')):
        code={'soft':153,'hard':254}[a.threshold]
        if a.code is not None:code=a.code
        shunt=a.shunt_value if a.shunt_value is not None else code*1.04/5300+off*.001
        tag=f'{a.threshold}_{off:+g}mV'
        deck=(SIM/'tb_kickback.cir').read_text().split('.control')[0].replace('@@VSH@@',f'{shunt:.15g}')
        deck=deck.replace('.include ../../g1_sense/sim/netlist/g1_sense.spice','.include '+str((out/'sense.spice').relative_to(SIM)))
        deck=deck.replace('.include netlist/g1_trip.spice','.include '+str((out/'trip.spice').relative_to(SIM)))
        if a.code is not None:
            for bit in range(8):
                prefix='s' if a.threshold=='soft' else 'h'
                deck=re.sub(r'^V'+prefix+str(bit)+r' .+$',f'V{prefix}{bit} {prefix}{bit} 0 dc {1.2*((code>>bit)&1):g}',deck,flags=re.M)
        for prefix,override in [('s',a.soft_code),('h',a.hard_code)]:
            if override is not None:
                assert 0<=override<=255
                for bit in range(8):deck=re.sub(r'^V'+prefix+str(bit)+r' .+$',f'V{prefix}{bit} {prefix}{bit} 0 dc {1.2*((override>>bit)&1):g}',deck,flags=re.M)
        if a.seed is not None:
            assert a.netlist=='sch','PEX statistical flags/finger scaling need separate qualification'
            deck=deck.replace('mos_tt','mos_tt_mismatch').replace('res_typ','res_typ_mismatch').replace('cap_typ','cap_typ_mismatch').replace('.temp 27',f'.temp {a.temperature}')
        if a.actual_bgr:
            deck=re.sub(r'^(Vref|Iib) .+\n','',deck,flags=re.M)
            deck += '.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib '+('hbt_typ_mismatch' if a.seed is not None else 'hbt_typ')+'\n.include '+str((out/'bgr.spice').relative_to(SIM))+'\nVr4 r4 0 0\nXbgr vdda 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr\n.global sub!\nVsub sub! 0 0\n.option gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7\n'
        if a.tight:deck += '.option reltol=1e-5 vntol=1e-7 abstol=1e-14\n'
        if a.gear:deck += '.option method=gear\n'
        if a.solver=='klu':deck += '.option klu\n'
        deck=deck.replace('.save ','.save v(clk) v(vref) v(iptat) v(vref_buf) ')
        if a.step_from is not None:
            deck=re.sub(r'^Vsh .+$',f'Vsh shp 0 pwl(0 {a.step_from:.15g} 0.5u {a.step_from:.15g} 0.501u {shunt:.15g})',deck,flags=re.M)
            deck=deck.replace('.save ','.save v(shp) ')
        controls=['set num_threads=1','set numdgt=15','set filetype=ascii','op',
            'print v(xt.icmp) v(xt.vth_soft) v(xt.vth_hard)',
            'let dqsoft = v(xt.icmp)-v(xt.vth_soft)','let dqhard = v(xt.icmp)-v(xt.vth_hard)',
            'echo QUIET $&dqsoft $&dqhard',f'tran 0.2n {a.tstop_us}u 0 {a.maxstep_ns}n',
            'let ds = v(xt.icmp)-v(xt.vth_soft)','let dh = v(xt.icmp)-v(xt.vth_hard)']
        for short,signal,start in [('s','soft',last_cycle*100e-9+20e-9),('h','hard',last_cycle*100e-9+70.2e-9)]:
            for suffix,t in [('pre',start-.2e-9),('kick',start+1e-9),('sample',start+20e-9)]:
                controls += [f'meas tran d{short}_{suffix} find d{short} at={t:.15g}']
            controls += [f'meas tran q{short}_sample find v(cmp_{signal}) at={start+20e-9:.15g}']
        if a.seed is not None:
            controls[3:3]=[f'setseed {a.seed}','reset']
            fps=[]
            for path,model in [('xs.xota.xm1','sg13_hv_pmos'),('xs.xref.xm1','sg13_hv_pmos'),('xt.xdacs.xms7_0a','sg13_hv_nmos'),('xt.xdach.xms7_0a','sg13_hv_nmos'),('xt.xcs.xm1','sg13_lv_nmos'),('xt.xch.xm1','sg13_lv_nmos')]:
                for par in ['w','l','delvto','factuo']:fps.append(f'@n.{path}.n{model}[{par}]')
            if a.actual_bgr:fps += ['@n.xbgr.xm34.nsg13_hv_nmos[delvto]','@n.xbgr.xr16.nr1[nsmm_rsh]','@q.xbgr.xq56.qnpn13g2[area]']
            controls += ['echo SAMPLE_PARAMETERS']+['print '+q for q in fps]
        wave=out/(tag+'.dat')
        controls += ['set wr_singlescale','set wr_vecnames',f'wrdata {wave.relative_to(SIM)} v(clk) v(xt.icmp) v(xt.vth_soft) v(xt.vth_hard) v(cmp_soft) v(cmp_hard) v(isense)',
                     'echo QUALIFICATION_END','quit 0']
        if a.separate_conditioners:
            deck=deck.replace('.save ','.save v(xt.icmp_h) ')
            controls=[c.replace('let dqhard = v(xt.icmp)','let dqhard = v(xt.icmp_h)').replace('let dh = v(xt.icmp)','let dh = v(xt.icmp_h)') for c in controls]
            controls=[c+' v(xt.icmp_h)' if c.startswith('wrdata ') else c for c in controls]
        if a.step_from is not None:
            controls=[c+' v(shp)' if c.startswith('wrdata ') else c for c in controls]
        if a.profile_rusage:
            expanded=[]
            for command in controls:
                expanded.append(command)
                if command=='op' or command.startswith('tran '):expanded += ['echo RUSAGE_'+('OP' if command=='op' else 'TRAN')+'_BEGIN','rusage everything','echo RUSAGE_END']
            controls=expanded
        deck += '.control\n'+'\n'.join(controls)+'\n.endc\n.end\n'
        dp=out/(tag+'.cir'); dp.write_text(deck)
        if a.replay_reference or a.solver_reference or a.failed_solver_reference or a.profile_reference:
            reference_id=a.replay_reference or a.solver_reference or a.failed_solver_reference or a.profile_reference
            ref=SIM/'qualification'/reference_id
            previous=json.loads((ref/'provenance.json').read_text())
            normalized=deck.replace(a.run_id,'@RUN@')
            old_normalized=(ref/(tag+'.cir')).read_text().replace(reference_id,'@RUN@')
            sources={name:sha(out/name)==sha(ref/name) for name in ['sense.spice','trip.spice']+(['bgr.spice'] if a.actual_bgr else [])}
            comparison={'reference_run':reference_id,'new_run':a.run_id,'original_timeout_s':previous.get('watchdog_timeout_s',300),'new_timeout_s':a.timeout_s,
                'normalized_deck_exact':normalized==old_normalized,'source_snapshots_exact':sources,
                'model_hashes_exact':provenance['model_sha256']==previous['model_sha256'],
                'image_id_exact':provenance['image_id_observed_by_host']==previous['image_id_observed_by_host'],
                'simulator_version_exact':provenance['ngspice_version']==previous['ngspice_version'],
                'original_deck_sha256':sha(ref/(tag+'.cir')),'new_deck_sha256':sha(dp),
                'normalized_deck_sha256':hashlib.sha256(normalized.encode()).hexdigest()}
            comparison['status']='passed' if all([comparison['normalized_deck_exact'],all(sources.values()),comparison['model_hashes_exact'],comparison['image_id_exact'],comparison['simulator_version_exact']]) else 'failed'
            filename='same_deck_replay.json'
            if a.solver_reference or a.failed_solver_reference:
                reference_status=json.loads((ref/'summary.json').read_text())[0]['solver_status']
                assert reference_status==('failed' if a.failed_solver_reference else 'passed')
                comparison['normalized_deck_except_solver_exact']=normalized.replace('.option klu\n','')==old_normalized.replace('.option klu\n','')
                comparison['scope']='Prelaunch changed-solver isolation only; waveform/decision/sample parity must be assessed after completion. Not an exact-deck recovery alias.'
                if a.failed_solver_reference:
                    assert normalized!=old_normalized, 'Failed-solver diagnostic must actually change solver'
                    comparison['scope']='Changed-solver diagnostic of numerical failure. Original failed attempt remains failed; no reference waveform or recovery alias. Sample fingerprints and new completion must be assessed separately.'
                    comparison['reference_solver_status']=reference_status
                comparison['status']='passed' if all([comparison['normalized_deck_except_solver_exact'],all(sources.values()),comparison['model_hashes_exact'],comparison['image_id_exact'],comparison['simulator_version_exact']]) else 'failed'
                filename='failed_solver_diagnostic_preflight.json' if a.failed_solver_reference else 'controlled_solver_preflight.json'
            if a.profile_reference:
                stripped='\n'.join(line for line in normalized.split('\n') if line not in ['echo RUSAGE_OP_BEGIN','echo RUSAGE_TRAN_BEGIN','rusage everything','echo RUSAGE_END'])
                comparison['normalized_deck_except_output_instrumentation_exact']=stripped==old_normalized
                comparison['scope']='Only added post-analysis rusage output instrumentation; same solver/source/model/numerical settings required. Not a recovery alias.'
                comparison['status']='passed' if all([comparison['normalized_deck_except_output_instrumentation_exact'],all(sources.values()),comparison['model_hashes_exact'],comparison['image_id_exact'],comparison['simulator_version_exact']]) else 'failed'
                filename='controlled_profile_preflight.json'
            (out/filename).write_text(json.dumps(comparison,indent=2)+'\n')
            assert comparison['status']=='passed', 'Replay differs from original; simulation not launched'
        if a.prepare_only:
            (out/'preparation_status.json').write_text(json.dumps({'status':'passed exact replay preparation','simulation_status':'not run','reference':a.replay_reference},indent=2)+'\n')
            continue
        with (out/(tag+'.log')).open('x') as log:
            state=run_bounded(['ngspice','-b',str(dp.relative_to(SIM))],log,out/(tag+'.json'),a.timeout_s,cwd=SIM,metadata={'shunt_V':shunt,'offset_mV':off,'threshold':a.threshold,'netlist':a.netlist,'deck_sha256':sha(dp)},interval_s=1)
        log=(out/(tag+'.log')).read_text()
        measures={k:float(v) for k,v in re.findall(r'^([a-z_]+)\s*=\s*([-+0-9.eE]+)',log,re.M)}
        errs=[l for l in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:)',l)]
        required=['ds_pre','ds_kick','ds_sample','dh_pre','dh_kick','dh_sample','qs_sample','qh_sample']
        complete=state['returncode']==0 and not errs and all(k in measures and math.isfinite(measures[k]) for k in required) and wave.exists()
        quiet=re.search(r'^QUIET (\S+) (\S+)',log,re.M)
        r={'fingerprints':re.findall(r'^(@[^=]+) = (\S+)',log,re.M),'case':tag,'shunt_V':shunt,'measures':measures,'errors':errs,'watchdog_status':state['status'],'returncode':state['returncode'],'wall_s':state['wall_s'],'solver_status':'passed' if complete else 'failed','decision_status':'not run','decision_scope':'Boundary characterization with 0.1mV shunt-equivalent quiet-input guard, not the adopted10percent system no-trip/trip bands','system_band_status':'not applicable (inside10percent ambiguity band)'}
        if state['status'] in ['timeout','interrupted']:r['solver_status']='not run to completion'
        data=[];outputs=[];times=[]
        if complete and quiet:
            quiet=list(map(float,quiet.groups())); r['quiet_soft_hard_V']=quiet
            qi=quiet[0 if a.threshold=='soft' else 1]; q=measures['qs_sample' if a.threshold=='soft' else 'qh_sample']
            # Guard is 0.1mV shunt = 1mV differential after gain20/divide2.
            r['decision_status']='not applicable' if abs(qi)<.001 else ('passed' if (q>.6)==(qi>0) else 'failed')
            r['decision_basis']='quiet differential >=1mV magnitude; output above/below0.6V sampled20ns after each of the last10 evaluation edges'
            data=[]
            for line in wave.read_text().splitlines():
                try: data.append(list(map(float,line.split())))
                except ValueError: pass
            if not data or data[-1][0]<a.tstop_us*1e-6*(1-1e-9):
                r['solver_status']='failed';r['decision_status']='not run';r['errors'].append(f'Saved waveform did not reach{a.tstop_us}us')
            else:
                times=[row[0] for row in data]
                outputs=[]
                col=5 if a.threshold=='soft' else 6
                phase=40e-9 if a.threshold=='soft' else 90.2e-9
                for cycle in range(max(2,last_cycle-9),last_cycle+1):
                    t=cycle*100e-9+phase
                    i=bisect.bisect_left(times,t)
                    lo,hi=data[i-1],data[i]
                    frac=(t-lo[0])/(hi[0]-lo[0])
                    outputs.append(lo[col]+frac*(hi[col]-lo[col]))
                r['sampled_output_V']=outputs
                both={}
                for which,col2,phase2 in [('soft',5,40e-9),('hard',6,90.2e-9)]:
                    vals=[]
                    for cycle in range(max(2,last_cycle-9),last_cycle+1):
                        t=cycle*100e-9+phase2;i=bisect.bisect_left(times,t);lo,hi=data[i-1],data[i];vals.append(lo[col2]+(t-lo[0])/(hi[0]-lo[0])*(hi[col2]-lo[col2]))
                    both[which]=vals
                r['both_sampled_output_V']=both
                r['decision_basis']=f'quiet differential >=1mV magnitude; output sampled20ns after{len(outputs)}evaluation edges; characterization only'
                r['wrong_decisions_outside_guard']=None if abs(qi)<.001 else sum((x>.6)!=(qi>0) for x in outputs)
                r['decision_status']='not applicable' if abs(qi)<.001 else ('passed' if r['wrong_decisions_outside_guard']==0 else 'failed')
        if outputs and a.step_from is None and (shunt<=code*1.04/5300*.9 or shunt>=code*1.04/5300*1.1):
            expected_high=shunt>=code*1.04/5300*1.1
            r['system_band_status']='passed' if all((q>.6)==expected_high for q in outputs) else 'failed'
        if complete and a.step_from is not None and data:
            def value(t,col):
                i=bisect.bisect_left(times,t);lo,hi=data[i-1],data[i]
                return lo[col]+(t-lo[0])/(hi[0]-lo[0])*(hi[col]-lo[col])
            hard_pre=value(.49e-6,6)
            crossings=[]
            for lo,hi in zip(data,data[1:]):
                if hi[0]>=.5e-6 and lo[6]<.6<=hi[6]:
                    crossings.append(lo[0]+(.6-lo[6])/(hi[6]-lo[6])*(hi[0]-lo[0]))
            phase_samples=[(n*100e-9+70e-9,value(n*100e-9+70e-9,8 if a.separate_conditioners else 2)) for n in range(5,last_cycle+1)]
            initial=value(.47e-6,8 if a.separate_conditioners else 2)
            final=sum(v for _,v in phase_samples[-3:])/3
            tol=.01*abs(final-initial)
            settled=next((t-.5e-6 for i,(t,v) in enumerate(phase_samples) if all(abs(vv-final)<=tol for _,vv in phase_samples[i:])),None)
            r['decision_status']='not applicable (step stimulus; quiet value is initial state)'
            r['wrong_decisions_outside_guard']=None
            r['decision_basis']='not applicable; use analog_step_status for step stimulus'
            r['step_metrics']={'initial_shunt_V':a.step_from,'final_shunt_V':shunt,'hard_before_step_V':hard_pre,'hard_first_high_delay_s':crossings[0]-.5e-6 if crossings else None,'hard_final_sample_V':outputs[-1],
                'conditioning_periodic_sample_settling_1percent_s':settled,'settling_definition':'First pre-hard-edge phase sample after which all remaining such samples are within1percent of final3-cycle mean;100ns sampling resolution, not continuous settling',
                'phase_samples':phase_samples}
            r['analog_step_status']='passed' if hard_pre<.6 and crossings and outputs[-1]>.6 and settled is not None else 'failed'
        if a.seed is not None or a.actual_bgr:
            r['system_band_status']='not applicable (statistical calibration probe)'
            r['scope']='Joint BGR PEX + SENSE/TRIP schematic statistical calibration probe; DC bias and transient decisions only, no completed calibration/yield claim'
        summary.append(r); (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        if wave.exists(): archive_new_wave(wave)
        print(tag,r['solver_status'],r['decision_status'],round(state['wall_s'],1),flush=True)
if __name__=='__main__':main()
