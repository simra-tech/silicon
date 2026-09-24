"""Saved-data-only exact binary replay, normalizing declared JSON bracket pairs."""
import argparse
import json
from pathlib import Path
from run_regenpair4_roomcal import ROOT,SIM,sha,check_packet,runtime,inspect,replay


def serialized_tree(records):
    tree=replay(records)
    for key in ['brackets','current_brackets']:
        if key in tree:
            assert set(tree[key])=={'soft','hard'}
            assert all(type(pair) is tuple and len(pair)==2 and all(type(x) is int for x in pair) for pair in tree[key].values())
            tree[key]={k:list(v) for k,v in tree[key].items()}
    return tree


def main():
    p=argparse.ArgumentParser();p.add_argument('--packet',required=True);p.add_argument('--packet-sha256',required=True);p.add_argument('--image-id',required=True);a=p.parse_args()
    packet,out=check_packet(a.packet,a.packet_sha256);observed=runtime(packet,a.image_id)
    complete=json.loads((out/'calibration_complete.json').read_text());assert complete['status']=='passed' and complete['packet_sha256']==a.packet_sha256
    provenance=json.loads((out/'provenance.json').read_text());assert provenance['runtime_identity']==observed and provenance['packet_sha256']==a.packet_sha256
    failed=ROOT/'.private/research/verification/regenpair4_roomcal_20260923_a.json'
    prior=json.loads(failed.read_text());assert prior['no_future_launches'] and prior['children'][-1]['mode']=='audit-calibration' and prior['children'][-1]['returncode']!=0
    records=[]
    for row in complete['records']:
        leaf=SIM/'qualification'/row['run'];r=inspect(leaf,packet,'p00',row['codes'])
        assert r==row==json.loads((leaf/'summary.json').read_text()) and r['parameter_audit']['parameters_before']==complete['parameters'];records.append(r)
    assert serialized_tree(records)==complete['tree']
    output=dict(status='passed',audit_revision='b exact tuple-to-JSON-list bracket representation only',auditor_sha256=sha(Path(__file__)),tests_sha256=sha(SIM/'test_regenpair4_roomcal_audit_b.py'),failed_original_host_sha256=sha(failed),failed_original_log_sha256=sha(failed.with_name('regenpair4_roomcal_audit-calibration_20260923_a.log')),calibration_sha256=sha(out/'calibration_complete.json'),packet_sha256=a.packet_sha256,leaf_count=len(records),codes=complete['tree']['fixed_residual_codes'])
    with (out/'calibration_audit.json').open('x') as stream:json.dump(output,stream,indent=2)


if __name__=='__main__':main()
