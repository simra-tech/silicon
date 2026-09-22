#!/usr/bin/env python3
"""Read-only original two-point calibration for the four final586 nominal anchors."""
import argparse
import json
from pathlib import Path
from prepare_586_source_controls import sha

HERE = Path(__file__).resolve().parent


def calibrated(rows):
    assert set(rows) == {-40, 25, 100, 125}
    f25, f100 = rows[25], rows[100]
    slope = (f100-f25)/75
    assert slope > 0
    points = [dict(temperature_C=t, frequency_Hz=f, inferred_temperature_C=25+(f-f25)/slope,
                   residual_C=25+(f-f25)/slope-t, role='calibration' if t in [25, 100] else 'independent') for t, f in sorted(rows.items())]
    worst = max(abs(p['residual_C']) for p in points if p['role'] == 'independent')
    return dict(status='passed' if worst <= 2 else 'failed', frequency_slope_Hz_per_C=slope, maximum_independent_abs_residual_C=worst,
                criterion='Original25/100C linear calibration; independent−40/125C absolute residual≤2C', points=points,
                scope='One nominal final586 source control; no population/PVT/intermediate/return/actualpad/newphysicalCC or adoption claim. Historical failures retained; no correction curve introduced.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    packet = json.loads(args.packet.read_text())
    selected = [case for case in packet['cases'] if case['label'] in ['new-t25', 'new-t100', 'new-tm40', 'new-t125']]
    assert len(selected) == 4 and not args.output.exists()
    rows, receipts, vectors = {}, {}, []
    for case in selected:
        run = HERE/'runs'/case['run_id']
        result, = json.loads((run/'summary.json').read_text())
        assert result['control_status'] == 'passed' and result['full_inventory_status'] == 'passed'
        rows[result['temperature_C']] = result['measurements']['freq']
        vectors.append(result['parameters_before'])
        receipts[case['run_id']] = {name: sha(run/name) for name in ['summary.json', 'provenance.json', 'preparation.json']}
    assert all(v == vectors[0] for v in vectors)
    result = calibrated(rows)
    result.update(full3180_same_nominal_parameters_across_anchors='passed', receipts_sha256=receipts, packet_sha256=sha(args.packet))
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
