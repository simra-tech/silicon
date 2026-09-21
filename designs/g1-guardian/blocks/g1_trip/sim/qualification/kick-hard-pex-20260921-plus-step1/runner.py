#!/usr/bin/env python3
"""Bounded loaded SENSE/TRIP kickback anchors, with saved differential/decision traces.
No RTL or pad model. Fixed DC inputs screen dynamic decision shift; ramp and phase
campaigns are separate required work. Existing PEX extraction limits apply.
"""
import argparse, bisect, hashlib, json, math, os, re, subprocess, sys
from pathlib import Path
SIM=Path(__file__).resolve().parent
ROOT=SIM.parents[4]
sys.path.insert(0,str(SIM.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--run-id',required=True)
    p.add_argument('--image-id',required=True)
    p.add_argument('--netlist',choices=['sch','pex'],default='sch')
    p.add_argument('--separate-conditioners',action='store_true')
    p.add_argument('--tstop-us',type=float,default=1.52)
    p.add_argument('--hold-scale',type=float,default=1)
    p.add_argument('--maxstep-ns',type=float,default=.2)
    p.add_argument('--offsets-mv',default='-0.25,0.25')
    p.add_argument('--threshold',choices=['soft','hard'],default='hard')
    a=p.parse_args(); last_cycle=math.floor((a.tstop_us*1e-6-90.2e-9)/100e-9); assert last_cycle>=4
    out=SIM/'qualification'/a.run_id; out.mkdir(parents=True,exist_ok=False)
    (out/'runner.py').write_text(Path(__file__).read_text())
    pd=Path('/foss/pdks/ihp-sg13g2')
    assert (pd/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    sense=SIM.parents[1]/'g1_sense/sim'/('netlist/g1_sense.spice' if a.netlist=='sch' else 'postlayout/g1_sense_pex.spice')
    trip=SIM/('netlist/g1_trip.spice' if a.netlist=='sch' else 'postlayout/g1_trip_pex.spice')
    for name,src in [('sense',sense),('trip',trip)]:
        text=src.read_text().replace(' sub! ',' vss ')
        if name=='trip' and a.hold_scale!=1:
            side=26*math.sqrt(a.hold_scale)
            text,n=re.subn(r'(cap_cmim w=)26u( l=)26u',lambda m:m[1]+f'{side:g}u'+m[2]+f'{side:g}u',text)
            assert n==3, f'Expected exactly3hold capacitors, got{n}'
        if name=='trip' and a.separate_conditioners:
            assert a.netlist=='sch', 'Separate conditioners need new physical extraction before PEX qualification'
            text=text.replace('XCOND isense icmp vss g1_cond','XCOND isense icmp vss g1_cond\nXCONDH isense icmp_h vss g1_cond')
            text=text.replace('XCH icmp vth_hard','XCH icmp_h vth_hard')
        (out/(name+'.spice')).write_text(text)
    provenance={'runner_arguments':sys.argv[1:],'image_id_observed_by_host':a.image_id,'pdk_commit':(pd/'COMMIT').read_text().strip(),'ngspice_version':subprocess.check_output(['ngspice','--version'],text=True),
        'git_head':subprocess.check_output(['git','-c','safe.directory=/work','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_sha256':{str(f.relative_to(ROOT)):sha(f) for f in [sense,trip,Path(__file__),SIM/'tb_kickback.cir']},
        'model_sha256':{str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},
        'fixture':'25kOhm/1pF conditioner, both DAC strings and clocked comparators, ideal VREF and PTAT, no RTL/pads; schematic floating resistor bulks tied to local vss; nominal tt/typ/cap_typ 27C; 10MHz 0.2ns clock edges',
        'separate_conditioners':a.separate_conditioners,'transient_endpoint_us':a.tstop_us,'candidate_hold_capacitance_scale':a.hold_scale,'candidate_scope':'isolated netlist sensitivity; no layout adoption',
        'rshunt':'1e12 Ohm as existing kickback fixture, not raised gmin','netlist':a.netlist}
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    summary=[]
    for off in map(float,a.offsets_mv.split(',')):
        code={'soft':153,'hard':254}[a.threshold]
        shunt=code*1.04/5300+off*.001
        tag=f'{a.threshold}_{off:+g}mV'
        deck=(SIM/'tb_kickback.cir').read_text().split('.control')[0].replace('@@VSH@@',f'{shunt:.15g}')
        deck=deck.replace('.include ../../g1_sense/sim/netlist/g1_sense.spice','.include '+str((out/'sense.spice').relative_to(SIM)))
        deck=deck.replace('.include netlist/g1_trip.spice','.include '+str((out/'trip.spice').relative_to(SIM)))
        deck=deck.replace('.save ','.save v(clk) ')
        controls=['set num_threads=1','set numdgt=15','set filetype=ascii','op',
            'print v(xt.icmp) v(xt.vth_soft) v(xt.vth_hard)',
            'let dqsoft = v(xt.icmp)-v(xt.vth_soft)','let dqhard = v(xt.icmp)-v(xt.vth_hard)',
            'echo QUIET $&dqsoft $&dqhard',f'tran 0.2n {a.tstop_us}u 0 {a.maxstep_ns}n',
            'let ds = v(xt.icmp)-v(xt.vth_soft)','let dh = v(xt.icmp)-v(xt.vth_hard)']
        for short,signal,start in [('s','soft',last_cycle*100e-9+20e-9),('h','hard',last_cycle*100e-9+70.2e-9)]:
            for suffix,t in [('pre',start-.2e-9),('kick',start+1e-9),('sample',start+20e-9)]:
                controls += [f'meas tran d{short}_{suffix} find d{short} at={t:.15g}']
            controls += [f'meas tran q{short}_sample find v(cmp_{signal}) at={start+20e-9:.15g}']
        wave=out/(tag+'.dat')
        controls += ['set wr_singlescale','set wr_vecnames',f'wrdata {wave.relative_to(SIM)} v(clk) v(xt.icmp) v(xt.vth_soft) v(xt.vth_hard) v(cmp_soft) v(cmp_hard) v(isense)',
                     'echo QUALIFICATION_END','quit 0']
        if a.separate_conditioners:
            deck=deck.replace('.save ','.save v(xt.icmp_h) ')
            controls=[c.replace('let dqhard = v(xt.icmp)','let dqhard = v(xt.icmp_h)').replace('let dh = v(xt.icmp)','let dh = v(xt.icmp_h)') for c in controls]
            controls=[c+' v(xt.icmp_h)' if c.startswith('wrdata ') else c for c in controls]
        deck += '.control\n'+'\n'.join(controls)+'\n.endc\n.end\n'
        dp=out/(tag+'.cir'); dp.write_text(deck)
        with (out/(tag+'.log')).open('x') as log:
            state=run_bounded(['ngspice','-b',str(dp.relative_to(SIM))],log,out/(tag+'.json'),300,cwd=SIM,metadata={'shunt_V':shunt,'offset_mV':off,'threshold':a.threshold,'netlist':a.netlist,'deck_sha256':sha(dp)},interval_s=1)
        log=(out/(tag+'.log')).read_text()
        measures={k:float(v) for k,v in re.findall(r'^([a-z_]+)\s*=\s*([-+0-9.eE]+)',log,re.M)}
        errs=[l for l in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:)',l)]
        required=['ds_pre','ds_kick','ds_sample','dh_pre','dh_kick','dh_sample','qs_sample','qh_sample']
        complete=state['returncode']==0 and not errs and all(k in measures and math.isfinite(measures[k]) for k in required) and wave.exists()
        quiet=re.search(r'^QUIET (\S+) (\S+)',log,re.M)
        r={'case':tag,'shunt_V':shunt,'measures':measures,'errors':errs,'watchdog_status':state['status'],'returncode':state['returncode'],'wall_s':state['wall_s'],'solver_status':'passed' if complete else 'failed','decision_status':'not run','decision_scope':'Boundary characterization with 0.1mV shunt-equivalent quiet-input guard, not the adopted10percent system no-trip/trip bands','system_band_status':'not applicable (inside10percent ambiguity band)'}
        if state['status']=='timeout':r['solver_status']='not run to completion'
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
                r['wrong_decisions_outside_guard']=None if abs(qi)<.001 else sum((x>.6)!=(qi>0) for x in outputs)
                r['decision_status']='not applicable' if abs(qi)<.001 else ('passed' if r['wrong_decisions_outside_guard']==0 else 'failed')
        summary.append(r); (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(tag,r['solver_status'],r['decision_status'],round(state['wall_s'],1),flush=True)
if __name__=='__main__':main()
