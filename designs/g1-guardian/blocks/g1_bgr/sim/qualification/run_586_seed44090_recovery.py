#!/usr/bin/env python3
"""One exact-input44090 recovery; only wall-clock bound changes120s to240s."""
import hashlib
import json
from pathlib import Path
import re
import sys
import run_586_mc_screen as original

HERE = Path(__file__).resolve().parent
REFERENCE = HERE/'bgr586-screen80-b6-20260922-a'
LEAF = REFERENCE/'s44090'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert '--run-id' in sys.argv and '--seeds' in sys.argv
    assert sys.argv[sys.argv.index('--seeds')+1] == '44090'
    run_id = sys.argv[sys.argv.index('--run-id')+1]
    assert run_id == 'bgr586-s44090-recovery240s-20260922-a'
    failed, = [r for r in json.loads((REFERENCE/'summary.json').read_text()) if r['seed'] == 44090]
    assert failed['status'] == 'failed' and failed['watchdog_status'] == 'timeout'
    old_log = (LEAF/'run.log').read_text()
    before = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', old_log, re.M)
    manifest = json.loads((HERE/'runs/bgr_one_draw_20260922_r1/manifest.json').read_text())
    assert len(before) == 2842 and [k for k, v in before] == manifest['parameters']
    assert not (LEAF/'nominal.dat').exists(), 'Unexpected overlap requires waveform parity contract'
    bindings = {str(p.relative_to(original.ROOT)): sha(p) for p in
                [REFERENCE/'summary.json', REFERENCE/'provenance.json', LEAF/'run.log', LEAF/'run.json',
                 LEAF/'nominal.cir', LEAF/'pex_nominal.spice', LEAF/'pex_mm.spice', LEAF/'.spiceinit',
                 Path(original.__file__), Path(__file__)]}
    contract = {'reference_run': str(LEAF.relative_to(original.ROOT)), 'seed': 44090,
                'original_timeout_s': 120, 'new_timeout_s': 240, 'live_bindings_sha256': bindings,
                'deck_contract': 'Byte-exact original failed input deck, source snapshots, runtime, seed, temperature sweep and solver; only watchdog changes.',
                'waveform_overlap_status': 'not applicable: original failed process exported no waveform; no numerical prefix parity claimed',
                'parameter_overlap_contract': 'All2842 original BEFORE values must equal recovery BEFORE and AFTER',
                'scope': 'Separate recovery attempt; does not remove or reclassify original120s population failure.'}
    allocate = original.allocate_run
    bounded = original.run_bounded
    seed_deck = original.seed_deck

    def exact_deck(deck, seed):
        result = seed_deck(deck, seed)
        assert seed == 44090 and result == (LEAF/'nominal.cir').read_text()
        return result

    def allocate_with_contract(sim, name):
        assert all(sha(original.ROOT/key) == value for key, value in bindings.items())
        out = allocate(sim, name)
        (out/'recovery_contract.json').write_text(json.dumps(contract, indent=2)+'\n')
        (out/'recovery_wrapper.py').write_bytes(Path(__file__).read_bytes())
        return out

    def fixed_watchdog(command, log, state, timeout, **kwargs):
        assert timeout == 120 and command == ['ngspice', '-b', 'nominal.cir']
        leaf = kwargs['cwd']
        assert all(sha(leaf/name) == sha(LEAF/name) for name in ['nominal.cir', 'pex_nominal.spice', 'pex_mm.spice', '.spiceinit'])
        return bounded(command, log, state, 240, **kwargs)

    original.seed_deck = exact_deck
    original.allocate_run = allocate_with_contract
    original.run_bounded = fixed_watchdog
    try:
        original.main()
    except SystemExit as stopped:
        code = stopped.code
    out = HERE/run_id
    result, = json.loads((out/'summary.json').read_text())
    check = result['status'] == 'passed' and result['parameters_before'] == [list(x) for x in before] == result['parameters_after']
    report = {'recovery_status': 'passed' if check else 'failed', 'original_population_attempt_status': 'failed watchdog120s, preserved',
              'all2842_original_before_recovery_before_after_exact': check,
              'waveform_overlap_status': contract['waveform_overlap_status'],
              'recovery_summary_sha256': sha(out/'summary.json'), 'contract_sha256': sha(out/'recovery_contract.json'),
              'tc_status': result['tc_status'], 'tc_ppm_C': result.get('tc_ppm_C'), 'wall_s': result['wall_s']}
    (out/'recovery_validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)
    raise SystemExit(0 if code == 0 and check else 1)


if __name__ == '__main__':
    main()
