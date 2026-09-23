#!/usr/bin/env python3
"""Prepare one separate900s same-input recovery; original600s failure untouched."""
import json
from pathlib import Path
from prepare_586_nominal_intermediates import HERE, ROOT, sha
from result_directory import allocate_run


def main():
    original = HERE/'runs/t2f586-nominal-intermediate-20260922-a-t75'
    summary, = json.loads((original/'summary.json').read_text())
    assert summary['status'] == 'failed' and summary['runtime']['status'] == 'timeout'
    assert summary['runtime']['timeout_s'] == 600 and not summary['errors']
    assert summary['runtime']['last_reported_sim_time_s'] == 2.74819e-5
    audit_path = HERE/'t2f586-nominal-intermediates-analysis-20260922.json'
    audit = json.loads(audit_path.read_text())
    record, = [r for r in audit['records'] if r['label'] == 't75']
    assert record['full3180_before_status'] == 'passed exact nominal realization'
    assert record['warning_lines_after_initial_transient'] == 0
    run_id = 't2f586-nominal75-recovery900-20260922-b'
    packet_path = HERE/(run_id+'.json')
    assert not packet_path.exists()
    out = allocate_run(HERE.parent, run_id, relative_parent='qualification/runs')
    prep = json.loads((original/'preparation.json').read_text())
    for name in ['bgr.spice', 't2f.spice', '.spiceinit', 'probe.cir', 'declared_fixture_difference.diff']:
        (out/name).write_bytes((original/name).read_bytes())
        assert sha(out/name) == sha(original/name)
    prep.update(run_id=run_id, watchdog_s=900,
        status='not run; distinct proposed900s watchdog-only recovery awaiting coordinator approval',
        original_failure=dict(run_id=original.name, summary_sha256=sha(original/'summary.json'),
            log_sha256=sha(original/'run.log'), audit_sha256=sha(audit_path), original_watchdog_s=600,
            progress_at_timeout_s=2.74819e-5, original_wave_prefix_comparison='not run; original exported wave absent'),
        recovery_scope='Only hostwatchdog600→900s and newrunID; SPICEdeck/source/models/tolerances/timing/temp/outputbasenamebyteexact. One separateattempt, no retryloop. Original600sfailure retained; allfull3180BEFOREAFTER/32us/13finitevectors/originalfrozen±2C remain mandatory.')
    prep['prior_preparation_failure'] = dict(run_id='t2f586-nominal75-recovery900-20260922-a',
        status='not run; preparation failed relative __file__ binding before packet/log/simulation; copied inputs retained')
    for path in [original/'summary.json', original/'run.log', original/'preparation.json', audit_path, Path(__file__).resolve()]:
        prep['live_bindings_sha256'][str(path.relative_to(ROOT))] = sha(path)
    (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
    packet = dict(status='not run; proposed watchdog-only recovery', cases=[dict(run_id=run_id, label='t75',
        temperature_C=75, preparation_sha256=sha(out/'preparation.json'), deck_sha256=sha(out/'probe.cir'))],
        nominal_analysis_sha256=prep['nominal_analysis_sha256'], expected_external_growth_GiB=.03,
        watchdog_s=900, original_failure_run=original.name)
    packet_path.write_text(json.dumps(packet, indent=2)+'\n')
    print(json.dumps(dict(packet=str(packet_path.relative_to(ROOT)), packet_sha256=sha(packet_path),
        deck_sha256=sha(out/'probe.cir'), original_deck_exact=sha(out/'probe.cir') == sha(original/'probe.cir')), indent=2))


if __name__ == '__main__':
    main()
