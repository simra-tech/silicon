#!/usr/bin/env python3
"""Time-weighted supply currents from retained actual-receiver transients."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def analyze(path, windows, signals):
    with path.open() as f:
        names = next(f).split()
        data = [list(map(float, line.split())) for line in f if line.strip()]
    result = {}
    for label, lo, hi in windows:
        currents = {}
        for name, voltage in signals.items():
            col = names.index(name)
            charge = 0.0
            peaks = []
            for a, b in zip(data, data[1:]):
                left, right = max(a[0], lo), min(b[0], hi)
                if right <= left:
                    continue
                first = -(a[col]+(b[col]-a[col])*(left-a[0])/(b[0]-a[0]))
                last = -(a[col]+(b[col]-a[col])*(right-a[0])/(b[0]-a[0]))
                charge += (first+last)*(right-left)/2
                peaks.extend([first, last])
            currents[name] = {'mean_A': charge/(hi-lo), 'mean_power_W': voltage*charge/(hi-lo),
                              'minimum_sampled_A': min(peaks), 'maximum_sampled_A': max(peaks),
                              'rail_voltage_V': voltage}
        result[label] = {'window_start_s': lo, 'window_end_s': hi, 'supplies': currents,
                         'combined_mean_power_W': sum(x['mean_power_W'] for x in currents.values())}
    return {'vector_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'windows': result}


def main():
    run = 't2f_ls_transitions_fasthot_native_20260922_01'
    result = analyze(HERE/'runs'/run/'transitions.dat',
                     [('initial_ptat', 5e-6, 11e-6), ('disabled', 14e-6, 17e-6),
                      ('reenabled_ptat', 22e-6, 29e-6), ('reference', 34e-6, 41e-6),
                      ('returned_ptat', 46e-6, 58e-6), ('r4_high', 64e-6, 70e-6)],
                     {'i(vdd)': 3.6, 'i(vdd12)': 1.32})
    result.update(run_id=run, scope='Fast/hot125C combined BGR/T2F/three actual LS. Estimated route RC, ideal1V IPTAT termination,50fF output. Cannot isolate LS current. Sampled peaks are not worst-case bounds.')
    (HERE/'transition_current_fasthot_20260922.json').write_text(json.dumps(result, indent=2)+'\n')
    base = HERE.parents[2]/'g1_osc/sim/qualification'
    run = 'osc_actual_receiver_nominal_20260922_01'
    result = analyze(base/'runs'/run/'receiver.dat', [('steady', 2e-6, 5.8e-6)],
                     {'i(vdd)': 1.2, 'i(vddclk)': 1.2})
    result.update(run_id=run, scope='Nominal27C code8 OSC and actual buf16 plus16 buf8. Exact internal SPEF, estimated assembly RC,100fF assumed at each leaf output. Further clock tree not present. Sampled peaks are not worst-case bounds.')
    (base/'actual_receiver_current_20260922.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
