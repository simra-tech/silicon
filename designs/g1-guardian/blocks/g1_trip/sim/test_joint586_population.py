import re
import unittest
from prepare_joint586_population import CASES, disabled_source, make_control


class PopulationContractTests(unittest.TestCase):
    def test_six_controls_include_changed_enabled_and_disabled(self):
        self.assertEqual(len(CASES), 6)
        self.assertIn(('changed', 73002, [25]), CASES)
        self.assertIn(('disabledchanged', 73002, [25]), CASES)

    def test_return_does_not_redraw(self):
        text = make_control('test', 73001, [25, 125, -40, 25], {'ALL': ['@a[x]']})
        self.assertEqual(text.count('\nreset\n'), 1)
        self.assertEqual(text.count('\nsetseed '), 1)
        self.assertEqual(text.count('\nop\n'), 8)
        self.assertEqual(text.count('print @a[x]'), 8)
        self.assertEqual(re.findall(r'^set temp=(.+)$', text, re.M), ['25', '125', '-40', '25'])
        self.assertIsNone(re.search(r'^(tran|dc|alter|altermod|ac)\b', text, re.M))

    def test_disabled_source_changes_only_flags(self):
        text = 'XM1 a b c d sg13_hv_nmos w=1u l=1u mm_ok=1\nXR1 a b 0 rppd w=1u l=1u mm_ok=1\n'
        actual = disabled_source(text)
        self.assertEqual(actual.replace('mm_ok=0', 'mm_ok=1'), text)
        self.assertEqual(actual.count('mm_ok=0'), 2)

    def test_already_disabled_source_rejected(self):
        with self.assertRaises(AssertionError):
            disabled_source('X a b c mm_ok=0\n')


if __name__ == '__main__':
    unittest.main()
