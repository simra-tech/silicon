#!/usr/bin/env python3
"""Prepare one exact-input 900 s recovery; retain the original 600 s failure."""
import json
from pathlib import Path
from prepare_586_adverse_controls import HERE, ROOT, sha
from result_directory import allocate_run
from run_bgr_substitution_draw_audit import read_group


def main():
    original = HERE/'runs/t2f586-adverse-controls-20260922-a-fast-highhot'
    row, = json.loads((original/'summary.json').read_text())
    prep = json.loads((original/'preparation.json').read_text())
    assert row['control_status'] == 'failed' and row['runtime']['status'] == 'timeout'
    assert row['runtime']['timeout_s'] == 600 and not row['errors']
    log = (original/'run.log').read_text()
    before = {tag: read_group(log, tag+'_BEFORE', keys) for tag, keys in prep['groups'].items()}
    reference = HERE/'runs/t2f586-adverse-controls-20260922-a-fast-cal25/summary.json'
    nominal, = json.loads(reference.read_text())
    assert sum(map(len, before.values())) == 3180
    assert before == nominal['parameters_before']
    run_id = 't2f586-fast-highhot-recovery900-20260923-a'
    packet = HERE/(run_id+'.json')
    assert not packet.exists()
    out = allocate_run(HERE.parent, run_id, relative_parent='qualification/runs')
    for name in ['bgr.spice', 't2f.spice', '.spiceinit', 'probe.cir',
                 'declared_fixture_difference.diff', 'declared_bgr_source_difference.diff']:
        (out/name).write_bytes((original/name).read_bytes())
        assert sha(out/name) == sha(original/name)
    prep.update(run_id=run_id, watchdog_s=900,
        status='not run; one separately authorized exact-input watchdog recovery',
        original_failure=dict(run_id=original.name, summary_sha256=sha(original/'summary.json'),
            log_sha256=sha(original/'run.log'), watchdog_s=600,
            progress_at_timeout_s=row['runtime']['last_reported_sim_time_s'],
            full3180_before_exact_same_corner=True,
            wave_prefix_comparison='not run; original exported waveform absent'),
        recovery_scope='Only host watchdog600 to900s and fresh directory. SPICE deck, sources, model cards, solver, timing, temperature, rails and output basename byte exact. No further automatic retry; original failure retained.')
    for p in [original/'summary.json', original/'run.log', original/'preparation.json', reference, Path(__file__).resolve()]:
        prep['live_bindings_sha256'][str(p.relative_to(ROOT))] = sha(p)
    (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
    payload = dict(status='not run; separately authorized exact-input recovery', cases=[dict(
        run_id=run_id, corner='fast', label='highhot', temperature_C=125, VDDA_V=3.6, VDD_V=1.32,
        preparation_sha256=sha(out/'preparation.json'), deck_sha256=sha(out/'probe.cir'))],
        original_failure_run=original.name, watchdog_s=900, expected_external_growth_GiB=.03)
    packet.write_text(json.dumps(payload, indent=2)+'\n')
    print(json.dumps(dict(packet=str(packet.relative_to(ROOT)), packet_sha256=sha(packet),
                         deck_sha256=sha(out/'probe.cir'), original_deck_exact=True), indent=2))


if __name__ == '__main__':
    main()
