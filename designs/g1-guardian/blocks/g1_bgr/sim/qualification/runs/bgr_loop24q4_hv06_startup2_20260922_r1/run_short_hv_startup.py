#!/usr/bin/env python3
"""Prepare/review, then explicitly execute only two frozen27C/3V startup inputs."""
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
NAME='bgr_loop24_qref4_r253p465_hv06'
SOURCE_SHA='586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
CASES={'typ_tt_typ_27_0.001':'8ee84b90ca3c4a8059ebb1f0f2ab75d1c9768fd8928f1079d29e404e45d67451',
       'typ_tt_typ_27_0.1':'c77b9cab13962c63e6ab2702b5a6913055e5bdc0374d213b471ef627f9799318'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_rows(p):return [[float(v) for v in line.split()] for line in p.read_text().splitlines()[1:] if line.strip()]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-id',required=True)
    ap.add_argument('--image-id',required=True)
    ap.add_argument('--execute',action='store_true',help='execute already prepared and reviewed decks; default only prepares')
    a=ap.parse_args()
    assert re.fullmatch('[a-z][a-z0-9_]*',a.run_id)
    out=HERE/'runs'/a.run_id
    source=HERE/'candidates'/NAME/(NAME+'.spice')
    assert sha(source)==SOURCE_SHA
    if not a.execute:
        olddir=HERE/'runs/bgr_startup6_20260921_01'
        old=json.loads((olddir/'manifest.json').read_text())
        out.mkdir(exist_ok=False)
        shutil.copy(__file__,out/Path(__file__).name)
        shutil.copy(olddir/'.spiceinit',out/'.spiceinit')
        shutil.copy(source,out/'pex_nominal.spice')
        pins={n:n for n in ['vdd','r4','vref','iptat','pbias','pcasc','vbe','dvbe']};pins['vss']='0'
        devices=[];all_nodes=set()
        for line in source.read_text().splitlines():
            f=line.split()
            if not f or not f[0].startswith(('XM','XQ')):continue
            labels='dgsb' if f[0].startswith('XM') else 'cbes'
            terminals={k:pins.get(v,'xbgr.'+v) for k,v in zip(labels,f[1:5])}
            all_nodes.update(terminals.values())
            devices.append({'instance':f[0],'model':f[5],'terminals':terminals,
                            'pairs':['gs','gd','gb','ds','db','sb'] if labels=='dgsb' else ['ce','be','bc']})
        nodes=sorted(all_nodes-{'0'})
        manifest={'status':'prepared; not run','command_prepare':sys.argv,'runner_sha256':sha(Path(__file__)),
                  'candidate_sha256':SOURCE_SHA,'image_id':a.image_id,'pdk_commit':old['pdk_commit'],
                  'model_sha256':old['model_sha256'],'osdi_sha256':old['osdi_sha256'],
                  'spiceinit_sha256':sha(out/'.spiceinit'),'original_manifest_sha256':sha(olddir/'manifest.json'),
                  'terminal_nodes':nodes,'devices':devices,'cases':[],
                  'scope':'Exactly original27C3V1ms/100ms startup inputs/settings, changed copiedsource only plus1thread/terminalexports. Not3.6V/125C reliability, newwirePEX, physicalfit, mismatch oradoption.'}
        for name,digest in CASES.items():
            original=next(c for c in old['cases'] if c['name']==name)
            assert original['status']=='passed' and original['vdd']==3.0 and original['startup'][0]==27
            path=olddir/(name+'.cir');assert sha(path)==digest==original['deck_sha256']
            deck=path.read_text();assert deck.count('.control\n')==deck.count('quit')==1
            export='wrdata '+name+'_terminals.dat '+' '.join('v('+n+')' for n in nodes)+'\n'
            prepared=deck.replace('.control\n','.control\nset num_threads=1\n').replace('quit',export+'quit')
            assert prepared.replace('.control\nset num_threads=1\n','.control\n').replace(export,'')==deck
            (out/(name+'.cir')).write_text(prepared)
            manifest['cases'].append({'name':name,'status':'not run','original_deck_sha256':digest,
                'deck_sha256':sha(out/(name+'.cir')),'non_export_input_byte_reconstruction':'passed',
                'startup':original['startup'],'vdd_V':3.0,'watchdog_seconds':300})
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps({k:v for k,v in manifest.items() if k not in ['devices','model_sha256','osdi_sha256']}));return
    manifest=json.loads((out/'manifest.json').read_text())
    assert manifest['status']=='prepared; not run'
    assert manifest['candidate_sha256']==sha(out/'pex_nominal.spice')==SOURCE_SHA
    assert manifest['runner_sha256']==sha(Path(__file__))==sha(out/Path(__file__).name)
    assert manifest['image_id']==a.image_id
    assert manifest['pdk_commit']==(PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    for key,folder,pattern in [('model_sha256','models','*.lib'),('osdi_sha256','osdi','*.osdi')]:
        assert manifest[key]=={str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice'/folder).glob(pattern))}
    assert manifest['spiceinit_sha256']==sha(out/'.spiceinit')
    assert len(manifest['cases'])==2 and all(c['status']=='not run' for c in manifest['cases'])
    manifest.update(status='running',command_execute=sys.argv,ngspice=subprocess.check_output(['ngspice','--version'],text=True))
    def save():(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    save();nodes=manifest['terminal_nodes'];indices={n:i+1 for i,n in enumerate(nodes)}
    for record in manifest['cases']:
        name=record['name'];assert sha(out/(name+'.cir'))==record['deck_sha256']
        record['status']='running';save();start=time.monotonic();timed=False
        with (out/(name+'.log')).open('x') as log,(out/(name+'.stderr.log')).open('x') as err:
            try:rc=subprocess.run(['ngspice','-b',name+'.cir'],cwd=out,stdout=log,stderr=err,timeout=300).returncode
            except subprocess.TimeoutExpired:rc=None;timed=True
        record.update(status='failed',solver_exit=rc,timed_out=timed,wall_seconds=time.monotonic()-start)
        try:
            data=read_rows(out/(name+'.dat'));term=read_rows(out/(name+'_terminals.dat'))
            logs=(out/(name+'.log')).read_text()+'\n'+(out/(name+'.stderr.log')).read_text()
            assert rc==0 and not timed and len(data)==len(term)>0
            assert all(len(r)==12 and all(map(math.isfinite,r)) for r in data)
            assert all(len(r)==len(nodes)+1 and all(map(math.isfinite,r)) for r in term)
            assert abs(data[-1][0]-3*record['startup'][1])<1e-9
            assert not re.search(r'(?im)^Error|Timestep too small|analysis aborted',logs)
            extrema=[]
            for d in manifest['devices']:
                for pair in d['pairs']:
                    p,n=[d['terminals'][x] for x in pair]
                    values=[(r[indices[p]] if p!='0' else 0)-(r[indices[n]] if n!='0' else 0) for r in term]
                    extrema.append({'instance':d['instance'],'model':d['model'],'pair':pair,
                                    'minimum_V':min(values),'maximum_V':max(values),'maximum_absolute_V':max(map(abs,values))})
            record.update(status='passed',saved_rows=len(data),last_saved_time_s=data[-1][0],
                vref_end_V=data[-1][1],iptat_end_A=data[-1][2],current_peak_A=max(-r[3] for r in data),
                startup_level_status='passed' if .9<data[-1][1]<1.2 and data[-1][2]>1e-6 else 'failed',
                hbt_external_vce_status='passed' if all(r['maximum_absolute_V']<=1.6 for r in extrema if r['pair']=='ce') else 'failed',
                external_terminal_extrema=extrema,waveform_sha256=sha(out/(name+'.dat')),
                terminal_waveform_sha256=sha(out/(name+'_terminals.dat')),
                warning_line_count=sum('warning' in line.lower() for line in logs.splitlines()),
                temperature_limiter_NaN_present='temperature limiting function received NaN' in logs)
        except (AssertionError,OSError,ValueError,IndexError) as exc:record['analysis_error']=repr(exc)
        save();print(json.dumps({k:v for k,v in record.items() if k!='external_terminal_extrema'}),flush=True)
        if record['status']!='passed':manifest['status']='failed';save();raise SystemExit(1)
    manifest['status']='completed';save()

if __name__=='__main__':main()
