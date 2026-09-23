import json
import unittest
import run_joint586_adverse_json_continuation as adapter


class JsonContinuation(unittest.TestCase):
    def test_original_failure_and_exact_normalization(self):
        value = [('room', 25, 3.3, 1.2, None)]
        saved = json.loads(json.dumps(value))
        self.assertNotEqual(value, saved)
        self.assertEqual(adapter.normalized_conditions(value, saved), saved)

    def test_value_change_rejected(self):
        with self.assertRaises(AssertionError):
            adapter.normalized_conditions([('room', 25, 3.3, 1.2, None)], [['room', 125, 3.3, 1.2, None]])

    def test_actual_frozen_sixty_decks(self):
        old = adapter.original.CONDITIONS
        try:
            receipt = adapter.qualify(adapter.original.SIM/'qualification/joint586-slow-calibration-s77101-20260923-a')
            self.assertEqual(receipt['unchanged_deck_count'], 60)
        finally:
            adapter.original.CONDITIONS = old


if __name__ == '__main__':
    unittest.main()
