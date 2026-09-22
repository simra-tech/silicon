#!/usr/bin/env python3
"""Read-only audit of the single completed same-input73034 recovery attempt."""
import argparse
import collections
import json
from pathlib import Path
import re
from prepare_joint586_leaf_recovery import ORIGINAL, SIM, ROOT, transform
from run_joint586_calibration import sha
from run_bgr_substitution_draw_audit import read_group


def audit(run_id):
    run = SIM/'qualification'/run_id
    prep = json.loads((run/'preparation.json').read_text())
    state = json.loads((run/'run.json').read_text())
    summary, = json.loads((run/'summary.json').read_text())
    provenance = json.loads((run/'provenance.json').read_text())
    original = SIM/'qualification'/ORIGINAL
    assert state['status'] != 'running' and prep['watchdog_s'] == state['timeout_s'] == 2400
    assert all(provenance['input_checks'].values())
    assert all(sha(ROOT/name) == value for name, value in prep['bindings_sha256'].items())
    assert all(sha(original/name) == value for name, value in prep['source_hashes'].items())
    assert (run/'probe.cir').read_text() == transform((original/'p09/probe.cir').read_text(), run_id)
    log = (run/'run.log').read_text()
    before = read_group(log, 'NON_BGR_BEFORE', prep['groups']['NON_BGR'])+read_group(log, 'BGR_BEFORE', prep['groups']['BGR'])
    assert len(before) == 11512 and before == prep['expected11512']
    lines = log.splitlines()
    initial = next(i for i, line in enumerate(lines) if 'Initial Transient Solution' in line)
    warnings = [(i, line) for i, line in enumerate(lines) if 'WARNING:' in line or 'temperature limiting function received NaN' in line]
    families = collections.Counter('temperature-limiter-NaN' if 'temperature limiting' in line else
        re.sub(r'\s+from instance.*', '', line.strip()) for i, line in warnings)
    times = [float(value) for value in re.findall(r'Reference value\s*:\s*([-+0-9.eE]+)', log)]
    buckets = collections.Counter(int(t/1e-7) for t in times)
    result = dict(status='passed read-only input/BEFORE audit; numerical outcome retained separately',
        logical_run=str(run.relative_to(ROOT)), runtime=state, recovery_outcome=summary['status'],
        original_sample_status='failed calibration; original1200s attempt unchanged',
        original_input_match_except_output_path=True, full11512_BEFORE_exact_original=True,
        legacy27_subset_in_full_BEFORE_exact=all(k in dict(before) for k in prep['groups']['LEGACY27']),
        complete_after_queries_present='NON_BGR_AFTER_END' in log and 'BGR_AFTER_END' in log,
        completed_wave_present=bool(list(run.glob('phase0.dat*'))),
        original_prefix_wave_comparison='not run; original1200s attempt exported no waveform',
        warning_counts=dict(before_initial_transient=sum(i < initial for i, line in warnings),
                            after_initial_transient=sum(i >= initial for i, line in warnings)),
        warning_families=dict(families), progress=dict(reference_records=len(times),
            last_reference_s=times[-1] if times else None, maximum_reference_s=max(times) if times else None,
            records_by_100ns_interval={str(k): v for k, v in sorted(buckets.items())}),
        artifact_sha256={n: sha(run/n) for n in ['summary.json', 'provenance.json', 'preparation.json', 'run.json', 'run.log', 'probe.cir', 'runner.py']},
        scope='One completed bounded2400s attempt only. Progress records are simulator reporting points, not a saved waveform or elapsed-time trace. Clock-edge association is not causal attribution. Originalfailedsample not overwritten/excluded; no repeatedwatchdog extension or populationgate waiver.')
    if state['status'] != 'completed':
        assert not result['complete_after_queries_present'] and not result['completed_wave_present']
        result['fullAFTER_and_independent27_and_decisions'] = 'not run; transient incomplete'
    else:
        result['fullAFTER_and_independent27_and_decisions'] = summary.get('status')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = audit(args.run_id)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['artifact_sha256', 'warning_families']}, indent=2))
