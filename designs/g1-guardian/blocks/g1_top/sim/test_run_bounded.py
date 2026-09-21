"""Process-level checks for retained diagnostics and reliable watchdog metadata."""
import json
import pathlib
import sys
import tempfile
import unittest
from run_bounded import run_bounded

class WatchdogTests(unittest.TestCase):
    def run_child(self, code, timeout):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = pathlib.Path(tmp.name)
        with (p/'child.log').open('x') as log:
            result = run_bounded([sys.executable, '-u', '-c', code], log,
                                 p/'child.json', timeout, interval_s=.02)
        return p, result

    def test_timeout_preserves_output_and_real_signal_exit(self):
        p, r = self.run_child('import time; print("progress before timeout", flush=True); time.sleep(10)', .2)
        self.assertEqual(r['status'], 'timeout')
        self.assertLess(r['returncode'], 0)
        self.assertIn('progress before timeout', (p/'child.log').read_text())
        self.assertEqual(json.loads((p/'child.json').read_text())['status'], 'timeout')
        self.assertGreater(len((p/'child.progress.jsonl').read_text().splitlines()), 1)

    def test_nonzero_is_failure_not_timeout(self):
        _, r = self.run_child('raise SystemExit(7)', 2)
        self.assertEqual((r['status'], r['returncode']), ('failed', 7))

    def test_success_is_process_completion_only(self):
        p, r = self.run_child('print("Reference value : 1.25e-7", flush=True)', 2)
        self.assertEqual((r['status'], r['returncode']), ('completed', 0))
        self.assertEqual(r['last_reported_sim_time_s'], 1.25e-7)
        with (p/'other.log').open('x') as log:
            with self.assertRaises(FileExistsError):
                run_bounded([sys.executable,'-c','pass'],log,p/'child.json',2)

class LaunchFailureTests(unittest.TestCase):
    def test_missing_working_directory_records_no_child_exit_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            p = pathlib.Path(temporary)
            with (p/'child.log').open('x') as log:
                result = run_bounded([sys.executable, '-c', 'pass'], log,
                                     p/'child.json', 1, cwd=p/'absent')
            self.assertEqual(result['status'], 'launch_failed')
            self.assertIsNone(result['returncode'])
            self.assertIn('launch_error', result)
            saved = json.loads((p/'child.json').read_text())
            self.assertEqual(saved['status'], 'launch_failed')
            self.assertIsNone(saved['returncode'])

class PrefixAcceptanceTests(unittest.TestCase):
    def fixture(self, rows):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        p = pathlib.Path(temporary.name)/'wave.txt'
        p.write_text('time v(vref) v(isense) v(gate) v(vdd) v(vdda) v(osc_clk) v(cmp_clk)\n' + rows)
        return p

    def test_finite_complete_saved_waveform_required(self):
        from run_top import validate_prefix
        p = self.fixture('0 1 1 0 1.2 3.3 0 0\n1e-6 1 1 0 1.2 3.3 1.2 1.2\n')
        self.assertTrue(validate_prefix('DIAGNOSTIC_PREFIX_END_S 1E-06', p, 1e-6)[0])
        p.unlink()
        self.assertFalse(validate_prefix('DIAGNOSTIC_PREFIX_END_S 1E-06', p, 1e-6)[0])

    def test_nonfinite_or_truncated_waveform_rejected(self):
        from run_top import validate_prefix
        p = self.fixture('0 1 1 0 1.2 3.3 0 0\n1e-6 nan 1 0 1.2 3.3 1.2 1.2\n')
        self.assertFalse(validate_prefix('DIAGNOSTIC_PREFIX_END_S 1E-06', p, 1e-6)[0])
        p = self.fixture('0 1 1 0 1.2 3.3 0 0\n5e-7 1 1 0 1.2 3.3 1.2 1.2\n')
        self.assertFalse(validate_prefix('DIAGNOSTIC_PREFIX_END_S 1E-06', p, 1e-6)[0])

if __name__ == '__main__':
    unittest.main()
