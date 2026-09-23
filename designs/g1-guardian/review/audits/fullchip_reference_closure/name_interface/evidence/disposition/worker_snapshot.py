#!/usr/bin/env python3
"""Saved-data disposition; preserve failed runners and missing-report errors."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


ap = argparse.ArgumentParser()
ap.add_argument('--output', type=Path, required=True)
a = ap.parse_args()
assert not a.output.exists()
bulk = Path(os.environ['G1_RESULTS_ROOT'])
paths = {
    'prepared': bulk / 'fullchip-name-interface-20260923-r1/summary.json',
    'same_original_failure': bulk / 'fullchip-name-control-same-20260923-r1/summary.json',
    'same_saved_failure': bulk / 'fullchip-name-control-same-saved-audit-20260923-r1/failure.json',
    'same_saved_pass': bulk / 'fullchip-name-control-same-saved-audit-20260923-r2/summary.json',
    'child_alias': bulk / 'fullchip-name-control-child-20260923-r1/summary.json',
    'wrong_connection': bulk / 'fullchip-name-control-wrong-20260923-r1/summary.json',
    'top_alias': bulk / 'fullchip-name-control-top-20260923-r1/summary.json'}
data = {k: json.loads(p.read_text()) for k, p in paths.items()}
assert data['same_original_failure']['status'] == 'failed stock-control parsing or preservation'
assert data['same_saved_pass']['status'].startswith('passed saved same-name')
assert data['same_saved_pass']['original_summary_sha256'] == sha(paths['same_original_failure'])
assert data['child_alias']['actual_strict_match'] is True
assert data['wrong_connection']['actual_strict_match'] is False
assert data['child_alias']['input_rules_unchanged'] and data['wrong_connection']['input_rules_unchanged']
for key in ('same_original_failure', 'child_alias', 'wrong_connection', 'top_alias'):
    forbidden = ('--ignore_top_ports_mismatch', '--net_only', '--disable_tap_extraction', '--implicit_nets')
    assert not any(any(arg.startswith(flag) for flag in forbidden) for arg in data[key]['command'])
top_dir = paths['top_alias'].parent
top_log = top_dir / 'stock.log'
assert data['top_alias']['returncode'] == 1
assert "Can't find a schematic counterpart for the top cell OTHER_TOP" in top_log.read_text()
assert not list((top_dir / 'reports').rglob('*.lvsdb'))
assert '| Status           | PASS' in top_log.read_text()
assert 'Congratulations! Netlists match.' not in top_log.read_text()
original = bulk / 'fullchip-source-reference-20260923-r1/g1_chip_top_current.cdl'
derived = bulk / 'fullchip-name-interface-20260923-r1/g1_chip_top_layout_name_only.cdl'
assert sha(original) == data['prepared']['original_reference_sha256']
assert sha(derived) == data['prepared']['derived_reference_sha256']
assert derived.read_bytes().replace(b'.SUBCKT placed_core_NOT_CONNECTED_FULLCHIP ', b'.SUBCKT g1_chip_top ', 1) == original.read_bytes()
result = dict(status='passed saved-data disposition; top-name error and helper failures retained',
              inputs={k: sha(p) for k, p in paths.items()}, top_failure_log_sha256=sha(top_log),
              original_reference_sha256=sha(original), top_name_only_reference_sha256=sha(derived),
              controls=[dict(case='same_names', stock_comparison='passed', expanded_MOS=4, top_pins=4,
                             metadata_initial='failed API usage', saved_data_recovery='passed', stock_rerun='not run'),
                        dict(case='child_alias', stock_comparison='passed', direct_MOS=4, nets=5, top_pins=4,
                             both_children_flattened=True, watchdog_seconds=180),
                        dict(case='wrong_connection', stock_comparison='failed', negative_detection='passed',
                             remaining_MOS_each_side=4),
                        dict(case='top_alias_observation', stock_comparison='not run: align failed first',
                             stock_alignment='failed', exitcode=1, lvsdb='missing, preserved as failure',
                             misleading_stock_summary_PASS='rejected')],
              checks=dict(top_name_only_inverse_and_token_proof='passed', unchanged_stock_child_alignment='passed',
                          wrong_connection_rejection='passed', mismatched_top_alignment='failed',
                          physical_extraction='not run', fullchip_LVS='not run',
                          known_IO_tap_comparison='failed prior result', production_source_geometry_rule_model_changes='not run',
                          stochastic_seed='not applicable'), script_sha256=sha(Path(__file__)))
a.output.mkdir(parents=True)
(a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
(a.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
