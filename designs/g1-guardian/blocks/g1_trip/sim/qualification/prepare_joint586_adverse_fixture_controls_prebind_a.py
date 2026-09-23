#!/usr/bin/env python3
"""Prepare six required owncorner rail/true-CM controls; never launch."""
import argparse
import difflib
import json
from pathlib import Path
from prepare_joint586_adverse import CONDITIONS, SIM, ROOT, REFERENCE, transform_fixture, sha
from prepare_joint586_adverse_transients import phases, append_shn
from result_directory import allocate_run

LABELS = ['low_cold_cm0','low_hot_cm0','high_cold_cm0','high_hot_cm0','room_cm_low','room_cm_high']


def fixture(original, run_id, corner, seed, condition):
    label, temp, vdda, vdd, cm = condition
    assert label in LABELS and cm is not None
    body, changes = transform_fixture(original, corner, vdda, vdd, cm)
    return append_shn(phases(body, REFERENCE, run_id, seed, [temp]))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corner',choices=['slow','fast'],required=True)
    p.add_argument('--campaign-id',required=True)
    p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--op-audit',type=Path,required=True)
    p.add_argument('--transient-packet',type=Path,required=True)
    a=p.parse_args();assert '/' not in a.campaign_id
    contract=json.loads(a.contract.read_text());op_audit=json.loads(a.op_audit.read_text())
    assert op_audit['status']=='passed strict owncorner OP qualification' and op_audit['corner']==a.corner
    assert op_audit['contract_sha256']==sha(a.contract) and all(op_audit['checks'].values())
    trans=json.loads(a.transient_packet.read_text());assert trans['corner']==a.corner
    assert trans['contract_sha256']==sha(a.contract) and trans['op_audit_sha256']==sha(a.op_audit)
    opcase,=[c for c in contract['op_controls'] if c['corner']==a.corner and c['label']=='return']
    op=(ROOT/opcase['deck']).parent;oprow,=json.loads((op/'summary.json').read_text())
    assert all(sha(op/n)==v for n,v in op_audit['receipts_sha256']['return'].items())
    ref=SIM/'qualification'/REFERENCE;original=(ref/'population_transient.cir').read_text()
    refprep=json.loads((ref/'preparation.json').read_text())
    output=SIM/'qualification'/(a.campaign_id+'.json');assert not output.exists()
    rows=[]
    for condition in CONDITIONS:
        if condition[0] not in LABELS:continue
        label,temp,vdda,vdd,cm=condition;run_id=a.campaign_id+'-'+label
        out=allocate_run(SIM,run_id)
        for name in opcase['source_hashes']:(out/name).write_bytes((op/name).read_bytes())
        (out/'population_inventory.json').write_bytes((ref/'population_inventory.json').read_bytes())
        deck=fixture(original,run_id,a.corner,opcase['seed'],condition)
        (out/'population_transient.cir').write_text(deck)
        (out/'declared_fixture_difference.diff').write_text(''.join(difflib.unified_diff(
            original.replace(REFERENCE,'@RUN@').splitlines(True),deck.replace(run_id,'@RUN@').splitlines(True),
            fromfile='qualifiedTypical',tofile=a.corner+'-'+label)))
        phase=next(r for r in oprow['phases'] if r['temperature_C']==temp)
        bound=[a.contract,a.op_audit,a.transient_packet,op/'summary.json',op/'provenance.json',
            ref/'population_transient.cir',ref/'preparation.json',Path(__file__),SIM/'run_joint586_adverse_fixture_control.py']
        bindings={str(q.absolute().relative_to(ROOT)):sha(q) for q in bound}
        prep=dict(run=run_id,corner=a.corner,label=label,condition=list(condition),seed=opcase['seed'],
            deck_sha256=sha(out/'population_transient.cir'),source_hashes=opcase['source_hashes'],
            inventory_sha256=contract['inventory_sha256'],expected_vector=phase['parameters_before'],
            op_reference=str(op.relative_to(ROOT)),groups=contract['groups'],expected_runtime_identity=contract['expected_runtime_identity'],
            prospective_sampling=refprep['prospective_sampling'],live_bindings_sha256=bindings,
            transient_packet=str(a.transient_packet.absolute().relative_to(ROOT)),watchdog_s=1200,columns=19,
            physical_scope=contract['physical_scope'],
            scope='Same owncorner control draw, fixed135/151 codes and25mV differential. Explicit rails/temperature/trueCM only; clock/codeHIGH tracks VDD, original0.6Vactual+legacy20ns/1.02us criteria unchanged. All11512+27 exact vs ownOP phase. ActualSHP/SHN observed; no recalibration, population or physicaladoption.')
        (out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n')
        rows.append(dict(run=run_id,label=label,preparation_sha256=sha(out/'preparation.json'),deck_sha256=prep['deck_sha256']))
    packet=dict(status='not run; six required fixture controls prepared',corner=a.corner,cases=rows,
        required_transient_packet_sha256=sha(a.transient_packet),contract_sha256=sha(a.contract),
        prospective_gate='Own ten-control TRANS audit including exactSHN19 original18 parity must PASS before any fixture control launch; six fullparameter/finitewave/actualinput/sampling gates before population.',
        estimated_maximum_bulk_GiB=.30,maximum_total_cpu_s=7200,no_population_release=True)
    output.write_text(json.dumps(packet,indent=2)+'\n');print(str(output.relative_to(ROOT)),sha(output))


if __name__=='__main__':main()
