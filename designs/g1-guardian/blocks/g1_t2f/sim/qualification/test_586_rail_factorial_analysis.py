import unittest
from analyze_586_rail_factorial import factorial


class FactorialAnalysisTests(unittest.TestCase):
    def test_additive_and_interacting_terms_are_distinct(self):
        r = factorial(1000, 1750, 350, 340, 345, 332)
        self.assertEqual(r['nominal_error_C'], 0)
        self.assertEqual(r['analog_plus_enable_delta_C'], -1)
        self.assertEqual(r['digital_rail_delta_C'], -.5)
        self.assertEqual(r['interaction_C'], -.3)
        self.assertAlmostEqual(r['observed_allhigh_error_C'], -1.8)
        self.assertLess(abs(r['reconstruction_residual_C']), 1e-10)

    def test_original_failure_not_refitted(self):
        r = factorial(1000, 1750, 350, 330, 345, 325)
        self.assertEqual(r['original_accuracy_status'], 'failed')
        self.assertEqual(r['observed_allhigh_error_C'], -2.5)

    def test_invalid_slope_rejected(self):
        with self.assertRaises(AssertionError):
            factorial(1000, 1000, 1, 2, 3, 4)


if __name__ == '__main__':
    unittest.main()
