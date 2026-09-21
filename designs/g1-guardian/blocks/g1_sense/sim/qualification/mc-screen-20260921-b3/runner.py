#!/usr/bin/env python3
"""Bounded revision-B SENSE qualification; run inside flow/run.sh container.
Preserves each deck, log, parameter fingerprint and solver/watchdog status.
Ideal reference and PTAT bias: not the joint calibrated threshold campaign.
"""
import argparse, hashlib, itertools, json, math, os, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
SIM = Path(__file__).resolve().parent
sys.path.insert(0, str(SIM.parents[1] / 'g1_top' / 'sim'))
from run_bounded import run_bounded
PDK = Path('/foss/pdks/ihp-sg13g2')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--image-id', required=True)
    ap.add_argument('--threads',type=int,default=1)
    ap.add_argument('--samples', type=int, default=20)
    ap.add_argument('--start-seed', type=int, default=41001)
    ap.add_argument('--mode', choices=['mc','corner','highrail','noise'], default='mc')
    args = ap.parse_args()
    out = SIM / 'qualification' / args.run_id
    out.mkdir(parents=True, exist_ok=False)
    (out/'runner.py').write_text(Path(__file__).read_text())
    assert (PDK/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    base = (SIM/'tb_sense_mc.cir').read_text().split('.control')[0]
    # Tie the testbench load substrate exactly as in the existing PEX fixture.
    base = base.replace(' sub! ', ' 0 ')
    base = base.replace('.temp @@TEMP@@','.temp 25').replace('@@TEMP@@','25')
    derived=out/'sense_substrate_tied.spice'
    derived.write_text((SIM/'netlist/g1_sense.spice').read_text().replace(' sub! ', ' vss '))
    base = base.replace('.include netlist/g1_sense.spice', '.include '+str(derived.relative_to(SIM)))
    meta = {'runner_arguments':sys.argv[1:], 'git_head': subprocess.check_output(['git','-c','safe.directory=/work','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'image_id_observed_by_host':args.image_id,'pdk_commit':(PDK/'COMMIT').read_text().strip(),
            'ngspice_version':subprocess.check_output(['ngspice','--version'],text=True),
            'source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in [SIM/'netlist/g1_sense.spice',SIM/'tb_sense_mc.cir',Path(__file__)]},
            'model_hashes':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').rglob('*')) if p.is_file()},
            'substrate_fixture':'all schematic resistor sub! nodes tied to the subcircuit vss port; matches physical substrate',
            'scope':'SENSE rev B schematic; ideal VREF=1.04 V, ideal PTAT; no comparator/DAC/BGR mismatch',
            'temperature_validity':'-40 to 125 C supported-range campaign', 'mode':args.mode,
            'cm_definition':'average(SENSE_P,SENSE_N)' if args.mode=='corner' else 'SENSE_N voltage, matching legacy fixture; true average adds Vsh/2'}
    (out/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
    cases = []
    if args.mode=='mc':
        cases=[(f'seed{s}',s,None) for s in range(args.start_seed,args.start_seed+args.samples)]
    elif args.mode=='corner':
        cases=[(f'{m}_{r}_{v}V_{t}C',None,(m,r,v,t)) for m,r,v,t in itertools.product(['tt','ss','ff'],['typ','bcs','wcs'],[3.0,3.3,3.6],[-40,27,85,125])]
    elif args.mode=='highrail': cases=[(f'highrail_tied_{v}',None,('tt','typ',v,27)) for v in [3.3,3.6]]
    else: cases=[('noise_tt_3.3V_27C',None,('tt','typ',3.3,27))]
    summary=[]
    for case_index,(name,seed,corner) in enumerate(cases):
        deck=base
        controls=['set numdgt=15','set filetype=ascii',f'set num_threads={args.threads}']
        if seed is not None:
            controls += [f'setseed {seed}','reset']
            temps=[25,-40,125,25]
        else:
            m,r,v,t=corner
            deck=deck.replace('mos_tt_mismatch','mos_'+m).replace('res_typ_mismatch','res_'+r).replace('VDDA=3.3',f'VDDA={v}').replace('.temp 25',f'.temp {t}')
            temps=[t]
        expected=[]
        for ti,temp in enumerate(temps):
            controls += [f'set temp={temp}',f'alter Iib dc={4.13e-6*(temp+273.15)/300.15:.16g}']
            for cm,sh in itertools.product([-0.1,0,0.3],[0,0.025,0.05]):
                tag=f't{ti}_c{cm}_s{sh}'
                expected.append(tag)
                controls += [f'alter Vcm dc={cm-sh/2 if args.mode=="corner" else cm}',f'alter Vsh dc={sh}','op',
                    f'echo ROW {tag} $&v(isense) $&v(vped) $&v(vref_buf) $&v(xdut.vp) $&v(xdut.vn) $&v(xdut.vped_ref) $&i(vdd)']
            if seed is not None:
                controls += [f'echo FINGERPRINT {ti}']
                for ota in ['xota','xbuf','xref']:
                    for mos in ['xm1','xm2']:
                        for par in ['w','l','delvto','factuo']:
                            controls += [f'print @n.xdut.{ota}.{mos}.nsg13_hv_pmos[{par}]']
                for par in ['nsmm_rsh','nsmm_w','nsmm_l']:
                    controls += [f'print @n.xdut.xr1n0.nr1[{par}]']
        controls += ['echo QUALIFICATION_END','quit 0']
        deck += '.control\n'+'\n'.join(controls)+'\n.endc\n.end\n'
        if args.mode=='highrail':
            deck=(SIM/'tb_sense.cir').read_text()
            for key,val in {'VDDA':v,'VREF':1.04,'VCM':0,'MOS':'mos_tt','RES':'res_typ','CAP':'cap_typ','TEMP':27}.items():
                deck=deck.replace('@@'+key+'@@',str(val))
            deck=deck.replace(' sub! ',' 0 ').replace('.include netlist/g1_sense.spice','.include '+str(derived.relative_to(SIM)))
            deck=deck.replace('set filetype=ascii',f'set filetype=ascii\nset num_threads={args.threads}')
            deck=deck.replace('.endc','echo QUALIFICATION_END\nquit 0\n.endc')
        if args.mode=='noise':
            deck=deck.split('.control')[0].replace('Vsh shp cm dc 0','Vsh shp cm dc 0 ac 1')
            deck += '.control\nset num_threads=1\nset numdgt=15\nnoise v(isense) Vsh dec 40 1 10meg\nprint onoise_total inoise_total\nsetplot noise1\nset wr_singlescale\nset wr_vecnames\nwrdata '+str((out/'noise_spectrum.dat').relative_to(SIM))+' onoise_spectrum inoise_spectrum\necho QUALIFICATION_END\nquit 0\n.endc\n.end\n'
        dp=out/(name+'.cir'); dp.write_text(deck)
        with (out/(name+'.log')).open('x') as log:
            state=run_bounded(['ngspice','-b',str(dp.relative_to(SIM))],log,out/(name+'.json'),300 if args.mode=='highrail' else 120,cwd=SIM,env=dict(os.environ,OMP_NUM_THREADS=str(args.threads)),metadata={'seed':seed,'corner':corner,'omp_threads':args.threads,'deck_sha256':sha(dp)},interval_s=0.2)
        log=(out/(name+'.log')).read_text()
        rows={}
        for line in log.splitlines():
            if line.startswith('ROW '):
                fields=line.split()
                try:
                    nums=list(map(float,fields[2:]))
                    if len(nums)==7 and all(map(math.isfinite,nums)): rows[fields[1]]=nums
                except ValueError: pass
        errors=[l for l in log.splitlines() if re.search(r'(?i)(^Error|fatal|timestep too small|doAnalyses:)',l)]
        result={'name':name,'seed':seed,'corner':corner,'watchdog_status':state['status'],'returncode':state['returncode'],'wall_s':state['wall_s'],'expected_rows':len(expected) if args.mode in ['mc','corner'] else 0,'valid_rows':len(rows),'rows':rows,'errors':errors,
                'status':'passed' if state['returncode']==0 and len(rows)==len(expected) and not errors and 'QUALIFICATION_END' in log else 'failed'}
        if args.mode in ['highrail','noise']:
            required=['vo0','vo5','vo45','vo50','vo55','g1k','f3db','gpk','vlo','vhi','t10','t90','vmax','tsettle','psrr1k','psrr100k','psrr1m','cmg1k','cmg1m']
            if args.mode=='noise': required=['onoise_total','inoise_total']
            measures={k:float(v) for k,v in re.findall(r'^([a-z0-9_]+)\s*=\s*([-+0-9.eE]+)',log,re.M)}
            result['measures']=measures
            if args.mode=='highrail' and all(k in measures for k in ['vo45','vo5','f3db']):
                result['gain']=(measures['vo45']-measures['vo5'])/.04
                result['gain_target_status']='passed' if 19.9<=result['gain']<=20.1 else 'failed'
                result['bandwidth_target_status']='passed' if measures['f3db']>=2e6 else 'failed'
            result['status']='passed' if state['returncode']==0 and all(k in measures and math.isfinite(measures[k]) for k in required) and not errors else 'failed'
        if state['status']=='timeout': result['status']='not run to completion'
        if seed is not None:
            fps=re.findall(r'FINGERPRINT \d+\n(.*?)(?=\n(?:Doing analysis|ROW|FINGERPRINT|QUALIFICATION_END)|\Z)',log,re.S)
            # Keep only parameter outputs, ignoring simulator temperature chatter.
            fps=['\n'.join(l for l in f.splitlines() if l.startswith('@n.')) for f in fps]
            result['fingerprint_count']=len(fps)
            result['frozen_sample']=len(fps)==4 and len(set(fps))==1 and len(fps[0].splitlines())==27
            result['fingerprint_sha256']=[hashlib.sha256(f.encode()).hexdigest() for f in fps]
        summary.append(result)
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(name,result['status'],len(rows),round(state['wall_s'],2),flush=True)
        if args.mode=='corner' and len(summary)>=3 and all(x['status']!='passed' for x in summary[-3:]):
            (out/'not_run.json').write_text(json.dumps({'reason':'three consecutive numerical failures; stop for diagnosis','cases':cases[case_index+1:]},indent=2)+'\n')
            break
if __name__=='__main__': main()
