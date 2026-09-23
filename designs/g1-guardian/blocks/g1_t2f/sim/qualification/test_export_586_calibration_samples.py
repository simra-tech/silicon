import unittest
from export_586_calibration_samples import validate_audit


class ExportTests(unittest.TestCase):
    def fixture(self):
        return dict(status='passed read-only evidence audit', requested_samples=2, completed_samples=2,
            passed_samples=1, failed_complete_samples=1,
            records=[dict(seed=74101, run='first', complete=True), dict(seed=74102, run='failed', complete=True)])

    def test_electrical_failure_retained(self):
        self.assertEqual(len(validate_audit(self.fixture())), 2)

    def test_incomplete_cohort_not_exported_as_complete(self):
        data = self.fixture()
        data['records'][1]['complete'] = False
        with self.assertRaises(AssertionError):
            validate_audit(data)

    def test_duplicate_seed_rejected(self):
        data = self.fixture()
        data['records'][1]['seed'] = 74101
        with self.assertRaises(AssertionError):
            validate_audit(data)


if __name__ == '__main__':
    unittest.main()
