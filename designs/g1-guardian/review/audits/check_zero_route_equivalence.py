#!/usr/bin/env python3
"""Prospectively bounded tight-solver equivalence, distinct from failed exact-parity gate."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
ROOT=Path(__file__).resolve().parents[4]
SENSE=ROOT/'designs/g1-guardian/blocks/g1_sense/sim';BASE=SENSE/'qualification/corners-20260921-a'
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();assert len(os.sched_getaffinity(0))==1
contract=json.loads(a.contract.read_text());a.output.mkdir(exist_ok=False);out=a.output.resolve()
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
modelroot=Path('/foss/pdks/ihp-sg13g2/libs.tech/ngspice/models')
def model_hashes():return {str(path.relative_to(modelroot)):sha(path) for path in sorted(modelroot.rglob('*')) if path.is_file()}
models=model_hashes();source=BASE/'sense_substrate_tied.spice';source_sha=sha(source)
shutil.copyfile(Path(__file__),out/Path(__file__).name);shutil.copyfile(a.contract,out/'contract.json')
(out/'provenance.json').write_text(json.dumps({'contract_sha256':sha(a.contract),'source_sha256':source_sha,'PDK_models':models,'PDK_commit':Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip()},indent=2)+'\n')
vectors=['v(isense)','v(vped)','v(vref_buf)','v(xdut.vp)','v(xdut.vn)','v(xdut.vped_ref)','i(vdd)']
baseline={row['name']:row for row in json.loads((BASE/'summary.json').read_text())}
results=[]
for name in contract['corners']:
    runs={}
    for kind in ('source','zero_R_inserted'):
        leaf=out/name/kind;leaf.mkdir(parents=True);shutil.copyfile(SENSE/'.spiceinit',leaf/'.spiceinit')
        deck=(BASE/(name+'.cir')).read_text().replace('.include qualification/corners-20260921-a/sense_substrate_tied.spice','.include '+str(source))
        deck=deck.replace('.option gmin=1e-13','.option gmin=1e-13\n.option '+ ' '.join(f'{key}={value:.12g}' for key,value in contract['solver'].items()))
        deck=deck.replace('set numdgt=15','set numdgt=17')
        if kind=='zero_R_inserted':
            assert deck.count('XDUT shp cm vref')==1
            deck=deck.replace('XDUT shp cm vref','Vrp shp corep 0\nVrn cm coren 0\nXDUT corep coren vref')
        def row_output(match):return 'echo PRECISE_BEGIN '+match[1]+'\n'+'\n'.join('print '+vector for vector in vectors)+'\necho PRECISE_END'
        deck,count=re.subn(r'^echo ROW (\S+) .*$',row_output,deck,flags=re.M);assert count==9
        (leaf/'fixture.cir').write_text(deck)
        with (leaf/'tool.log').open('x') as stream:
            state=run_bounded(['ngspice','-b','fixture.cir'],stream,leaf/'run.json',contract['timeout_s_per_leaf'],cwd=leaf,
                env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),metadata={'deck_sha256':sha(leaf/'fixture.cir'),'source_sha256':source_sha,'contract_sha256':sha(a.contract)},interval_s=1)
        log=(leaf/'tool.log').read_text();rows={};precision_ok=True
        for key,block in re.findall(r'^PRECISE_BEGIN (\S+)\n(.*?)^PRECISE_END$',log,re.M|re.S):
            assert key not in rows
            tokens=[]
            for vector in vectors:
                matches=re.findall(r'^'+re.escape(vector)+r'\s*=\s*([-+\d.eE]+)\s*$',block,re.M)
                assert len(matches)==1,(name,kind,vector,block)
                token=matches[0];tokens.append(float(token))
                mantissa=token.lower().split('e')[0].lstrip('+-').replace('.','').lstrip('0')
                precision_ok &= len(mantissa)>=17 or float(token)==0
            rows[key]=tokens
        errors=[line for line in log.splitlines() if re.search(r'(?i)(^Error|fatal|timestep too small|doAnalyses:)',line)]
        complete=state['status']=='completed' and state['returncode']==0 and not errors and precision_ok and set(rows)==set(baseline[name]['rows']) and all(all(map(math.isfinite,row)) for row in rows.values()) and 'QUALIFICATION_END' in log
        runs[kind]={'status':'passed' if complete else 'failed','rows':rows,'errors':errors,'precision_ok':precision_ok,'deck_sha256':sha(leaf/'fixture.cir')}
        print(name,kind,runs[kind]['status'],flush=True)
        if not complete:break
    result={'name':name,'runs':runs,'status':'failed'}
    if len(runs)==2 and all(item['status']=='passed' for item in runs.values()):
        left=runs['source']['rows'];right=runs['zero_R_inserted']['rows']
        voltage=max(abs(left[key][column]-right[key][column]) for key in left for column in range(6))
        ratios=[abs(left[key][6]-right[key][6])/max(contract['current_abs_floor_A'],contract['current_relative_limit']*abs(left[key][6])) for key in left]
        gains=[]
        for cm in (-.1,0,.3):
            gain=lambda rows:(rows[f't0_c{cm}_s0.05'][0]-rows[f't0_c{cm}_s0'][0])/.05
            gains.append(abs(gain(left)-gain(right)))
        result.update(voltage_max_abs_delta_V=voltage,current_max_limit_ratio=max(ratios),gain_max_abs_delta_V_per_V=max(gains))
        result['status']='passed' if voltage<=contract['voltage_abs_limit_V'] and max(ratios)<=1 and max(gains)<contract['gain_abs_delta_limit_V_per_V'] else 'failed'
    results.append(result)
    unchanged=sha(source)==source_sha and model_hashes()==models
    summary={'status':'passed' if len(results)==5 and all(row['status']=='passed' for row in results) and unchanged else ('running' if len(results)<5 and result['status']=='passed' and unchanged else 'failed'),
        'model_and_source_hashes_unchanged':unchanged,'contract_sha256':sha(a.contract),'results':results,'original_exact_PVT_status':'failed and retained'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    if result['status']!='passed' or not unchanged:raise RuntimeError('Prospective equivalence gate failed; no expansion')
