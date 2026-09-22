#!/usr/bin/env python3
"""Bounded standalone BGR bias charge pilot with explicit zero-current control."""
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

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
BGR=ROOT/'designs/g1-guardian/blocks/g1_bgr/sim/qualification'
PDK=Path('/foss/pdks/ihp-sg13g2')
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--charge-fc',type=float,choices=[0,100,1000],required=True)
    p.add_argument('--polarity',type=int,choices=[-1,1],default=1)
    p.add_argument('--node',choices=['pbias','pcasc','vref'],default='pbias')
    p.add_argument('--maxstep-ns',type=float,choices=[1,2],default=2)
    a=p.parse_args();assert len(os.sched_getaffinity(0))==1 and not a.output.exists()
    source=BGR/'candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
    assert sha(source)=='586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    old=BGR/'runs/bgr_matched_load_20260922_r1/candidate'
    assert (source.read_bytes()==(old/'pex_nominal.spice').read_bytes())
    qualified=json.loads((BGR/'runs/bgr_one_draw_20260922_r1/manifest.json').read_text())
    assert qualified['status']=='passed harness qualification' and qualified['source_sha256']==sha(source)
    params=qualified['parameters'];assert len(params)==2842
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    out=a.output.resolve();out.mkdir(parents=True)
    shutil.copyfile(source,out/'source.spice');shutil.copyfile(old/'.spiceinit',out/'.spiceinit')
    shutil.copyfile(Path(__file__),out/'runner.py')
    amplitude=a.polarity*a.charge_fc*1e-15/1e-9
    points=[(0,0),(20e-6,0),(20e-6+10e-12,amplitude),(20e-6+1e-9,amplitude),(20e-6+1.01e-9,0),(40e-6,0)]
    models={str(p.relative_to(PDK)):sha(p) for p in (PDK/'libs.tech/ngspice/models').rglob('*') if p.is_file()}
    contract=dict(source_sha256=sha(source),script_sha256=sha(Path(__file__)),baseline_load_deck_sha256=sha(old/'load.cir'),
                  mismatch='disabled: same nominal libraries/source as completed matched-load control',seed=42001,
                  parameter_count=2842,models=models,PDK_commit=(PDK/'COMMIT').read_text().strip(),
                  ngspice=subprocess.check_output(['ngspice','-v'],universal_newlines=True),
                  node=a.node,charge_fC=a.charge_fc,polarity=a.polarity,maxstep_ns=a.maxstep_ns,
                  pulse_start_s=20e-6,pulse_edges_s=10e-12,pulse_plateau_s=990e-12,
                  duration_s=40e-6,wall_limit_s=300,temperature_C=27,VDD_V=3.3,
                  downstream='IPTAT held at1V by measurement source; VREF1pF, no actual downstream SENSE/TRIP or pad.',
                  modifications='Remove matched-load100nA/15us VREF step, insert declared zero/charge bias-current pulse. Same source and solver tolerances; explicit frozen-parameter observations and current saving added.',
                  diagnostic_return_limits='Prior load diagnostic: VREF1mV, IPTAT0.1% from pre-pulse mean; not an allocated transient safety/radiation criterion.',
                  scope='Electrical imposed charge only, not collected-charge/LET/radiation rate or fault survival. New physical candidate CPEX not used.')
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    nodes='v(vref) i(vload) i(vdd) v(vbe) v(dvbe) v(pbias) v(pcasc) v(xbgr.c2) v(xbgr.vbe3) v(xbgr.vd1) v(xbgr.vd2) @iset[current]'
    deck=f'''* Standalone reference electrical charge pulse; not radiation qualification
.lib {PDK}/libs.tech/ngspice/models/cornerHBT.lib hbt_typ
.lib {PDK}/libs.tech/ngspice/models/cornerMOShv.lib mos_tt
.lib {PDK}/libs.tech/ngspice/models/cornerRES.lib res_typ
.include source.spice
.option seed=42001 gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7
.global sub!
Vsub sub! 0 0
Vdd vdd 0 3.3
Vr4 r4 0 0
Xbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr
Vload iptat 0 1
Cload vref 0 1p
Iset 0 {a.node} pwl({' '.join('%.17g %.17g'%v for v in points)})
.save {nodes}
.control
set num_threads=1
set numdgt=17
set wr_singlescale
set wr_vecnames
option temp=27
setseed 42001
reset
op
echo REF_FP_BEFORE_BEGIN
'''+''.join('print '+k+'\n' for k in params)+f'''echo REF_FP_BEFORE_END
tran 2n 40u 0 {a.maxstep_ns}n
echo REF_FP_AFTER_BEGIN
'''+''.join('print '+k+'\n' for k in params)+f'''echo REF_FP_AFTER_END
wrdata {out}/wave.tsv {nodes}
echo REF_SET_COMPLETE
quit 0
.endc
.end
'''
    (out/'fixture.cir').write_text(deck)
    with (out/'tool.log').open('x') as log:
        state=run_bounded(['ngspice','-b','fixture.cir'],log,out/'run.json',300,cwd=out,env=dict(os.environ,OMP_NUM_THREADS='1'),interval_s=1)
    log=(out/'tool.log').read_text();errors=[];fps={};metrics={}
    try:
        for phase in ('BEFORE','AFTER'):
            assert log.count('REF_FP_'+phase+'_BEGIN\n')==log.count('REF_FP_'+phase+'_END\n')==1
            part=log.split('REF_FP_'+phase+'_BEGIN\n')[1].split('REF_FP_'+phase+'_END\n')[0]
            values=re.findall(r'(?m)^(@\S+)\s*=\s*(\S+)',part);assert [r[0] for r in values]==params
            fps[phase]={k:float(v) for k,v in values};assert all(map(math.isfinite,fps[phase].values()))
        assert fps['BEFORE']==fps['AFTER']
        rows=[list(map(float,line.split())) for line in (out/'wave.tsv').read_text().splitlines()[1:] if line.strip()]
        assert rows[0][0]==0 and abs(rows[-1][0]-40e-6)<1e-15
        assert all(len(r)==13 and all(map(math.isfinite,r)) for r in rows)
        assert all(b[0]>c[0] for c,b in zip(rows,rows[1:]))
        before=[r for r in rows if 15e-6<=r[0]<=19e-6];returned=[r for r in rows if r[0]>=35e-6]
        pre=[sum(r[i] for r in before)/len(before) for i in (1,2)]
        residual=[max(abs(r[i]-pre[i-1]) for r in returned) for i in (1,2)]
        delivered=sum((b[0]-c[0])*(c[12]+b[12])/2 for c,b in zip(rows,rows[1:]))
        assert abs(delivered-a.polarity*a.charge_fc*1e-15)<=max(1e-20,a.charge_fc*1e-20)
        metrics=dict(rows=len(rows),wave_sha256=sha(out/'wave.tsv'),delivered_charge_C=delivered,pre_VREF_V_IPTAT_A=pre,
                     return_error_VREF_V_IPTAT_A=residual,
                     diagnostic_return_passed=residual[0]<=.001 and residual[1]/abs(pre[1])<=.001,
                     VREF_min_V=min(r[1] for r in rows),VREF_max_V=max(r[1] for r in rows),
                     IPTAT_min_A=min(r[2] for r in rows),IPTAT_max_A=max(r[2] for r in rows),
                     observed_node_min_V=min(min(r[i] for i in (1,4,5,6,7,8,9,10,11)) for r in rows),
                     observed_node_max_V=max(max(r[i] for i in (1,4,5,6,7,8,9,10,11)) for r in rows))
    except (AssertionError,ValueError,OSError,IndexError) as exc:
        errors.append(type(exc).__name__+': '+str(exc))
    numerical_errors=[line for line in log.splitlines() if re.search(r'(?i)^error|fatal|timestep too small|doAnalyses:|no such vector',line)]
    complete=state['status']=='completed' and state['returncode']==0 and not errors and not numerical_errors and 'REF_SET_COMPLETE' in log
    unchanged=sha(source)==contract['source_sha256'] and all(sha(PDK/name)==h for name,h in models.items())
    result=dict(status='passed characterization' if complete and unchanged else 'failed',errors=errors,numerical_errors=numerical_errors,
                inputs_unchanged=unchanged,fingerprints=fps,metrics=metrics,wall_s=state['wall_s'],deck_sha256=sha(out/'fixture.cir'),log_sha256=sha(out/'tool.log'),
                radiation_acceptance='not applicable',full_chain_recovery='not run',model_reliability='not run')
    (out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='fingerprints'},indent=2))
    raise SystemExit(0 if complete and unchanged else 1)


if __name__=='__main__':
    main()
