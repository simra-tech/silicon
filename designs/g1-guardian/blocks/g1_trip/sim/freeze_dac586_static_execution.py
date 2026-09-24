#!/usr/bin/env python3
"""Freeze prepared input and complete execution-helper identities, without launching."""
import argparse
import json
from pathlib import Path
from prepare_dac586_static_controls import SIM, ROOT, CASES, sha

FILES = ['prepare_dac586_static_controls.py', 'run_dac586_static_control.py', 'audit_dac586_static_controls.py',
         'freeze_dac586_static_execution.py', 'test_dac586_static_controls.py', 'test_dac586_static_runtime.py',
         'prepare_joint586_population.py', 'run_bgr_substitution_draw_audit.py', 'run_nominal_clock_probe.py',
         'analyze_bgr_substitution_outcomes.py', 'result_directory.py']


def freeze(prefix, output):
    assert not output.exists()
    paths = [SIM/name for name in FILES]
    # run_nominal_clock_probe imports the shared bounded runner.
    paths.append(SIM.parents[1]/'g1_top/sim/run_bounded.py')
    result = {'status': 'prepared; execution not run', 'prefix': prefix,
        'source_sha256': {str(path.relative_to(ROOT)): sha(path) for path in paths},
        'preparations_sha256': {str((SIM/'qualification'/(prefix+'-'+label)/'preparation.json').relative_to(ROOT)):
            sha(SIM/'qualification'/(prefix+'-'+label)/'preparation.json') for label, _, _, _ in CASES},
        'hard_aggregate_bound_s': 4200, 'max_concurrent_simulators': 1,
        'scope': '11 static controls only, no code population or dynamic settling claim. CPU lease/resource gate external prerequisite.'}
    output.write_text(json.dumps(result, indent=2)+'\n')
    return sha(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    print(freeze(a.prefix, ROOT/a.output))
