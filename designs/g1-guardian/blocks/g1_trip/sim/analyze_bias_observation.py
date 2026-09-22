#!/usr/bin/env python3
"""Algebraic temperature-motion decomposition after exact output-only qualification."""
import argparse
import bisect
import json
import math
from pathlib import Path
import re
from wave_archive import open_wave

SIM = Path(__file__).resolve().parent


def decompose(nodes, code, channel):
    ref, buf, ped, sh = (nodes[k] for k in ['vref', 'vref_buf', 'vped', 'shp'])
    sense, conditioned, dac = nodes['isense'], nodes['icmp'], nodes['vth_' + channel]
    terms = {
        'reference_nominal_ratio': -code / 530 * ref,
        'buffer_tracking_residual': -code / 530 * (buf - ref),
        'pedestal_residual': .5 * (ped - 51 / 53 * buf),
        'shunt_nominal_gain': 10 * sh,
        'sense_gain_pedestal_residual': .5 * (sense - ped - 20 * sh),
        'conditioning_residual': conditioned - .5 * sense,
        'dac_ratio_loading_residual': -(dac - (255 + code) / 530 * buf),
    }
    differential = conditioned - dac
    error = sum(terms.values()) - differential
    assert math.isfinite(error) and abs(error) < 2e-15
    return {'differential_V': differential, 'terms_V': terms, 'identity_reconstruction_error_V': error}


def load_run(name):
    run = SIM / 'qualification' / name
    summary, = json.loads((run / 'summary.json').read_text())
    preparation = json.loads((run / 'preparation.json').read_text())
    assert summary['output_only_qualification_status'] == 'passed'
    assert summary['all27_parameters_exact'] and summary['original_wave_parity']['status'].startswith('passed')
    sense = (run / 'sense.spice').read_text()
    trip = (run / 'trip.spice').read_text()
    assert len(re.findall(r'^XRD1\d+ ', sense, re.M)) == 2
    assert len(re.findall(r'^XRD2\d+ ', sense, re.M)) == 51
    assert len(re.findall(r'^XR2N\d+ ', sense, re.M)) == 20
    assert len(re.findall(r'^XR2P\d+ ', sense, re.M)) == 20
    assert len(re.findall(r'^XRU\d+ ', trip, re.M)) == 530
    assert 'XRU254 t0 s253 ' in trip and 'XRU529 vref s528 ' in trip
    assert len(re.findall(r'^XRC\d+ ', trip, re.M)) == 10
    with open_wave(run / (preparation['case'] + '.dat')) as stream:
        lines = stream.readlines()
    data = [list(map(float, line.split())) for line in lines[1:]]
    assert all(len(row) == 18 and all(math.isfinite(v) for v in row) for row in data)
    times = [row[0] for row in data]
    def interpolate(time):
        i = bisect.bisect_left(times, time)
        assert 0 < i < len(times)
        low, high = data[i-1], data[i]
        fraction = (time - low[0]) / (high[0] - low[0])
        row = [a + fraction * (b - a) for a, b in zip(low, high)]
        return row, {'method': 'linear between retained accepted waveform rows',
                     'bracket_times_s': [low[0], high[0]], 'fraction': fraction,
                     'bracket_width_s': high[0] - low[0]}
    def nodes(row):
        return dict(zip(['vref', 'iptat_voltage', 'vref_buf', 'vped', 'shp'], row[13:18]),
                    isense=row[7], icmp=row[2], vth_soft=row[3], vth_hard=row[4])
    quiet = {re.sub(r'^xt\.', '', key[2:-1]): value
             for key, value in summary['quiet_op_V'].items()}
    quiet['iptat_voltage'] = quiet.pop('iptat')
    points = {'quiet_op': {'nodes_V': quiet}}
    for channel in ['soft', 'hard']:
        for cycle in [2, 3, 4]:
            edge = summary['wave_analysis']['actual_clock_rising_crossings_s'][channel][cycle]
            for delay in [-1, 0, .2, .5, 1, 20]:
                row, interpolation = interpolate(edge + delay * 1e-9)
                points['%s_cycle%d_edge%+gns' % (channel, cycle, delay)] = {
                    'time_s': row[0], 'clock_edge_s': edge, 'delay_after_actual_edge_ns': delay,
                    'interpolation': interpolation, 'nodes_V': nodes(row),
                    'soft_hard_output_V': row[5:7], 'hard_clock_V': row[8],
                    'hard_frontend_xp_xq_xn_yn_V': row[9:13]}
    for point in points.values():
        point['decomposition'] = {channel: decompose(point['nodes_V'], code, channel)
                                  for channel, code in [('soft', 136), ('hard', 154)]}
    return {'run': name, 'temperature_C': summary['temperature_C'], 'points': points,
            'source_hashes': preparation['source_hashes'], 'fingerprints': summary['fingerprints']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', nargs=2, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    room, hot = sorted((load_run(name) for name in args.runs), key=lambda r: r['temperature_C'])
    assert [room['temperature_C'], hot['temperature_C']] == [25., 125.]
    assert room['source_hashes'] == hot['source_hashes'] and room['fingerprints'] == hot['fingerprints']
    delta = {}
    for key, cold_point in room['points'].items():
        hot_point = hot['points'][key]
        delta[key] = {'node_temperature_motion_V': {node: hot_point['nodes_V'][node] - value
                                                    for node, value in cold_point['nodes_V'].items()},
                      'differential_motion_V': {}, 'term_temperature_motion_V': {}}
        for channel in ['soft', 'hard']:
            lo, hi = cold_point['decomposition'][channel], hot_point['decomposition'][channel]
            terms = {term: hi['terms_V'][term] - value for term, value in lo['terms_V'].items()}
            motion = hi['differential_V'] - lo['differential_V']
            assert abs(sum(terms.values()) - motion) < 3e-15
            delta[key]['differential_motion_V'][channel] = motion
            delta[key]['term_temperature_motion_V'][channel] = terms
            delta[key].setdefault('temperature_identity_reconstruction_error_V', {})[channel] = sum(terms.values()) - motion
    result = {'status': 'passed exact algebraic reconstruction after output-only parity', 'runs': [room, hot],
              'temperature_motion_hot_minus_room': delta,
              'basis': 'Source-declared nominal ratios: pedestal51/53, SENSE20, conditioner1/2, DAC(255+code)/530. All deviations are retained as residual terms; this identity does not fit or replace calibration.',
              'scope': 'Simulated descriptive decomposition at quiet OP and matched actual clock phases. Terms are algebraic bins, not isolated block causality or a proof of comparator correctness from static input sign. IPTAT is pin voltage only. Original hot failures unchanged; no BGR replacement or statistical qualification.'}
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(result['status'])
    print(json.dumps(delta['quiet_op'], indent=2))


if __name__ == '__main__':
    main()
