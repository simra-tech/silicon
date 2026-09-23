import unittest
from audit_expanded_sta import wire_values,macro_totals


class ReportTests(unittest.TestCase):
    def test_two_corner_values(self):
        self.assertEqual(wire_values(' Wire capacitance: 0.5-0.4\n'),[.5,.4])

    def test_invalid_or_missing_capacitance(self):
        for text in ('',' Wire capacitance: nan\n',' Wire capacitance: 0.0\n',' Wire capacitance: -0.1\n',' Wire capacitance: inf\n'):
            with self.assertRaises(AssertionError):wire_values(text)

    def test_duplicate_report_rejected(self):
        with self.assertRaises(AssertionError):wire_values(' Wire capacitance: 1\n'*2)

    def test_macro_totals(self):
        self.assertEqual(macro_totals('*1 sdo\n*D_NET *1 0.2\n'),{'sdo':.2})

    def test_duplicate_total_rejected(self):
        with self.assertRaises(AssertionError):macro_totals('*1 sdo\n*D_NET *1 0.2\n*D_NET *1 0.2\n')


if __name__=='__main__':unittest.main()
