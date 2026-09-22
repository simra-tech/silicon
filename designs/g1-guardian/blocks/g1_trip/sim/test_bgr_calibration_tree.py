import unittest
from audit_bgr_calibration_tree import replay


def record(a, b, soft, hard, status='passed'):
    return {'run': '%d-%d' % (a, b), 'codes': [a, b], 'status': status,
            'decisions': {'soft': soft, 'hard': hard}}


class TreeReplayTests(unittest.TestCase):
    def test_exact_pair_required_after_divergence(self):
        rows = [record(0, 0, True, True), record(255, 255, False, False),
                record(127, 127, True, True), record(191, 191, True, False),
                record(223, 223, False, False), record(159, 159, True, False)]
        self.assertEqual(replay(rows)['next_required_codes'], [223, 159])

    def test_failed_selected_probe_is_not_replaced(self):
        rows = [record(0, 0, True, True), record(255, 255, False, False),
                record(127, 127, True, True, 'failed')]
        self.assertEqual(replay(rows)['bracket_status'], 'failed selected probe; no automatic retry')

    def test_original_binary_bracket_and_offpath(self):
        rows = [record(c, c, c < 181, c < 181) for c in [0, 255, 127, 191, 159, 175, 183, 179, 181, 180, 239]]
        out = replay(rows)
        self.assertEqual(out['brackets'], {'soft': (180, 181), 'hard': (180, 181)})
        self.assertEqual(out['fixed_residual_codes'], {'soft': 181, 'hard': 181})
        self.assertEqual(out['off_path_runs'], ['239-239'])
        self.assertEqual(out['corrected_codes'], {'soft': 206, 'hard': 255})

    def test_offpath_nonmonotonic_prevents_adoption(self):
        rows = [record(c, c, c < 181, c < 181) for c in [0, 255, 127, 191, 159, 175, 183, 179, 181, 180]]
        rows.append(record(239, 239, True, True))
        out = replay(rows)
        self.assertFalse(out['all_observed_probe_monotonicity']['soft'])
        self.assertNotIn('corrected_codes', out)

    def test_duplicate_pair_requires_explicit_parity(self):
        with self.assertRaises(ValueError):
            replay([record(0, 0, True, True)]*2)


if __name__ == '__main__':
    unittest.main()
