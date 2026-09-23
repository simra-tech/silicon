import unittest
from analyze_586_supply_decomposition import decompose


class DecompositionTests(unittest.TestCase):
    def test_original_failure_preserved_without_refit(self):
        row = decompose(1025000, 1100000, 958600, 957900, -40)
        self.assertAlmostEqual(row['nominal_rail_error_C'], -1.4)
        self.assertAlmostEqual(row['supply_induced_difference_C'], -.7)
        self.assertAlmostEqual(row['total_adverse_error_C'], -2.1)
        self.assertEqual(row['original_adverse_accuracy_status'], 'failed')

    def test_no_supply_change_zero_delta(self):
        row = decompose(1025000, 1100000, 1124700, 1124700, 125)
        self.assertEqual(row['supply_induced_difference_C'], 0.)

    def test_invalid_slope_rejected(self):
        with self.assertRaises(AssertionError):
            decompose(100, 99, 110, 111, 125)


if __name__ == '__main__':
    unittest.main()
