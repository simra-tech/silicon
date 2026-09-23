#!/usr/bin/env python3
"""Current BGR source with six historical startup stimuli, no new PEX claim."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
sys.path.insert(0,str(HERE.parents[2]/'g1_trip/sim'))
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory

SOURCE_SHA='586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
IMAGE='sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def terminal_map(source):
    pins={n:n for n in ('vdd','r4','vref','iptat','pbias','pcasc','vbe','dvbe')};pins['vss']='0'
    devices=[]
    for line in source.splitlines():
        f=line.split()
        if not f or not f[0].startswith(('XM','XQ')):continue
        nodes={k:pins.get(n,'xbgr.'+n)for k,n in zip('dgsb'if f[0].startswith('XM')else'cbes',f[1:5])}
        assert len(nodes)==4
        devices.append(dict(instance=f[0],model=f[5],nodes=nodes))
    assert len(devices)==637 and len({d['instance']for d in devices})==637
    return devices,sorted({n for d in devices for n in d['nodes'].values()}-{'0'})


def instrument(deck,parameters,nodes):
    assert len(parameters)==len(set(parameters))==2842
    assert deck.count('quit\n')==1 and deck.count('tran ')==1 and ' uic\n' in deck
    addition=('echo STARTUP2842_BEGIN\n'+''.join('print '+p+'\n'for p in parameters)+
              'echo STARTUP2842_END\nwrdata terminals.dat '+' '.join('v('+n+')'for n in nodes)+'\n')
    result=deck.replace('quit\n',addition+'quit\n')
    assert result.replace(addition,'')==deck
    return result


def validate_wave(data,header,expected_header,endpoint):
    assert header==expected_header
    assert data.ndim==2 and data.shape[1]==len(header)and len(data)>1
    assert np.isfinite(data).all()and np.all(np.diff(data[:,0])>0)
    assert 0<data[0,0] and abs(data[-1,0]-endpoint)<1e-9


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',type=int,choices=(0,2,3,4,5),required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--image-id',required=True)
    p.add_argument('--instrumented',action='store_true')
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    old=HERE/'runs/bgr_startup6_20260921_01'
    reference=HERE/'runs/bgr_one_draw_20260922_r1'
    q=json.loads((reference/'manifest.json').read_text());source=reference/'disabled/pex_nominal.spice'
    m=json.loads((old/'manifest.json').read_text());case=m['cases'][a.case]
    assert len(m['cases'])==6 and case['status']=='passed' and case['vdd']==3.0
    assert sha(source)==q['source_sha256']==SOURCE_SHA and q['status']=='passed harness qualification'
    assert a.image_id==IMAGE
    pd=Path('/foss/pdks/ihp-sg13g2')
    assert (pd/'COMMIT').read_text().strip()==q['runtime']['pdk_commit']
    for key,folder,pattern in [('model_sha256','models','*.lib'),('osdi_sha256','osdi','*.osdi')]:
        assert q['runtime'][key]=={str(f.relative_to(pd)):sha(f)for f in sorted((pd/'libs.tech/ngspice'/folder).glob(pattern))}
    assert subprocess.check_output(['ngspice','--version'],universal_newlines=True)==q['ngspice']
    original=old/(case['name']+'.cir');assert sha(original)==case['deck_sha256']
    deck=original.read_text();devices,nodes=terminal_map(source.read_text())
    if a.instrumented:deck=instrument(deck,q['parameters'],nodes)
    init=(old/'.spiceinit').read_text();assert init.count('set num_threads=4')==1
    init=init.replace('set num_threads=4','set num_threads=1')
    a.output.mkdir(parents=True)
    shutil.copyfile(str(source),str(a.output/'pex_nominal.spice'))
    shutil.copyfile(str(Path(__file__)),str(a.output/'runner.py'))
    (a.output/'startup.cir').write_text(deck);(a.output/'.spiceinit').write_text(init)
    inputs={str(f):sha(f)for f in (source,original,old/'manifest.json',old/'.spiceinit',reference/'manifest.json')}
    prov=dict(source_sha256=SOURCE_SHA,inputs=inputs,case=case,image_manifest=a.image_id,runtime=q['runtime'],ngspice=q['ngspice'],
        instrumented=a.instrumented,parameter_order=q['parameters'],terminal_devices=devices,terminal_nodes=nodes,
        runner_sha256=sha(Path(__file__)),deck_sha256=sha(a.output/'startup.cir'),spiceinit_sha256=sha(a.output/'.spiceinit'),
        declared_changes='Canonical586 source substituted; initializer4->1threads. Optional read-only endpoint2842 queries and terminal-voltage export. Exact original UIC/ramp/seed/load/tolerances/process/temperature.',
        scope='Legacy329-capacitance source, ideal1V IPTAT/1pF VREF. No final native RC, actual downstream, physical startup/EN or lifetime qualification.')
    (a.output/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n')
    with (a.output/'run.log').open('x')as stream:
        state=run_bounded(['ngspice','-b','startup.cir'],stream,a.output/'run.json',300,cwd=a.output,interval_s=1)
    log=(a.output/'run.log').read_text()
    errors=re.findall(r'^.*(?:Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse).*$',log,re.M|re.I)
    result=dict(status='failed',runtime=state,errors=errors,warnings=warning_inventory(log),startup_level_status='not run',hbt_vce_status='not run',
        full2842_pretransient_status='not run: original UIC fixture has no operating-point initialization; none inserted',
        not_run=['Final native parasitics and actual downstream startup','Startup-before-EN contract','Foundry lifetime/model validity'],not_applicable=['MC sample yield: mismatch disabled'])
    try:
        assert state['status']=='completed'and state['returncode']==0 and not errors
        wave=a.output/(case['name']+'.dat');data=np.loadtxt(str(wave),skiprows=1,ndmin=2)
        header=wave.read_text().splitlines()[0].split()
        expected=['time','v(vref)','i(vload)','i(vdd)','v(vbe)','v(dvbe)','v(pbias)','v(pcasc)','v(xbgr.c2)','v(xbgr.vbe3)','v(xbgr.vd1)','v(xbgr.vd2)']
        validate_wave(data,header,expected,3*case['startup'][1])
        result.update(status='passed numerical startup',waveform_sha256=sha(wave),rows=len(data),endpoint_s=float(data[-1,0]),
            vref_end_V=float(data[-1,1]),iptat_end_A=float(data[-1,2]),current_peak_A=float((-data[:,3]).max()),
            startup_level_status='passed'if .9<data[-1,1]<1.2 and data[-1,2]>1e-6 else'failed')
        if a.instrumented:
            sections=re.findall(r'^STARTUP2842_BEGIN\n(.*?)^STARTUP2842_END$',log,re.M|re.S);assert len(sections)==1
            params=re.findall(r'^(@[^\s]+)\s*=\s*(\S+)',sections[0],re.M)
            assert [k for k,v in params]==q['parameters']and all(np.isfinite(float(v))for k,v in params)
            terminal=np.loadtxt(str(a.output/'terminals.dat'),skiprows=1,ndmin=2)
            th=(a.output/'terminals.dat').read_text().splitlines()[0].split()
            validate_wave(terminal,th,['time']+['v('+n+')'for n in nodes],3*case['startup'][1])
            assert terminal.shape==(len(data),len(nodes)+1)and np.isfinite(terminal).all()and np.array_equal(terminal[:,0],data[:,0])
            index={n:i+1 for i,n in enumerate(nodes)};extrema=[]
            for device in devices:
                for pair in ('gs','gd','gb','ds','db','sb')if device['instance'].startswith('XM')else('ce','be','bc'):
                    n1,n2=[device['nodes'][key]for key in pair]
                    values=(terminal[:,index[n1]]if n1!='0'else 0)-(terminal[:,index[n2]]if n2!='0'else 0)
                    extrema.append(dict(instance=device['instance'],model=device['model'],pair=pair,max_abs_V=float(np.abs(values).max())))
            result.update(full2842_endpoint_status='passed finite exact inventory order',parameters_endpoint=params,terminal_extrema=extrema,
                hbt_vce_status='passed'if all(r['max_abs_V']<=1.6 for r in extrema if r['pair']=='ce')else'failed')
        if a.case==0:
            # Reuse the completed identical-source1ms evidence instead of
            # rerunning a new uninstrumented control. Only endpoint exports
            # and placement of the one-thread setting differ.
            control=HERE/'runs/bgr_loop24q4_hv06_startup2_20260922_r3'
            cp=json.loads((control/'manifest.json').read_text())
            c,=[r for r in cp['cases']if r['name']==case['name']]
            assert c['status']=='passed'and c['solver_exit']==0 and not c['timed_out']
            assert cp['candidate_sha256']==sha(control/'pex_nominal.spice')==SOURCE_SHA
            assert cp['model_sha256']==q['runtime']['model_sha256']and cp['osdi_sha256']==q['runtime']['osdi_sha256']
            olddeck=control/(case['name']+'.cir');assert sha(olddeck)==c['deck_sha256']
            export='wrdata '+case['name']+'_terminals.dat '+' '.join('v('+n+')'for n in nodes)+'\n'
            assert olddeck.read_text().replace('.control\nset num_threads=1\n','.control\n').replace(export,'')==original.read_text()
            assert (control/'.spiceinit').read_bytes()==(old/'.spiceinit').read_bytes()
            cw=control/(case['name']+'.dat');assert sha(cw)==c['waveform_sha256']
            exact=wave.read_bytes()==cw.read_bytes()
            result.update(instrumentation_original_wave_bytes_exact=exact,instrumentation_parity_status='passed'if exact else'failed',
                          original_control_manifest_sha256=sha(control/'manifest.json'),original_control_wave_sha256=sha(cw))
            assert exact,'Original12-column waveform changed by read-only instrumentation'
        assert all(sha(Path(f))==h for f,h in inputs.items())
    except (AssertionError,ValueError,OSError,IndexError,KeyError)as exc:
        result.update(status='failed numerical or provenance gate',analysis_error=repr(exc))
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    # Control waveform remains raw for the one exact paired comparison.
    print(json.dumps({k:v for k,v in result.items()if k not in ('warnings','parameters_endpoint','terminal_extrema')},indent=2))
    raise SystemExit(0 if result['status']=='passed numerical startup'else 1)


if __name__=='__main__':main()
