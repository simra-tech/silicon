import unittest
from prepare_586_fast76002_method import make_prefix,GEAR,ORIGINAL


class MethodOnly(unittest.TestCase):
    def test_inverse_restores_exact_qualified_gear(self):
        new=make_prefix((ORIGINAL/'probe.cir').read_text())
        self.assertEqual(new.replace('method=trap','method=gear'),(GEAR/'probe.cir').read_text())
        self.assertEqual(new.count('method=trap'),1)
        self.assertEqual(new.count('tran 5n 2u\n'),1)
    def test_duplicate_or_missing_method_rejected(self):
        old=(ORIGINAL/'probe.cir').read_text()
        with self.assertRaises(AssertionError):make_prefix(old.replace('method=gear','method=trap'))


if __name__=='__main__':unittest.main()
