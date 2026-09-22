import math
import unittest
from analyze_current_envelopes import integrate_linear_current, window_values, fixture_windows


class CurrentIntegralTests(unittest.TestCase):
    def test_pinned_full_timeline(self):
        name, windows = fixture_windows('001e608cb3018553d48542d951bfe22a20d7c970c34376cb3553d5404bd96b36')
        self.assertEqual(name, 'full42us')
        self.assertEqual(windows['complete'], (0, 42e-6))
        self.assertEqual(windows['fault_transition'], (30e-6, 32e-6))
        with self.assertRaises(ValueError):
            fixture_windows('unqualified source')

    def test_dc_and_ramp_rms(self):
        self.assertEqual(integrate_linear_current([0, 1], [-2, -2])['rms_A'], 2)
        r = integrate_linear_current([0, 2], [-1, 1])
        self.assertEqual(r['mean_A'], 0)
        self.assertAlmostEqual(r['rms_A'], 1/math.sqrt(3))

    def test_boundaries_and_no_extrapolation(self):
        self.assertEqual(window_values([0, 1, 2], [0, 2, 4], .5, 1.5), ([.5, 1, 1.5], [1, 2, 3]))
        with self.assertRaises(ValueError):
            window_values([0, 1], [0, 2], -.1, .5)
        with self.assertRaises(ValueError):
            integrate_linear_current([0, 0], [1, 1])


if __name__ == '__main__':
    unittest.main()
