#!/usr/bin/env python3
"""Run only one reviewed OP inventory; no transient option exists."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from run_nominal_clock_probe import run_bounded

SIM = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_group(log, tag, expected):
    sections = re.findall(r'^' + tag + r'_BEGIN\n(.*?)^' + tag + r'_END$', log, re.M | re.S)
    assert len(sections) == 1, 'Missing or repeated group ' + tag
    rows = [list(pair) for pair in re.findall(r'^(@\S+)\s*=\s*(\S+)', sections[0], re.M)]
    assert [key for key, value in rows] == expected, 'Invalid/missing/reordered parameter query in ' + tag
    assert all(math.isfinite(float(value)) for key, value in rows)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--image-id', required=True)
    parser.add_argument('--timeout-s', type=float, default=120)
    args = parser.parse_args()
    assert '/' not in args.run_id and args.run_id not in ['.', '..'] and 0 < args.timeout_s <= 120
    out = SIM / 'qualification' / args.run_id
    prep = json.loads((out / 'preparation.json').read_text())
    temperature = prep['temperature_C']
    assert temperature in [25, 125]
    inventory = json.loads((out / 'non_bgr_inventory.json').read_text())
    bindings = json.loads((out / 'prelaunch_reference_bindings.json').read_text())
    assert prep['run'] == args.run_id and prep['status'] == 'prepared only; simulator not run'
    assert not (out / 'op.log').exists() and not (out / 'summary.json').exists()
    deck = out / 'draw_audit.cir'
    text = deck.read_text()
    assert not re.search(r'^(tran|dc|ac|noise|alter|altermod)\b', text, re.M | re.I)
    assert len(re.findall(r'^op$', text, re.M)) == 1
    assert 'setseed 71002\nreset\nop\n' in text
    pdk = Path('/foss/pdks/ihp-sg13g2')
    runtime = {'image_id_observed_by_host': args.image_id, 'pdk_commit': (pdk / 'COMMIT').read_text().strip(),
               'ngspice_version': subprocess.check_output(['ngspice', '--version'], text=True),
               'model_sha256': {str(p.relative_to(pdk)): sha(p) for p in (pdk / 'libs.tech/ngspice/models').rglob('*') if p.is_file()},
               'solver': 'sparse'}
    checks = {'deck_exact': sha(deck) == prep['deck_sha256'],
              'source_exact': all(sha(out / name) == value for name, value in prep['source_hashes'].items()),
              'runtime_exact': runtime == prep['expected_runtime_identity'],
              'query_inventory_exact': sha(out / 'non_bgr_inventory.json') == prep['non_bgr_inventory_sha256'],
              'live_reference_bindings_exact': all(sha(SIM.parents[4] / relative) == expected
                                                  for relative, expected in bindings['sha256'].items())}
    assert bindings['sha256'][prep['candidate_nominal_reference']] == prep['candidate_nominal_reference_manifest_sha256']
    groups = {'LEGACY27': list(prep['legacy27_expected']), 'NON_BGR_ALL': inventory['queries'], 'BGR_ALL': prep['bgr_queries']}
    caps = [query for query in inventory['queries'] if query.startswith('@c.')]
    assert len(caps) == 6 and all(query.endswith('.c1[scale]') for query in caps)
    assert len(inventory['queries']) == 8670
    provenance = {'runner_arguments': sys.argv[1:], 'source_hashes': prep['source_hashes'],
                  'runtime_identity': runtime, 'input_checks': checks, 'runner_sha256': sha(Path(__file__)),
                  'preparation_sha256': sha(out / 'preparation.json'),
                  'prelaunch_reference_bindings': bindings,
                  'ordered_parameter_groups': groups,
                  'cmim_queries': caps,
                  'cmim_model_provenance': {
                      'path': 'libs.tech/ngspice/models/capacitors_mod_mismatch.lib',
                      'sha256': runtime['model_sha256']['libs.tech/ngspice/models/capacitors_mod_mismatch.lib'],
                      'wrapper': 'cap_cmim', 'inner_device': 'C1', 'queried_parameter': 'scale',
                      'lines': [51, 54, 58, 60, 62],
                      'expression': '(1+(cap_carea_mm-1)/sqrt(l*w*1e12))',
                      'scope': 'Actual pinned wrapper connects random cap_carea_mm to innerC1 scale; query existence/finitevalues must pass runtime output contract. No fallback to nominal capacitance or omission.'},
                  'scope': 'OP-only query/realization qualification. No transient, calibration or BGR adoption.'}
    (out / 'runner.py').write_text(Path(__file__).read_text())
    (out / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    assert all(checks.values()), 'Input preflight failed; no simulator launch'
    with (out / 'op.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', str(deck.relative_to(SIM))], stream, out / 'op.json',
                            args.timeout_s, cwd=SIM, metadata={'seed': 71002, 'temperature_C': temperature,
                            'kind': prep['kind'], 'deck_sha256': sha(deck)}, interval_s=1)
    log = (out / 'op.log').read_text()
    warnings = [line for line in log.splitlines() if 'warning' in line.lower() or 'nan' in line.lower()]
    errors = [line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such vector|no such parameter|not available|cannot parse)', line)]
    complete = state['status'] == 'completed' and state['returncode'] == 0 and not errors and 'DRAW_AUDIT_END' in log
    observed = {}
    query_status = 'not run'
    legacy_status = False
    candidate_nominal_status = None
    quiet = {}
    if complete:
        try:
            observed = {tag: read_group(log, tag, queries) for tag, queries in groups.items()}
            regions = re.findall(r'^BGR_ALL_END\n(.*?)^DRAW_AUDIT_END$', log, re.M | re.S)
            assert len(regions) == 1
            quiet = {key: float(value) for key, value in re.findall(r'^(v\([^\n=]+\))\s*=\s*(\S+)', regions[0], re.M)}
            assert set(quiet) == {'v(vref)', 'v(iptat)', 'v(vref_buf)', 'v(vped)', 'v(shp)', 'v(isense)', 'v(xt.icmp)', 'v(xt.vth_soft)', 'v(xt.vth_hard)'}
            assert all(math.isfinite(value) for value in quiet.values())
            legacy = dict(observed['LEGACY27'])
            required = prep['legacy27_expected'] if prep['kind'] == 'baseline' else prep['non_bgr24_expected']
            legacy_status = all(legacy[key] == value for key, value in required.items())
            full = dict(observed['NON_BGR_ALL'])
            assert all(full[key] == value for key, value in prep['non_bgr24_expected'].items())
            assert all(math.isfinite(float(full[key])) and float(full[key]) > 0 for key in caps)
            query_status = 'passed complete ordered finite parameter groups and all6CMIM scales'
            if prep['kind'] == 'candidate':
                candidate_nominal_status = [value for key, value in observed['BGR_ALL']] == prep['expected_candidate2842_nominal_values']
        except (AssertionError, ValueError, KeyError) as error:
            query_status = 'failed'
            errors.append('Parameter query qualification failed: ' + str(error))
    qualified = complete and query_status.startswith('passed') and legacy_status and candidate_nominal_status is not False
    result = {'kind': prep['kind'], 'seed': 71002, 'temperature_C': temperature,
              'solver_status': 'passed' if complete else 'failed', 'wall_s': state['wall_s'],
              'watchdog_status': state['status'], 'returncode': state['returncode'], 'errors': errors,
              'warning_lines': warnings, 'quiet_op_V': quiet,
              'ordered_parameter_groups': observed, 'parameter_query_status': query_status,
              'original_legacy_required_exact': legacy_status, 'candidate2842_all_nominal_exact': candidate_nominal_status,
              'op_inventory_qualification_status': 'passed' if qualified else 'failed',
              'scope': 'An individual OP inventory is not fullnonBGRpairparity. Compare both complete8670vectors before any transient; originalhotfailures unchanged.'}
    (out / 'summary.json').write_text(json.dumps([result], indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['kind', 'solver_status', 'wall_s', 'parameter_query_status', 'original_legacy_required_exact', 'candidate2842_all_nominal_exact', 'op_inventory_qualification_status', 'errors']}, indent=2))
    raise SystemExit(0 if qualified else 1)


if __name__ == '__main__':
    main()
