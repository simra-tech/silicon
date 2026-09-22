#!/usr/bin/env python3
"""Read-only intermediate outcomes, including complete BEFORE evidence on timeout."""
import argparse
import json
import re
from pathlib import Path
from prepare_586_nominal_intermediates import HERE, ROOT, sha, deck_for
from run_bgr_substitution_draw_audit import read_group


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    packet_path = HERE/'t2f586-nominal-intermediate-20260922-a.json'
    packet = json.loads(packet_path.read_text())
    records = []
    for case in packet['cases']:
        run = HERE/'runs'/case['run_id']
        if not (run/'summary.json').exists():
            records.append(dict(label=case['label'], status='not run'))
            continue
        row, = json.loads((run/'summary.json').read_text())
        prep = json.loads((run/'preparation.json').read_text())
        prov = json.loads((run/'provenance.json').read_text())
        log = (run/'run.log').read_text()
        checks = dict(preparation=sha(run/'preparation.json') == case['preparation_sha256'],
            deck=sha(run/'probe.cir') == prep['deck_sha256'] == case['deck_sha256'],
            transform=(run/'probe.cir').read_text() == deck_for(prep['temperature_C'], prep['groups']),
            source=all(sha(run/n) == value for n, value in prep['source_hashes'].items()),
            runtime=prov['runtime_identity'] == prep['runtime'],
            original_input_checks=all(prov['input_checks'].values()),
            live_bindings=all(sha(ROOT/n) == value for n, value in prep['live_bindings_sha256'].items()))
        assert all(checks.values())
        before = {tag: read_group(log, tag+'_BEFORE', keys) for tag, keys in prep['groups'].items()}
        assert sum(map(len, before.values())) == 3180 and before == prep['expected3180']
        after_present = all(tag+'_AFTER_BEGIN' in log and tag+'_AFTER_END' in log for tag in prep['groups'])
        first_transient = log.find('Initial Transient Solution')
        assert first_transient >= 0
        def warnings(text):
            return [line for line in text.splitlines() if re.search(r'warning', line, re.I)]
        record = dict(label=case['label'], run_id=case['run_id'], temperature_C=prep['temperature_C'],
            status=row['status'], numerical_control_status=row['numerical_control_status'], calibration_status=row['calibration_status'],
            runtime=row['runtime'], input_checks=checks, full3180_before_status='passed exact nominal realization',
            after_inventory_status='present; successful runner comparison retained' if after_present else 'not run',
            waveform_status='present' if (run/prep['output_wave']).exists() or (run/(prep['output_wave']+'.gz')).exists() else 'not run',
            warning_lines_before_initial_transient=len(warnings(log[:first_transient])),
            warning_lines_after_initial_transient=len(warnings(log[first_transient:])), errors=row['errors'],
            receipts_sha256={n: sha(run/n) for n in ['summary.json', 'provenance.json', 'preparation.json', 'run.log', 'probe.cir']})
        if row.get('calibration'):
            record['calibration'] = row['calibration']
        records.append(record)
    result = dict(status='failed incomplete nominal temperature coverage' if any(r['status'] == 'failed' for r in records)
        else 'passed' if all(r['status'] == 'passed' for r in records) else 'not run to completion',
        packet_sha256=sha(packet_path), records=records,
        scope='Original held-out intermediate checks; no refit. Exact BEFORE evidence on timeout does not substitute for AFTER/wave/calibration. Progress points are not a saved waveform or causal numerical diagnosis; no retry authorized by this report.')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
