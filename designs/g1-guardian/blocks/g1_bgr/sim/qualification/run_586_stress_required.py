#!/usr/bin/env python3
"""Reapply three original stress stimuli to canonical586; no physical-RC claim."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import numpy as np
from run_586_startup_required import HERE,SOURCE_SHA,IMAGE,sha,terminal_map,run_bounded,warning_inventory

HEADERS=['time','v(vref)','i(vload)','i(vdd)','v(vbe)','v(dvbe)','v(pbias)','v(pcasc)',
         'v(xbgr.c2)','v(xbgr.vbe3)','v(xbgr.vd1)','v(xbgr.vd2)']


def instrument(deck,parameters,nodes):
    assert len(parameters)==len(set(parameters))==2842
    assert deck.count('tran 2n 40u\n')==1 and deck.count('quit\n')==1
    assert ' uic'not in deck and '\nop\n'not in deck
    addition=('echo STRESS2842_BEGIN\n'+''.join('print '+p+'\n'for p in parameters)+
              'echo STRESS2842_END\nwrdata terminals.dat '+' '.join('v('+n+')'for n in nodes)+'\n')
    result=deck.replace('quit\n',addition+'quit\n')
    assert result.replace(addition,'')==deck
    return result


def validate(data,header,expected):
    assert header==expected and data.ndim==2 and data.shape[1]==len(expected) and len(data)>1
    assert np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
    assert data[0,0]>=0 and abs(data[-1,0]-40e-6)<1e-12


def analyze(folder,provenance):
    p=provenance;state=json.loads((folder/'run.json').read_text());log=(folder/'run.log').read_text()
    errors=re.findall(r'^.*(?:Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse|\bnan\b).*$',log,re.M|re.I)
    result=dict(status='failed',runtime=state,errors=errors,warnings=warning_inventory(log),
        endpoint_parameter_status='not run',hbt_vce_status='not run',startup_level_status='not run',
        pretransient_parameters='not run: original transient initializes OP internally; no extra OP inserted',
        not_run=['Final native RC','Actual downstream loading','Full voltage/lifetime qualification','Allocated recovery/settling error'],
        not_applicable=['Statistical yield: mismatch disabled'])
    try:
        assert state['status']=='completed'and state['returncode']==0 and not errors
        wave=folder/(p['case']['name']+'.dat');data=np.loadtxt(str(wave),skiprows=1,ndmin=2)
        validate(data,wave.read_text().splitlines()[0].split(),HEADERS)
        terminal=np.loadtxt(str(folder/'terminals.dat'),skiprows=1,ndmin=2)
        validate(terminal,(folder/'terminals.dat').read_text().splitlines()[0].split(),['time']+['v('+n+')'for n in p['terminal_nodes']])
        assert np.array_equal(terminal[:,0],data[:,0])
        section,=re.findall(r'^STRESS2842_BEGIN\n(.*?)^STRESS2842_END$',log,re.M|re.S)
        params=re.findall(r'^(@[^\s]+)\s*=\s*(\S+)',section,re.M)
        assert [k for k,v in params]==p['parameter_order']and all(np.isfinite(float(v))for k,v in params)
        index={n:i+1 for i,n in enumerate(p['terminal_nodes'])};extrema=[]
        for device in p['terminal_devices']:
            for pair in ('gs','gd','gb','ds','db','sb')if device['instance'].startswith('XM')else('ce','be','bc'):
                n1,n2=[device['nodes'][k]for k in pair]
                delta=(terminal[:,index[n1]]if n1!='0'else 0)-(terminal[:,index[n2]]if n2!='0'else 0)
                extrema.append(dict(instance=device['instance'],model=device['model'],pair=pair,max_abs_V=float(np.abs(delta).max())))
        result.update(status='passed numerical characterization',endpoint_parameter_status='passed',parameters_endpoint=params,
            terminal_extrema=extrema,wave_sha256=sha(wave),terminal_wave_sha256=sha(folder/'terminals.dat'),rows=len(data),
            endpoint_s=float(data[-1,0]),vref_end_V=float(data[-1,1]),vref_min_V=float(data[:,1].min()),vref_max_V=float(data[:,1].max()),
            iptat_end_A=float(data[-1,2]),supply_current_peak_A=float((-data[:,3]).max()),
            startup_level_status='passed'if .9<data[-1,1]<1.2 else'failed',
            hbt_vce_status='passed'if all(r['max_abs_V']<=1.6 for r in extrema if r['pair']=='ce')else'failed')
    except (AssertionError,ValueError,OSError,IndexError,KeyError)as exc:
        result.update(status='failed numerical or provenance gate',analysis_error=repr(exc))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',choices=('dip','r4','load'),required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--image-id',required=True)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and a.image_id==IMAGE
    old=HERE/'runs/bgr_stress3_20260921_01';reference=HERE/'runs/bgr_one_draw_20260922_r1'
    manifest=json.loads((old/'manifest.json').read_text());q=json.loads((reference/'manifest.json').read_text())
    case,=[r for r in manifest['cases']if r['name']==a.case]
    assert case['status']=='passed'and case['stress']==a.case and case['startup']is None and not case['mm']
    source=reference/'disabled/pex_nominal.spice';assert sha(source)==q['source_sha256']==SOURCE_SHA
    assert q['status']=='passed harness qualification'
    pd=Path('/foss/pdks/ihp-sg13g2');assert (pd/'COMMIT').read_text().strip()==q['runtime']['pdk_commit']
    for key,folder,pattern in [('model_sha256','models','*.lib'),('osdi_sha256','osdi','*.osdi')]:
        assert q['runtime'][key]=={str(f.relative_to(pd)):sha(f)for f in sorted((pd/'libs.tech/ngspice'/folder).glob(pattern))}
    assert subprocess.check_output(['ngspice','--version'],universal_newlines=True)==q['ngspice']
    original=old/(a.case+'.cir');assert sha(original)==case['deck_sha256']
    devices,nodes=terminal_map(source.read_text());deck=instrument(original.read_text(),q['parameters'],nodes)
    init=(old/'.spiceinit').read_text();assert init.count('set num_threads=4')==1
    init=init.replace('set num_threads=4','set num_threads=1')
    a.output.mkdir(parents=True)
    for f in [source,Path(__file__)]:shutil.copyfile(str(f),str(a.output/('pex_nominal.spice'if f==source else'runner.py')))
    (a.output/'stress.cir').write_text(deck);(a.output/'.spiceinit').write_text(init)
    inputs={str(f):sha(f)for f in (source,original,old/'manifest.json',old/'.spiceinit',reference/'manifest.json',HERE/'run_586_startup_required.py')}
    prov=dict(source_sha256=SOURCE_SHA,inputs=inputs,case=case,image_manifest=a.image_id,runtime=q['runtime'],ngspice=q['ngspice'],
        parameter_order=q['parameters'],terminal_devices=devices,terminal_nodes=nodes,runner_sha256=sha(Path(__file__)),
        deck_sha256=sha(a.output/'stress.cir'),spiceinit_sha256=sha(a.output/'.spiceinit'),
        declared_changes='Canonical586 source; initializer4->1threads; read-only endpoint2842 and terminal export. Original stress/implicit OP/time/seed/tolerances unchanged.',
        scope='Legacy329C/idealIPTAT1V/1pFVREF; synthetic original nominal stress, not final native RC/real downstream or lifetime.')
    (a.output/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n')
    with(a.output/'run.log').open('x')as stream:
        run_bounded(['ngspice','-b','stress.cir'],stream,a.output/'run.json',300,cwd=a.output,interval_s=1)
    result=analyze(a.output,prov)
    assert all(sha(Path(f))==h for f,h in inputs.items())
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in('warnings','parameters_endpoint','terminal_extrema')},indent=2))
    raise SystemExit(0 if result['status']=='passed numerical characterization'else 1)


if __name__=='__main__':main()
