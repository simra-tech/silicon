import unittest
from run_586_calibration_sample import REFERENCE, TEMPERATURES, sample_deck, calibrate, qualification_gate
from pathlib import Path
import tempfile


class SampleTests(unittest.TestCase):
    def test_only_seed_and_temperature_transform(self):
        old = (REFERENCE/'probe.cir').read_text()
        for seed in [74101, 74400]:
            for temperature in TEMPERATURES:
                new = sample_deck(old, seed, temperature)
                restored = new.replace('setseed %d\n' % seed, 'setseed 74001\n')
                restored = restored.replace('.temp %d\n' % temperature, '.temp 25\n')
                restored = restored.replace('set temp=%d\n' % temperature, 'set temp=25\n')
                self.assertEqual(restored, old)

    def test_outside_population_or_conditions_rejected(self):
        old = (REFERENCE/'probe.cir').read_text()
        for seed, temperature in [(74001, 25), (74401, 25), (74101, 50)]:
            with self.assertRaises(AssertionError):
                sample_deck(old, seed, temperature)

    def test_linear_criterion_retained(self):
        rows = {25: 1000., 100: 1750., -40: 350., 125: 2000.}
        self.assertEqual(calibrate(rows)['status'], 'passed')
        rows[-40] += 20.01
        self.assertEqual(calibrate(rows)['status'], 'failed')
        self.assertEqual(calibrate(rows)['slope_Hz_per_C'], 10.)

    def test_missing_condition_and_bad_slope_rejected(self):
        for rows in [{25: 1}, {25: 1000., 100: 999., -40: 800., 125: 1100.}]:
            with self.assertRaises(AssertionError):
                calibrate(rows)

    def test_unqualified_population_gate_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'audit.json'
            path.write_text('{"status":"failed"}')
            with self.assertRaises(AssertionError):
                qualification_gate(path)


if __name__ == '__main__':
    unittest.main()
