"""Bounded original slow residual pair; only fourth TRAN argument becomes0.5ns."""
import copy
import difflib
import json
from pathlib import Path
from prepare_joint586_tmax_matrix import ROOT,SIM,sha,declared_pair
from prepare_joint586_tmax_probe import OLD
from result_directory import allocate_run

NEW='tran 0.2n 1.02u 0 0.5n\n'


def matched_transform(original,original_run,new_run,seed):
    old_output='qualification/'+original_run+'/phase0.dat';new_output='qualification/'+new_run+'/phase0.dat'
    assert seed==77101 and original.count('setseed 77101\n')==1
    assert original.count(OLD)==original.count(old_output)==1 and NEW not in original
    assert '.options klu' not in original.lower() and '.nodeset' not in original.lower()
    result=original.replace(OLD,NEW).replace(old_output,new_output)
    assert result.replace(NEW,OLD).replace(new_output,old_output)==original
    return result


def source_gate(out,original,prep):
    assert all(sha(out/n)==sha(original.parent/n)==v for n,v in prep['source_hashes'].items())
    assert sha(out/'population_inventory.json')==prep['inventory_sha256']


def main():
    oldpacket=SIM/'qualification/joint586-tmax-matrix-20260923-a.json'
    prioraudit=SIM/'qualification/joint586-tmax-matrix-audit-20260923-c.json'
    audit=json.loads(prioraudit.read_text());assert audit['numerical_passed']==6 and audit['evidence_failed']==0
    cases=[c for c in json.loads(oldpacket.read_text())['controls'] if c['seed']==77101]
    assert len(cases)==2
    entries=[json.loads((SIM/'qualification'/c['original_run']/'summary.json').read_text()) for c in cases]
    declared_pair(entries,77101);controls=[]
    for case in cases:
        previous=SIM/'qualification'/case['run_id'];prep=copy.deepcopy(json.loads((previous/'preparation.json').read_text()))
        original=SIM/'qualification'/prep['original_run'];leaf=original.name
        run='joint586-tmax-halfns-s77101-'+leaf+'-20260923-a';out=allocate_run(SIM,run)
        old=(original/'probe.cir').read_text();deck=matched_transform(old,prep['original_run'],run,77101)
        (out/'probe.cir').write_text(deck)
        for name in ['sense.spice','trip.spice','bgr.spice','population_inventory.json']:(out/name).write_bytes((original.parent/name).read_bytes())
        source_gate(out,original,prep)
        (out/'declared_tmax_difference.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),deck.splitlines(True),fromfile='original0.2ns '+leaf,tofile='fixed0.5ns diagnostic')))
        prep.update(run_id=run,deck_sha256=sha(out/'probe.cir'),scope='Original slow77101 cold24.5/25.5mV pair only. Sole fourth TRAN argument0.2ns to0.5ns; all original sources/options/seed/codes/endpoint/sampling/screens retained. Original1ns failures retained; no method/source/population adoption.')
        files=[previous/'preparation.json',oldpacket,prioraudit]+[SIM/n for n in ['prepare_joint586_tmax_halfns.py','run_joint586_tmax_halfns.py','audit_joint586_tmax_halfns.py','test_joint586_tmax_halfns.py']]
        prep['live_bindings_sha256'].update({str(f.relative_to(ROOT)):sha(f) for f in files})
        (out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n')
        controls.append(dict(run_id=run,seed=77101,original_run=prep['original_run'],preparation_sha256=sha(out/'preparation.json'),watchdog_s=1200))
    packet=dict(status='authorized bounded smaller-step pair only; no adoption',controls=controls,bindings_sha256={str(prioraudit.relative_to(ROOT)):sha(prioraudit)},expected_bulk_GiB=.12,scope='Stop this method branch if unchanged prospective consistency screen fails; no adaptive tolerance relaxation.')
    path=SIM/'qualification/joint586-tmax-halfns-20260923-a.json';assert not path.exists();path.write_text(json.dumps(packet,indent=2)+'\n');print(sha(path))


if __name__=='__main__':main()
