import unittest
from prepare_joint586_leaf_recovery import transform, ORIGINAL


class RecoveryTests(unittest.TestCase):
    def test_only_output_path_changes(self):
        original = '.include qualification/'+ORIGINAL+'/sense.spice\nsetseed 73034\ntran 0.2n 1.02u 0 0.2n\nwrdata qualification/'+ORIGINAL+'/p09/phase0.dat v(a)\n'
        changed = transform(original, 'fresh')
        self.assertIn('.include qualification/'+ORIGINAL+'/sense.spice\n', changed)
        self.assertEqual(changed.replace('qualification/fresh/phase0.dat', 'qualification/'+ORIGINAL+'/p09/phase0.dat'), original)

    def test_missing_output_rejected(self):
        with self.assertRaises(AssertionError):
            transform('tran 0.2n 1.02u\n', 'fresh')


if __name__ == '__main__':
    unittest.main()
