#!/usr/bin/env python3
"""Exploratory electrical charge injection, not a particle or radiation model."""
import argparse
import bisect
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
SIM=HERE.parent
ROOT=SIM.parents[4]
PDK=Path('/foss/pdks/ihp-sg13g2')
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interpolate(rows,time,column):
    times=[r[0] for r in rows]
    j=bisect.bisect_left(times,time)
    if rows[j][0]==time:
        return rows[j][column]
    a,b=rows[j-1:j+1]
    return a[column]+(time-a[0])*(b[column]-a[column])/(b[0]-a[0])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--polarity',type=int,choices=[-1,1],required=True)
    p.add_argument('--phase',type=float,default=250,help='Pulse start ns, between decision clocks')
    p.add_argument('--nodes',default='q,qb')
    p.add_argument('--charge-fc',type=float,default=1000)
    a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert 0<=a.charge_fc<=1000 and a.phase in (220.3,250)
    nodes=a.nodes.split(',');assert nodes and all(n in ('q','qb','n4','n10','n12') for n in nodes)
    src=SIM/'qualification/cmp-cellpex-smoke-b1-20260922-a/cmp.spice'
    expected='2b655dfb3780eb43f55bf2641c93ea58e150c08e4691343e5e5a796ebc32fe2d'
    assert sha(src)==expected
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    out=a.output.resolve();out.mkdir(parents=True)
    shutil.copyfile(src,out/'cmp.spice');shutil.copyfile(SIM/'.spiceinit',out/'.spiceinit')
    shutil.copyfile(Path(__file__),out/'runner.py')
    cards=[line.split() for line in src.read_text().splitlines() if line.startswith('XM')]
    assert len(cards)==30 and src.read_text().count('Cext_')==109
    params=[f'@n.x1.{t[0].lower()}.n{t[5]}[{name}]' for t in cards for name in ('w','l','delvto','factuo')]
    assert len(set(params))==120
    models={str(f.relative_to(PDK)):sha(f) for f in (PDK/'libs.tech/ngspice/models').rglob('*') if f.is_file()}
    contract=dict(source_sha256=expected,script_sha256=sha(Path(__file__)),seed=62001,parameters=params,
                  source_scope='Existing revision1 cell CPEX30MOS/109C. Native per-finger convention inherited; no new AP equivalence or fullmacro claim.',
                  PDK_commit=(PDK/'COMMIT').read_text().strip(),models=models,
                  ngspice=subprocess.check_output(['ngspice','-v'],universal_newlines=True),
                  temperature_C=25,VDD_V=1.2,common_mode_V=.75,differentials_V=[-.01,.01],
                  source_resistance_ohm=1000,source_capacitance_pF=1,output_load_fF=10,clock_Hz=10e6,
                  maxstep_s=20e-12,stop_s=720e-9,wall_limit_s=120,
                  pulse='Trapezoid10ps edges,990ps plateau; area is amplitude times1ns. Positive current injects from ground to node.',
                  phase_ns=a.phase,charge_fC=a.charge_fc,polarity=a.polarity,nodes=nodes,
                  scope='Imposed electrical charge only; no LET, cross section, upset rate, irradiation or radiation-hardness claim. Outside-rail excursions invalidate reliability inference.')
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    results=[]
    for differential in (-.01,.01):
        for node,charge in [('q',0)]+[(node,a.charge_fc) for node in nodes]:
            name=('neg' if differential<0 else 'pos')+'_'+node+'_'+str(int(charge))+'fC'
            leaf=out/name;leaf.mkdir();shutil.copyfile(out/'.spiceinit',leaf/'.spiceinit')
            target=node if node in ('q','qb') else 'x1.'+node
            amplitude=a.polarity*charge*1e-15/1e-9
            start=a.phase*1e-9
            points=[(0,0),(start,0),(start+10e-12,amplitude),(start+1e-9,amplitude),(start+1.01e-9,0),(720e-9,0)]
            deck=f'''* Comparator exploratory electrical charge injection; not LET
.include {out}/cmp.spice
.lib {PDK}/libs.tech/ngspice/models/cornerMOSlv.lib mos_tt_mismatch
.temp 25
.option method=trap reltol=1e-5 abstol=1e-14 vntol=1e-7
Vdd vdd 0 1.2
Vp ip0 0 {.75+differential/2:.17g}
Vn in0 0 {.75-differential/2:.17g}
Rp ip0 inp 1k
Rn in0 inn 1k
Cp inp 0 1p
Cn inn 0 1p
Vclk clk 0 pulse(0 1.2 20n .2n .2n 50n 100n)
X1 inp inn clk q qb vdd 0 g1_cmp
Cq q 0 10f
Cqb qb 0 10f
Iset 0 {target} pwl({' '.join('%.17g %.17g'%v for v in points)})
.save v(q) v(qb) v(inp) v(inn) v(clk) v(x1.n4) v(x1.n10) v(x1.n12) i(vdd) @iset[current]
.control
set num_threads=1
set numdgt=17
set wr_singlescale
set wr_vecnames
setseed 62001
reset
op
echo SET_FP_BEFORE_BEGIN
'''+''.join('print '+k+'\n' for k in params)+'''echo SET_FP_BEFORE_END
tran 20p 720n 0 20p
echo SET_FP_AFTER_BEGIN
'''+''.join('print '+k+'\n' for k in params)+f'''echo SET_FP_AFTER_END
wrdata {leaf}/wave.tsv v(q) v(qb) v(inp) v(inn) v(clk) v(x1.n4) v(x1.n10) v(x1.n12) i(vdd) @iset[current]
echo SET_COMPLETE
quit 0
.endc
.end
'''
            (leaf/'fixture.cir').write_text(deck)
            with (leaf/'tool.log').open('x') as log:
                state=run_bounded(['ngspice','-b','fixture.cir'],log,leaf/'run.json',120,cwd=leaf,env=dict(os.environ,OMP_NUM_THREADS='1'),interval_s=.5)
            log=(leaf/'tool.log').read_text();errors=[];metrics={};fps={}
            try:
                for phase in ('BEFORE','AFTER'):
                    assert log.count('SET_FP_'+phase+'_BEGIN\n')==log.count('SET_FP_'+phase+'_END\n')==1
                    part=log.split('SET_FP_'+phase+'_BEGIN\n')[1].split('SET_FP_'+phase+'_END\n')[0]
                    rows=re.findall(r'(?m)^(@\S+)\s*=\s*(\S+)',part)
                    assert [r[0] for r in rows]==params
                    fps[phase]={k:float(v) for k,v in rows}
                    assert all(map(math.isfinite,fps[phase].values()))
                assert fps['BEFORE']==fps['AFTER']
                wave=leaf/'wave.tsv'
                rows=[list(map(float,line.split())) for line in wave.read_text().splitlines()[1:] if line.strip()]
                assert rows[0][0]==0 and abs(rows[-1][0]-720e-9)<1e-15
                assert all(len(r)==11 and all(map(math.isfinite,r)) for r in rows)
                assert all(b[0]>c[0] for c,b in zip(rows,rows[1:]))
                sampled={str(t):interpolate(rows,t*1e-9,1) for t in (140,240,280,340,440,540,640)}
                expected_high=differential>0
                decision=lambda value: value>=1.08 if expected_high else value<=.12
                # At phase220.3ns,240ns is already post-injection; only140ns is pre-injection.
                pre=(140,240) if a.phase==250 else (140,)
                assert all(decision(sampled[str(t)]) for t in pre), 'Control not in expected pre-injection state'
                delivered=sum((b[0]-c[0])*(c[10]+b[10])/2 for c,b in zip(rows,rows[1:]))
                assert abs(delivered-a.polarity*charge*1e-15)<=max(1e-20,charge*1e-15*1e-5)
                metrics=dict(sampled_q_V=sampled,pre_injection_expected_state='passed',
                             changed_held_decision=not decision(sampled['280']),
                             recovered_next_decision=decision(sampled['340']),
                             recovered_late_decisions=all(decision(sampled[str(t)]) for t in (440,540,640)),
                             min_observed_node_V=min(min(r[i] for i in (1,2,3,4,6,7,8)) for r in rows),
                             max_observed_node_V=max(max(r[i] for i in (1,2,3,4,6,7,8)) for r in rows),
                             delivered_charge_C=delivered,wave_sha256=sha(wave),rows=len(rows))
            except (AssertionError,ValueError,OSError,IndexError) as exc:
                errors.append(type(exc).__name__+': '+str(exc))
            numerical_errors=[line for line in log.splitlines() if re.search(r'(?i)^error|fatal|timestep too small|doAnalyses:|no such vector',line)]
            complete=state['status']=='completed' and state['returncode']==0 and 'SET_COMPLETE' in log and not errors and not numerical_errors
            row=dict(name=name,node=node,differential_V=differential,charge_fC=charge,polarity=a.polarity,
                     status='passed characterization' if complete else 'failed',errors=errors,numerical_errors=numerical_errors,
                     fingerprints=fps,metrics=metrics,wall_s=state['wall_s'],deck_sha256=sha(leaf/'fixture.cir'),log_sha256=sha(leaf/'tool.log'),
                     radiation_acceptance='not applicable',full_chain_recovery='not run')
            (leaf/'analysis.json').write_text(json.dumps(row,indent=2)+'\n');results.append(row)
            (out/'manifest.json').write_text(json.dumps(results,indent=2)+'\n')
            print(name,row['status'],flush=True)
            if not complete:
                raise SystemExit(1)
    assert sha(src)==expected and all(sha(PDK/name)==h for name,h in models.items())
    assert all(r['fingerprints']['BEFORE']==results[0]['fingerprints']['BEFORE'] for r in results)


if __name__=='__main__':
    main()
