#!/usr/bin/env python3
"""Compare first-pair trajectories at matched actual phases; no simulation."""
import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path
import re
from analyze_bias_observation import decompose
from run_bias_observation_probe import quiet_values
from wave_archive import open_wave, wave_sha

SIM = Path(__file__).resolve().parent


def initial_warning_phases(log):
    counts = {'before_inventory': 0, 'inventory': 0, 'transient_initialization': 0, 'after_initial_transient_solution': 0}
    phase = 'before_inventory'
    for line in log.splitlines():
        if line == 'NON_BGR_BEFORE_BEGIN':
            phase = 'inventory'
        if line == 'BGR_BEFORE_END':
            phase = 'transient_initialization'
        if line.startswith('Initial Transient Solution'):
            phase = 'after_initial_transient_solution'
        if 'warning' in line.lower() or re.search(r'\bnan\b', line, re.I):
            counts[phase] += 1
    return counts


def load(name, prefix, failed_observation_audit=None):
    run = SIM / 'qualification' / name
    result, = json.loads((run / 'summary.json').read_text())
    prep = json.loads((run / 'preparation.json').read_text())
    observations = result
    if prefix and failed_observation_audit is not None:
        assert result['prefix_contract_status'] == 'failed'
        assert failed_observation_audit['run'] == name and failed_observation_audit['original_fixture_status'] == 'failed; unchanged'
        assert failed_observation_audit['limited_observation_status'].startswith('passed finite saved219ns')
        assert failed_observation_audit['summary_sha256'] == hashlib.sha256((run / 'summary.json').read_bytes()).hexdigest()
        assert failed_observation_audit['log_sha256'] == hashlib.sha256((run / 'run.log').read_bytes()).hexdigest()
        assert failed_observation_audit['decoded_wave_sha256'] == wave_sha(run / 'hard_+0mV.dat')
        observations = failed_observation_audit
    else:
        assert result['prefix_contract_status'] == 'passed' if prefix else result['controlled_substitution_status'] == 'passed comparison contract'
    assert observations['parameter_audit']['checks'] and all(observations['parameter_audit']['checks'].values())
    with open_wave(run / 'hard_+0mV.dat') as stream:
        lines = stream.readlines()
    data = [list(map(float, line.split())) for line in lines[1:] if line.strip()]
    assert all(len(row) == 18 and all(math.isfinite(v) for v in row) for row in data)
    times = [row[0] for row in data]
    assert all(a < b for a, b in zip(times, times[1:]))
    log = (run / 'run.log').read_text()
    quiet = {re.sub(r'^xt\.', '', key[2:-1]): value for key, value in quiet_values(log).items()}
    quiet['iptat_voltage'] = quiet.pop('iptat')
    points = {'quiet_op': {'nodes_V': quiet}}
    for channel in ['soft', 'hard']:
        edge = observations['wave_analysis']['channels'][channel]['actual_edge_s'] if prefix else result['wave_analysis']['actual_clock_rising_crossings_s'][channel][0]
        for offset in [-1, 0, .2, .5, 1, 20]:
            t = edge+offset*1e-9
            i = bisect.bisect_left(times, t)
            assert 0 < i < len(times)
            lo, hi = data[i-1], data[i]
            fraction = (t-lo[0])/(hi[0]-lo[0])
            row = [a+fraction*(b-a) for a, b in zip(lo, hi)]
            nodes = dict(zip(['vref', 'iptat_voltage', 'vref_buf', 'vped', 'shp'], row[13:18]),
                         isense=row[7], icmp=row[2], vth_soft=row[3], vth_hard=row[4])
            points['%s_first_edge%+gns' % (channel, offset)] = {
                'actual_edge_s': edge, 'time_s': t, 'offset_ns': offset,
                'interpolation': {'bracket_times_s': [lo[0], hi[0]], 'fraction': fraction, 'bracket_width_s': hi[0]-lo[0]},
                'all18_vector_values': dict(zip(prep['wave_columns'], row)), 'nodes_V': nodes}
    for point in points.values():
        point['decomposition'] = {channel: decompose(point['nodes_V'], code, channel) for channel, code in [('soft', 136), ('hard', 154)]}
    return {'run': name, 'temperature_C': result['temperature_C'], 'source_hashes': prep['source_hashes'],
            'parameter_groups': observations['parameter_audit']['ordered_parameter_groups'], 'points': points,
            'warning_phase_counts': initial_warning_phases(log),
            'summary_sha256': hashlib.sha256((run / 'summary.json').read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--failed-prefix-observation-audit', type=Path)
    args = parser.parse_args()
    room = load('joint-bgr586-nominal-substitution-room-20260922-a', False)
    observation_audit = json.loads(args.failed_prefix_observation_audit.read_text()) if args.failed_prefix_observation_audit else None
    hot = load('joint-bgr586-hot-prefix219ns-20260922-a', True, observation_audit)
    assert room['source_hashes'] == hot['source_hashes'] and [room['temperature_C'], hot['temperature_C']] == [25, 125]
    assert room['parameter_groups'] == hot['parameter_groups']
    room.pop('parameter_groups')
    hot.pop('parameter_groups')
    changes = {}
    for name, point in room['points'].items():
        other = hot['points'][name]
        entry = {'node_motion_V': {key: other['nodes_V'][key]-value for key, value in point['nodes_V'].items()}, 'differential_motion_V': {}, 'term_motion_V': {}}
        for channel in ['soft', 'hard']:
            cold_terms, hot_terms = point['decomposition'][channel], other['decomposition'][channel]
            delta = hot_terms['differential_V']-cold_terms['differential_V']
            terms = {key: hot_terms['terms_V'][key]-value for key, value in cold_terms['terms_V'].items()}
            assert abs(sum(terms.values())-delta) < 3e-15
            entry['differential_motion_V'][channel] = delta
            entry['term_motion_V'][channel] = terms
        changes[name] = entry
    output = {'status': 'passed full draw equality and descriptive first-pair algebraic reconstruction', 'runs': [room, hot],
              'original_prefix_fixture_status': 'failed; separate explicit saved-observation scope' if observation_audit else 'passed',
              'failed_observation_audit_sha256': hashlib.sha256(args.failed_prefix_observation_audit.read_bytes()).hexdigest() if observation_audit else None,
              'hot_minus_room_matched_actual_phase': changes,
              'scope': 'First soft/hard evaluation pair only, not complete period or late state. NominalBGR586 at both temperatures with fullnonBGR realization equality; no waveform parity across original/replacement BGR sources. Algebraic residual bins are observations, not causal attribution. Physical-fidelity gate remainsfailed; no calibration/MC expansion.'}
    with args.output.open('x') as stream:
        json.dump(output, stream, indent=2)
        stream.write('\n')
    print(output['status'])
    print(json.dumps({key: changes[key]['differential_motion_V'] for key in ['quiet_op', 'soft_first_edge+20ns', 'hard_first_edge+20ns']}, indent=2))


if __name__ == '__main__':
    main()
