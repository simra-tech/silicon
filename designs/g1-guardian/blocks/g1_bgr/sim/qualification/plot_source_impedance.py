#!/usr/bin/env python3
"""Plot qualified three-tuple stationary reference impedance/input referral."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent


def complex_array(data):
    return np.array(data['real'])+1j*np.array(data['imaginary'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-prefix', required=True)
    args = parser.parse_args()
    paths = [HERE/(args.output_prefix+suffix) for suffix in ['.png', '.svg', '.json']]
    assert not any(path.exists() for path in paths)
    figure, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    summary = {'status': 'passed', 'sources': {}, 'conditions': [],
               'scope': 'Simulated stationary loaded baseline BGR C-PEX + actual schematic SENSE/TRIP, held-reset comparators. Not clocked sampling, periodic T2F, newly affected route PEX or product acceptance.'}
    for condition, color in [('nominal', '#2066ad'), ('slowcold', '#24843e'), ('fasthot', '#b3353b')]:
        path = HERE/('loaded_source_impedance_'+condition+'_20260922_r1.json')
        item = json.loads(path.read_text())
        assert item['status'] == 'passed'
        summary['sources'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        freq = np.array(item['frequency_Hz'])
        op = item['dc_operating_point']
        row = {'condition': condition, 'conditions': item['conditions'], 'vref_V': op['v(vref)'], 'iptat_V': op['v(iptat)'],
               'bgr_current_A': op['i(vsupply)'], 'iptat_current_A': op['i(vsptat)'], 'total_analog_current_A': -op['i(vdda)']}
        for port, style in [('vref', '-'), ('iptat', '--')]:
            values = complex_array(item['ports'][port]['loaded_driving_point_ohm'])
            axes[0, 0].loglog(freq, abs(values), style, color=color, label=condition+' '+port)
            row[port+'_low_frequency_loaded_Z_ohm'] = float(abs(values[0]))
        gain = complex_array(item['local_shunt_gain_V_V']['soft_differential'])
        axes[0, 1].loglog(freq, abs(gain), color=color, label=condition)
        row['low_frequency_shunt_to_soft_differential_gain_V_V'] = float(gain[0].real)
        for port, axis in [('vref', axes[1, 0]), ('iptat', axes[1, 1])]:
            for decision, style in [('soft_differential', '-'), ('hard_differential', '--')]:
                values = complex_array(item['ports'][port]['port_voltage_to_equivalent_shunt_V_V'][decision])
                axis.loglog(freq, abs(values), style, color=color, label=condition+' '+decision.split('_')[0])
        summary['conditions'].append(row)
    titles = ['Loaded driving-point impedance', 'Local shunt → soft differential gain',
              'Raw VREF voltage → equivalent shunt', 'IPTAT voltage → equivalent shunt']
    units = ['Magnitude (Ω)', 'Magnitude (V/V)', 'Magnitude (V/V)', 'Magnitude (V/V)']
    for axis, title, unit in zip(axes.flat, titles, units):
        axis.set_title(title)
        axis.set_ylabel(unit)
        axis.grid(True, which='both', alpha=.2)
        axis.legend(fontsize=7, ncol=2)
    for axis in axes[1]:
        axis.set_xlabel('Frequency (Hz)')
    figure.suptitle('Simulated stationary loaded reference — no periodic T2F or clocked-decision claim')
    figure.tight_layout(rect=(0, 0, 1, .97))
    figure.savefig(str(paths[0]), dpi=160)
    figure.savefig(str(paths[1]))
    paths[2].write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
