#!/usr/bin/env python3
"""Scheduling-only overnight adapter for the unchanged fixed300 T2F runner.

Each of four independent solver leaves parks after deck creation but before the
original 600 s watchdog. No original electrical command or criterion changes.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import run_586_calibration_sample as original

RUNNER_SHA = 'baddb21f4ad6b841c80848df3a185a63da178ecdaad7f8191a886b097045570f'
POLICY = '20260923-owner-overnight10reserve-v5'
START = datetime.datetime(2026, 9, 23, 20, 27, 13, tzinfo=datetime.timezone.utc)
END = datetime.datetime(2026, 9, 24, 6, 27, 13, tzinfo=datetime.timezone.utc)
REPLACEMENT_REL = '.private/research/verification/t2f586_overnight16_replacement_authority_20260924_r1.json'
REQUIRED = {'cpu_budget_positive', 'quota_growth_and_reserve', 'inodes_available',
            'ram_available', 'coordinated_CPU_reservations_fit',
            'external_allocation_growth', 'external_inodes',
            'overnight_window_active', 'overnight_ledger_activated'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def age_seconds(stamp):
    when = datetime.datetime.strptime(stamp.replace('+00:00', 'Z'), '%Y-%m-%dT%H:%M:%S.%fZ')
    return (datetime.datetime.utcnow()-when).total_seconds()


def relative(path):
    result = Path(path)
    assert not result.is_absolute() and '..' not in result.parts
    return result


def context():
    args = sys.argv[1:]
    run_id = args[args.index('--run-id')+1]
    seed = int(args[args.index('--seed')+1])
    cpu = int(os.environ['G1_CPUSET'])
    lease_path = original.ROOT/relative(os.environ['G1_T2F_OVERNIGHT_LEASE_REL'])
    lease_sha = os.environ['G1_T2F_OVERNIGHT_LEASE_SHA256']
    assert sha(Path(original.__file__)) == RUNNER_SHA
    assert sha(lease_path) == lease_sha
    lease = json.loads(lease_path.read_text())
    assert lease['status'] == 'ROOT authorized T2F overnight leaf admission'
    assert cpu in lease['cpus'] and lease['target'] == 't2f586_typical_fixed300'
    assert lease['adapter_sha256'] == sha(Path(__file__))
    return dict(run_id=run_id, seed=seed, cpu=cpu, lease_path=lease_path,
                lease_sha256=lease_sha, lease=lease, out=original.HERE/'runs'/run_id)


def permit_valid(grant, request_path, ctx, index, max_age=45):
    assert grant['request_sha256'] == sha(request_path)
    assert grant['lease_sha256'] == ctx['lease_sha256']
    assert grant['run_id'] == ctx['run_id'] and grant['seed'] == ctx['seed']
    assert grant['cpu'] == ctx['cpu'] and grant['leaf_index'] == index
    assert sha(ctx['lease_path']) == ctx['lease_sha256']
    authority_path = original.ROOT/relative(grant['authority_path'])
    assert sha(authority_path) == grant['authority_sha256']
    authority = json.loads(authority_path.read_text())
    if grant['authority_sha256'] == ctx['lease_sha256']:
        assert authority_path == ctx['lease_path']
        assert authority['status'] == 'ROOT authorized T2F overnight leaf admission'
        if (original.ROOT/REPLACEMENT_REL).exists():
            return False
    else:
        assert authority_path == original.ROOT/REPLACEMENT_REL
        assert authority['status'] == 'ROOT authorized T2F replacement leaf admission'
        assert authority['previous_lease_sha256'] == ctx['lease_sha256']
        assert authority['no_future_prior_authority_launches'] is True
        assert authority['no_new_sample_claims'] is True
    assert ctx['cpu'] in authority['cpus']
    gate_path = original.ROOT/relative(grant['gate_path'])
    assert sha(gate_path) == grant['gate_sha256']
    gate = json.loads(gate_path.read_text())
    assert gate['status'] == 'passed' and gate['policy_version'] == authority['policy_version']
    if gate['policy_version'] == POLICY:
        now = datetime.datetime.now(datetime.timezone.utc)
        if not START <= now < END:
            return False
        assert gate['window_status'] == 'active overnight CPU loan window'
        required = REQUIRED
    else:
        assert grant['authority_sha256'] != ctx['lease_sha256']
        assert gate['policy_version'] == '20260923-owner-fixed64-v4'
        required = REQUIRED-{'overnight_window_active','overnight_ledger_activated'}
    assert all(gate['checks'].get(key) is True for key in required)
    assert all(gate[key] == authority[key] for key in
               ('activation_sha256', 'checker_sha256', 'ledger_sha256'))
    allocation = gate['coordinated_allocation']
    assert ctx['cpu'] in allocation['cpus']
    if gate['policy_version'] == POLICY:
        assert ctx['cpu'] in allocation['active_additional_reservations']
    assert gate['project_cpu_budget'] >= allocation['distinct_cpu_ceiling']
    if not (0 <= age_seconds(gate['utc']) <= max_age and
            0 <= age_seconds(grant['issued_utc']) <= max_age):
        return False
    return True


def heartbeat(path, ctx, index):
    value = dict(status='parked before next solver leaf; no solver child',
                 run_id=ctx['run_id'], seed=ctx['seed'], cpu=ctx['cpu'],
                 leaf_index=index, lease_sha256=ctx['lease_sha256'],
                 utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    pending = path.with_name(path.name+'.pending')
    pending.write_text(json.dumps(value, indent=2)+'\n')
    os.replace(str(pending), str(path))


def wait_for_leaf(ctx, index):
    out = ctx['out']
    request = out/('admission-p%02d.request.json' % index)
    grant_path = out/('admission-p%02d.grant.json' % index)
    if not request.exists():
        with request.open('x') as stream:
            json.dump(dict(status='waiting host admission; no solver child',
                run_id=ctx['run_id'], seed=ctx['seed'], cpu=ctx['cpu'],
                leaf_index=index, lease_sha256=ctx['lease_sha256'],
                runner_sha256=RUNNER_SHA), stream, indent=2)
    while True:
        assert sha(ctx['lease_path']) == ctx['lease_sha256']
        if grant_path.exists() and permit_valid(json.loads(grant_path.read_text()), request, ctx, index):
            return request, grant_path
        heartbeat(out/('admission-p%02d.heartbeat.json' % index), ctx, index)
        time.sleep(15)


original_run_bounded = original.run_bounded


def main():
    ctx = context()
    def admitted_run_bounded(*args, **kwargs):
        leaf = Path(kwargs['cwd'])
        assert leaf.parent.resolve() == ctx['out'].resolve()
        assert leaf.name in ('p00', 'p01', 'p02', 'p03')
        assert args[0] == ['ngspice', '-b', 'probe.cir'] and args[3] == 600
        index = int(leaf.name[1:])
        request, grant = wait_for_leaf(ctx, index)
        consumed = ctx['out']/('admission-p%02d.consumed.json' % index)
        with consumed.open('x') as stream:
            json.dump(dict(status='fresh permit consumed immediately before original solver call',
                run_id=ctx['run_id'],seed=ctx['seed'],cpu=ctx['cpu'],leaf_index=index,
                request_sha256=sha(request),grant_sha256=sha(grant),
                utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),stream,indent=2)
        return original_run_bounded(*args, **kwargs)
    original.run_bounded = admitted_run_bounded
    original.main()


if __name__ == '__main__':
    main()
