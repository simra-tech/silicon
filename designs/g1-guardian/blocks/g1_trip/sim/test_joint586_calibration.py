import unittest
from pathlib import Path
import tempfile
from run_joint586_calibration import calibration_deck, check_pause


class Joint586CalibrationTests(unittest.TestCase):
    def test_explicit_pause_only_at_leaf_boundary(self):
        check_pause(None)
        with tempfile.TemporaryDirectory() as directory:
            flag = Path(directory)/'PAUSE'
            check_pause(flag)
            flag.touch()
            with self.assertRaises(InterruptedError):
                check_pause(flag)

    def fixture(self):
        return '.temp 25.0\nVsh shp 0 dc 0.025\n'+''.join('V%s%d %s%d 0 dc 0\n' % (k, i, k, i) for k in ['s', 'h'] for i in range(8))+'.include old/source.spice\n.control\nsetseed 73001\nreset\ntran 0.2n 1.02u 0 0.2n\nwrdata old/phase0.dat v(q)\n.endc\n.end\n'

    def test_only_declared_stimulus_and_seed(self):
        result = calibration_deck(self.fixture(), 'old', 'new', 73002, [0, 255], .027, 125)
        self.assertEqual(result.count('setseed 73002\n'), 1)
        self.assertEqual(result.count('reset\n'), 1)
        self.assertEqual(result.count('tran 0.2n 1.02u 0 0.2n\n'), 1)
        self.assertIn('Vh7 h7 0 dc 1.2\n', result)
        self.assertIn('Vs7 s7 0 dc 0\n', result)
        self.assertIn('wrdata new/phase0.dat v(q)', result)

    def test_missing_qualified_seed_fails(self):
        with self.assertRaises(AssertionError):
            calibration_deck(self.fixture().replace('73001', '73002'), 'old', 'new', 73003, [0, 255], .025, 25)

    def test_out_of_range_code_fails(self):
        with self.assertRaises(AssertionError):
            calibration_deck(self.fixture(), 'old', 'new', 73003, [0, 256], .025, 25)


if __name__ == '__main__':
    unittest.main()
