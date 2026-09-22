#!/usr/bin/env python3
"""Two separately archived disabled OP recoveries; only120s→300s watchdog."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import run_joint586_population_op as original
from result_directory import allocate_run
from run_bgr_substitution_draw_audit import read_group

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(reference, run_id):
    assert reference in ['joint586-mm-opqual-20260922-a-disabled', 'joint586-mm-opqual-20260922-a-disabledchanged']
    assert run_id == reference+'-recovery300s-r2'
    ref = SIM/'qualification'/reference
    row, = json.loads((ref/'summary.json').read_text())
    assert row['watchdog_status'] == 'timeout' and row['op_qualification_status'] == 'failed'
    prep = json.loads((ref/'preparation.json').read_text())
    assert not prep['mismatch_enabled'] and prep['planning']['watchdog_s'] == 120
    before = []
    for tag in ['NON_BGR', 'BGR']:
        before += read_group((ref/'run.log').read_text(), 'P0_'+tag+'_BEFORE', prep['prospective_groups'][tag])
    assert len(before) == 11512 and not (ref/'op0.dat').exists()
    old = (ref/'population_op.cir').read_text()
    new = old.replace(reference, run_id)
    assert new.replace(run_id, reference) == old
    extra = {str(path.relative_to(ROOT)): sha(path) for path in
             [ref/'summary.json', ref/'provenance.json', ref/'run.log', ref/'run.json', ref/'population_op.cir',
              ref/'preparation.json', Path(__file__).resolve()]}
    out = allocate_run(SIM, run_id)
    for name in ['sense.spice', 'trip.spice', 'bgr.spice', 'population_inventory.json']:
        (out/name).write_bytes((ref/name).read_bytes())
    (out/'population_op.cir').write_text(new)
    prep['live_bindings_sha256'].update(extra)
    prep.update(run=run_id, deck_sha256=sha(out/'population_op.cir'), recovery_actual_watchdog_s=300)
    (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
    contract = {'reference_run': reference, 'new_run': run_id, 'original120s_status': 'failed timeout, immutable',
                'new_watchdog_s': 300, 'reference_full11512_before': before,
                'allowed_difference': 'Output-run paths and wall-clock watchdog only; source/deck/model/seed/codes/OP/query/settings unchanged.',
                'prefix_waveform_parity': 'not applicable: original completed first OP/BEFORE queries but never exported op0.dat',
                'required_overlap': 'Original11512 BEFORE equals recovery BEFORE and AFTER exactly',
                'live_reference_hashes': extra}
    (out/'recovery_contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    (out/'recovery_wrapper.py').write_text(Path(__file__).read_text())
    print(json.dumps({'prepared': run_id, 'deck_sha256': prep['deck_sha256'], 'new_watchdog_s': 300}))


def run():
    run_id = sys.argv[sys.argv.index('--run-id')+1]
    out = SIM/'qualification'/run_id
    contract = json.loads((out/'recovery_contract.json').read_text())
    assert run_id == contract['reference_run']+'-recovery300s-r2'
    assert contract['new_watchdog_s'] == 300
    assert all(sha(ROOT/path) == value for path, value in contract['live_reference_hashes'].items())
    reference = SIM/'qualification'/contract['reference_run']
    assert (out/'population_op.cir').read_text().replace(run_id, reference.name) == (reference/'population_op.cir').read_text()
    bounded = original.run_bounded

    def new_watchdog(command, stream, state, timeout, **kwargs):
        assert timeout == 120
        return bounded(command, stream, state, 300, **kwargs)

    original.run_bounded = new_watchdog
    try:
        original.main()
    except SystemExit as stopped:
        code = stopped.code
    result, = json.loads((out/'summary.json').read_text())
    complete = result['op_qualification_status'] == 'passed'
    exact = complete and result['phases'][0]['parameters_before'] == result['phases'][0]['parameters_after'] == contract['reference_full11512_before']
    report = {'recovery_status': 'passed' if exact else 'failed or incomplete', 'original120s_status': 'failed preserved',
              'original11512_before_recovery_before_after_exact': exact,
              'waveform_overlap_status': contract['prefix_waveform_parity'],
              'new_watchdog_s': 300, 'wall_s': result['wall_s'], 'summary_sha256': sha(out/'summary.json'),
              'contract_sha256': sha(out/'recovery_contract.json')}
    (out/'recovery_validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)
    raise SystemExit(0 if code == 0 and exact else 1)


if __name__ == '__main__':
    if '--prepare-reference' in sys.argv:
        p = argparse.ArgumentParser(description=__doc__)
        p.add_argument('--prepare-reference', required=True)
        p.add_argument('--run-id', required=True)
        a = p.parse_args()
        prepare(a.prepare_reference, a.run_id)
    else:
        run()
