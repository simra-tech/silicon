import json
import unittest
import numpy as np
from audit_586_raw_terminal_mapping import candidate_mos
from probe_586_external_terminals import json_orientation


class MappingTests(unittest.TestCase):
    def test_forward_nmos(self):
        current, swapped = candidate_mos([2, 0, -2, 0, 1], 2, 1)
        self.assertEqual(current, [2, 0, -2, 0])
        self.assertFalse(swapped)

    def test_reverse_nmos(self):
        current, swapped = candidate_mos([2, 0, -2, 0, 1], 1, 2)
        self.assertEqual(current, [-2, 0, 2, 0])
        self.assertTrue(swapped)

    def test_pmos_polarity(self):
        current, swapped = candidate_mos([2, 0, -2, 0, -1], 1, 3.3)
        self.assertEqual(current, [-2, 0, 2, 0])
        self.assertFalse(swapped)

    def test_numpy_orientation_serializes(self):
        for value in [None, np.bool_(True), np.bool_(False)]:
            result = json.loads(json.dumps({'swapped': json_orientation(value)}))
            self.assertIn(result['swapped'], [None, True, False])


if __name__ == '__main__':
    unittest.main()
