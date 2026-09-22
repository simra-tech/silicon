#!/usr/bin/env python3
"""Strict completed-leaf host replay: source/sample/entire saved output equality."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from wave_archive import open_wave, wave_sha

SIM = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(reference, candidate):
    old = json.loads((reference / 'provenance.json').read_text())
    new = json.loads((candidate / 'provenance.json').read_text())
    left = json.loads((reference / 'summary.json').read_text())
    right = json.loads((candidate / 'summary.json').read_text())
    assert len(left) == len(right) == 1, 'Host parity uses one bounded leaf'
    left, right = left[0], right[0]
    tag = left['case']
    sources = ['sense.spice', 'trip.spice', 'bgr.spice']
    normalized = [(directory / (tag + '.cir')).read_text().replace(directory.name, '@RUN@')
                  for directory in [reference, candidate]]
    checks = {
        'different_run_directories': reference.resolve() != candidate.resolve(),
        'case_exact': tag == right['case'],
        'actual_bgr_both': old.get('actual_bgr') is True and new.get('actual_bgr') is True,
        'normalized_deck_exact': normalized[0] == normalized[1],
        'source_snapshots_exact': all(sha(reference / name) == sha(candidate / name) for name in sources),
        'model_hashes_exact': bool(old['model_sha256']) and old['model_sha256'] == new['model_sha256'],
        'pdk_commit_exact': old['pdk_commit'] == new['pdk_commit'] == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b',
        'image_exact': old['image_id_observed_by_host'] == new['image_id_observed_by_host'] == 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0',
        'engine_exact': bool(old['ngspice_version']) and old['ngspice_version'] == new['ngspice_version'],
        'seed_exact': old.get('seed') == new.get('seed') and old.get('seed') is not None,
        'both_solver_completed': all(row['solver_status'] == 'passed' and row['watchdog_status'] == 'completed' and row['returncode'] == 0 for row in [left, right]),
        'all27_parameters_exact': len(left['fingerprints']) == len(right['fingerprints']) == 27 and left['fingerprints'] == right['fingerprints'],
        'measurements_exact': bool(left['measures']) and left['measures'] == right['measures'],
        'both_late_outputs_exact': bool(left.get('both_sampled_output_V')) and left.get('both_sampled_output_V') == right.get('both_sampled_output_V'),
        'quiet_differences_exact': left.get('quiet_soft_hard_V') == right.get('quiet_soft_hard_V') and left.get('quiet_soft_hard_V') is not None,
    }
    waves = [directory / (tag + '.dat') for directory in [reference, candidate]]
    checks['whole_saved_waveform_bytes_exact'] = wave_sha(waves[0]) == wave_sha(waves[1])
    points = [0, 0]
    endpoints = [None, None]
    maxima = None
    compatible = True
    finite = True
    with open_wave(waves[0]) as a, open_wave(waves[1]) as b:
        headers = [a.readline().split(), b.readline().split()]
        checks['waveform_columns_exact'] = headers[0] == headers[1]
        for pair in itertools.zip_longest(a, b):
            parsed = []
            for index, line in enumerate(pair):
                if line is None:
                    parsed.append(None)
                    continue
                values = list(map(float, line.split()))
                assert values, 'Empty waveform record'
                points[index] += 1
                endpoints[index] = values[0]
                finite = finite and all(math.isfinite(value) for value in values)
                parsed.append(values)
            if any(row is None for row in parsed) or len(parsed[0]) != len(parsed[1]):
                compatible = False
            elif compatible:
                delta = [abs(x-y) for x,y in zip(*parsed)]
                maxima = delta if maxima is None else [max(x,y) for x,y in zip(maxima,delta)]
    checks['finite_complete_waveforms'] = finite and all(points) and all(end is not None and end >= old['transient_endpoint_us'] * 1e-6 * (1-1e-9) for end in endpoints)
    report = {'status': 'passed' if all(checks.values()) else 'failed',
              'reference_run': reference.name, 'candidate_run': candidate.name,
              'checks': checks, 'points': points, 'endpoint_s': endpoints,
              'waveform_sha256': [wave_sha(path) for path in waves],
              'source_sha256': {name: [sha(directory / name) for directory in [reference, candidate]] for name in sources},
              'normalized_deck_sha256': [hashlib.sha256(text.encode()).hexdigest() for text in normalized],
              'diagnostic_rowwise_max_abs_difference': maxima if compatible else None,
              'scope': 'One completed same-seed joint SPARSE/KLU leaf, whichever the identical decks specify. Exact archived 27 parameter strings, all saved waveform bytes and sampled results required. No tolerance waiver, solver-family expansion, other corner, seed ensemble or electrical acceptance is implied.'}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    candidate = SIM / 'qualification' / args.candidate
    report = compare(SIM / 'qualification' / args.reference, candidate)
    output = args.output or candidate / 'host_parity.json'
    with output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
