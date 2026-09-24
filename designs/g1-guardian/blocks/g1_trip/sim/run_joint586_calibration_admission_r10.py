"""Scheduling-only admission adapter around the unchanged fulljoint586 runner.

Each leaf parks outside the original 1200 s solver watchdog until the host
controller provides a fresh, ROOT-bound resource permit. No deck, seed,
ngspice command, option, analysis, or electrical criterion is changed.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import run_joint586_calibration as original

RUNNER_SHA='5bccaeca523fcca0640b498446b07483c49e7bdbfdfdc11639f3f8af4c80ed81'
REPLACEMENT='joint586_post100_elastic_replacement_authority_20260924_r10.json'
REQUIRED_CHECKS={'cpu_budget_positive','quota_growth_and_reserve','inodes_available',
    'ram_available','coordinated_CPU_reservations_fit','external_allocation_growth','external_inodes'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc():
    return datetime.datetime.utcnow().isoformat()+'Z'


def age_seconds(stamp):
    when=datetime.datetime.strptime(stamp.replace('+00:00','Z'),'%Y-%m-%dT%H:%M:%S.%fZ')
    return (datetime.datetime.utcnow()-when).total_seconds()


def parse_utc(stamp):
    normalized=stamp.replace('+00:00','Z')
    return datetime.datetime.strptime(normalized,'%Y-%m-%dT%H:%M:%SZ')


def write_atomic(path,value):
    pending=path.with_name(path.name+'.pending')
    pending.write_text(json.dumps(value,indent=2)+'\n')
    os.replace(str(pending),str(path))


def request_context():
    args=sys.argv[1:]
    run_id=args[args.index('--run-id')+1]
    seed=int(args[args.index('--seed')+1])
    cpu=int(os.environ['G1_CPUSET'])
    lease_rel=Path(os.environ['G1_R10_LEASE_REL'])
    assert not lease_rel.is_absolute() and '..' not in lease_rel.parts
    lease=original.ROOT/lease_rel
    lease_sha=os.environ['G1_R10_LEASE_SHA256']
    assert sha(Path(original.__file__))==RUNNER_SHA
    assert sha(lease)==lease_sha
    authority=json.loads(lease.read_text())
    assert authority['status']=='ROOT authorized r10 terminal successor and leaf admission'
    assert cpu in authority['cpus']
    return dict(run_id=run_id,seed=seed,cpu=cpu,lease=lease,lease_sha256=lease_sha,
        output=original.SIM/'qualification'/run_id)


def permit_valid(grant,request,context,max_age=45):
    if grant.get('request_sha256')!=sha(request):raise AssertionError('Admission request identity changed')
    if grant.get('lease_sha256')!=context['lease_sha256']:raise AssertionError('Admission lease mismatch')
    if grant.get('seed')!=context['seed'] or grant.get('cpu')!=context['cpu']:
        raise AssertionError('Admission seed/CPU mismatch')
    authority_rel=Path(grant['authority_path'])
    gate_rel=Path(grant['gate_path'])
    assert not authority_rel.is_absolute() and '..' not in authority_rel.parts
    assert not gate_rel.is_absolute() and '..' not in gate_rel.parts
    authority_path=original.ROOT/authority_rel
    replacement=original.ROOT/'.private/research/verification'/REPLACEMENT
    if replacement.exists() and (authority_path!=replacement or grant['authority_sha256']!=sha(replacement)):
        return False
    if sha(authority_path)!=grant['authority_sha256']:
        raise AssertionError('Admission authority bytes changed')
    authority=json.loads(authority_path.read_text())
    if grant['authority_sha256']!=context['lease_sha256']:
        assert authority['status']=='ROOT authorized r10 replacement leaf admission'
        assert authority['previous_lease_sha256']==context['lease_sha256']
        assert authority['target']=='r10 existing leaves only' and authority['no_new_sample_claims'] is True
        assert authority['execution_contract_sha256']==json.loads(context['lease'].read_text())['execution_contract_sha256']
        assert authority['source_runner_sha256']==RUNNER_SHA
        assert authority['adapter_sha256']==sha(Path(__file__))
        for key in ('checker','ledger','activation'):
            path=Path(authority[key+'_path'])
            assert not path.is_absolute() and '..' not in path.parts
            assert sha(original.ROOT/path)==authority[key+'_sha256']
    else:
        assert authority_path==context['lease']
        assert authority['status']=='ROOT authorized r10 terminal successor and leaf admission'
    assert context['cpu'] in authority['cpus']
    gate=original.ROOT/gate_rel
    if sha(gate)!=grant['gate_sha256']:raise AssertionError('Resource gate bytes changed')
    report=json.loads(gate.read_text())
    if report.get('status')!='passed':return False
    for key in ('activation_sha256','checker_sha256','ledger_sha256','policy_version'):
        if report.get(key)!=authority[key]:raise AssertionError('Gate authority binding mismatch: '+key)
    if report['policy_version']=='20260923-owner-overnight10reserve-v5':
        if report.get('window_status')!='active overnight CPU loan window':
            return False
        now=datetime.datetime.utcnow()
        if not parse_utc(report['window_start_utc'])<=now<parse_utc(report['window_end_utc']):
            return False
        if report.get('checks',{}).get('overnight_window_active') is not True:
            raise AssertionError('Overnight window check missing')
        if report.get('checks',{}).get('overnight_ledger_activated') is not True:
            raise AssertionError('Overnight ledger check missing')
    if not all(report.get('checks',{}).get(key) is True for key in REQUIRED_CHECKS):
        raise AssertionError('Incomplete resource gate')
    if context['cpu'] not in report['coordinated_allocation']['cpus']:
        raise AssertionError('CPU absent from resource allocation')
    if report['project_cpu_budget']<report['coordinated_allocation']['distinct_cpu_ceiling']:
        raise AssertionError('CPU budget below coordinated allocation')
    if not 0<=age_seconds(report['utc'])<=max_age:return False
    if not 0<=age_seconds(grant['issued_utc'])<=max_age:return False
    return True


def wait_for_leaf(context,index,pause_path,heartbeat_seconds=15):
    out=context['output']
    request=out/('admission-p%02d.request.json'%index)
    grant=out/('admission-p%02d.grant.json'%index)
    if not request.exists():
        with request.open('x') as stream:
            json.dump(dict(status='waiting host admission; no solver child',run_id=context['run_id'],
                seed=context['seed'],cpu=context['cpu'],leaf_index=index,
                lease_sha256=context['lease_sha256'],runner_sha256=RUNNER_SHA),stream,indent=2)
    while True:
        assert sha(context['lease'])==context['lease_sha256']
        original_check_pause(pause_path)
        if grant.exists() and permit_valid(json.loads(grant.read_text()),request,context):
            original_check_pause(pause_path)
            return
        write_atomic(out/('admission-p%02d.heartbeat.json'%index),dict(
            status='parked before next leaf; no solver child',seed=context['seed'],cpu=context['cpu'],
            leaf_index=index,lease_sha256=context['lease_sha256'],utc=utc()))
        time.sleep(heartbeat_seconds)


original_check_pause=original.check_pause
original_run_bounded=original.run_bounded


def main():
    context=request_context()
    last_index=[None]
    last_pause_path=[None]
    def checked_pause(path):
        original_check_pause(path)
        last_pause_path[0]=path
        summary=context['output']/'summary.json'
        row,=json.loads(summary.read_text()) if summary.exists() else [None]
        index=0 if row is None else len(row['probes'])
        last_index[0]=index
        wait_for_leaf(context,index,path)
    def checked_run_bounded(*args,**kwargs):
        index=last_index[0]
        assert index is not None
        wait_for_leaf(context,index,last_pause_path[0])
        started=context['output']/('admission-p%02d.started.json'%index)
        with started.open('x') as stream:
            json.dump(dict(status='solver leaf started; admission consumed',seed=context['seed'],
                cpu=context['cpu'],leaf_index=index,utc=utc()),stream,indent=2)
        return original_run_bounded(*args,**kwargs)
    original.check_pause=checked_pause
    original.run_bounded=checked_run_bounded
    original.main()


if __name__=='__main__':main()
