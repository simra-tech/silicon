#!/usr/bin/env python3
"""Distinct continuation control matching two OP solves per changed code."""
import difflib
import json
from pathlib import Path
import re
from prepare_dac586_chunk_controls import ROOT,SIM,transform as one_op_transform
from run_dac586_static_control import sha
from result_directory import allocate_run


def transform(original, old_id, new_id, groups):
    one=one_op_transform(original,old_id,new_id,groups)
    assert one.count('op\nwrdata ')==2
    result=one.replace('op\nwrdata ','op\nop\nwrdata ')
    assert result.replace('op\nop\nwrdata ','op\nwrdata ')==one
    assert len(re.findall(r'^op$',result,re.M))==6
    return result


def prepare():
    old=SIM/'qualification/dac586-chunk-execution-20260923-a.json'
    packet=json.loads(old.read_text())
    assert all(sha(ROOT/name)==value for name,value in packet['source_and_reference_sha256'].items())
    prior=SIM/'qualification/dac586-chunk-qualification-20260923-a.json'
    report=json.loads(prior.read_text());assert len(report['controls'])==2
    assert all(row['status']=='failed' for row in report['controls'])
    bindings=dict(packet['source_and_reference_sha256']);bindings[str(old.relative_to(ROOT))]=sha(old)
    bindings[str(prior.relative_to(ROOT))]=sha(prior)
    preps={}
    for label in ['room','hot']:
        oldout=SIM/'qualification'/('dac586-chunk-warm-controls-20260923-a-'+label)
        prep=json.loads((oldout/'preparation.json').read_text())
        out=allocate_run(SIM,'dac586-twoop-chunk-controls-20260923-b-'+label)
        for name in ['sense.spice','trip.spice','bgr.spice','population_inventory.json']:
            (out/name).write_bytes((oldout/name).read_bytes())
        ref=SIM/'qualification'/prep['initial_reference']
        original=(ref/'dac_static.cir').read_text()
        deck=transform(original,ref.name,out.name,prep['groups']);(out/'dac_chunk.cir').write_text(deck)
        (out/'declared_difference.diff').write_text(''.join(difflib.unified_diff(
            (oldout/'dac_chunk.cir').read_text().replace(oldout.name,'@RUN@').splitlines(True),
            deck.replace(out.name,'@RUN@').splitlines(True),fromfile='preservedOneOPcontinuation',tofile='twoOPcontinuation')))
        prep.update(run=out.name,deck_sha256=sha(out/'dac_chunk.cir'),solves_per_changed_code=2,
            prior_failed_control=str(oldout.relative_to(ROOT)),
            control_schedule='Originalstatic127 twoOP, then alter128/twoOP, restore127/twoOP; same full11512/27 and exact12column static overlap gates.',
            scope='Distinct twoOP continuation qualification; prior oneOP strict failures retained. No tolerance substitution, population or dynamic settling claim.')
        prep['bindings_sha256'][str((oldout/'preparation.json').relative_to(ROOT))]=sha(oldout/'preparation.json')
        (out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n')
        preps[str((out/'preparation.json').relative_to(ROOT))]=sha(out/'preparation.json')
    for name in ['prepare_dac586_twoop_chunk.py','run_dac586_twoop_chunk.py','test_dac586_twoop_chunk.py']:
        bindings[str((SIM/name).relative_to(ROOT))]=sha(SIM/name)
    result=dict(packet,prefix='dac586-twoop-chunk-controls-20260923-b',preparations_sha256=preps,
        source_and_reference_sha256=bindings,status='prepared twoOP control; simulator not run')
    dest=SIM/'qualification/dac586-twoop-chunk-execution-20260923-b.json';assert not dest.exists()
    dest.write_text(json.dumps(result,indent=2)+'\n');print(sha(dest))


if __name__=='__main__':prepare()
