import unittest
from prepare_586_fast76002_prefix import ORIGINAL, MEASUREMENTS, make_prefix


class PrefixTests(unittest.TestCase):
    def test_exact_restore_and_no_future_measurements(self):
        original = (ORIGINAL/'probe.cir').read_text()
        prefix = make_prefix(original)
        self.assertEqual(len(MEASUREMENTS.strip().splitlines()), 12)
        self.assertNotIn('meas tran ', prefix)
        self.assertNotIn('print freq', prefix)
        self.assertIn('tran 5n 2u\n', prefix)
        restored = prefix.replace('tran 5n 2u\n', 'tran 5n 32u\n').replace('wrdata phase0.dat ', MEASUREMENTS+'wrdata phase0.dat ')
        self.assertEqual(restored, original)

    def test_unexpected_future_measurement_rejected(self):
        original = (ORIGINAL/'probe.cir').read_text()
        with self.assertRaises(AssertionError):
            make_prefix(original.replace('quit\n', 'meas tran future max v(fout) from=8u to=9u\nquit\n'))

    def test_wrong_seed_or_duplicate_transient_rejected(self):
        original = (ORIGINAL/'probe.cir').read_text()
        for bad in [original.replace('setseed 76002', 'setseed 76003'), original.replace('tran 5n 32u\n', 'tran 5n 32u\ntran 5n 32u\n')]:
            with self.assertRaises(AssertionError):
                make_prefix(bad)


if __name__ == '__main__':
    unittest.main()
