#!/usr/bin/env python3
"""Frozen four-clip CC pilot with strict membership, eight AC and context gates."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import time
import pya
from sense_feed_field_math import parse_caps, reduce_caps, ac_deck, ac_check, context_check
from screen_sense_dual_gate_proposal import GM4, sha
from prepare_sense_feed_field_inventory import SOURCE, BASELINE, CANDIDATE

HERE=Path(__file__).resolve().parent
LIMIT=128*1024*1024


def dump(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def size(folder):return sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())


def bounded(command,folder,name,seconds,batch,clip_bytes):
    """Own child process group; stop on timeout, interruption or sampled growth cap."""
    record=dict(status='running',command=command,timeout_s=seconds)
    destination=folder/(name+'.json');logfile=folder/(name+'.log');start=time.monotonic()
    interrupted=[];handlers={sig:signal.signal(sig,lambda signum,frame:interrupted.append(signum)) for sig in (signal.SIGTERM,signal.SIGINT)}
    proc=None;reason=None
    try:
        with logfile.open('x') as log:
            proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            record['pid']=proc.pid;dump(destination,record)
            while proc.poll() is None:
                elapsed=time.monotonic()-start;growth=size(batch)+clip_bytes
                if interrupted or elapsed>=seconds or growth>LIMIT:
                    reason='interrupted' if interrupted else 'timeout' if elapsed>=seconds else 'output_limit'
                    os.killpg(proc.pid,signal.SIGTERM)
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                    break
                try:proc.wait(timeout=.25)
                except subprocess.TimeoutExpired:pass
            record.update(returncode=proc.returncode,status=reason or ('completed' if proc.returncode==0 else 'failed'))
    except Exception as exc:
        record.update(status='runner_error',error=repr(exc));raise
    finally:
        if proc is not None and proc.poll() is None:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
        for sig,handler in handlers.items():signal.signal(sig,handler)
        record.update(wall_s=time.monotonic()-start,observed_total_output_bytes=size(batch)+clip_bytes)
        if record['observed_total_output_bytes']>LIMIT:record['status']='output_limit'
        dump(destination,record)
    return record


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--clips',type=Path,required=True);p.add_argument('--controls',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    pdk=Path('/foss/pdks/ihp-sg13g2');assert (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    source=GM4.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)==SOURCE
    prepared=json.loads((a.clips/'summary.json').read_text())
    assert prepared['status']=='passed four exact source-held XM14 pilot clips; extraction not run'
    assert prepared['baseline_GDS_sha256']==BASELINE and prepared['candidate_GDS_sha256']==CANDIDATE
    assert prepared['source_sha256']==SOURCE and [r['name'] for r in prepared['clips']]==['before24','before48','after24','after48']
    controls=json.loads(a.controls.read_text());assert controls['status']=='passed'
    assert 'test_sense_feed_field_math.py' in ' '.join(controls['command'])
    package=Path('/usr/local/lib/python3.12/dist-packages/klayout_pex')
    deck=HERE.parent/'export_clip_lvsdb.lvs'
    rules={str(q.relative_to(package)):sha(q) for q in (package/'pdk/ihp-sg13g2/libs.tech/kpex').rglob('*') if q.is_file()}
    assert rules
    a.output.mkdir(parents=True);clip_bytes=size(a.clips)
    for name in ('run_sense_feed_field_pilot.py','sense_feed_field_math.py','test_sense_feed_field_math.py'):
        (a.output/name).write_bytes((HERE/name).read_bytes())
    result=dict(status='running four-clip field pilot',source_sha256=SOURCE,baseline_GDS_sha256=BASELINE,
        candidate_GDS_sha256=CANDIDATE,clip_summary_sha256=sha(a.clips/'summary.json'),controls_receipt_sha256=sha(a.controls),
        runner_sha256=sha(Path(__file__)),math_sha256=sha(HERE/'sense_feed_field_math.py'),
        controls_source_sha256=sha(HERE/'test_sense_feed_field_math.py'),stock_export_wrapper_sha256=sha(deck),
        installed_rule_hashes=rules,clips=[],context_checks={},output_limit_bytes=LIMIT,
        limits=dict(native_export_s=30,KPEX_CC_s=120,AC_s=30),
        boundary='Source-proven P/N pieces held at equal diagnostic potential; all other drawing nets and VSUBS grounded; no fill',
        not_run=['Other feeder sites','Complete Poly/Active/Cont/MIM field','Fullchip fill/context',
                 'Source compact-model attachment or actual electrical circuit','IR/EM','Adoption'])
    start=time.monotonic();summary=a.output/'summary.json';dump(summary,result)
    try:
        checked=bounded(['python3',str(HERE/'test_sense_feed_field_math.py')],a.output,'current_controls',30,a.output,clip_bytes)
        control_log=(a.output/'current_controls.log').read_text()
        assert checked['status']=='completed' and 'Ran 18 tests' in control_log and control_log.rstrip().endswith('OK')
        assert sha(HERE/'sense_feed_field_math.py')==result['math_sha256']
        assert sha(HERE/'test_sense_feed_field_math.py')==result['controls_source_sha256']
        result['current_controls']=checked;dump(summary,result)
        for row in prepared['clips']:
            name=row['name'];clip=a.clips/name;leaf=a.output/name;leaf.mkdir()
            provenance=json.loads((clip/'provenance.json').read_text())
            assert sha(clip/'clip.gds')==row['GDS_sha256']==provenance['GDS_sha256']
            assert sha(clip/'provenance.json')==row['provenance_sha256']
            assert provenance['status']=='passed exact source/member/roundtrip clip preparation'
            item=dict(name=name,status='not run',GDS_sha256=row['GDS_sha256'],provenance_sha256=row['provenance_sha256'],steps=[],AC=[])
            result['clips'].append(item);dump(summary,result)
            database=leaf/'clip.lvsdb'
            command=['klayout','-b','-r',str(deck)]
            for value in ['input='+str((clip/'clip.gds').resolve()),'report='+str(database.resolve()),
                'export_netlist='+str((leaf/'clip.cir').resolve()),'target_netlist='+str((leaf/'cleanup.cir').resolve()),
                'thr=1','run_mode=deep','net_only=true','no_simplify=true','combine_devices=false',
                'purge=false','purge_nets=false','top_lvl_pins=true','spice_net_names=true','scale=false']:
                command+=['-rd',value]
            state=bounded(command,leaf,'native_export',30,a.output,clip_bytes);item['steps'].append(state);dump(summary,result)
            assert state['status']=='completed' and database.exists(),'Stock native export incomplete'
            command=['kpex','--pdk','ihp-sg13g2','--threads','1','--lvsdb',str(database.resolve()),
                     '--cell','sense_fill_clip','--2.5D','--mode','CC','--out_dir',str((leaf/'kpex').resolve())]
            state=bounded(command,leaf,'kpex',120,a.output,clip_bytes);item['steps'].append(state);dump(summary,result)
            assert state['status']=='completed','KPEX did not complete'
            paths=list((leaf/'kpex').rglob('*_k25d_pex_netlist.spice'));assert len(paths)==1,'Missing or ambiguous capacitor graph'
            raw=paths[0].read_text();caps=parse_caps(raw);reduced=reduce_caps(caps,provenance)
            assert math.isfinite(reduced['floating_charge_residual_F']) and reduced['floating_charge_residual_F']<=1e-25
            item.update(serialized_capacitor_graph_sha256=sha(paths[0]),reduction=reduced,
                        serializer_scope='Unchanged stock emitted SPICE capacitor graph; AC validates these retained values')
            dump(leaf/'reduction.json',reduced);dump(summary,result)
            for col,drive in enumerate(('P','N')):
                path=leaf/('drive_'+drive+'.cir');path.write_text(ac_deck(caps,reduced['node_groups'],drive))
                state=bounded(['ngspice','-b',str(path.resolve())],leaf,'AC_'+drive,30,a.output,clip_bytes)
                log=(leaf/('AC_'+drive+'.log')).read_text(errors='replace')
                checked=ac_check(log,state.get('returncode'),[reduced['matrix_F'][i][col] for i in range(2)])
                checked.update(drive=drive,deck_sha256=sha(path),child=state);item['AC'].append(checked);dump(summary,result)
                assert state['status']=='completed' and checked['status']=='passed','Independent AC check failed'
            assert sha(source)==SOURCE and sha(clip/'clip.gds')==row['GDS_sha256']
            item['status']='passed extraction/member/matrix/two-AC checks';dump(summary,result)
        assert len(result['clips'])==4 and sum(len(r['AC']) for r in result['clips'])==8
        items={r['name']:r['reduction'] for r in result['clips']}
        for state in ('before','after'):result['context_checks'][state]=context_check(items[state+'24'],items[state+'48'])
        result['signed_candidate_minus_baseline']={str(width):{
            key:items['after'+str(width)][key]-items['before'+str(width)][key]
            for key in ('P_ground_F','N_ground_F','mutual_F','differential_energy_F','common_mode_energy_F')}
            for width in (24,48)}
        assert all(sha(package/key)==value for key,value in rules.items()) and sha(deck)==result['stock_export_wrapper_sha256']
        result['status']='passed bounded local metal-field pilot' if all(r['status']=='passed' for r in result['context_checks'].values()) else 'failed original 1% or zero-denominator context gate'
    except Exception as exc:
        result.update(status='failed bounded field pilot execution',error=repr(exc));raise
    finally:
        result.update(wall_s=time.monotonic()-start,observed_total_output_bytes=size(a.output)+clip_bytes)
        dump(summary,result);print(json.dumps({k:v for k,v in result.items() if k not in ('installed_rule_hashes','clips')},indent=2))
    raise SystemExit(0 if result['status']=='passed bounded local metal-field pilot' else 1)


if __name__=='__main__':main()
