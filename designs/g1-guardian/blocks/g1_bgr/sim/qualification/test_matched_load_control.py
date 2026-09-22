import unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
import run_matched_load_control as target


class LoadAnalysis(unittest.TestCase):
    def fixture(self):
        d = np.zeros((20001, 12))
        d[:, 0] = np.linspace(0, 40e-6, len(d))
        d[:, 1] = 1.04
        d[:, 2] = 4e-6
        d[:, 3] = -25e-6
        d[(d[:, 0] >= 5.01e-6) & (d[:, 0] <= 20e-6), 1] -= .008
        return d

    def analyze(self, data):
        with patch.object(target.np, 'loadtxt', return_value=data), patch.object(target, 'sha', return_value='test'):
            return target.analyze(Path('synthetic.dat'))

    def test_scoped_pass_and_finite_step(self):
        result = self.analyze(self.fixture())
        self.assertEqual(result['status'], 'passed')
        self.assertAlmostEqual(result['finite_step_V_per_A'], -80000, places=5)

    def test_vref_return_fails(self):
        data = self.fixture()
        data[-100:, 1] += .0011
        self.assertFalse(self.analyze(data)['checks']['vref_return_1mV'])

    def test_iptat_return_fails(self):
        data = self.fixture()
        data[-100:, 2] *= 1.0011
        self.assertFalse(self.analyze(data)['checks']['iptat_return_0p1percent'])

    def test_partial_endpoint_rejected(self):
        with self.assertRaises(AssertionError):
            self.analyze(self.fixture()[:-1])

    def test_nonfinite_rejected(self):
        data = self.fixture()
        data[100, 8] = np.nan
        with self.assertRaises(AssertionError):
            self.analyze(data)

    def test_nonmonotone_rejected(self):
        data = self.fixture()
        data[100, 0] = data[99, 0]
        with self.assertRaises(AssertionError):
            self.analyze(data)


if __name__ == '__main__':
    unittest.main()
