import unittest
from export_joint586_calibration import validate_audit


class ExportTests(unittest.TestCase):
    def audit(self):
        return dict(status='passed read-only evidence audit; outcomes separate', requested_samples=2, completed_samples=2,
                    fully_passed_samples=1, failed_completed_samples=1,
                    records=[dict(seed=1, run='sample1', complete=True), dict(seed=2, run='sample2', complete=True)])

    def test_failed_sample_retained(self):
        self.assertEqual(len(validate_audit(self.audit())), 2)

    def test_incomplete_refused(self):
        value = self.audit()
        value['records'][1]['complete'] = False
        with self.assertRaises(AssertionError):
            validate_audit(value)

    def test_duplicate_seed_refused(self):
        value = self.audit()
        value['records'][1]['seed'] = 1
        with self.assertRaises(AssertionError):
            validate_audit(value)

    def test_count_mismatch_refused(self):
        value = self.audit()
        value['failed_completed_samples'] = 0
        with self.assertRaises(AssertionError):
            validate_audit(value)


if __name__ == '__main__':
    unittest.main()
