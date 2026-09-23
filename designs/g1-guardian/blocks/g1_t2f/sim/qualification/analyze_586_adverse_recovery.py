#!/usr/bin/env python3
"""Join a distinct exact-input recovery without overwriting original failures."""
import argparse
import json
from pathlib import Path
from prepare_586_adverse_controls import HERE, sha
from analyze_586_adverse_controls import analyze_corner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    packet_path = HERE/'t2f586-adverse-controls-20260922-a.json'
    recovery_packet = HERE/'t2f586-fast-highhot-recovery900-20260923-a.json'
    original = json.loads(packet_path.read_text())
    recovery_case, = json.loads(recovery_packet.read_text())['cases']
    old_case, = [r for r in original['cases'] if (r['corner'], r['label']) == ('fast', 'highhot')]
    old = HERE/'runs'/old_case['run_id']
    new = HERE/'runs'/recovery_case['run_id']
    before, = json.loads((old/'summary.json').read_text())
    after, = json.loads((new/'summary.json').read_text())
    assert before['control_status'] == 'failed' and before['runtime']['status'] == 'timeout'
    assert before['runtime']['timeout_s'] == 600 and after['runtime']['timeout_s'] == 900
    assert after['control_status'] == after['full3180_status'] == 'passed'
    exact = {n: sha(old/n) == sha(new/n) for n in ['probe.cir', 'bgr.spice', 't2f.spice', '.spiceinit']}
    assert all(exact.values())
    result = dict(status='failed electrical calibration; original numerical failure retained', corners={},
        original_packet_sha256=sha(packet_path), recovery_packet_sha256=sha(recovery_packet),
        recovery=dict(original_run=old.name, distinct_recovery_run=new.name, exact_input_hashes=exact,
            original_summary_sha256=sha(old/'summary.json'), recovery_summary_sha256=sha(new/'summary.json'),
            original_status=before['control_status'], original_runtime=before['runtime'],
            recovery_status=after['control_status'], recovery_runtime=after['runtime'],
            waveform_prefix_parity='not run; original timed-out run exported no waveform'),
        scope='Twelve deterministic conditions, thirteen attempts including one separately authorized exact-input recovery. Both original nominal-rail calibrations remain frozen. No changed threshold, replacement population, statistical claim, source/card change or newphysicalPEX adoption.')
    for corner in ['slow', 'fast']:
        entries, receipts = {}, {}
        for case in [c for c in original['cases'] if c['corner'] == corner]:
            selected = recovery_case if case == old_case else case
            run = HERE/'runs'/selected['run_id']
            assert sha(run/'probe.cir') == selected['deck_sha256']
            assert sha(run/'preparation.json') == selected['preparation_sha256']
            provenance = json.loads((run/'provenance.json').read_text())
            assert all(provenance['input_checks'].values())
            row, = json.loads((run/'summary.json').read_text())
            entries[case['label']] = row
            receipts[run.name] = {n: sha(run/n) for n in ['summary.json', 'provenance.json', 'preparation.json', 'probe.cir']}
        result['corners'][corner] = analyze_corner(entries, receipts)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], output_sha256=sha(args.output),
        corners={c: dict(status=r['status'], maximum_abs_C=r['calibration']['maximum_independent_abs_residual_C'])
                 for c, r in result['corners'].items()}), indent=2))


if __name__ == '__main__':
    main()
