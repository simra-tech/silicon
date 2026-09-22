#!/usr/bin/env python3
"""Read-only independent endpoint, prefix, inventory and warning-phase receipt."""
import hashlib
import json
import math
from pathlib import Path
from bgr_prefix_parity import compare_prefix_waves
from analyze_bgr_prefix_trajectories import initial_warning_phases
from wave_archive import open_wave, wave_sha

SIM = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    run = SIM / 'qualification/joint-bgr586-fullhot1200s-20260922-a'
    output = SIM.parent / 'reports/resume-server-20260922/joint-bgr586-fullhot1200s-audit.json'
    assert not output.exists()
    result, = json.loads((run / 'summary.json').read_text())
    prep = json.loads((run / 'preparation.json').read_text())
    assert result['controlled_substitution_status'] == 'passed comparison contract'
    wave = run / 'hard_+0mV.dat'
    with open_wave(wave) as stream:
        lines = stream.readlines()
    rows = [list(map(float, line.split())) for line in lines[1:]]
    assert len(lines[0].split()) == 18 and all(len(r) == 18 and all(math.isfinite(v) for v in r) for r in rows)
    assert rows[0][0] == 0 and abs(rows[-1][0] - 1.02e-6) < 1e-18
    assert all(a[0] < b[0] for a, b in zip(rows, rows[1:]))
    parity = compare_prefix_waves(SIM / 'qualification' / prep['prefix_reference_run'] / 'hard_+0mV.dat', wave)
    assert parity == result['strict_200ns_prefix_parity'] and parity['status'].startswith('passed')
    groups = result['parameter_audit']['ordered_parameter_groups']
    baseline, = json.loads((SIM / 'qualification' / prep['required_baseline_op_run'] / 'summary.json').read_text())
    expected_non = baseline['ordered_parameter_groups']['NON_BGR_ALL']
    assert len(expected_non) == 8670
    assert groups['NON_BGR_BEFORE'] == groups['NON_BGR_AFTER'] == expected_non
    assert groups['BGR_BEFORE'] == groups['BGR_AFTER']
    assert len(groups['BGR_BEFORE']) == 2842
    assert [v for k, v in groups['BGR_BEFORE']] == prep['candidate2842_nominal_expected']
    assert all(result['parameter_audit']['checks'].values())
    comparators = result['wave_analysis']['comparators']
    assert set(comparators) == {'soft', 'hard'}
    for row in comparators.values():
        assert row['measured_edge_decision'] is False and row['legacy_phase_decision'] is False
        assert len(row['measured_edge_sample_times_s']) == 3 and row['sampling_policies_agree']
    warnings = initial_warning_phases((run / 'run.log').read_text())
    audit = dict(status='passed completed fullhot diagnostic audit', run=run.name, wall_s=result['wall_s'],
                 summary_sha256=sha(run / 'summary.json'), log_sha256=sha(run / 'run.log'),
                 decoded_wave_sha256=wave_sha(wave), row_count=len(rows), columns=18,
                 interval_s=[rows[0][0], rows[-1][0]], strict_prefix=parity, parameter_checks=result['parameter_audit']['checks'],
                 original_late_comparators=comparators, warning_phases=warnings, raw_warning_array_count=len(result['warning_lines']),
                 script_sha256=sha(Path(__file__)), earlier600s_timeout='failed; retained', earlier219ns_fixture='failed; retained',
                 calibration_population_and_physical_adoption='not run', scope='One nominal replacement BGR with matched non-BGR random draw; not all mismatch enabled or yield')
    output.write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps({k: v for k, v in audit.items() if k not in ('strict_prefix', 'original_late_comparators')}, indent=2))


if __name__ == '__main__':
    main()
