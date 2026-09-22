#!/usr/bin/env python3
"""Complex source/load/decision transfers from qualified stationary AC fixtures."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ports', required=True)
    parser.add_argument('--shunt', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    folders = {key: HERE/'runs'/value for key, value in [('ports', args.ports), ('shunt', args.shunt)]}
    manifests = {key: json.loads((folder/'manifest.json').read_text()) for key, folder in folders.items()}
    assert all(item['status'] == 'passed' for item in manifests.values())
    assert manifests['shunt']['qualified_reference_manifest_sha256'] == sha(folders['ports']/'manifest.json')
    for key in ['image_id', 'pdk_commit', 'ngspice', 'source_sha256', 'model_sha256', 'osdi_sha256', 'tuple', 'conditions']:
        assert manifests['ports'][key] == manifests['shunt'][key]
    waves, frequency = {}, None
    for group, manifest in manifests.items():
        for row in manifest['cases']:
            if row['name'] == 'control':
                continue
            path = folders[group]/(row['name']+'_ac.dat')
            assert sha(path) == row['ac_waveform_sha256']
            data = np.loadtxt(str(path), skiprows=1)
            assert np.isfinite(data).all() and data.shape[0] == 451
            if frequency is None:
                frequency = data[:, 0]
            assert np.array_equal(frequency, data[:, 0])
            waves[row['name']] = {name: data[:, 1+2*index]+1j*data[:, 2+2*index] for index, name in enumerate(row['op_vectors'])}

    def describe(values):
        assert np.isfinite(values).all()
        return {'real': list(map(float, values.real)), 'imaginary': list(map(float, values.imag)),
                'selected': [{'frequency_Hz': float(frequency[index]), 'real': float(values[index].real),
                              'imaginary': float(values[index].imag), 'magnitude': float(abs(values[index])),
                              'phase_deg': float(np.angle(values[index], deg=True))} for index in range(0, 451, 50)]}

    result = {'status': 'passed', 'manifest_sha256': {key: sha(folder/'manifest.json') for key, folder in folders.items()},
              'conditions': manifests['ports']['conditions'], 'frequency_Hz': list(map(float, frequency)),
              'dc_operating_point': manifests['ports']['cases'][1]['op'],
              'local_shunt_gain_V_V': {}, 'ports': {},
              'scope': 'Stationary linearized loaded baseline C-PEX BGR with actual schematic SENSE/TRIP reset-state loads. Branch currents include retained1TOhm numerical shunts. Effective source/load admittance includes other-port interactions; not isolated output resistance. No periodic T2F, clocked decision transfer or newly affected layout PEX.',
              'diagnostic_contract': '50uV shunt increment at decision is prospective engineering diagnostic, not product allocation. These frequency-domain transfers alone are not a decision-time coupling verdict; actual aggressor waveform/coupling network and clocked sampling are still needed.'}
    shunt = waves['shunt']
    gains = {'isense': shunt['v(isense)'], 'soft_differential': shunt['v(xt.icmp)']-shunt['v(xt.vth_soft)'],
             'hard_differential': shunt['v(xt.icmp)']-shunt['v(xt.vth_hard)']}
    result['local_shunt_gain_V_V'] = {key: describe(value) for key, value in gains.items()}
    for port in ['vref', 'iptat']:
        wave = waves[port]
        z = wave['v('+port+')']
        branch = wave['i(vsref)' if port == 'vref' else 'i(vsptat)']
        transfer = {'isense': wave['v(isense)'], 'soft_differential': wave['v(xt.icmp)']-wave['v(xt.vth_soft)'],
                    'hard_differential': wave['v(xt.icmp)']-wave['v(xt.vth_hard)']}
        result['ports'][port] = {'loaded_driving_point_ohm': describe(z),
                                 'effective_BGR_admittance_S': describe(-branch/z),
                                 'effective_downstream_admittance_S': describe((1+branch)/z),
                                 'injected_current_to_decision_ohm': {key: describe(value) for key, value in transfer.items()},
                                 'injected_current_to_equivalent_shunt_V_A': {key: describe(value/gains[key]) for key, value in transfer.items()},
                                 'port_voltage_to_equivalent_shunt_V_V': {key: describe(value/gains[key]/z) for key, value in transfer.items()}}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'local_low_frequency_shunt_gain_V_V': {key: value['selected'][0] for key, value in result['local_shunt_gain_V_V'].items()},
                      'low_frequency_port_voltage_to_equivalent_shunt_V_V': {port: {key: value['selected'][0] for key, value in row['port_voltage_to_equivalent_shunt_V_V'].items()} for port, row in result['ports'].items()}}, indent=2))


if __name__ == '__main__':
    main()
