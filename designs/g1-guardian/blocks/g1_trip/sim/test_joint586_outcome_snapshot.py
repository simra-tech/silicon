import unittest
from audit_joint586_calibration import outcome_snapshot


class OutcomeTests(unittest.TestCase):
    def test_missing_decision_not_observed_wrong_decision(self):
        result = dict(seed=73025, status='failed electrical or numerical check', bracket_status='passed selected probes',
            guards_status='passed', residual_half_mV_status='failed', probes=[dict(run='failed', kind='residual',
                status='failed', decisions={}, expected_decisions={'soft': False, 'hard': False}),
                dict(run='wrong', kind='residual', status='passed', decisions={'soft': False, 'hard': True},
                     expected_decisions={'soft': False, 'hard': False})])
        row = outcome_snapshot(result)
        self.assertEqual(row['numerical_failed_leaves'], ['failed'])
        self.assertEqual(row['observed_wrong_decision_leaves'], ['wrong'])
        self.assertFalse(row['full_expected_leaf_coverage'])


if __name__ == '__main__':
    unittest.main()
