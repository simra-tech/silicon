import unittest
from audit_joint586_calibration import replay_parent_tree


class ParentReplayTests(unittest.TestCase):
    def probes(self):
        return [dict(kind='calibration', codes=[0, 0], status='passed', decisions={'soft': True, 'hard': True}, run='p00'),
                dict(kind='calibration', codes=[255, 255], status='passed', decisions={'soft': False, 'hard': False}, run='p01'),
                dict(kind='calibration', codes=[127, 127], status='failed', decisions={}, run='p02')]

    def test_failed_tree_json_brackets(self):
        rows = self.probes()
        tree = replay_parent_tree(rows)
        self.assertEqual(tree['current_brackets'], {'soft': [0, 255], 'hard': [0, 255]})
        self.assertEqual(tree['all_attempts'], rows)
        self.assertEqual(tree['failed_selected_run'], 'p02')

    def test_guard_and_audit_metadata_not_added_to_replay(self):
        rows = self.probes()
        audited = [dict(r, log_sha256='audit-only') for r in rows]
        tree = replay_parent_tree(rows+[dict(kind='guard')])
        self.assertEqual(tree['all_attempts'], rows)
        self.assertNotEqual(tree['all_attempts'], audited)

    def test_unfinished_parent_not_complete(self):
        self.assertIsNone(replay_parent_tree(self.probes()[:1]))


if __name__ == '__main__':
    unittest.main()
