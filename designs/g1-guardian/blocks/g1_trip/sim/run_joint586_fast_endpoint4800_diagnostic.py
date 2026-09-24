#!/usr/bin/env python3
"""One exact fast78103 endpoint, 4800 s operational watchdog; not population."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

from result_directory import allocate_run
from run_bgr_substitution_draw_audit import read_group
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import analyze_wave,run_bounded

SIM=Path(__file__).resolve().parent
ROOT=SIM.parents[4]
ORIGINAL=SIM/'qualification/joint586-fast-nodeset-calibration-s78103-20260923-a'
REFERENCE=SIM/'qualification/joint586-mm-tranqual-20260922-a-enabled/preparation.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()


def redirected(original,old_run,new_run,index):
    before='qualification/'+old_run+'/p%02d/phase0.dat'%index
    after='qualification/'+new_run+'/p%02d/phase0.dat'%index
    assert original.count(before)==1 and original.count('wrdata ')==1
    result=original.replace(before,after)
    assert result.replace(after,before)==original
    return result


def verify_input(packet,row):
    source=ORIGINAL/('p%02d'%row['index'])
    assert packet['status']=='PREPARED ONLY; original1200s timeouts retained; no sample/population credit'
    assert packet['seed']==78103 and packet['watchdog_s']==4800 and packet['target_transient_s']==1.02e-6
    assert sha(ORIGINAL/'provenance.json')==packet['original_provenance_sha256']
    assert sha(REFERENCE)==packet['reference_preparation_sha256']
    assert all(sha(ORIGINAL/name)==value for name,value in packet['original_source_hashes'].items())
    for key,name in [('original_deck_sha256','probe.cir'),('original_log_sha256','run.log'),
                     ('original_run_sha256','run.json'),('original_leaf_summary_sha256','summary.json')]:
        assert sha(source/name)==row[key]
    original_summary=json.loads((source/'summary.json').read_text())
    assert original_summary['status']=='failed' and original_summary['codes']==row['codes']
    assert original_summary['shunt_V']==.025 and original_summary['temperature_C']==25
    assert original_summary['corner']=='fast' and original_summary['wave_columns']==18
    assert original_summary['watchdog_status']=='timeout' and original_summary['returncode']==-15
    original_deck=(source/'probe.cir').read_text()
    new_deck=redirected(original_deck,ORIGINAL.name,row['run_id'],row['index'])
    assert hashlib.sha256(new_deck.encode()).hexdigest()==row['diagnostic_deck_sha256']
    prep=json.loads(REFERENCE.read_text())
    log=(source/'run.log').read_text()
    vector=read_group(log,'NON_BGR_BEFORE',prep['groups']['NON_BGR'])+read_group(log,'BGR_BEFORE',prep['groups']['BGR'])
    assert len(vector)==packet['before_vector_count']==11512
    assert canonical(vector)==packet['before_vector_sha256']==row['before_vector_sha256']
    return new_deck,vector,prep


def runtime_matches(image_id):
    expected=json.loads((ORIGINAL/'provenance.json').read_text())['runtime_identity']
    pdk=Path('/foss/pdks/ihp-sg13g2')
    observed=dict(image_id_observed_by_host=image_id,pdk_commit=(pdk/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(path.relative_to(pdk)):sha(path) for path in (pdk/'libs.tech/ngspice/models').rglob('*') if path.is_file()},
        solver='sparse')
    assert observed==expected
    return observed


def audit_result(log_path,wave_path,vector,prep):
    log=log_path.read_text()
    assert 'JOINT_POPULATION_TRAN_END' in log
    section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S)
    before=read_group(section,'NON_BGR_BEFORE',prep['groups']['NON_BGR'])+read_group(section,'BGR_BEFORE',prep['groups']['BGR'])
    assert before==vector
    parameters=phase_parameters(section,prep['groups'],vector)
    rows=[list(map(float,line.split())) for line in wave_path.read_text().splitlines()[1:] if line.strip()]
    assert rows and all(len(row)==18 and all(math.isfinite(value) for value in row) for row in rows)
    assert abs(rows[-1][0]-1.02e-6)<1e-18
    analysis=analyze_wave([row[:13] for row in rows],prep['prospective_sampling'])
    assert analysis['sampling_status']=='passed'
    decisions={key:row['measured_edge_decision'] for key,row in analysis['comparators'].items()}
    assert set(decisions)=={'soft','hard'} and all(type(value) is bool for value in decisions.values())
    return dict(parameter_audit=parameters,wave_rows=len(rows),last_time_s=rows[-1][0],
        wave_columns=18,wave_sha256=sha(wave_path),analysis=analysis,decisions=decisions)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet',type=Path,required=True)
    parser.add_argument('--packet-sha256',required=True)
    parser.add_argument('--endpoint',type=int,choices=[0,1],required=True)
    parser.add_argument('--image-id',required=True)
    args=parser.parse_args()
    packet_path=args.packet if args.packet.is_absolute() else ROOT/args.packet
    assert sha(packet_path)==args.packet_sha256
    packet=json.loads(packet_path.read_text())
    row,=[r for r in packet['rows'] if r['index']==args.endpoint]
    assert sha(Path(__file__))==packet['diagnostic_runner_sha256']
    deck,vector,prep=verify_input(packet,row)
    runtime=runtime_matches(args.image_id)
    out=allocate_run(SIM,row['run_id'])
    leaf=out/('p%02d'%args.endpoint);leaf.mkdir()
    (leaf/'probe.cir').write_text(deck)
    assert sha(leaf/'probe.cir')==row['diagnostic_deck_sha256']
    summary=dict(status='running; diagnostic only',seed=78103,endpoint=args.endpoint,
        original_run_id=ORIGINAL.name,run_id=row['run_id'],packet_sha256=args.packet_sha256,
        original_1200s_timeout_retained=True,population_credit=False,
        source_deck_delta='single wrdata target path only',original_before_vector_sha256=packet['before_vector_sha256'],
        expected_runtime_identity=runtime,watchdog_s=4800)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (leaf/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str((leaf/'probe.cir').relative_to(SIM))],stream,leaf/'run.json',4800,cwd=SIM,interval_s=1)
    summary['runtime']=state
    try:
        assert state['status']=='completed' and state['returncode']==0
        summary['observation']=audit_result(leaf/'run.log',leaf/'phase0.dat',vector,prep)
        summary['status']='passed exact-input endpoint diagnostic; original population still failed'
    except (AssertionError,ValueError,OSError,KeyError,IndexError) as exc:
        summary.update(status='failed endpoint diagnostic; original population still failed',analysis_error=repr(exc))
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({key:value for key,value in summary.items() if key not in ('observation','expected_runtime_identity','runtime')},indent=2))
    if not summary['status'].startswith('passed'):raise SystemExit(1)


if __name__=='__main__':main()
