#!/usr/bin/env python3
"""Saved engine/database controls; no new stock extraction or comparison."""
import argparse
import copy
import json
import os
from pathlib import Path
import traceback
from inspect_stock_result_r3 import analyze, classify, inspect_database, sha, resolve_top

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    a.output.mkdir(parents=True)
    for name in ('test_saved_results_r3.py', 'inspect_stock_result_r3.py', 'run_fullchip_stock.py'):
        (a.output / name).write_bytes((HERE / name).read_bytes())
    result = dict(status='running saved-data tests', rows=[])
    try:
        evidence = HERE.parent / 'name_interface/evidence'
        positive = None
        for name, expected, code in [('same_run', True, 0), ('child_alias', True, 0),
                                     ('wrong_connection', False, 0), ('top_alignment_failure', False, 1)]:
            folder = evidence / name
            source = json.loads((folder / 'summary.json').read_text())
            assert source['returncode'] == code
            parsed = analyze(folder / 'reports', code, 'NAME_CONTROL_TOP', False, ['A', 'Y', 'VDD', 'VSS'])
            assert parsed['status'].startswith('passed') == expected
            if expected:
                assert all(parsed['database'][side]['NAME_CONTROL_TOP']['expanded_devices'] == 4 for side in ('layout', 'reference'))
                positive = parsed
            if name == 'wrong_connection':
                assert parsed['explicit_engine_mismatch'] and parsed['database']['status'] == 'failed'
            if name == 'top_alignment_failure':
                assert parsed['database'] is None and not parsed['explicit_engine_match']
                wrapper = '\n'.join(p.read_text() for p in (folder / 'reports').glob('lvs_run_*.log'))
                assert '| Status' in wrapper and '| PASS' in wrapper
            result['rows'].append(dict(case=name, expected_strict_match=expected,
                                       original_summary_sha256=sha(folder / 'summary.json'), result=parsed))
        warning_db = HERE.parents[1] / 'io-tap-binding-lvs-levelup-20260922-r1/normalized/lvs/g1_chip_top.lvsdb'
        warning = inspect_database(warning_db, 'sg13g2_LevelUpInv')
        assert warning['status'] == 'failed'
        assert any(row['reachable_from_chip'] and any('MatchWithWarning' in counts for counts in row['pairs'].values()) for row in warning['circuits'])
        result['rows'].append(dict(case='actual_saved_IO_tap_MatchWithWarning_rejected', result=warning))
        db = positive['database']
        engine = 'Congratulations! Netlists match.'
        for name, code, text, report in [('nonzero_exit_with_positive_engine', 1, engine, db),
                                        ('missing_database_with_positive_engine', 0, engine, None),
                                        ('contradictory_engine_signatures', 0, engine + " Netlists don't match", db)]:
            parsed = classify(code, text, report, 'NAME_CONTROL_TOP', False)
            assert parsed['status'].startswith('failed')
            result['rows'].append(dict(case=name, result=parsed))
        # Revisions must not hide wrong tops, ambiguous names or relaxed flags.
        assert resolve_top({'mixed_Top': {}}, 'MIXED_TOP') == 'mixed_Top'
        assert resolve_top({'mixed_Top': {}, 'MIXED_TOP': {}}, 'mixed_top') is None
        assert resolve_top({'another_top': {}}, 'mixed_top') is None
        result['rows'].append(dict(case='unique_case_binding_positive_collision_and_wrong_top_negative', status='passed'))
        physical_lines = [
            'Selected LAYOUT_NETLIST option: (none)', 'Selected NET_ONLY option: false',
            'Selected IMPLICIT_NETS option: (none)', 'Selected DISABLE_TAP_EXTRACTION option: false',
            'Starting SG13G2 LVS Comparison in strict port mode.',
            'flag_missing_ports enabled: missing/mislabeled top-level ports are treated as errors.']
        for suffix, expected in [('', True), ('false', True), ('true', False),
                                 ('unknown', False), ('false\\nSelected IGNORE_TOP_PORTS_MISMATCH option: false', False)]:
            text = '\\n'.join([engine] + physical_lines + ['Selected IGNORE_TOP_PORTS_MISMATCH option: ' + suffix])
            got = classify(0, text, db, 'name_control_top', True)
            assert got['status'].startswith('passed') == expected
            result['rows'].append(dict(case='strict_flag_value_' + repr(suffix), result=got))
        absent_strict = classify(0, engine + '\\nSelected IGNORE_TOP_PORTS_MISMATCH option: ', db, 'NAME_CONTROL_TOP', True)
        assert absent_strict['status'].startswith('failed')
        result['rows'].append(dict(case='blank_flag_without_strict_branch_proof_rejected', result=absent_strict))
        recorded_engine = (Path(os.environ['G1_RESULTS_ROOT']) / 'fullchip-native-strict-lvs-20260923-r2/reports/sealed_native.log').read_text()
        recorded = classify(0, recorded_engine, db, 'NAME_CONTROL_TOP', True)
        assert recorded['checks']['native_extraction_strict_unrelaxed_switches']
        assert recorded['status'].startswith('failed') and recorded['explicit_engine_mismatch']
        result['rows'].append(dict(case='actual_multiline_log_strict_branch_and_mismatch_both_recognized', result=recorded))
        result.update(status='passed sixteen saved-data and failure-propagation controls',
                      new_stock_runs='not run', final_native_fullchip_LVS='not run', seed='not applicable',
                      script_sha256=sha(Path(__file__)), parser_sha256=sha(HERE / 'inspect_stock_result_r3.py'))
    except BaseException as exc:
        result.update(status='failed saved-data control', exception=repr(exc), traceback=traceback.format_exc())
        raise
    finally:
        (a.output / 'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
        print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
