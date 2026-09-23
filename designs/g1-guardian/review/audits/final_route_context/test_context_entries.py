import unittest
from report_context_entries import entries


class ContextEntries(unittest.TestCase):
    def test_equal_nonzero(self):
        self.assertTrue(all(r['status']=='passed' for r in entries([[1.,-.1],[-.1,2.]],[[1.,-.1],[-.1,2.]])))

    def test_exceeds_original_relative_gate(self):
        rows=entries([[1.02,-.1],[-.1,2.]],[[1.,-.1],[-.1,2.]])
        self.assertTrue(rows[0]['status'].startswith('failed greater'))

    def test_equal_zero_still_undefined(self):
        rows=entries([[1.,0.],[0.,2.]],[[1.,0.],[0.,2.]])
        self.assertIsNone(rows[1]['relative_difference'])
        self.assertEqual(rows[1]['absolute_difference_fF'],0)
        self.assertTrue(rows[1]['status'].startswith('failed undefined'))

    def test_nonzero_to_zero_not_accepted(self):
        rows=entries([[1.,-.1],[-.1,2.]],[[1.,0.],[0.,2.]])
        self.assertFalse(rows[1]['exact_equal'])
        self.assertTrue(rows[1]['status'].startswith('failed undefined'))

    def test_bad_matrix_rejected(self):
        for bad in ([[1.]],[[1.,float('nan')],[0.,1.]]):
            with self.assertRaises(AssertionError): entries(bad,[[1.,0.],[0.,1.]])


if __name__=='__main__': unittest.main()
