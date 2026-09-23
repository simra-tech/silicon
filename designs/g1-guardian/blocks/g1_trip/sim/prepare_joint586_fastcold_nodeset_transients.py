#!/usr/bin/env python3
"""Prepare two full original fast78001 nodeset diagnostics, without running."""
import difflib
import json
from pathlib import Path
from prepare_joint586_fastcold_nodeset import SIM, ROOT, ORIGINAL, NODES, sha, guesses
from result_directory import allocate_run

PACKET = SIM/'qualification/joint586-fastcold-nodeset-transients-contract-20260923-a.json'
OP_PACKET = SIM/'qualification/joint586-fastcold-nodeset-op-contract-20260923-b.json'


def transform(original, run_id, solver, values):
    assert solver in ['sparse', 'klu'] and list(values) == NODES
    assert '.nodeset' not in original and '.options klu' not in original
    old = 'qualification/'+ORIGINAL.name+'/phase0.dat'
    new = 'qualification/'+run_id+'/phase0.dat'
    assert original.count(old) == 1 and original.count('\n.control\n') == 1
    assert original.count('tran 0.2n 1.02u 0 0.2n\n') == 1
    assert original.count('setseed 78001\n') == 1
    added = '.nodeset '+' '.join('v('+n+')='+values[n] for n in NODES)+'\n'
    if solver == 'klu':
        added += '.options klu\n'
    result = original.replace(old, new).replace('\n.control\n', '\n'+added+'.control\n')
    assert result.replace(new, old).replace('\n'+added+'.control\n', '\n.control\n') == original
    return result, dict(added_algorithm_lines=added, original_output=old,
        fresh_output=new, exact_inverse_restores_original=True,
        transient_and_all_eight_measurements_unchanged=True)


def main():
    assert not PACKET.exists()
    prep = json.loads((ORIGINAL/'preparation.json').read_text())
    op = json.loads(OP_PACKET.read_text())
    values = guesses((ORIGINAL/'run.log').read_text())
    assert values == op['guesses_original_printed_strings']
    assert len(prep['expected_vector']) == 11512 and prep['columns'] == 19
    body = (ORIGINAL/'population_transient.cir').read_text()
    sources = {n: sha(ORIGINAL/n) for n in ['sense.spice', 'trip.spice', 'bgr.spice', 'population_inventory.json']}
    cases = []
    op_paths = [OP_PACKET]
    for oldcase in op['cases']:
        run = SIM/'qualification'/oldcase['run']
        result, = json.loads((run/'summary.json').read_text())
        assert result['status'] == 'passed finite fullparameter OP diagnostic; exact comparisons separate'
        assert not result.get('analysis_error') and not result['errors']
        op_paths += [run/n for n in ['summary.json', 'run.json', 'run.log', 'op.dat', 'provenance.json']]
    for solver in ['sparse', 'klu']:
        run = 'joint586-fastcold-nodeset-transient-'+solver+'-20260923-a'
        out = allocate_run(SIM, run)
        for name in sources:
            (out/name).write_bytes((ORIGINAL/name).read_bytes())
        deck, audit = transform(body, run, solver, values)
        (out/'population_transient.cir').write_text(deck)
        (out/'transform_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
        (out/'declared_initialization_difference.diff').write_text(''.join(difflib.unified_diff(
            body.splitlines(True), deck.splitlines(True), fromfile='originalFailedFast78001', tofile=solver+'NodesetFullTransient')))
        cases.append(dict(solver=solver, run=run, deck_sha256=sha(out/'population_transient.cir'),
            transform_sha256=sha(out/'transform_audit.json'), watchdog_s=1200))
    helpers = ['prepare_joint586_fastcold_nodeset_transients.py', 'run_joint586_fastcold_nodeset_transients.py',
        'test_joint586_fastcold_nodeset_transients.py', 'prepare_joint586_fastcold_nodeset.py',
        'run_joint586_fastcold_klu.py', 'prepare_joint586_fastcold_klu.py',
        'run_joint586_transients.py', 'run_bgr_substitution_draw_audit.py',
        'run_nominal_clock_probe.py', 'audit_joint586_adverse_transients.py',
        'analyze_bgr_substitution_outcomes.py', 'wave_archive.py', '.spiceinit']
    paths = op_paths+[SIM/n for n in helpers]+[ORIGINAL/n for n in list(sources)+[
        'population_transient.cir', 'preparation.json', 'summary.json', 'run.log', 'run.json', 'provenance.json']]
    packet = dict(status='prepared only; no transient lease', cases=cases, original=ORIGINAL.name,
        source_hashes=sources, guesses_original_printed_strings=values, original_preparation=prep,
        bindings_sha256={str(p.relative_to(ROOT)): sha(p) for p in paths},
        forecast=dict(maximum_cpu_seconds=2400, home_growth_gib=0.15, single_thread_per_leaf=True),
        scope='Two separate full1.02us fast78001 initialization diagnostics: original SPARSE plus eight canonical nodeset guesses, or same nodeset plus KLU. Original source/cards/seed/codes135,151/rails/temperature/trueCM/stimulus/timing/11512+27/19vectors/eight measurements/1200s unchanged. Only declared initialization/solver lines and fresh output paths differ. No IC/UIC/tolerance change. Original failures remain. Numerical completion, exact parameter/wave/grid and original decision sampling are separate. No new-fixture own6 qualification, fast30 release, solver adoption or physical qualification.')
    PACKET.write_text(json.dumps(packet, indent=2)+'\n')
    print(PACKET.relative_to(ROOT), sha(PACKET))


if __name__ == '__main__':
    main()
