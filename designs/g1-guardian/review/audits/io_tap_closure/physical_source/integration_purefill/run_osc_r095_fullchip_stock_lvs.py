#!/usr/bin/env python3
"""Strict stock deep LVS for the isolated OSC R0.95 full-chip comparison.

The immutable canonical source is bound separately. Only its exact, reversible
three all-VDD pad-dummy projection is used as the stock comparison reference;
even a matching result is not an unprojected canonical LVS pass.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

import current_rz_bindings as prior
import current_rz_stock_preconditions as pre

TOP = 'placed_core_NOT_CONNECTED_FULLCHIP'
PDK_COMMIT = '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
GDS = ('osc-r095-fullchip-integration-20260924-r1/osc_r095_fullchip.gds',
       '18b897feb06b7a02508ea8734d40845d69bcb515955368daba9dd1938a1949c9')
CANONICAL = ('osc-r095-physical-20260924-r1/fullchip_r095_candidate.cdl',
             '126acd51cae404f55e9a3470d521d0d90f5115e668fbf393ac48c492e4507333')
PROJECTION = ('osc-r095-fullchip-integration-20260924-r1/source_projection_r1/physical_AP_three_dummy_comparison_only.cdl',
              '5e280d2e5e6955435e789a9838331d40eec83f9b1566e51d2a0796be06489dad')
PROJECTION_PROOF = ('osc-r095-fullchip-integration-20260924-r1/source_projection_r1/summary.json',
                    '9e9bd2e6564db226c685985124166d08bd61fcc8e7573aa6649cf1f653e09491')
NATIVE_PROOF = ('osc-r095-fullchip-native-dummies-20260924-r1/summary.json',
                'a5d625206e5f8917395ffa80a80ddeae83a29de45720d5b5420840de00578e3c')
FLAT = ('osc-r095-fullchip-flat-reference-20260924-r1/physical_AP_three_dummy_flat_reference.cdl',
        'a730e9a44a5ba31a9e923f0bafd8a5dbb6f65a5cc69f08f6e7c28459b6bba14b')
FLAT_PROOF = ('osc-r095-fullchip-flat-reference-20260924-r1/summary.json',
              '0471704a49ea66df144720303b82d5d8b55aacf165c8c87c5b6e4e8ce77ef915')
BOUND = (GDS, CANONICAL, PROJECTION, PROJECTION_PROOF, NATIVE_PROOF, FLAT, FLAT_PROOF,
         prior.STOCK_LVS_RULE_BASELINE, prior.PHYSICAL['main'], prior.EXPECTED_PINS,
         prior.STRICT_PARSER)


def read(path):
    return json.loads(path.read_text())


def bound_files():
    return {prior.bound(spec): spec[1] for spec in BOUND}


def prove_inputs():
    files = bound_files()
    files.update({Path(__file__).resolve(): prior.sha(Path(__file__)),
                  Path(prior.__file__).resolve(): prior.sha(prior.__file__),
                  Path(pre.__file__).resolve(): prior.sha(pre.__file__)})
    projection = read(prior.bound(PROJECTION_PROOF))
    native = read(prior.bound(NATIVE_PROOF))
    flat = read(prior.bound(FLAT_PROOF))
    assert projection['status'] == 'passed exact reversible source-only three-dummy projection; new native proof and stock LVS not run'
    assert projection['canonical_source_sha256'] == CANONICAL[1]
    assert projection['projected_source_sha256'] == PROJECTION[1]
    assert projection['reverse_bytes_exact'] is True
    assert projection['all_other_source_primitives_parameters_and_pins_held'] is True
    assert len(projection['removed']) == 3
    assert all(row['nodes'] == ['VDD']*4 and row['model'] == 'SG13_HV_PMOS'
               for row in projection['removed'].values())
    assert native['status'] == 'passed independent three-dummy source/native-terminal proof'
    assert len(native['source_occurrences']) == len(native['physical_instances']) == 3
    assert all(set(row['terminal_nodes'].values()) == {'VDD'} for row in native['source_occurrences'])
    assert all(row['all_four_terminals_to_native_VDD'].startswith('passed') for row in native['physical_instances'])
    assert native['inputs'][str(prior.bound(GDS))] == GDS[1]
    assert native['inputs'][str(prior.bound(CANONICAL))] == CANONICAL[1]
    assert flat['status'] == 'passed exact stock-reader source flatten roundtrip'
    assert flat['input_sha256'] == PROJECTION[1] and flat['output_sha256'] == FLAT[1]
    assert flat['primitive_count'] == 76059
    assert flat['roundtrip_pairs']['device'] == {'Match': 76059}
    assert flat['roundtrip_pairs']['pin'] == {'Match': 22}
    pdk = Path(os.environ.get('PDK_ROOT', '/foss/pdks'))/os.environ.get('PDK', 'ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip() == PDK_COMMIT
    deck = pdk/'libs.tech/klayout/tech/lvs/run_lvs.py'
    assert deck.is_file()
    original_rules = read(prior.bound(prior.STOCK_LVS_RULE_BASELINE))['stock_rule_hashes']
    tech_rules = read(prior.bound(prior.PHYSICAL['main']))['stock_rule_hashes']
    def rules_held():
        pre.require_rules(pre.rule_files(original_rules), pre.rule_files(pre.rule_tree(pdk, 'libs.tech/klayout/tech/lvs')))
        pre.require_rules(pre.rule_files(tech_rules), pre.rule_files(pre.rule_tree(pdk, 'libs.tech/klayout/tech')))
        return True
    assert rules_held()
    return files, deck, rules_held


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--summary', type=Path, required=True)
    ap.add_argument('--run-dir', type=Path, required=True)
    ap.add_argument('--resource-gate', type=Path, required=True)
    ap.add_argument('--cpu', type=int, required=True)
    args = ap.parse_args()
    assert not args.summary.exists() and not args.run_dir.exists()
    assert os.sched_getaffinity(0) == {args.cpu}
    files, deck, rules_held = prove_inputs()
    gate = read(args.resource_gate)
    pre.require_affinity(gate, os.sched_getaffinity(0), args.cpu)
    cmd = ['python3', str(deck), '--layout', str(prior.bound(GDS)),
           '--netlist', str(prior.bound(FLAT)), '--topcell', TOP,
           '--run_mode', 'deep', '--top_lvl_pins', '--spice_comments',
           '--run_dir', str(args.run_dir)]
    log = args.summary.with_suffix('.engine.log')
    assert not log.exists()
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    with log.open('x') as stream:
        try:
            process = subprocess.run(['timeout', '--kill-after=5', '600']+cmd,
                                     stdout=stream, stderr=subprocess.STDOUT,
                                     check=False, timeout=610)
            engine_rc = process.returncode
        except subprocess.TimeoutExpired:
            engine_rc = 124
    analysis = args.run_dir/'strict_analysis.json'
    parse_rc = None
    if args.run_dir.is_dir() and not analysis.exists():
        parse_cmd = ['python3', str(prior.bound(prior.STRICT_PARSER)),
                     '--reports', str(args.run_dir), '--returncode', str(engine_rc),
                     '--top', TOP, '--pins-json', str(prior.bound(prior.EXPECTED_PINS)),
                     '--output', str(analysis), '--mode', 'deep']
        parse_log = args.summary.with_suffix('.parser.log')
        assert not parse_log.exists()
        with parse_log.open('x') as stream:
            try:
                process = subprocess.run(['timeout', '--kill-after=5', '60']+parse_cmd,
                                         stdout=stream, stderr=subprocess.STDOUT,
                                         check=False, timeout=70)
                parse_rc = process.returncode
            except subprocess.TimeoutExpired:
                parse_rc = 124
    strict = read(analysis) if analysis.is_file() else {}
    try:
        rules_after = rules_held()
    except (AssertionError, OSError):
        rules_after = False
    try:
        bindings_after = pre.require_bound_hashes(files)
    except (AssertionError, OSError):
        bindings_after = False
    passed = (engine_rc == 0 and parse_rc == 0 and
              strict.get('status') == 'passed strict saved comparison' and
              strict.get('checks') and all(strict['checks'].values()) and
              rules_after and bindings_after)
    result = {'status': 'passed projected-reference strict stock LVS' if passed else 'failed projected-reference strict stock LVS',
              'wrapper_source_sha256': files[Path(__file__).resolve()],
              'prior_bindings_source_sha256': files[Path(prior.__file__).resolve()],
              'preconditions_source_sha256': files[Path(pre.__file__).resolve()],
              'canonical_source_sha256': CANONICAL[1], 'comparison_source_sha256': FLAT[1],
              'projection_source_sha256': PROJECTION[1], 'layout_gds_sha256': GDS[1],
              'native_dummy_proof_sha256': NATIVE_PROOF[1],
              'source_projection_proof_sha256': PROJECTION_PROOF[1],
              'source_flatten_proof_sha256': FLAT_PROOF[1],
              'canonical_unprojected_LVS': 'not run',
              'source_device_omissions': 'exactly three proved all-VDD stock-purged IO pad PMOS in comparison only',
              'strict_missing_ports': True, 'stock_deck_unmodified': rules_after,
              'bound_inputs_unchanged_after_engine': bindings_after,
              'engine_returncode': engine_rc, 'parser_returncode': parse_rc,
              'stock_command': cmd, 'analysis_sha256': prior.sha(analysis) if analysis.is_file() else None}
    with args.summary.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'canonical_unprojected_LVS': 'not run'}))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
