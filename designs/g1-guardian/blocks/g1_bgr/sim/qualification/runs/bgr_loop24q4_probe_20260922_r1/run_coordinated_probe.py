#!/usr/bin/env python3
"""Bounded25C baseline/candidate OP density and external-terminal diagnostics."""
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
PDK=Path('/foss/pdks/ihp-sg13g2')
NAME='bgr_loop24_qref4_r253p465'
SOURCES=[('baseline',HERE.parent/'postlayout/g1_bgr_pex.spice','72417e072003d2ce28a108c47ef6ac86927ce6c6f89f3a614f360165a31c9d77'),
         ('candidate',HERE/'candidates'/NAME/(NAME+'.spice'),'53513ab43c62ead3a4c171f5a026b165e2a0bfda2b5b0cb5b104a30aae33a4e2')]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-id',required=True)
    ap.add_argument('--image-id',required=True)
    a=ap.parse_args()
    assert re.fullmatch('[a-z][a-z0-9_]*',a.run_id)
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    assert all(sha(p)==digest for _,p,digest in SOURCES)
    out=HERE/'runs'/a.run_id
    out.mkdir(exist_ok=False)
    shutil.copy(__file__,out/Path(__file__).name)
    shutil.copy(HERE/'.spiceinit',out/'.spiceinit')
    manifest={'command':sys.argv,'image_id':a.image_id,'runner_sha256':sha(Path(__file__)),
              'pdk_commit':(PDK/'COMMIT').read_text().strip(),
              'ngspice':subprocess.check_output(['ngspice','--version'],text=True),
              'spiceinit_sha256':sha(HERE/'.spiceinit'),
              'model_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},
              'osdi_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/osdi').glob('*.osdi'))},
              'temperature_C':25,'vdd_V':3.3,'r4_V':0,'IPTAT_fixture_V':1,'VREF_load_F':1e-12,
              'solver':'gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7; original .spiceinit',
              'mismatch':'disabled','cases':[],
              'scope':'Nominal numerical completion separate from density hypothesis and literal terminal diagnostics. No current-density reliability allocation or foundry SOA adoption; existing HV short-length model-scope concern retained. No startup/actual downstream loads/new wiring PEX/physical fit/MC.'}
    def save(): (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    save()
    for variant,source,digest in SOURCES:
        shutil.copy(source,out/(variant+'.spice'))
        pins=dict(zip('vdd vss r4 vref iptat pbias pcasc vbe dvbe'.split(),'vdd 0 r4 vref iptat pbias pcasc vbe dvbe'.split()))
        nodes=set(); devices=[]; hbt=[]
        for line in source.read_text().splitlines():
            f=line.split()
            if not f: continue
            if f[0].startswith('XM'): labels='dgsb';pairs=['gs','gd','gb','ds','db','sb']
            elif f[0].startswith('XQ'): labels='cbes';pairs=['ce','be','bc','cs','bs','es']
            elif f[0].startswith('XR'): labels='pns';pairs=['pn','ps','ns']
            else: continue
            terminals={key:pins.get(value,'xbgr.'+value) for key,value in zip(labels,f[1:])}
            nodes.update(terminals.values())
            devices.append({'instance':f[0],'model':f[1+len(labels)],'terminals':terminals,'pairs':pairs})
            if f[0].startswith('XQ') and f[1:4]!=['vss','vss','vss']:
                assert all(value in f for value in ['we=0.07u','le=0.9u','Nx=1','m=1'])
                hbt.append(f[0].lower())
        nodes=sorted(nodes-{'0'})
        queries=[f'@q.xbgr.{d}.qnpn13g2[{p}]' for d in hbt for p in ['area','ic','ib']]
        deck='* Coordinated candidate25C density and external terminal probe\n'
        deck+=''.join(f'.lib {PDK}/libs.tech/ngspice/models/{lib}.lib {corner}\n' for lib,corner in [('cornerHBT','hbt_typ'),('cornerMOShv','mos_tt'),('cornerRES','res_typ')])
        deck+=f'.include {variant}.spice\n.temp 25\n.option gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7\n.global sub!\nVsub sub! 0 0\nVdd vdd 0 3.3\nVr4 r4 0 0\nXbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr\nVload iptat 0 1\nCload vref 0 1p\n.control\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\nop\n'
        deck+=''.join('print '+q+'\n' for q in queries)
        vectors=['v('+n+')' for n in nodes]+['i(vload)','i(vdd)']
        deck+=f'wrdata {variant}.dat '+' '.join(vectors)+'\nquit\n.endc\n.end\n'
        (out/(variant+'.cir')).write_text(deck)
        start=time.monotonic();timed=False
        with (out/(variant+'.log')).open('x') as log,(out/(variant+'.stderr.log')).open('x') as err:
            try: rc=subprocess.run(['ngspice','-b',variant+'.cir'],cwd=out,stdout=log,stderr=err,timeout=120).returncode
            except subprocess.TimeoutExpired:rc=None;timed=True
        record={'variant':variant,'source_sha256':digest,'deck_sha256':sha(out/(variant+'.cir')),
                'solver_exit':rc,'timed_out':timed,'watchdog_seconds':120,'wall_seconds':time.monotonic()-start,
                'status':'failed','expected_parameter_count':len(queries),'node_order':nodes}
        try:
            logs=(out/(variant+'.log')).read_text()+'\n'+(out/(variant+'.stderr.log')).read_text()
            matches=re.findall(r'(@[^\s]+)\s*=\s*([-+0-9.eE]+)',logs)
            parameters={k:float(v) for k,v in matches}
            rows=[[float(v) for v in line.split()] for line in (out/(variant+'.dat')).read_text().splitlines()[1:] if line.strip()]
            assert rc==0 and len(rows)==1 and len(rows[0])==len(vectors)+1
            assert len(matches)==len(parameters)==len(queries) and set(parameters)==set(queries)
            assert all(math.isfinite(v) for v in parameters.values()) and all(math.isfinite(v) for v in rows[0])
            # IC/.063um² is valid only for the exact original .07x.9um unit
            # with nominal VBIC area factor1; fail closed if that condition fails.
            assert all(parameters[f'@q.xbgr.{d}.qnpn13g2[area]']==1.0 for d in hbt)
            assert not re.search(r'(?im)^Error|no such parameter|not available|analysis aborted|Timestep too small',logs)
            volts=dict(zip(nodes,rows[0][1:]));volts['0']=0
            record.update(status='passed',parameters=parameters,node_voltages_V=volts,
                          hbt_unit_area_um2=0.063,hbt_area_factor_all_one=True,
                          iptat_A=rows[0][-2],supply_current_A=-rows[0][-1],
                          waveform_sha256=sha(out/(variant+'.dat')),
                          hbt_current_density_A_per_um2={d:parameters[f'@q.xbgr.{d}.qnpn13g2[ic]']/0.063 for d in hbt})
            record['external_terminal_voltages']=[{'instance':d['instance'],'model':d['model'],'pair':pair,
                'voltage_V':volts[d['terminals'][pair[0]]]-volts[d['terminals'][pair[1]]]}
                for d in devices for pair in d['pairs']]
        except (AssertionError,OSError,ValueError,KeyError,IndexError) as exc:
            record['analysis_error']=repr(exc)
        manifest['cases'].append(record);save()
        print(json.dumps({k:v for k,v in record.items() if k not in ['parameters','node_voltages_V','hbt_current_density_A_per_um2','external_terminal_voltages']}),flush=True)
        if record['status']!='passed':raise SystemExit(1)
    baseline,candidate=manifest['cases']
    comparisons=[]
    for key,value in candidate['parameters'].items():
        if not key.endswith('[ic]'):continue
        original=re.sub(r'_u\d+(?=\.)','',key)
        ref=baseline['parameters'][original]
        comparisons.append({'candidate_parameter':key,'baseline_parameter':original,'candidate_ic_A':value,'baseline_ic_A':ref,'relative_delta':value/ref-1})
    manifest['unit_current_comparisons']=comparisons
    manifest['maximum_absolute_unit_IC_relative_delta']=max(abs(r['relative_delta']) for r in comparisons)
    manifest['density_hypothesis']='quantified diagnostic; coordinator review required, not current-density reliability approval'
    save()

if __name__=='__main__':main()
