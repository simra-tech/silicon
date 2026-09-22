#!/usr/bin/env python3
"""Source-bound extracted mismatch power-order screen; no fault-survival claim."""
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
PDK = Path('/foss/pdks/ihp-sg13g2')
sys.path.insert(0, str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--qualification', type=Path, required=True)
    p.add_argument('--order', choices=['A','D','S'], required=True)
    p.add_argument('--seed', type=int, default=56001)
    p.add_argument('--vdd', type=float, default=1.2)
    p.add_argument('--vdda', type=float, default=3.3)
    a = p.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and not a.output.exists()
    assert (PDK/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    source = HERE.parent.parent/'reports/flat-pex-20260921T150429Z_42162722/ngspice_pex.spice'
    assert sha(source) == '087bdf16283f0aad73d940ef5c5a8d577764622ab243580bb77766d35a9da293'
    q = json.loads(a.qualification.read_text())
    assert q['status']=='passed' and q['source_sha256']==sha(source)
    assert sha(HERE/'run_mismatch.py')==q['script_sha256']
    out = a.output.resolve(); out.mkdir(parents=True)
    original = source.read_text()
    enabled = '\n'.join(line+' mm_ok=1' if line.startswith('XM') else line for line in original.splitlines())+'\n'
    qualified = a.qualification.parent/'source_mm1.spice'
    assert enabled == qualified.read_text()
    (out/'source_mm1.spice').write_text(enabled)
    shutil.copyfile(HERE.parent/'.spiceinit',out/'.spiceinit')
    shutil.copyfile(Path(__file__),out/'runner.py')
    targets = ['n.x1.'+line.split()[0].lower()+'.n'+line.split()[5] for line in original.splitlines() if line.startswith('XM')]
    assert len(set(targets))==8
    model_hashes={str(x.relative_to(PDK)):sha(x) for x in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))}
    early='0 0 0.5u 0 1.5u {v} 9u {v}'
    late='0 0 3u 0 4u {v} 9u {v}'
    pa=(late if a.order=='D' else early).format(v=a.vdda)+f' 12u {a.vdda}'
    pd=(late if a.order=='A' else early).format(v=a.vdd)+' 9.5u 0 12u 0'
    deck=f'''* Extracted LS power-order fixed draw, ideal clamped absent rail
.include {out}/source_mm1.spice
.lib {PDK}/libs.tech/ngspice/models/cornerMOSlv.lib mos_tt_mismatch
.lib {PDK}/libs.tech/ngspice/models/cornerMOShv.lib mos_tt_mismatch
.temp 27
.option method=gear reltol=1e-4 abstol=1e-16 vntol=1e-7 gmin=1e-16 seed={a.seed}
.global sub!
Vsub sub! 0 0
Vdda vdda 0 pwl({pa})
Vdd vdd 0 pwl({pd})
Vin in 0 pwl(0 0 6u 0 6.001u {a.vdd} 7u {a.vdd} 7.001u 0 12u 0)
X1 in out vdd vdda 0 g1_ls_up
Cload out 0 20f
.control
set num_threads=1
set numdgt=17
set wr_singlescale
set wr_vecnames
setseed {a.seed}
reset
'''
    markers=[]
    for index,temp in enumerate((27,125,-40,27)):
        deck+=f'set temp={temp}\nop\n'
        for phase in ('before','after'):
            mark=f't{index}_{phase}';markers.append(mark)
            deck+=f'echo LS_PWR_BEGIN {mark}\n'
            deck+='\n'.join(f'print @{t}[{name}]' for t in targets for name in ('w','l','delvto','factuo'))+'\n'
            deck+=f'echo LS_PWR_END {mark}\n'
            if phase=='before':
                deck+='tran 100p 12u 0 100p\n'
                deck+=f'wrdata {out}/t{index}.tsv v(in) v(out) v(vdd) v(vdda) i(vdd) i(vdda)\n'
    deck+='echo LS_PWR_COMPLETE\nquit 0\n.endc\n.end\n'
    (out/'fixture.cir').write_text(deck)
    contract=dict(order=a.order,seed=a.seed,VDD_V=a.vdd,VDDA_V=a.vdda,temperature_order_C=[27,125,-40,27],
                  load_fF=20,max_step_s=100e-12,stop_s=12e-6,wall_limit_s=180,
                  source_sha256=sha(source),qualified_enabled_source_sha256=sha(qualified),
                  qualification_sha256=sha(a.qualification),script_sha256=sha(Path(__file__)),
                  model_hashes=model_hashes,PDK_commit=(PDK/'COMMIT').read_text().strip(),
                  ngspice=subprocess.check_output(['ngspice','-v'],universal_newlines=True),
                  logic='Settled input-low output <=10% VDDA, input-high >=90% VDDA. Initial and missing-core low checked separately.',
                  current='Signed source current observed; no allocated back-powering/current limit. Ideal clamped absent rail, not floating rail.',
                  limitations='Macro20fF, no actual receiver mismatch or route resistance; not terminal reliability or fault survival.')
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    with (out/'tool.log').open('x') as log:
        state=run_bounded(['ngspice','-b','fixture.cir'],log,out/'run.json',180,cwd=out,env=dict(os.environ,OMP_NUM_THREADS='1'),interval_s=.5)
    log=(out/'tool.log').read_text(); fps={}; waves=[]; errors=[]
    try:
        for mark in markers:
            assert log.count('LS_PWR_BEGIN '+mark+'\n')==log.count('LS_PWR_END '+mark+'\n')==1
            part=log.split('LS_PWR_BEGIN '+mark+'\n')[1].split('LS_PWR_END '+mark+'\n')[0]
            values={k:float(v) for k,v in re.findall(r'(?m)^(@\S+)\s*=\s*([-+\d.eE]+)\s*$',part)}
            assert len(values)==32 and all(map(math.isfinite,values.values()))
            fps[mark]=values
        assert all(v==fps[markers[0]] for v in fps.values())
        for index,temp in enumerate((27,125,-40,27)):
            path=out/f't{index}.tsv'
            rows=[list(map(float,line.split())) for line in path.read_text().splitlines()[1:] if line.strip()]
            assert rows[0][0]==0 and abs(rows[-1][0]-12e-6)<1e-15
            assert all(len(r)==7 and all(map(math.isfinite,r)) for r in rows)
            assert all(b[0]>c[0] for c,b in zip(rows,rows[1:]))
            windows={name:[r for r in rows if start<=r[0]<=stop] for name,start,stop in
                     [('first_rail',1.8e-6,2.8e-6),('both_low',4.5e-6,5.8e-6),('both_high',6.5e-6,6.9e-6),
                      ('after_low',7.5e-6,8.8e-6),('core_absent',10e-6,11.9e-6)]}
            metrics={name:dict(out_min_V=min(r[2] for r in rs),out_max_V=max(r[2] for r in rs),
                                core_injection_peak_A=max(r[5] for r in rs),analog_injection_peak_A=max(r[6] for r in rs),
                                core_draw_peak_A=max(-r[5] for r in rs),analog_draw_peak_A=max(-r[6] for r in rs)) for name,rs in windows.items()}
            checks={name:(m['out_min_V']>=.9*a.vdda if name=='both_high' else m['out_max_V']<=.1*a.vdda) for name,m in metrics.items()}
            waves.append(dict(temperature_C=temp,sha256=sha(path),rows=len(rows),metrics=metrics,checks=checks))
        assert waves[0]['sha256']==waves[3]['sha256']
    except (AssertionError,ValueError,OSError) as exc:
        errors.append(type(exc).__name__+': '+str(exc))
    numerical_errors=[line for line in log.splitlines() if re.search(r'(?i)^error|fatal|timestep too small|doAnalyses:',line)]
    passed=state['status']=='completed' and state['returncode']==0 and len(waves)==4 and not errors and not numerical_errors and 'LS_PWR_COMPLETE' in log
    bindings=sha(source)==contract['source_sha256'] and all(sha(PDK/name)==h for name,h in model_hashes.items())
    result=dict(numerical_status='passed' if passed else 'failed',binding_status='passed' if bindings else 'failed',
                electrical_acceptance=('passed' if all(all(w['checks'].values()) for w in waves) else 'failed') if passed else 'not run',
                backpowering_limit_acceptance='not run',floating_supply='not run',physical_measurement='not applicable',
                fingerprints=fps,waves=waves,errors=errors,numerical_errors=numerical_errors,
                simulation_wall_s=state['wall_s'],deck_sha256=sha(out/'fixture.cir'),log_sha256=sha(out/'tool.log'))
    (out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('fingerprints','waves')},indent=2))
    raise SystemExit(0 if passed and bindings else 1)


if __name__=='__main__':
    main()
