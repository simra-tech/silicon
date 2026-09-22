#!/usr/bin/env python3
"""Eight-device extracted up-shifter mismatch qualification and fixed-load screen."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent; SIM=HERE.parent; ROOT=HERE.parents[6]
PDK=Path('/foss/pdks/ihp-sg13g2')
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mode',choices=['qualify','screen'],required=True)
    parser.add_argument('--qualification',type=Path)
    parser.add_argument('--seeds',default='')
    a=parser.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    source=SIM.parent/'reports/flat-pex-20260921T150429Z_42162722/ngspice_pex.spice'
    assert sha(source)=='087bdf16283f0aad73d940ef5c5a8d577764622ab243580bb77766d35a9da293'
    initial=SIM/'.spiceinit'; original=source.read_text()
    cards=[line for line in original.splitlines() if line.startswith('XM')]
    assert len(cards)==8 and all('mm_ok' not in line for line in cards)
    targets=['n.x1.'+line.split()[0].lower()+'.n'+line.split()[5] for line in cards]
    assert len(set(targets))==8
    params=['w','l','delvto','factuo']
    models={str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))}
    for name in ('sg13g2_moslv_mod_mismatch.lib','sg13g2_moshv_mod_mismatch.lib'):
        assert 'mm_ok=0' in (PDK/'libs.tech/ngspice/models'/name).read_text()
    binding={str(p.relative_to(ROOT)):sha(p) for p in (source,initial,Path(__file__))}
    out=a.output.resolve();out.mkdir(parents=True)
    shutil.copyfile(Path(__file__),out/'runner.py')
    for enabled in (0,1):
        text='\n'.join(line+f' mm_ok={enabled}' if line.startswith('XM') else line for line in original.splitlines())+'\n'
        (out/f'source_mm{enabled}.spice').write_text(text)
    contract=dict(source_sha256=sha(source),script_sha256=sha(Path(__file__)),source_bindings=binding,model_hashes=models,
                  PDK_commit=(PDK/'COMMIT').read_text().strip(),ngspice=subprocess.check_output(['ngspice','-v'],universal_newlines=True),
                  targets=targets,parameters=params,temperature_order_C=[27,125,-40,27],
                  VDD_V=1.2,VDDA_V=3.3,load_fF=20,stop_s=900e-9,max_step_s=100e-12,
                  logic_low_max_V=.33,logic_high_min_V=2.97,wall_limit_s=120,
                  limits='Fixed20fF macro CPEX; not assembled wire resistance, actual receiver mismatch, power-order/back-powering, terminal reliability, or physical silicon qualification.')
    if a.mode=='screen':
        assert a.qualification is not None
        q=json.loads(a.qualification.read_text())
        assert q['status']=='passed' and q['source_sha256']==sha(source) and q['script_sha256']==sha(Path(__file__))
        contract['qualification_sha256']=sha(a.qualification)
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')

    def run(name,seed,enabled):
        leaf=out/name;leaf.mkdir();shutil.copyfile(initial,leaf/'.spiceinit')
        deck=f'''* Source-bound up-shifter fixed-load mismatch screen
.include {out/f'source_mm{enabled}.spice'}
.temp 27
.option method=gear reltol=1e-4 abstol=1e-16 vntol=1e-7 gmin=1e-16 seed={seed}
.lib {PDK}/libs.tech/ngspice/models/cornerMOSlv.lib mos_tt_mismatch
.lib {PDK}/libs.tech/ngspice/models/cornerMOShv.lib mos_tt_mismatch
.global sub!
Vsub sub! 0 0
Vdd vdd 0 1.2
Vdda vdda 0 3.3
X1 in out vdd vdda 0 g1_ls_up
Cload out 0 20f
Vin in 0 pwl(0 0 300n 0 301n 1.2 600n 1.2 601n 0 900n 0)
.control
set num_threads=1
set numdgt=17
set wr_singlescale
set wr_vecnames
setseed {seed}
reset
'''
        marks=[]
        for index,temp in enumerate(contract['temperature_order_C']):
            deck+=f'set temp={temp}\nop\n'
            for phase in ('before','after'):
                marker=f't{index}_{phase}';marks.append(marker)
                deck+='echo LS_FP_BEGIN '+marker+'\n'+'\n'.join(f'print @{target}[{p}]' for target in targets for p in params)+'\necho LS_FP_END '+marker+'\n'
                if phase=='before':
                    deck+='tran 100p 900n 0 100p\n'
                    deck+=f'wrdata {leaf}/t{index}.tsv v(in) v(out) i(vdd) i(vdda) v(x1.n_3) v(x1.n_4) v(x1.n_5)\n'
        deck+='echo LS_MISMATCH_END\nquit 0\n.endc\n.end\n'
        (leaf/'fixture.cir').write_text(deck)
        with (leaf/'tool.log').open('x') as log:
            state=run_bounded(['ngspice','-b','fixture.cir'],log,leaf/'run.json',120,cwd=leaf,env=dict(os.environ,OMP_NUM_THREADS='1'),interval_s=.5)
        log=(leaf/'tool.log').read_text();fps={};waves={};metrics={};errors=[]
        try:
            for marker in marks:
                assert log.count('LS_FP_BEGIN '+marker+'\n')==1 and log.count('LS_FP_END '+marker+'\n')==1
                part=log.split('LS_FP_BEGIN '+marker+'\n')[1].split('LS_FP_END '+marker+'\n')[0]
                values={k:float(v) for k,v in re.findall(r'(?m)^(@\S+)\s*=\s*([-+\d.eE]+)\s*$',part)}
                assert len(values)==32 and all(map(math.isfinite,values.values()))
                fps[marker]=values
            assert all(values==fps[marks[0]] for values in fps.values())
            for index,temp in enumerate(contract['temperature_order_C']):
                path=leaf/f't{index}.tsv';lines=path.read_text().splitlines()
                rows=[list(map(float,line.split())) for line in lines[1:] if line.strip()]
                assert len(rows)>2 and all(len(r)==8 and all(map(math.isfinite,r)) for r in rows)
                assert abs(rows[0][0])<1e-15 and abs(rows[-1][0]-900e-9)<1e-15
                assert all(b[0]>aa[0] for aa,b in zip(rows,rows[1:]))
                low=[r for r in rows if 100e-9<=r[0]<=290e-9 or 700e-9<=r[0]<=890e-9]
                high=[r for r in rows if 400e-9<=r[0]<=590e-9]
                assert low and high
                values=dict(low_max_V=max(r[2] for r in low),high_min_V=min(r[2] for r in high),
                            VDDA_peak_draw_A=max(-r[4] for r in rows),VDD_peak_draw_A=max(-r[3] for r in rows),
                            VDDA_low_mean_A=-sum(r[4] for r in low)/len(low),VDDA_high_mean_A=-sum(r[4] for r in high)/len(high))
                values['logic_status']='passed' if values['low_max_V']<=.33 and values['high_min_V']>=2.97 else 'failed'
                metrics[str(index)]=values;waves[str(index)]=dict(sha256=sha(path),rows=len(rows),temperature_C=temp)
        except (AssertionError,ValueError,OSError) as exc:errors.append(type(exc).__name__+': '+str(exc))
        numerical_errors=[line for line in log.splitlines() if re.search(r'(?i)^error|fatal|timestep too small|doAnalyses:',line)]
        passed=state['returncode']==0 and state['status']=='completed' and len(fps)==8 and len(waves)==4 and not errors and not numerical_errors and 'LS_MISMATCH_END' in log
        row=dict(name=name,seed=seed,enabled=enabled,status='passed' if passed else 'failed',
                 electrical_acceptance='passed' if passed and all(v['logic_status']=='passed' for v in metrics.values()) else 'failed' if passed else 'not run',
                 fingerprints=fps,waves=waves,metrics=metrics,errors=errors,numerical_errors=numerical_errors,
                 wall_s=state['wall_s'],deck_sha256=sha(leaf/'fixture.cir'),log_sha256=sha(leaf/'tool.log'))
        (leaf/'analysis.json').write_text(json.dumps(row,indent=2)+'\n');print(name,row['status'],row['electrical_acceptance'],flush=True)
        return row

    specs=[('repeat_a',56001,1),('repeat_b',56001,1),('changed',56002,1),('disabled_a',56001,0),('disabled_b',56002,0)] if a.mode=='qualify' else [(f'seed{s}',s,1) for s in map(int,a.seeds.split(','))]
    cases=[]
    for name,seed,enabled in specs:
        cases.append(run(name,seed,enabled));(out/'manifest.json').write_text(json.dumps(dict(cases=cases),indent=2)+'\n')
        if cases[-1]['status']!='passed':break
    checks=dict(all_numerical_complete=len(cases)==len(specs) and all(r['status']=='passed' for r in cases),
                original_bindings_unchanged=all(sha(ROOT/p)==h for p,h in binding.items()),
                models_unchanged=all(sha(PDK/p)==h for p,h in models.items()))
    if a.mode=='qualify' and checks['all_numerical_complete']:
        fp=lambda i:cases[i]['fingerprints']['t0_before']
        hashes=lambda i:[cases[i]['waves'][str(j)]['sha256'] for j in range(4)]
        checks.update(same_seed_parameters=fp(0)==fp(1),same_seed_waves=hashes(0)==hashes(1),
                      changed_seed_all8_devices=all(any(fp(0)[f'@{t}[{p}]']!=fp(2)[f'@{t}[{p}]'] for p in params) for t in targets),
                      disabled_seed_parameters=fp(3)==fp(4),disabled_seed_waves=hashes(3)==hashes(4),
                      disabled_nominal=all(fp(3)[f'@{t}[delvto]']==0 and fp(3)[f'@{t}[factuo]']==1 for t in targets),
                      temperature_return_wave_exact=all(hashes(i)[0]==hashes(i)[3] for i in range(5)))
    result=dict(status='passed' if all(checks.values()) else 'failed',checks=checks,source_sha256=sha(source),script_sha256=sha(Path(__file__)),
                samples=len(cases),electrical_failed=sum(r['electrical_acceptance']=='failed' for r in cases),
                full_receiver_power_order='not run',current_limit_allocation='not run',physical_measurement='not applicable')
    (out/('qualification.json' if a.mode=='qualify' else 'assessment.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='passed' else 1)

if __name__=='__main__':main()
