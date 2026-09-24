#!/usr/bin/env python3
"""Execute a reviewed output-only replay; qualify original waveform bytes exactly."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from run_nominal_clock_probe import analyze_wave, validate_saved_nodes, run_bounded
from wave_archive import archive_new_wave, open_wave, wave_sha

SIM = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_original_columns(original, observed):
    """No rounding/tolerances; project exact original-width rows including header."""
    assert len(original) == len(observed) and len(original) > 1
    assert all(len(line.split()) == 13 for line in original)
    assert all(len(line.split()) == 18 for line in observed)
    projected = []
    data = []
    for index, (old, new) in enumerate(zip(original, observed)):
        assert old.endswith(b'\n') and new.endswith(b'\n')
        projected.append(new[:len(old)-1] + b'\n')
        assert projected[-1] == old, 'Original13column byte mismatch at row%d' % index
        if index:
            values = [float(token) for token in new.split()]
            assert all(math.isfinite(v) for v in values)
            assert values[:13] == [float(token) for token in old.split()]
            data.append(values)
    return {'status': 'passed exact13column decoded bytes and numeric rows',
            'row_count_including_header': len(original),
            'projected_original_sha256': hashlib.sha256(b''.join(projected)).hexdigest()}, data


def quiet_values(log):
    region = re.findall(r'^BIAS_OBSERVATION_OP\n(.+?)^BIAS_OBSERVATION_OP_END$', log, re.M | re.S)
    assert len(region) == 1
    pairs = re.findall(r'^(v\([^\n=]+\))\s*=\s*(\S+)', region[0], re.M)
    result = {name: float(value) for name, value in pairs}
    assert set(result) == {'v(vref)', 'v(iptat)', 'v(vref_buf)', 'v(vped)', 'v(shp)',
                           'v(isense)', 'v(xt.icmp)', 'v(xt.vth_soft)', 'v(xt.vth_hard)'}
    assert all(math.isfinite(value) for value in result.values())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--image-id', required=True)
    parser.add_argument('--timeout-s', type=float, default=600)
    args = parser.parse_args()
    assert '/' not in args.run_id and args.run_id not in ['.', '..'] and 0 < args.timeout_s <= 600
    out = SIM / 'qualification' / args.run_id
    prep = json.loads((out / 'preparation.json').read_text())
    original = SIM / 'qualification' / prep['reference_run']
    case = prep['case']
    assert prep['run'] == args.run_id and prep['status'] == 'prepared only; simulation not run'
    assert not (out / 'summary.json').exists() and not (out / (case + '.log')).exists()
    pdk = Path('/foss/pdks/ihp-sg13g2')
    runtime = {'image_id_observed_by_host': args.image_id,
               'pdk_commit': (pdk / 'COMMIT').read_text().strip(),
               'ngspice_version': subprocess.check_output(['ngspice', '--version'], text=True),
               'model_sha256': {str(p.relative_to(pdk)): sha(p) for p in (pdk / 'libs.tech/ngspice/models').rglob('*') if p.is_file()},
               'solver': 'sparse'}
    deck = out / (case + '.cir')
    nodes = validate_saved_nodes(deck.read_text(), (out / 'trip.spice').read_text())
    checks = {'prepared_deck_exact': sha(deck) == prep['prepared_deck_sha256'],
              'source_exact': all(sha(out / name) == value for name, value in prep['source_hashes'].items()),
              'runtime_exact': runtime == prep['expected_runtime_identity'],
              'original_summary_exact': sha(original / 'summary.json') == prep['reference_summary_sha256'],
              'original_provenance_exact': sha(original / 'provenance.json') == prep['reference_provenance_sha256'],
              'original_decoded_wave_exact': wave_sha(original / (case + '.dat')) == prep['reference_decoded_wave_sha256'],
              'source_hierarchy_passed': nodes['status'].startswith('passed')}
    (out / 'runner.py').write_text(Path(__file__).read_text())
    provenance = {'runner_arguments': sys.argv[1:], 'preparation_sha256': sha(out / 'preparation.json'),
                  'runtime_identity': runtime, 'input_checks': checks, 'source_hashes': prep['source_hashes'],
                  'runner_sha256': sha(Path(__file__)), 'reference_run': prep['reference_run'],
                  'scope': 'Exact output-only18column replay; original13columns remain first and must match allbytes.'}
    (out / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    assert all(checks.values()), 'Preflight failed; simulator not launched'
    with (out / (case + '.log')).open('x') as stream:
        state = run_bounded(['ngspice', '-b', str(deck.relative_to(SIM))], stream,
                            out / (case + '.json'), args.timeout_s, cwd=SIM,
                            metadata={'seed': prep['seed'], 'temperature_C': prep['temperature_C'],
                                      'deck_sha256': sha(deck), 'clock_Hz': 5000000}, interval_s=1)
    log = (out / (case + '.log')).read_text()
    errors = [line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such vector|not available|cannot parse)', line)]
    fingerprints = [list(pair) for pair in re.findall(r'^(@[^=]+) = (\S+)', log, re.M)]
    fp_exact = len(fingerprints) == 27 and fingerprints == prep['expected_observed27_parameters']
    wave = out / (case + '.dat')
    complete = state['status'] == 'completed' and state['returncode'] == 0 and not errors and 'QUALIFICATION_END' in log and wave.exists()
    parity = {'status': 'not run'}
    analysis = {'sampling_status': 'not run'}
    quiet = {}
    if complete:
        try:
            with open_wave(original / (case + '.dat'), 'rb') as stream:
                old = stream.readlines()
            parity, data = compare_original_columns(old, wave.read_bytes().splitlines(keepends=True))
            assert parity['projected_original_sha256'] == prep['reference_decoded_wave_sha256']
            analysis = analyze_wave([row[:13] for row in data], prep['prospective_sampling'])
            quiet = quiet_values(log)
        except (AssertionError, ValueError, IndexError) as error:
            parity = {'status': 'failed', 'error': str(error)}
            errors.append('Output observation qualification failed: ' + str(error))
    qualified = complete and fp_exact and parity['status'].startswith('passed') and analysis['sampling_status'] == 'passed' and bool(quiet)
    result = {'seed': prep['seed'], 'temperature_C': prep['temperature_C'], 'case': case,
              'solver_status': 'passed' if complete else 'failed', 'watchdog_status': state['status'],
              'returncode': state['returncode'], 'wall_s': state['wall_s'], 'errors': errors,
              'fingerprints': fingerprints, 'all27_parameters_exact': fp_exact,
              'original_wave_parity': parity, 'wave_analysis': analysis, 'quiet_op_V': quiet,
              'output_only_qualification_status': 'passed' if qualified else 'failed',
              'scope': 'Observation qualification only; unchanged original5MHz hot electrical failure and10MHz failure. IPTAT is node voltage, not current. No causal attribution or BGR replacement.'}
    (out / 'summary.json').write_text(json.dumps([result], indent=2) + '\n')
    if wave.exists():
        archive_new_wave(wave)
    print(json.dumps({key: result[key] for key in ['solver_status', 'wall_s', 'all27_parameters_exact', 'output_only_qualification_status', 'errors']}, indent=2))
    raise SystemExit(0 if qualified else 1)


if __name__ == '__main__':
    main()
