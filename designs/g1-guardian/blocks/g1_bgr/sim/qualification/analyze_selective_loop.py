#!/usr/bin/env python3
"""Compare nominal selective-loop hypothesis to retained exact baseline data."""
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    output = HERE/'selective_loop16_nominal_analysis_20260922_r1.json'
    assert not output.exists()
    probe_path = HERE/'runs/bgr_selective_loop16_density_20260922_r1/manifest.json'
    probe = json.loads(probe_path.read_text())
    baseline, candidate = probe['cases']
    assert all(row['status'] == 'passed' for row in probe['cases'])
    comparisons = []
    for parameter, value in candidate['parameters'].items():
        original = __import__('re').sub(r'_u\d+(?=\.)', '', parameter)
        base = baseline['parameters'][original]
        comparisons.append({'parameter': parameter, 'baseline': base, 'candidate': value,
                            'relative_difference': value/base-1 if base else None,
                            'absolute_difference': value-base})
    files = [HERE/'runs/bgr_array_baseline_nominal_20260921_01/nominal.dat',
             HERE/'runs/bgr_selective_loop16_nominal_20260922_r1/nominal.dat']
    data = [np.loadtxt(str(path), skiprows=1) for path in files]
    assert np.array_equal(data[0][:, 0], data[1][:, 0])
    columns = ['vref', 'iptat', 'supply_current', 'vbe', 'dvbe', 'pbias', 'pcasc', 'c2', 'vbe3', 'vd1', 'vd2']
    waveform = {name: {'maximum_absolute_difference': float(np.max(np.abs(data[1][:, i]-data[0][:, i]))),
                       'baseline_25C': float(np.interp(25, data[0][:, 0], data[0][:, i])),
                       'candidate_25C': float(np.interp(25, data[1][:, 0], data[1][:, i]))} for i, name in enumerate(columns, 1)}
    current = [row for row in comparisons if row['parameter'].endswith('[ic]')]
    result = {'status': 'nominal hypothesis characterized; not adoption or mismatch qualification',
              'probe_manifest_sha256': hashlib.sha256(probe_path.read_bytes()).hexdigest(),
              'waveform_sha256': {str(path.relative_to(HERE)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
              'unit_parameter_comparisons': comparisons,
              'maximum_HBT_unit_ic_relative_difference': max(abs(row['relative_difference']) for row in current),
              'temperature_waveform_comparison': waveform,
              'limitations': 'Direct nominal per-unit current comparison at25C only. No arbitrary acceptance tolerance adopted. Full temperature terminal/model validity, mismatch, legal placement, extracted new wiring, DRC/LVS, startup, loading and stability remain separate gates.'}
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'unit_parameter_comparisons'}, indent=2))


if __name__ == '__main__':
    main()
