#!/usr/bin/env python3
"""Read-only existing rail waveforms; combined analog current is not T2F-only."""
import argparse
import json
from pathlib import Path
import numpy as np
from prepare_586_source_controls import HERE, sha
from run_586_source_control import load_wave


def summarize(time, current, start, end):
    assert time[0] <= start < end <= time[-1]
    inside = (time > start) & (time < end)
    grid = np.r_[start, time[inside], end]
    values = np.r_[np.interp(start, time, current), current[inside], np.interp(end, time, current)]
    duration = end-start
    return dict(start_s=start, end_s=end, time_weighted_mean_A=float(np.trapz(values, grid)/duration),
        time_weighted_rms_A=float(np.sqrt(np.trapz(values*values, grid)/duration)),
        maximum_sampled_A=float(values.max()), minimum_sampled_A=float(values.min()),
        maximum_sampled_time_s=float(grid[values.argmax()]), samples_including_interpolated_boundaries=len(grid))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    runs = ['t2f586-source-controls-20260922-a-'+label for label in ['new-tm40', 'new-t25', 'new-t100', 'new-t125']]
    runs += ['t2f586-nominal-intermediate-20260922-a-'+label for label in ['tm20', 't0', 't50', 't75']]
    runs += ['t2f586-nominal75-recovery900-20260922-b']
    runs += [case['run_id'] for case in json.loads((HERE/'t2f586-adverse-controls-20260922-a.json').read_text())['cases']]
    records = []
    for run_id in runs:
        run = HERE/'runs'/run_id
        row, = json.loads((run/'summary.json').read_text())
        prep = json.loads((run/'preparation.json').read_text())
        deck = (run/'probe.cir').read_text()
        assert 'wrdata ptat_T12.5.dat v(fout) v(vref) i(vdd) i(vdd12) ' in deck
        receipt = dict(run_id=run_id, status='not run', original_outcome=row.get('status', row.get('control_status')),
            receipts_sha256={n: sha(run/n) for n in ['summary.json', 'preparation.json', 'provenance.json', 'probe.cir']},
            temperature_C=prep['temperature_C'], corner=prep.get('corner', 'typical'),
            source_hashes=prep['source_hashes'])
        successful = row.get('numerical_control_status', row.get('control_status')) == 'passed'
        if not successful:
            receipt['reason'] = 'Original numerical control failed; no completed current-wave analysis or inferred missing result'
            records.append(receipt)
            continue
        blob, data = load_wave(run/'ptat_T12.5.dat')
        assert data.ndim == 2 and data.shape[1] == 13 and np.isfinite(data).all() and data[-1, 0] == 32e-6
        assert np.all(np.diff(data[:, 0]) > 0)
        rails = {}
        for name, column, scope in [('VDDA', 3, 'Combined BGR+T2F analog supply; not separately assignable to T2F'),
                                     ('VDD12', 4, 'T2F 1.2V-domain source in this fixture; no BGR terminal attached')]:
            delivered = -data[:, column]
            rails[name] = dict(positive_sign='Current delivered by ideal voltage source into circuit', scope=scope,
                full_transient=summarize(data[:, 0], delivered, data[0, 0], data[-1, 0]),
                measured_edge_window=summarize(data[:, 0], delivered, row['measurements']['t_a'], row['measurements']['t_b']))
        receipt.update(status='passed read-only waveform statistics', rails=rails, waveform_sha256=__import__('hashlib').sha256(blob).hexdigest())
        records.append(receipt)
    result = dict(status='completed selected existing-wave statistics; failed inputs explicitly not run', records=records,
        columns={'time': 0, 'v(fout)': 1, 'v(vref)': 2, 'i(vdd)': 3, 'i(vdd12)': 4},
        scope='Simulated DC-initialized 32us enable fixtures, idealrails/IPTAT1V/50fF output. Peak is sampled, not a continuous/worstcase/lifetime/physicalIR bound. RMS uses time-weighted piecewise-linear integration. Edgewindow endpoints use rounded printed ngspice t_a/t_b; not exact internalmeasurement times. VDDA is combined BGR+T2F: never add a separate BGR current to it. No new simulation/model/source/acceptance changes.',
        correction='Prior informal statement that final58613-column traces omitted rail currents was incorrect; exact wrdata proves columns3/4. This report uses actual retained currents, not voltage-based inference.')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], attempts=len(records), waveforms_analyzed=sum(r['status'].startswith('passed') for r in records),
                         output_sha256=sha(args.output)), indent=2))


if __name__ == '__main__':
    main()
