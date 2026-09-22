#!/usr/bin/env python3
"""Describe retained VREF load steps; not a frequency-domain impedance extraction."""
import hashlib
import json
import re
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def average(data, column, left, right):
    time = data[:, 0]
    selected = (time > left) & (time < right)
    axis = np.concatenate(([left], time[selected], [right]))
    values = np.interp(axis, time, data[:, column])
    return float(np.trapz(values, axis)/(right-left))


def main():
    output = HERE/'load_anchor_summary_20260922_r1.json'
    assert not output.exists()
    rows = []
    for run_id in ['bgr_stress3_20260921_01', 'bgr_capload9_20260921_01']:
        folder = HERE/'runs'/run_id
        manifest = json.loads((folder/'manifest.json').read_text())
        for row in manifest['cases']:
            if row.get('stress') != 'load':
                continue
            path = folder/(row['name']+'.cir')
            assert sha(path) == row['deck_sha256'] and row['status'] == 'passed'
            deck = path.read_text()
            assert 'Istep vref 0 pwl(0 0 5u 0 5.01u 100n 20u 100n 20.01u 0 40u 0)' in deck
            temperature = float(re.search(r'(?m)^option temp=([-+0-9.eE]+)$', deck).group(1))
            capacitance = re.search(r'(?m)^Cload vref 0 (\S+)$', deck).group(1)
            capacitance = float(capacitance[:-1])*1e-12 if capacitance.endswith('p') else float(capacitance)
            wave = folder/(row['name']+'.dat')
            data = np.loadtxt(str(wave), skiprows=1)
            assert data.shape[1] == 12 and np.isfinite(data).all() and abs(data[-1, 0]-40e-6) < 1e-12
            before, loaded, after = [average(data, 1, left, right) for left, right in [(3e-6, 4e-6), (18e-6, 19e-6), (35e-6, 39e-6)]]
            rows.append({'run_id': run_id, 'case': row['name'], 'waveform_sha256': sha(wave),
                         'manifest_sha256': sha(folder/'manifest.json'), 'source_sha256': manifest['pex_sha256'],
                         'hbt': row['hbt'], 'mos': row['mos'], 'res': row['res'], 'vdd_V': row['vdd'],
                         'temperature_C': temperature, 'VREF_load_F': capacitance,
                         'IPTAT_fixture': 'ideal1V clamp', 'load_step_A': 100e-9,
                         'window_average_VREF_V': {'before_3_to_4us': before, 'loaded_18_to_19us': loaded, 'recovered_35_to_39us': after},
                         'loaded_window_delta_V': loaded-before,
                         'finite_step_response_magnitude_V_per_A': abs((loaded-before)/100e-9),
                         'after_window_return_delta_V': after-before,
                         'IPTAT_before_A': average(data, 2, 3e-6, 4e-6),
                         'IPTAT_loaded_A': average(data, 2, 18e-6, 19e-6),
                         'supply_current_average_0_to_40us_A': -average(data, 3, 0, 40e-6),
                         'supply_current_saved_peak_A': float(np.max(-data[:, 3]))})
    result = {'status': 'retained characterization analyzed', 'cases': rows,
              'scope': 'Time-weighted finite100nA VREF load-step response with original standalone fixture. The ratio is not an AC output-impedance sweep and may include incomplete settling/nonlinearity. No source impedance versus frequency, actual downstream kickback, coupling, rail/return network or acceptance budget is inferred.'}
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
