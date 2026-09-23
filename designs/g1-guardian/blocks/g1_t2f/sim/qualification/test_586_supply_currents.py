import unittest
import numpy as np
from analyze_586_supply_currents import summarize


class SupplyStatisticsTests(unittest.TestCase):
    def test_constant_current_and_interpolated_window(self):
        row = summarize(np.array([0., 1., 3.]), np.array([2., 2., 2.]), .5, 2.)
        self.assertEqual(row['time_weighted_mean_A'], 2.)
        self.assertEqual(row['time_weighted_rms_A'], 2.)
        self.assertEqual(row['maximum_sampled_A'], 2.)
        self.assertEqual(row['samples_including_interpolated_boundaries'], 3)

    def test_rms_integrates_sampled_squared_current_trapezoid(self):
        row = summarize(np.array([0., 1.]), np.array([0., 1.]), 0., 1.)
        self.assertEqual(row['time_weighted_mean_A'], .5)
        self.assertAlmostEqual(row['time_weighted_rms_A'], np.sqrt(.5))

    def test_negative_current_not_clipped(self):
        row = summarize(np.array([0., 1., 2.]), np.array([-2., 0., 2.]), 0., 2.)
        self.assertEqual(row['time_weighted_mean_A'], 0.)
        self.assertEqual(row['minimum_sampled_A'], -2.)

    def test_extrapolation_rejected(self):
        with self.assertRaises(AssertionError):
            summarize(np.array([0., 1.]), np.array([1., 1.]), -.1, 1.)


if __name__ == '__main__':
    unittest.main()
