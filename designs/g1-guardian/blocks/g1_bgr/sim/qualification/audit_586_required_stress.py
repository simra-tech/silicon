#!/usr/bin/env python3
"""Independent saved-data accounting of original current-source stress fixtures."""
import argparse
import json
from pathlib import Path
import re
import numpy as np
from run_586_startup_required import HERE,SOURCE_SHA,IMAGE,sha,terminal_map


def audit(folder):
    p=json.loads((folder/'provenance.json').read_text());s=json.loads((folder/'summary.json').read_text())
    q=json.loads((HERE/'runs/bgr_one_draw_20260922_r1/manifest.json').read_text())
    assert p['image_manifest']==IMAGE and p['runtime']==q['runtime']and p['ngspice']==q['ngspice']
    assert p['source_sha256']==sha(folder/'pex_nominal.spice')==SOURCE_SHA
    for name,key in [('runner.py','runner_sha256'),('stress.cir','deck_sha256'),('.spiceinit','spiceinit_sha256')]:assert sha(folder/name)==p[key]
    assert all(sha(Path(f))==h for f,h in p['inputs'].items())
    old=HERE/'runs/bgr_stress3_20260921_01';original=(old/(p['case']['name']+'.cir')).read_text()
    original_m=json.loads((old/'manifest.json').read_text())
    assert p['case']in original_m['cases']
    assert sha(old/(p['case']['name']+'.cir'))==p['case']['deck_sha256']
    assert (folder/'.spiceinit').read_text()==(old/'.spiceinit').read_text().replace('set num_threads=4','set num_threads=1')
    body=(folder/'stress.cir').read_text()
    stripped,n=re.subn(r'echo STRESS2842_BEGIN\n(?:print @[^\n]+\n){2842}echo STRESS2842_END\nwrdata terminals.dat [^\n]+\n','',body)
    assert n==1 and stripped==original and ' uic'not in body and '\nop\n'not in body
    state=json.loads((folder/'run.json').read_text());assert state==s['runtime']
    record=dict(case=p['case']['name'],status=s['status'],summary_sha256=sha(folder/'summary.json'),
                provenance_sha256=sha(folder/'provenance.json'),run_log_sha256=sha(folder/'run.log'))
    if state['status']!='completed' or state['returncode']!=0:return record
    log=(folder/'run.log').read_text()
    fatal=re.findall(r'^.*(?:Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse|\bnan\b).*$',log,re.I|re.M)
    record['original_log_gate']='failed'if fatal else'passed'
    record['original_log_findings']=fatal
    # A completed raw waveform can be audited independently even when the
    # original warning/error gate failed. Do not relabel that attempt passed.
    if fatal and any('The temperature limiting function received NaN.'not in line for line in fatal):return record
    sections=re.findall(r'^STRESS2842_BEGIN\n(.*?)^STRESS2842_END$',log,re.M|re.S);assert len(sections)==1
    params=re.findall(r'^(@[^\s]+)\s*=\s*(\S+)',sections[0],re.M)
    assert len(params)==2842 and [k for k,v in params]==q['parameters']==p['parameter_order']
    assert all(np.isfinite(float(v))for k,v in params)
    if 'parameters_endpoint'in s:assert [list(r)for r in params]==s['parameters_endpoint']
    devices,nodes=terminal_map((folder/'pex_nominal.spice').read_text())
    assert devices==p['terminal_devices']and nodes==p['terminal_nodes']
    header=['time','v(vref)','i(vload)','i(vdd)','v(vbe)','v(dvbe)','v(pbias)','v(pcasc)','v(xbgr.c2)','v(xbgr.vbe3)','v(xbgr.vd1)','v(xbgr.vd2)']
    arrays=[]
    for file,expected in [(p['case']['name']+'.dat',header),('terminals.dat',['time']+['v('+n+')'for n in nodes])]:
        path=folder/file;assert path.read_text().splitlines()[0].split()==expected
        d=np.loadtxt(str(path),skiprows=1,ndmin=2)
        assert len(d)>1 and d.shape[1]==len(expected)and np.isfinite(d).all()
        assert d[0,0]>=0 and np.all(np.diff(d[:,0])>0)and abs(d[-1,0]-40e-6)<1e-12
        arrays.append(d)
    d,t=arrays;assert np.array_equal(d[:,0],t[:,0])
    if 'wave_sha256'in s:
        assert sha(folder/(p['case']['name']+'.dat'))==s['wave_sha256']and sha(folder/'terminals.dat')==s['terminal_wave_sha256']
    index={n:i+1 for i,n in enumerate(nodes)};vce=[]
    for device in devices:
        if not device['instance'].startswith('XQ'):continue
        c,e=device['nodes']['c'],device['nodes']['e']
        vce.append(float(np.abs((t[:,index[c]]if c!='0'else 0)-(t[:,index[e]]if e!='0'else 0)).max()))
    assert len(vce)==301
    vce_status='passed'if max(vce)<=1.6 else'failed';level_status='passed'if .9<d[-1,1]<1.2 else'failed'
    if s['status']=='passed numerical characterization':
        assert s['hbt_vce_status']==vce_status and s['startup_level_status']==level_status
    record.update(full2842_endpoint_status='passed',waveform_status='passed',rows=len(d),
        max_hbt_external_vce_V=max(vce),hbt_vce_status=vce_status,final_level_screen=level_status,
        waveform_sha256=sha(folder/(p['case']['name']+'.dat')),terminal_wave_sha256=sha(folder/'terminals.dat'),
        scope='Saved finite endpoint/screen audit only; original failed log gate remains failed without a warning waiver.',
        vref_end_V=float(d[-1,1]),vref_min_V=float(d[:,1].min()),vref_max_V=float(d[:,1].max()),iptat_end_A=float(d[-1,2]))
    return record


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();rows=[audit(f)for f in a.run]
    assert len({r['case']for r in rows})==len(rows)and {r['case']for r in rows}<={'dip','r4','load'}
    result=dict(status='passed independent evidence audit; individual failures retained',cases=rows,original_stimuli=3,unrun=3-len(rows),
        script_sha256=sha(Path(__file__)),not_run=['Actual downstream loading','Final native RC','Allocated recovery/settling error and full voltage/lifetime qualification'],
        not_applicable=['Statistical yield of mismatch-disabled characterization'])
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
