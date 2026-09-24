#!/usr/bin/env python3
"""One 78103 [127,127] diagnostic, 4800 s; never original-population credit."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re

from result_directory import allocate_run
from analyze_bgr_substitution_outcomes import warning_inventory
from run_nominal_clock_probe import run_bounded
import run_joint586_fast_endpoint4800_diagnostic as endpoint
import run_joint586_fast_nodeset_staged as original

SIM=Path(__file__).resolve().parent
ROOT=SIM.parents[4]
P=ROOT/'.private/research/verification'
PACKET=P/'joint586_fast_78103_midpoint4800_contract_20260924_r1.json'
LEASE=P/'fast78103_midpoint4800_cpu31_root_lease_20260924_r1.json'
PROOF=P/'fast78103_endpoint_entry_equivalence_20260924_r1.json'
ORIGINAL=SIM/'qualification/joint586-fast-nodeset-calibration-s78103-20260923-a'
REFERENCE=SIM/'qualification/joint586-mm-tranqual-20260922-a-enabled'
RUN_ID='joint586-fast-s78103-p02-midpoint4800-20260924-r1'
ERROR_PATTERN=r'(?im)^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse'
REQUIRED={'cpu_budget_positive','quota_growth_and_reserve','inodes_available',
          'ram_available','coordinated_CPU_reservations_fit','external_allocation_growth',
          'external_inodes'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def canonical(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def check_inherited_helpers(packet):
    contract=SIM/'qualification/joint586-fast-nodeset-staged-contract-20260923-a/contract.json'
    assert sha(contract)==packet['original_campaign_contract_sha256']
    inherited=read(contract)
    assert len(inherited['live_bindings_sha256'])==39
    assert all(sha(ROOT/name)==digest for name,digest in inherited['live_bindings_sha256'].items())
    assert sha(ROOT/'flow/run.sh')==packet['flow_run_sha256']


def future_original_deck(codes,index,original_text):
    deck=original.adverse_deck(original_text,REFERENCE.name,ORIGINAL.name,78103,
        codes,.025,original.CONDITIONS[0],'fast')
    before='qualification/'+ORIGINAL.name+'/phase0.dat'
    after='qualification/'+ORIGINAL.name+'/p%02d/phase0.dat'%index
    assert deck.count(before)==1 and deck.count('wrdata ')==1
    result=deck.replace(before,after)
    assert result.replace(after,before)==deck
    return result


def diagnostic_deck(original_deck):
    before='qualification/'+ORIGINAL.name+'/p02/phase0.dat'
    after='qualification/'+RUN_ID+'/p02/phase0.dat'
    assert original_deck.count(before)==1 and original_deck.count('wrdata ')==1
    result=original_deck.replace(before,after)
    assert result.replace(after,before)==original_deck
    return result


def render(packet):
    original_text=(REFERENCE/'population_transient.cir').read_text()
    endpoint_packet=read(endpoint.ROOT/'.private/research/verification/joint586_fast_78103_endpoint4800_contract_20260923_r2.json')
    for index,codes in ((0,[0,0]),(1,[255,255])):
        expected=future_original_deck(codes,index,original_text)
        row,=[x for x in endpoint_packet['rows'] if x['index']==index]
        assert hashlib.sha256(expected.encode()).hexdigest()==row['original_deck_sha256']
        assert expected==(ORIGINAL/('p%02d'%index)/'probe.cir').read_text()
    assert not (ORIGINAL/'p02').exists()
    expected=future_original_deck([127,127],2,original_text)
    diagnostic=diagnostic_deck(expected)
    assert hashlib.sha256(expected.encode()).hexdigest()==packet['hypothetical_original_midpoint_deck_sha256']
    assert hashlib.sha256(diagnostic.encode()).hexdigest()==packet['diagnostic_midpoint_deck_sha256']
    return diagnostic


def fresh_gate(lease,packet):
    gate_path=ROOT/lease['resource_gate_path']
    assert gate_path.parent==P and sha(gate_path)==lease['resource_gate_sha256']
    gate=read(gate_path)
    assert gate['status']=='passed' and gate['policy_version']=='20260923-owner-fixed64-v4'
    assert gate['checker_sha256']==packet['global_checker_sha256']
    assert gate['authorization_sha256']==packet['global_authorization_sha256']
    assert gate['project_cpu_budget']>=64
    assert gate['coordinated_allocation']['distinct_cpu_ceiling']==64
    assert 31 in gate['coordinated_allocation']['cpus']
    assert all(gate['checks'].get(key) is True for key in REQUIRED)
    observed=datetime.datetime.strptime(gate['utc'].replace('+00:00','Z'),'%Y-%m-%dT%H:%M:%S.%fZ')
    age=(datetime.datetime.utcnow()-observed).total_seconds()
    assert -10<=age<=120
    raw_path=ROOT/gate['raw_v4_path']
    assert raw_path.parent==P and sha(raw_path)==gate['raw_v4_sha256']
    raw=read(raw_path)
    assert raw['status']=='passed' and raw['project_cpu_budget']>=64
    assert raw['expected_growth_gib']>=.03 and raw['expected_ram_gib']>=4
    assert raw['external_growth_gib']>=.12 and raw['reserve_gib']>=16
    assert raw['external_reserve_gib']>=8
    assert all(raw['checks'].get(key) is True for key in REQUIRED)
    return gate


def validate_inputs(packet_path,packet_sha,lease_sha,image_id):
    assert packet_path==PACKET and sha(PACKET)==packet_sha
    packet=read(PACKET);lease=read(LEASE)
    assert packet['status']=='PREPARED ONLY; one midpoint diagnostic, no population credit'
    assert packet['seed']==78103 and packet['codes']==[127,127]
    assert packet['run_id']==RUN_ID and packet['watchdog_s']==4800
    assert packet['cpu_candidate']==31 and packet['population_credit'] is False
    assert packet['midpoint_runner_sha256']==sha(Path(__file__))
    assert packet['original_runner_sha256']==sha(Path(original.__file__))
    assert packet['endpoint_runner_sha256']==sha(Path(endpoint.__file__))
    assert packet['original_provenance_sha256']==sha(ORIGINAL/'provenance.json')
    assert packet['reference_preparation_sha256']==sha(REFERENCE/'preparation.json')
    assert packet['reference_deck_sha256']==sha(REFERENCE/'population_transient.cir')
    assert all(sha(ORIGINAL/name)==value for name,value in packet['original_source_hashes'].items())
    assert packet['endpoint_equivalence_proof_sha256']==sha(PROOF)
    assert packet['endpoint_equivalence_source_sha256']==sha(P/'prove_fast78103_endpoint_entry_equivalence_r1.py')
    assert packet['endpoint_audit_sha256']==sha(P/'fast78103_endpoint4800_saved_audit_20260924_r1.json')
    assert packet['endpoint_terminal_sha256']==sha(P/'fast78103_endpoint4800_terminal_20260924_r1.json')
    assert packet['global_checker_sha256']==sha(P/'check_resources_v4_night_samecore_global_r1.py')
    assert packet['global_authorization_sha256']==sha(P/'fixed64_night_samecore_global_authorization_20260924_r1.json')
    check_inherited_helpers(packet)
    assert packet['image_id']==image_id=='sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
    proof=read(PROOF)
    assert proof['status']=='passed saved-only endpoint-to-original-entry semantics; midpoint not run'
    assert proof['next_required_codes']==[127,127] and proof['population_credit'] is False
    assert canonical(proof['entries'])==packet['endpoint_entries_canonical_sha256']
    assert sha(LEASE)==lease_sha and lease['status']=='ROOT authorized one 78103 midpoint4800 diagnostic on returned CPU31'
    assert lease['cpu']==31 and lease['packet_sha256']==packet_sha
    assert lease['cpu31_return_review_sha256']==sha(P/'fast78103_endpoint_cpu31_return_root_review_20260924_r1.json')
    assert lease['cpu31_return_candidate_sha256']==sha(P/'fast78103_endpoint_cpu31_return_candidate_20260924_r1.json')
    assert len(os.sched_getaffinity(0))==1 and 31 in os.sched_getaffinity(0)
    fresh_gate(lease,packet)
    prep=read(REFERENCE/'preparation.json')
    assert prep['expected_runtime_identity']==endpoint.runtime_matches(image_id)
    assert all(sha(REFERENCE/name)==digest for name,digest in prep['source_hashes'].items())
    assert sha(REFERENCE/'population_inventory.json')==prep['inventory_sha256']
    assert not (SIM/'qualification'/RUN_ID).exists()
    return packet,render(packet),prep


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet-sha256',required=True)
    parser.add_argument('--lease-sha256',required=True)
    parser.add_argument('--image-id',required=True)
    args=parser.parse_args()
    packet,deck,prep=validate_inputs(PACKET,args.packet_sha256,args.lease_sha256,args.image_id)
    endpoint_packet=read(P/'joint586_fast_78103_endpoint4800_contract_20260923_r2.json')
    _,vector,_=endpoint.verify_input(endpoint_packet,endpoint_packet['rows'][0])
    out=allocate_run(SIM,RUN_ID)
    leaf=out/'p02';leaf.mkdir()
    (leaf/'probe.cir').write_text(deck)
    assert sha(leaf/'probe.cir')==packet['diagnostic_midpoint_deck_sha256']
    summary=dict(status='running one midpoint diagnostic only',seed=78103,codes=[127,127],
        run_id=RUN_ID,packet_sha256=args.packet_sha256,lease_sha256=args.lease_sha256,
        original_run_id=ORIGINAL.name,endpoint_equivalence_proof_sha256=sha(PROOF),
        original_1200s_failures_retained=True,population_credit=False,
        source_deck_delta='single wrdata target path only',watchdog_s=4800)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (leaf/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str((leaf/'probe.cir').relative_to(SIM))],
            stream,leaf/'run.json',4800,cwd=SIM,interval_s=1)
    summary['runtime']=state
    try:
        check_inherited_helpers(packet)
        assert state['status']=='completed' and state['returncode']==0
        log=(leaf/'run.log').read_text()
        assert not [line for line in log.splitlines() if re.search(ERROR_PATTERN,line)]
        observation=endpoint.audit_result(leaf/'run.log',leaf/'phase0.dat',vector,prep)
        warnings=warning_inventory(log)
        summary.update(observation=observation,warnings=warnings,
            status='passed exact-input midpoint diagnostic; no calibration or population credit')
    except (AssertionError,ValueError,OSError,KeyError,IndexError) as exc:
        summary.update(status='failed midpoint diagnostic; no population credit',analysis_error=repr(exc))
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({key:value for key,value in summary.items() if key not in ('observation','runtime','warnings')},indent=2))
    if not summary['status'].startswith('passed'):
        raise SystemExit(1)


if __name__=='__main__':
    main()
