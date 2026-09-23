"""Pure controls for the new physical-PEX qualification wrapper (no solver)."""
import subprocess
import sys
import unittest
from pathlib import Path

import run_mc_newpex as candidate


class Controls(unittest.TestCase):
    def test_attempted_timeout_is_failed_not_not_run(self):
        row = candidate.attempt_classification(True)
        self.assertEqual(row, {'status': 'failed', 'failure_kind': 'numerical watchdog timeout'})

    def test_non_timeout_initially_failed_until_full_audit(self):
        self.assertEqual(candidate.attempt_classification(False)['status'], 'failed')

    def test_second_resistor_scaling_option_rejected_before_allocation(self):
        runner = Path(candidate.__file__)
        cmd = [sys.executable, str(runner), '--run-id', 'invalid-no-run',
               '--image-id', 'invalid', '--suite', 'qualify', '--pex-source', 'invalid',
               '--pex-sha256', 'invalid', '--r-charge-scale', '0.95']
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('unrecognized arguments: --r-charge-scale 0.95', result.stderr)


if __name__ == '__main__':
    unittest.main()
