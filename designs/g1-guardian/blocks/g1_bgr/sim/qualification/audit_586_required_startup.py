#!/usr/bin/env python3
"""Audit saved startup evidence, preserving failed originals and recovery scope."""
import argparse
import json
from pathlib import Path
import re
import numpy as np
from run_586_startup_required import HERE,SOURCE_SHA,IMAGE,sha,instrument,terminal_map,validate_wave


def audit_new(run):
    s=json.loads((run/'summary.json').read_text());p=json.loads((run/'provenance.json').read_text())
    state=json.loads((run/'run.json').read_text())
    assert s['runtime']==state and sha(run/'runner.py')==p['runner_sha256']
    assert sha(run/'pex_nominal.spice')==p['source_sha256']==SOURCE_SHA
    assert sha(run/'startup.cir')==p['deck_sha256']and sha(run/'.spiceinit')==p['spiceinit_sha256']
    assert all(sha(Path(f))==h for f,h in p['inputs'].items())
    q=json.loads((HERE/'runs/bgr_one_draw_20260922_r1/manifest.json').read_text())
    assert p['runtime']==q['runtime']and p['ngspice']==q['ngspice']and p['image_manifest']==IMAGE
    old=HERE/'runs/bgr_startup6_20260921_01'
    original=(old/(p['case']['name']+'.cir')).read_text()
    devices,nodes=terminal_map((run/'pex_nominal.spice').read_text())
    assert nodes==p['terminal_nodes']and devices==p['terminal_devices']and p['instrumented']
    assert (run/'startup.cir').read_text()==instrument(original,p['parameter_order'],nodes)
    assert (run/'.spiceinit').read_text()==(old/'.spiceinit').read_text().replace('set num_threads=4','set num_threads=1')
    r=dict(case=p['case']['name'],original_case=p['case']['startup'],status='failed original fixture',
           receipts_sha256={f:sha(run/f)for f in ('summary.json','provenance.json','run.json','run.log','runner.py','startup.cir','.spiceinit')},
           pretransient_parameters='not run: no OP inserted before original UIC')
    if s['status']!='passed numerical startup':
        r.update(reason=s.get('analysis_error'),runtime=state);return r
    assert state['status']=='completed'and state['returncode']==0
    log=(run/'run.log').read_text()
    assert not re.search(r'Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|\bnan\b',log,re.I)
    wave=run/(p['case']['name']+'.dat');assert sha(wave)==s['waveform_sha256']
    data=np.loadtxt(str(wave),skiprows=1,ndmin=2)
    header=['time','v(vref)','i(vload)','i(vdd)','v(vbe)','v(dvbe)','v(pbias)','v(pcasc)','v(xbgr.c2)','v(xbgr.vbe3)','v(xbgr.vd1)','v(xbgr.vd2)']
    endpoint=3*p['case']['startup'][1]
    validate_wave(data,wave.read_text().splitlines()[0].split(),header,endpoint)
    terminal=np.loadtxt(str(run/'terminals.dat'),skiprows=1,ndmin=2)
    validate_wave(terminal,(run/'terminals.dat').read_text().splitlines()[0].split(),['time']+['v('+n+')'for n in nodes],endpoint)
    assert np.array_equal(terminal[:,0],data[:,0])
    section,=re.findall(r'^STARTUP2842_BEGIN\n(.*?)^STARTUP2842_END$',log,re.M|re.S)
    parameters=re.findall(r'^(@[^\s]+)\s*=\s*(\S+)',section,re.M)
    assert [k for k,v in parameters]==p['parameter_order']and len(parameters)==2842
    assert all(np.isfinite(float(v))for k,v in parameters)
    assert [list(row)for row in parameters]==s['parameters_endpoint']
    index={n:i+1 for i,n in enumerate(nodes)}
    vce=[]
    for d in devices:
        if not d['instance'].startswith('XQ'):continue
        c,e=d['nodes']['c'],d['nodes']['e']
        delta=(terminal[:,index[c]]if c!='0'else 0)-(terminal[:,index[e]]if e!='0'else 0)
        vce.append(float(np.abs(delta).max()))
    assert len(vce)==301
    level=.9<data[-1,1]<1.2 and data[-1,2]>1e-6
    r.update(status='passed original fixture screens'if level and max(vce)<=1.6 else'failed original electrical screen',
        numerical_status='passed',full2842_endpoint_status='passed',wave_sha256=sha(wave),terminal_wave_sha256=sha(run/'terminals.dat'),
        startup_level_status='passed'if level else'failed',hbt_vce_status='passed'if max(vce)<=1.6 else'failed',
        max_hbt_external_vce_V=max(vce),vref_end_V=float(data[-1,1]),iptat_end_A=float(data[-1,2]),
        unsaved_initial_interval_s=[0,float(data[0,0])],rows=len(data))
    if p['case']['startup']==[27,.001]:assert s['instrumentation_parity_status']=='passed'and s['instrumentation_original_wave_bytes_exact']
    return r


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    rows=[audit_new(run)for run in a.run]
    assert len({r['case']for r in rows})==len(rows)
    original=HERE/'runs/bgr_loop24q4_hv06_startup2_20260922_r3'
    om=json.loads((original/'manifest.json').read_text());old,=[r for r in om['cases']if r['startup']==[27,.1]]
    assert om['candidate_sha256']==SOURCE_SHA and old['status']=='failed'
    recovered=HERE/'runs/bgr_hv06_startup100ms_maxstep20us_20260922_r1'
    rm=json.loads((recovered/'manifest.json').read_text())
    assert rm['status']=='passed scoped numerical/level/HBT screen'and rm['source_sha256']==SOURCE_SHA
    assert rm['reference_manifest_sha256']==sha(original/'manifest.json')and rm['maxstep_s']==20e-6
    assert sha(recovered/'typ_tt_typ_27_0.1.cir')==rm['deck_sha256']and sha(recovered/'pex_nominal.spice')==SOURCE_SHA
    assert rm['solver_status']=='completed'and rm['solver_returncode']==0 and rm['last_saved_time_s']==.3 and not rm['numerical_errors']
    result=dict(status='passed independent saved-evidence audit; original100ms failure retained',new_cases=rows,
        original_nominal100ms=dict(status='failed',manifest_sha256=sha(original/'manifest.json')),
        distinct_nominal100ms_recovery=dict(status='passed scoped numerical/level/HBT screen',manifest_sha256=sha(recovered/'manifest.json'),maxstep_s=20e-6,
            full2842_endpoint='not run in this historical diagnostic',not_a_replacement=True),
        original_stimulus_count=6,original_cases_with_new_audit=len(rows),original_unrun_count=5-len(rows),
        not_run=['Final physical RC/actual downstream/EN startup contract','Full model/lifetime acceptance'],
        not_applicable=['Statistical seed qualification: deterministic mismatch-disabled fixture'],
        script_sha256=sha(Path(__file__)))
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
