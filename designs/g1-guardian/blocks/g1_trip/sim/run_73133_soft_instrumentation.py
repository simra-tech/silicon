"""Two unchanged-source output-only soft-regeneration observations."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import numpy as np
import run_regenpair4_r100_73133_b as base

ROOT,SIM=base.ROOT,base.SIM
NAME='joint586-73133-soft-instrumentation-20260923-a'
PARENT=base.NAME
NODES=['v(xt.xcs.xp)','v(xt.xcs.xq)','v(xt.xcs.xn)','v(xt.xcs.yn)']


def transform(text,case):
    assert case in ['c08','heldout-p27']
    assert text.count('setseed 73133\n')==1 and text.count('tran 0.2n 1.02u 0 0.2n\n')==1
    assert not any(n in text for n in NODES)
    old='qualification/'+PARENT+'/'+case+'/phase0.dat';new='qualification/'+NAME+'/'+case+'/phase0.dat'
    assert text.count(old)==1
    text=text.replace(old,new)
    for prefix in ['.save ','wrdata ']:
        line,=re.findall('(?m)^'+re.escape(prefix)+'.+$',text)
        text=text.replace(line+'\n',line+' '+' '.join(NODES)+'\n')
    return text


def prepare():
    source=SIM/'qualification'/PARENT/'contract.json';assert base.sha(source)=='93b156d9151c85c5f11a7a2f25419dcc5e0e20db66b6dca616ed99f6bd22e431'
    old=json.loads(source.read_text());out=base.allocate_run(SIM,NAME)
    bindings=dict(old['bindings_sha256'])
    for f in [source,Path(__file__).resolve(),SIM/'test_73133_soft_instrumentation.py']:bindings[str(f.relative_to(ROOT))]=base.sha(f)
    cases={}
    for case in ['c08','heldout-p27']:
        prior=SIM/'qualification'/PARENT/case;summary=json.loads((prior/'summary.json').read_text());assert summary['status']=='passed'
        leaf=out/case;leaf.mkdir();text=(prior/'probe.cir').read_text();new=transform(text,case)
        inverse=new.replace(' '+' '.join(NODES)+'\n','\n').replace(NAME,PARENT);assert inverse==text
        (leaf/'probe.cir').write_text(new)
        for n in ['probe.cir','summary.json','run.json','run.log']:bindings[str((prior/n).relative_to(ROOT))]=base.sha(prior/n)
        cases[case]=dict(deck_sha256=base.sha(leaf/'probe.cir'),prior=str(prior.relative_to(ROOT)))
    for n in old['source_hashes']:bindings[str((SIM/'qualification'/PARENT/n).relative_to(ROOT))]=old['source_hashes'][n]
    with (out/'contract.json').open('x') as f:json.dump(dict(run_id=NAME,cases=cases,bindings_sha256=bindings,base_contract=str(source.relative_to(ROOT)),watchdog_s=1200,
        scope='Only append4softinternal outputs; original18prefix/timegrid comparisons remain explicit. Same73133source/codes/solver/.2ns/reset/full11512+27. No sizing/criterion/adoption change.'),f,indent=2)
    print(str((out/'contract.json').relative_to(ROOT)),base.sha(out/'contract.json'))


def check(path,digest):
    assert base.sha(ROOT/path)==digest;packet=json.loads((ROOT/path).read_text())
    assert packet['run_id']==NAME and packet['watchdog_s']==1200
    assert all(base.sha(ROOT/n)==v for n,v in packet['bindings_sha256'].items())
    for case,ref in packet['cases'].items():
        leaf=SIM/'qualification'/NAME/case;assert base.sha(leaf/'probe.cir')==ref['deck_sha256']
        assert (leaf/'probe.cir').read_text()==transform((ROOT/ref['prior']/'probe.cir').read_text(),case)
    return packet,json.loads((ROOT/packet['base_contract']).read_text())


def readwave(path):
    with base.open_wave(path,'rb') as f:blob=f.read()
    header=blob.splitlines()[0].decode().split();data=np.array([list(map(float,l.split())) for l in blob.splitlines()[1:] if l.strip()])
    assert data.shape[1]==len(header) and np.isfinite(data).all() and np.all(np.diff(data[:,0])>0) and abs(data[-1,0]-1.02e-6)<1e-18
    return header,data,hashlib.sha256(blob).hexdigest()


def inspect(packet,control,case):
    leaf=SIM/'qualification'/NAME/case;prior=ROOT/packet['cases'][case]['prior'];old=json.loads((prior/'summary.json').read_text())
    state=json.loads((leaf/'run.json').read_text());log=(leaf/'run.log').read_text();base.runtime_gate(state,log)
    section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S);g=control['groups']
    before=base.read_group(section,'NON_BGR_BEFORE',g['NON_BGR'])+base.read_group(section,'BGR_BEFORE',g['BGR'])
    parsed=base.phase_parameters(section,g,before)
    assert len(before)==11512 and before==parsed['parameters_after']==old['parameter_audit']['parameters_before']
    assert parsed['legacy27']==old['parameter_audit']['legacy27'] and len(parsed['legacy27'])==27
    names,data,digest=readwave(leaf/'phase0.dat');oldnames,olddata,olddigest=readwave(prior/'phase0.dat')
    assert names==oldnames+NODES and len(oldnames)==18
    analysis=base.analyze_wave(data[:,:13].tolist(),control['sampling']);assert analysis['sampling_status']=='passed'
    exact_grid=np.array_equal(data[:,0],olddata[:,0]);exact_prefix=np.array_equal(data[:,:18],olddata)
    errors={name:float(np.max(np.abs(np.interp(olddata[:,0],data[:,0],data[:,i])-olddata[:,i]))) for i,name in enumerate(oldnames[1:],1)}
    cycles=[]
    for edge in analysis['actual_clock_rising_crossings_s']['soft'][2:5]:
        samples=[]
        for ns in [-1,0,.1,.2,.3,.5,1,2,5,20,80]:
            v=[float(np.interp(edge+ns*1e-9,data[:,0],data[:,i])) for i in range(len(names))]
            samples.append(dict(delay_ns=ns,input_differential_V=v[2]-v[3],soft_output_V=v[5],soft_internal_xp_xq_xn_yn_V=v[18:22]))
        cycles.append(dict(edge_s=edge,samples=samples))
    decisions={k:v['measured_edge_decision'] for k,v in analysis['comparators'].items()}
    return dict(numerical_status='passed',parameter11512_legacy27_exact=True,exact_original_grid=exact_grid,exact_original18_numeric=exact_prefix,
        parity_status='passed' if exact_grid and exact_prefix and decisions==old['decisions'] else 'failed',original_decisions=old['decisions'],decisions=decisions,
        fullwave_interpolated_max_errors_V=errors,cycles=cycles,decoded_wave_sha256=digest,original_decoded_wave_sha256=olddigest,wall_s=state['wall_s'])


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','run','audit']);p.add_argument('--packet');p.add_argument('--packet-sha256');p.add_argument('--case',choices=['c08','heldout-p27']);p.add_argument('--image-id');a=p.parse_args()
    if a.mode=='prepare':prepare();return
    packet,control=check(a.packet,a.packet_sha256);observed=base.runtime(control,a.image_id);out=SIM/'qualification'/NAME
    if a.mode=='run':
        leaf=out/a.case;assert not (leaf/'run.json').exists()
        with (leaf/'provenance.json').open('x') as f:json.dump(dict(runtime=observed,packet_sha256=a.packet_sha256),f,indent=2)
        with (leaf/'run.log').open('x') as log:base.run_bounded(['ngspice','-b',str((leaf/'probe.cir').relative_to(SIM))],log,leaf/'run.json',1200,cwd=SIM,interval_s=1)
        result=dict(numerical_status='failed',parity_status='not run')
        try:result.update(inspect(packet,control,a.case))
        except (AssertionError,ValueError,KeyError,OSError,IndexError) as e:result['analysis_error']=repr(e)
        with (leaf/'summary.json').open('x') as f:json.dump(result,f,indent=2)
        if (leaf/'phase0.dat').exists():base.archive_new_wave(leaf/'phase0.dat')
        raise SystemExit(0 if result['numerical_status']=='passed' else 1)
    rows=[]
    for case in ['c08','heldout-p27']:
        row=inspect(packet,control,case);assert row==json.loads((out/case/'summary.json').read_text());rows.append(dict(case=case,result=row))
    with (out/'audit.json').open('x') as f:json.dump(dict(status='completed output-only diagnosis',packet_sha256=a.packet_sha256,records=rows),f,indent=2)


if __name__=='__main__':main()
