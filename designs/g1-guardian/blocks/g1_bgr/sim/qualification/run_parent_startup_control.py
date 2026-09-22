#!/usr/bin/env python3
"""One exact100ms source-only parent control; no tolerance/watchdog changes."""
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

HERE=Path(__file__).resolve().parent;PDK=Path('/foss/pdks/ihp-sg13g2')
REFERENCE=HERE/'runs/bgr_loop24q4_hv06_startup2_20260922_r3'
NAME='typ_tt_typ_27_0.1'
PARENT_SHA='53513ab43c62ead3a4c171f5a026b165e2a0bfda2b5b0cb5b104a30aae33a4e2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return [[float(v) for v in line.split()] for line in p.read_text().splitlines()[1:] if line.strip()]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-id',required=True);ap.add_argument('--image-id',required=True);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    assert re.fullmatch('[a-z][a-z0-9_]*',a.run_id)
    out=HERE/'runs'/a.run_id
    source=HERE/'candidates/bgr_loop24_qref4_r253p465/bgr_loop24_qref4_r253p465.spice';assert sha(source)==PARENT_SHA
    if not a.execute:
        old=json.loads((REFERENCE/'manifest.json').read_text());case=next(c for c in old['cases'] if c['name']==NAME)
        assert case['status']=='failed' and case['startup']==[27,.1] and case['vdd_V']==3
        converted=[];changed=[]
        for line in source.read_text().splitlines():
            f=line.split()
            if f and f[0] in ['XM31','XM33']:
                assert 'l=0.5u' in f;line=line.replace('l=0.5u','l=0.6u');changed.append(f[0])
            converted.append(line)
        assert set(changed)=={'XM31','XM33'} and ('\n'.join(converted)+'\n').encode()==(REFERENCE/'pex_nominal.spice').read_bytes()
        assert sha(REFERENCE/(NAME+'.cir'))==case['deck_sha256']
        out.mkdir(exist_ok=False);shutil.copy(__file__,out/Path(__file__).name)
        for name in ['.spiceinit',NAME+'.cir']:shutil.copy(REFERENCE/name,out/name)
        shutil.copy(source,out/'pex_nominal.spice')
        m={k:old[k] for k in ['pdk_commit','model_sha256','osdi_sha256','terminal_nodes','devices']}
        m.update(status='prepared; not run',image_id=a.image_id,runner_sha256=sha(Path(__file__)),source_sha256=PARENT_SHA,
                 reference_manifest_sha256=sha(REFERENCE/'manifest.json'),reference_source_sha256=sha(REFERENCE/'pex_nominal.spice'),
                 deck_sha256=sha(out/(NAME+'.cir')),spiceinit_sha256=sha(out/'.spiceinit'),
                 source_only_change_gate='passed; only originalXM31/XM33 L.6→.5um reverses toparent',
                 fixture=dict(name=NAME,startup=[27,.1],vdd_V=3.0,expected_first_saved_max_s=2e-6,watchdog_seconds=300),
                 scope='Exactfailed100msdeck/init/models/settings/UIC; copiedsource only. No sourceadoption/MC/reliability claim; unsaved[0,tfirst) notbounded.')
        (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({k:v for k,v in m.items() if k not in ['devices','model_sha256','osdi_sha256']}));return
    m=json.loads((out/'manifest.json').read_text());assert m['status']=='prepared; not run'
    assert m['runner_sha256']==sha(Path(__file__))==sha(out/Path(__file__).name)
    assert m['source_sha256']==sha(out/'pex_nominal.spice')==PARENT_SHA
    assert m['deck_sha256']==sha(out/(NAME+'.cir'))==sha(REFERENCE/(NAME+'.cir'))
    assert m['spiceinit_sha256']==sha(out/'.spiceinit')==sha(REFERENCE/'.spiceinit')
    assert m['image_id']==a.image_id and m['pdk_commit']==(PDK/'COMMIT').read_text().strip()
    for key,folder,pattern in [('model_sha256','models','*.lib'),('osdi_sha256','osdi','*.osdi')]:
        assert m[key]=={str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice'/folder).glob(pattern))}
    def save():(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    m.update(status='running',ngspice=subprocess.check_output(['ngspice','--version'],text=True));save();start=time.monotonic();timed=False
    with (out/(NAME+'.log')).open('x') as log,(out/(NAME+'.stderr.log')).open('x') as err:
        try:rc=subprocess.run(['ngspice','-b',NAME+'.cir'],cwd=out,stdout=log,stderr=err,timeout=300).returncode
        except subprocess.TimeoutExpired:rc=None;timed=True
    m.update(status='failed',solver_exit=rc,timed_out=timed,wall_seconds=time.monotonic()-start)
    try:
        data=rows(out/(NAME+'.dat'));term=rows(out/(NAME+'_terminals.dat'))
        logs=(out/(NAME+'.log')).read_text()+'\n'+(out/(NAME+'.stderr.log')).read_text()
        assert len(data)==len(term)>0
        assert all(len(r)==12 and all(map(math.isfinite,r)) for r in data)
        assert all(len(r)==len(m['terminal_nodes'])+1 and all(map(math.isfinite,r)) for r in term)
        assert [r[0] for r in data]==[r[0] for r in term] and all(b[0]>a[0] for a,b in zip(data,data[1:]))
        assert 0<data[0][0]<=2e-6
        m.update(saved_rows=len(data),first_saved_s=data[0][0],last_saved_s=data[-1][0],last_VREF_V=data[-1][1],last_IPTAT_A=data[-1][2],
                 observed_current_peak_A=max(-r[3] for r in data),data_terminal_time_grids='passed exact/strictmonotone',
                 unobserved_initial_interval_s=[0,data[0][0]],temperature_limiter_NaN_present='temperature limiting function received NaN' in logs,
                 solver_failure_lines=[l for l in logs.splitlines() if re.search('Timestep too small|trouble with|simulation.*aborted',l)],
                 waveform_sha256=sha(out/(NAME+'.dat')),terminal_waveform_sha256=sha(out/(NAME+'_terminals.dat')))
        indices={n:i+1 for i,n in enumerate(m['terminal_nodes'])};vce=[]
        for d in m['devices']:
            if not d['instance'].startswith('XQ'):continue
            p,n=d['terminals']['c'],d['terminals']['e']
            vce.extend(abs((r[indices[p]] if p!='0' else 0)-(r[indices[n]] if n!='0' else 0)) for r in term)
        m['observed_HBT_VCE_max_V']=max(vce)
        m['startup_level_status']='passed' if .9<data[-1][1]<1.2 and data[-1][2]>1e-6 else 'failed'
        m['hbt_external_vce_status']='passed' if max(vce)<=1.6 else 'failed'
        assert rc==0 and not timed and abs(data[-1][0]-.3)<1e-9 and not re.search(r'(?im)^Error|Timestep too small|analysis aborted',logs)
        assert m['startup_level_status']==m['hbt_external_vce_status']=='passed'
        m['status']='passed'
    except (AssertionError,OSError,ValueError,IndexError) as exc:m['analysis_error']=repr(exc)
    save();print(json.dumps({k:v for k,v in m.items() if k not in ['devices','model_sha256','osdi_sha256']}))
    if m['status']!='passed':raise SystemExit(1)
if __name__=='__main__':main()
