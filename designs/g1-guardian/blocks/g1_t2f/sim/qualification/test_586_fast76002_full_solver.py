import unittest
from prepare_586_fast76002_full_solver import ORIGINAL, make_full


class FullSolverTests(unittest.TestCase):
    def test_exact_single_selector(self):
        original = (ORIGINAL/'probe.cir').read_text()
        trial = make_full(original)
        self.assertEqual(trial.replace('.options klu\n', ''), original)
        self.assertEqual(len(trial.splitlines()), len(original.splitlines())+1)
        self.assertEqual(trial.count('tran 5n 32u\n'), 1)
        self.assertEqual(trial.count('meas tran '), original.count('meas tran '))

    def test_reject_wrong_endpoint_or_seed(self):
        original = (ORIGINAL/'probe.cir').read_text()
        for changed in [original.replace('tran 5n 32u', 'tran 5n 2u'), original.replace('setseed 76002', 'setseed 76003')]:
            with self.assertRaises(AssertionError):
                make_full(changed)


if __name__ == '__main__':
    unittest.main()
