import unittest
from analyze_joint586_fastcold_nodeset_pair import compare_waves


def blob(times, shift=0):
    return ('time '+' '.join('v(n%d)'%i for i in range(18))+'\n'+''.join(
        ' '.join(map(str, [t]+[t+shift]*18))+'\n' for t in times)).encode()


class PairTests(unittest.TestCase):
    def test_exact_self(self):
        r = compare_waves(blob([0,1]), blob([0,1]))
        self.assertTrue(r['decoded_bytes_exact'] and r['numeric_rows_exact'] and r['time_grid_exact'])

    def test_grid_failure_retained(self):
        r = compare_waves(blob([0,1]), blob([0,.5,1]))
        self.assertFalse(r['time_grid_exact'])
        self.assertFalse(r['decoded_bytes_exact'])
        self.assertEqual(r['uniongrid_voltage_comparison']['v(n0)']['max_abs_V'], 0)

    def test_voltage_difference_not_exact(self):
        r = compare_waves(blob([0,1]), blob([0,1], .125))
        self.assertFalse(r['numeric_rows_exact'])
        self.assertEqual(r['uniongrid_voltage_comparison']['v(n0)']['max_abs_V'], .125)

    def test_duplicate_time_not_interpolated(self):
        r = compare_waves(blob([0,0,1]), blob([0,1]))
        self.assertTrue(r['uniongrid_voltage_comparison'].startswith('not run'))


if __name__ == '__main__':
    unittest.main()
