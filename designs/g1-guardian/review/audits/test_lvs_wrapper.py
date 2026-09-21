#!/usr/bin/env python3
"""Ensure failures cannot be hidden by pipelines or PDK zero-exit mismatches."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
WRAPPER = ROOT / 'designs/g1-guardian/blocks/g1_padring/flow/lvs/run_core_lvs.sh'


class FailurePropagation(unittest.TestCase):
    def run_case(self, mode):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for name, code in {
                'python3': """#!/bin/sh
case "$1" in
  */core_cdl.py) [ "$MOCK_MODE" != cdl_failure ] || exit 7; echo cdl-ready ;;
  */run_lvs.py)
    case "$MOCK_MODE" in
      process_failure) echo 'Comparison mode: PASS (netlists match).'; exit 8 ;;
      mismatch) echo "Comparison mode: FAIL (netlists do not match)." ;;
      incomplete) echo 'Still extracting...' ;;
      *) echo 'Comparison mode: PASS (netlists match).' ;;
    esac ;;
esac
""",
                'klayout': """#!/bin/sh
[ "$MOCK_MODE" != geometry_failure ] || exit 9
echo geometry-ready
""",
            }.items():
                path = base / name; path.write_text(code); path.chmod(0o755)
            env = dict(os.environ, PATH=str(base) + os.pathsep + os.environ['PATH'], MOCK_MODE=mode)
            run = subprocess.run(['bash', str(WRAPPER), 'fixture with spaces', str(base / 'out with spaces')],
                                 env=env, capture_output=True, text=True)
            return run.returncode, run.stdout + run.stderr

    def test_explicit_pass(self):
        self.assertEqual(self.run_case('pass')[0], 0)

    def test_failures(self):
        for mode in ('cdl_failure', 'geometry_failure', 'process_failure', 'mismatch', 'incomplete'):
            with self.subTest(mode=mode):
                code, output = self.run_case(mode)
                self.assertNotEqual(code, 0, output)


if __name__ == '__main__': unittest.main()
