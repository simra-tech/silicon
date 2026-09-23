#!/usr/bin/env python3
"""Saved engine/database controls; no new stock extraction or comparison."""
import argparse
import copy
import json
import os
from pathlib import Path
import traceback
from inspect_stock_result import analyze, classify, inspect_database, sha

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    a.output.mkdir(parents=True)
    for name in ('test_saved_results.py', 'inspect_stock_result.py', 'run_fullchip_stock.py'):
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
        result.update(status='passed eight saved-data and failure-propagation controls',
                      new_stock_runs='not run', final_native_fullchip_LVS='not run', seed='not applicable',
                      script_sha256=sha(Path(__file__)), parser_sha256=sha(HERE / 'inspect_stock_result.py'))
    except BaseException as exc:
        result.update(status='failed saved-data control', exception=repr(exc), traceback=traceback.format_exc())
        raise
    finally:
        (a.output / 'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
        print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
