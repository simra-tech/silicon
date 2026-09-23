#!/usr/bin/env python3
"""One exact original32us KLU diagnostic; retain original SPARSE failure."""
import difflib
import json
from pathlib import Path
from prepare_586_fast76002_solver import HERE, ROOT, ORIGINAL, sha
from result_directory import allocate_run

PREFIX = HERE/'runs/t2f586-fast76002-klu2us-20260923-a'


def make_full(original):
    assert original.count('\n.control\n') == 1 and original.count('tran 5n 32u\n') == 1
    assert original.count('method=gear') == 1 and original.count('setseed 76002\n') == 1
    assert '.options klu' not in original and '.options sparse' not in original
    trial = original.replace('\n.control\n', '\n.options klu\n.control\n')
    assert trial.replace('.options klu\n', '') == original
    return trial


def main():
    run_id = 't2f586-fast76002-klu32us-20260923-a'
    packet = HERE/(run_id+'.json'); assert not packet.exists()
    prefix, = json.loads((PREFIX/'summary.json').read_text())
    assert prefix['control_status'] == 'passed waveform-only diagnostic' and prefix['full3180_status'] == 'passed'
    assert prefix['parameters_before'] == prefix['parameters_after']
    prep = json.loads((PREFIX/'preparation.json').read_text())
    assert prefix['parameters_before'] == prep['required_before3180']
    out = allocate_run(HERE.parent, run_id, relative_parent='qualification/runs')
    for name in ['bgr.spice', 't2f.spice', '.spiceinit', 'population_inventory.json']:
        assert sha(PREFIX/name) == sha(ORIGINAL/name)
        (out/name).write_bytes((ORIGINAL/name).read_bytes())
    original = (ORIGINAL/'probe.cir').read_text(); trial = make_full(original)
    (out/'probe.cir').write_text(trial)
    (out/'declared_solver_difference.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), trial.splitlines(True),
        fromfile='preservedFailed32usSparse76002', tofile='separate32usKlu76002')))
    prep.update(run_id=run_id, status='not run; prepared original32us selector-only diagnostic',
        endpoint_s=32e-6, watchdog_s=600, deck_sha256=sha(out/'probe.cir'), removed_future_commands=[],
        required_klu_prefix=PREFIX.name, required_klu_prefix_summary_sha256=sha(PREFIX/'summary.json'),
        scope='ONE original32us76002 diagnostic; sole deck addition .options klu. Original Gear/seed/reset/OP/measurements/source/model/full3180/13vectors/load/rails/timing/600s unchanged. Original SPARSE600s failure remains failed. Require full3180 exact original and qualified2usKLU, finite32us waveform/HBTVCE<=1.6/positive finite original frequency measurements. No solver adoption, replacement sample, recalibration, population release or numerical-bound substitution for exact comparison failures.')
    for path in [PREFIX/'summary.json', PREFIX/'run.log', PREFIX/'phase0.dat.gz', PREFIX/'preparation.json',
                 Path(__file__).resolve(), HERE/'run_586_fast76002_full_solver.py']:
        prep['live_bindings_sha256'][str(path.relative_to(ROOT))] = sha(path)
    (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
    result = dict(status='not run; one bounded original32us diagnostic', run_id=run_id,
        preparation_sha256=sha(out/'preparation.json'), deck_sha256=sha(out/'probe.cir'),
        original_deck_sha256=sha(ORIGINAL/'probe.cir'), inverse_selector_restores_original=True,
        watchdog_s=600, endpoint_s=32e-6, expected_external_growth_GiB=.05,
        no_population_release=True, required_prefix_summary_sha256=sha(PREFIX/'summary.json'))
    packet.write_text(json.dumps(result, indent=2)+'\n'); print(packet.relative_to(ROOT), sha(packet))


if __name__ == '__main__':
    main()
